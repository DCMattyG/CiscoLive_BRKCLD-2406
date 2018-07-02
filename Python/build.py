"""
DOCSTRING
"""

import os
import sys
import json
import time
import datetime
import threading
import argparse
from subprocess import Popen, DEVNULL
from ucsd.ucsd_module import JsonObj, get_os, set_ucsd_addr, get_ucsd_addr, set_cloupia_key, get_resource_path, create_ucsd_module, call_ucsd_api

# Import "winreg" on Windows Systems #
try:
    from winreg import SetValueEx, OpenKeyEx, ConnectRegistry, HKEY_CURRENT_USER, KEY_ALL_ACCESS, REG_DWORD
except ImportError:
    pass

########################
#                      #
#  Set Deploy Options  #
#                      #
########################

# Automatically Enable/Disable Windows Proxy #
SET_PROXY = False

# Select Features to be Deployed #
DEPLOY_ACCOUNTS = False
DEPLOY_WORKFLOWS = False
DEPLOY_MDS = False
DEPLOY_UCS = False
DEPLOY_ACI = False
DEPLOY_SERVERS = False
DEPLOY_VCENTER = False
DEPLOY_STORAGE = False

#####################
#                   #
#  Parse Arguments  #
#                   #
#####################

# Initiate Arg Parser #
PARSER = argparse.ArgumentParser()

# Add Description #
PARSER = argparse.ArgumentParser(description='This will deploy your new datacenter.')

PARSER.add_argument("-proxy", dest="proxy", action="store_true", help="configure windows proxy", default=False)
PARSER.add_argument("-accounts", dest="accounts", action="store_true", help="add accounts into UCSD", default=False)
PARSER.add_argument("-workflows", dest="workflows", action="store_true", help="import workflows into UCSD", default=False)
PARSER.add_argument("-mds", dest="mds", action="store_true", help="deploy MDS", default=False)
PARSER.add_argument("-ucs", dest="ucs", action="store_true", help="deploy UCS", default=False)
PARSER.add_argument("-aci", dest="aci", action="store_true", help="deploy ACI", default=False)
PARSER.add_argument("-servers", dest="servers", action="store_true", help="deploy servers", default=False)
PARSER.add_argument("-vcenter", dest="vcenter", action="store_true", help="deploy vcenter", default=False)
PARSER.add_argument("-storage", dest="storage", action="store_true", help="deploy storage", default=False)
PARSER.add_argument("-all", dest="all", action="store_true", help="deploy everything", default=False)

# Read Arguments from the Command Line #
ARGS = PARSER.parse_args()

# Check Arguments and Set Deployment Values #
if ARGS.proxy:
    SET_PROXY = True
if ARGS.accounts:
    DEPLOY_ACCOUNTS = True
if ARGS.workflows:
    DEPLOY_WORKFLOWS = True
if ARGS.mds:
    DEPLOY_MDS = True
if ARGS.ucs:
    DEPLOY_UCS = True
if ARGS.aci:
    DEPLOY_ACI = True
if ARGS.servers:
    DEPLOY_SERVERS = True
if ARGS.vcenter:
    DEPLOY_VCENTER = True
if ARGS.storage:
    DEPLOY_STORAGE = True
if ARGS.all:
    DEPLOY_ACCOUNTS = True
    DEPLOY_WORKFLOWS = True
    DEPLOY_MDS = True
    DEPLOY_UCS = True
    DEPLOY_ACI = True
    DEPLOY_SERVERS = True
    DEPLOY_VCENTER = True
    DEPLOY_STORAGE = True

# Print Selected Deployment Options #
print("DEPLOY:")
print("Set Proxy:\t" + str(SET_PROXY))
print("Accounts:\t" + str(DEPLOY_ACCOUNTS))
print("Workflows:\t" + str(DEPLOY_WORKFLOWS))
print("MDS:\t\t" + str(DEPLOY_MDS))
print("UCS:\t\t" + str(DEPLOY_UCS))
print("ACI:\t\t" + str(DEPLOY_ACI))
print("Servers:\t" + str(DEPLOY_SERVERS))
print("VCenter:\t" + str(DEPLOY_VCENTER))
print("Storage:\t" + str(DEPLOY_STORAGE))
print()

# Verify Deployment Options #
while True:
    proceed = input("Whould you like to proceed (y/n)? ")
    if proceed.strip() in ['n','N']:
        sys.exit()
    elif proceed.strip() in ['y','Y']:
        break

#################
#               #
#  Set Globals  #
#               #
#################

OS = get_os()

if OS == "Windows":
    print("Windows Operating System detected!")
elif OS == "Linux":
    print("Linux Operating System detected!")
elif OS == "Darwin":
    print("Mac Operating System detected!")
else:
    print("Operating System not detected!")

UCSD_ADDR = "10.0.0.80"
set_ucsd_addr(UCSD_ADDR)

CLOUPIA_KEY = "56593F1D37DD4BECB284C4CEFF74CFFA"
set_cloupia_key(CLOUPIA_KEY)

ACCOUNTS_FILE = open(get_resource_path("resources") + "accounts.json", "r")
ACCOUNTS_JSON = json.loads(ACCOUNTS_FILE.read())

ACCOUNTS = JsonObj(ACCOUNTS_JSON)

########################
#                      #
#  Modify Permissions  #
#                      #
########################

# Set Permissions on Files in Linux Operating Systems #
if OS == "Linux" or OS == "Darwin":
    print("Modifying file permissions...")
    os.chmod("./bin/vcsa-cli-installer/lin64/vcsa-deploy", 0o777)
    os.chmod("./bin/vcsa-cli-installer/lin64/vcsa-deploy.bin", 0o777)

########################
#                      #
#  Set Temp Variables  #
#                      #
########################

UCSD_POD = "Default Pod"
UCS_ORG = "org-root"

# Collect Start Time #
START_TIME = datetime.datetime.now()

######################
#                    #
#  Helper Functions  #
#                    #
######################

# Monitor Server Deploy Threads #
def server_thread_deploy(sr_call, thread_id, return_values):
    """
    DOCSTRING
    """

    max_time = time.time() + 3600
    srResult = call_ucsd_api(sr_call)

    while(srResult.json()['serviceResult'] < 2 and time.time() < max_time):
        time.sleep(60)
        srResult = call_ucsd_api(sr_call)

    if time.time() > max_time:
        return_values[thread_id] = -1

    return_values[thread_id] = int(srResult.json()['serviceResult'])

# Display Progress Spinner #
spin_delay = 1

def spin_char():
    print("|", end="\b", flush=True)
    time.sleep(spin_delay)
    print("/", end="\b", flush=True)
    time.sleep(spin_delay)
    print("-", end="\b", flush=True)
    time.sleep(spin_delay)
    print("\\", end="\b", flush=True)
    time.sleep(spin_delay)

###################
#                 #
#  Disable Proxy  #
#                 #
###################

# Windows Operating Systems Only #
if OS == "Windows":
    A_REG = ConnectRegistry(None, HKEY_CURRENT_USER)
    A_KEY = OpenKeyEx(A_REG, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                    0, KEY_ALL_ACCESS)

    if SET_PROXY:
        print("Disabling Proxy...")
        SetValueEx(A_KEY, "ProxyEnable", 0, REG_DWORD, 0)

###############################
#                             #
#  Configure Device Accounts  #
#                             #
###############################

if DEPLOY_ACCOUNTS:
    print()
    print("###############################")
    print("#                             #")
    print("#  Configure Device Accounts  #")
    print("#                             #")
    print("###############################")
    print()

# Add BMA Account #
bmaAccount = create_ucsd_module("addBmaAccount")

bmaAccount.modulePayload.param0.bmaName = ACCOUNTS.BMA.name
bmaAccount.modulePayload.param0.bmaDescription = ACCOUNTS.BMA.descr
bmaAccount.modulePayload.param0.serverIP = ACCOUNTS.BMA.ipAddress
bmaAccount.modulePayload.param0.pxeServerIP = ACCOUNTS.BMA.pxeAddress
bmaAccount.modulePayload.param0.inventoryNodeIP = get_ucsd_addr()

if DEPLOY_ACCOUNTS:
    print("Adding Bare Metal Agents...")
    call_ucsd_api(bmaAccount)

# Add UCS Account #
ucsAccount = create_ucsd_module("userAPICreateUCSAccount")

ucsAccount.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsAccount.modulePayload.param0.description = ACCOUNTS.UCS.descr
ucsAccount.modulePayload.param0.server = ACCOUNTS.UCS.ipAdddress
ucsAccount.modulePayload.param0.userId = ACCOUNTS.UCS.userName
ucsAccount.modulePayload.param0.passwd = ACCOUNTS.UCS.password

if DEPLOY_ACCOUNTS:
    print("Adding UCS Accounts...")
    call_ucsd_api(ucsAccount)

# Add ACI Account #
aciAccount = create_ucsd_module("userAPICreateInfraAccount")

aciAccount.modulePayload.param0.accountName = ACCOUNTS.ACI.name
aciAccount.modulePayload.param0.description = ACCOUNTS.ACI.descr
aciAccount.modulePayload.param0.accountCategory = "4"
aciAccount.modulePayload.param0.accountType = "APIC"
aciAccount.modulePayload.param0.destinationIPAddress = ACCOUNTS.ACI.ipAddress
aciAccount.modulePayload.param0.login = ACCOUNTS.ACI.userName
aciAccount.modulePayload.param0.password = ACCOUNTS.ACI.password
aciAccount.modulePayload.param0.protocol = "https"
aciAccount.modulePayload.param0.port = "443"

if DEPLOY_ACCOUNTS:
    print("Adding ACI Accounts...")
    call_ucsd_api(aciAccount)

# Add MDS A/B ACCOUNTS #
mdsAccountA = create_ucsd_module("addPhysicalNetworkDeviceConfig")
mdsAccountB = create_ucsd_module("addPhysicalNetworkDeviceConfig")

mdsAccountA.modulePayload.param0.podName = UCSD_POD
mdsAccountA.modulePayload.param0.serverAddress = ACCOUNTS.MDSA.ipAddress
mdsAccountA.modulePayload.param0.username = ACCOUNTS.MDSA.userName
mdsAccountA.modulePayload.param0.password = ACCOUNTS.MDSA.password

mdsAccountB.modulePayload.param0.podName = UCSD_POD
mdsAccountB.modulePayload.param0.serverAddress = ACCOUNTS.MDSB.ipAddress
mdsAccountB.modulePayload.param0.username = ACCOUNTS.MDSB.userName
mdsAccountB.modulePayload.param0.password = ACCOUNTS.MDSB.password

if DEPLOY_ACCOUNTS:
    print("Adding MDS Accounts...")
    call_ucsd_api(mdsAccountA)
    call_ucsd_api(mdsAccountB)

# Add Pure Account #
pureAccount = create_ucsd_module("userAPICreateInfraAccount")

pureAccount.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureAccount.modulePayload.param0.description = ACCOUNTS.PURE.descr
pureAccount.modulePayload.param0.accountCategory = "2"
pureAccount.modulePayload.param0.accountType = "FlashArray"
pureAccount.modulePayload.param0.destinationIPAddress = ACCOUNTS.PURE.ipAddress
pureAccount.modulePayload.param0.login = ACCOUNTS.PURE.userName
pureAccount.modulePayload.param0.password = ACCOUNTS.PURE.password
pureAccount.modulePayload.param0.protocol = "https"
pureAccount.modulePayload.param0.port = "0"

if DEPLOY_ACCOUNTS:
    print("Adding Pure Storage Accounts...")
    call_ucsd_api(pureAccount)

# Pause for Initial Device Inventory #
if DEPLOY_ACCOUNTS:
    print("Waiting 30 Seconds for Device Inventory...")
    time.sleep(30)

###########################
#                         #
#  Upload UCSD Workflows  #
#                         #
###########################

if DEPLOY_WORKFLOWS:
    print()
    print("#############################")
    print("#                           #")
    print("#  Uploading UCSD Workflows #")
    print("#                           #")
    print("#############################")
    print()

ucsdWorkflow = create_ucsd_module("userAPIUnifiedImport")

ucsdWorkflow.uploadFile = "..\\workflows\\BM_Deploy.wfdx"

ucsdWorkflow.modulePayload.param0.uploadPolicy = "BM_Deploy.wfdx"
ucsdWorkflow.modulePayload.param0.description = "CLUS Bare Metal Deployment"

ucsdWorkflow.modulePayload.param1.workflowImportPolicy = "replace"
ucsdWorkflow.modulePayload.param1.customTaskImportPolicy = "replace"
ucsdWorkflow.modulePayload.param1.ScriptModuleImportPolicy = "replace"
ucsdWorkflow.modulePayload.param1.activityImportPolicy = "replace"

ucsdWorkflow.modulePayload.param2 = "CLUS"

if DEPLOY_WORKFLOWS:
    print("Uploading Workflows...")
    call_ucsd_api(ucsdWorkflow)

###########################
#                         #
#  Configure MDS Devices  #
#                         #
###########################

if DEPLOY_MDS:
    print()
    print("###########################")
    print("#                         #")
    print("#  Configure MDS Devices  #")
    print("#                         #")
    print("###########################")
    print()

# MDS Enable Features #
mdsFeaturesA1 = create_ucsd_module("configureFeature")
mdsFeaturesA2 = create_ucsd_module("configureFeature")
mdsFeaturesB1 = create_ucsd_module("configureFeature")
mdsFeaturesB2 = create_ucsd_module("configureFeature")

mdsFeaturesA1.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                               ACCOUNTS.MDSA.ipAddress)
mdsFeaturesA1.modulePayload.param0.featureName = (UCSD_POD + "@" +
                                                 ACCOUNTS.MDSA.ipAddress +
                                                 "@npiv@1")
mdsFeaturesA1.modulePayload.param0.enable = "true"
mdsFeaturesA1.modulePayload.param0.copyRunToStartConfig = "false"

mdsFeaturesA2.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                               ACCOUNTS.MDSA.ipAddress)
mdsFeaturesA2.modulePayload.param0.featureName = (UCSD_POD + "@" +
                                                 ACCOUNTS.MDSA.ipAddress +
                                                 "@fport-channel-trunk@1")
mdsFeaturesA2.modulePayload.param0.enable = "true"
mdsFeaturesA2.modulePayload.param0.copyRunToStartConfig = "false"

mdsFeaturesB1.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                               ACCOUNTS.MDSB.ipAddress)
mdsFeaturesB1.modulePayload.param0.featureName = (UCSD_POD + "@" +
                                                 ACCOUNTS.MDSB.ipAddress +
                                                 "@npiv@1")
mdsFeaturesB1.modulePayload.param0.enable = "true"
mdsFeaturesB1.modulePayload.param0.copyRunToStartConfig = "false"

mdsFeaturesB2.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                               ACCOUNTS.MDSB.ipAddress)
mdsFeaturesB2.modulePayload.param0.featureName = (UCSD_POD + "@" +
                                                 ACCOUNTS.MDSB.ipAddress +
                                                 "@fport-channel-trunk@1")
mdsFeaturesB2.modulePayload.param0.enable = "true"
mdsFeaturesB2.modulePayload.param0.copyRunToStartConfig = "false"

if DEPLOY_MDS:
    print("Enabling MDS Features...")
    call_ucsd_api(mdsFeaturesA1)
    call_ucsd_api(mdsFeaturesA2)
    call_ucsd_api(mdsFeaturesB1)
    call_ucsd_api(mdsFeaturesB2)

# MDS Create VSANs #
mdsVSANA = create_ucsd_module("createVSANConfig")
mdsVSANB = create_ucsd_module("createVSANConfig")

mdsVSANA.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                           ACCOUNTS.MDSA.ipAddress)
mdsVSANA.modulePayload.param0.vsanId = "20"
mdsVSANA.modulePayload.param0.vsanName = "VSAN20"
mdsVSANA.modulePayload.param0.enhance = "true"
mdsVSANA.modulePayload.param0.copyRunToStartConfig = "false"

mdsVSANB.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                           ACCOUNTS.MDSB.ipAddress)
mdsVSANB.modulePayload.param0.vsanId = "30"
mdsVSANB.modulePayload.param0.vsanName = "VSAN30"
mdsVSANB.modulePayload.param0.enhance = "true"
mdsVSANB.modulePayload.param0.copyRunToStartConfig = "false"

if DEPLOY_MDS:
    print("Creating VSANs...")
    call_ucsd_api(mdsVSANA)
    call_ucsd_api(mdsVSANB)

# MDS Attach VSAN to Ports #
mdsVSANPortA1 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortA2 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortA3 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortA4 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortB1 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortB2 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortB3 = create_ucsd_module("fcPortVSANConfig")
mdsVSANPortB4 = create_ucsd_module("fcPortVSANConfig")

mdsVSANPortA1.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSA.ipAddress)
mdsVSANPortA1.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSA.ipAddress +
                                             "@fc1/1")
mdsVSANPortA1.modulePayload.param0.vsanId = "20"
mdsVSANPortA1.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortA1.modulePayload.param0.enable = "true"

