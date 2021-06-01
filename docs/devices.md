# Devices

Sidekick does not extend or override NetBox devices. However, Sidekick makes
extensive use of devices both for inventory purposes and day-to-day
operations. Therefore, it's important to understand how to add and manage
devices in a way compatible with Sidekick.

Adding all details about a network device can be tedious. Sidekick attempts to
help with this by automating some parts.

## NetBox Secrets

In order to help with this automation, you'll need to have NetBox configured to
store Secrets. Documentation about that can be found
[here](https://netbox.readthedocs.io/en/stable/core-functionality/secrets/).

It's best if you create two User Keys. The first User Key is used to
approve/activate additional keys. This should be considered more of an admin
action. Store the details about this user's keys in a safe place.

The second User Key should be assigned to a "dummy" user in NetBox called,
for example, `network`. Create a private/public key pair for this user and
store it somewhere on the server where NetBox is running (for example,
`/opt/netbox/.ssh/id_rsa` and `/opt/netbox/.ssh/id_rsa.pub`).

Once this is configured, add the following to your NetBox configuration file:

```
PLUGINS_CONFIG = {
    'sidekick': {
        'secret_user': 'network',
        'secret_private_key_path': '/opt/netbox/.ssh/id_rsa',
    }
}
```

This will allow the Sidekick management commands to decrypt secrets on
behalf of the `network` user.

## Adding a Device

To add a device, do the following:

1. In the NetBox web interface, add a new device like normal.
   * Give the device a unique name.
   * Set the Site and Rack location.
   * Set the Device Type.
   * Set the Platform to the Network Operating System of the device.

2. Once this basic information is added, you'll next want to add two Secrets.
   * In the Device details page, click the "Add secret" button.
   * Add a Secret of type "SNMPv2 Community" with a name of "snmp" and data
     of the SNMP community that can be used to connect to the device using SNMP.

## Configuring a Device

You should now have a device with some basic information and some Secrets. You
can now use a built-in Sidekick management command that will do the following:

* Create an interface called "mgmt" and assign it an IP address used to connect
  to the device via SNMP.
* Assign that IP address as the Primary IPv4 address of the device.

You can do this through the web interface, but this may be a little faster.

To run this command, do the following:

```
cd /opt/netbox/netbox
source /opt/netbox/venv/bin/activate
python manage.py configure_device --name "Main Router" --ip 192.168.1.1/24 --dry-run
python manage.py configure_device --name "Main Router" --ip 192.168.1.1/24
```

The `--dry-run` argument will perform a dry run / no-op and report some of
the actions that will happen.

> Note: The code for this command can be found at
> `sidekick/management/commands/configure_device.py` if you need to
> customize it.

# NICs

A NIC is a one-to-one relationship with a Device's Interface. The purpose of
this is to extend the attributes/properties of an Interface without directly
modifying NetBox itself.

A NIC represents some operational properties of an Interface such as if the
device is "up", enabled, and various counters of the Interface that can be
used for metrics.

Importing this information is done via SNMP and requires a device to have
some key "Secrets" configured. See the above section on Devices for how to
do this.

Once these secrets have been added to a device, you can run a command called
`update_interfaces` to import the operational data about an interface.

This data is meant to be imported periodically, such as every 5 or 10 minutes.
The data will only be recorded in NetBox/Sidekick once. The last 5 updates
of each NIC are kept. Older updates are discarded. This allows you to work with
prior updates, for example to get the rate of change for storing in metrics.

You are then expected to have external monitoring and graphing services, such
as Sensu and Graphite, query for this data and store it in a more approprite
time-series fashion.

To import status and counter details for each interface of a device, run the
following commands:

```
cd /opt/netbox/netbox
source /opt/netbox/venv/bin/activate
python manage.py update_interfaces --device-name "Main Router"
```

"Main Router" is the unique name of the device in NetBox.

It's best to configure this command to be run via Cron or something similar.

## API Access

NIC information is available via REST API. This allows you to configure a
monitoring or metric system to query NetBox for NIC information. For example,
you can create alerts if an Interface/NIC is down or you can import
TX and RX counters into a graphing service.

To query via the API, run something like the following:

```
curl https://netbox.example.com/api/plugins/sidekick/nics/device/<ID>/?name=<NIC> -H "Authorization: Token <token>"
```

Where `ID` is the Device ID (such as 3) and `NIC` is the name of the
NIC (such as `ge-0/2/0`).

## Graphite Support

Using the API access, you can create a separate, decoupled script to query
NetBox for the NIC information. In addition to this, Sidekick supports sending
NIC metrics directly to Graphite. To enable this, add the following to your
NetBox configuration file:

```
PLUGINS_CONFIG = {
    'sidekick': {
        'graphite_host': 'graphite.exaple.com',
    }
}
```

> NOTE: You may have other settings already defined. If so, do not remove them.
> Instead, amend the `graphite_host` option to the set.

Once this has been added, the `update_interfaces` script will automatically send
metric information to Graphite.

> NOTE: By default, the `update_interfaces` script will store the _difference_
of the past two updates -- in other words, the rate of change. Traditionally,
Graphite would store the current counter values of the different metrics and then
determine the rate of change using the `deviate` function. However, the rate of
change is stored due to legacy configuration at Cybera. You can modify the
`update_interfaces` script as needed if you prefer to have the counters stored
instead of the difference.
