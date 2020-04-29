#!/bin/python3

import os
import sys
import argparse

# argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--storage', help = 'Storage where to search for backups', required = True)
parser.add_argument('-o', '--days-old', help = 'How old can Backup be')
parser.add_argument('-v', '--vmid', help = "VMID's to check", )
args = vars(parser.parse_args())

# binaries
PVESM = "sudo /usr/sbin/pvesm"
PVECTL = "sudo /usr/bin/pvectl"
LXCLS = "sudo /usr/bin/lxc-ls"
QM = "sudo /usr/sbin/qm"