mdsVSANPortA2.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSA.ipAddress)
mdsVSANPortA2.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSA.ipAddress +
                                             "@fc1/2")
mdsVSANPortA2.modulePayload.param0.vsanId = "20"
mdsVSANPortA2.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortA2.modulePayload.param0.enable = "true"

mdsVSANPortA3.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSA.ipAddress)
mdsVSANPortA3.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSA.ipAddress +
                                             "@fc1/13")
mdsVSANPortA3.modulePayload.param0.vsanId = "20"
mdsVSANPortA3.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortA3.modulePayload.param0.enable = "true"

mdsVSANPortA4.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSA.ipAddress)
mdsVSANPortA4.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSA.ipAddress +
                                             "@fc1/14")
mdsVSANPortA4.modulePayload.param0.vsanId = "20"
mdsVSANPortA4.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortA4.modulePayload.param0.enable = "true"

mdsVSANPortB1.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSB.ipAddress)
mdsVSANPortB1.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSB.ipAddress +
                                             "@fc1/1")
mdsVSANPortB1.modulePayload.param0.vsanId = "30"
mdsVSANPortB1.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortB1.modulePayload.param0.enable = "true"

mdsVSANPortB2.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSB.ipAddress)
mdsVSANPortB2.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSB.ipAddress +
                                             "@fc1/2")
mdsVSANPortB2.modulePayload.param0.vsanId = "30"
mdsVSANPortB2.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortB2.modulePayload.param0.enable = "true"

mdsVSANPortB3.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSB.ipAddress)
mdsVSANPortB3.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSB.ipAddress +
                                             "@fc1/13")
mdsVSANPortB3.modulePayload.param0.vsanId = "30"
mdsVSANPortB3.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortB3.modulePayload.param0.enable = "true"

mdsVSANPortB4.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                ACCOUNTS.MDSB.ipAddress)
mdsVSANPortB4.modulePayload.param0.fcPort = (UCSD_POD + "@" +
                                             ACCOUNTS.MDSB.ipAddress +
                                             "@fc1/14")
mdsVSANPortB4.modulePayload.param0.vsanId = "30"
mdsVSANPortB4.modulePayload.param0.copyRunToStartConfig = "false"
mdsVSANPortB4.modulePayload.param0.enable = "true"

if DEPLOY_MDS:
    print("Attatching VSANs to Ports...")
    call_ucsd_api(mdsVSANPortA1)
    call_ucsd_api(mdsVSANPortA2)
    call_ucsd_api(mdsVSANPortA3)
    call_ucsd_api(mdsVSANPortA4)
    call_ucsd_api(mdsVSANPortB1)
    call_ucsd_api(mdsVSANPortB2)
    call_ucsd_api(mdsVSANPortB3)
    call_ucsd_api(mdsVSANPortB4)

# MDS Create Port Channels #
mdsPortChannelA = create_ucsd_module("networkDeviceCLICommandConfig")
mdsPortChannelB = create_ucsd_module("networkDeviceCLICommandConfig")

mdsPortChannelA.modulePayload.param0.netDevice = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress)
mdsPortChannelA.modulePayload.param0.cliCommands = "end\nconfigure terminal\ninterface port-channel 20\nchannel mode active\nswitchport rate-mode dedicated"
mdsPortChannelA.modulePayload.param0.UndoCliCommands = "end\nconfigure terminal\nno interface port-channel 20"
mdsPortChannelA.modulePayload.param0.error = "end\nconfigure terminal\nno interface port-channel 20"

mdsPortChannelB.modulePayload.param0.netDevice = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress)
mdsPortChannelB.modulePayload.param0.cliCommands = "end\nconfigure terminal\ninterface port-channel 30\nchannel mode active\nswitchport rate-mode dedicated"
mdsPortChannelB.modulePayload.param0.UndoCliCommands = "end\nconfigure terminal\nno interface port-channel 30"
mdsPortChannelB.modulePayload.param0.error = "end\nconfigure terminal\nno interface port-channel 30"

if DEPLOY_MDS:
    print("Creating MDS Port Channels...")
    call_ucsd_api(mdsPortChannelA)
    call_ucsd_api(mdsPortChannelB)

# MDS Add Port-Channels to VSANs #
mdsPortChannelVsanA = create_ucsd_module("associateVfcToVsan")
mdsPortChannelVsanB = create_ucsd_module("associateVfcToVsan")

mdsPortChannelVsanA.modulePayload.param0.netdevice = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress)
mdsPortChannelVsanA.modulePayload.param0.vfcId = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress + "@Fibre@port-channel20")
mdsPortChannelVsanA.modulePayload.param0.vsanId = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress + "@20")

mdsPortChannelVsanB.modulePayload.param0.netdevice = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress)
mdsPortChannelVsanB.modulePayload.param0.vfcId = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress + "@Fibre@port-channel30")
mdsPortChannelVsanB.modulePayload.param0.vsanId = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress + "@30")

if DEPLOY_MDS:
    print("Associating Port Channels to Vsans...")
    call_ucsd_api(mdsPortChannelVsanA)
    call_ucsd_api(mdsPortChannelVsanB)

# MDS Collect Inventory #
mdsCollectInventory = create_ucsd_module("collectInventoryConfig")

mdsCollectInventory.modulePayload.param0.networkDevices = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress)
mdsCollectInventory.modulePayload.param0.networkDevices += ","
mdsCollectInventory.modulePayload.param0.networkDevices += (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress)

if DEPLOY_MDS:
    print("Collecting MDS Inventory...")
    call_ucsd_api(mdsCollectInventory)

# Pause for MDS Inventory Collection #
if DEPLOY_MDS:
    print("Waiting 30 Seconds for MDS Inventory Collection...")
    time.sleep(30)

# MDS Add Ports to Port-Channels #
mdsPortToChannelA1 = create_ucsd_module("interfacePortChannelConfig")
mdsPortToChannelA2 = create_ucsd_module("interfacePortChannelConfig")
mdsPortToChannelB1 = create_ucsd_module("interfacePortChannelConfig")
mdsPortToChannelB2 = create_ucsd_module("interfacePortChannelConfig")

mdsPortToChannelA1.modulePayload.param0.netdevice = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress)
mdsPortToChannelA1.modulePayload.param0.port = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress + "@Fibre Channel@fc1/13")
mdsPortToChannelA1.modulePayload.param0.portChannel = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress + "@Fibre@port-channel20")

mdsPortToChannelA2.modulePayload.param0.netdevice = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress)
mdsPortToChannelA2.modulePayload.param0.port = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress + "@Fibre Channel@fc1/14")
mdsPortToChannelA2.modulePayload.param0.portChannel = (UCSD_POD + "@" + ACCOUNTS.MDSA.ipAddress + "@Fibre@port-channel20")

mdsPortToChannelB1.modulePayload.param0.netdevice = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress)
mdsPortToChannelB1.modulePayload.param0.port = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress + "@Fibre Channel@fc1/13")
mdsPortToChannelB1.modulePayload.param0.portChannel = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress + "@Fibre@port-channel30")

mdsPortToChannelB2.modulePayload.param0.netdevice = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress)
mdsPortToChannelB2.modulePayload.param0.port = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress + "@Fibre Channel@fc1/14")
mdsPortToChannelB2.modulePayload.param0.portChannel = (UCSD_POD + "@" + ACCOUNTS.MDSB.ipAddress + "@Fibre@port-channel30")

if DEPLOY_MDS:
    print("Associating Ports to Port Channels...")
    call_ucsd_api(mdsPortToChannelA1)
    call_ucsd_api(mdsPortToChannelA2)
    call_ucsd_api(mdsPortToChannelB1)
    call_ucsd_api(mdsPortToChannelB2)

# MDS Enable Ports #
mdsPortConfigA1 = create_ucsd_module("configurePort")
mdsPortConfigA2 = create_ucsd_module("configurePort")
mdsPortConfigA3 = create_ucsd_module("configurePort")
mdsPortConfigA4 = create_ucsd_module("configurePort")
mdsPortConfigB1 = create_ucsd_module("configurePort")
mdsPortConfigB2 = create_ucsd_module("configurePort")
mdsPortConfigB3 = create_ucsd_module("configurePort")
mdsPortConfigB4 = create_ucsd_module("configurePort")

mdsPortConfigA1.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSA.ipAddress)
mdsPortConfigA1.modulePayload.param0.port = "fc1/1"
mdsPortConfigA1.modulePayload.param0.description = "Connection to SAN"
mdsPortConfigA1.modulePayload.param0.enable = "true"
mdsPortConfigA1.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigA2.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSA.ipAddress)
mdsPortConfigA2.modulePayload.param0.port = "fc1/2"
mdsPortConfigA2.modulePayload.param0.description = "Connection to SAN"
mdsPortConfigA2.modulePayload.param0.enable = "true"
mdsPortConfigA2.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigA3.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSA.ipAddress)
mdsPortConfigA3.modulePayload.param0.port = "fc1/13"
mdsPortConfigA3.modulePayload.param0.description = "Connection to UCS"
mdsPortConfigA3.modulePayload.param0.enable = "true"
mdsPortConfigA3.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigA4.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSA.ipAddress)
mdsPortConfigA4.modulePayload.param0.port = "fc1/14"
mdsPortConfigA4.modulePayload.param0.description = "Connection to UCS"
mdsPortConfigA4.modulePayload.param0.enable = "true"
mdsPortConfigA4.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigB1.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSB.ipAddress)
mdsPortConfigB1.modulePayload.param0.port = "fc1/1"
mdsPortConfigB1.modulePayload.param0.description = "Connection to SAN"
mdsPortConfigB1.modulePayload.param0.enable = "true"
mdsPortConfigB1.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigB2.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSB.ipAddress)
mdsPortConfigB2.modulePayload.param0.port = "fc1/2"
mdsPortConfigB2.modulePayload.param0.description = "Connection to SAN"
mdsPortConfigB2.modulePayload.param0.enable = "true"
mdsPortConfigB2.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigB3.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSB.ipAddress)
mdsPortConfigB3.modulePayload.param0.port = "fc1/13"
mdsPortConfigB3.modulePayload.param0.description = "Connection to UCS"
mdsPortConfigB3.modulePayload.param0.enable = "true"
mdsPortConfigB3.modulePayload.param0.copyRunToStartConfig = "false"

mdsPortConfigB4.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                                  ACCOUNTS.MDSB.ipAddress)
mdsPortConfigB4.modulePayload.param0.port = "fc1/14"
mdsPortConfigB4.modulePayload.param0.description = "Connection to UCS"
mdsPortConfigB4.modulePayload.param0.enable = "true"
mdsPortConfigB4.modulePayload.param0.copyRunToStartConfig = "false"

if DEPLOY_MDS:
    print("Enabling Ports...")
    call_ucsd_api(mdsPortConfigA1)
    call_ucsd_api(mdsPortConfigA2)
    call_ucsd_api(mdsPortConfigA3)
    call_ucsd_api(mdsPortConfigA4)
    call_ucsd_api(mdsPortConfigB1)
    call_ucsd_api(mdsPortConfigB2)
    call_ucsd_api(mdsPortConfigB3)
    call_ucsd_api(mdsPortConfigB4)

# MDS Create ZoneSets #
mdsZoneSetA = create_ucsd_module("createSanZoneSet")
mdsZoneSetB = create_ucsd_module("createSanZoneSet")

mdsZoneSetA.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                              ACCOUNTS.MDSA.ipAddress)
mdsZoneSetA.modulePayload.param0.name = "CLUS-ZONESET-A"
mdsZoneSetA.modulePayload.param0.vsan = (UCSD_POD + "@" +
                                         ACCOUNTS.MDSA.ipAddress + "@" +
                                         mdsVSANPortA1.modulePayload.param0.vsanId)
mdsZoneSetA.modulePayload.param0.enhanced = "true"
mdsZoneSetA.modulePayload.param0.copyToStartup = "false"

mdsZoneSetB.modulePayload.param0.netdevice = (UCSD_POD + "@" +
                                              ACCOUNTS.MDSB.ipAddress)
mdsZoneSetB.modulePayload.param0.name = "CLUS-ZONESET-B"
mdsZoneSetB.modulePayload.param0.vsan = (UCSD_POD + "@" +
                                         ACCOUNTS.MDSB.ipAddress + "@" +
                                         mdsVSANPortB1.modulePayload.param0.vsanId)
mdsZoneSetB.modulePayload.param0.enhanced = "true"
mdsZoneSetB.modulePayload.param0.copyToStartup = "false"

if DEPLOY_MDS:
    print("Creating ZoneSets...")
    call_ucsd_api(mdsZoneSetA)
    call_ucsd_api(mdsZoneSetB)

########################################################################################
#                                                                                      #
#  Below is not needed due to this process being handled by the server build workflow  #
#                                                                                      #
########################################################################################

# MDS Create SAN Zone #
# mdsSANZoneA = create_ucsd_module("createSanZone")
# mdsSANZoneB = create_ucsd_module("createSanZone")

# if DEPLOY_MDS:
    # print("Creating SAN Zones...")
    # call_ucsd_api(mdsSANZoneA)
    # call_ucsd_api(mdsSANZoneB)

# MDS Add Zone Members #
# mdsZoneMemberA = create_ucsd_module("addMemberToSANZoneConfig")
# mdsZoneMemberB = create_ucsd_module("addMemberToSANZoneConfig")

# if DEPLOY_MDS:
    # print("Adding Zone Members...")
    # call_ucsd_api(mdsZoneMemberA)
    # call_ucsd_api(mdsZoneMemberB)

# MDS Add Zone to ZoneSets #
# mdsZoneToZoneSetA = create_ucsd_module("addSANZoneToSetConfig")
# mdsZoneToZoneSetB = create_ucsd_module("addSANZoneToSetConfig")

#if DEPLOY_MDS:
    #print("Adding Zones to ZoneSets...")
    #call_ucsd_api(mdsZoneToZoneSetA)
    #call_ucsd_api(mdsZoneToZoneSetB)

# MDS ActivateZoneSets #
# mdsActivateZoneSetA = create_ucsd_module("activateSANZoneSetConfig")
# mdsActivateZoneSetB = create_ucsd_module("activateSANZoneSetConfig")

# if DEPLOY_MDS:
    # print("Activating ZoneSets...")
    # call_ucsd_api(mdsActivateZoneSetA)
    # call_ucsd_api(mdsActivateZoneSetB)

###########################
#                         #
#  Configure UCS Devices  #
#                         #
###########################

#########################################################################
#  UCS FC Ports:                                                        #
#  Enable Unified on designated ports manually prior to running script  #
#########################################################################

if DEPLOY_UCS:
    print()
    print("###########################")
    print("#                         #")
    print("#  Configure UCS Devices  #")
    print("#                         #")
    print("###########################")
    print()

# UCS Configure Uplinks #
ucsUplinkA01 = create_ucsd_module("ucsConfigureUplinkPort")
ucsUplinkA02 = create_ucsd_module("ucsConfigureUplinkPort")
ucsUplinkB01 = create_ucsd_module("ucsConfigureUplinkPort")
ucsUplinkB02 = create_ucsd_module("ucsConfigureUplinkPort")

ucsUplinkA01.modulePayload.param0.ethernetPort = (ACCOUNTS.UCS.name +
                                                  ";sys/switch-A/slot-1/switch-ether/port-1")
ucsUplinkA02.modulePayload.param0.ethernetPort = (ACCOUNTS.UCS.name +
                                                  ";sys/switch-A/slot-1/switch-ether/port-2")
ucsUplinkB01.modulePayload.param0.ethernetPort = (ACCOUNTS.UCS.name +
                                                  ";sys/switch-B/slot-1/switch-ether/port-1")
ucsUplinkB02.modulePayload.param0.ethernetPort = (ACCOUNTS.UCS.name +
                                                  ";sys/switch-B/slot-1/switch-ether/port-2")

if DEPLOY_UCS:
    print("Configuring Uplink Ports...")
    call_ucsd_api(ucsUplinkA01)
    call_ucsd_api(ucsUplinkA02)
    call_ucsd_api(ucsUplinkB01)
    call_ucsd_api(ucsUplinkB02)

# UCS Create LAN Port Channels #

# Port Channel Objects #
lanPortA = {'slotId': '1', 'portId': '1'}
lanPortB = {'slotId': '1', 'portId': '2'}

lanPortArray = [lanPortA, lanPortB]

# Port Channel Variables #
ucsLanPortchannelA = create_ucsd_module("ucsLanPortChannel")
ucsLanPortchannelB = create_ucsd_module("ucsLanPortChannel")

ucsLanPortchannelA.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsLanPortchannelA.modulePayload.param0.switchId = "A"
ucsLanPortchannelA.modulePayload.param0.name = "PC01"
ucsLanPortchannelA.modulePayload.param0.portId = "001"
ucsLanPortchannelA.modulePayload.param0.portList = lanPortArray

ucsLanPortchannelB.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsLanPortchannelB.modulePayload.param0.switchId = "B"
ucsLanPortchannelB.modulePayload.param0.name = "PC02"
ucsLanPortchannelB.modulePayload.param0.portId = "002"
ucsLanPortchannelB.modulePayload.param0.portList = lanPortArray

