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
    Udp6TransportTarget,
)

from sidekick.models import (
    AccountingProfile,
    NetworkService,
)

from ipaddress import ip_address

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
    'ae', 'et', 'ge', 'irb', 'lt', 'xe',
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


def get_pysnmp_udp_transport_target(ipaddress):
    ip = ip_address(ipaddress)

    if ip.version == 4:
        return UdpTransportTarget((ipaddress, 161))
    else:
        return Udp6TransportTarget((ipaddress, 161))


def snmpget(remote_ip, community, oid):
    pysnmp_udp_transport_target = get_pysnmp_udp_transport_target(remote_ip)

    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community),
        pysnmp_udp_transport_target,
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


def snmpwalk(remote_ip, community, oid):
    _results = []
    pysnmp_udp_transport_target = get_pysnmp_udp_transport_target(remote_ip)

    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            pysnmp_udp_transport_target,
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


def snmpwalk_bulk_accounting(remote_ip, community):
    data = []
    isps = {}
    class_names = {}
    scu_bytes = {}
    dcu_bytes = {}

    jnxScuStatsClName_re = r'.*2636\.3\.16\.1\.1\.1\.6\.(\d+)\.(\d+)\.(\d+)\.(\d+)\.(.+)'
    jnxDcuStatsClName_re = r'.*2636\.3\.6\.2\.1\.6\.(\d+)\.(\d+)\.(\d+)\.(.+)'
    jnxScuStatsBytes_re = r'.*2636\.3\.16\.1\.1\.1\.5\.(\d+)\.1\.(\d+)\.(.+)'
    jnxDcuStatsBytes_re = r'.*2636\.3\.6\.2\.1\.5\.(\d+)\.1\.(\d+)\.(.+)'

    pysnmp_udp_transport_target = get_pysnmp_udp_transport_target(remote_ip)

    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            pysnmp_udp_transport_target,
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
        isp_name = snmpget(remote_ip, community, _oid)
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


def snmpwalk_bulk(remote_ip, community):
    data = []
    results = {}
    ipv4_addresses = {}

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

    pysnmp_udp_transport_target = get_pysnmp_udp_transport_target(remote_ip)

    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            pysnmp_udp_transport_target,
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
                    results[index]['in_rate'] = int(in_rate) // 8
                continue

            # Match the jnx-specific entries
            match = re.match(jnxifHCOut1SecRate_re, f"{r[0]}")
            if match:
                index = f"{r[0]}".split('.')[-1]
                if index not in results:
                    results[index] = {}
                out_rate = r[1].prettyPrint()
                if out_rate != "No more variables left in this MIB View":
                    results[index]['out_rate'] = int(out_rate) // 8
                continue

            # Match the format IF-MIB::FOO
            match = re.match(oid_re, str(r[0].prettyPrint()))
            if match:
                # If this is not a special case,
                # do a simple parsing of the result
                if match[2] not in special:
                    index = f"{r[0]}".split('.')[-1]
                    if index not in results:
                        results[index] = {}
                    # sometimes one OID ends before the other
                    # during the SNMP walk and it would then return
                    # "No more variables left in this MIB View"
                    # on subsequent queries.
                    # Let us check if we already have a result
                    # so we do not overwrite the initial correct one
                    if match[2] not in results[index]:
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
                        ipv4_addresses[v4_address] = cidr

    # Loop through the results
    # and match the IP address with the netmask
    for k, v in results.items():
        if 'ipv4' not in results[k]:
            results[k]['ipv4'] = []

        if 'ipAdEntIfIndex' in v:
            for ipv4 in v['ipAdEntIfIndex']:
                if ipv4 in ipv4_addresses.keys():
                    results[k]['ipv4'].append(f"{ipv4}/{ipv4_addresses[ipv4]}")

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
    target_in = f"sumSeries(scale(keepLastValue({service_name}.*.*.in_octets), 8))"
    target_out = f"sumSeries(scale(keepLastValue({service_name}.*.*.out_octets), -8))"
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

    # 95th Percentile
    query = f"{query}&target=scale(nPercentile(sum({targets_in}), 95), 8)"
    query = f"{query}&target=scale(nPercentile(sum({targets_out}), 95), -8)"

    r = requests.get(query)
    results = json.loads(r.content.decode('utf-8'))
    if len(results) == 0:
        results = [
            {'datapoints': [[0, 0]]},
            {'datapoints': [[0, 0]]},
            {'datapoints': [[0, 0]]},
            {'datapoints': [[0, 0]]},
        ]

    graph_data = {}
    data = [[], [], [], [], []]

    for d in results[0]['datapoints']:
        data[0].append(d[1])
        data[1].append(d[0])

    for d in results[1]['datapoints']:
        data[2].append(d[0])

    if len(results) > 2:
        for d in results[2]['datapoints']:
            data[3].append(d[0])

    if len(results) > 3:
        for d in results[3]['datapoints']:
            data[4].append(d[0])

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
        for prefix in network_service.get_prefixes():
            if prefix not in prefixes[member_id]['prefixes']:
                prefixes[member_id]['prefixes'].append(prefix)
        prefixes[member_id]['prefixes'].sort()
    return prefixes


