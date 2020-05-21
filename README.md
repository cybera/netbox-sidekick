# netbox-sidekick

> This plugin is in heavy development and will have breaking changes.
> There's a good chance this plugin might not end up being used long-term,
> either. Please use at your own risk.

# Table of Contents

> General

* [Introduction](#introduction)
* [Installation](#installation)

> Members

* [Managing Members](#managing-members)
* [Importing Members](#importing-members)

> Member Nodes

* [Managing Member Nodes](#managing-member-nodes)
* [Importing Member Nodes](#importing-member-nodes)
* [Managing Member Node Links](#managing-member-node-links)
* [Importing Member Node Links](#importing-member-node-links)

> Development

* [Development Guidelines](#development-guidelines)

# Introduction

This plugin contains various Django models and tools that extends NetBox
to help you manage an NREN. A lot of this functionality is very specific
to managing an NREN - specifically, how Cybera manages its members and
devices.

The models in this plugin reference the core NetBox models but do not
override or customize them. For example: instead of extending NetBox's
"tenant" models with additional information that would be useful for
membership management, this plugin has a Member model with has a
one-to-one relationship with a NetBox tenant. This way, you can still
use NetBox's tenant feature to apply ownership to different devices and
services, but have NREN-specific details safely decoupled in the Member
model.

We've opted to use a plugin instead of using NetBox's custom fields for
the following reasons:

1. Custom fields can't easily handle one-to-many relationships. For
   example, a Tenant/Member can subscribe to multiple services.

2. Keeping all data localized to a plugin makes it easier to
   revert/remove this later on without destroying your existing NetBox
   environment.

# Installation

> Current development instructions:

1. Have a working [NetBox](https://netbox.readthedocs.io/en/stable/) installation.

2. Clone the `netbox-sidekick` repo somewhere on the NetBox server:

```shell
$ cd /opt
$ git clone https://github.com/cybera/netbox-sidekick
```

3. Install it:

```shell
$ cd netbox-sidekick
$ python setup.py develop
```

4. Follow the Post-Install instructions

> Future stable instructions:

1. Have a working [NetBox](https://netbox.readthedocs.io/en/stable/) installation.

2. Add `netbox-sidekick` to `local_requirements.txt` in the root of the NetBox
installation directory.

3. Install the requirements:

```shell
$ pip install -r local_requirements.txt
```

4. Follow the Post-Install instructions

> Post-Install instructions

1. Modify the NetBox `configuration.py` file to enable the plugin:

```
PLUGINS = [
  'netbox_sidekick',
]
```

2. Install the migrations:

```shell
$ cd /opt/netbox/netbox
$ python manage.py migrate netbox_sidekick
```

3. Restart NetBox:

```shell
$ sudo service netbox restart
$ sudo service netbox-rq restart
```

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
cd /opt/netboox/netbox
python manage.py import_members --file /path/to/members.csv --reconcile
python manage.py import_members --file /path/to/members.csv --dry-run
python manage.py import_members --file /path/to/members.csv
```

For an example CSV, see the `members.csv` testing fixture in the
`netbox_sidekick/fixtures` directory.

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

# Development Guidelines

## Use Flake8

Use [Flake8](https://flake8.pycqa.org/en/latest/) for a standard code style.
At the moment, we're ignoring W504 and E501. We're not monsters.

For `vim` and Syntastic:

```
let g:syntastic_python_checkers = ['flake8']
let g:syntastic_python_flake8_post_args='--ignore=W504,E501'
```

## Add unit tests where possible

Unit tests are stored in the `netbox_sidekick/tests` directory. Files begin
with `test_`.

To test the files, run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py test netbox_sidekick
```

## Update migrations when required

If you make any changes to `models.py`, you will need to generate a new set of
migrations.

First make sure you have the following in `configuration.py`:

```
DEVELOPER = True
```

Then run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py makemigrations netbox_sidekick
```