# Port Channel Execute #
if DEPLOY_UCS:
    print("Creating LAN Port Channels...")
    call_ucsd_api(ucsLanPortchannelA)
    call_ucsd_api(ucsLanPortchannelB)

# Pause for Port Channel Discovery #
if DEPLOY_UCS:
    print("Waiting 1 Minute for LAN Port Channel Turn-Up...")
    time.sleep(60)

# UCS Create SAN Port Channels #

# Port Channel Objects #
sanPortA = {'slotId': '1', 'portId': '31'}
sanPortB = {'slotId': '1', 'portId': '32'}

sanPortArray = [sanPortA, sanPortB]

# Port Channel Variables #
ucsSanPortchannelA = create_ucsd_module("ucsSanPortChannel")
ucsSanPortchannelB = create_ucsd_module("ucsSanPortChannel")

ucsSanPortchannelA.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsSanPortchannelA.modulePayload.param0.switchId = "A"
ucsSanPortchannelA.modulePayload.param0.name = "FC20"
ucsSanPortchannelA.modulePayload.param0.portId = "020"
ucsSanPortchannelA.modulePayload.param0.portList = sanPortArray

ucsSanPortchannelB.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsSanPortchannelB.modulePayload.param0.switchId = "B"
ucsSanPortchannelB.modulePayload.param0.name = "FC30"
ucsSanPortchannelB.modulePayload.param0.portId = "030"
ucsSanPortchannelB.modulePayload.param0.portList = sanPortArray

# Port Channel Execute #
if DEPLOY_UCS:
    print("Creating SAN Port Channels...")
    call_ucsd_api(ucsSanPortchannelA)
    call_ucsd_api(ucsSanPortchannelB)

# Pause for SAN Port Channel Discovery #
if DEPLOY_UCS:
    print("Waiting 1 Minute for SAN Port Channel Turn-Up...")
    time.sleep(60)

# UCS Create VLANs #
ucsVLAN02 = create_ucsd_module("ucsCreateVlan")
ucsVLAN10 = create_ucsd_module("ucsCreateVlan")

ucsVLAN02.modulePayload.param0.name = "VLAN2"
ucsVLAN02.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsVLAN02.modulePayload.param0.physicalInfra = "true"
ucsVLAN02.modulePayload.param0.vlanType = "dual"
ucsVLAN02.modulePayload.param0.dualVLAN = "2"

ucsVLAN10.modulePayload.param0.name = "VLAN10"
ucsVLAN10.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsVLAN10.modulePayload.param0.physicalInfra = "true"
ucsVLAN10.modulePayload.param0.vlanType = "dual"
ucsVLAN10.modulePayload.param0.dualVLAN = "10"

if DEPLOY_UCS:
    print("Creating VLANs...")
    call_ucsd_api(ucsVLAN02)
    call_ucsd_api(ucsVLAN10)

# UCS Create VSANs #
ucsVSAN20 = create_ucsd_module("ucsVsan")
ucsVSAN30 = create_ucsd_module("ucsVsan")

ucsVSAN20.modulePayload.param0.name = "VSAN20"
ucsVSAN20.modulePayload.param0.id = "20"
ucsVSAN20.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsVSAN20.modulePayload.param0.vsanType = "SAN Cloud"
ucsVSAN20.modulePayload.param0.switchId = "dual"
ucsVSAN20.modulePayload.param0.fcoeVlan = "20"

ucsVSAN30.modulePayload.param0.name = "VSAN30"
ucsVSAN30.modulePayload.param0.id = "30"
ucsVSAN30.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsVSAN30.modulePayload.param0.vsanType = "SAN Cloud"
ucsVSAN30.modulePayload.param0.switchId = "dual"
ucsVSAN30.modulePayload.param0.fcoeVlan = "30"

if DEPLOY_UCS:
    print("Creating VSANs...")
    call_ucsd_api(ucsVSAN20)
    call_ucsd_api(ucsVSAN30)

# UCS Update SAN Port Channels (Add VSAN) #

# Port Channel Update Variables #
updateSanPortchannelA = create_ucsd_module("updateSanPortChannel")
updateSanPortchannelB = create_ucsd_module("updateSanPortChannel")

updateSanPortchannelA.modulePayload.param0.accountName = ACCOUNTS.UCS.name
updateSanPortchannelA.modulePayload.param0.switchId = "A"
updateSanPortchannelA.modulePayload.param0.name = "FC20"
updateSanPortchannelA.modulePayload.param0.portId = "020"
updateSanPortchannelA.modulePayload.param0.vsan = "VSAN20"
updateSanPortchannelA.apiCall = "/cloupia/api-v2/datacenter/'" + UCSD_POD + "'/account/" + ACCOUNTS.UCS.name + "/ucsSanPortChannel/'fabric/san/A/pc-20'"

updateSanPortchannelB.modulePayload.param0.accountName = ACCOUNTS.UCS.name
updateSanPortchannelB.modulePayload.param0.switchId = "B"
updateSanPortchannelB.modulePayload.param0.name = "FC30"
updateSanPortchannelB.modulePayload.param0.portId = "030"
updateSanPortchannelB.modulePayload.param0.vsan = "VSAN30"
updateSanPortchannelB.apiCall = "/cloupia/api-v2/datacenter/'" + UCSD_POD + "'/account/" + ACCOUNTS.UCS.name + "/ucsSanPortChannel/'fabric/san/B/pc-30'"

# Port Channel Update Execute #
if DEPLOY_UCS:
    print("Updating SAN Port Channels...")
    call_ucsd_api(updateSanPortchannelA)
    call_ucsd_api(updateSanPortchannelB)

# UCS Create UUID Pool #
ucsUUIDPool = create_ucsd_module("ucsUuidPool")

ucsUUIDPool.modulePayload.param0.name = "CLUS-UUID-POOL"
ucsUUIDPool.modulePayload.param0.descr = "Cisco Live UUID Pool"
ucsUUIDPool.modulePayload.param0.prefix = "other"
ucsUUIDPool.modulePayload.param0.otherPrefix = "00000000-0000-0000"
ucsUUIDPool.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsUUIDPool.modulePayload.param0.org = UCS_ORG
ucsUUIDPool.modulePayload.param0.firstMACAddress = "0000-000000000001"
ucsUUIDPool.modulePayload.param0.size = "32"

if DEPLOY_UCS:
    print("Creating UUID Pool...")
    call_ucsd_api(ucsUUIDPool)

# UCS Create IPMI Pool #
ucsIPMIPool = create_ucsd_module("createUcsIPPool")

ucsIPMIPool.modulePayload.param0.ippoolName = "CLUS-EXT-MGMT"
ucsIPMIPool.modulePayload.param0.descr = "Cisco Live Management IP Pool"
ucsIPMIPool.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsIPMIPool.modulePayload.param0.assignmentOrder = "sequential"
ucsIPMIPool.modulePayload.param0.addIPv6Block = "false"
ucsIPMIPool.modulePayload.param0.addIPv4Block = "true"
ucsIPMIPool.modulePayload.param0.ipv4BlockFromAddress = "10.0.0.110"
ucsIPMIPool.modulePayload.param0.ipv4BlockSize = "32"
ucsIPMIPool.modulePayload.param0.ipv4BlockSubnetMask = "255.255.255.0"
ucsIPMIPool.modulePayload.param0.ipv4BlockDefaultGateway = "10.0.0.1"
ucsIPMIPool.modulePayload.param0.ipv4BlockPrimaryDns = "171.68.226.120"
ucsIPMIPool.modulePayload.param0.ipv4BlockSecondaryDns = "171.70.168.183"

if DEPLOY_UCS:
    print("Creating IP Pool...")
    call_ucsd_api(ucsIPMIPool)

# UCS Create MAC Pools #
ucsMACPoolA = create_ucsd_module("ucsMacPool")
ucsMACPoolB = create_ucsd_module("ucsMacPool")

ucsMACPoolA.modulePayload.param0.name = "CLUS-MAC-POOL-A"
ucsMACPoolA.modulePayload.param0.desc = "Cisco Live MAC Pool Side A"
ucsMACPoolA.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsMACPoolA.modulePayload.param0.org = UCS_ORG
ucsMACPoolA.modulePayload.param0.firstMACAddress = "00:25:B5:00:0A:00"
ucsMACPoolA.modulePayload.param0.size = "32"

ucsMACPoolB.modulePayload.param0.name = "CLUS-MAC-POOL-B"
ucsMACPoolB.modulePayload.param0.desc = "Cisco Live MAC Pool Side B"
ucsMACPoolB.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsMACPoolB.modulePayload.param0.org = UCS_ORG
ucsMACPoolB.modulePayload.param0.firstMACAddress = "00:25:B5:00:0B:00"
ucsMACPoolB.modulePayload.param0.size = "32"

if DEPLOY_UCS:
    print("Creating MAC Pool...")
    call_ucsd_api(ucsMACPoolA)
    call_ucsd_api(ucsMACPoolB)

# UCS Create vNIC Templates #
ucsVNICTemplateA = create_ucsd_module("ucsAddvNICTemplate")
ucsVNICTemplateB = create_ucsd_module("ucsAddvNICTemplate")

ucsVNICTemplateA.modulePayload.param0.name = "CLUS-VNIC-TEMP-A"
ucsVNICTemplateA.modulePayload.param0.descr = "Cisco Live vNIC Template Side A"
ucsVNICTemplateA.modulePayload.param0.org = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsVNICTemplateA.modulePayload.param0.switchId = "A"
ucsVNICTemplateA.modulePayload.param0.enableFailover = "false"
ucsVNICTemplateA.modulePayload.param0.targetAdapter = "true"
ucsVNICTemplateA.modulePayload.param0.targetVM = "false"
ucsVNICTemplateA.modulePayload.param0.templType = "updating-template"
#ucsVNICTemplateA.modulePayload.param0.vlanIdentityList = (ACCOUNTS.UCS.name +
#                                                          ";fabric/lan/net-" +
#                                                          ucsVLAN10.modulePayload.param0.name)
ucsVNICTemplateA.modulePayload.param0.vlanIdentityList = (ACCOUNTS.UCS.name +
                                                          ";fabric/lan/net-default")
ucsVNICTemplateA.modulePayload.param0.nativeVlan = "default"
ucsVNICTemplateA.modulePayload.param0.mtu = "1500"
ucsVNICTemplateA.modulePayload.param0.identPoolName = (ACCOUNTS.UCS.name +
                                                       ";org-root;org-root/mac-pool-" +
                                                       ucsMACPoolA.modulePayload.param0.name +
                                                       ";" + ucsMACPoolA.modulePayload.param0.name)

ucsVNICTemplateB.modulePayload.param0.name = "CLUS-VNIC-TEMP-B"
ucsVNICTemplateB.modulePayload.param0.descr = "Cisco Live vNIC Template Side B"
ucsVNICTemplateB.modulePayload.param0.org = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsVNICTemplateB.modulePayload.param0.switchId = "B"
ucsVNICTemplateB.modulePayload.param0.enableFailover = "false"
ucsVNICTemplateB.modulePayload.param0.targetAdapter = "true"
ucsVNICTemplateB.modulePayload.param0.targetVM = "false"
ucsVNICTemplateB.modulePayload.param0.templType = "updating-template"
#ucsVNICTemplateB.modulePayload.param0.vlanIdentityList = (ACCOUNTS.UCS.name +
#                                                          ";fabric/lan/net-" +
#                                                          ucsVLAN10.modulePayload.param0.name)
ucsVNICTemplateB.modulePayload.param0.vlanIdentityList = (ACCOUNTS.UCS.name +
                                                          ";fabric/lan/net-default")
ucsVNICTemplateB.modulePayload.param0.nativeVlan = "default"
ucsVNICTemplateB.modulePayload.param0.mtu = "1500"
ucsVNICTemplateB.modulePayload.param0.identPoolName = (ACCOUNTS.UCS.name +
                                                       ";org-root;org-root/mac-pool-" +
                                                       ucsMACPoolB.modulePayload.param0.name +
                                                       ";" + ucsMACPoolB.modulePayload.param0.name)

if DEPLOY_UCS:
    print("Creating vNIC Templates...")
    call_ucsd_api(ucsVNICTemplateA)
    call_ucsd_api(ucsVNICTemplateB)

# UCS Create LAN Connectivity Policy #

# LAN Connectivity Policy Objects #
lanTemplateA = {}
lanTemplateA['adapterProfileName'] = 'CLUS-SIDE-A'
lanTemplateA['nwTemplName'] = 'CLUS-VNIC-TEMP-A'
lanTemplateA['name'] = 'CLUS-VNIC-A'
lanTemplateA['order'] = '1'
lanTemplateA['status'] = "created"

lanTemplateB = {}
lanTemplateB['adapterProfileName'] = 'CLUS-SIDE-B'
lanTemplateB['nwTemplName'] = 'CLUS-VNIC-TEMP-B'
lanTemplateB['name'] = 'CLUS-VNIC-B'
lanTemplateB['order'] = '2'
lanTemplateB['status'] = "created"

lanTemplateArray = [lanTemplateA, lanTemplateB]

# LAN Connectivity Policy Variables #
ucsLANConnectivityPol = create_ucsd_module("ucsLanConnectivityPolicy")

ucsLANConnectivityPol.modulePayload.param0.name = "CLUS-LAN-CON-POL"
ucsLANConnectivityPol.modulePayload.param0.descr = "Cisco Live LAN Connectivity Policy"
ucsLANConnectivityPol.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsLANConnectivityPol.modulePayload.param0.org = UCS_ORG
ucsLANConnectivityPol.modulePayload.param0.spVNIC = lanTemplateArray

# LAN Connectivity Policy Execute #
if DEPLOY_UCS:
    print("Creating LAN Connectivity Policy...")
    call_ucsd_api(ucsLANConnectivityPol)

# UCS Create WWNN Pool #
ucsWWNNPool = create_ucsd_module("ucsWwnPool")

ucsWWNNPool.modulePayload.param0.name = "CLUS-WWNN-POOL"
ucsWWNNPool.modulePayload.param0.descr = "Cisco Live WWNN Pool"
ucsWWNNPool.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsWWNNPool.modulePayload.param0.org = UCS_ORG
ucsWWNNPool.modulePayload.param0.firstAddress = "20:00:00:25:B5:00:00:00"
ucsWWNNPool.modulePayload.param0.size = "32"
ucsWWNNPool.modulePayload.param0.purpose = "node-wwn-assignment"

if DEPLOY_UCS:
    print("Creating WWNN Pool...")
    call_ucsd_api(ucsWWNNPool)

# UCS Create WWPN Pools #
ucsWWPNPoolA = create_ucsd_module("ucsWwnPool")
ucsWWPNPoolB = create_ucsd_module("ucsWwnPool")

ucsWWPNPoolA.modulePayload.param0.name = "CLUS-WWPN-POOL-A"
ucsWWPNPoolA.modulePayload.param0.descr = "Cisco Live WWPN Pool Side A"
ucsWWPNPoolA.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsWWPNPoolA.modulePayload.param0.org = UCS_ORG
ucsWWPNPoolA.modulePayload.param0.firstAddress = "20:00:00:25:B5:00:0A:00"
ucsWWPNPoolA.modulePayload.param0.size = "32"
ucsWWPNPoolA.modulePayload.param0.purpose = "port-wwn-assignment"

ucsWWPNPoolB.modulePayload.param0.name = "CLUS-WWPN-POOL-B"
ucsWWPNPoolB.modulePayload.param0.descr = "Cisco Live WWPN Pool Side B"
ucsWWPNPoolB.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsWWPNPoolB.modulePayload.param0.org = UCS_ORG
ucsWWPNPoolB.modulePayload.param0.firstAddress = "20:00:00:25:B5:00:0B:00"
ucsWWPNPoolB.modulePayload.param0.size = "32"
ucsWWPNPoolB.modulePayload.param0.purpose = "port-wwn-assignment"

if DEPLOY_UCS:
    print("Creating WWPN Pool...")
    call_ucsd_api(ucsWWPNPoolA)
    call_ucsd_api(ucsWWPNPoolB)

# UCS Create vHBA Templates #
ucsVHBATemplateA = create_ucsd_module("ucsVhbaTemplate")
ucsVHBATemplateB = create_ucsd_module("ucsVhbaTemplate")

ucsVHBATemplateA.modulePayload.param0.name = "CLUS-VHBA-TMPL-A"
ucsVHBATemplateA.modulePayload.param0.descr = "Cisco Live vHBA Template Side A"
ucsVHBATemplateA.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsVHBATemplateA.modulePayload.param0.org = UCS_ORG
ucsVHBATemplateA.modulePayload.param0.switchId = "A"
ucsVHBATemplateA.modulePayload.param0.vSAN = "VSAN20"
ucsVHBATemplateA.modulePayload.param0.templType = "updating-template"
ucsVHBATemplateA.modulePayload.param0.maxDataFieldSize = "2048"
ucsVHBATemplateA.modulePayload.param0.wwnPool = "CLUS-WWPN-POOL-A"

