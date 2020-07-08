#!/usr/bin/python3
# Check for QNAP-NAS
# Version: 0.1

from pysnmp import hlapi
import argparse

"""
Quick SNMP - https://github.com/alessandromaggio/quicksnmp/blob/master/quicksnmp.py
"""
    
def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def construct_value_pairs(list_of_pairs):
    pairs = []
    for key, value in list_of_pairs.items():
        pairs.append(hlapi.ObjectType(hlapi.ObjectIdentity(key), value))
    return pairs


def get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def set(target, value_pairs, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.setCmd(
    engine,
    credentials,
    hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_value_pairs(value_pairs)
    )
    return fetch(handler, 1)[0]


def get_bulk(target, oids, credentials, count, start_from=0, port=161,
            engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value


def fetch(handler, count):
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = cast(var_bind[1])
                result.append(items)
            else:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result

"""
End of Quicksnmp
"""

# return codes
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3

nagiosprefixes = {
    OK: "OK",
    WARNING: "WARNING",
    CRITICAL: "CRITICAL",
    UNKNOWN: "UNKNOWN"
}

def main(args):

    import sys
    import datetime


    critical_temp = args.critical
    warning_temp = args.warning
    host = args.host
    exclude = args.exclude
    oid_temp = '.1.3.6.1.4.1.24681.1.2.6.0'
    oid_hostname = '.1.3.6.1.4.1.24681.1.2.13.0'
    oid_diskIndex = '.1.3.6.1.4.1.24681.1.2.10.0'
    oid_diskSerial = '.1.3.6.1.4.1.24681.1.2.11.1.5.'
    oid_diskHealth =  '.1.3.6.1.4.1.24681.1.2.11.1.7.'
    oid_diskLabel = '.1.3.6.1.4.1.24681.1.2.11.1.2.'
    oid_raidIndex = '.1.3.6.1.4.1.24681.1.2.16.0'
    oid_raidState = '.1.3.6.1.4.1.24681.1.2.17.1.6.'
    oid_raidLabel = '.1.3.6.1.4.1.24681.1.2.17.1.2.'
    oid_uptime = '.1.3.6.1.4.1.24681.1.2.4.0'

    STATES = []
    str_tmp = ""

    # get current values
    try:
        values = get(host, [oid_uptime, oid_temp, oid_hostname, oid_diskIndex, oid_raidIndex], hlapi.CommunityData(args.community))
    except:
        print ("UNKNOWN - SNMP on host {0} not available".format(host))
        sys.exit(UNKNOWN)
    
    temp = str(values.get(oid_temp[1:])).split(' ', 1)[0]
    diskIndex = values.get(oid_diskIndex[1:])
    raidIndex = values.get(oid_raidIndex[1:])
    
    uptime = values.get(oid_uptime[1:])
    uptime  = datetime.timedelta(seconds=uptime/100)

    # temp check

    if temp >= critical_temp:
        STATES.append(CRITICAL)
        str_tmp = str_tmp + " Temp: {0} °C".format(temp)
    if temp >= warning_temp and temp <= critical_temp:
        STATES.append(WARNING)
        str_tmp = str_tmp + " Temp: {0} °C".format(temp)

    
    # disks check
    i = 1
    disks = []
    while i <= diskIndex:
        oid_diskSerial_i = oid_diskSerial + str(i)
        oid_diskHealth_i = oid_diskHealth + str(i)
        oid_diskLabel_i = oid_diskLabel + str(i)
        diskSerial = get(host, [oid_diskSerial_i], hlapi.CommunityData(args.community)).get(oid_diskSerial_i[1:])
        diskHealth =  get(host, [oid_diskHealth_i], hlapi.CommunityData(args.community)).get(oid_diskHealth_i[1:])
        diskLabel =  get(host, [oid_diskLabel_i], hlapi.CommunityData(args.community)).get(oid_diskLabel_i[1:])
        if diskHealth != 'GOOD':
            STATES.append(CRITICAL)
            str_tmp  = str_tmp + " DRIVE: {0} STATE: {1};".format(diskSerial, diskHealth)
        disks.append((diskLabel, diskSerial, diskHealth))
        i += 1

    
    # RAID check
    i = 1
    raids = []
    while i <= raidIndex:
        oid_raidState_i = oid_raidState + str(i)
        oid_raidLabel_i = oid_raidLabel + str(i)
        raidState = get(host, [oid_raidState_i], hlapi.CommunityData(args.community)).get(oid_raidState_i[1:])
        raidLabel = get(host, [oid_raidLabel_i], hlapi.CommunityData(args.community)).get(oid_raidLabel_i[1:])
        if raidState != 'Ready':
            STATES.append(CRITICAL)
            str_tmp = str_tmp + " RAID: {0} State: {1}".format(raidLabel, raidState)
        raids.append((raidLabel, raidState))
        i += 1

    # OK String

    str_ok = ''
    for disk in disks:
        str_ok = str_ok + "Disk: {0} Serial: {1} State: {2}; \n".format(disk[0], disk[1], disk[2])
    for raid in raids:
        str_ok = str_ok + "Raid: {0} State: {1}".format(raid[0],raid[1])


    if CRITICAL in STATES:
        print ("CRITICAL - " + str_tmp)
        sys.exit(CRITICAL)
    if WARNING in STATES and CRITICAL not in STATES:
        print ("UNKNOWN - " + str_tmp)
        sys.exit(WARNING)
    else:
        print ("OK - Uptime: {0} \n".format(uptime) + str_ok)
        sys.exit(OK)



if __name__ == "__main__":
    # argsparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='QNAP-NAS Host Address', required=True)
    parser.add_argument('-c', '--critical', help='Critical Value for Temp', default='65')
    parser.add_argument('-w', '--warning', help='Warning Value for Temp', default='60')
    parser.add_argument('-x', '--exclude', help='Checks to exclude', action='append')
    parser.add_argument('-C', '--community', help='SNMP Community', required=True)
    args = parser.parse_args()
    main(args)
