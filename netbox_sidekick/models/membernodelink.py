from django.db import models
from django.urls import reverse

from utilities.models import ChangeLoggedModel


# MemberNodeLinkType represents a type of member node link.
class MemberNodeLinkType(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Type',
        help_text='A type to represent a group of members node links',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernodelinktype_detail', args=[self.slug])

    @property
    def member_node_link_count(self):
        return self.membernodelink_set.count()


# MemberNodeLink represents a link between two member nodes.
class MemberNodeLink(ChangeLoggedModel):
    owner = models.ForeignKey(
        to='netbox_sidekick.Member',
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='The name of the node link',
        blank=True,
        default='',
    )

    label = models.CharField(
        max_length=255,
        verbose_name='Label',
        help_text='A short name for the node link',
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

    link_type = models.ForeignKey(
        'netbox_sidekick.MemberNodeLinkType',
        on_delete=models.PROTECT,
    )

    a_endpoint = models.ForeignKey(
        'netbox_sidekick.MemberNode',
        verbose_name='A Endpoint',
        related_name='a_endpoint',
        on_delete=models.PROTECT,
    )

    z_endpoint = models.ForeignKey(
        'netbox_sidekick.MemberNode',
        verbose_name='Z Endpoint',
        related_name='z_endpoint',
        on_delete=models.PROTECT,
    )

    throughput = models.FloatField(
        verbose_name='Throughput',
        help_text="Gigabits per second",
        blank=True,
        default=0,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.name == '':
            return self.owner.description
        else:
            return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernodelink_detail', args=[self.pk])
