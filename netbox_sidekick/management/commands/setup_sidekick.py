from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField
from tenancy.models import Tenant, TenantGroup

from .sidekick_utils import MEMBER_TYPES


class Command(BaseCommand):
    help = "Setup Sidekick"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        # Create a new Tenant Group called Members.
        try:
            tg = TenantGroup.objects.get(name="Members")
        except TenantGroup.DoesNotExist:
            if options['dry_run']:
                self.stdout.write('Would have created a Tenant Group called Members')
            else:
                tg = TenantGroup(name='Members')
                tg.save()

        tenant_obj_type = ContentType.objects.get_for_model(Tenant)

        # Create a new Custom Field called MemberType
        # and add it to Tenant.
        try:
            mtf = CustomField.objects.get(name="member_type")
        except CustomField.DoesNotExist:
            if options['dry_run']:
                self.stdout.write('Would have created a Custom Field called member_type')
            else:
                mtf = CustomField(
                    type=CustomFieldTypeChoices.TYPE_SELECT,
                    name='member_type',
                    required=False,
                    choices=MEMBER_TYPES,
                )
                mtf.save()
                mtf.content_types.set([tenant_obj_type])

        # Create a new Custom Field called latitude
        # and add it to Tenant.
        try:
            latitude = CustomField.objects.get(name="latitude")
        except CustomField.DoesNotExist:
            if options['dry_run']:
                self.stdout.write('Would have created a Custom Field called latitude')
            else:
                latitude = CustomField(
                    type=CustomFieldTypeChoices.TYPE_TEXT,
                    name='latitude',
                    required=False,
                    default='',
                )
                latitude.save()
                latitude.content_types.set([tenant_obj_type])

        # Create a new Custom Field called longitude
        # and add it to Tenant.
        try:
            longitude = CustomField.objects.get(name="longitude")
        except CustomField.DoesNotExist:
            if options['dry_run']:
                self.stdout.write('Would have created a Custom Field called longitude')
            else:
                longitude = CustomField(
                    type=CustomFieldTypeChoices.TYPE_TEXT,
                    name='longitude',
                    required=False,
                    default='',
                )
                longitude.save()
                longitude.content_types.set([tenant_obj_type])
