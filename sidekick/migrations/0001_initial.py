# Generated by Django 4.0.4 on 2022-10-08 01:13

import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('extras', '0073_journalentry_tags_custom_fields'),
        ('tenancy', '0011_standardize_name_length'),
        ('ipam', '0043_add_tenancy_to_aggregates'),
        ('dcim', '0122_standardize_name_length'),
        ('dcim', '0153_created_datetimefield'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogicalSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Logical System',
                'verbose_name_plural': 'Logical Systems',
            },
        ),
        migrations.CreateModel(
            name='NetworkServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Network Service Type',
                'verbose_name_plural': 'Network Service Types',
            },
        ),
        migrations.CreateModel(
            name='RoutingType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Routing Type',
                'verbose_name_plural': 'Routing Types',
            },
        ),
        migrations.CreateModel(
            name='NetworkService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('legacy_id', models.CharField(blank=True, default='', max_length=255)),
                ('start_date', models.DateField(blank=True, default=django.utils.timezone.now, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('comments', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tenancy.tenant')),
                ('network_service_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='network_service_type', to='sidekick.networkservicetype')),
                ('member_site', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dcim.site')),
                ('backup_for', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='sidekick.networkservice')),
            ],
            options={
                'ordering': ['member', 'network_service_type'],
                'verbose_name': 'Network Service',
                'verbose_name_plural': 'Network Services',
            },
        ),
        migrations.CreateModel(
            name='NetworkServiceDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('vlan', models.IntegerField(blank=True, null=True)),
                ('comments', models.TextField(blank=True)),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_devices', to='dcim.device')),
                ('interface', models.CharField(blank=True, max_length=255, null=True)),
                ('network_service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_devices', to='sidekick.networkservice')),
                ('legacy_id', models.CharField(blank=True, default='', max_length=255)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Network Service Device',
                'verbose_name_plural': 'Network Service Devices',
            },
        ),
        migrations.CreateModel(
            name='AccountingSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('destination', models.CharField(max_length=255)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dcim.device')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Accounting Source',
                'verbose_name_plural': 'Accounting Sources',
                'ordering': ['device', 'name', 'destination'],
            },
        ),
        migrations.CreateModel(
            name='AccountingProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('comments', models.TextField(blank=True, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tenancy.tenant')),
                ('accounting_sources', models.ManyToManyField(blank=True, to='sidekick.accountingsource')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Accounting Profile',
                'verbose_name_plural': 'Accounting Profiles',
                'ordering': ['member', 'name'],
            },
        ),
        migrations.AddField(
            model_name='networkservice',
            name='accounting_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='sidekick.accountingprofile'),
        ),
        migrations.AddField(
            model_name='networkservice',
            name='custom_field_data',
            field=models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AddField(
            model_name='networkservice',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags'),
        ),
        migrations.CreateModel(
            name='AccountingSourceCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('scu', models.BigIntegerField(default=0)),
                ('dcu', models.BigIntegerField(default=0)),
                ('accounting_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sidekick.accountingsource')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Accounting Source Counter',
                'verbose_name_plural': 'Accounting Source Counters',
            },
        ),
        migrations.CreateModel(
            name='BandwidthProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('effective_date', models.DateField(blank=True, default=django.utils.timezone.now, null=True)),
                ('comments', models.TextField(blank=True, null=True)),
                ('traffic_cap', models.BigIntegerField(blank=True, null=True)),
                ('burst_limit', models.BigIntegerField(blank=True, null=True)),
                ('accounting_profile', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sidekick.accountingprofile')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Bandwidth Profile',
                'verbose_name_plural': 'Bandwidth Profiles',
                'ordering': ['accounting_profile'],
            },
        ),
        migrations.AlterField(
            model_name='networkservice',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='networkservice',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='NetworkServiceGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('network_services', models.ManyToManyField(to='sidekick.networkservice')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Network Service Group',
                'verbose_name_plural': 'Network Service Groups',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NetworkServiceL2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('vlan', models.IntegerField(blank=True, null=True)),
                ('comments', models.TextField(blank=True)),
                ('legacy_id', models.CharField(blank=True, default='', max_length=255)),
                ('network_service_device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_l2', to='sidekick.networkservicedevice')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Network Service L2',
                'verbose_name_plural': 'Network Services L2',
            },
        ),
        migrations.CreateModel(
            name='NetworkServiceL3',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('asn', models.CharField(blank=True, default='', max_length=255)),
                ('ipv4_unicast', models.BooleanField(default=True)),
                ('ipv4_multicast', models.BooleanField(default=True)),
                ('ipv4_prefixes', models.TextField(blank=True, null=True)),
                ('ipv6_unicast', models.BooleanField(default=False)),
                ('ipv6_multicast', models.BooleanField(default=False)),
                ('ipv6_prefixes', models.TextField(blank=True, null=True)),
                ('comments', models.TextField(blank=True)),
                ('logical_system', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_l3', to='sidekick.logicalsystem')),
                ('member_router_address_ipv4', models.CharField(blank=True, default='', max_length=255)),
                ('member_router_address_ipv6', models.CharField(blank=True, default='', max_length=255)),
                ('provider_router_address_ipv4', models.CharField(blank=True, default='', max_length=255)),
                ('provider_router_address_ipv6', models.CharField(blank=True, default='', max_length=255)),
                ('routing_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_l3', to='sidekick.routingtype')),
                ('legacy_id', models.CharField(blank=True, default='', max_length=255)),
                ('network_service_device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_l3', to='sidekick.networkservicedevice')),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Network Service L3',
                'verbose_name_plural': 'Network Services L3',
            },
        ),
        migrations.CreateModel(
            name='NIC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('admin_status', models.IntegerField(default=True)),
                ('oper_status', models.IntegerField(default=True)),
                ('out_octets', models.BigIntegerField(default=0)),
                ('in_octets', models.BigIntegerField(default=0)),
                ('out_unicast_packets', models.BigIntegerField(default=0)),
                ('in_unicast_packets', models.BigIntegerField(default=0)),
                ('out_nunicast_packets', models.BigIntegerField(default=0)),
                ('in_nunicast_packets', models.BigIntegerField(default=0)),
                ('out_errors', models.BigIntegerField(default=0)),
                ('in_errors', models.BigIntegerField(default=0)),
                ('interface', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nic', to='dcim.interface')),
                ('in_rate', models.BigIntegerField(default=0)),
                ('out_rate', models.BigIntegerField(default=0)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='extras.TaggedItem', to='extras.Tag', verbose_name='Tags')),
            ],
            options={
                'ordering': ['interface__device__name', 'interface__name'],
                'verbose_name': 'NIC',
                'verbose_name_plural': 'NICs',
            },
        ),
    ]
