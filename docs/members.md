# Members

## Managing Members

"Members" are organizations who use your services. Sidekick leverages NetBox's
"tenants" to store members.

Sidekick requires there to be a Tenant Group called "Members" as well as
the following custom fields attached to the Tenant model:

* member_type
* latitude
* longitude
* crm_id
* active

These requirements can be created automatically by running the `setup_sidekick`
command:

```shell
cd /opt/netbox/netbox
python manage.py setup_sidekick --dry-run
```

Once these requirements are satisfied, you can begin adding Members
to NetBox in one of two ways:

1. Manually creating them by choosing from the top menu: Organization > Tenants
2. Running an import script.

## Importing Members via a Script

This plugin comes with a command titled `import_members` to help import a CSV
of your member data into NetBox.

By default, this command expects a CSV file to have the following columns:

```
name, description, member type, comment, latitude, longitude
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
