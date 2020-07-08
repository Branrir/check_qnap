# Nagios QNAP-NAS check

Nagios Check for QNAP-NAS used to monitor temperature, disk health and RAID status.

## For Python requirements run:

sudo pip3 install -r requirements

## Installation:

```bash
cd /usr/lib/nagios/plugins
wget https://raw.githubusercontent.com/Branrir/check_qnap/master/check_qnap.py
chmod +x check_qnap.py
```
## 

| Parameter | Description |
| --- | --- |
| -h, --help | Shows help |
| -H, --host | Hostaddress |
| -C, --communityName | SNMP v2c CommunityNamme |
| -w, --warning | Warning value in °C |
| -c, --critical | Critical value in °C |

Example usage:
```bash
/usr/lib/nagios/plugins/check_qnap.py -C public -H 10.10.25.33
```
Output: 
```bash
OK - Uptime: 3 days, 6:29:49.640000 
Disk: HDD1 Serial: WD30EFRX-68EUZN0
 State: GOOD; 
Disk: HDD2 Serial: WD3000F9YZ-09N20
 State: GOOD; 
Disk: HDD3 Serial: ST3000VX000-1ES1
 State: GOOD; 
Disk: HDD4 Serial: WD30EURS-63R8UY0
 State: GOOD; 
Raid: [RAID6 Disk Volume: Drive 1 2 3 4] State: Ready
```

-------
Special thanks to Alessandro Maggio for https://github.com/alessandromaggio/quicksnmp