def get_services_for_graphite(member):
    services = {}
    for s in NetworkService.objects.filter(member__id=member.id):
        services[s.id] = s

    return services.values()


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


# ============================================================
# ClickHouse Query Utilities (Approach A: coexist with Graphite)
# ============================================================

import logging

_ch_logger = logging.getLogger('sidekick.clickhouse')
_ch_logger.setLevel(logging.INFO)
# If no handler is attached, add a simple one so we don't lose logs
if not _ch_logger.handlers:
    class NullHandler(logging.NullHandler if hasattr(logging, 'NullHandler') else logging.Handler):
        pass
    _ch_logger.addHandler(NullHandler())


def _get_clickhouse_client_from_config(config):
    """Create a ClickHouseHTTP client from PLUGINS_CONFIG['sidekick'] settings."""
    from .clickhouse import ClickHouseHTTP
    url = config.get('clickhouse_url')
    if not url:
        return None
    return ClickHouseHTTP(
        base_url=url,
        user=config.get('clickhouse_user', 'default'),
        password=config.get('clickhouse_password', ''),
        database=config.get('clickhouse_database', 'pmacct'),
    )


def _period_to_interval(period):
    """Convert a Graphite-style period string to a ClickHouse INTERVAL value."""
    period_map = {
        '-1d': '1 DAY',
        '-7d': '7 DAY',
        '-30d': '30 DAY',
        '-1y': '1 YEAR',
        '-1Y': '1 YEAR',
        '-5y': '5 YEAR',
    }
    return period_map.get(period)


def _get_graph_title(period):
    """Return the display title for a given period."""
    title_map = {
        '-1d': 'Last Day - GB',
        '-7d': 'Last Week - GB',
        '-30d': 'Last Month - GB',
        '-1y': 'Last Year - GB',
        '-1Y': 'Last Year - GB',
        '-5y': 'Last 5 Years - GB',
    }
    return title_map.get(period, 'Unknown Period')


def _parse_clickhouse_tsv(result_text):
    """Parse ClickHouse TabSeparatedWithNames output into a list of lists (rows of values).
    
    The first row is the header (column names), which is stripped. Returns a list of
    rows, where each row is a list of values (strings, ints, or floats).
    """
    if not result_text or not result_text.strip():
        return []
    lines = result_text.strip().split('\n')
    if len(lines) <= 1:
        # Only header or empty
        return []
    # Skip header (first line), parse remaining
    rows = []
    for line in lines[1:]:
        if not line:
            continue
        row = []
        for val in line.split('\t'):
            v = val.strip()
            if v == '' or v == '\\N':
                row.append(None)
            else:
                try:
                    if '.' in v:
                        row.append(float(v))
                    else:
                        row.append(int(v))
                except (ValueError, TypeError):
                    row.append(v)
        rows.append(row)
    return rows


def _escape_clickhouse_string(s):
    """Escape a string for safe inclusion in a ClickHouse SQL literal.
    
    ClickHouse uses single quotes; internal single quotes are escaped by doubling.
    """
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"


