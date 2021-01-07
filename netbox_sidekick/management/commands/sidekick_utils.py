import netaddr
import re

from django.contrib.auth.models import User

from pysnmp.hlapi import (
    getCmd, nextCmd,
    CommunityData, ContextData,
    ObjectIdentity, ObjectType,
    SnmpEngine,
    UdpTransportTarget,
)

from secrets.models import UserKey


MEMBER_TYPES = [
    'Enterprise',
    'Government/Not For Profit',
    'K-12 School Districts',
    'Post-Secondary Institution',
]

NETMASKS = {
    '0.0.0.0': '0', '128.0.0.0': '1', '192.0.0.0': '2', '224.0.0.0': '3',
    '240.0.0.0': '4', '248.0.0.0': '5', '252.0.0.0': '6', '254.0.0.0': '7',
    '255.0.0.0': '8', '255.128.0.0': '9', '255.192.0.0': '10', '255.224.0.0': '11',
    '255.240.0.0': '12', '255.248.0.0': '13', '255.252.0.0': '14', '255.254.0.0': '15',
    '255.255.0.0': '16', '255.255.128.0': '17', '255.255.192.0': '18', '255.255.224.0': '19',
    '255.255.240.0': '20', '255.255.248.0': '21', '255.255.252.0': '22', '255.255.254.0': '23',
    '255.255.255.0': '24', '255.255.255.128': '25', '255.255.255.192': '26',
    '255.255.255.224': '27', '255.255.255.240': '28', '255.255.255.248': '29',
    '255.255.255.252': '30', '255.255.255.254': '31', '255.255.255.255': '32',
}

NIC_ADMIN_STATUSES = {
    1: True,
    2: False,
    3: False,
}

NIC_OPER_STATUSES = {
    1: 'Up',
    2: 'Down',
    3: 'Testing',
    4: 'Unknown',
    5: 'Dormant',
    6: 'Not Present',
    7: 'Lower Layer Down',
}

OIDs = [
    ObjectType(ObjectIdentity('IF-MIB', 'ifIndex')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifOperStatus')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifAdminStatus')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifName')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifAlias')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifMtu')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifType')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifDescr')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifPhysAddress')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifHighSpeed')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifHCOutOctets')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifHCInOctets')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifOutOctets')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifInOctets')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifInNUcastPkts')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifOutNUcastPkts')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifHCInUcastPkts')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifHCOutUcastPkts')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifInUcastPkts')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifOutUcastPkts')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifOutErrors')),
    ObjectType(ObjectIdentity('IF-MIB', 'ifInErrors')),
    ObjectType(ObjectIdentity('IP-MIB', 'ipAdEntNetMask')),
    ObjectType(ObjectIdentity('IP-MIB', 'ipAdEntIfIndex')),
    ObjectType(ObjectIdentity('IPV6-MIB', 'ipv6AddrPfxLength')),
]

VALID_INTERFACE_NAMES = [
    # Arista
    'Ethernet', 'Vlan',

    # Juniper
    'ae', 'et', 'ge', 'lt', 'xe',
]


def decrypt_secret(device, name, user, private_key_path):
    private_key = None
    with open(private_key_path) as f:
        private_key = f.read()

    try:
        _user = User.objects.get(username=user)
    except User.DoesNotExist:
        raise Exception(f"Unable to find user {user}")

    try:
        user_key = UserKey.objects.get(user=_user)
    except UserKey.DoesNotExist:
        raise Exception(f"Unable to find UserKey for {user}")

    master_key = user_key.get_master_key(private_key)
    if master_key is None:
        raise Exception(f"Invalid private key {private_key_path}")

    secret = device.secrets.filter(name=name)
    if len(secret) == 1:
        s = secret[0]
        s.decrypt(master_key)
        return s.plaintext


