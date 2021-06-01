# Membership Mapping

Sidekick can generate a GRENML-based file for creating a map of the NREN's membership.

In order to configure Sidekick to do this, do the following steps:

## Members and Sites

Make sure you have added all of your members as Tenants and have created one Site
for each member, with the Site having the same name as the member.

Also make sure that the Site has the latitude and longitude values populated.

Use the Site's "description" field to specify an alertnative name that will be
used in the map. For example, if your Site is called "Member's New Data Centre"
but you'd prefer the map to have "Member's Data Centre", put the latter name
as a description.

## Adding Data

Modify the NetBox `configuration.py` file and add the following setting:

```
PLUGINS_CONFIG = {
    'sidekick': {
        'mapping_primary_owner': 'Your NREN Name',
        'mapping_primary_site': 'Your Main Site',
        ...
    }
}
```

"Your NREN Name" should be a Tenant that you've added to NetBox to represent yourself.

"Your Main Site" should be the name or description of the Site you've added to NetBox
to represent yourself.

## Adding Network Services

As you add [Network Services](network_services.md) to Sidekick/NetBox, make sure that
each service ultimately points to a Device located in one of your PoPs (Sites).

One this has been done for all of your members' services, all pieces are now in place
to generate a map of membership.

## Generating the GRENML File

The GRENML file is generated via an API call:

```
curl https://netbox.example.com/api/plugins/sidekick/map/ -H "Authorization: Token <token>"
```

## Testing on the Command Line

You can also test map generation on the command-line:

```
$ python manage.py gren_map
```