def _execute_clickhouse(ch_client, query):
    """Execute a ClickHouse query and return parsed rows (list of lists).
    
    Returns (rows, raw_query) where rows is a list of parsed rows and
    raw_query is the full SQL used (for debugging/debug display).
    Appends FORMAT TabSeparatedWithNames to the query.
    Logs errors to the 'sidekick.clickhouse' logger.
    """
    full_query = query + "\nFORMAT TabSeparatedWithNames"
    try:
        result = ch_client.execute(full_query)
        rows = _parse_clickhouse_tsv(result)
        _ch_logger.debug("ClickHouse query returned %d rows", len(rows))
        return rows, full_query
    except RuntimeError as e:
        # Log the error but don't crash — caller decides whether to fall back
        _ch_logger.error("ClickHouse query failed: %s | Query: %s", str(e), full_query[:500])
        return [], full_query
    except Exception as e:
        # Catch-all for any other unexpected errors
        _ch_logger.error("ClickHouse unexpected error: %s | Query: %s", str(e), full_query[:500])
        return [], full_query


def _get_interface_ids_for_service(ch_client, member_name, service_name):
    """Query dim_interface_labels to find all interface_ids for a given member+service.
    
    Returns a list of interface_id strings for use in an IN clause.
    Logs a warning if no results found (dimension table may be out of sync).
    """
    query = (
        f"SELECT interface_id FROM dim_interface_labels "
        f"WHERE member_name = {_escape_clickhouse_string(member_name)} "
        f"AND service_name = {_escape_clickhouse_string(service_name)}"
    )
    rows, _ = _execute_clickhouse(ch_client, query)
    ids = [str(r[0]) for r in rows if r and r[0] is not None]
    if not ids:
        _ch_logger.warning("No interface_ids found for member='%s' service='%s' — check dim_interface_labels",
                          member_name, service_name)
    return ids


def _get_accounting_source_ids(ch_client, accounting_sources):
    """Query dim_accounting_sources to find accounting_source_ids for given AccountingSource objects.

    Returns a list of accounting_source_id strings for use in an IN clause.
    Uses (source_name, destination_name) pairs for the lookup.

    NOTE: destination_name is the raw CharField value from the model, not a related object's name.
    """
    if not accounting_sources:
        return []

    conditions = []
    for acct in accounting_sources:
        source_name = getattr(acct, 'name', '')
        # destination is a CharField on the model, not a ForeignKey
        dest_name = getattr(acct, 'destination', '') or ''
        conditions.append(
            f"(source_name = {_escape_clickhouse_string(source_name)} "
            f"AND destination_name = {_escape_clickhouse_string(dest_name)})"
        )

    query = (
        f"SELECT accounting_source_id FROM dim_accounting_sources "
        f"WHERE {' OR '.join(conditions)}"
    )
    rows, _ = _execute_clickhouse(ch_client, query)
    return [str(r[0]) for r in rows if r and r[0] is not None]


def _transpose_to_uplot(rows):
    """Convert ClickHouse TSV rows [[ts, in, out], ...] to uPlot column-oriented format.

    Returns [[timestamps], [in_vals], [out_vals]] for simple graphs.
    """
    if not rows:
        return [[], [], []]
    timestamps = []
    in_vals = []
    out_vals = []
    for row in rows:
        if row and len(row) >= 3:
            timestamps.append(row[0])
            in_vals.append(row[1])
            out_vals.append(row[2])
    return [timestamps, in_vals, out_vals]


def _transpose_to_uplot_with_p95(rows, p95_in=0, p95_out=0):
    """Convert ClickHouse TSV rows to uPlot format with p95 constant lines.

    Returns [[timestamps], [in_vals], [out_vals], [p95_in]*n, [p95_out]*n].
    Matches the exact shape returned by get_graphite_data().
    """
    if not rows:
        return [[], [], [], [], []]
    timestamps = []
    in_vals = []
    out_vals = []
    for row in rows:
        if row and len(row) >= 3:
            timestamps.append(row[0])
            in_vals.append(row[1])
            out_vals.append(row[2])
    p95_in_vals = [p95_in] * len(timestamps)
    p95_out_vals = [p95_out] * len(timestamps)
    return [timestamps, in_vals, out_vals, p95_in_vals, p95_out_vals]


