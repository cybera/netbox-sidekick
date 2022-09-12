import json
import netaddr
import onepasswordconnectsdk
import re
import requests
import rrdtool
import time
import whisper

from pysnmp.hlapi import (
    getCmd, nextCmd,
    CommunityData, ContextData,
    ObjectIdentity, ObjectType,
    SnmpEngine,
    UdpTransportTarget,
)

from sidekick.models import (
    AccountingProfile,
    NetworkService,
)

GRAPHS = {
    # 'last_day': {
    #     'title': 'Last Day',
    #     'from': '-1d',
    # },
    # 'last_week': {
    #     'title': 'Last Week',
    #     'from': '-7d',
    # },
    # 'last_month': {
    #     'title': 'Last Month',
    #     'from': '-4w',
    # },
    'last_year': {
        'title': 'Last Year',
        'from': '-1y',
    },
}

MEMBER_TYPES = [
    'Enterprise',
    'Government/Not For Profit',
    'K-12 School Districts',
    'Post-Secondary Institution',
]

MEMBER_TYPE_CHOICES = [
    ('Enterprise', 'Enterprise'),
    ('Government/Not For Profit', 'Government/Not For Profit'),
    ('K-12 School Districts', 'K-12 School Districts'),
    ('Post-Secondary Institution', 'Post-Secondary Institution'),
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

    # jnx ifHCIn1SecRate
    ObjectType(ObjectIdentity('.1.3.6.1.4.1.2636.3.3.1.1.7')),

    # jnx ifHCOut1SecRate
    ObjectType(ObjectIdentity('.1.3.6.1.4.1.2636.3.3.1.1.8')),
]

ACCOUNTING_OIDS = [
    # jnxScuStatsClName
    ObjectType(ObjectIdentity('.1.3.6.1.4.1.2636.3.16.1.1.1.6')),
    # jnxDcuStatsClName
    ObjectType(ObjectIdentity('.1.3.6.1.4.1.2636.3.6.2.1.6')),
    # jnxScuStatsBytes
    ObjectType(ObjectIdentity('.1.3.6.1.4.1.2636.3.16.1.1.1.5')),
    # jnxDcuStatsBytes
    ObjectType(ObjectIdentity('.1.3.6.1.4.1.2636.3.6.2.1.5')),
]


VALID_INTERFACE_NAMES = [
    # Arista
    'Ethernet', 'Vlan',

    # Cisco
    'Fa', 'Gi', 'Nu', 'Po', 'StackPort', 'Te', 'Vl',

    # Juniper
    'ae', 'et', 'ge', 'lt', 'xe',
]


def decrypt_1pw_secret(token_path, host, vault, device, field):
    token = None
    with open(token_path) as f:
        token = f.read().strip()

    client = onepasswordconnectsdk.client.new_client(
        host, token)

    secret = None
    item = client.get_item(device, vault)
    for _v in item.fields:
        if _v.label == field:
            secret = _v.value
            break

    if secret is None:
        raise Exception("Unable to find secret: {field}")

    return secret


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


