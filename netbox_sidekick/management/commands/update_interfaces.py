import re

from django.conf import settings
from django.core.management.base import BaseCommand

from dcim.choices import InterfaceModeChoices, InterfaceTypeChoices
from dcim.models import Device, Interface

from ipam.models import IPAddress

from netbox_sidekick.models import NIC

from .sidekick_utils import (
    VALID_INTERFACE_NAMES,
    decrypt_secret,
    snmpwalk_bulk,
)


RE_ARISTA_VLAN = re.compile(r'^Vlan(\d+)$')

IP_VERSIONS = {
    'ipv4': 4,
    'ipv6': 6,
}


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
        secret_username = settings.PLUGINS_CONFIG['netbox_sidekick'].get('secret_user', None)
        private_key_path = settings.PLUGINS_CONFIG['netbox_sidekick'].get('secret_private_key_path', None)

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
            for i in device.vc_interfaces.all():
                existing_interfaces[i.name] = i

            # Obtain the list of interfaces.
            # For each device that is not supposed to be ignored,
            # add that interface to the device if it doesn't already exist.
            for iface_index, iface_details in device_info.items():
                iface_name = iface_details['ifName']
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

                    iface_status = False
                    admin_status = iface_details['ifAdminStatus']
                    oper_status = iface_details['ifOperStatus']
                    if admin_status == 1 and oper_status == 1:
                        iface_status = True
                    if existing_interface.connection_status != iface_status:
                        existing_interface.connection_status = iface_status
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
                        iface = Interface(
                            device=device,
                            description=iface_details['ifDescr'],
                            name=iface_name,
                            type=iface_type,
                            enabled=iface_details['ifAdminStatus'],
                            mac_address=iface_details['ifPhysAddress'],
                            mtu=iface_details['ifMtu'],
                            mode=iface_mode,
                            untagged_vlan=iface_untagged_vlan,
                        )
                        iface.save()

            # To account for one or more new interfaces being added,
            # build a list of interface names already on the device.
            existing_interfaces = {}
            for i in device.vc_interfaces.all():
                existing_interfaces[i.name] = i

            # Obtain the list of IP addresses on each interface.
            # For each interface that is not supposed to be ignored,
            # add the IP address to the interface if it doesn't already exist.
            for iface_index, iface_details in device_info.items():
                iface_name = iface_details['ifName']

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

                                    self.stdout.write(
                                        f"IP Address {interface_ip} is already assigned to " +
                                        f"{ip.assigned_object.name} on {ip.assigned_object.device.name}. " +
                                        f"Will not assign to {existing_interface.name}.")
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
                iface_name = iface_details['ifName']
                if not any(i in iface_name for i in VALID_INTERFACE_NAMES):
                    continue

                if iface_name not in existing_interfaces.keys():
                    continue

                existing_interface = existing_interfaces[iface_name]
                if options['dry_run']:
                    self.stdout.write(f"Would have updated counters for {existing_interface.name}")
                else:
                    NIC.objects.update_or_create(
                        interface=existing_interface,
                        defaults={
                            'interface_id': existing_interface.id,
                            'admin_status': iface_details['ifAdminStatus'],
                            'oper_status': iface_details['ifOperStatus'],
                            'out_octets': iface_details['ifHCOutOctets'],
                            'in_octets': iface_details['ifHCInOctets'],
                            'out_unicast_packets': iface_details['ifHCOutUcastPkts'],
                            'in_unicast_packets': iface_details['ifHCInUcastPkts'],
                            'out_nunicast_packets': iface_details['ifOutNUcastPkts'],
                            'in_nunicast_packets': iface_details['ifInNUcastPkts'],
                            'out_errors': iface_details['ifOutErrors'],
                            'in_errors': iface_details['ifInErrors'],
                        }
                    )
