"""Guard the sidekick API serializer contract.

Each rule below exists because a consumer paid for its absence.

`id` was missing from every sidekick serializer except the accounting ones, while core
NetBox publishes it on every endpoint. Consumers had to parse the trailing segment of
`url` to identify a record — the ops MCP entity resolver did exactly that before
2026-10-27.

`display` is the string NetBox uses for human-facing labels and join keys; without it a
consumer reimplements `__str__`.

Foreign keys rendered as bare integers (`member: 37`), so resolving a member name or a
logical system name took a second request per relation. Core NetBox renders them as
brief nested objects on read and accepts a primary key on write (`nested=True`).

These are contract tests over serializer classes, so they need no database.
"""

from django.test import SimpleTestCase
from rest_framework import serializers

from sidekick.api.serializers import (
    accounting,
    networkservice,
    nic,
)

NESTED_EXPECTATIONS = {
    networkservice.NetworkServiceSerializer: ('network_service_type', 'member', 'member_site'),
    # `interface` is deliberately absent: it is a CharField holding a name, not a FK.
    networkservice.NetworkServiceDeviceSerializer: ('network_service', 'device'),
    networkservice.NetworkServiceL2Serializer: ('network_service_device',),
    networkservice.NetworkServiceL3Serializer: (
        'network_service_device', 'logical_system', 'routing_type'),
    networkservice.NetworkServiceGroupSerializer: ('network_services',),
    accounting.AccountingProfileSerializer: ('member',),
    accounting.BandwidthProfileSerializer: ('accounting_profile',),
    accounting.AccountingSourceSerializer: ('device',),
}

# Fields deliberately left as primary keys, with the reason recorded here so a later
# reader does not "fix" them into a recursion or a payload problem.
INTENTIONAL_PKS = {
    networkservice.NetworkServiceSerializer: ('backup_for', 'accounting_profile'),
    networkservice.NetworkServiceL3Serializer: ('ip_prefixes',),
    accounting.AccountingProfileSerializer: ('accounting_sources',),
}


class BandwidthProfileBillingFieldsTest(SimpleTestCase):
    """Billing is cap times rate; the cap and its billability must be readable.

    BandwidthProfile holds the per-member transit cap with an effective date and a
    `billable` flag, reached through AccountingProfile.member. The serializer published
    neither `accounting_profile` nor `billable` before 2026-10-27, so no API consumer
    could compute a bill without hitting the database directly.
    """

    def test_billable_is_published(self):
        self.assertIn('billable', accounting.BandwidthProfileSerializer.Meta.fields)

    def test_accounting_profile_is_nested_and_carries_member(self):
        field = accounting.BandwidthProfileSerializer().fields['accounting_profile']
        self.assertIsInstance(field, serializers.BaseSerializer)
        self.assertIn('member', field.Meta.brief_fields)

    def test_traffic_cap_is_published(self):
        fields = accounting.BandwidthProfileSerializer.Meta.fields
        for name in ('traffic_cap', 'burst_limit', 'effective_date'):
            self.assertIn(name, fields)


def _serializers():
    """Every ModelSerializer defined in the sidekick serializer modules."""
    found = []
    for module in (accounting, networkservice):
        for name in dir(module):
            obj = getattr(module, name)
            is_serializer = isinstance(obj, type) and issubclass(
                obj, serializers.ModelSerializer)
            if is_serializer and obj.__module__ == module.__name__:
                found.append(obj)
    return found


class SerializerFieldContractTest(SimpleTestCase):
    def test_every_serializer_publishes_id(self):
        offenders = [
            serializer.__name__
            for serializer in _serializers()
            if 'id' not in (getattr(getattr(serializer, 'Meta', None), 'fields', ()) or ())
        ]
        self.assertEqual(
            offenders,
            [],
            f"serializers without an 'id' field: {offenders}. Consumers cannot identify "
            "a record from a list response without it.",
        )

    def test_every_serializer_publishes_display(self):
        offenders = [
            serializer.__name__
            for serializer in _serializers()
            if 'display' not in (getattr(getattr(serializer, 'Meta', None), 'fields', ()) or ())
        ]
        self.assertEqual(offenders, [], f"serializers without a 'display' field: {offenders}")

    def test_every_serializer_declares_brief_fields(self):
        missing = [
            serializer.__name__
            for serializer in _serializers()
            if not getattr(getattr(serializer, 'Meta', None), 'brief_fields', None)
        ]
        self.assertEqual(
            missing,
            [],
            f"serializers without brief_fields: {missing}. A nested relation would then "
            "render its full payload, and nesting could recurse.",
        )

    def test_brief_fields_are_a_subset_of_fields(self):
        offenders = []
        for serializer in _serializers():
            meta = serializer.Meta
            extra = [field for field in meta.brief_fields if field not in meta.fields]
            if extra:
                offenders.append(f"{serializer.__name__}: {extra}")
        self.assertEqual(offenders, [], f"brief_fields absent from fields: {offenders}")


class NestedRelationTest(SimpleTestCase):
    def test_expected_relations_are_nested(self):
        for serializer, field_names in NESTED_EXPECTATIONS.items():
            declared = serializer().fields
            for name in field_names:
                with self.subTest(serializer=serializer.__name__, field=name):
                    self.assertIn(
                        name,
                        declared,
                        f"{serializer.__name__} does not declare {name}, so it would render "
                        "as a bare primary key",
                    )
                    self.assertIsInstance(
                        declared[name],
                        serializers.BaseSerializer,
                        f"{serializer.__name__}.{name} is not a serializer, so it renders "
                        "as a bare primary key instead of a brief object",
                    )

    def test_intentionally_pk_fields_stay_pk(self):
        for serializer, field_names in INTENTIONAL_PKS.items():
            declared = serializer().fields
            for name in field_names:
                with self.subTest(serializer=serializer.__name__, field=name):
                    self.assertIn(name, declared)
                    self.assertNotIsInstance(
                        declared[name],
                        serializers.BaseSerializer,
                        f"{serializer.__name__}.{name} was nested, see INTENTIONAL_PKS "
                        f"for why {name} is a primary key",
                    )


class NICSerializerTest(SimpleTestCase):
    def test_nic_publishes_id(self):
        declared = nic.NICSerializer().fields
        self.assertIn('id', declared)
        self.assertIn('interface_name', declared)