ucsVHBATemplateB.modulePayload.param0.name = "CLUS-VHBA-TMPL-B"
ucsVHBATemplateB.modulePayload.param0.descr = "Cisco Live vHBA Template Side B"
ucsVHBATemplateB.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsVHBATemplateB.modulePayload.param0.org = UCS_ORG
ucsVHBATemplateB.modulePayload.param0.switchId = "B"
ucsVHBATemplateB.modulePayload.param0.vSAN = "VSAN30"
ucsVHBATemplateB.modulePayload.param0.templType = "updating-template"
ucsVHBATemplateB.modulePayload.param0.maxDataFieldSize = "2048"
ucsVHBATemplateB.modulePayload.param0.wwnPool = "CLUS-WWPN-POOL-B"

if DEPLOY_UCS:
    print("Creating vHBA Templates...")
    call_ucsd_api(ucsVHBATemplateA)
    call_ucsd_api(ucsVHBATemplateB)

# UCS Create SAN Connectivity Policy #

# SAN Connectivity Policy Objects #
sanTemplateA = {}
sanTemplateA['nwTemplName'] = 'CLUS-VHBA-TMPL-A'
sanTemplateA['name'] = 'CLUS-VHBA-A'
sanTemplateA['order'] = '1'
sanTemplateA['spDn'] = UCS_ORG
sanTemplateA['status'] = "created"

sanTemplateB = {}
sanTemplateB['nwTemplName'] = 'CLUS-VHBA-TMPL-B'
sanTemplateB['name'] = 'CLUS-VHBA-B'
sanTemplateB['order'] = '2'
sanTemplateB['spDn'] = UCS_ORG
sanTemplateB['status'] = "created"

sanTemplateArray = [sanTemplateA, sanTemplateB]

# SAN Connectivity Policy Variables #
ucsSANConnectivityPol = create_ucsd_module("ucsSanConnectivityPolicy")

ucsSANConnectivityPol.modulePayload.param0.name = "CLUS-SAN-CON-POL"
ucsSANConnectivityPol.modulePayload.param0.descr = "Cisco Live SAN Connectivity Policy"
ucsSANConnectivityPol.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsSANConnectivityPol.modulePayload.param0.org = UCS_ORG
ucsSANConnectivityPol.modulePayload.param0.identPoolName = "CLUS-WWNN-POOL"
ucsSANConnectivityPol.modulePayload.param0.spVHBA = sanTemplateArray

# SAN Connectivity Policy Execute #
if DEPLOY_UCS:
    print("Creating SAN Connectivity Policy...")
    call_ucsd_api(ucsSANConnectivityPol)

# UCS Create Server Pool #
ucsServerPoolBlade = create_ucsd_module("ucsCreateServerPool")
ucsServerPoolRack = create_ucsd_module("ucsCreateServerPool")

ucsServerPoolBlade.modulePayload.param0.poolName = "CLUS-BLADE-POOL"
ucsServerPoolBlade.modulePayload.param0.poolDescription = "Cisco Live Blade Server Pool"
ucsServerPoolBlade.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsServerPoolBlade.modulePayload.param0.serverPoolList = ""

ucsServerPoolRack.modulePayload.param0.poolName = "CLUS-RACK-POOL"
ucsServerPoolRack.modulePayload.param0.poolDescription = "Cisco Live Rack Server Pool"
ucsServerPoolRack.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsServerPoolRack.modulePayload.param0.serverPoolList = ""

if DEPLOY_UCS:
    print("Creating Server Pools...")
    call_ucsd_api(ucsServerPoolBlade)
    call_ucsd_api(ucsServerPoolRack)

# UCS Create Server Qualification #
ucsServerPoolQualBlade = create_ucsd_module("createUcsServerQualification")
ucsServerPoolQualRack = create_ucsd_module("createUcsServerQualification")

ucsServerPoolQualBlade.modulePayload.param0.name = "CLUS-BLADE-QUAL"
ucsServerPoolQualBlade.modulePayload.param0.descr = "Cisco Live Blade Server Qualification"
ucsServerPoolQualBlade.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsServerPoolQualBlade.modulePayload.param0.chassisQualExists = "true"
ucsServerPoolQualBlade.modulePayload.param0.minChassisId = "1"
ucsServerPoolQualBlade.modulePayload.param0.maxChassisId = "20"

ucsServerPoolQualRack.modulePayload.param0.name = "CLUS-RACK-QUAL"
ucsServerPoolQualRack.modulePayload.param0.descr = "Cisco Live Rack Server Qualification"
ucsServerPoolQualRack.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsServerPoolQualRack.modulePayload.param0.rackQualExists = "true"
ucsServerPoolQualRack.modulePayload.param0.minRackId = "1"
ucsServerPoolQualRack.modulePayload.param0.maxRackId = "20"

if DEPLOY_UCS:
    print("Creating Server Pool Qualification...")
    call_ucsd_api(ucsServerPoolQualBlade)
    call_ucsd_api(ucsServerPoolQualRack)

# UCS Create Server Qualification #
ucsServerPoolPolicyBlade = create_ucsd_module("createUcsServerPoolPolicy")
ucsServerPoolPolicyRack = create_ucsd_module("createUcsServerPoolPolicy")

ucsServerPoolPolicyBlade.modulePayload.param0.name = "CLUS-BLADE-POL"
ucsServerPoolPolicyBlade.modulePayload.param0.descr = "Cisco Live Blade Qualification Policy"
ucsServerPoolPolicyBlade.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsServerPoolPolicyBlade.modulePayload.param0.qualIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG +
                                                              ";" + UCS_ORG + "/blade-qualifier-" +
                                                              ucsServerPoolQualBlade.modulePayload.param0.name)
ucsServerPoolPolicyBlade.modulePayload.param0.poolDn = (ACCOUNTS.UCS.name + ";" + UCS_ORG +
                                                        ";" + UCS_ORG + "/compute-pool-" +
                                                        ucsServerPoolBlade.modulePayload.param0.poolName)

ucsServerPoolPolicyRack.modulePayload.param0.name = "CLUS-RACK-POL"
ucsServerPoolPolicyRack.modulePayload.param0.descr = "Cisco Live Rack Qualification Policy"
ucsServerPoolPolicyRack.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsServerPoolPolicyRack.modulePayload.param0.qualIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG +
                                                             ";" + UCS_ORG + "/blade-qualifier-" +
                                                             ucsServerPoolQualRack.modulePayload.param0.name)
ucsServerPoolPolicyRack.modulePayload.param0.poolDn = (ACCOUNTS.UCS.name + ";" + UCS_ORG +
                                                       ";" + UCS_ORG + "/compute-pool-" +
                                                       ucsServerPoolRack.modulePayload.param0.poolName)

if DEPLOY_UCS:
    print("Creating Server Pool Qualification Policy...")
    call_ucsd_api(ucsServerPoolPolicyBlade)
    call_ucsd_api(ucsServerPoolPolicyRack)

# UCS Create Local Disk Policy #
ucsLocalDiskPolicyRAID1 = create_ucsd_module("createLocalDiskConfigurationPolicy")
ucsLocalDiskPolicyRAID5 = create_ucsd_module("createLocalDiskConfigurationPolicy")

ucsLocalDiskPolicyRAID1.modulePayload.param0.name = "CLUS-DISK-RAID1"
ucsLocalDiskPolicyRAID1.modulePayload.param0.descr = "Cisco Live Local Disk RAID1"
ucsLocalDiskPolicyRAID1.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsLocalDiskPolicyRAID1.modulePayload.param0.mode = "raid-mirrored"
ucsLocalDiskPolicyRAID1.modulePayload.param0.protectConfig = "false"
ucsLocalDiskPolicyRAID1.modulePayload.param0.flexFlashState = "disable"

ucsLocalDiskPolicyRAID5.modulePayload.param0.name = "CLUS-DISK-RAID5"
ucsLocalDiskPolicyRAID5.modulePayload.param0.descr = "Cisco Live Local Disk RAID5"
ucsLocalDiskPolicyRAID5.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsLocalDiskPolicyRAID5.modulePayload.param0.mode = "raid-striped-parity"
ucsLocalDiskPolicyRAID5.modulePayload.param0.protectConfig = "false"
ucsLocalDiskPolicyRAID5.modulePayload.param0.flexFlashState = "disable"

if DEPLOY_UCS:
    print("Creating Local Disk Policy...")
    call_ucsd_api(ucsLocalDiskPolicyRAID1)
    call_ucsd_api(ucsLocalDiskPolicyRAID5)

# UCS Create Boot Policy #
ucsBootPolicyHDD = create_ucsd_module("ucsCreateBootPolicy")
ucsBootPolicyLAN = create_ucsd_module("ucsCreateBootPolicy")

ucsBootPolicyHDD.modulePayload.param0.policyName = "CLUS-BOOT-HDD"
ucsBootPolicyHDD.modulePayload.param0.policyDescription = "Cisco Live Boot from HDD"
ucsBootPolicyHDD.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsBootPolicyHDD.modulePayload.param0.rebootOnOrderChange = "false"
ucsBootPolicyHDD.modulePayload.param0.enforceNames = "false"
ucsBootPolicyHDD.modulePayload.param0.bootMode = "legacy"
ucsBootPolicyHDD.modulePayload.param0.bootSecurity = "false"
ucsBootPolicyHDD.modulePayload.param0.addLocalDisk = "true"

ucsBootPolicyLAN.modulePayload.param0.policyName = "CLUS-BOOT-LAN"
ucsBootPolicyLAN.modulePayload.param0.policyDescription = "Cisco Live Boot from LAN"
ucsBootPolicyLAN.modulePayload.param0.orgIdentity = (ACCOUNTS.UCS.name + ";" + UCS_ORG)
ucsBootPolicyLAN.modulePayload.param0.rebootOnOrderChange = "false"
ucsBootPolicyLAN.modulePayload.param0.enforceNames = "false"
ucsBootPolicyLAN.modulePayload.param0.bootMode = "legacy"
ucsBootPolicyLAN.modulePayload.param0.bootSecurity = "false"
ucsBootPolicyLAN.modulePayload.param0.addPriLanBoot = "true"
ucsBootPolicyLAN.modulePayload.param0.privNIC = "eth0"
ucsBootPolicyLAN.modulePayload.param0.addSecLanBoot = "true"
ucsBootPolicyLAN.modulePayload.param0.secvNIC = "eth1"

if DEPLOY_UCS:
    print("Creating Boot Policy...")
    call_ucsd_api(ucsBootPolicyHDD)
    call_ucsd_api(ucsBootPolicyLAN)
    #call_ucsd_api(ucsBootPolicySAN)

# UCS Create Storage Policy #
ucsStoragePolicyRAID1 = create_ucsd_module("ucsStoragePolicy")
ucsStoragePolicyRAID5 = create_ucsd_module("ucsStoragePolicy")

ucsStoragePolicyRAID1.modulePayload.param0.policyName = "CLUS-STOR-POL-R1"
ucsStoragePolicyRAID1.modulePayload.param0.policyDescription = "Cisco Live Storage Policy RAID1"
ucsStoragePolicyRAID1.modulePayload.param0.ucsAcctName = ACCOUNTS.UCS.name
ucsStoragePolicyRAID1.modulePayload.param0.orgName = UCS_ORG
ucsStoragePolicyRAID1.modulePayload.param0.localDiskConfigPolicy = ucsLocalDiskPolicyRAID1.modulePayload.param0.name
ucsStoragePolicyRAID1.modulePayload.param0.connectivityType = "Use SAN Connectivity Policy"
ucsStoragePolicyRAID1.modulePayload.param0.noOfVhba = "0"
ucsStoragePolicyRAID1.modulePayload.param0.sanConnPolicy = ucsSANConnectivityPol.modulePayload.param0.name

ucsStoragePolicyRAID5.modulePayload.param0.policyName = "CLUS-STOR-POL-R5"
ucsStoragePolicyRAID5.modulePayload.param0.policyDescription = "Cisco Live Storage Policy RAID5"
ucsStoragePolicyRAID5.modulePayload.param0.ucsAcctName = ACCOUNTS.UCS.name
ucsStoragePolicyRAID5.modulePayload.param0.orgName = UCS_ORG
ucsStoragePolicyRAID5.modulePayload.param0.localDiskConfigPolicy = ucsLocalDiskPolicyRAID5.modulePayload.param0.name
ucsStoragePolicyRAID5.modulePayload.param0.connectivityType = "Use SAN Connectivity Policy"
ucsStoragePolicyRAID5.modulePayload.param0.noOfVhba = "0"
ucsStoragePolicyRAID5.modulePayload.param0.sanConnPolicy = ucsSANConnectivityPol.modulePayload.param0.name

if DEPLOY_UCS:
    print("Creating Storage Policy...")
    call_ucsd_api(ucsStoragePolicyRAID1)
    call_ucsd_api(ucsStoragePolicyRAID5)

# UCS Create Network Policy #
ucsNetworkPolicy = create_ucsd_module("ucsNetworkPolicy")

ucsNetworkPolicy.modulePayload.param0.policyName = "CLUS-NET-POL"
ucsNetworkPolicy.modulePayload.param0.policyDescription = "Cisco Live Network Policy"
ucsNetworkPolicy.modulePayload.param0.accountName = ACCOUNTS.UCS.name
ucsNetworkPolicy.modulePayload.param0.orgDn = UCS_ORG
ucsNetworkPolicy.modulePayload.param0.connectivityType = "Use LAN Connectivity Policy"
ucsNetworkPolicy.modulePayload.param0.lanConnPolicy = ucsLANConnectivityPol.modulePayload.param0.name
ucsNetworkPolicy.modulePayload.param0.expertNoOfVnics = "0"

if DEPLOY_UCS:
    print("Creating Network Policy...")
    call_ucsd_api(ucsNetworkPolicy)

# UCS Create Service Profile Template #
ucsSPTemplateBlade = create_ucsd_module("userAPICreateServiceProfileTemplate")
ucsSPTemplateRack = create_ucsd_module("userAPICreateServiceProfileTemplate")

ucsSPTemplateBlade.modulePayload.param0 = ACCOUNTS.UCS.name
ucsSPTemplateBlade.modulePayload.param3.spTemplateName = "ESX_Template_Blade"
ucsSPTemplateBlade.modulePayload.param3.storagePolicyName = ucsStoragePolicyRAID1.modulePayload.param0.policyName
ucsSPTemplateBlade.modulePayload.param3.networkPolicyName = ucsNetworkPolicy.modulePayload.param0.policyName
ucsSPTemplateBlade.modulePayload.param3.OrgName = UCS_ORG
ucsSPTemplateBlade.modulePayload.param3.spTemplateType = "Updating-Template"
ucsSPTemplateBlade.modulePayload.param3.serverPowerState = "down"
ucsSPTemplateBlade.modulePayload.param3.uuidPool.name = ucsUUIDPool.modulePayload.param0.name
ucsSPTemplateBlade.modulePayload.param3.bootPolicy.name = ucsBootPolicyHDD.modulePayload.param0.policyName

ucsSPTemplateRack.modulePayload.param0 = ACCOUNTS.UCS.name
ucsSPTemplateRack.modulePayload.param3.spTemplateName = "ESX_Template_Rack"
ucsSPTemplateRack.modulePayload.param3.storagePolicyName = ucsStoragePolicyRAID5.modulePayload.param0.policyName
ucsSPTemplateRack.modulePayload.param3.networkPolicyName = ucsNetworkPolicy.modulePayload.param0.policyName
ucsSPTemplateRack.modulePayload.param3.OrgName = UCS_ORG
ucsSPTemplateRack.modulePayload.param3.spTemplateType = "Updating-Template"
ucsSPTemplateRack.modulePayload.param3.serverPowerState = "down"
ucsSPTemplateRack.modulePayload.param3.uuidPool.name = ucsUUIDPool.modulePayload.param0.name
ucsSPTemplateRack.modulePayload.param3.bootPolicy.name = ucsBootPolicyHDD.modulePayload.param0.policyName

if DEPLOY_UCS:
    print("Creating Blade Service Profile Templates...")
    call_ucsd_api(ucsSPTemplateBlade)
    print("Creating Rack Service Profile Templates...")
    call_ucsd_api(ucsSPTemplateRack)

###########################
#                         #
#  Configure ACI Devices  #
#                         #
###########################

if DEPLOY_ACI:
    print()
    print("###########################")
    print("#                         #")
    print("#  Configure ACI Devices  #")
    print("#                         #")
    print("###########################")
    print()

# ACI Create VLAN Pool #
aciVLANPool = create_ucsd_module("createVlanPoolConfig")

aciVLANPool.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciVLANPool.modulePayload.param0.vlanPoolName = "CLUS-VLAN-POOL"
aciVLANPool.modulePayload.param0.description = "Cisco Live Physical VLAN Pool"
aciVLANPool.modulePayload.param0.range = "1-10"

if DEPLOY_ACI:
    print("Creating VLAN Pool...")
    call_ucsd_api(aciVLANPool)

# ACI Create AEP #
aciAEP = create_ucsd_module("createAttachableEntityProfileConfig")

