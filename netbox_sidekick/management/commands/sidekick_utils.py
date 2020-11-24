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


def get_device_info_via_snmp(ipaddress, community):
    _results = {}

    indexes = get_interfaces_indexes(ipaddress, community)
    types = get_interfaces_types(ipaddress, community)
    names = get_interfaces_names(ipaddress, community)
    aliases = get_interfaces_aliases(ipaddress, community)
    descriptions = get_interfaces_descriptions(ipaddress, community)
    speeds = get_interfaces_speeds(ipaddress, community)
    mtus = get_interfaces_mtus(ipaddress, community)
    admin_statuses = get_interfaces_admin_statuses(ipaddress, community)
    oper_statuses = get_interfaces_oper_statuses(ipaddress, community)
    ipv4 = get_interfaces_ipv4(ipaddress, community)
    ipv4_masks = get_interfaces_ipv4_masks(ipaddress, community)
    ipv6 = get_interfaces_ipv6(ipaddress, community)

    hc_in_octets = get_interfaces_hc_in_octets(ipaddress, community)
    hc_out_octets = get_interfaces_hc_out_octets(ipaddress, community)

    in_octets = get_interfaces_in_octets(ipaddress, community)
    out_octets = get_interfaces_out_octets(ipaddress, community)

    in_errors = get_interfaces_in_errors(ipaddress, community)
    out_errors = get_interfaces_out_errors(ipaddress, community)

    hc_in_unicast_packets = get_interfaces_hc_in_unicast_packets(ipaddress, community)
    hc_out_unicast_packets = get_interfaces_hc_out_unicast_packets(ipaddress, community)

    in_unicast_packets = get_interfaces_in_unicast_packets(ipaddress, community)
    out_unicast_packets = get_interfaces_out_unicast_packets(ipaddress, community)

    in_nunicast_packets = get_interfaces_in_nunicast_packets(ipaddress, community)
    out_nunicast_packets = get_interfaces_out_nunicast_packets(ipaddress, community)

    for i in indexes:
        v = {}
        v['type'] = types.get(i, None)
        v['name'] = names.get(i, None)
        v['alias'] = aliases.get(i, '').strip()
        v['speed'] = speeds.get(i, None)
        v['admin_status'] = int(admin_statuses.get(i, 0))
        v['oper_status'] = int(oper_statuses.get(i, 0))
        v['mtu'] = mtus.get(i, None)
        v['description'] = descriptions.get(i, '').strip()
        v['in_errors'] = in_errors.get(i, None)
        v['out_errors'] = out_errors.get(i, None)
        v['in_nunicast_packets'] = in_nunicast_packets.get(i, None)
        v['out_nunicast_packets'] = out_nunicast_packets.get(i, None)

        v['in_octets'] = 0
        if i in hc_in_octets:
            v['in_octets'] = hc_in_octets[i]
        elif i in in_octets:
            v['in_octets'] = in_octets[i]

        v['out_octets'] = 0
        if i in hc_out_octets:
            v['out_octets'] = hc_out_octets[i]
        elif i in out_octets:
            v['out_octets'] = out_octets[i]

        v['in_unicast_packets'] = 0
        if i in hc_in_unicast_packets:
            v['in_unicast_packets'] = hc_in_unicast_packets[i]
        elif i in in_unicast_packets:
            v['in_unicast_packets'] = in_unicast_packets[i]

        v['out_unicast_packets'] = 0
        if i in hc_out_unicast_packets:
            v['out_unicast_packets'] = hc_out_unicast_packets[i]
        elif i in out_unicast_packets:
            v['out_unicast_packets'] = out_unicast_packets[i]

        addrs = ipv4.get(i, None)
        v['ipv4'] = None
        if addrs is not None:
            _addrs = []
            for addr in addrs:
                if addr in ipv4_masks:
                    addr = f"{addr}/{ipv4_masks[addr]}"
                _addrs.append(addr)
            v['ipv4'] = _addrs

        v['ipv6'] = None
        if ipv6 is not None:
            v['ipv6'] = ipv6.get(i, None)

        _results[i] = v

    return _results


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


