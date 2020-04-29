#!/usr/bin/python3

import os
import sys
import argparse
import datetime
import timedelta
import re


# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--storage', help = 'Storage where to search for backups', required = True)
parser.add_argument('-c', '--critical', help = 'How old can Backup be (Critical)', default=3)
parser.add_argument('-w', '--warning', help = 'How old can Backup be (Critical)', default=2)
parser.add_argument('-v', '--vmid', help = "VMID's to check", required = True)
args = vars(parser.parse_args())

# Return codes
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

# binaries
PVESM = "sudo /usr/sbin/pvesm"
PVECTL = "sudo /usr/bin/pvectl"
LXCLS = "sudo /usr/bin/lxc-ls"
QM = "sudo /usr/sbin/qm"

# Temp vars
states = []

# Check if Backup Storage exist
backup_storage = args.storage
if os.system('{0} lsit {1}'.format(PVESM, backup_storage)):
    StorageList = os.system('{0} lsit {1}'.format(PVESM, backup_storage))
else:
    print ("Critical - Storage {0} does not exist")
    sys.exit(CRITICAL)

# Check VMID's and get Backups
vmids = args.vmid

for vmid in vmids:
    vmtype = ''
    backups = []
    
    if vmid < 3:
        print ("Critical - Invalid vmid")
        sys.exit(CRITICAL)
    if os.system('{0} list |grep $ID > /dev/null 2>&1'.format(QM)):
        vmtype = 'qemu'
    else:
        print ("Unknown - VM {vmid} does not exist".format(vmid))
        sys.exit(UNKNOWN)

    for backup in StorageList:
        if 'vzdump-{}-{}'.format(vmtype, vmid) in backup:
            backups.append(backup)

    if len(backups) == 0:
        print ('Critical - No backups of vm {0}'.format(vmid))
        sys.exit(CRITICAL)

    # Get date string    
    last_item = backup[-1]
    backup_date = re.search("([0-9]{4}\_[0-9]{2}\[0-9]{2}\-[0-9]{2}\_[0-9]{2}\_[0-9]{2})", last_item)
    backup_date_obj  = datetime.strptime(backup_date, '%y_%m_%d-%H_%M_%S')
    backup_check_warn = backup_date_obj - timedelta(days=args.warning)
    backup_check_crit = backup_date_obj - timedelta(days=args.critical)

    # Check last backup
    if datetime.now() >= backup_check_warn:
        print ('Critical - {} total backups of vm {}. Last backup is from {}. Size: ${}MB'.format(len(backups), vmid, backup_date_obj, 'placeholder')) 