def get_clickhouse_nic_graph(nic, ch_client, period="-1Y"):
    """ClickHouse equivalent of get_graphite_nic_graph.
    
    Queries a single interface's traffic from nic_metrics_unified via dim_interface_labels.
    Returns the same JSON shape as get_graphite_nic_graph.
    """
    if ch_client is None:
        return None
    
    # Get device name and interface name from the NIC model
    # graphite_device_name() and graphite_interface_name() give the Graphite components
    # but for dim_interface_labels we need the NetBox names
    try:
        device_name = nic.interface.device.name
    except Exception:
        device_name = None
    
    try:
        interface_name = nic.interface.name
    except Exception:
        interface_name = None
    
    if not device_name or not interface_name:
        return None
    
    # Find the interface_id via dim_interface_labels
    interval = _period_to_interval(period)
    if interval is None:
        return None
    
    # Single combined query: find the interface_id and get the time series
    query = (
        f"SELECT "
        f"    toUnixTimestamp(bucket) AS timestamp, "
        f"    avg(CASE WHEN metric = 'in_octets' THEN delta ELSE 0 END) * 8 AS in_bps, "
        f"    avg(CASE WHEN metric = 'out_octets' THEN delta ELSE 0 END) * -8 AS out_bps "
        f"FROM nic_metrics_unified "
        f"WHERE interface_id IN ("
        f"    SELECT interface_id FROM dim_interface_labels "
        f"    WHERE device_name = {_escape_clickhouse_string(device_name)} "
        f"    AND interface_name = {_escape_clickhouse_string(interface_name)}"
        f") "
        f"AND metric IN ('in_octets', 'out_octets') "
        f"AND ts >= now() - INTERVAL {interval} "
        f"GROUP BY "
        f"    toStartOfInterval(ts, toIntervalMinute(5)) AS bucket "
        f"ORDER BY timestamp"
    )
    
    rows, full_query = _execute_clickhouse(ch_client, query)
    
    if not rows:
        # Return empty but valid structure
        return {
            'title': _get_graph_title(period),
            'data': [[], [], []],
            'query': full_query,
        }
    
    # Transpose: [[timestamps], [in], [out]]
    data = [[], [], []]
    for row in rows:
        if row and len(row) >= 3:
            data[0].append(row[0])  # timestamp
            data[1].append(row[1])  # in_bps
            data[2].append(row[2])  # out_bps
    
    return {
        'title': _get_graph_title(period),
        'data': data,
        'query': full_query,
    }


def get_clickhouse_service_graph(service, ch_client, period="-1Y"):
    """ClickHouse equivalent of get_graphite_service_graph.
    
    Queries all interfaces for a single NetworkService from nic_metrics_unified.
    Returns the same JSON shape as get_graphite_service_graph.
    """
    if ch_client is None:
        return None
    
    # Get member and service names from the NetworkService model
    try:
        member_name = service.member.name
    except Exception:
        member_name = None
    
    if not member_name:
        return None
    
    service_name = getattr(service, 'name', str(service))
    
    interval = _period_to_interval(period)
    if interval is None:
        return None
    
    # Sum all interfaces for this service
    query = (
        f"SELECT "
        f"    toUnixTimestamp(bucket) AS timestamp, "
        f"    sum(CASE WHEN metric = 'in_octets' THEN delta ELSE 0 END) * 8 AS in_bps, "
        f"    sum(CASE WHEN metric = 'out_octets' THEN delta ELSE 0 END) * -8 AS out_bps "
        f"FROM nic_metrics_unified "
        f"WHERE interface_id IN ("
        f"    SELECT interface_id FROM dim_interface_labels "
        f"    WHERE member_name = {_escape_clickhouse_string(member_name)} "
        f"    AND service_name = {_escape_clickhouse_string(service_name)}"
        f") "
        f"AND metric IN ('in_octets', 'out_octets') "
        f"AND ts >= now() - INTERVAL {interval} "
        f"GROUP BY "
        f"    toStartOfInterval(ts, toIntervalMinute(5)) AS bucket "
        f"ORDER BY timestamp"
    )
    
    rows, full_query = _execute_clickhouse(ch_client, query)
    
    if not rows:
        return {
            'title': _get_graph_title(period),
            'data': [[], [], []],
            'query': full_query,
        }
    
    data = [[], [], []]
    for row in rows:
        if row and len(row) >= 3:
            data[0].append(row[0])
            data[1].append(row[1])
            data[2].append(row[2])
    
    return {
        'title': _get_graph_title(period),
        'data': data,
        'query': full_query,
    }


