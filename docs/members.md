# Members

## Managing Members

"Members" are organizations who use your services. NetBox has a built-in Tenant
model that manages "tenants" - owners of the resources you manage in NetBox.

Sidekick extends NetBox's tenants with some NREN-specific information such as:

* Types of Members (such as Internet Exchange, K-12 School, Post-Secondary, etc)
* Member information such as their address and contact information.
* Latitude and Longitude for mapping purposes.

In order to manage members in NetBox:

1. First create a Tenant Group in NetBox called "Members".
2. Populate NetBox with "Tenants". The name and description of each Tenant
   should match the member's name as this creates the link/bridge between
   a NetBox Tenant and a Member.

Once your members are populated as "tenants", you can either manually begin
adding Members using the NetBox/Django admin interface or use the import script.

Members are associated with a "Member Type". This is a category of membership
such as K-12, Post-Secondary, etc. You can add member types by using the Django
admin interface. If you import your members, member types will automatically
be created as they are discovered in your CSV file.

## Importing Members

This plugin comes with a command titled `import_members` to help import a CSV
of your member data into NetBox.

By default, this command expects a CSV file to have the following columns:

```
name, category, member_since, invoice_period_start, users, connection, billing_first_name, billing_last_name, billing_title, address_1, city, postal_code, telephone, email, supernet
```

If your CSV file differs, you can modify the import code at
`management/commands/import_members.py`.

The import command has a `--reconcile` flag that will make sure the members
listed in your CSV file match existing tenants in NetBox.

To perform an import, run:

```
cd /opt/netbox/netbox
python manage.py import_members --file /path/to/members.csv --reconcile
python manage.py import_members --file /path/to/members.csv --dry-run
python manage.py import_members --file /path/to/members.csv
```

For an example CSV, see the `members.csv` testing fixture in the
`netbox_sidekick/fixtures` directory.

## Importing Institutions

There's a command called `import_institutions` which reads a CSV file
of the following format:

```
name, latitude, longitude, altitude, address, url, type
```

This data is an amendment to Member data. In our initial data organization,
we have parts of models scattered around, so we have to do multiple
imports in order to create a full model -- in this case, Members.

The import commands should be considered a reference. You will most
likely need to customize them to fit your organization.

# Member Nodes

## Managing Member Nodes

A Member Node is a site/location of a network connection of a member.
Keeping track of member nodes is usually done for reporting and mapping
purposes.

Member Nodes are related to a Member Node Type. This is similar to a
Member Type, but since there can be differences between them, two
different types exist.

You can create Member Node Types in the Django admin interface or they
will automatically be created as they are discovered in a CSV file.

Once Member Node Types are created, you can create Member Nodes, again,
by either using the Django admin interface or by importing a CSV.

## Importing Member Nodes

Similar to importing members, this plugin comes with a command titled
`import_member_nodes` to import a CSV file of your member nodes.

By default, this command expects a CSV file to have the following columns:

```
name, label, internal_id, latitude, longitude, altitude, address, type, owner, co-owner
```

> co-owner is currently ignored.

If your CSV file differs, you can modify the import code at
`management/commands/import_member_nodes.py`.

To perform an import, run:

```
cd /opt/netbox/netbox
python manage.py import_member_nodes --file /path/to/nodes.csv --dry-run
python manage.py import_member_nodes --file /path/to/nodes.csv
```

## Managing Member Node Links

A Member Node Link is a link between two member nodes. Currently, this is
recorded purely for mapping purposes.

A Member Node Link Type exists to store the different kinds of links. This is
because there are, once again, different categories of links that differ
from Member Types and Member Node Types. As usual, you can create Member Node
Link Types from the Django admin interface or they will be automatically
created as they are discovered when importing a CSV file.

Once Member Node Link Types are created, you can create Member Node Links
from the Django admin interface or import a CSV file.

## Importing Member Node Links

Similar to the above, this plugin comes with a command titled
`import_member_node_links` to import a CSV file of your member node links.

By default, this command expects a CSV file to have the following columns:

```
name, label, internal_id, a_endpoint, z_endpoint, type, throughput, owner, co-owner
```

> co-owner is currently ignored.

If your CSV file differs, you can modify the import code at
`management/commands/import_member_node_links.py`.

To perform an import, run:

```
cd /opt/netbox/netbox
python manage.py import_member_node_links --file /path/to/links.csv --dry-run
python manage.py import_member_node_links --file /path/to/links.csv
```
