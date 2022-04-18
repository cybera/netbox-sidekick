from django.core.management.base import BaseCommand
from django.utils.text import slugify

from dcim.models import Site
from tenancy.models import Contact, ContactAssignment, ContactRole


class Command(BaseCommand):
    help = "Migrate Contacts for NetBox 3.2"

    def _get_contact_data(self, site):
        name = site.contact_name.strip()
        phone = site.contact_phone.strip()
        email = site.contact_email.strip()

        attrs = {
            'name': name
        }

        if phone:
            attrs['phone'] = phone
        if email:
            attrs['email'] = email

        return attrs

    def handle(self, *args, **options):
        try:
            contact_role = ContactRole.objects.get(name='Network')
        except ContactRole.DoesNotExist:
            contact_role = ContactRole(
                name="Network",
                slug=slugify("Network"),
            )
            contact_role.save()

        sites = Site.objects.exclude(contact_name='')
        for site in sites:
            contact_data = self._get_contact_data(site)
            contact = Contact.objects.filter(**contact_data).first()
            if not contact:
                contact = Contact(**contact_data)
                contact.save()

            elif site.contacts.filter(contact=contact).exists():
                continue

            assignment = ContactAssignment(
                object=site,
                contact=contact,
                role=contact_role,
                priority="Primary",
            )
            assignment.save()

            Site.objects.filter(pk=site.pk).update(
                contact_name='',
                contact_phone='',
                contact_email='',
            )