def get_clickhouse_member_bandwidth(ch_client, member, services, accounting_sources, period="-1y"):
    """ClickHouse equivalent for member bandwidth (services + accounting + remaining + p95).

    Mirrors the combined behavior of get_graphite_service_graph + get_graphite_data for
    member bandwidth pages (MemberBandwidthDataView, NetworkUsageMemberView, etc.).

    Returns:
        {
            'service_data': {'data': [[ts], [in], [out], [p95_in], [p95_out]], 'query': '...'},
            'accounting_data': {'data': [[ts], [in], [out], [p95_in], [p95_out]], 'query': '...'},
            'remaining_data': {'data': [[ts], [in], [out], [p95_in], [p95_out]], 'query': '...'},
        }
    """
    if ch_client is None:
        return None

    try:
        member_name = member.name
    except Exception:
        return None

    interval = _period_to_interval(period)
    if interval is None:
        return None

    results = {
        'service_data': {'data': [[], [], [], [], []], 'query': ''},
        'accounting_data': {'data': [[], [], [], [], []], 'query': ''},
        'remaining_data': {'data': [[], [], [], [], []], 'query': ''},
    }

    # --- 1. Service Data ---
    service_interface_ids = []
    for svc in services:
        ids = _get_interface_ids_for_service(ch_client, member_name, svc.name)
        service_interface_ids.extend(ids)
    service_interface_ids = list(set(service_interface_ids))

    svc_rows = []
    if service_interface_ids:
        svc_query = (
            f"SELECT "
            f"    toUnixTimestamp(bucket) AS timestamp, "
            f"    sum(CASE WHEN metric = 'in_octets' THEN delta ELSE 0 END) * 8 AS in_bps, "
            f"    sum(CASE WHEN metric = 'out_octets' THEN delta ELSE 0 END) * -8 AS out_bps "
            f"FROM nic_metrics_unified "
            f"WHERE interface_id IN ({', '.join(service_interface_ids)}) "
            f"AND metric IN ('in_octets', 'out_octets') "
            f"AND ts >= now() - INTERVAL {interval} "
            f"GROUP BY toStartOfInterval(ts, toIntervalMinute(5)) AS bucket "
            f"ORDER BY timestamp"
        )
        svc_rows, full_query = _execute_clickhouse(ch_client, svc_query)
        results['service_data']['query'] = full_query
    else:
        results['service_data']['query'] = 'no service interfaces found'

    # --- 2. Accounting Data ---
    accounting_source_ids = _get_accounting_source_ids(ch_client, accounting_sources)

    acct_rows = []
    if accounting_source_ids:
        acct_query = (
            f"SELECT "
            f"    toUnixTimestamp(bucket) AS timestamp, "
            f"    sum(CASE WHEN metric = 'in_octets' THEN delta ELSE 0 END) * 8 AS in_bps, "
            f"    sum(CASE WHEN metric = 'out_octets' THEN delta ELSE 0 END) * -8 AS out_bps "
            f"FROM nic_metrics_unified "
            f"WHERE accounting_source_id IN ({', '.join(accounting_source_ids)}) "
            f"AND metric IN ('in_octets', 'out_octets') "
            f"AND ts >= now() - INTERVAL {interval} "
            f"GROUP BY toStartOfInterval(ts, toIntervalMinute(5)) AS bucket "
            f"ORDER BY timestamp"
        )
        acct_rows, full_query = _execute_clickhouse(ch_client, acct_query)
        results['accounting_data']['query'] = full_query
    else:
        results['accounting_data']['query'] = 'no accounting sources found'

    # --- 3. Compute P95s ---
    def _calc_p95(rows):
        in_vals = [r[1] for r in rows if r and len(r) >= 2 and r[1] is not None]
        out_vals = [r[2] for r in rows if r and len(r) >= 3 and r[2] is not None]
        p95_in = 0
        p95_out = 0
        if in_vals:
            in_sorted = sorted(in_vals)
            idx = int(len(in_sorted) * 0.95)
            p95_in = in_sorted[min(idx, len(in_sorted) - 1)]
        if out_vals:
            out_sorted = sorted(out_vals)
            idx = int(len(out_sorted) * 0.95)
            p95_out = out_sorted[min(idx, len(out_sorted) - 1)]
        return p95_in, p95_out

    svc_p95_in, svc_p95_out = _calc_p95(svc_rows)
    acct_p95_in, acct_p95_out = _calc_p95(acct_rows)

    # --- 4. Remaining (Services - Accounting, only positive) ---
    svc_map = {}
    for row in svc_rows:
        if row and len(row) >= 3:
            svc_map[row[0]] = [row[1], row[2], 0, 0]
    for row in acct_rows:
        if row and len(row) >= 3:
            if row[0] in svc_map:
                svc_map[row[0]][2] = row[1]
                svc_map[row[0]][3] = row[2]

    remaining_rows = []
    for ts, vals in sorted(svc_map.items()):
        rem_in = max(0, vals[0] - vals[2])
        rem_out = min(0, vals[1] - vals[3])
        remaining_rows.append([ts, rem_in, rem_out])

    rem_p95_in, rem_p95_out = _calc_p95(remaining_rows)

    # --- 5. Transpose all datasets to uPlot column-oriented format ---
    results['service_data']['data'] = _transpose_to_uplot_with_p95(svc_rows, svc_p95_in, svc_p95_out)
    results['accounting_data']['data'] = _transpose_to_uplot_with_p95(acct_rows, acct_p95_in, acct_p95_out)
    results['remaining_data']['data'] = _transpose_to_uplot_with_p95(remaining_rows, rem_p95_in, rem_p95_out)
    results['remaining_data']['query'] = 'computed in Python (services - accounting)'

    return results