def snmpwalk_bulk_accounting(ipaddress, community):
    data = []
    isps = {}
    class_names = {}
    scu_bytes = {}
    dcu_bytes = {}

    jnxScuStatsClName_re = r'.*2636\.3\.16\.1\.1\.1\.6\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(.+)'
    jnxDcuStatsClName_re = r'.*2636\.3\.6\.2\.1\.6\.(\d+)\.(\d+)\.(\d+)\.(.+)'
    jnxScuStatsBytes_re = r'.*2636\.3\.16\.1\.1\.1\.5\.(\d+)\.1\.(\d+)\.(.+)'
    jnxDcuStatsBytes_re = r'.*2636\.3\.6\.2\.1\.5\.(\d+)\.1\.(\d+)\.(.+)'

    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ipaddress, 161)),
            ContextData(),
            lexicographicMode=False,
            lookupMib=True,
            *ACCOUNTING_OIDS):

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
            # collect class name via jnxScuStatsClName
            m = re.match(jnxScuStatsClName_re, f"{r[0]}")
            if m:
                isps[m[1]] = ""
                class_names[m[5]] = f"{r[1]}"

            # collect class name via jnxDcuStatsClName
            m = re.match(jnxDcuStatsClName_re, f"{r[0]}")
            if m:
                isps[m[1]] = ""
                class_names[m[4]] = f"{r[1]}"

            # collect scu bytes via jnxScuStatsBytes
            m = re.match(jnxScuStatsBytes_re, f"{r[0]}")
            if m:
                _isp = m[1]
                _class = m[3]

                if _class not in scu_bytes:
                    scu_bytes[_class] = {}
                if _isp not in scu_bytes[_class]:
                    scu_bytes[_class][_isp] = f"{r[1]}"

            # collect scu bytes via jnxDcuStatsBytes
            m = re.match(jnxDcuStatsBytes_re, f"{r[0]}")
            if m:
                _isp = m[1]
                _class = m[3]

                if _class not in dcu_bytes:
                    dcu_bytes[_class] = {}
                if _isp not in dcu_bytes[_class]:
                    dcu_bytes[_class][_isp] = f"{r[1]}"

    # Obtain the name for each ISP
    for isp in isps.keys():
        _oid = f".1.3.6.1.2.1.31.1.1.1.18.{isp}"
        isp_name = snmpget(ipaddress, community, _oid)
        if isp_name is not None:
            isps[isp] = f"{isp_name[0][1]}"

    # Format and structure the results
    classes = {}

    for k, v in scu_bytes.items():
        for isp, data in v.items():
            title = f"{class_names[k]} -- {isps[isp]}"
            if title not in classes:
                classes[title] = {}
                classes[title]['class'] = class_names[k]
                classes[title]['isp'] = isps[isp]
            classes[title]['scu'] = data

    for k, v in dcu_bytes.items():
        for isp, data in v.items():
            title = f"{class_names[k]} -- {isps[isp]}"
            if title not in classes:
                classes[title] = {}
                classes[title]['class'] = class_names[k]
                classes[title]['isp'] = isps[isp]
            classes[title]['dcu'] = data

    return classes


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

    jnxifHCIn1SecRate_re = r'.*2636\.3\.3\.1\.1\.7'
    jnxifHCOut1SecRate_re = r'.*2636\.3\.3\.1\.1\.8'

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
            # Match the jnx-specific entries
            match = re.match(jnxifHCIn1SecRate_re, f"{r[0]}")
            if match:
                index = f"{r[0]}".split('.')[-1]
                if index not in results:
                    results[index] = {}
                in_rate = r[1].prettyPrint()
                if in_rate != "No more variables left in this MIB View":
                    results[index]['in_rate'] = in_rate

            # Match the jnx-specific entries
            match = re.match(jnxifHCOut1SecRate_re, f"{r[0]}")
            if match:
                index = f"{r[0]}".split('.')[-1]
                if index not in results:
                    results[index] = {}
                out_rate = r[1].prettyPrint()
                if out_rate != "No more variables left in this MIB View":
                    results[index]['out_rate'] = r[1].prettyPrint()

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


