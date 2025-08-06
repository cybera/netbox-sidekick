# Members

## Managing Members

"Members" are organizations who use your services. Sidekick leverages NetBox's
"tenants" to store members.

Sidekick requires there to be a Tenant Group called "Members" as well as
the following custom fields attached to the Tenant model:

* member_type
* crm_id
* active

These requirements can be created automatically by running the `setup_sidekick`
command:

```shell
cd /opt/netbox/netbox
python manage.py setup_sidekick --dry-run
```

Once these requirements are satisfied, you can begin adding Members
to NetBox by manually creating them by choosing from the top
menu: Organization > Tenants

## Member Sites

In addition to having one member per tenant, Sidekick also expects that
each member also has a Site with the same name as the member.

Currently, you have to manually create each Site.
