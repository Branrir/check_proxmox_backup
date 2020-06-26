# Nagios SNMP Bandwidth check

Nagios Check for Proxmox Backups.

## Example output (with performance data):

OK - VM 101: 3 total backups of vm 101. Last backup is from 2020-06-19 00:02:26. Size: 103.93GiB;

## For Python requirements run:

sudo pip3 install -r requirements

## Installation:

Run following on remote server:

```bash
cd /usr/lib/nagios/plugins
wget https://raw.githubusercontent.com/Branrir/check_proxmox_backup/master/check_proxmox_backup.py
chmod +x check_proxmox_backups.py
```
## 

| Parameter | Description |
| --- | --- |
| -h, --help | Shows help |
| -v, --vmid | VM ID to check, can de used multiple times | 
| -s, --storage | Storage where backups are located |
| --verbose | Verbose mode, shows all variables (for debugging) | 
| -w, --warning | Warning value (days old) |
| -c, --critical | Critical value (days old) |

Example usage:
```bash
/usr/check_proxmox_backup.py -s Backup -v 101  -c 10 -w 8
```
Output: 
```bash
OK - VM 101: 3 total backups of vm 101. Last backup is from 2020-06-19 00:02:26. Size: 103.93GiB;
```