def simple_snmp_query(ipaddress, community, oid):
    _results = {}

    data = snmpwalk(ipaddress, community, oid)
    if data is None:
        return None

    for d in data:
        i = f"{d[0][0]}".split('.')[-1]
        _results[i] = f"{d[0][1]}"

    return _results


def get_interfaces_indexes(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.2.2.1.1')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_admin_statuses(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.2.2.1.7')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_oper_statuses(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.2.2.1.8')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_names(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.31.1.1.1.1')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_speeds(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.31.1.1.1.15')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_types(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifType')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_descriptions(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifDescr')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_ipv6(ipaddress, community):
    OID = ObjectIdentity('1.3.6.1.2.1.55.1.8.1.2')
    ipv6_re = r'^1\.3\.6\.1\.2\.1\.55\.1\.8\.1\.2\.(\d+)\.((\d+\.){15}(\d+))'

    _results = {}
    data = snmpwalk(ipaddress, community, OID)
    if data is None:
        return None

    for d in data:
        m = re.match(ipv6_re, f"{d[0][0]}")
        if m:
            index = m[1]
            if index not in _results:
                _results[index] = []

            i = 0
            v6string = ''
            for v in m[2].split('.'):
                v6string = f"{v6string}{format(int(v), '02x')}"
                if i % 2 and i < 14:
                    v6string = "%s:" % (v6string)
                i += 1
            _results[index].append(f"{v6string}/{d[0][1]}")

    if len(_results) == 0:
        return None
    return _results


def get_interfaces_ipv4_masks(ipaddress, community):
    OID = ObjectIdentity('1.3.6.1.2.1.4.20.1.3')
    ipv4_re = r'^1\.3\.6\.1\.2\.1\.4\.20\.1\.3\.(\d+\.\d+\.\d+\.\d+)'

    _results = {}
    data = snmpwalk(ipaddress, community, OID)
    for d in data:
        v4_mask = d[0][1].prettyPrint()
        m = re.match(ipv4_re, f"{d[0][0]}")
        if m:
            v4_address = m[1]
            cidr = NETMASKS[v4_mask]
            _results[v4_address] = cidr

    if len(_results) == 0:
        return None
    return _results


def get_interfaces_ipv4(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.4.20.1.2')
    ipv4_re = r'^1\.3\.6\.1\.2\.1\.4\.20\.1\.2\.(\d+\.\d+\.\d+\.\d+)'

    _results = {}
    data = snmpwalk(ipaddress, community, OID)
    for d in data:

        m = re.match(ipv4_re, f"{d[0][0]}")
        if m:
            index = d[0][1].prettyPrint()
            if index not in _results:
                _results[index] = []

            v4_address = m[1]
            _results[index].append(v4_address)

    if len(_results) == 0:
        return None
    return _results


def get_interfaces_aliases(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.31.1.1.1.18')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_hc_out_octets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifHCOutOctets')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_hc_in_octets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifHCInOctets')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_out_octets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifOutOctets')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_in_octets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifInOctets')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_in_nunicast_packets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifInNUcastPkts')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_out_nunicast_packets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifOutNUcastPkts')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_hc_in_unicast_packets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifHCInUcastPkts')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_hc_out_unicast_packets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifHCOutUcastPkts')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_in_unicast_packets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifInUcastPkts')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_out_unicast_packets(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifOutUcastPkts')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_out_errors(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifOutErrors')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_in_errors(ipaddress, community):
    OID = ObjectIdentity('IF-MIB', 'ifInErrors')
    return simple_snmp_query(ipaddress, community, OID)


def get_interfaces_mtus(ipaddress, community):
    OID = ObjectIdentity('.1.3.6.1.2.1.2.2.1.4')
    return simple_snmp_query(ipaddress, community, OID)
