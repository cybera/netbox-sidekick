from django.core.management.base import BaseCommand

from tenancy.models import Tenant, TenantGroup


class Command(BaseCommand):
    help = "Print member contacts"

    def handle(self, *args, **options):
        group = TenantGroup.objects.get(name="Members")
        members = Tenant.objects.filter(group=group)
        for member in members:
            for site in member.sites.all():
                for c in site.contacts.all():
                    contact = c.contact
                    self.stdout.write(f"{member},{contact.name},{contact.email}")
