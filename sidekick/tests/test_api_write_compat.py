"""A nested relation must still accept a primary key on write.

On 2026-10-27 the sidekick serializers started rendering foreign keys as brief
nested objects instead of bare integers. NetBox's `nested=True` means "render
briefly on read, accept a primary key on write", and that asymmetry is the whole
reason the change is meant to be safe for anyone who writes through the API.

This test asserts the write half, because "nested renders as an object" passing
its own tests says nothing about whether a PATCH still works. A regression here
would break every script that updates a service by id while the read path looked
perfectly healthy.
"""

from sidekick.tests.utils import BaseTest


class NestedWriteCompatibilityTest(BaseTest):
    def test_patch_accepts_a_member_primary_key(self):
        url = '/api/plugins/sidekick/networkservice/1/'

        response = self.client.patch(
            url, data={'member': 2}, content_type='application/json', **self.header)

        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        # Written as a key, read back as an object.
        self.assertIsInstance(body['member'], dict)
        self.assertEqual(body['member']['id'], 2)

    def test_patch_accepts_a_logical_system_primary_key(self):
        url = '/api/plugins/sidekick/networkservicel3/1/'

        response = self.client.patch(
            url, data={'logical_system': 2}, content_type='application/json', **self.header)

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['logical_system']['id'], 2)

    def test_patch_still_rejects_an_unknown_primary_key(self):
        url = '/api/plugins/sidekick/networkservice/1/'

        response = self.client.patch(
            url, data={'member': 999999}, content_type='application/json', **self.header)

        self.assertEqual(response.status_code, 400, response.content)

    def test_declared_nullability_matches_the_model(self):
        """`allow_null` on a nested field must follow the model's `null=True`.

        A serializer that advertises null for a NOT NULL column makes the API
        schema wrong and defers the failure to the database.
        """
        from rest_framework import serializers as drf

        from sidekick.api.serializers import networkservice

        checks = [
            (networkservice.NetworkServiceSerializer, 'member', False),
            (networkservice.NetworkServiceSerializer, 'member_site', False),
            (networkservice.NetworkServiceSerializer, 'network_service_type', False),
            (networkservice.NetworkServiceDeviceSerializer, 'network_service', True),
            (networkservice.NetworkServiceDeviceSerializer, 'device', True),
            (networkservice.NetworkServiceL2Serializer, 'network_service_device', True),
            (networkservice.NetworkServiceL3Serializer, 'network_service_device', True),
            (networkservice.NetworkServiceL3Serializer, 'logical_system', True),
            (networkservice.NetworkServiceL3Serializer, 'routing_type', True),
        ]
        for serializer_class, name, nullable in checks:
            with self.subTest(serializer=serializer_class.__name__, field=name):
                field = serializer_class().fields[name]
                self.assertIsInstance(field, drf.BaseSerializer)
                self.assertEqual(
                    field.allow_null,
                    nullable,
                    f"{serializer_class.__name__}.{name}: allow_null={field.allow_null} "
                    f"but the model column is {'nullable' if nullable else 'NOT NULL'}",
                )
