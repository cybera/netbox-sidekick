# Generated by Django 3.0.8 on 2020-09-10 03:48

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dcim', '0106_role_default_color'),
        ('tenancy', '0009_standardize_description'),
        ('auth', '0011_update_proxy_permissions'),
        ('ipam', '0036_standardize_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('title', models.CharField(blank=True, default='', max_length=255)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('phone', models.CharField(blank=True, default='', max_length=255)),
                ('comments', models.TextField(blank=True, default='')),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='ContactType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('billing_exempt', models.BooleanField(default=False)),
                ('start_date', models.DateField(blank=True, default=django.utils.timezone.now)),
                ('invoice_period_start', models.CharField(blank=True, default='', max_length=255)),
                ('number_of_users', models.IntegerField(blank=True, default=0)),
                ('billing_address_1', models.CharField(blank=True, default='', max_length=255)),
                ('billing_address_2', models.CharField(blank=True, default='', max_length=255)),
                ('billing_city', models.CharField(blank=True, default='', max_length=255)),
                ('billing_postal_code', models.CharField(blank=True, default='', max_length=255)),
                ('billing_province', models.CharField(blank=True, default='', max_length=255)),
                ('billing_country', models.CharField(blank=True, default='', max_length=255)),
                ('url', models.URLField(blank=True, default='')),
                ('supernet', models.BooleanField(blank=True, default=True)),
                ('latitude', models.FloatField(blank=True, default=0)),
                ('longitude', models.FloatField(blank=True, default=0)),
                ('comments', models.TextField(blank=True, default='')),
                ('auth_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='auth.Group')),
            ],
            options={
                'ordering': ['member_type', 'tenant'],
            },
        ),
        migrations.CreateModel(
            name='MemberNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('label', models.CharField(blank=True, default='', max_length=255)),
                ('internal_id', models.CharField(blank=True, default='', max_length=255)),
                ('latitude', models.FloatField(blank=True, default=0)),
                ('longitude', models.FloatField(blank=True, default=0)),
                ('altitude', models.FloatField(blank=True, default=0)),
                ('address', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'ordering': ['owner', 'name'],
            },
        ),
        migrations.CreateModel(
            name='MemberNodeLinkType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MemberNodeType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MemberType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NetworkServiceConnectionType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MemberNodeLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('label', models.CharField(blank=True, default='', max_length=255)),
                ('internal_id', models.CharField(blank=True, default='', max_length=255)),
                ('throughput', models.FloatField(blank=True, default=0)),
                ('a_endpoint', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='a_endpoint', to='netbox_sidekick.MemberNode')),
                ('link_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.MemberNodeLinkType')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.Member')),
                ('z_endpoint', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='z_endpoint', to='netbox_sidekick.MemberNode')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='membernode',
            name='node_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.MemberNodeType'),
        ),
        migrations.AddField(
            model_name='membernode',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.Member'),
        ),
        migrations.CreateModel(
            name='MemberContact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.Contact')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.Member')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.ContactType')),
            ],
            options={
                'ordering': ['member', 'contact', 'type'],
            },
        ),
        migrations.AddField(
            model_name='member',
            name='member_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.MemberType'),
        ),
        migrations.AddField(
            model_name='member',
            name='tenant',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='tenancy.Tenant'),
        ),
        migrations.CreateModel(
            name='LogicalSystem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='RoutingType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NetworkServiceConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('start_date', models.DateField(blank=True, default=django.utils.timezone.now)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('comments', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('asn', models.CharField(blank=True, default='', max_length=255)),
                ('ipv4_unicast', models.BooleanField(default=True)),
                ('ipv4_multicast', models.BooleanField(default=True)),
                ('ipv4_prefixes', models.TextField(blank=True, null=True)),
                ('ipv6_unicast', models.BooleanField(default=False)),
                ('ipv6_multicast', models.BooleanField(default=False)),
                ('ipv6_prefixes', models.TextField(blank=True, null=True)),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_services', to='dcim.Device')),
                ('interface', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_services', to='dcim.Interface')),
                ('logical_system', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_connections', to='netbox_sidekick.LogicalSystem')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='netbox_sidekick.Member')),
                ('member_router_address_ipv4', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='member_router_address_ipv4', to='ipam.IPAddress')),
                ('member_router_address_ipv6', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='member_router_address_ipv6', to='ipam.IPAddress')),
                ('network_service_connection_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='network_service_connection', to='netbox_sidekick.NetworkServiceConnectionType')),
                ('provider_router_address_ipv4', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='provider_router_address_ipv4', to='ipam.IPAddress')),
                ('provider_router_address_ipv6', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='provider_router_address_ipv6', to='ipam.IPAddress')),
                ('routing_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='network_service_connections', to='netbox_sidekick.RoutingType')),
            ],
            options={
                'ordering': ['member', 'network_service_connection_type'],
            },
        ),
    ]
