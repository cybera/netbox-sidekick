from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from tenancy.models import Tenant, TenantGroup
from dcim.models import Device

from .sidekick_utils import MEMBER_TYPES


class Command(BaseCommand):
    help = "Setup Sidekick"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

        parser.add_argument(
            '--quiet', required=False, action='store_true',
            help='Suppress messages')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        quiet = options['quiet']

        tenant_obj_type = ContentType.objects.get_for_model(Tenant)
        device_obj_type = ContentType.objects.get_for_model(Device)

        # Create a new Tenant Group called Members.
        try:
            tg = TenantGroup.objects.get(name="Members")
        except TenantGroup.DoesNotExist:
            tg = TenantGroup(name='Members')
            if dry_run:
                self.stdout.write('Would have created a Tenant Group called Members')
            else:
                tg.save()
                if not quiet:
                    self.stdout.write('Created Tenant Group called Members')

        # Create a new Custom Field called MemberType
        # and add it to Tenant.
        try:
            member_type = CustomField.objects.get(name="member_type")
        except CustomField.DoesNotExist:
            member_type = CustomField(
                type=CustomFieldTypeChoices.TYPE_SELECT,
                name='member_type',
                required=False,
                choices=MEMBER_TYPES,
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called member_type')
            else:
                member_type.save()
                member_type.content_types.set([tenant_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called member_type')

        # Create a new Custom Field called latitude
        # and add it to Tenant and Device.
        try:
            latitude = CustomField.objects.get(name="latitude")
        except CustomField.DoesNotExist:
            latitude = CustomField(
                type=CustomFieldTypeChoices.TYPE_TEXT,
                name='latitude',
                required=False,
                default='',
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called latitude')
            else:
                latitude.save()
                latitude.content_types.set([tenant_obj_type, device_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called latitude')

        # Create a new Custom Field called longitude
        # and add it to Tenant and Device.
        try:
            longitude = CustomField.objects.get(name="longitude")
        except CustomField.DoesNotExist:
            longitude = CustomField(
                type=CustomFieldTypeChoices.TYPE_TEXT,
                name='longitude',
                required=False,
                default='',
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called longitude')
            else:
                longitude.save()
                longitude.content_types.set([tenant_obj_type, device_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called longitude')

        # Create a new Custom Field called primary_map_node
        # and add it to Device.
        try:
            primary_map_node = CustomField.objects.get(name="primary_map_node")
        except CustomField.DoesNotExist:
            primary_map_node = CustomField(
                type=CustomFieldTypeChoices.TYPE_BOOLEAN,
                name='primary_map_node',
                label='Primary Map Node',
                description='The node that represents the primary/central device for mapping purposes',
                required=False,
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called primary_map_node')
            else:
                primary_map_node.save()
                primary_map_node.content_types.set([device_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called primary_map_node')

        # Create a new Custom Field called map_label
        # and add it to Device.
        try:
            map_label = CustomField.objects.get(name="map_label")
        except CustomField.DoesNotExist:
            map_label = CustomField(
                type=CustomFieldTypeChoices.TYPE_TEXT,
                name='map_label',
                label='Map Label',
                description='A descriptive name for mapping purposes',
                required=False,
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called map_label')
            else:
                map_label.save()
                map_label.content_types.set([device_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called map_label')

        # Create a new Custom Field called crm_id
        # and add it to Tenant.
        try:
            crm_id = CustomField.objects.get(name="crm_id")
        except CustomField.DoesNotExist:
            crm_id = CustomField(
                type=CustomFieldTypeChoices.TYPE_TEXT,
                name='crm_id',
                required=False,
                default='',
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called crm_id')
            else:
                crm_id.save()
                crm_id.content_types.set([tenant_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called crm_id')

        # Create a new Custom Field called active
        # and add it to Tenant.
        try:
            active = CustomField.objects.get(name="active")
        except CustomField.DoesNotExist:
            active = CustomField(
                type=CustomFieldTypeChoices.TYPE_BOOLEAN,
                name='active',
                required=False,
                default=True,
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called active')
            else:
                active.save()
                active.content_types.set([tenant_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called active')

        # Create a new Custom Field called legacy_id
        # and add it to Device
        try:
            legacy_id = CustomField.objects.get(name="legacy_id")
        except CustomField.DoesNotExist:
            legacy_id = CustomField(
                type=CustomFieldTypeChoices.TYPE_TEXT,
                name='legacy_id',
                required=False,
                default='',
            )
            if dry_run:
                self.stdout.write('Would have created a Custom Field called legacy_id')
            else:
                legacy_id.save()
                legacy_id.content_types.set([device_obj_type])
                if not quiet:
                    self.stdout.write('Created Custom Field called legacy_id')