def snmpget(ipaddress, community, oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community),
        UdpTransportTarget((ipaddress, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid)))
    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        raise Exception(f"Error performing snmpget: {errorIndication}")
    elif errorStatus:
        _msg = '%s at %s' % (
            errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
        raise Exception(f"Error performing snmpget: {_msg}")
    else:
        if len(varBinds) > 0:
            return varBinds
        return None


def snmpwalk(ipaddress, community, oid):
    _results = []
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ipaddress, 161)),
            ContextData(),
            ObjectType(oid),
            lexicographicMode=False,
            lookupMib=True):

        if errorIndication:
            raise Exception(f"Error performing snmpwalk: {errorIndication}")
        if errorStatus:
            _msg = '%s at %s' % (
                errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            raise Exception(f"Error performing snmpget: {_msg}")
        else:
            _results.append(varBinds)

    if len(_results) > 0:
        return _results
    return None


def snmpwalk_bulk(ipaddress, community):
    data = []
    results = {}
    ip_addresses = {}

    special = [
        'ifAdminStatus',
        'ifOperStatus',
        'ipv6AddrPfxLength',
        'ipAdEntNetMask',
        'ipAdEntIfIndex',
    ]

    oid_re = r'^(.*)::(\w+)'
    ipv6_re = r'^1\.3\.6\.1\.2\.1\.55\.1\.8\.1\.2\.(\d+)\.((\d+\.){15}(\d+))'
    ipv4_re = r'^1\.3\.6\.1\.2\.1\.4\.20\.1\.2\.(\d+\.\d+\.\d+\.\d+)'
    ipv4_mask_re = r'^1\.3\.6\.1\.2\.1\.4\.20\.1\.3\.(\d+\.\d+\.\d+\.\d+)'

    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ipaddress, 161)),
            ContextData(),
            lexicographicMode=False,
            lookupMib=True,
            *OIDs):

        if errorIndication:
            raise Exception(f"Error performing snmpwalk: {errorIndication}")
        if errorStatus:
            _msg = '%s at %s' % (
                errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            raise Exception(f"Error performing snmpget: {_msg}")
        else:
            data.append(varBinds)

    for row in data:
        for r in row:
            # Match the format IF-MIB::FOO
            match = re.match(oid_re, str(r[0].prettyPrint()))
            if match:
                # If this is not a special case,
                # do a simple parsing of the result
                if match[2] not in special:
                    index = f"{r[0]}".split('.')[-1]
                    if index not in results:
                        results[index] = {}
                    results[index][match[2]] = r[1].prettyPrint()

                # Parse admin status
                if match[2] == 'ifAdminStatus' or match[2] == 'ifOperStatus':
                    index = f"{r[0]}".split('.')[-1]
                    if index not in results:
                        results[index] = []
                    results[index][match[2]] = r[1]

                # Parse IPv6 addresses
                if match[2] == 'ipv6AddrPfxLength':
                    if f"{r[1]}" == "":
                        continue
                    match2 = re.match(ipv6_re, f"{r[0]}")
                    if match2:
                        index = match2[1]
                        if index not in results:
                            results[index] = {}
                        if 'ipv6' not in results[index]:
                            results[index]['ipv6'] = []
                        i = 0
                        v6string = ''
                        for m in match2[2].split('.'):
                            v6string = f"{v6string}{format(int(m), '02x')}"
                            if i % 2 and i < 14:
                                v6string = "%s:" % (v6string)
                            i += 1
                        _ip = netaddr.IPNetwork(f"{v6string}/{r[1]}")
                        results[index]['ipv6'].append(f"{_ip}")

                # Parse IPv4 addresses
                if match[2] == 'ipAdEntIfIndex':
                    if f"{r[1]}" == "":
                        continue
                    match2 = re.match(ipv4_re, f"{r[0]}")
                    if match2:
                        index = r[1].prettyPrint()
                        if index not in results:
                            results[index] = {}
                        if 'ipAdEntIfIndex' not in results[index]:
                            results[index]['ipAdEntIfIndex'] = []
                        v4_address = match2[1]
                        results[index]['ipAdEntIfIndex'].append(v4_address)

                # Get the netmask for IPs
                # and store them in a different variable
                if match[2] == "ipAdEntNetMask":
                    if f"{r[1]}" == "":
                        continue
                    match2 = re.match(ipv4_mask_re, f"{r[0]}")
                    if match2:
                        v4_mask = r[1].prettyPrint()
                        v4_address = match2[1]
                        cidr = NETMASKS[v4_mask]
                        ip_addresses[v4_address] = cidr

    # Loop through the results
    # and match the IP address with the netmask
    for k, v in results.items():
        if 'ipv4' not in results[k]:
            results[k]['ipv4'] = []

        if 'ipAdEntIfIndex' in v:
            for ipv4 in v['ipAdEntIfIndex']:
                if ipv4 in ip_addresses.keys():
                    results[k]['ipv4'].append(f"{ipv4}/{ip_addresses[ipv4]}")

    return results
