#!/usr/bin/python3

import os
import sys
import argparse
import datetime
import re
import subprocess 


def main(args):

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
    if os.system('bash -c "{0} list {1} >/dev/null 2>&1"'.format(PVESM, backup_storage)) == 0:
        StorageList = subprocess.check_output(['{0} list {1}'.format(PVESM, backup_storage)], shell=True, executable='/bin/bash')
        StorageList = StorageList.splitlines()
        if args['verbose']:
            print ('Saved List:' + str(StorageList))
    else:
        print ("Critical - Storage {0} does not exist".format(backup_storage))
        sys.exit(CRITICAL)
    
    # Check Backup Storage type
    if os.system('bash -c "{0} list {1} | grep \' pbs-\'>/dev/null 2>&1"'.format(PVESM, backup_storage)) == 0:
        backup_storage_type = "pbs"
        if args['verbose']:
            print ("Given Storage is a Proxmox Backup Storage")
    else:
        backup_storage_type = "no-pbs"
        if args['verbose']:
            print ("Given Storage is NOT Proxmox Backup Storage")
    # Check VMID's and get Backups
    vmids = args['vmid']

    for vmid in vmids:
        vmtype = ''
        vmtype_pbs = ''
        backups = []
        string_tmp += ' VM/CT {0}:'.format(vmid)

        if len(vmid) < 3:
            string_tmp += "Invalid vmid"
            states.append(CRITICAL)
        if os.system('bash -c "{0} list | grep \'{1} \'  > /dev/null 2>&1"'.format(QM, vmid)) == 0:
            vmtype = 'qemu'
            vmtype_pbs = 'vm'
        else:
            print ('bash -c "{0} | grep \'{1} \'  > /dev/null 2>&1"'.format(LXCLS, vmid))
            if os.system('bash -c "{0} | grep \'{1} \'  > /dev/null 2>&1"'.format(LXCLS, vmid)) == 0:
                
                vmtype = 'lxc'
                vmtype_pbs = 'ct'
            else:
                string_tmp += "VM/CT {0} does not exist ".format(vmid)
                states.append(UNKNOWN)

        for backup in StorageList:
            if args['verbose']:
                print ('Inspecting:' + str(backup))                
            if backup_storage_type == "no-pbs":
                if 'vzdump-{0}-{1}'.format(vmtype, vmid) in str(backup):
                    backups.append(str(backup))
                    if args['verbose']:
                        print('Append: ' + str(backup))
            else:
                if '/{0}/{1}/'.format(vmtype_pbs, vmid) in str(backup):
                    backups.append(str(backup))
                    if args['verbose']:
                        print('Append: ' + str(backup))

    
        if vmtype == None:
            string_tmp += 'No backups of vm {0}'.format(vmid)
            states.append(CRITICAL)

        # Get date string
        if vmtype != None:
        


            if len(backups) != 0:
                last_item = backups[-1]
                if backup_storage_type == "no-pbs":
                    backup_date = re.search(r"\d{4}\_\d{2}\_\d{2}\-\d{2}\_\d{2}\_\d{2}", last_item).group()
                    backup_date_obj  = datetime.datetime.strptime(backup_date, '%Y_%m_%d-%H_%M_%S')
                else:
                    backup_date = re.search(r"\d{4}\-\d{2}\-\d{2}T\d{2}\:\d{2}\:\d{2}Z", last_item).group()
                    backup_date_obj  = datetime.datetime.strptime(backup_date, '%Y-%m-%dT%H:%M:%SZ')
                try:
                    size = round(int(last_item.rsplit(" ", 2)[-2][:-1])*9.3132257461548E-9, 2)
                except:
                    size = round(int(last_item.rsplit(" ", 2)[-1][:-1])*9.3132257461548E-9, 2)  
                
                if args['verbose']:
                    print('Last Backup:' + backup_date)
                              
                backup_check_warn = backup_date_obj + datetime.timedelta(days=int(args['warning']))
                backup_check_crit = backup_date_obj + datetime.timedelta(days=int(args['critical']))

                # Check last backup
                if datetime.datetime.now() >= backup_check_crit:
                    string_tmp += ' Total backups: {0}. Last backup: {1}. Size: {2}GiB;'.format(len(backups), backup_date_obj, size) 
                    states.append(CRITICAL)
                if datetime.datetime.now() >= backup_check_warn:
                    string_tmp += ' Total backups: {0}. Last backup: {1}. Size: {2}GiB;'.format(len(backups), backup_date_obj, size)
                    states.append(WARNING)
                else:
                    string_tmp += ' Total backups: {0}. Last backup: {1}. Size: {2}GiB;'.format(len(backups), backup_date_obj, size)
                    states.append(OK)
            else:
                string_tmp += ' No backups found'
                states.append(CRITICAL)

    #  Check states 
    if CRITICAL in states:
        print ('CRITICAL -{0}'.format(string_tmp))
        sys.exit(CRITICAL)
    if WARNING in states and CRITICAL not in states and UNKNOWN not in states:
        print ('WARNING -{0}'.format(string_tmp))
        sys.exit(WARNING)
    if UNKNOWN in states and CRITICAL not in states and WARNING not in states:
        print ('UNKNOWN -{0}'.format(string_tmp))
        sys.exit(UNKNOWN)
    if OK in states and UNKNOWN not in states and CRITICAL not in states and WARNING not in states:
        print ('OK -{0}'.format(string_tmp))
        sys.exit(OK)


if __name__ == "__main__":
    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--storage', help = 'Storage where to search for backups', required = True)
    parser.add_argument('-c', '--critical', help = 'How old can Backup be (Critical)', default=3)
    parser.add_argument('-w', '--warning', help = 'How old can Backup be (Critical)', default=2)
    parser.add_argument('-v', '--vmid', help = "VMID's to check", required = True, action='append')
    parser.add_argument('--verbose', help='Turns on verbose mode', action='store_true')
    args = vars(parser.parse_args())

    main(args)