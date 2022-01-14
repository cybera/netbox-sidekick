import graphyte
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from dcim.choices import InterfaceModeChoices, InterfaceTypeChoices
from dcim.models import Device, Interface

from ipam.models import IPAddress

from sidekick.models import (
    NetworkServiceDevice,
    NIC,
)

from sidekick.utils import (
    VALID_INTERFACE_NAMES,
    decrypt_secret,
    snmpwalk_bulk,
)


RE_ARISTA_VLAN = re.compile(r'^Vlan(\d+)$')

IP_VERSIONS = {
    'ipv4': 4,
    'ipv6': 6,
}

METRIC_CATEGORIES = [
    'in_octets', 'out_octets',
    'in_unicast_packets', 'out_unicast_packets',
    'in_nunicast_packets', 'out_nunicast_packets',
    'in_errors', 'out_errors',
]


class Command(BaseCommand):
    help = "Update Interface/NIC data on a device"

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-name', required=True, help='The name of the device')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        # First, query for the device by name.
        try:
            device = Device.objects.get(name=options['device_name'])
        except Device.DoesNotExist:
            self.stdout.write(f"Unable to find device: {options['device_name']}")
            return

        # Determine the information needed to connect to the device.
        mgmt_ip = device.primary_ip4
        secret_username = settings.PLUGINS_CONFIG['sidekick'].get('secret_user', None)
        private_key_path = settings.PLUGINS_CONFIG['sidekick'].get('secret_private_key_path', None)

        # If all of the connection information was found,
        # attempt to decrypt the connection credentials,
        # connect to the device, and inventory the interfaces.
        if mgmt_ip is not None and \
           secret_username is not None and \
           private_key_path is not None:

            _mgmt_ip = "%s" % (mgmt_ip.address.ip)

            try:
                snmp = decrypt_secret(device, 'snmp', secret_username, private_key_path)
            except Exception as e:
                self.stdout.write(f"Unable to decrypt snmp secret: {e}")

            if snmp is None:
                self.stdout.write(f"Unable to find snmp secret for {device}")
                return

            try:
                device_info = snmpwalk_bulk(_mgmt_ip, snmp)
                # device_info = get_device_info_via_snmp(_mgmt_ip, snmp)
            except Exception as e:
                self.stdout.write(f"Error querying device {device}: {e}")
                return

            # If we're able to connect,
            # build a list of interface names already on the device.
            existing_interfaces = {}
            for i in device.vc_interfaces():
                existing_interfaces[i.name] = i

            # Obtain the list of interfaces.
            # For each device that is not supposed to be ignored,
            # add that interface to the device if it doesn't already exist.
            for iface_index, iface_details in device_info.items():
                iface_name = iface_details.get('ifName', None)
                if iface_name is None:
                    continue
                # self.stdout.write(f"{iface_details['name']}: {iface_details['oper_status']}")
                # continue

                if not any(i in iface_details['ifName'] for i in VALID_INTERFACE_NAMES):
                    continue

                iface_type = InterfaceTypeChoices.TYPE_VIRTUAL
                if iface_details['ifHighSpeed'] == 1000:
                    iface_type = InterfaceTypeChoices.TYPE_1GE_FIXED
                if iface_details['ifHighSpeed'] == 10000:
                    iface_type = InterfaceTypeChoices.TYPE_10GE_FIXED
                if iface_details['ifHighSpeed'] == 'ieee8023adLag':
                    iface_type = InterfaceTypeChoices.TYPE_LAG

                # TODO: VLAN management is incomplete right now.
                # _vlan = None
                iface_mode = InterfaceModeChoices.MODE_TAGGED
                if '.' in iface_name:
                    iface_mode = InterfaceModeChoices.MODE_ACCESS
                    # _vlan = iface_name.split('.')[1]
                if 'Vlan' in iface_name:
                    iface_mode = InterfaceModeChoices.MODE_ACCESS
                #     m = RE_ARISTA_VLAN.search(iface_name)
                #     if m:
                #         _vlan = m.group(1)

                iface_untagged_vlan = None
                # if _vlan is not None:
                #     try:
                #         iface_untagged_vlan = VLAN.objects.get(vid=_vlan)
                #     except VLAN.MultipleObjectsReturned:
                #         self.stdout.write(f"WARNING: Multiple results found for VLAN {_vlan}. Not setting VLAN.")
                #     except VLAN.DoesNotExist:
                #         self.stdout.write(f"WARNING: No results found for VLAN {_vlan}. Not setting VLAN.")

                # If the interface already exists, update a few fields.
                # We do not update the interface type because that could have
                # been updated in NetBox directly to something more specific/better
                # than what SNMP can can determine.
                if iface_name in existing_interfaces.keys():
                    existing_interface = existing_interfaces[iface_name]

                    changed = False
                    _descr = iface_details['ifAlias'].strip()
                    if existing_interface.description != _descr:
                        existing_interface.description = _descr
                        changed = True

                    admin_status = f"{iface_details['ifAdminStatus']}"
                    if admin_status == "up":
                        admin_status = 1
                    if admin_status == "down":
                        admin_status = 0

                    iface_status = False
                    oper_status = iface_details['ifOperStatus']
                    if admin_status == 1 and oper_status == 1:
                        iface_status = True
                    if existing_interface.enabled != iface_status:
                        existing_interface.enabled = iface_status
                        changed = True

                    if existing_interface.untagged_vlan != iface_untagged_vlan:
                        existing_interface.untagged_vlan = iface_untagged_vlan
                        changed = True

                    if changed is True:
                        if options['dry_run']:
                            self.stdout.write(f"Would have updated {iface_name}")
                        else:
                            existing_interface.save()

                if iface_name not in existing_interfaces.keys():
                    if options['dry_run']:
                        self.stdout.write(f"Would have added {iface_name}")
                    else:
                        admin_status = f"{iface_details['ifAdminStatus']}"
                        if admin_status == "down":
                            admin_status = False
                        if admin_status == "up":
                            admin_status = True

                        mtu = iface_details.get('ifMtu', 0)
                        if 'No more variables' in f"{mtu}":
                            mtu = 0

                        iface = Interface(
                            device=device,
                            description=iface_details.get('ifDescr', None),
                            name=iface_name,
                            type=iface_type,
                            enabled=admin_status,
                            mac_address=iface_details.get('ifPhysAddress', None),
                            mtu=mtu,
                            mode=iface_mode,
                            untagged_vlan=iface_untagged_vlan,
                        )
                        iface.save()

            # To account for one or more new interfaces being added,
            # build a list of interface names already on the device.
            existing_interfaces = {}
            for i in device.vc_interfaces():
                existing_interfaces[i.name] = i

            # Obtain the list of IP addresses on each interface.
            # For each interface that is not supposed to be ignored,
            # add the IP address to the interface if it doesn't already exist.
            for iface_index, iface_details in device_info.items():
                iface_name = iface_details.get('ifName', None)
                if iface_name is None:
                    continue

                if not any(i in iface_name for i in VALID_INTERFACE_NAMES):
                    continue

                if iface_name not in existing_interfaces.keys():
                    continue

                existing_interface = existing_interfaces[iface_name]
                existing_ip_addresses = existing_interface.ip_addresses.all()

                for version, family in IP_VERSIONS.items():
                    if version not in iface_details.keys():
                        continue

                    if iface_details[version] is None:
                        continue

                    # Check if an IP was removed from the device.
                    # If so, then delete it from NetBox.
                    for existing_ip in existing_ip_addresses:
                        if existing_ip.family == family:
                            if f"{existing_ip}" not in iface_details[version]:
                                if options['dry_run']:
                                    self.stdout.write(
                                        f"Would have removed {existing_ip} from {iface_name}")
                                else:
                                    existing_ip.assigned_object = None
                                    existing_ip.description = f"Previously assigned to {options['device_name']} on interface {iface_name}"
                                    existing_ip.save()

                    # Check if an IP needs to be added to NetBox.
                    for interface_ip in iface_details[version]:
                        # If the IP polled from the device is not in the NetBox device interface...
                        if not any(interface_ip == f"{_ip}" for _ip in existing_ip_addresses):
                            try:
                                ip = IPAddress.objects.get(address=interface_ip)
                                if ip.assigned_object is not None and ip.assigned_object.id != existing_interface.id:
                                    # If the IP being reported is the management IP, then ignore.
                                    # This is because we want to standardize on the name of the
                                    # management interface, even if the IP address is on a different
                                    # interface. This isn't ideal and should be improved in the
                                    # future.
                                    if ip == mgmt_ip:
                                        continue

                                    # Also ignore private IP addresses since they can be
                                    # reused in different locations. Again, this isn't ideal and
                                    # should be improved in the future.
                                    if f"{ip}".startswith("10.") or f"{ip}".startswith("172.") or f"{ip}".startswith("192."):
                                        continue

                                    # If the IP assignment is on the same device, we will assume
                                    # a reconfiguration was made. In this case, we reassign the
                                    # IP.
                                    if ip.assigned_object.device.name == existing_interface.device.name:
                                        ip.assigned_object = existing_interface
                                        ip.save()
                                        continue

                                    self.stdout.write(
                                        f"IP Address {interface_ip} is already assigned to "
                                        f"{ip.assigned_object.name} on {ip.assigned_object.device.name}. "
                                        f"Will not assign to {existing_interface.name} on "
                                        f"{existing_interface.device.name}")
                                    continue
                                # Otherwise, add the IP to the interface.
                                else:
                                    if options['dry_run']:
                                        self.stdout.write(
                                            f"Would have added {interface_ip} to {existing_interface.name}")
                                    else:
                                        if ip.description != existing_interface.description:
                                            ip.description = existing_interface.description
                                        ip.assigned_object = existing_interface
                                        ip.save()
                            except IPAddress.MultipleObjectsReturned:
                                self.stdout.write(f"WARNING: Multiple results found for IP {interface_ip}. Skipping.")
                                continue
                            except IPAddress.DoesNotExist:
                                if options['dry_run']:
                                    self.stdout.write(
                                        f"Would have created IP address {interface_ip} and added it to " +
                                        f"{existing_interface.name}")
                                else:
                                    ip = IPAddress(
                                        address=interface_ip,
                                        description=existing_interface.description)
                                    ip.save()

                                    existing_interface.ip_address = ip
                                    existing_interface.save()

            # Obtain the counters on each interface.
            # For each interface that is not supposed to be ignored,
            # store the counters as a NIC object.
            for iface_index, iface_details in device_info.items():
                iface_name = iface_details.get('ifName', None)
                if iface_name is None:
                    continue

                if not any(i in iface_name for i in VALID_INTERFACE_NAMES):
                    continue

                if iface_name not in existing_interfaces.keys():
                    continue

                existing_interface = existing_interfaces[iface_name]
                if options['dry_run']:
                    self.stdout.write(f"Would have updated counters for {existing_interface.name}: {iface_details}")
                else:
                    admin_status = iface_details.get('ifAdminStatus', 0)
                    if 'No more variables' in f"{admin_status}":
                        admin_status = 0

                    oper_status = iface_details.get('ifOperStatus', 0)
                    if 'No more variables' in f"{oper_status}":
                        oper_status = 0

                    out_octets = iface_details.get('ifHCOutOctets', 0)
                    if 'No more variables' in f"{out_octets}":
                        out_octets = 0

                    in_octets = iface_details.get('ifHCInOctets', 0)
                    if 'No more variables' in f"{in_octets}":
                        in_octets = 0

                    out_unicast_packets = iface_details.get('ifHCOutUcastPkts', 0)
                    if 'No more variables' in f"{out_unicast_packets}":
                        out_unicast_packets = 0

                    in_unicast_packets = iface_details.get('ifHCInUcastPkts', 0)
                    if 'No more variables' in f"{in_unicast_packets}":
                        in_unicast_packets = 0

                    out_nunicast_packets = iface_details.get('ifOutNUcastPkts', 0)
                    if 'No more variables' in f"{out_nunicast_packets}":
                        out_nunicast_packets = 0

                    in_nunicast_packets = iface_details.get('ifInNUcastPkts', 0),
                    if 'No more variables' in f"{in_nunicast_packets}":
                        in_nunicast_packets = 0

                    out_errors = iface_details.get('ifOutErrors', 0)
                    if 'No more variables' in f"{out_errors}":
                        out_errors = 0

                    in_errors = iface_details.get('ifInErrors', 0)
                    if 'No more variables' in f"{in_errors}":
                        in_errors = 0

                    nic = NIC(
                        interface=existing_interface,
                        interface_id=existing_interface.id,
                        admin_status=admin_status,
                        oper_status=oper_status,
                        out_octets=out_octets,
                        in_octets=in_octets,
                        out_unicast_packets=out_unicast_packets,
                        in_unicast_packets=in_unicast_packets,
                        out_nunicast_packets=out_nunicast_packets,
                        in_nunicast_packets=in_unicast_packets,
                        out_errors=out_errors,
                        in_errors=in_errors,
                    )

                    if 'in_rate' in iface_details:
                        nic.in_rate = iface_details['in_rate']
                    if 'out_rate' in iface_details:
                        nic.out_rate = iface_details['out_rate']

                    nic.save()

                # Send the metrics to Graphite if graphite_host has been set.
                graphite_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_host', None)
                if graphite_host is not None:
                    graphyte.init(graphite_host)

                    # Determine the difference between the last two updates.
                    # This is because Cybera's metrics were previously stored in RRD
                    # files which only retains the derivative and not what the actual
                    # counters were.
                    previous_entries = NIC.objects.filter(
                        interface_id=existing_interface.id).order_by('-last_updated')
                    if len(previous_entries) < 2:
                        continue

                    e1 = previous_entries[0]
                    e2 = previous_entries[1]
                    total_seconds = (e1.last_updated - e2.last_updated).total_seconds()

                    graphite_prefix = "{}.{}".format(
                        e1.graphite_device_name(), e1.graphite_interface_name())

                    for cat in METRIC_CATEGORIES:
                        m1 = getattr(e1, cat, None)
                        m2 = getattr(e2, cat, None)
                        if m1 is not None and m2 is not None:
                            diff = (m1 - m2)

                            if diff != 0:
                                diff = diff / total_seconds
                            graphite_name = f"{graphite_prefix}.{cat}"
                            if options['dry_run']:
                                self.stdout.write(f"{graphite_name} {diff} {total_seconds}")
                            else:
                                graphyte.send(graphite_name, diff)

                    # Determine if the interface is part of a member's network service.
                    # If so, send a second set of metrics to Graphite with a prefix
                    # dedicated to that service.
                    try:
                        nsd = NetworkServiceDevice.objects.get(
                            device=device, interface=existing_interface.name,
                            network_service__active=True)
                    except NetworkServiceDevice.MultipleObjectsReturned:
                        self.stdout.write(f"Multiple results found for network service using "
                                          f"{device} {existing_interface.name}")
                        continue
                    except NetworkServiceDevice.DoesNotExist:
                        continue

                    ns = nsd.network_service
                    service_prefix = f"{ns.graphite_service_name()}.{graphite_prefix}"

                    for cat in ['in_octets', 'out_octets']:
                        graphite_name = f"{service_prefix}.{cat}"
                        m1 = getattr(e1, cat, None)
                        m2 = getattr(e2, cat, None)
                        if m1 is not None and m2 is not None:
                            diff = (m1 - m2)

                            if diff != 0:
                                diff = diff / total_seconds
                            graphyte.send(graphite_name, diff)