aciAEP.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciAEP.modulePayload.param0.name = "CLUS-AEP"
aciAEP.modulePayload.param0.description = "Cisco Live Attachable Entity Profile"

if DEPLOY_ACI:
    print("Creating AEP...")
    call_ucsd_api(aciAEP)

# ACI Create Physical Domain #
aciPhysDom = create_ucsd_module("createPhysicalDomainConfig")

aciPhysDom.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciPhysDom.modulePayload.param0.name = "CLUS-PHYS-DOM"
aciPhysDom.modulePayload.param0.entityProfile = (ACCOUNTS.ACI.name + "@" +
                                                 aciAEP.modulePayload.param0.name)
aciPhysDom.modulePayload.param0.vlanPool = (ACCOUNTS.ACI.name + "@" +
                                            aciVLANPool.modulePayload.param0.vlanPoolName +
                                            "@static")

if DEPLOY_ACI:
    print("Creating Physical Domain...")
    call_ucsd_api(aciPhysDom)

# ACI Create Link Level Policy #
aciLinkLevelPol1G = create_ucsd_module("createLinkLevelPolicyConfig")
aciLinkLevelPol10G = create_ucsd_module("createLinkLevelPolicyConfig")

aciLinkLevelPol1G.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciLinkLevelPol1G.modulePayload.param0.linkLevelName = "LINKLEVEL-POL-1G"
aciLinkLevelPol1G.modulePayload.param0.description = "Link Level Policy 1G"
aciLinkLevelPol1G.modulePayload.param0.speed = "1G"

aciLinkLevelPol10G.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciLinkLevelPol10G.modulePayload.param0.linkLevelName = "LINKLEVEL-POL-10G"
aciLinkLevelPol10G.modulePayload.param0.description = "Link Level Policy 10G"
aciLinkLevelPol10G.modulePayload.param0.speed = "10G"

if DEPLOY_ACI:
    print("Creating Link Level Policies...")
    call_ucsd_api(aciLinkLevelPol1G)
    call_ucsd_api(aciLinkLevelPol10G)

# ACI Create CDP Policy #
aciCDPPolicyON = create_ucsd_module("createCDPInterfacePolicyConfig")
aciCDPPolicyOFF = create_ucsd_module("createCDPInterfacePolicyConfig")

aciCDPPolicyON.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciCDPPolicyON.modulePayload.param0.cdpInterfaceName = "CDP-POL-ON"
aciCDPPolicyON.modulePayload.param0.description = "CDP Policy ON"
aciCDPPolicyON.modulePayload.param0.adminState = "enabled"

aciCDPPolicyOFF.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciCDPPolicyOFF.modulePayload.param0.cdpInterfaceName = "CDP-POL-OFF"
aciCDPPolicyOFF.modulePayload.param0.description = "CDP Policy OFF"
aciCDPPolicyOFF.modulePayload.param0.adminState = "disabled"

if DEPLOY_ACI:
    print("Creating CDP Policies...")
    call_ucsd_api(aciCDPPolicyON)
    call_ucsd_api(aciCDPPolicyOFF)

# ACI Create LLDP Policy #
aciLLDPPolicyON = create_ucsd_module("createLLDPInterfacePolicyConfig")
aciLLDPPolicyOFF = create_ucsd_module("createLLDPInterfacePolicyConfig")

aciLLDPPolicyON.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName = "LLDP-POL-ON"
aciLLDPPolicyON.modulePayload.param0.description = "LLDP Policy ON"
aciLLDPPolicyON.modulePayload.param0.receiveState = "enabled"
aciLLDPPolicyON.modulePayload.param0.transmitState = "enabled"

aciLLDPPolicyOFF.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciLLDPPolicyOFF.modulePayload.param0.lldpInterfaceName = "LLDP-POL-OFF"
aciLLDPPolicyOFF.modulePayload.param0.description = "LLDP Policy OFF"
aciLLDPPolicyOFF.modulePayload.param0.receiveState = "disabled"
aciLLDPPolicyOFF.modulePayload.param0.transmitState = "disabled"

if DEPLOY_ACI:
    print("Creating LLDP Policies...")
    call_ucsd_api(aciLLDPPolicyON)
    call_ucsd_api(aciLLDPPolicyOFF)

# ACI Create Port Channel Policy #
aciPCPolicyLACP = create_ucsd_module("createPortChannelPolicyConfig")

aciPCPolicyLACP.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciPCPolicyLACP.modulePayload.param0.interfaceName = "PORTCHANNEL-POL-LACP"
aciPCPolicyLACP.modulePayload.param0.description = "Port Channel Policy LACP Active"
aciPCPolicyLACP.modulePayload.param0.mode = "LACP Active"

if DEPLOY_ACI:
    print("Creating LACP Policies...")
    call_ucsd_api(aciPCPolicyLACP)

# ACI Create Interface Policy Group #
aciIntPolGroupInt07 = create_ucsd_module("createVPCInterfacePolicyGroupConfig")
aciIntPolGroupInt23 = create_ucsd_module("createVPCInterfacePolicyGroupConfig")
aciIntPolGroupInt24 = create_ucsd_module("createVPCInterfacePolicyGroupConfig")
aciIntPolGroupInt47 = create_ucsd_module("createVPCInterfacePolicyGroupConfig")
aciIntPolGroupInt48 = create_ucsd_module("createVPCInterfacePolicyGroupConfig")

aciIntPolGroupInt07.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntPolGroupInt07.modulePayload.param0.name = "VPC-INT-POL-GRP-07"
aciIntPolGroupInt07.modulePayload.param0.description = "VPC Interface Policy Group e1/7"
aciIntPolGroupInt07.modulePayload.param0.linkLevelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                            aciLinkLevelPol10G.modulePayload.param0.linkLevelName)
aciIntPolGroupInt07.modulePayload.param0.cdpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                      aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
aciIntPolGroupInt07.modulePayload.param0.lldpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                       aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
aciIntPolGroupInt07.modulePayload.param0.attachedEntryProfile = (ACCOUNTS.ACI.name + "@" +
                                                                 aciAEP.modulePayload.param0.name)
aciIntPolGroupInt07.modulePayload.param0.portChannelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                              aciPCPolicyLACP.modulePayload.param0.interfaceName)

aciIntPolGroupInt23.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntPolGroupInt23.modulePayload.param0.name = "VPC-INT-POL-GRP-23"
aciIntPolGroupInt23.modulePayload.param0.description = "VPC Interface Policy Group e1/23"
aciIntPolGroupInt23.modulePayload.param0.linkLevelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                            aciLinkLevelPol10G.modulePayload.param0.linkLevelName)
aciIntPolGroupInt23.modulePayload.param0.cdpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                      aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
aciIntPolGroupInt23.modulePayload.param0.lldpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                       aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
aciIntPolGroupInt23.modulePayload.param0.attachedEntryProfile = (ACCOUNTS.ACI.name + "@" +
                                                                 aciAEP.modulePayload.param0.name)
aciIntPolGroupInt23.modulePayload.param0.portChannelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                              aciPCPolicyLACP.modulePayload.param0.interfaceName)

aciIntPolGroupInt24.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntPolGroupInt24.modulePayload.param0.name = "VPC-INT-POL-GRP-24"
aciIntPolGroupInt24.modulePayload.param0.description = "VPC Interface Policy Group e1/24"
aciIntPolGroupInt24.modulePayload.param0.linkLevelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                            aciLinkLevelPol10G.modulePayload.param0.linkLevelName)
aciIntPolGroupInt24.modulePayload.param0.cdpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                      aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
aciIntPolGroupInt24.modulePayload.param0.lldpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                       aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
aciIntPolGroupInt24.modulePayload.param0.attachedEntryProfile = (ACCOUNTS.ACI.name + "@" +
                                                                 aciAEP.modulePayload.param0.name)
aciIntPolGroupInt24.modulePayload.param0.portChannelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                              aciPCPolicyLACP.modulePayload.param0.interfaceName)

aciIntPolGroupInt47.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntPolGroupInt47.modulePayload.param0.name = "VPC-INT-POL-GRP-47"
aciIntPolGroupInt47.modulePayload.param0.description = "VPC Interface Policy Group e1/47"
aciIntPolGroupInt47.modulePayload.param0.linkLevelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                            aciLinkLevelPol1G.modulePayload.param0.linkLevelName)
aciIntPolGroupInt47.modulePayload.param0.cdpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                      aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
aciIntPolGroupInt47.modulePayload.param0.lldpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                       aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
aciIntPolGroupInt47.modulePayload.param0.attachedEntryProfile = (ACCOUNTS.ACI.name + "@" +
                                                                 aciAEP.modulePayload.param0.name)
aciIntPolGroupInt47.modulePayload.param0.portChannelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                              aciPCPolicyLACP.modulePayload.param0.interfaceName)

aciIntPolGroupInt48.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntPolGroupInt48.modulePayload.param0.name = "VPC-INT-POL-GRP-48"
aciIntPolGroupInt48.modulePayload.param0.description = "VPC Interface Policy Group e1/48"
aciIntPolGroupInt48.modulePayload.param0.linkLevelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                            aciLinkLevelPol1G.modulePayload.param0.linkLevelName)
aciIntPolGroupInt48.modulePayload.param0.cdpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                      aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
aciIntPolGroupInt48.modulePayload.param0.lldpPolicy = (ACCOUNTS.ACI.name + "@" +
                                                       aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
aciIntPolGroupInt48.modulePayload.param0.attachedEntryProfile = (ACCOUNTS.ACI.name + "@" +
                                                                 aciAEP.modulePayload.param0.name)
aciIntPolGroupInt48.modulePayload.param0.portChannelPolicy = (ACCOUNTS.ACI.name + "@" +
                                                              aciPCPolicyLACP.modulePayload.param0.interfaceName)

if DEPLOY_ACI:
    print("Creating Interface Policy Groups...")
    call_ucsd_api(aciIntPolGroupInt07)
    call_ucsd_api(aciIntPolGroupInt23)
    call_ucsd_api(aciIntPolGroupInt24)
    call_ucsd_api(aciIntPolGroupInt47)
    call_ucsd_api(aciIntPolGroupInt48)

# ACI Create Interface Profile #
aciIntProfileInt07 = create_ucsd_module("createInterfaceProfileConfig")
aciIntProfileInt23 = create_ucsd_module("createInterfaceProfileConfig")
aciIntProfileInt24 = create_ucsd_module("createInterfaceProfileConfig")
aciIntProfileInt47 = create_ucsd_module("createInterfaceProfileConfig")
aciIntProfileInt48 = create_ucsd_module("createInterfaceProfileConfig")

aciIntProfileInt07.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntProfileInt07.modulePayload.param0.name = "CLUS-INT-PROF-07"
aciIntProfileInt07.modulePayload.param0.description = "Cisco Live Interface Profile e1/7"

aciIntProfileInt23.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntProfileInt23.modulePayload.param0.name = "CLUS-INT-PROF-23"
aciIntProfileInt23.modulePayload.param0.description = "Cisco Live Interface Profile e1/23"

aciIntProfileInt24.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntProfileInt24.modulePayload.param0.name = "CLUS-INT-PROF-24"
aciIntProfileInt24.modulePayload.param0.description = "Cisco Live Interface Profile e1/24"

aciIntProfileInt47.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntProfileInt47.modulePayload.param0.name = "CLUS-INT-PROF-47"
aciIntProfileInt47.modulePayload.param0.description = "Cisco Live Interface Profile e1/47"

aciIntProfileInt48.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciIntProfileInt48.modulePayload.param0.name = "CLUS-INT-PROF-48"
aciIntProfileInt48.modulePayload.param0.description = "Cisco Live Interface Profile e1/48"

if DEPLOY_ACI:
    print("Creating Interface Profiles...")
    call_ucsd_api(aciIntProfileInt07)
    call_ucsd_api(aciIntProfileInt23)
    call_ucsd_api(aciIntProfileInt24)
    call_ucsd_api(aciIntProfileInt47)
    call_ucsd_api(aciIntProfileInt48)

# ACI Associate Access Ports to Interface Profile #
aciAccessPortToIntProfInt07 = create_ucsd_module("associateAccessPortSelectorToInterfaceProfileConfig")
aciAccessPortToIntProfInt23 = create_ucsd_module("associateAccessPortSelectorToInterfaceProfileConfig")
aciAccessPortToIntProfInt24 = create_ucsd_module("associateAccessPortSelectorToInterfaceProfileConfig")
aciAccessPortToIntProfInt47 = create_ucsd_module("associateAccessPortSelectorToInterfaceProfileConfig")
aciAccessPortToIntProfInt48 = create_ucsd_module("associateAccessPortSelectorToInterfaceProfileConfig")

aciAccessPortToIntProfInt07.modulePayload.param0.interfaceProfile = (ACCOUNTS.ACI.name + "@" +
                                                                     aciIntProfileInt07.modulePayload.param0.name)
aciAccessPortToIntProfInt07.modulePayload.param0.name = "INT-SEL-1-07"
aciAccessPortToIntProfInt07.modulePayload.param0.description = "Interface Selector e1/7"
aciAccessPortToIntProfInt07.modulePayload.param0.interfaceIDs = "1/7"
aciAccessPortToIntProfInt07.modulePayload.param0.interfacePolicyGrp = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntPolGroupInt07.modulePayload.param0.name +
                                                                       "@uni/infra/funcprof/accbundle-" +
                                                                       aciIntPolGroupInt07.modulePayload.param0.name)

aciAccessPortToIntProfInt23.modulePayload.param0.interfaceProfile = (ACCOUNTS.ACI.name + "@" +
                                                                     aciIntProfileInt23.modulePayload.param0.name)
aciAccessPortToIntProfInt23.modulePayload.param0.name = "INT-SEL-1-23"
aciAccessPortToIntProfInt23.modulePayload.param0.description = "Interface Selector e1/23"
aciAccessPortToIntProfInt23.modulePayload.param0.interfaceIDs = "1/23"
aciAccessPortToIntProfInt23.modulePayload.param0.interfacePolicyGrp = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntPolGroupInt23.modulePayload.param0.name +
                                                                       "@uni/infra/funcprof/accbundle-" +
                                                                       aciIntPolGroupInt23.modulePayload.param0.name)

aciAccessPortToIntProfInt24.modulePayload.param0.interfaceProfile = (ACCOUNTS.ACI.name + "@" +
                                                                     aciIntProfileInt24.modulePayload.param0.name)
aciAccessPortToIntProfInt24.modulePayload.param0.name = "INT-SEL-1-24"
aciAccessPortToIntProfInt24.modulePayload.param0.description = "Interface Selector e1/24"
aciAccessPortToIntProfInt24.modulePayload.param0.interfaceIDs = "1/24"
aciAccessPortToIntProfInt24.modulePayload.param0.interfacePolicyGrp = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntPolGroupInt24.modulePayload.param0.name +
                                                                       "@uni/infra/funcprof/accbundle-" +
                                                                       aciIntPolGroupInt24.modulePayload.param0.name)

aciAccessPortToIntProfInt47.modulePayload.param0.interfaceProfile = (ACCOUNTS.ACI.name + "@" +
                                                                     aciIntProfileInt47.modulePayload.param0.name)
aciAccessPortToIntProfInt47.modulePayload.param0.name = "INT-SEL-1-47"
aciAccessPortToIntProfInt47.modulePayload.param0.description = "Interface Selector e1/47"
aciAccessPortToIntProfInt47.modulePayload.param0.interfaceIDs = "1/47"
aciAccessPortToIntProfInt47.modulePayload.param0.interfacePolicyGrp = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntPolGroupInt47.modulePayload.param0.name +
                                                                       "@uni/infra/funcprof/accbundle-" +
                                                                       aciIntPolGroupInt47.modulePayload.param0.name)

aciAccessPortToIntProfInt48.modulePayload.param0.interfaceProfile = (ACCOUNTS.ACI.name + "@" +
                                                                     aciIntProfileInt48.modulePayload.param0.name)
aciAccessPortToIntProfInt48.modulePayload.param0.name = "INT-SEL-1-48"
aciAccessPortToIntProfInt48.modulePayload.param0.description = "Interface Selector e1/48"
aciAccessPortToIntProfInt48.modulePayload.param0.interfaceIDs = "1/48"
aciAccessPortToIntProfInt48.modulePayload.param0.interfacePolicyGrp = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntPolGroupInt48.modulePayload.param0.name +
                                                                       "@uni/infra/funcprof/accbundle-" +
                                                                       aciIntPolGroupInt48.modulePayload.param0.name)

if DEPLOY_ACI:
    print("Assinging Access Ports to Interface Profiles...")
    call_ucsd_api(aciAccessPortToIntProfInt07)
    call_ucsd_api(aciAccessPortToIntProfInt23)
    call_ucsd_api(aciAccessPortToIntProfInt24)
    call_ucsd_api(aciAccessPortToIntProfInt47)
    call_ucsd_api(aciAccessPortToIntProfInt48)

