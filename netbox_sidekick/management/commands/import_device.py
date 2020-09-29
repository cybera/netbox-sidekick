import re

from django.conf import settings
from django.core.management.base import BaseCommand

from dcim.choices import InterfaceModeChoices, InterfaceTypeChoices
from dcim.models import Device, Interface

from ipam.models import IPAddress, VLAN

from napalm import get_network_driver

from netbox_sidekick.models import NIC
from netbox_sidekick.napalm.junos import SidekickJunOSDriver

from .sidekick_utils import decrypt_secret, VALID_INTERFACE_NAMES


RE_ARISTA_VLAN = re.compile(r'^Vlan(\d+)$')


class Command(BaseCommand):
    help = "Import device information"

    def add_arguments(self, parser):
        parser.add_argument(
            '--name', required=True, help='The name of the device')

        parser.add_argument(
            '--ip', required=False, help='The management IP of the device')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        # First, query for the device by name.
        try:
            device = Device.objects.get(name=options['name'])
        except Device.DoesNotExist:
            self.stdout.write(f"Unable to find device: {options['name']}")
            return

        # If an IP address was specified, then configure the device with it.
        _ip = options['ip']
        if _ip is not None:
            # Make sure there's an interface named "mgmt"
            # If there isn't, then create one.
            mgmt_iface = next((True for iface in device.vc_interfaces.all() if iface.name == 'mgmt'), None)
            if not mgmt_iface:
                if options['dry_run']:
                    self.stdout.write('Would have created a managment interface called mgmt')
                else:
                    mgmt_iface = Interface(device=device, name='mgmt', type=InterfaceTypeChoices.TYPE_VIRTUAL)
                    mgmt_iface.save()

            # Make sure the specific IP address exists and is on the mgmt interface.
            try:
                _ip = options['ip']
                mgmt_ip = IPAddress.objects.get(address=_ip)

                # If the IP exists, make sure it's currently not assigned to another interface.
                if mgmt_ip.interface is not None:
                    if mgmt_ip.interface.name != 'mgmt' and mgmt_ip.interface.device.id != device.id:
                        self.stdout.write(f"IP Address {_ip} is already assigned to {mgmt_ip.interface.device.name}")
                        return
                # Otherwise, add the IP to the interface.
                else:
                    if options['dry_run']:
                        self.stdout.write(f"Would have added {mgmt_ip} to the mgmt interface")
                    else:
                        mgmt_ip.interface = mgmt_iface
                        mgmt_ip.save()
            except IPAddress.DoesNotExist:
                # If the IP doesn't exist, create it and link it to the mgmt interfae.
                if options['dry_run']:
                    self.stdout.write(f"Would have created IP address {options['ip']} and assigned it to the mgmt interface")
                else:
                    mgmt_ip = IPAddress(address=options['ip'], interface=mgmt_iface)
                    mgmt_ip.save()

            # Ensure the primary IP address of the device is set to the mgmt IP.
            if device.primary_ip4 is None or device.primary_ip4.id != mgmt_ip.id:
                if options['dry_run']:
                    self.stdout.write(f"Would have assigned {mgmt_ip} as the primary IP of the device")
                else:
                    device.primary_ip4 = mgmt_ip
                    device.save()

        # If an IP, platform, username, and password are defined,
        # try to connect to the device and pull some information from it.
        napalm_driver = None
        if device.platform.name == 'Juniper Junos':
            napalm_driver = 'junos'
        if device.platform.name == 'Arista EOS':
            napalm_driver = 'eos'

        # Determine the information needed to connect to the device.
        mgmt_ip = device.primary_ip4
        secret_username = settings.PLUGINS_CONFIG['netbox_sidekick'].get('secret_user', None)
        private_key_path = settings.PLUGINS_CONFIG['netbox_sidekick'].get('secret_private_key_path', None)

        # If all of the connection information was found,
        # attempt to decrypt the connection credentials,
        # connect to the device, and inventory the interfaces.
        if napalm_driver is not None and \
           mgmt_ip is not None and \
           secret_username is not None and \
           private_key_path is not None:

            _mgmt_ip = "%s" % (mgmt_ip.address.ip)

            try:
                username = decrypt_secret(device, 'username', secret_username, private_key_path)
                password = decrypt_secret(device, 'password', secret_username, private_key_path)
            except Exception as e:
                self.stdout.write(f"Unable to decrypt secret: {e}")

            # Connect to the device
            if napalm_driver == 'junos':
                napalm_device = SidekickJunOSDriver(_mgmt_ip, username, password)
            else:
                driver = get_network_driver(napalm_driver)
                napalm_device = driver(_mgmt_ip, username, password)
            napalm_device.open()

            # If we're able to connect,
            # build a list of interface names already on the device.
            existing_interfaces = {}
            for i in device.vc_interfaces.all():
                existing_interfaces[i.name] = i

            # Obtain the list of interfaces.
            # For each device that is not supposed to be ignored,
            # add that interface to the device if it doesn't already exist.
            for iface_name, iface_details in napalm_device.get_interfaces().items():
                if not any(i in iface_name for i in VALID_INTERFACE_NAMES):
                    continue

                iface_type = InterfaceTypeChoices.TYPE_VIRTUAL
                if iface_details['speed'] == 1000:
                    iface_type = InterfaceTypeChoices.TYPE_1GE_FIXED
                if iface_details['speed'] == 10000:
                    iface_type = InterfaceTypeChoices.TYPE_10GE_FIXED
                if 'ae' in iface_name:
                    iface_type = InterfaceTypeChoices.TYPE_LAG
                if 'lt' in iface_name:
                    iface_type = InterfaceTypeChoices.TYPE_VIRTUAL

                _vlan = None
                iface_mode = InterfaceModeChoices.MODE_TAGGED
                if '.' in iface_name:
                    iface_mode = InterfaceModeChoices.MODE_ACCESS
                    _vlan = iface_name.split('.')[1]
                if 'Vlan' in iface_name:
                    iface_mode = InterfaceModeChoices.MODE_ACCESS
                    m = RE_ARISTA_VLAN.search(iface_name)
                    if m:
                        _vlan = m.group(1)

                iface_untagged_vlan = None
                #if _vlan is not None:
                #    try:
                #        iface_untagged_vlan = VLAN.objects.get(vid=_vlan)
                #    except VLAN.MultipleObjectsReturned:
                #        self.stdout.write(f"WARNING: Multiple results found for VLAN {_vlan}. Not setting VLAN.")
                #    except VLAN.DoesNotExist:
                #        self.stdout.write(f"WARNING: No results found for VLAN {_vlan}. Not setting VLAN.")

                # If the interface already exists, update a few fields.
                # We do not update the interface type because that could have
                # been updated in NetBox directly to something more specific/better
                # than what NetBox+NAPALM can determine on their own.
                if iface_name in existing_interfaces.keys():
                    existing_interface = existing_interfaces[iface_name]

                    changed = False
                    if existing_interface.description != iface_details['description']:
                        existing_interface.description = iface_details['description']
                        changed = True

                    if existing_interface.connection_status != iface_details['is_up']:
                        existing_interface.connection_status = iface_details['is_up']
                        changed = True

                    if existing_interface.enabled != iface_details['is_enabled']:
                        existing_interface.enabled = iface_details['is_enabled']
                        changed = True

                    if existing_interface.untagged_vlan != iface_untagged_vlan:
                        existing_interface.untagged_vlan = iface_untagged_vlan
                        changed = True

                    # if existing_interface.type != iface_type:
                    #     changed = True
                    #     existing_interface.type = iface_type

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
                            description=iface_details['description'],
                            name=iface_name,
                            type=iface_type,
                            connection_status=iface_details['is_up'],
                            enabled=iface_details['is_enabled'],
                            mac_address=iface_details['mac_address'],
                            mtu=iface_details['mtu'],
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
            for iface_name, iface_details in napalm_device.get_interfaces_ip().items():
                if not any(i in iface_name for i in VALID_INTERFACE_NAMES):
                    continue

                if iface_name not in existing_interfaces.keys():
                    continue

                existing_interface = existing_interfaces[iface_name]

                for version in ['ipv4', 'ipv6']:
                    if version not in iface_details.keys():
                        continue

                    for device_ip, ip_details in iface_details[version].items():
                        _ip = f"{device_ip}/{ip_details['prefix_length']}"
                        try:
                            ip = IPAddress.objects.get(address=_ip)
                            if ip.assigned_object is not None and ip.assigned_object.id == existing_interface.id:
                                continue

                            if ip.assigned_object is not None and ip.assigned_object.id != existing_interface.id:
                                # If the IP being reported is the management IP, then ignore.
                                # This is because we want to standardize on the name of the
                                # management interface, even if the IP address is on a different
                                # interface. This isn't ideal and should be improved in the future.
                                #
                                # This also ignores private IP addresses since they can be reused
                                # in different locations. Again, this isn't ideal and should be
                                # improved in the future.
                                if ip != mgmt_ip and \
                                   not f"{ip}".startswith("10.") and \
                                   not f"{ip}".startswith("192.") and \
                                   not f"{ip}".startswith("172."):
                                    self.stdout.write(
                                        f"IP Address {_ip} is already assigned to " +
                                        f"{ip.assigned_object.name} on {ip.assigned_object.device.name}. " +
                                        f"Will not assign to {existing_interface.name}.")
                                    continue
                            # Otherwise, add the IP to the interface.
                            else:
                                if options['dry_run']:
                                    self.stdout.write(
                                        f"Would have added {_ip} to {existing_interface.name}")

                                else:
                                    if ip.description != existing_interface.description:
                                        ip.description = existing_interface.description
                                    ip.assigned_object = existing_interface
                                    ip.save()
                        except IPAddress.MultipleObjectsReturned:
                            self.stdout.write(f"WARNING: Multiple results found for IP {_ip}. Skipping.")
                            continue
                        except IPAddress.DoesNotExist:
                            if options['dry_run']:
                                self.stdout.write(
                                    f"Would have created IP address {_ip} and added it to " +
                                    f"{existing_interface.name}")
                            else:
                                ip = IPAddress(
                                    address=_ip,
                                    description=existing_interface.description)
                                ip.save()

                                existing_interface.ip_address = ip
                                existing_interface.save()

            # Obtain the counters on each interface.
            # For each interface that is not supposed to be ignored,
            # store the counters as a NIC object.
            for iface_name, iface_details in napalm_device.get_interfaces_counters().items():
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
                            'is_up': existing_interface.connection_status,
                            'is_enabled': existing_interface.enabled,
                            'tx_octets': iface_details['tx_octets'],
                            'rx_octets': iface_details['rx_octets'],
                            'tx_unicast_packets': iface_details['tx_unicast_packets'],
                            'rx_unicast_packets': iface_details['rx_unicast_packets'],
                            'tx_multicast_packets': iface_details['tx_multicast_packets'],
                            'rx_multicast_packets': iface_details['rx_multicast_packets'],
                            'tx_broadcast_packets': iface_details['tx_broadcast_packets'],
                            'rx_broadcast_packets': iface_details['rx_broadcast_packets'],
                            'tx_discards': iface_details['tx_discards'],
                            'rx_discards': iface_details['rx_discards'],
                            'tx_errors': iface_details['tx_errors'],
                            'rx_errors': iface_details['rx_errors'],
                        }
                    )
