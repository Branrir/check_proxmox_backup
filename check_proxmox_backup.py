#!/usr/bin/python3

import os
import sys
import argparse
import datetime
import timedelta
import re
import subprocess 


# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--storage', help = 'Storage where to search for backups', required = True)
parser.add_argument('-c', '--critical', help = 'How old can Backup be (Critical)', default=3)
parser.add_argument('-w', '--warning', help = 'How old can Backup be (Critical)', default=2)
parser.add_argument('-v', '--vmid', help = "VMID's to check", required = True, action='append')
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
string_tmp = ''

# Check if Backup Storage exist
backup_storage = args['storage']
if os.system('bash -c "{0} list {1}"'.format(PVESM, backup_storage)) == 0:
    StorageList = subprocess.check_output(['{0} list {1}'.format(PVESM, backup_storage)], shell=True, executable='/bin/bash')
    StorageList = StorageList.splitlines()
    #StorageList = subprocess.run(['bash', '-c', '{0} list {1}'.format(PVESM, backup_storage)], stdout=subprocess.PIPE).stdout
else:
    print ("Critical - Storage {0} does not exist".format(backup_storage))
    sys.exit(CRITICAL)

# Check VMID's and get Backups
vmids = args['vmid']

for vmid in vmids:
    vmtype = ''
    backups = []
    string_tmp += 'VM {0}:'.format(vmid)
    
    if len(vmid) < 3:
        string_tmp += "Invalid vmid"
        states.append(CRITICAL)
    if os.system('bash -c "{0} list | grep {1} > /dev/null 2>&1"'.format(QM, vmid)) == 0:
        vmtype = 'qemu'
    else:
        string_tmp += "VM {0} does not exist".format(vmid)
        states.append(UNKNOWN)

    for backup in StorageList:
        #print (backup)
        if 'vzdump-{0}-{1}'.format(vmtype, vmid) in str(backup):
            backups.append(str(backup))

    
    if len(backups) == 0:
        string_tmp += 'No backups of vm {0}'.format(vmid)
        states.append(CRITICAL)

    # Get date string    
    last_item = backup[-1]
    print(last_item)
    backup_date = re.search("([0-9]{4}\_[0-9]{2}\[0-9]{2}\-[0-9]{2}\_[0-9]{2}\_[0-9]{2})", last_item)
    backup_date_obj  = datetime.strptime(backup_date, '%y_%m_%d-%H_%M_%S')
    backup_check_warn = backup_date_obj - timedelta(days=args['warning'])
    backup_check_crit = backup_date_obj - timedelta(days=args['critical'])

    # Check last backup
    if datetime.now() >= backup_check_crit:
        string_tmp += '{} total backups of vm {}. Last backup is from {}. Size: ${}MB'.format(len(backups), vmid, backup_date_obj, 'placeholder') 
        states.append(CRITICAL)
    if datetime.now() >= backup_check_warn:
        string_tmp += '{} total backups of vm {}. Last backup is from {}. Size: ${}MB'.format(len(backups), vmid, backup_date_obj, 'placeholder')
        states.append(WARNING)
    else:
        string_tmp += '{} total backups of vm {}. Last backup is from {}. Size: ${}MB'.format(len(backups), vmid, backup_date_obj, 'placeholder')
        states.append(OK)


#  Check states 
if CRITICAL in states:
    print ('CRITICAL - {}')
    sys.exit(CRITICAL)
if WARNING in states and CRITICAL not in states and UNKNOWN not in states:
    print ('WARNING - {}')
    sys.exit(WARNING)
if UNKNOWN in states and CRITICAL not in states and WARNING not in states:
    print ('UNKNOWN - {}')
    sys.exit(UNKNOWN)
if OK in states and UNKNOWN not in states and CRITICAL not in states and WARNING not in states:
    print ('OK - {}')
    sys.exit(OK)