# ACI Create VPC Explicit Protection Group #
aciVPCExpProtGrp01 = create_ucsd_module("createVPCExplicitProtectionGroupsConfig")

aciVPCExpProtGrp01.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciVPCExpProtGrp01.modulePayload.param0.name = "VPC-PROT-GRP-01"
aciVPCExpProtGrp01.modulePayload.param0.id = "1"
aciVPCExpProtGrp01.modulePayload.param0.vpcDomainPolicy = (ACCOUNTS.ACI.name + "@default")

# Note: Update this to read leaves from: /cloupia/api-v2/ApicFabricLeafNodeIdentity #
# aciVPCExpProtGrp01.modulePayload.param0.switchOne
# aciVPCExpProtGrp01.modulePayload.param0.switchTwo

if DEPLOY_ACI:
    print("Creating VPC Protection Group...")
    call_ucsd_api(aciVPCExpProtGrp01)

# ACI Create Switch Profile #
aciSwitchProfileInt07 = create_ucsd_module("createSwitchProfileConfig")
aciSwitchProfileInt23 = create_ucsd_module("createSwitchProfileConfig")
aciSwitchProfileInt24 = create_ucsd_module("createSwitchProfileConfig")
aciSwitchProfileInt47 = create_ucsd_module("createSwitchProfileConfig")
aciSwitchProfileInt48 = create_ucsd_module("createSwitchProfileConfig")

aciSwitchProfileInt07.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciSwitchProfileInt07.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-07"
aciSwitchProfileInt07.modulePayload.param0.description = "Cisco Live Switch Profile e1/7"

aciSwitchProfileInt23.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciSwitchProfileInt23.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-23"
aciSwitchProfileInt23.modulePayload.param0.description = "Cisco Live Switch Profile e1/23"

aciSwitchProfileInt24.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciSwitchProfileInt24.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-24"
aciSwitchProfileInt24.modulePayload.param0.description = "Cisco Live Switch Profile e1/24"

aciSwitchProfileInt47.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciSwitchProfileInt47.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-47"
aciSwitchProfileInt47.modulePayload.param0.description = "Cisco Live Switch Profile e1/47"

aciSwitchProfileInt48.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciSwitchProfileInt48.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-48"
aciSwitchProfileInt48.modulePayload.param0.description = "Cisco Live Switch Profile e1/48"

if DEPLOY_ACI:
    print("Creating Switch Profiles...")
    call_ucsd_api(aciSwitchProfileInt07)
    call_ucsd_api(aciSwitchProfileInt23)
    call_ucsd_api(aciSwitchProfileInt24)
    call_ucsd_api(aciSwitchProfileInt47)
    call_ucsd_api(aciSwitchProfileInt48)

# ACI Associate Switches to Switch Profile #
aciSwitchesToProfileInt07 = create_ucsd_module("associateSwitchSelectorToSwitchProfileConfig")
aciSwitchesToProfileInt23 = create_ucsd_module("associateSwitchSelectorToSwitchProfileConfig")
aciSwitchesToProfileInt24 = create_ucsd_module("associateSwitchSelectorToSwitchProfileConfig")
aciSwitchesToProfileInt47 = create_ucsd_module("associateSwitchSelectorToSwitchProfileConfig")
aciSwitchesToProfileInt48 = create_ucsd_module("associateSwitchSelectorToSwitchProfileConfig")

aciSwitchesToProfileInt07.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                aciSwitchProfileInt07.modulePayload.param0.switchProfileName)
aciSwitchesToProfileInt07.modulePayload.param0.name = "101-102"

aciSwitchesToProfileInt23.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                aciSwitchProfileInt23.modulePayload.param0.switchProfileName)
aciSwitchesToProfileInt23.modulePayload.param0.name = "101-102"

aciSwitchesToProfileInt24.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                aciSwitchProfileInt24.modulePayload.param0.switchProfileName)
aciSwitchesToProfileInt24.modulePayload.param0.name = "101-102"

aciSwitchesToProfileInt47.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                aciSwitchProfileInt47.modulePayload.param0.switchProfileName)
aciSwitchesToProfileInt47.modulePayload.param0.name = "101-102"

aciSwitchesToProfileInt48.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                aciSwitchProfileInt48.modulePayload.param0.switchProfileName)
aciSwitchesToProfileInt48.modulePayload.param0.name = "101-102"

# Note: Update this to read leaves from: /cloupia/api-v2/ApicFabricLeafNodeIdentity #
# aciSwitchesToProfile.modulePayload.param0.leaf

if DEPLOY_ACI:
    print("Associating Switches to Switch Profiles...")
    call_ucsd_api(aciSwitchesToProfileInt07)
    call_ucsd_api(aciSwitchesToProfileInt23)
    call_ucsd_api(aciSwitchesToProfileInt24)
    call_ucsd_api(aciSwitchesToProfileInt47)
    call_ucsd_api(aciSwitchesToProfileInt48)

# ACI Associate Interfaces to Switch Profile #
aciIntProfToSwitchProfInt07 = create_ucsd_module("associateInterfaceSelectorProfileToSwitchProfileConfig")
aciIntProfToSwitchProfInt23 = create_ucsd_module("associateInterfaceSelectorProfileToSwitchProfileConfig")
aciIntProfToSwitchProfInt24 = create_ucsd_module("associateInterfaceSelectorProfileToSwitchProfileConfig")
aciIntProfToSwitchProfInt47 = create_ucsd_module("associateInterfaceSelectorProfileToSwitchProfileConfig")
aciIntProfToSwitchProfInt48 = create_ucsd_module("associateInterfaceSelectorProfileToSwitchProfileConfig")

aciIntProfToSwitchProfInt07.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                  aciSwitchProfileInt07.modulePayload.param0.switchProfileName)
aciIntProfToSwitchProfInt07.modulePayload.param0.interfaceSelPfName = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntProfileInt07.modulePayload.param0.name)

aciIntProfToSwitchProfInt23.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                  aciSwitchProfileInt23.modulePayload.param0.switchProfileName)
aciIntProfToSwitchProfInt23.modulePayload.param0.interfaceSelPfName = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntProfileInt23.modulePayload.param0.name)

aciIntProfToSwitchProfInt24.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                  aciSwitchProfileInt24.modulePayload.param0.switchProfileName)
aciIntProfToSwitchProfInt24.modulePayload.param0.interfaceSelPfName = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntProfileInt24.modulePayload.param0.name)

aciIntProfToSwitchProfInt47.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                  aciSwitchProfileInt47.modulePayload.param0.switchProfileName)
aciIntProfToSwitchProfInt47.modulePayload.param0.interfaceSelPfName = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntProfileInt47.modulePayload.param0.name)

aciIntProfToSwitchProfInt48.modulePayload.param0.switchProfile = (ACCOUNTS.ACI.name + "@" +
                                                                  aciSwitchProfileInt48.modulePayload.param0.switchProfileName)
aciIntProfToSwitchProfInt48.modulePayload.param0.interfaceSelPfName = (ACCOUNTS.ACI.name + "@" +
                                                                       aciIntProfileInt48.modulePayload.param0.name)

if DEPLOY_ACI:
    print("Associating Interfaces to Switch Profiles...")
    call_ucsd_api(aciIntProfToSwitchProfInt07)
    call_ucsd_api(aciIntProfToSwitchProfInt23)
    call_ucsd_api(aciIntProfToSwitchProfInt24)
    call_ucsd_api(aciIntProfToSwitchProfInt47)
    call_ucsd_api(aciIntProfToSwitchProfInt48)

# ACI Create Tenant #
aciTenant = create_ucsd_module("createTenantConfig")

aciTenant.modulePayload.param0.apicAccount = ACCOUNTS.ACI.name
aciTenant.modulePayload.param0.name = "CiscoLive"
aciTenant.modulePayload.param0.description = "Cisco Live Tenant"
aciTenant.modulePayload.param0.monitoringPolicy = (ACCOUNTS.ACI.name + "@common@default")

if DEPLOY_ACI:
    print("Creating Tenants...")
    call_ucsd_api(aciTenant)

# ACI Create VRF #
aciVRF = create_ucsd_module("createPrivateNetworkConfig")

aciVRF.modulePayload.param0.tenantName = (ACCOUNTS.ACI.name + "@" +
                                          aciTenant.modulePayload.param0.name)
aciVRF.modulePayload.param0.privateNetwork = "CLUS-VRF"
aciVRF.modulePayload.param0.polEnforce = "unenforced"
aciVRF.modulePayload.param0.privateNetworkDescription = "Cisco Live VRF"
aciVRF.modulePayload.param0.bgpTimers = (ACCOUNTS.ACI.name + "@common@default")
aciVRF.modulePayload.param0.ospfTimers = (ACCOUNTS.ACI.name + "@common@default")
aciVRF.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

if DEPLOY_ACI:
    print("Creating VRFs...")
    call_ucsd_api(aciVRF)

# ACI Create Bridge Domain #
aciBDVlan01 = create_ucsd_module("createTenantBridgeDomain")
aciBDVlan02 = create_ucsd_module("createTenantBridgeDomain")
aciBDVlan10 = create_ucsd_module("createTenantBridgeDomain")

aciBDVlan01.modulePayload.param0.tenantName = (ACCOUNTS.ACI.name + "@" +
                                               aciTenant.modulePayload.param0.name)
aciBDVlan01.modulePayload.param0.name = "CLUS-BD-VLAN01"
aciBDVlan01.modulePayload.param0.description = "Cisco Live Bridge Domain Vlan 1"
aciBDVlan01.modulePayload.param0.network = (ACCOUNTS.ACI.name + "@" +
                                            aciTenant.modulePayload.param0.name + "@" +
                                            aciVRF.modulePayload.param0.privateNetwork)
aciBDVlan01.modulePayload.param0.forwarding = "Custom"
aciBDVlan01.modulePayload.param0.l2Unicast = "Flood"
aciBDVlan01.modulePayload.param0.l2Multicast = "Flood"
aciBDVlan01.modulePayload.param0.arpFlooding = "true"
aciBDVlan01.modulePayload.param0.unicastRouting = "true"
aciBDVlan01.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

aciBDVlan02.modulePayload.param0.tenantName = (ACCOUNTS.ACI.name + "@" +
                                               aciTenant.modulePayload.param0.name)
aciBDVlan02.modulePayload.param0.name = "CLUS-BD-VLAN02"
aciBDVlan02.modulePayload.param0.description = "Cisco Live Bridge Domain Vlan 2"
aciBDVlan02.modulePayload.param0.network = (ACCOUNTS.ACI.name + "@" +
                                            aciTenant.modulePayload.param0.name + "@" +
                                            aciVRF.modulePayload.param0.privateNetwork)
aciBDVlan02.modulePayload.param0.forwarding = "Optimize"
aciBDVlan02.modulePayload.param0.l2Unicast = "Flood"
aciBDVlan02.modulePayload.param0.l2Multicast = "Flood"
aciBDVlan02.modulePayload.param0.arpFlooding = "false"
aciBDVlan02.modulePayload.param0.unicastRouting = "true"
aciBDVlan02.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

aciBDVlan10.modulePayload.param0.tenantName = (ACCOUNTS.ACI.name + "@" +
                                               aciTenant.modulePayload.param0.name)
aciBDVlan10.modulePayload.param0.name = "CLUS-BD-VLAN10"
aciBDVlan10.modulePayload.param0.description = "Cisco Live Bridge Domain Vlan 10"
aciBDVlan10.modulePayload.param0.network = (ACCOUNTS.ACI.name + "@" +
                                            aciTenant.modulePayload.param0.name + "@" +
                                            aciVRF.modulePayload.param0.privateNetwork)
aciBDVlan10.modulePayload.param0.forwarding = "Optimize"
aciBDVlan10.modulePayload.param0.l2Unicast = "Flood"
aciBDVlan10.modulePayload.param0.l2Multicast = "Flood"
aciBDVlan10.modulePayload.param0.arpFlooding = "false"
aciBDVlan10.modulePayload.param0.unicastRouting = "true"
aciBDVlan10.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

if DEPLOY_ACI:
    print("Creating Bridge Domains...")
    call_ucsd_api(aciBDVlan01)
    call_ucsd_api(aciBDVlan02)
    call_ucsd_api(aciBDVlan10)

# ACI Create Subnet #
aciSubnetVlan01 = create_ucsd_module("createSubnetToBridgeNetworkConfig")
aciSubnetVlan02 = create_ucsd_module("createSubnetToBridgeNetworkConfig")
aciSubnetVlan10 = create_ucsd_module("createSubnetToBridgeNetworkConfig")

aciSubnetVlan01.modulePayload.param0.bridgeDomain = (ACCOUNTS.ACI.name + "@" +
                                                     aciTenant.modulePayload.param0.name +
                                                     "@" + aciBDVlan01.modulePayload.param0.name)
aciSubnetVlan01.modulePayload.param0.ipAddress = "10.0.0.3"
aciSubnetVlan01.modulePayload.param0.mask = "24"
aciSubnetVlan01.modulePayload.param0.sharedSubnet = "false"
aciSubnetVlan01.modulePayload.param0.publicSubnet = "false"
aciSubnetVlan01.modulePayload.param0.privateSubnet = "true"
aciSubnetVlan01.modulePayload.param0.description = "Cisco Live 10.0.0.X Subnet"

aciSubnetVlan02.modulePayload.param0.bridgeDomain = (ACCOUNTS.ACI.name + "@" +
                                                     aciTenant.modulePayload.param0.name +
                                                     "@" + aciBDVlan02.modulePayload.param0.name)
aciSubnetVlan02.modulePayload.param0.ipAddress = "10.2.0.1"
aciSubnetVlan02.modulePayload.param0.mask = "24"
aciSubnetVlan02.modulePayload.param0.sharedSubnet = "false"
aciSubnetVlan02.modulePayload.param0.publicSubnet = "false"
aciSubnetVlan02.modulePayload.param0.privateSubnet = "true"
aciSubnetVlan02.modulePayload.param0.description = "Cisco Live 10.2.0.X Subnet"

aciSubnetVlan10.modulePayload.param0.bridgeDomain = (ACCOUNTS.ACI.name + "@" +
                                                     aciTenant.modulePayload.param0.name +
                                                     "@" + aciBDVlan10.modulePayload.param0.name)
aciSubnetVlan10.modulePayload.param0.ipAddress = "10.10.0.1"
aciSubnetVlan10.modulePayload.param0.mask = "24"
aciSubnetVlan10.modulePayload.param0.sharedSubnet = "false"
aciSubnetVlan10.modulePayload.param0.publicSubnet = "false"
aciSubnetVlan10.modulePayload.param0.privateSubnet = "true"
aciSubnetVlan10.modulePayload.param0.description = "Cisco Live 10.10.0.X Subnet"

if DEPLOY_ACI:
    print("Creating Subnets...")
    call_ucsd_api(aciSubnetVlan01)
    call_ucsd_api(aciSubnetVlan02)
    call_ucsd_api(aciSubnetVlan10)

# ACI Create Application Profile #
aciAppProfile = create_ucsd_module("createTenantApplicationProfileConfig")

aciAppProfile.modulePayload.param0.tenantName = (ACCOUNTS.ACI.name + "@" +
                                                 aciTenant.modulePayload.param0.name)
aciAppProfile.modulePayload.param0.applnProfileName = "CLUS-APP"
aciAppProfile.modulePayload.param0.description = "Cisco Live Application"
aciAppProfile.modulePayload.param0.monitorPolicy = (ACCOUNTS.ACI.name + "@common@default")

if DEPLOY_ACI:
    print("Creating Application Profiles...")
    call_ucsd_api(aciAppProfile)

# ACI Create Endpoint Group #
aciEPGVlan01 = create_ucsd_module("createEPGConfig")
aciEPGVlan02 = create_ucsd_module("createEPGConfig")
aciEPGVlan10 = create_ucsd_module("createEPGConfig")

aciEPGVlan01.modulePayload.param0.approfName = (ACCOUNTS.ACI.name + "@" +
                                                aciTenant.modulePayload.param0.name +
                                                "@" +
                                                aciAppProfile.modulePayload.param0.applnProfileName)
aciEPGVlan01.modulePayload.param0.epgName = "CLUS-VLAN-01"
aciEPGVlan01.modulePayload.param0.epgDescription = "Cisco Live EPG Vlan 1"
aciEPGVlan01.modulePayload.param0.customQos = (ACCOUNTS.ACI.name + "@common@default")
aciEPGVlan01.modulePayload.param0.bridgeDomain = (ACCOUNTS.ACI.name + "@" +
                                                  aciTenant.modulePayload.param0.name +
                                                  "@" +
                                                  aciBDVlan01.modulePayload.param0.name)
aciEPGVlan01.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

aciEPGVlan02.modulePayload.param0.approfName = (ACCOUNTS.ACI.name + "@" +
                                                aciTenant.modulePayload.param0.name +
                                                "@" +
                                                aciAppProfile.modulePayload.param0.applnProfileName)