# Most of this was taken from
# https://github.com/graphite-project/whisper/blob/master/bin/rrd2whisper.py
# https://github.com/graphite-project/whisper/blob/master/bin/whisper-resize.py
def convert_rrd(rrd_file, dest_dir):
    datasource_map = {
        'OUTOCTETS': 'out_octets',
        'OUTUCASTPKTS': 'out_unicast_packets',
        'OUTNUCASTPKTS': 'out_nunicast_packets',
        'INNUCASTPKTS': 'in_nunicast_packets',
        'INERRORS': 'in_errors',
        'OUTERRORS': 'out_errors',
        'INUCASTPKTS': 'in_unicast_packets',
        'INOCTETS': 'in_octets',
    }

    rra_indices = []
    rrd_info = rrdtool.info(rrd_file)
    seconds_per_pdp = rrd_info['step']
    for key in rrd_info:
        if key.startswith('rra['):
            index = int(key.split('[')[1].split(']')[0])
            rra_indices.append(index)

    rra_count = max(rra_indices) + 1
    rras = []
    for i in range(rra_count):
        rra_info = {}
        rra_info['pdp_per_row'] = rrd_info['rra[%d].pdp_per_row' % i]
        rra_info['rows'] = rrd_info['rra[%d].rows' % i]
        rra_info['cf'] = rrd_info['rra[%d].cf' % i]
        if 'xff' in rrd_info:
            rra_info['xff'] = rrd_info['rra[%d].xff' % i]
        rras.append(rra_info)

    datasources = []
    if 'ds' in rrd_info:
        datasources = rrd_info['ds'].keys()
    else:
        ds_keys = [key for key in rrd_info if key.startswith('ds[')]
        datasources = list(set(key[3:].split(']')[0] for key in ds_keys))

    relevant_rras = []
    for rra in rras:
        if rra['cf'] == 'MAX':
            relevant_rras.append(rra)

    archives = []
    for rra in relevant_rras:
        precision = rra['pdp_per_row'] * seconds_per_pdp
        points = rra['rows']
        archives.append((precision, points))

    for datasource in datasources:
        now = int(time.time())
        d = datasource_map[datasource]
        dest_path = f"{dest_dir}/{d}.wsp"
        try:
            whisper.create(dest_path, archives, xFilesFactor=0.5)
        except whisper.InvalidConfiguration:
            pass

        datapoints = []
        for precision, points in reversed(archives):
            retention = precision * points
            endTime = now - now % precision
            startTime = endTime - retention
            (time_info, columns, rows) = rrdtool.fetch(
                rrd_file,
                'MAX',
                '-r', str(precision),
                '-s', str(startTime),
                '-e', str(endTime),
                '-a')
            column_index = list(columns).index(datasource)
            rows.pop()
            values = [row[column_index] for row in rows]
            timestamps = list(range(*time_info))
            datapoints = zip(timestamps, values)
            datapoints = [datapoint for datapoint in datapoints if datapoint[1] is not None]
            whisper.update_many(dest_path, datapoints)


def get_graphite_nic_graph(nic, graphite_render_host=None, period="-1Y"):
    if graphite_render_host is None:
        return None

    carbon_name = "{}.{}".format(
        nic.graphite_device_name(),
        nic.graphite_interface_name()
    )

    query_base = f"{graphite_render_host}/render?format=json"
    graph_data = {}
    graph_data['title'] = "Last Year - GB"
    metric_in = f"{carbon_name}.in_octets"
    metric_out = f"{carbon_name}.out_octets"
    target_in = f"scale(keepLastValue({metric_in}), 8)"
    target_out = f"scale(keepLastValue({metric_out}), -8)"
    query = f"{query_base}&from={period}&target={target_in}&target={target_out}"

    r = requests.get(query)
    # graphs[period][inout]['graph'] = b64encode(r.content).decode('utf-8')
    results = json.loads(r.content.decode('utf-8'))
    data = [[], [], []]
    if len(results) == 0:
        return None

    for d in results[0]['datapoints']:
        data[0].append(d[1])
        data[1].append(d[0])

    for d in results[1]['datapoints']:
        data[2].append(d[0])
    graph_data['data'] = data
    graph_data['query'] = query

    return graph_data


def get_graphite_service_graph(graphite_render_host, service, period="-1Y"):
    if graphite_render_host is None:
        return None

    service_name = service.graphite_service_name()

    query_base = f"{graphite_render_host}/render?format=json"

    graph_data = {}
    graph_data['title'] = "Last Year - GB"
    target_in = f"scale(keepLastValue({service_name}.*.*.in_octets), 8)"
    target_out = f"scale(keepLastValue({service_name}.*.*.out_octets), -8)"
    query = f"{query_base}&from={period}&target={target_in}&target={target_out}"

    r = requests.get(query)
    # graphs[period][inout]['graph'] = b64encode(r.content).decode('utf-8')
    results = json.loads(r.content.decode('utf-8'))
    if len(results) == 0:
        return None

    data = [[], [], []]

    for d in results[0]['datapoints']:
        data[0].append(d[1])
        data[1].append(d[0])

    for d in results[1]['datapoints']:
        data[2].append(d[0])
    graph_data['data'] = data
    graph_data['query'] = query

    return graph_data


