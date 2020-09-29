from django.db import models
from django.urls import reverse

from extras.models import ChangeLoggedModel


# MemberNodeType represents a type of member node.
class MemberNodeType(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Type',
        help_text='A type to represent a group of member nodes',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernodetype_detail', args=[self.slug])

    @property
    def member_node_count(self):
        return self.membernode_set.count()


# MemberNode represents a POP/Node of a Tenant.
class MemberNode(ChangeLoggedModel):
    owner = models.ForeignKey(
        to='netbox_sidekick.Member',
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='The name of the node',
        blank=True,
        default='',
    )

    label = models.CharField(
        max_length=255,
        verbose_name='Label',
        help_text='A short name for the node',
        blank=True,
        default='',
    )

    internal_id = models.CharField(
        max_length=255,
        verbose_name='Internal ID',
        help_text='An internal ID for the node',
        blank=True,
        default='',
    )

    latitude = models.FloatField(
        verbose_name='Latitude',
        help_text="Latitude of the node's location",
        blank=True,
        default=0,
    )

    longitude = models.FloatField(
        verbose_name='Longitude',
        help_text="Longitude of the node's location",
        blank=True,
        default=0,
    )

    altitude = models.FloatField(
        verbose_name='Altitude',
        help_text="Altitude of the node's location",
        blank=True,
        default=0,
    )

    address = models.CharField(
        max_length=255,
        verbose_name='Address',
        help_text='A short address of the node',
        blank=True,
        default='',
    )

    node_type = models.ForeignKey(
        to='netbox_sidekick.MemberNodeType',
        on_delete=models.PROTECT,
        verbose_name='Node Type',
    )

    class Meta:
        ordering = ['owner', 'name']

    def __str__(self):
        if self.name == '':
            return self.owner.tenant.description
        else:
            return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernode_detail', args=[self.pk])