aciEPGVlan02.modulePayload.param0.epgName = "CLUS-VLAN-02"
aciEPGVlan02.modulePayload.param0.epgDescription = "Cisco Live EPG Vlan 2"
aciEPGVlan02.modulePayload.param0.customQos = (ACCOUNTS.ACI.name + "@common@default")
aciEPGVlan02.modulePayload.param0.bridgeDomain = (ACCOUNTS.ACI.name + "@" +
                                                  aciTenant.modulePayload.param0.name +
                                                  "@" +
                                                  aciBDVlan02.modulePayload.param0.name)
aciEPGVlan02.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

aciEPGVlan10.modulePayload.param0.approfName = (ACCOUNTS.ACI.name + "@" +
                                                aciTenant.modulePayload.param0.name +
                                                "@" +
                                                aciAppProfile.modulePayload.param0.applnProfileName)
aciEPGVlan10.modulePayload.param0.epgName = "CLUS-VLAN-10"
aciEPGVlan10.modulePayload.param0.epgDescription = "Cisco Live EPG Vlan 10"
aciEPGVlan10.modulePayload.param0.customQos = (ACCOUNTS.ACI.name + "@common@default")
aciEPGVlan10.modulePayload.param0.bridgeDomain = (ACCOUNTS.ACI.name + "@" +
                                                  aciTenant.modulePayload.param0.name +
                                                  "@" +
                                                  aciBDVlan10.modulePayload.param0.name)
aciEPGVlan10.modulePayload.param0.monPolicy = (ACCOUNTS.ACI.name + "@common@default")

if DEPLOY_ACI:
    print("Creating EPGs...")
    call_ucsd_api(aciEPGVlan01)
    call_ucsd_api(aciEPGVlan02)
    call_ucsd_api(aciEPGVlan10)

# ACI Attach Physical Domain to EPG #
aciPhysDomToEPGVlan01 = create_ucsd_module("addDomainToEPGConfig")
aciPhysDomToEPGVlan02 = create_ucsd_module("addDomainToEPGConfig")
aciPhysDomToEPGVlan10 = create_ucsd_module("addDomainToEPGConfig")

aciPhysDomToEPGVlan01.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                  aciTenant.modulePayload.param0.name +
                                                  "@" +
                                                  aciAppProfile.modulePayload.param0.applnProfileName +
                                                  "@" +
                                                  aciEPGVlan01.modulePayload.param0.epgName)
aciPhysDomToEPGVlan01.modulePayload.param0.domainProfile = (ACCOUNTS.ACI.name +
                                                            "@Physical Domain@" +
                                                            aciPhysDom.modulePayload.param0.name)
aciPhysDomToEPGVlan01.modulePayload.param0.deployImmediacy = "On Demand"
aciPhysDomToEPGVlan01.modulePayload.param0.resolutionImmediacy = "On Demand"

aciPhysDomToEPGVlan02.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                  aciTenant.modulePayload.param0.name +
                                                  "@" +
                                                  aciAppProfile.modulePayload.param0.applnProfileName +
                                                  "@" +
                                                  aciEPGVlan02.modulePayload.param0.epgName)
aciPhysDomToEPGVlan02.modulePayload.param0.domainProfile = (ACCOUNTS.ACI.name +
                                                            "@Physical Domain@" +
                                                            aciPhysDom.modulePayload.param0.name)
aciPhysDomToEPGVlan02.modulePayload.param0.deployImmediacy = "On Demand"
aciPhysDomToEPGVlan02.modulePayload.param0.resolutionImmediacy = "On Demand"

aciPhysDomToEPGVlan10.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                  aciTenant.modulePayload.param0.name +
                                                  "@" +
                                                  aciAppProfile.modulePayload.param0.applnProfileName +
                                                  "@" +
                                                  aciEPGVlan10.modulePayload.param0.epgName)
aciPhysDomToEPGVlan10.modulePayload.param0.domainProfile = (ACCOUNTS.ACI.name +
                                                            "@Physical Domain@" +
                                                            aciPhysDom.modulePayload.param0.name)
aciPhysDomToEPGVlan10.modulePayload.param0.deployImmediacy = "On Demand"
aciPhysDomToEPGVlan10.modulePayload.param0.resolutionImmediacy = "On Demand"

if DEPLOY_ACI:
    print("Attaching Physical Domain to EPGs...")
    call_ucsd_api(aciPhysDomToEPGVlan01)
    call_ucsd_api(aciPhysDomToEPGVlan02)
    call_ucsd_api(aciPhysDomToEPGVlan10)

# ACI Attach Leaf Policy to EPG #
# Vlan 1 Variables #
aciLeafPolToEPGVlan01Port07 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan01Port23 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan01Port24 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan01Port47 = create_ucsd_module("addStaticPathToEPGConfig")

# Vlan 2 Variables #
aciLeafPolToEPGVlan02Port07 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan02Port23 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan02Port24 = create_ucsd_module("addStaticPathToEPGConfig")

# Vlan 10 Variables #
aciLeafPolToEPGVlan10Port07 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan10Port23 = create_ucsd_module("addStaticPathToEPGConfig")
aciLeafPolToEPGVlan10Port24 = create_ucsd_module("addStaticPathToEPGConfig")

# Vlan 1 VPC Mappings #

aciLeafPolToEPGVlan01Port07.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan01.modulePayload.param0.epgName)
aciLeafPolToEPGVlan01Port07.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan01Port07.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt07.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan01Port07.modulePayload.param0.encapsulation = "vlan-1"
aciLeafPolToEPGVlan01Port07.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan01Port07.modulePayload.param0.mode = "802.1P Tagged"

aciLeafPolToEPGVlan01Port23.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan01.modulePayload.param0.epgName)
aciLeafPolToEPGVlan01Port23.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan01Port23.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt23.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan01Port23.modulePayload.param0.encapsulation = "vlan-1"
aciLeafPolToEPGVlan01Port23.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan01Port23.modulePayload.param0.mode = "802.1P Tagged"

aciLeafPolToEPGVlan01Port24.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan01.modulePayload.param0.epgName)
aciLeafPolToEPGVlan01Port24.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan01Port24.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt24.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan01Port24.modulePayload.param0.encapsulation = "vlan-1"
aciLeafPolToEPGVlan01Port24.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan01Port24.modulePayload.param0.mode = "802.1P Tagged"

aciLeafPolToEPGVlan01Port47.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan01.modulePayload.param0.epgName)
aciLeafPolToEPGVlan01Port47.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan01Port47.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt47.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan01Port47.modulePayload.param0.encapsulation = "vlan-1"
aciLeafPolToEPGVlan01Port47.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan01Port47.modulePayload.param0.mode = "802.1P Tagged"

# Vlan 2 VPC Mappings #

aciLeafPolToEPGVlan02Port07.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan02.modulePayload.param0.epgName)
aciLeafPolToEPGVlan02Port07.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan02Port07.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt07.modulePayload.param0.name + "]")
aciLeafPolToEPGVlan02Port07.modulePayload.param0.encapsulation = "vlan-2"
aciLeafPolToEPGVlan02Port07.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan02Port07.modulePayload.param0.mode = "Tagged"

aciLeafPolToEPGVlan02Port23.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan02.modulePayload.param0.epgName)
aciLeafPolToEPGVlan02Port23.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan02Port23.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt23.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan02Port23.modulePayload.param0.encapsulation = "vlan-2"
aciLeafPolToEPGVlan02Port23.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan02Port23.modulePayload.param0.mode = "Tagged"

aciLeafPolToEPGVlan02Port24.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan02.modulePayload.param0.epgName)
aciLeafPolToEPGVlan02Port24.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan02Port24.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt24.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan02Port24.modulePayload.param0.encapsulation = "vlan-2"
aciLeafPolToEPGVlan02Port24.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan02Port24.modulePayload.param0.mode = "Tagged"

# Vlan 10 VPC Mappings #

aciLeafPolToEPGVlan10Port07.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan10.modulePayload.param0.epgName)
aciLeafPolToEPGVlan10Port07.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan10Port07.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt07.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan10Port07.modulePayload.param0.encapsulation = "vlan-10"
aciLeafPolToEPGVlan10Port07.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan10Port07.modulePayload.param0.mode = "Tagged"

aciLeafPolToEPGVlan10Port23.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan10.modulePayload.param0.epgName)
aciLeafPolToEPGVlan10Port23.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan10Port23.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt23.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan10Port23.modulePayload.param0.encapsulation = "vlan-10"
aciLeafPolToEPGVlan10Port23.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan10Port23.modulePayload.param0.mode = "Tagged"

aciLeafPolToEPGVlan10Port24.modulePayload.param0.epg = (ACCOUNTS.ACI.name + "@" +
                                                        aciTenant.modulePayload.param0.name +
                                                        "@" +
                                                        aciAppProfile.modulePayload.param0.applnProfileName +
                                                        "@" +
                                                        aciEPGVlan10.modulePayload.param0.epgName)
aciLeafPolToEPGVlan10Port24.modulePayload.param0.pathType = "Virtual Port Channel"
# Update this to dynamically pull leaves #
aciLeafPolToEPGVlan10Port24.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" +
                                                            aciIntPolGroupInt24.modulePayload.param0.name +
                                                            "]")
aciLeafPolToEPGVlan10Port24.modulePayload.param0.encapsulation = "vlan-10"
aciLeafPolToEPGVlan10Port24.modulePayload.param0.deploymentImmediacy = "Immediate"
aciLeafPolToEPGVlan10Port24.modulePayload.param0.mode = "Tagged"

if DEPLOY_ACI:
    print("Attaching Leaf Profiles to EPGs...")
    # Vlan 1 Execute#
    call_ucsd_api(aciLeafPolToEPGVlan01Port07)
    call_ucsd_api(aciLeafPolToEPGVlan01Port23)
    call_ucsd_api(aciLeafPolToEPGVlan01Port24)
    call_ucsd_api(aciLeafPolToEPGVlan01Port47)

    # Vlan 2 Execute #
    call_ucsd_api(aciLeafPolToEPGVlan02Port07)
    call_ucsd_api(aciLeafPolToEPGVlan02Port23)
    call_ucsd_api(aciLeafPolToEPGVlan02Port24)

    # Vlan 10 Execute #
    call_ucsd_api(aciLeafPolToEPGVlan10Port07)
    call_ucsd_api(aciLeafPolToEPGVlan10Port23)
    call_ucsd_api(aciLeafPolToEPGVlan10Port24)

##################################################################################
#                                                                                #
#  Below is not needed since we are deploying in "unenforced" mode for the demo  #
#                                                                                #
##################################################################################

# ACI Create Contract #
# aciContract = create_ucsd_module("createContractConfig")

# if DEPLOY_ACI:
    # call_ucsd_api(aciContract)

# ACI Create Contract Subject #
# aciContractSubj = create_ucsd_module("createContractSubjectConfig")

# if DEPLOY_ACI:
    # call_ucsd_api(aciContractSubj)

# ACI Create Subject Filter #
# aciSubjFilter = create_ucsd_module("createTenantFilterConfig")

# if DEPLOY_ACI:
    # call_ucsd_api(aciSubjFilter)

# ACI Create Filter Rule #
# aciFilterRule = create_ucsd_module("createTenantFilterRuleConfig")

# if DEPLOY_ACI:
    # call_ucsd_api(aciFilterRule)

# ACI Create Add Filter To Contract #
# aciFilterToContract = create_ucsd_module("addFilterToContractSubjectConfig")

# if DEPLOY_ACI:
    # call_ucsd_api(aciFilterToContract)

# ACI Create Add Contract To EPG #
# aciContractToEPG = create_ucsd_module("addContractToEPGConfig")

# if DEPLOY_ACI:
    # call_ucsd_api(aciContractToEPG)

# Pause for Flood & Learn #
if DEPLOY_ACI:
    print("Waiting 5 minutes for flood & learn...")
    time.sleep(300)

########################
#                      #
#  Deploy ESX Servers  #
#                      #
########################

if DEPLOY_SERVERS:
    print()
    print("########################")
    print("#                      #")
    print("#  Deploy ESX Servers  #")
    print("#                      #")
    print("########################")
    print()

# ESX Server Deployment #
bmDeployServerRack00 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade01 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade02 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade03 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade04 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade05 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade06 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade07 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")
bmDeployServerBlade08 = create_ucsd_module("userAPISubmitWorkflowServiceRequest")

bmWorkFlowName = "Bare Metal Deploy v2"

bmDeployServerRack00.modulePayload.param0 = bmWorkFlowName
bmDeployServerRack00.modulePayload.param1.list[1]['value'] = "ESX-SERVER-00"
bmDeployServerRack00.modulePayload.param1.list[3]['value'] = "ESX_Template_Rack"
bmDeployServerRack00.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-RACK-POOL"
bmDeployServerRack00.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-RACK-QUAL"
bmDeployServerRack00.modulePayload.param1.list[8]['value'] = "10.0.0.210"
bmDeployServerRack00.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerRack00.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerRack00.modulePayload.param1.list[11]['value'] = "ESX-SERVER-00"
bmDeployServerRack00.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerRack00.modulePayload.param1.list[25]['value'] = "ESX-SERVER-00-A"
bmDeployServerRack00.modulePayload.param1.list[26]['value'] = "ESX-SERVER-00-B"

bmDeployServerBlade01.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade01.modulePayload.param1.list[1]['value'] = "ESX-SERVER-01"
bmDeployServerBlade01.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade01.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade01.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade01.modulePayload.param1.list[8]['value'] = "10.0.0.211"
bmDeployServerBlade01.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade01.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade01.modulePayload.param1.list[11]['value'] = "ESX-SERVER-01"
bmDeployServerBlade01.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade01.modulePayload.param1.list[25]['value'] = "ESX-SERVER-01-A"
bmDeployServerBlade01.modulePayload.param1.list[26]['value'] = "ESX-SERVER-01-B"

bmDeployServerBlade02.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade02.modulePayload.param1.list[1]['value'] = "ESX-SERVER-02"
bmDeployServerBlade02.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade02.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade02.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade02.modulePayload.param1.list[8]['value'] = "10.0.0.212"
bmDeployServerBlade02.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade02.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade02.modulePayload.param1.list[11]['value'] = "ESX-SERVER-02"
bmDeployServerBlade02.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade02.modulePayload.param1.list[25]['value'] = "ESX-SERVER-02-A"
bmDeployServerBlade02.modulePayload.param1.list[26]['value'] = "ESX-SERVER-02-B"

bmDeployServerBlade03.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade03.modulePayload.param1.list[1]['value'] = "ESX-SERVER-03"
bmDeployServerBlade03.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade03.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade03.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade03.modulePayload.param1.list[8]['value'] = "10.0.0.213"
bmDeployServerBlade03.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade03.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade03.modulePayload.param1.list[11]['value'] = "ESX-SERVER-03"
bmDeployServerBlade03.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade03.modulePayload.param1.list[25]['value'] = "ESX-SERVER-03-A"
bmDeployServerBlade03.modulePayload.param1.list[26]['value'] = "ESX-SERVER-03-B"

bmDeployServerBlade04.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade04.modulePayload.param1.list[1]['value'] = "ESX-SERVER-04"
bmDeployServerBlade04.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade04.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade04.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade04.modulePayload.param1.list[8]['value'] = "10.0.0.214"
bmDeployServerBlade04.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade04.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade04.modulePayload.param1.list[11]['value'] = "ESX-SERVER-04"
bmDeployServerBlade04.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade04.modulePayload.param1.list[25]['value'] = "ESX-SERVER-04-A"
bmDeployServerBlade04.modulePayload.param1.list[26]['value'] = "ESX-SERVER-04-B"

bmDeployServerBlade05.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade05.modulePayload.param1.list[1]['value'] = "ESX-SERVER-05"
bmDeployServerBlade05.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade05.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade05.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade05.modulePayload.param1.list[8]['value'] = "10.0.0.215"
bmDeployServerBlade05.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade05.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade05.modulePayload.param1.list[11]['value'] = "ESX-SERVER-05"
bmDeployServerBlade05.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade05.modulePayload.param1.list[25]['value'] = "ESX-SERVER-05-A"
bmDeployServerBlade05.modulePayload.param1.list[26]['value'] = "ESX-SERVER-05-B"

bmDeployServerBlade06.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade06.modulePayload.param1.list[1]['value'] = "ESX-SERVER-06"
bmDeployServerBlade06.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade06.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade06.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade06.modulePayload.param1.list[8]['value'] = "10.0.0.216"
bmDeployServerBlade06.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade06.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade06.modulePayload.param1.list[11]['value'] = "ESX-SERVER-06"
bmDeployServerBlade06.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade06.modulePayload.param1.list[25]['value'] = "ESX-SERVER-06-A"
bmDeployServerBlade06.modulePayload.param1.list[26]['value'] = "ESX-SERVER-06-B"

bmDeployServerBlade07.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade07.modulePayload.param1.list[1]['value'] = "ESX-SERVER-07"
bmDeployServerBlade07.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade07.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade07.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade07.modulePayload.param1.list[8]['value'] = "10.0.0.217"
bmDeployServerBlade07.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade07.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade07.modulePayload.param1.list[11]['value'] = "ESX-SERVER-07"
bmDeployServerBlade07.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade07.modulePayload.param1.list[25]['value'] = "ESX-SERVER-07-A"
bmDeployServerBlade07.modulePayload.param1.list[26]['value'] = "ESX-SERVER-07-B"