def get_clickhouse_service_group_bandwidth(ch_client, service_group, period="-1y"):
    """ClickHouse equivalent for service group bandwidth (multi-member aggregation).

    Handles the NetworkServiceGroup case where services span multiple members.
    For each member in the group, fetches service + accounting data, then sums across.

    Args:
        ch_client: ClickHouseHTTP client.
        service_group: A NetworkServiceGroup model instance.
        period: Period string (e.g., '-1y').

    Returns:
        {
            'service_data': {'data': [[ts], [in], [out], [p95_in], [p95_out]], 'query': '...'},
            'accounting_data': {'data': [[ts], [in], [out], [p95_in], [p95_out]], 'query': '...'},
            'remaining_data': {'data': [[ts], [in], [out], [p95_in], [p95_out]], 'query': '...'},
        }
    """
    if ch_client is None:
        return None

    interval = _period_to_interval(period)
    if interval is None:
        return None

    results = {
        'service_data': {'data': [[], [], [], [], []], 'query': ''},
        'accounting_data': {'data': [[], [], [], [], []], 'query': ''},
        'remaining_data': {'data': [[], [], [], [], []], 'query': ''},
    }

    # Collect all unique member+service pairs and their accounting sources
    member_services_map = {}    # member_name -> [service_name, ...]
    member_accounting_map = {}  # member_name -> [AccountingSource, ...]

    for network_service in service_group.network_services.all():
        member = network_service.member
        member_name = member.name

        if member_name not in member_services_map:
            member_services_map[member_name] = []
        member_services_map[member_name].append(network_service.name)

        if member_name not in member_accounting_map:
            member_accounting_map[member_name] = get_accounting_sources(member)

    # Resolve all interface IDs and accounting source IDs now that the maps are built
    all_service_interface_ids = []
    all_accounting_source_ids = []

    for member_name, svc_names in member_services_map.items():
        for svc_name in svc_names:
            ids = _get_interface_ids_for_service(ch_client, member_name, svc_name)
            all_service_interface_ids.extend(ids)

    for member_name, acct_sources in member_accounting_map.items():
        ids = _get_accounting_source_ids(ch_client, acct_sources)
        all_accounting_source_ids.extend(ids)

    all_service_interface_ids = list(set(all_service_interface_ids))
    all_accounting_source_ids = list(set(all_accounting_source_ids))

    # --- 1. Service Data (sum across all interfaces in the group) ---
    svc_rows = []
    if all_service_interface_ids:
        svc_query = (
            f"SELECT "
            f"    toUnixTimestamp(bucket) AS timestamp, "
            f"    sum(CASE WHEN metric = 'in_octets' THEN delta ELSE 0 END) * 8 AS in_bps, "
            f"    sum(CASE WHEN metric = 'out_octets' THEN delta ELSE 0 END) * -8 AS out_bps "
            f"FROM nic_metrics_unified "
            f"WHERE interface_id IN ({', '.join(all_service_interface_ids)}) "
            f"AND metric IN ('in_octets', 'out_octets') "
            f"AND ts >= now() - INTERVAL {interval} "
            f"GROUP BY toStartOfInterval(ts, toIntervalMinute(5)) AS bucket "
            f"ORDER BY timestamp"
        )
        svc_rows, full_query = _execute_clickhouse(ch_client, svc_query)
        results['service_data']['query'] = full_query
    else:
        results['service_data']['query'] = 'no service interfaces found in group'

    # --- 2. Accounting Data (sum across all accounting sources in the group) ---
    acct_rows = []
    if all_accounting_source_ids:
        acct_query = (
            f"SELECT "
            f"    toUnixTimestamp(bucket) AS timestamp, "
            f"    sum(CASE WHEN metric = 'in_octets' THEN delta ELSE 0 END) * 8 AS in_bps, "
            f"    sum(CASE WHEN metric = 'out_octets' THEN delta ELSE 0 END) * -8 AS out_bps "
            f"FROM nic_metrics_unified "
            f"WHERE accounting_source_id IN ({', '.join(all_accounting_source_ids)}) "
            f"AND metric IN ('in_octets', 'out_octets') "
            f"AND ts >= now() - INTERVAL {interval} "
            f"GROUP BY toStartOfInterval(ts, toIntervalMinute(5)) AS bucket "
            f"ORDER BY timestamp"
        )
        acct_rows, full_query = _execute_clickhouse(ch_client, acct_query)
        results['accounting_data']['query'] = full_query
    else:
        results['accounting_data']['query'] = 'no accounting sources found in group'

    # --- 3. Compute P95s ---
    def _calc_p95(rows):
        in_vals = [r[1] for r in rows if r and len(r) >= 2 and r[1] is not None]
        out_vals = [r[2] for r in rows if r and len(r) >= 3 and r[2] is not None]
        p95_in = 0
        p95_out = 0
        if in_vals:
            in_sorted = sorted(in_vals)
            idx = int(len(in_sorted) * 0.95)
            p95_in = in_sorted[min(idx, len(in_sorted) - 1)]
        if out_vals:
            out_sorted = sorted(out_vals)
            idx = int(len(out_sorted) * 0.95)
            p95_out = out_sorted[min(idx, len(out_sorted) - 1)]
        return p95_in, p95_out

    svc_p95_in, svc_p95_out = _calc_p95(svc_rows)
    acct_p95_in, acct_p95_out = _calc_p95(acct_rows)

    # --- 4. Remaining (Services - Accounting, only positive) ---
    svc_map = {}
    for row in svc_rows:
        if row and len(row) >= 3:
            svc_map[row[0]] = [row[1], row[2], 0, 0]
    for row in acct_rows:
        if row and len(row) >= 3:
            if row[0] in svc_map:
                svc_map[row[0]][2] = row[1]
                svc_map[row[0]][3] = row[2]

    remaining_rows = []
    for ts, vals in sorted(svc_map.items()):
        rem_in = max(0, vals[0] - vals[2])
        rem_out = min(0, vals[1] - vals[3])
        remaining_rows.append([ts, rem_in, rem_out])

    rem_p95_in, rem_p95_out = _calc_p95(remaining_rows)

    # --- 5. Transpose to uPlot column-oriented format ---
    results['service_data']['data'] = _transpose_to_uplot_with_p95(svc_rows, svc_p95_in, svc_p95_out)
    results['accounting_data']['data'] = _transpose_to_uplot_with_p95(acct_rows, acct_p95_in, acct_p95_out)
    results['remaining_data']['data'] = _transpose_to_uplot_with_p95(remaining_rows, rem_p95_in, rem_p95_out)
    results['remaining_data']['query'] = 'computed in Python (services - accounting)'

    return results


def _service_has_clickhouse_backend(settings):
    """Check if the sidekick plugin is configured to use ClickHouse for queries.
    
    Reads from PLUGINS_CONFIG['sidekick']['use_clickhouse'].
    Returns (True, ch_client) if ClickHouse should be used, (False, None) otherwise.
    """
    config = settings.PLUGINS_CONFIG.get('sidekick', {})
    use_clickhouse = config.get('use_clickhouse', False)
    if not use_clickhouse:
        return (False, None)
    ch_client = _get_clickhouse_client_from_config(config)
    if ch_client is None:
        _ch_logger.warning("use_clickhouse is True but no clickhouse_url configured — falling back to Graphite")
        return (False, None)
    return (use_clickhouse, ch_client)
