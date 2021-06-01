from django.db import models
from django.urls import reverse

from extras.models import ChangeLoggedModel


# ContactType represents different types of contacts.
class ContactType(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Type',
        help_text='A type to represent a contact',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:sidekick:contacttype_detail', args=[self.slug])


# Contact represents contact information of a person
class Contact(ChangeLoggedModel):
    first_name = models.CharField(
        max_length=255,
        unique=False,
        verbose_name='First Name',
        help_text='The first name of the contact',
    )

    last_name = models.CharField(
        max_length=255,
        unique=False,
        verbose_name='Last Name',
        help_text='The last name of the contact',
    )

    title = models.CharField(
        max_length=255,
        verbose_name='Title',
        help_text='The title of the contact',
        blank=True,
        default='',
    )

    email = models.EmailField(
        verbose_name='Email Address',
        help_text='The email address of the contact',
        blank=True,
        default='',
    )

    phone = models.CharField(
        max_length=255,
        verbose_name='Phone Number',
        help_text='The phone number of the contact',
        blank=True,
        default='',
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the contact',
        blank=True,
        default='',
    )

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:contact_detail', args=[self.pk])


class MemberContact(ChangeLoggedModel):
    member = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    contact = models.ForeignKey(
        'sidekick.Contact',
        on_delete=models.PROTECT,
    )

    type = models.ForeignKey(
        'sidekick.ContactType',
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ['member', 'contact', 'type']

    def __str__(self):
        return f"{self.member} {self.type}: {self.contact}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:membercontact_detail', args=[self.pk])