bmDeployServerBlade08.modulePayload.param0 = bmWorkFlowName
bmDeployServerBlade08.modulePayload.param1.list[1]['value'] = "ESX-SERVER-08"
bmDeployServerBlade08.modulePayload.param1.list[3]['value'] = "ESX_Template_Blade"
bmDeployServerBlade08.modulePayload.param1.list[4]['value'] = "UCSM;org-root;org-root/compute-pool-CLUS-BLADE-POOL"
bmDeployServerBlade08.modulePayload.param1.list[5]['value'] = "UCSM;org-root;org-root/blade-qualifier-CLUS-BLADE-QUAL"
bmDeployServerBlade08.modulePayload.param1.list[8]['value'] = "10.0.0.218"
bmDeployServerBlade08.modulePayload.param1.list[9]['value'] = "255.255.255.0"
bmDeployServerBlade08.modulePayload.param1.list[10]['value'] = "10.0.0.1"
bmDeployServerBlade08.modulePayload.param1.list[11]['value'] = "ESX-SERVER-08"
bmDeployServerBlade08.modulePayload.param1.list[13]['value'] = "0"
bmDeployServerBlade08.modulePayload.param1.list[25]['value'] = "ESX-SERVER-08-A"
bmDeployServerBlade08.modulePayload.param1.list[26]['value'] = "ESX-SERVER-08-B"

if DEPLOY_SERVERS:
    print("Deploying Rack Servers...")
    sr00 = call_ucsd_api(bmDeployServerRack00)

    print("Deploying Blade Servers...")
    sr01 = call_ucsd_api(bmDeployServerBlade01)
    sr02 = call_ucsd_api(bmDeployServerBlade02)
    sr03 = call_ucsd_api(bmDeployServerBlade03)
    sr04 = call_ucsd_api(bmDeployServerBlade04)
    sr05 = call_ucsd_api(bmDeployServerBlade05)
    sr06 = call_ucsd_api(bmDeployServerBlade06)
    sr07 = call_ucsd_api(bmDeployServerBlade07)
    sr08 = call_ucsd_api(bmDeployServerBlade08)

# Monitor Server Deployment Status #

if DEPLOY_SERVERS:
    print("Monitoring Server Deployment...")

    srMonitor00 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor01 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor02 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor03 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor04 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor05 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor06 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor07 = create_ucsd_module("userAPIGetWorkflowStatus")
    srMonitor08 = create_ucsd_module("userAPIGetWorkflowStatus")

    srMonitor00.modulePayload.param0 = sr00.json()['serviceResult']
    srMonitor01.modulePayload.param0 = sr01.json()['serviceResult']
    srMonitor02.modulePayload.param0 = sr02.json()['serviceResult']
    srMonitor03.modulePayload.param0 = sr03.json()['serviceResult']
    srMonitor04.modulePayload.param0 = sr04.json()['serviceResult']
    srMonitor05.modulePayload.param0 = sr05.json()['serviceResult']
    srMonitor06.modulePayload.param0 = sr06.json()['serviceResult']
    srMonitor07.modulePayload.param0 = sr07.json()['serviceResult']
    srMonitor08.modulePayload.param0 = sr08.json()['serviceResult']

    deploy_results = [None] * 9

    srThread0 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor00, "thread_id":0, "return_values":deploy_results})
    srThread1 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor01, "thread_id":1, "return_values":deploy_results})
    srThread2 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor02, "thread_id":2, "return_values":deploy_results})
    srThread3 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor03, "thread_id":3, "return_values":deploy_results})
    srThread4 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor04, "thread_id":4, "return_values":deploy_results})
    srThread5 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor05, "thread_id":5, "return_values":deploy_results})
    srThread6 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor06, "thread_id":6, "return_values":deploy_results})
    srThread7 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor07, "thread_id":7, "return_values":deploy_results})
    srThread8 = threading.Thread(target=server_thread_deploy, kwargs={"sr_call":srMonitor08, "thread_id":8, "return_values":deploy_results})

    srThread0.start()
    srThread1.start()
    srThread2.start()
    srThread3.start()
    srThread4.start()
    srThread5.start()
    srThread6.start()
    srThread7.start()
    srThread8.start()

    while threading.active_count() > 1:
        active = threading.active_count() - 1
        if active > 1:
            print("Waiting on {} servers to complete...     ".format(active), end="\r")
        else:
            print("Waiting on {} server to complete...     ".format(active), end="\r")
        time.sleep(60)

    print("")
    print("Server Deployment Complete!")

# Pause for Server Boot #
if DEPLOY_VCENTER:
    print("Waiting 5 Minutess for Server Boot...")
    time.sleep(300)

#############################
#                           #
#  Configure Storage Array  #
#                           #
#############################

if DEPLOY_STORAGE:
    print()
    print("#############################")
    print("#                           #")
    print("#  Configure Storage Array  #")
    print("#                           #")
    print("#############################")
    print()

# Create Pure Host Group #
pureHostGroup = create_ucsd_module("flashArrayCreateHostGroup")

pureHostGroup.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostGroup.modulePayload.param0.hostGroupPreName = "ESX-HOSTS"

if DEPLOY_STORAGE:
    print("Creating Storage Host Group...")
    pTest = call_ucsd_api(pureHostGroup)

# Add ESX Hosts to Pure Host Group #
pureHostToGroup01 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup02 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup03 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup04 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup05 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup06 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup07 = create_ucsd_module("flashArrayConnectHostToHostGroup")
pureHostToGroup08 = create_ucsd_module("flashArrayConnectHostToHostGroup")

pureHostToGroup01.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup01.modulePayload.param0.hostName = bmDeployServerBlade01.modulePayload.param1.list[1]['value']
pureHostToGroup01.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup02.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup02.modulePayload.param0.hostName = bmDeployServerBlade02.modulePayload.param1.list[1]['value']
pureHostToGroup02.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup03.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup03.modulePayload.param0.hostName = bmDeployServerBlade03.modulePayload.param1.list[1]['value']
pureHostToGroup03.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup04.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup04.modulePayload.param0.hostName = bmDeployServerBlade04.modulePayload.param1.list[1]['value']
pureHostToGroup04.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup05.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup05.modulePayload.param0.hostName = bmDeployServerBlade05.modulePayload.param1.list[1]['value']
pureHostToGroup05.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup06.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup06.modulePayload.param0.hostName = bmDeployServerBlade06.modulePayload.param1.list[1]['value']
pureHostToGroup06.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup07.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup07.modulePayload.param0.hostName = bmDeployServerBlade07.modulePayload.param1.list[1]['value']
pureHostToGroup07.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

pureHostToGroup08.modulePayload.param0.accountName = ACCOUNTS.PURE.name
pureHostToGroup08.modulePayload.param0.hostName = bmDeployServerBlade08.modulePayload.param1.list[1]['value']
pureHostToGroup08.modulePayload.param0.hostGroupName = pureHostGroup.modulePayload.param0.hostGroupPreName

if DEPLOY_STORAGE:
    print("Adding Hosts to Storage Group...")
    call_ucsd_api(pureHostToGroup01)
    call_ucsd_api(pureHostToGroup02)
    call_ucsd_api(pureHostToGroup03)
    call_ucsd_api(pureHostToGroup04)
    call_ucsd_api(pureHostToGroup05)
    call_ucsd_api(pureHostToGroup06)
    call_ucsd_api(pureHostToGroup07)
    call_ucsd_api(pureHostToGroup08)

####################
#                  #
#  Deploy vCenter  #
#                  #
####################

if DEPLOY_VCENTER:
    print()
    print("####################")
    print("#                  #")
    print("#  Deploy vCenter  #")
    print("#                  #")
    print("####################")
    print()

if DEPLOY_VCENTER:
    print("Deploying vCenter VCSA...", end="", flush=True)

    max_time = time.time() + 3600

    if OS == "Windows":
        new_call = Popen(['cmd', '/c', '.\\bin\\vcsa-cli-installer\\win32\\vcsa-deploy.exe', 'install', '--no-esx-ssl-verify', '--accept-eula', '--acknowledge-ceip', '..\\bin\\vcsa-cli-installer\\templates\\embedded_vCSA_on_ESXi_CLUS.json'], stdout=DEVNULL)
    elif OS == "Linux" or OS == "Darwin":
        new_call = Popen(['./bin/vcsa-cli-installer/win32/vcsa-deploy.exe', 'install', '--no-esx-ssl-verify', '--accept-eula', '--acknowledge-ceip', '../bin/vcsa-cli-installer/templates/embedded_vCSA_on_ESXi_CLUS.json'], stdout=DEVNULL)

    while new_call.poll() == None and time.time() < max_time:
        for i in range(20):
            spin_char()
        print(".", end="", flush=True)

    print()
    deploy_result = new_call.poll()

    if deploy_result == None:
        deploy_result = -1

    if deploy_result != 0 or time.time() > max_time:
        print("vCenter VCSA Deployment Failed!")
    else:
        print("vCenter VCSA Deployed Successfully!")

# if DEPLOY_VCENTER:
#     print()
#     print("##############################")
#     print("#                            #")
#     print("#  Creating vCenter Account  #")
#     print("#                            #")
#     print("##############################")
#     print()

# Add VMWare Account #
vmAccount = create_ucsd_module("userAPICreateInfraAccount")

vmAccount.modulePayload.param0.accountName = "vSphere"
vmAccount.modulePayload.param0.description = "vSphere Account"
vmAccount.modulePayload.param0.accountCategory = "5"
vmAccount.modulePayload.param0.accountType = "VMWARE"
vmAccount.modulePayload.param0.destinationIPAddress = "10.0.0.5"
vmAccount.modulePayload.param0.login = "administrator@vsphere.local"
vmAccount.modulePayload.param0.password = ACCOUNTS.VM.password
vmAccount.modulePayload.param0.protocol = "https"
vmAccount.modulePayload.param0.port = "443"

if DEPLOY_VCENTER:
   print("Adding vCenter Account...")
   call_ucsd_api(vmAccount)

# Pause for Initial vCenter Inventory #
if DEPLOY_VCENTER:
    print("Waiting 30 Seconds for vCenter Inventory...")
    time.sleep(30)

# Create VMWare Datacenter #
vmDatacenter = create_ucsd_module("createVMwareDatacenter")

vmDatacenter.modulePayload.param0.accountName = "vSphere"
vmDatacenter.modulePayload.param0.dcName = "CLUS-DC"

if DEPLOY_VCENTER:
   print("Creating VMWare Datacenter...")
   call_ucsd_api(vmDatacenter)

# Create VMWare Cluster #
vmCluster = create_ucsd_module("createVMwareCluster")

vmCluster.modulePayload.param0.accountName = "vSphere"
vmCluster.modulePayload.param0.dcName = "CLUS-DC"
vmCluster.modulePayload.param0.clusterName = "CLUS-CLUSTER"
vmCluster.modulePayload.param0.isDRSEnabled = "false"
vmCluster.modulePayload.param0.isAdmissionControlEnabled = "false"
vmCluster.modulePayload.param0.isDASEnabled = "false"
vmCluster.modulePayload.param0.swapFileLocation = "Store in Directory"

if DEPLOY_VCENTER:
   print("Creating VMWare Cluster...")
   call_ucsd_api(vmCluster)

# Add Hosts to VMWare Cluster #
vmHost01 = create_ucsd_module("registerHostWithVCenter")
vmHost02 = create_ucsd_module("registerHostWithVCenter")
vmHost03 = create_ucsd_module("registerHostWithVCenter")
vmHost04 = create_ucsd_module("registerHostWithVCenter")
vmHost05 = create_ucsd_module("registerHostWithVCenter")
vmHost06 = create_ucsd_module("registerHostWithVCenter")
vmHost07 = create_ucsd_module("registerHostWithVCenter")
vmHost08 = create_ucsd_module("registerHostWithVCenter")

vmHost01.modulePayload.param0.accountName = "vSphere"
vmHost01.modulePayload.param0.isPXEHost = "false"
vmHost01.modulePayload.param0.hostNode = "10.0.0.211"
vmHost01.modulePayload.param0.userName = "root"
vmHost01.modulePayload.param0.password = "password"
vmHost01.modulePayload.param0.associationType = "CLUSTER"
vmHost01.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost02.modulePayload.param0.accountName = "vSphere"
vmHost02.modulePayload.param0.isPXEHost = "false"
vmHost02.modulePayload.param0.hostNode = "10.0.0.212"
vmHost02.modulePayload.param0.userName = "root"
vmHost02.modulePayload.param0.password = "password"
vmHost02.modulePayload.param0.associationType = "CLUSTER"
vmHost02.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost03.modulePayload.param0.accountName = "vSphere"
vmHost03.modulePayload.param0.isPXEHost = "false"
vmHost03.modulePayload.param0.hostNode = "10.0.0.213"
vmHost03.modulePayload.param0.userName = "root"
vmHost03.modulePayload.param0.password = "password"
vmHost03.modulePayload.param0.associationType = "CLUSTER"
vmHost03.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost04.modulePayload.param0.accountName = "vSphere"
vmHost04.modulePayload.param0.isPXEHost = "false"
vmHost04.modulePayload.param0.hostNode = "10.0.0.214"
vmHost04.modulePayload.param0.userName = "root"
vmHost04.modulePayload.param0.password = "password"
vmHost04.modulePayload.param0.associationType = "CLUSTER"
vmHost04.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost05.modulePayload.param0.accountName = "vSphere"
vmHost05.modulePayload.param0.isPXEHost = "false"
vmHost05.modulePayload.param0.hostNode = "10.0.0.215"
vmHost05.modulePayload.param0.userName = "root"
vmHost05.modulePayload.param0.password = "password"
vmHost05.modulePayload.param0.associationType = "CLUSTER"
vmHost05.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost06.modulePayload.param0.accountName = "vSphere"
vmHost06.modulePayload.param0.isPXEHost = "false"
vmHost06.modulePayload.param0.hostNode = "10.0.0.216"
vmHost06.modulePayload.param0.userName = "root"
vmHost06.modulePayload.param0.password = "password"
vmHost06.modulePayload.param0.associationType = "CLUSTER"
vmHost06.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost07.modulePayload.param0.accountName = "vSphere"
vmHost07.modulePayload.param0.isPXEHost = "false"
vmHost07.modulePayload.param0.hostNode = "10.0.0.217"
vmHost07.modulePayload.param0.userName = "root"
vmHost07.modulePayload.param0.password = "password"
vmHost07.modulePayload.param0.associationType = "CLUSTER"
vmHost07.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

vmHost08.modulePayload.param0.accountName = "vSphere"
vmHost08.modulePayload.param0.isPXEHost = "false"
vmHost08.modulePayload.param0.hostNode = "10.0.0.218"
vmHost08.modulePayload.param0.userName = "root"
vmHost08.modulePayload.param0.password = "password"
vmHost08.modulePayload.param0.associationType = "CLUSTER"
vmHost08.modulePayload.param0.clusterOrDC = "CLUS-CLUSTER"

if DEPLOY_VCENTER:
   print("Adding Hosts to VMWare Cluster...")
   call_ucsd_api(vmHost01)
   call_ucsd_api(vmHost02)
   call_ucsd_api(vmHost03)
   call_ucsd_api(vmHost04)
   call_ucsd_api(vmHost05)
   call_ucsd_api(vmHost06)
   call_ucsd_api(vmHost07)
   call_ucsd_api(vmHost08)

# Attach Storage to VMWare Cluster #
vmDataStore = create_ucsd_module("userAPISubmitWorkflowServiceRequest")

vmDataStore.modulePayload.param0 = "Add Pure FlashArray Volume to ESXi Clusterv1"

volume_params = []
volume_params.append({"name":"vCenter Account","value":"vSphere"})
volume_params.append({"name":"Select Cluster","value":"CLUS-CLUSTER"})
volume_params.append({"name":"FlashArray Account","value":"PURE"})
volume_params.append({"name":"Host Group Name","value":"ESX-HOSTS"})
volume_params.append({"name":"Datastore Name","value":"ESXVol"})
volume_params.append({"name":"Datastore Size","value":"1"})
volume_params.append({"name":"Datastore Size Unit","value":"TB"})

vmDataStore.modulePayload.param1 = {"list":volume_params}

if DEPLOY_VCENTER:
   print("Attaching Datastore to vCenter...")
   call_ucsd_api(vmDataStore)

##################
#                #
#  Enable Proxy  #
#                #
##################

# Windows Operating Systems Only #
if OS == "Windows":
    if SET_PROXY:
        print("Enabling Proxy...")
        SetValueEx(A_KEY, "ProxyEnable", 0, REG_DWORD, 1)

# Collect End Time #
END_TIME = datetime.datetime.now()

# Print Script Runtime #
print()
print('Duration: {}'.format(END_TIME - START_TIME))
