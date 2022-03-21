# Accounting

Accounting refers to tracking and limiting a member's bandwidth.

Sidekick currently supports the following accounting features:

* Importing SCU/DCU accounting sources from a Juniper router.
* Importing SCU/DCU statistics about each accounting source.
* Creating a "Bandwidth Profile" for each member which records their bandwidth limit.
* Creating "Accounting Profiles" which ties together one or more SCU/DCU accounting
  sources and a "Bandwidth Profile"
* Displaying basic tables and filters about Accounting Profiles and Bandwidth Profiles.


## Importing Accounting Sources

There are two ways to import Accounting Sources:

1. Manually through the Django Admin page.
2. Using the import script.

### Import Script

It's best to have the import script run at a regular interval, similar to the
`update_interfaces` script.

To run this script, you need to have NetBox and Sidekick configured with credentials
as described in the [Devices](./devices.md) doc. Once configured, you can run the
script by doing the following:

```
cd /opt/netbox/netbox
source /opt/netbox/venv/bin/activate
python manage.py scu_dcu --name "Main Router" --dry-run
python manage.py scu_dcu --name "Main Router"
```

## Accounting Profiles and Bandwidth Profiles

To create Accounting Profiles and Bandwidth Profiles, use the Django Admin interface.

1. First, click on "Add" next to Accounting Profiles.
2. Select the Member from the drop-down box.
3. (Optional) Give the profile a name. If no name is given, the profile is referred
  to by the member's name.
4. Add any comments.
5. Select one or more Accounting Sources.
6. Click "Add another Bandwidth Profile".
7. Fill out the Traffic Cap, Burst Limit, Effective Date, and any comments.
