# Membership Mapping

Sidekick can generate a GRENML-based file for creating a map of the NREN's membership.

In order to configure Sidekick to do this, do the following steps:

## Custom Fields

As detailed in the [Install](install.md) doc, the `setup_sidekick` script will create
several custom fields. The following fields are used for mapping:

* `latitude`: This custom field is added to Tenants and Devices and is used to record
  the latitude of a tenant's location and of a network device.
* `longitude`: Similar to the `latitude` field, but for longitude.
* `primary_map_node`: This custom field is added to Devices and is used to designate
  a single device as the center of your map.
* `map_label`: This custom field is added to Devices and is used to provide a friendly
  description of a device for a map.

## Adding Data

Modify the NetBox `configuration.py` file and add the following setting:

```
PLUGINS_CONFIG = {
    'netbox_sidekick': {
				'mapping_primary_owner': 'Your NREN Name',
        ...
    }
}
```

"Your NREN Name" should be a Tenant that you've added to NetBox to represent yourself.

While you are adding Tenants to NetBox (as detailed in the [Members](members.md) doc), also add their latitude and longitude. This will be used to plot their locations on a map.

Next, as you are adding Devices to NetBox, do the following:

* For any Device (such as a router) that represents a PoP of your NREN, add the latitude
  and longitude of the PoP's location.
* For one Device (such as a router) that represents the primary PoP of your NREN, set
  `primary_map_node` to "True". All other PoPs will then point to this primary node.
* Optionally, for any Device, fill in the `map_label` field and specify a friendly name
  for the map location. For example, instead of "Calgary Core Router", which represents
  the router of the Calgary PoP, you can set `map_label` to "Calgary" and have that
  displayed in the map.

## Adding Network Services

As you add [Network Services](network_services.md) to Sidekick/NetBox, make sure that
each service ultimately points to a Device located in one of your PoPs.

One this has been done for all of your members' services, all pieces are now in place
to generate a map of membership.

## Generating the GRENML File

The GRENML file is generated via an API call:

```
curl https://netbox.example.com/api/plugins/sidekick/map/ -H "Authorization: Token <token>"
```