def get_graphite_data(graphite_render_host, targets_in, targets_out, period="-1Y"):
    if graphite_render_host is None:
        return None

    targets_in = ', '.join(targets_in)
    targets_out = ', '.join(targets_out)

    query = f"{graphite_render_host}/render?format=json&from={period}"
    query = f"{query}&target=transformNull(scale(sum({targets_in}), 8))"
    query = f"{query}&target=transformNull(scale(sum({targets_out}), -8))"

    r = requests.get(query)
    results = json.loads(r.content.decode('utf-8'))
    if len(results) == 0:
        results = [
            {'datapoints': [[0, 0]]},
            {'datapoints': [[0, 0]]},
        ]

    graph_data = {}
    data = [[], [], []]

    for d in results[0]['datapoints']:
        data[0].append(d[1])
        data[1].append(d[0])

    for d in results[1]['datapoints']:
        data[2].append(d[0])

    graph_data['data'] = data
    graph_data['query'] = query

    return graph_data


def format_graphite_service_query(services):
    services_in = []
    services_out = []
    for service in services:
        name = service.graphite_service_name()
        services_in.append(f"{name}.*.*.in_octets")
        services_out.append(f"{name}.*.*.out_octets")

    targets_in = f"sumSeries({', '.join(services_in)})"
    targets_out = f"sumSeries({', '.join(services_out)})"

    return (targets_in, targets_out)


def format_graphite_accounting_query(accounting):
    accounting_in = []
    accounting_out = []
    for acct in accounting:
        name = acct.graphite_full_path_name()
        accounting_in.append(f"{name}.in_octets")
        accounting_out.append(f"{name}.out_octets")

    targets_in = f"sumSeries({', '.join(accounting_in)})"
    targets_out = f"sumSeries({', '.join(accounting_out)})"

    return (targets_in, targets_out)


def format_graphite_remaining_query(services, accounting):
    services_in = []
    services_out = []
    for service in services:
        name = service.graphite_service_name()
        services_in.append(f"{name}.*.*.in_octets")
        services_out.append(f"{name}.*.*.out_octets")

    targets_in = f"sumSeries({', '.join(services_in)})"
    targets_out = f"sumSeries({', '.join(services_out)})"

    if len(accounting) > 0:
        accounting_in = []
        accounting_out = []
        for acct in accounting:
            name = acct.graphite_full_path_name()
            accounting_in.append(f"{name}.in_octets")
            accounting_out.append(f"{name}.out_octets")

        targets_in = f"removeBelowValue(diffSeries(sumSeries({', '.join(services_in)}), {', '.join(accounting_in)}), 0)"
        targets_out = f"removeBelowValue(diffSeries(sumSeries({', '.join(services_out)}), {', '.join(accounting_out)}), 0)"

    return (targets_in, targets_out)


def get_all_ip_prefixes():
    prefixes = {}
    for network_service in NetworkService.objects.filter(active=True):
        member_id = network_service.member.id
        if member_id not in prefixes:
            prefixes[member_id] = {
                'prefixes': [],
                'member': network_service.member,
            }
        for prefix in network_service.get_ip_prefixes():
            if prefix not in prefixes[member_id]['prefixes']:
                prefixes[member_id]['prefixes'].append(prefix)
        prefixes[member_id]['prefixes'].sort()
    return prefixes


def get_services(member):
    services = []
    for s in NetworkService.objects.filter(member__id=member.id):
        services.append(s)

    return services


def get_accounting_sources(member):
    accounting_sources = []
    for a in AccountingProfile.objects.filter(member__id=member.id):
        for acct_source in a.accounting_sources.all():
            accounting_sources.append(acct_source)

    return accounting_sources


def get_period(request):
    period = request.GET.get('period', '-7d')
    if period not in ['-1d', '-7d', '-30d', '-1y', '-5y']:
        return None
    return period
