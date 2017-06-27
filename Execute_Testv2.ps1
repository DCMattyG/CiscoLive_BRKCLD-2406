$global:basePath = "S:\Scripts\"
$global:modulePath = $basePath + "Modules\"
$ucsdAddr = "10.0.0.80"
<# Cloupia Key Build 65814 #>
$cloupiaKey = "F5B1B5577CCA44CEB4F45088CFED5814"

try {
    . ("$basePath\SSL_Helper.ps1")
    . ("$basePath\Function_Testv2.ps1")
}
catch {
    Write-Host "Error while loading supporting PowerShell Scripts" 
}


$accounts = Get-Content $basePath\Infra\accounts.json | Out-String | ConvertFrom-JSON

$deployAccounts = $false
$deployUCS = $false
$deployACI = $false
$deployMDS = $false

<######################>
<#                    #>
<# Set Temp Variables #>
<#                    #>
<######################>

$ucsdPod = "Default Pod"
#$ucsOrg = "root"

<#############################>
<#                           #>
<# Configure Device Accounts #>
<#                           #>
<#############################>

<# Add BMA Account #>
$bmaAccount = Create-UCSDModule $modulePath "addBmaAccount"

$bmaAccount.modulePayload.param0.bmaName = $accounts.BMA.name
$bmaAccount.modulePayload.param0.bmaDescription = $accounts.BMA.descr
$bmaAccount.modulePayload.param0.serverIP = $accounts.BMA.ipAddress
$bmaAccount.modulePayload.param0.pxeServerIP = $accounts.BMA.pxeAddress
$bmaAccount.modulePayload.param0.inventoryNodeIP = $ucsdAddr

if($deployAccounts) {
    Call-UCSDAPI $bmaAccount
}

<# Add UCS Account #>
$ucsAccount = Create-UCSDModule $modulePath "userAPICreateUCSAccount"

$ucsAccount.modulePayload.param0.accountName = $accounts.UCS.name
$ucsAccount.modulePayload.param0.description = $accounts.UCS.descr
$ucsAccount.modulePayload.param0.server = $accounts.UCS.ipAdddress
$ucsAccount.modulePayload.param0.userId = $accounts.UCS.userName
$ucsAccount.modulePayload.param0.passwd = $accounts.UCS.password

if($deployAccounts) {
    Call-UCSDAPI $ucsAccount
}

<# Add ACI Account #>
$aciAccount = Create-UCSDModule $modulePath "userAPICreateInfraAccount"

$aciAccount.modulePayload.param0.accountName = $accounts.ACI.name
$aciAccount.modulePayload.param0.description = $accounts.ACI.descr
$aciAccount.modulePayload.param0.destinationIPAddress = $accounts.ACI.ipAddress
$aciAccount.modulePayload.param0.login = $accounts.ACI.userName
$aciAccount.modulePayload.param0.password = $accounts.ACI.password

if($deployAccounts) {
    Call-UCSDAPI $aciAccount
}

<# Add MDS A/B Accounts #>
$mdsAccountA = Create-UCSDModule $modulePath "addPhysicalNetworkDeviceConfig"
$mdsAccountB = Create-UCSDModule $modulePath "addPhysicalNetworkDeviceConfig"

$mdsAccountA.modulePayload.param0.podName = $ucsdPod
$mdsAccountA.modulePayload.param0.serverAddress = $accounts.MDSA.ipAddress
$mdsAccountA.modulePayload.param0.username = $accounts.MDSA.userName
$mdsAccountA.modulePayload.param0.password = $accounts.MDSA.password

$mdsAccountB.modulePayload.param0.podName = $ucsdPod
$mdsAccountB.modulePayload.param0.serverAddress = $accounts.MDSB.ipAddress
$mdsAccountB.modulePayload.param0.username = $accounts.MDSB.userName
$mdsAccountb.modulePayload.param0.password = $accounts.MDSB.password

if($deployAccounts) {
    Call-UCSDAPI $mdsAccountA
    #Call-UCSDAPI $mdsAccountB
}

<#########################>
<#                       #>
<# Configure UCS Devices #>
<#                       #>
<#########################>

<# UCS Global Variables #>
$ucsOrg = "org-root"

<# UCS Configure Uplinks #>
$ucsUplinkA01 = Create-UCSDModule $modulePath "ucsConfigureUplinkPort"
$ucsUplinkA02 = Create-UCSDModule $modulePath "ucsConfigureUplinkPort"
$ucsUplinkB01 = Create-UCSDModule $modulePath "ucsConfigureUplinkPort"
$ucsUplinkB02 = Create-UCSDModule $modulePath "ucsConfigureUplinkPort"

$ucsUplinkA01.modulePayload.param0.ethernetPort = $accounts.UCS.name + ";sys/switch-A/slot-1/switch-ether/port-1"
$ucsUplinkA02.modulePayload.param0.ethernetPort = $accounts.UCS.name + ";sys/switch-A/slot-1/switch-ether/port-2"
$ucsUplinkB01.modulePayload.param0.ethernetPort = $accounts.UCS.name + ";sys/switch-B/slot-1/switch-ether/port-1"
$ucsUplinkB02.modulePayload.param0.ethernetPort = $accounts.UCS.name + ";sys/switch-B/slot-1/switch-ether/port-2"

if($deployUCS) {
    Call-UCSDAPI $ucsUplinkA01
    Call-UCSDAPI $ucsUplinkA02
    Call-UCSDAPI $ucsUplinkB01
    Call-UCSDAPI $ucsUplinkB02
}

<# UCS Create Port Channels #>

<# Port Channel Objects #>
$portA = New-Object System.Object
$portA | Add-Member -MemberType NoteProperty -Name "slotId" -Value "1"
$portA | Add-Member -MemberType NoteProperty -Name "portId" -Value "1"

$portB = New-Object System.Object
$portB | Add-Member -MemberType NoteProperty -Name "slotId" -Value "1"
$portB | Add-Member -MemberType NoteProperty -Name "portId" -Value "2"

$portArray = ($portA, $portB)

<# Port Channel Variables #>
$ucsPortchannelA = Create-UCSDModule $modulePath "ucsLanPortChannel"
$ucsPortchannelB = Create-UCSDModule $modulePath "ucsLanPortChannel"

$ucsPortchannelA.modulePayload.param0.accountName = $accounts.UCS.name
$ucsPortchannelA.modulePayload.param0.switchId = "A"
$ucsPortchannelA.modulePayload.param0.name = "PC01"
$ucsPortchannelA.modulePayload.param0.portId = "001"
$ucsPortchannelA.modulePayload.param0.portList = $portArray

$ucsPortchannelB.modulePayload.param0.accountName = $accounts.UCS.name
$ucsPortchannelB.modulePayload.param0.switchId = "B"
$ucsPortchannelB.modulePayload.param0.name = "PC02"
$ucsPortchannelB.modulePayload.param0.portId = "002"
$ucsPortchannelB.modulePayload.param0.portList = $portArray

<# Port Channel Execute #>
if($deployUCS) {
    Call-UCSDAPI $ucsPortchannelA
    Call-UCSDAPI $ucsPortchannelB
}

<#################################################################>
<# UCS Enable Port Channels Manually #>
<#################################################################>

<# UCS Create VLANs #>
$ucsVLAN02 = Create-UCSDModule $modulePath "ucsCreateVlan"
$ucsVLAN10 = Create-UCSDModule $modulePath "ucsCreateVlan"

$ucsVLAN02.modulePayload.param0.name = "VLAN2"
$ucsVLAN02.modulePayload.param0.accountName = $accounts.UCS.name
$ucsVLAN02.modulePayload.param0.physicalInfra = "true"
$ucsVLAN02.modulePayload.param0.vlanType = "dual"
$ucsVLAN02.modulePayload.param0.dualVLAN = "2"

$ucsVLAN10.modulePayload.param0.name = "VLAN10"
$ucsVLAN10.modulePayload.param0.accountName = $accounts.UCS.name
$ucsVLAN10.modulePayload.param0.physicalInfra = "true"
$ucsVLAN10.modulePayload.param0.vlanType = "dual"
$ucsVLAN10.modulePayload.param0.dualVLAN = "10"

if($deployUCS) {
    Call-UCSDAPI $ucsVLAN02
    Call-UCSDAPI $ucsVLAN10
}

<# UCS Create VSANs #>
$ucsVSAN20 = Create-UCSDModule $modulePath "ucsVsan"
$ucsVSAN30 = Create-UCSDModule $modulePath "ucsVsan"

$ucsVSAN20.modulePayload.param0.name = "VSAN20"
$ucsVSAN20.modulePayload.param0.id = "20"
$ucsVSAN20.modulePayload.param0.accountName = $accounts.UCS.name
$ucsVSAN20.modulePayload.param0.vsanType = "SAN Cloud"
$ucsVSAN20.modulePayload.param0.switchId = "A"
$ucsVSAN20.modulePayload.param0.fcoeVlan = "20"

$ucsVSAN30.modulePayload.param0.name = "VSAN30"
$ucsVSAN30.modulePayload.param0.id = "30"
$ucsVSAN30.modulePayload.param0.accountName = $accounts.UCS.name
$ucsVSAN30.modulePayload.param0.vsanType = "SAN Cloud"
$ucsVSAN30.modulePayload.param0.switchId = "B"
$ucsVSAN30.modulePayload.param0.fcoeVlan = "30"

if($deployUCS) {
    Call-UCSDAPI $ucsVSAN20
    Call-UCSDAPI $ucsVSAN30
}

<# UCS Create UUID Pool #>
$ucsUUIDPool = Create-UCSDModule $modulePath "ucsUuidPool"

$ucsUUIDPool.modulePayload.param0.name = "CLUS-UUID-POOL"
$ucsUUIDPool.modulePayload.param0.descr = "Cisco Live UUID Pool"
$ucsUUIDPool.modulePayload.param0.prefix = "other"
$ucsUUIDPool.modulePayload.param0.otherPrefix = "00000000-0000-0000"
$ucsUUIDPool.modulePayload.param0.accountName = $accounts.UCS.name
$ucsUUIDPool.modulePayload.param0.org = $ucsOrg
$ucsUUIDPool.modulePayload.param0.firstMACAddress = "0000-000000000001"
$ucsUUIDPool.modulePayload.param0.size = "32"

if($deployUCS) {
    Call-UCSDAPI $ucsUUIDPool
}

<# UCS Create IPMI Pool #>
$ucsIPMIPool = Create-UCSDModule $modulePath "createUcsIPPool"

$ucsIPMIPool.modulePayload.param0.ippoolName = "CLUS-EXT-MGMT"
$ucsIPMIPool.modulePayload.param0.descr = "Cisco Live Management IP Pool"
$ucsIPMIPool.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsIPMIPool.modulePayload.param0.assignmentOrder = "sequential"
$ucsIPMIPool.modulePayload.param0.addIPv6Block = "false"
$ucsIPMIPool.modulePayload.param0.addIPv4Block = "true"
$ucsIPMIPool.modulePayload.param0.ipv4BlockFromAddress = "10.0.0.110"
$ucsIPMIPool.modulePayload.param0.ipv4BlockSize = "32"
$ucsIPMIPool.modulePayload.param0.ipv4BlockSubnetMask = "255.255.255.0"
$ucsIPMIPool.modulePayload.param0.ipv4BlockDefaultGateway = "10.0.0.1"
$ucsIPMIPool.modulePayload.param0.ipv4BlockPrimaryDns = "171.68.226.120"
$ucsIPMIPool.modulePayload.param0.ipv4BlockSecondaryDns = "171.70.168.183"

if($deployUCS) {
    Call-UCSDAPI $ucsIPMIPool
}

<# UCS Create MAC Pools #>
$ucsMACPoolA = Create-UCSDModule $modulePath "ucsMacPool"
$ucsMACPoolB = Create-UCSDModule $modulePath "ucsMacPool"

$ucsMACPoolA.modulePayload.param0.name = "CLUS-MAC-POOL-A"
$ucsMACPoolA.modulePayload.param0.desc = "Cisco Live MAC Pool Side A"
$ucsMACPoolA.modulePayload.param0.accountName = $accounts.UCS.name
$ucsMACPoolA.modulePayload.param0.org = $ucsOrg
$ucsMACPoolA.modulePayload.param0.firstMACAddress = "00:25:B5:00:0A:00"
$ucsMACPoolA.modulePayload.param0.size = "32"

$ucsMACPoolB.modulePayload.param0.name = "CLUS-MAC-POOL-B"
$ucsMACPoolB.modulePayload.param0.desc = "Cisco Live MAC Pool Side B"
$ucsMACPoolB.modulePayload.param0.accountName = $accounts.UCS.name
$ucsMACPoolB.modulePayload.param0.org = $ucsOrg
$ucsMACPoolB.modulePayload.param0.firstMACAddress = "00:25:B5:00:0B:00"
$ucsMACPoolB.modulePayload.param0.size = "32"

if($deployUCS) {
    Call-UCSDAPI $ucsMACPoolA
    Call-UCSDAPI $ucsMACPoolB
}

<# UCS Create vNIC Templates #>
$ucsVNICTemplateA = Create-UCSDModule $modulePath "ucsAddvNICTemplate"
$ucsVNICTemplateB = Create-UCSDModule $modulePath "ucsAddvNICTemplate"

$ucsVNICTemplateA.modulePayload.param0.name = "CLUS-VNIC-TEMP-A"
$ucsVNICTemplateA.modulePayload.param0.descr = "Cisco Live vNIC Template Side A"
$ucsVNICTemplateA.modulePayload.param0.org = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsVNICTemplateA.modulePayload.param0.switchId = "A"
$ucsVNICTemplateA.modulePayload.param0.enableFailover = "false"
$ucsVNICTemplateA.modulePayload.param0.targetAdapter = "true"
$ucsVNICTemplateA.modulePayload.param0.targetVM = "false"
$ucsVNICTemplateA.modulePayload.param0.templType = "updating-template"
#$ucsVNICTemplateA.modulePayload.param0.vlanIdentityList = $accounts.UCS.name + ";fabric/lan/net-" + $ucsVLAN10.modulePayload.param0.name
$ucsVNICTemplateA.modulePayload.param0.vlanIdentityList = ($accounts.UCS.name + ";fabric/lan/net-default")
$ucsVNICTemplateA.modulePayload.param0.nativeVlan = "default"
$ucsVNICTemplateA.modulePayload.param0.mtu = "1500"
$ucsVNICTemplateA.modulePayload.param0.identPoolName = $accounts.UCS.name + ";org-root;org-root/mac-pool-" + $ucsMACPoolA.modulePayload.param0.name + ";" + $ucsMACPoolA.modulePayload.param0.name

$ucsVNICTemplateB.modulePayload.param0.name = "CLUS-VNIC-TEMP-B"
$ucsVNICTemplateB.modulePayload.param0.descr = "Cisco Live vNIC Template Side B"
$ucsVNICTemplateB.modulePayload.param0.org = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsVNICTemplateB.modulePayload.param0.switchId = "B"
$ucsVNICTemplateB.modulePayload.param0.enableFailover = "false"
$ucsVNICTemplateB.modulePayload.param0.targetAdapter = "true"
$ucsVNICTemplateB.modulePayload.param0.targetVM = "false"
$ucsVNICTemplateB.modulePayload.param0.templType = "updating-template"
#$ucsVNICTemplateB.modulePayload.param0.vlanIdentityList = $accounts.UCS.name + ";fabric/lan/net-" + $ucsVLAN10.modulePayload.param0.name
$ucsVNICTemplateB.modulePayload.param0.vlanIdentityList = ($accounts.UCS.name + ";fabric/lan/net-default")
$ucsVNICTemplateB.modulePayload.param0.nativeVlan = "default"
$ucsVNICTemplateB.modulePayload.param0.mtu = "1500"
$ucsVNICTemplateB.modulePayload.param0.identPoolName = $accounts.UCS.name + ";org-root;org-root/mac-pool-" + $ucsMACPoolB.modulePayload.param0.name + ";" + $ucsMACPoolB.modulePayload.param0.name

if($deployUCS) {
    Call-UCSDAPI $ucsVNICTemplateA
    Call-UCSDAPI $ucsVNICTemplateB
}
<# NOTES: May need to add "add vNIC to template to overcome issue #>

<# UCS Create LAN Connectivity Policy #>

<# LAN Connectivity Policy Objects #>
$lanTemplateA = New-Object System.Object
$lanTemplateA | Add-Member -MemberType NoteProperty -Name "adapterProfileName" -Value "CLUS-SIDE-A"
$lanTemplateA | Add-Member -MemberType NoteProperty -Name "nwTemplName" -Value "CLUS-VNIC-TEMP-A"
$lanTemplateA | Add-Member -MemberType NoteProperty -Name "name" -Value "CLUS-VNIC-A"
$lanTemplateA | Add-Member -MemberType NoteProperty -Name "order" -Value "1"
$lanTemplateA | Add-Member -MemberType NoteProperty -Name "status" -Value "created"

$lanTemplateB = New-Object System.Object
$lanTemplateB | Add-Member -MemberType NoteProperty -Name "adapterProfileName" -Value "CLUS-SIDE-B"
$lanTemplateB | Add-Member -MemberType NoteProperty -Name "nwTemplName" -Value "CLUS-VNIC-TEMP-B"
$lanTemplateB | Add-Member -MemberType NoteProperty -Name "name" -Value "CLUS-VNIC-B"
$lanTemplateB | Add-Member -MemberType NoteProperty -Name "order" -Value "2"
$lanTemplateB | Add-Member -MemberType NoteProperty -Name "status" -Value "created"

$lanTemplateArray = ($lanTemplateA, $lanTemplateB)

<# LAN Connectivity Policy Variables #>
$ucsLANConnectivityPol = Create-UCSDModule $modulePath "ucsLanConnectivityPolicy"

$ucsLANConnectivityPol.modulePayload.param0.name = "CLUS-LAN-CON-POL"
$ucsLANConnectivityPol.modulePayload.param0.descr = "Cisco Live LAN Connectivity Policy"
$ucsLANConnectivityPol.modulePayload.param0.accountName = $accounts.UCS.name
$ucsLANConnectivityPol.modulePayload.param0.org = $ucsOrg
$ucsLANConnectivityPol.modulePayload.param0.spVNIC = $lanTemplateArray

<# LAN Connectivity Policy Execute #>
if($deployUCS) {
    Call-UCSDAPI $ucsLANConnectivityPol
}

<# UCS Add vNICs to LAN Connectivity Policy
$ucsLANConnectivityPolvNICA = Create-UCSDModule $modulePath "updateUcsLanConnectivityPolicy"
$ucsLANConnectivityPolvNICB = Create-UCSDModule $modulePath "updateUcsLanConnectivityPolicy"

$ucsLANConnectivityPolvNICA.modulePayload.param0.name = $ucsLANConnectivityPol.modulePayload.param0.name
$ucsLANConnectivityPolvNICA.modulePayload.param0.spVNIC.adaptorProfileName = "clus-side-a"
$ucsLANConnectivityPolvNICA.modulePayload.param0.spVNIC.name = "vnic-tmp-clus-a"
$ucsLANConnectivityPolvNICA.modulePayload.param0.spVNIC.nwTemplName = "vnic-tmp-clus-a"
$ucsLANConnectivityPolvNICA.modulePayload.param0.spVNIC.order = "1"

$ucsLANConnectivityPolvNICB.modulePayload.param0.name = $ucsLANConnectivityPol.modulePayload.param0.name
$ucsLANConnectivityPolvNICB.modulePayload.param0.spVNIC.adaptorProfileName = "clus-side-b"
$ucsLANConnectivityPolvNICB.modulePayload.param0.spVNIC.name = "vnic-tmp-clus-b"
$ucsLANConnectivityPolvNICB.modulePayload.param0.spVNIC.nwTemplName = "vnic-tmp-clus-b"
$ucsLANConnectivityPolvNICB.modulePayload.param0.spVNIC.order = "1"

$ucsLANConnectivityPolvNICA.apiCall = "/cloupia/api-v2/datacenter/'Default Pod'/account/'" + $accounts.UCS.name + "'/ucsOrg/'org-root'/ucsLanConnectivityPolicy/'org-root/lan-conn-pol-" +$ucsLANConnectivityPol.modulePayload.param0.name + "'"

#Call-UCSDAPI $ucsLANConnectivityPolvNICA
#Call-UCSDAPI $ucsLANConnectivityPolvNICB
#>

<# UCS Create WWNN Pool #>
$ucsWWNNPool = Create-UCSDModule $modulePath "ucsWwnPool"

$ucsWWNNPool.modulePayload.param0.name = "CLUS-WWNN-POOL"
$ucsWWNNPool.modulePayload.param0.descr = "Cisco Live WWNN Pool"
$ucsWWNNPool.modulePayload.param0.accountName = $accounts.UCS.name
$ucsWWNNPool.modulePayload.param0.org = $ucsOrg
$ucsWWNNPool.modulePayload.param0.firstAddress = "20:00:00:25:B5:00:00:00"
$ucsWWNNPool.modulePayload.param0.size = "32"
$ucsWWNNPool.modulePayload.param0.purpose = "node-wwn-assignment"

if($deployUCS) {
    Call-UCSDAPI $ucsWWNNPool
}

<# UCS Create WWPN Pools #>
$ucsWWPNPoolA = Create-UCSDModule $modulePath "ucsWwnPool"
$ucsWWPNPoolB = Create-UCSDModule $modulePath "ucsWwnPool"

$ucsWWPNPoolA.modulePayload.param0.name = "CLUS-WWPN-POOL-A"
$ucsWWPNPoolA.modulePayload.param0.descr = "Cisco Live WWPN Pool Side A"
$ucsWWPNPoolA.modulePayload.param0.accountName = $accounts.UCS.name
$ucsWWPNPoolA.modulePayload.param0.org = $ucsOrg
$ucsWWPNPoolA.modulePayload.param0.firstAddress = "20:00:00:25:B5:00:0A:00"
$ucsWWPNPoolA.modulePayload.param0.size = "32"
$ucsWWPNPoolA.modulePayload.param0.purpose = "port-wwn-assignment"

$ucsWWPNPoolB.modulePayload.param0.name = "CLUS-WWPN-POOL-B"
$ucsWWPNPoolB.modulePayload.param0.descr = "Cisco Live WWPN Pool Side B"
$ucsWWPNPoolB.modulePayload.param0.accountName = $accounts.UCS.name
$ucsWWPNPoolB.modulePayload.param0.org = $ucsOrg
$ucsWWPNPoolB.modulePayload.param0.firstAddress = "20:00:00:25:B5:00:0B:00"
$ucsWWPNPoolB.modulePayload.param0.size = "32"
$ucsWWPNPoolB.modulePayload.param0.purpose = "port-wwn-assignment"

if($deployUCS) {
    Call-UCSDAPI $ucsWWPNPoolA
    Call-UCSDAPI $ucsWWPNPoolB
}

<# UCS Create vHBA Templates #>
$ucsVHBATemplateA = Create-UCSDModule $modulePath "ucsVhbaTemplate"
$ucsVHBATemplateB = Create-UCSDModule $modulePath "ucsVhbaTemplate"

$ucsVHBATemplateA.modulePayload.param0.name = "CLUS-VHBA-TMPL-A"
$ucsVHBATemplateA.modulePayload.param0.descr = "Cisco Live vHBA Template Side A"
$ucsVHBATemplateA.modulePayload.param0.accountName = $accounts.UCS.name
$ucsVHBATemplateA.modulePayload.param0.org = $ucsOrg
$ucsVHBATemplateA.modulePayload.param0.switchId = "A"
$ucsVHBATemplateA.modulePayload.param0.vSAN = "VSAN20"
$ucsVHBATemplateA.modulePayload.param0.templType = "updating-template"
$ucsVHBATemplateA.modulePayload.param0.maxDataFieldSize = "2048"
$ucsVHBATemplateA.modulePayload.param0.wwnPool = "CLUS-WWPN-POOL-A"

$ucsVHBATemplateB.modulePayload.param0.name = "CLUS-VHBA-TMPL-B"
$ucsVHBATemplateB.modulePayload.param0.descr = "Cisco Live vHBA Template Side B"
$ucsVHBATemplateB.modulePayload.param0.accountName = $accounts.UCS.name
$ucsVHBATemplateB.modulePayload.param0.org = $ucsOrg
$ucsVHBATemplateB.modulePayload.param0.switchId = "B"
$ucsVHBATemplateB.modulePayload.param0.vSAN = "VSAN30"
$ucsVHBATemplateB.modulePayload.param0.templType = "updating-template"
$ucsVHBATemplateB.modulePayload.param0.maxDataFieldSize = "2048"
$ucsVHBATemplateB.modulePayload.param0.wwnPool = "CLUS-WWPN-POOL-B"

if($deployUCS) {
    Call-UCSDAPI $ucsVHBATemplateA
    Call-UCSDAPI $ucsVHBATemplateB
}

<# UCS Create SAN Connectivity Policy #>

<# SAN Connectivity Policy Objects #>
$sanTemplateA = New-Object System.Object
$sanTemplateA | Add-Member -MemberType NoteProperty -Name "nwTemplName" -Value "CLUS-VHBA-TMPL-A"
$sanTemplateA | Add-Member -MemberType NoteProperty -Name "name" -Value "CLUS-VHBA-A"
$sanTemplateA | Add-Member -MemberType NoteProperty -Name "order" -Value "1"
$sanTemplateA | Add-Member -MemberType NoteProperty -Name "spDn" -Value $ucsOrg
$sanTemplateA | Add-Member -MemberType NoteProperty -Name "status" -Value "created"

$sanTemplateB = New-Object System.Object
$sanTemplateB | Add-Member -MemberType NoteProperty -Name "nwTemplName" -Value "CLUS-VHBA-TMPL-B"
$sanTemplateB | Add-Member -MemberType NoteProperty -Name "name" -Value "CLUS-VHBA-B"
$sanTemplateB | Add-Member -MemberType NoteProperty -Name "order" -Value "2"
$sanTemplateB | Add-Member -MemberType NoteProperty -Name "spDn" -Value $ucsOrg
$sanTemplateB | Add-Member -MemberType NoteProperty -Name "status" -Value "created"

$sanTemplateArray = ($sanTemplateA, $sanTemplateB)

<# SAN Connectivity Policy Variables #>
$ucsSANConnectivityPol = Create-UCSDModule $modulePath "ucsSanConnectivityPolicy"

$ucsSANConnectivityPol.modulePayload.param0.name = "CLUS-SAN-CON-POL"
$ucsSANConnectivityPol.modulePayload.param0.descr = "Cisco Live SAN Connectivity Policy"
$ucsSANConnectivityPol.modulePayload.param0.accountName = $accounts.UCS.name
$ucsSANConnectivityPol.modulePayload.param0.org = $ucsORg
$ucsSANConnectivityPol.modulePayload.param0.identPoolName = "CLUS-WWNN-POOL"
$ucsSANConnectivityPol.modulePayload.param0.spVHBA = $sanTemplateArray

<# SAN Connectivity Policy Execute #>
if($deployUCS) {
    Call-UCSDAPI $ucsSANConnectivityPol
}

<# UCS Create Server Pool #>
$ucsServerPoolBlade = Create-UCSDModule $modulePath "ucsCreateServerPool"
$ucsServerPoolRack = Create-UCSDModule $modulePath "ucsCreateServerPool"

$ucsServerPoolBlade.modulePayload.param0.poolName = "CLUS-BLADE-POOL"
$ucsServerPoolBlade.modulePayload.param0.poolDescription = "Cisco Live Blade Server Pool"
$ucsServerPoolBlade.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsServerPoolBlade.modulePayload.param0.serverPoolList = ""

$ucsServerPoolRack.modulePayload.param0.poolName = "CLUS-RACK-POOL"
$ucsServerPoolRack.modulePayload.param0.poolDescription = "Cisco Live Rack Server Pool"
$ucsServerPoolRack.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsServerPoolRack.modulePayload.param0.serverPoolList = ""

if($deployUCS) {
    Call-UCSDAPI $ucsServerPoolBlade
    Call-UCSDAPI $ucsServerPoolRack
}

<# UCS Create Server Qualification #>
$ucsServerPoolQualBlade = Create-UCSDModule $modulePath "createUcsServerQualification"
$ucsServerPoolQualRack = Create-UCSDModule $modulePath "createUcsServerQualification"

$ucsServerPoolQualBlade.modulePayload.param0.name = "CLUS-BLADE-QUAL"
$ucsServerPoolQualBlade.modulePayload.param0.descr = "Cisco Live Blade Server Qualification"
$ucsServerPoolQualBlade.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsServerPoolQualBlade.modulePayload.param0.chassisQualExists = "true"
$ucsServerPoolQualBlade.modulePayload.param0.minChassisId = "1"
$ucsServerPoolQualBlade.modulePayload.param0.maxChassisId = "20"

$ucsServerPoolQualRack.modulePayload.param0.name = "CLUS-RACK-QUAL"
$ucsServerPoolQualRack.modulePayload.param0.descr = "Cisco Live Rack Server Qualification"
$ucsServerPoolQualRack.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsServerPoolQualRack.modulePayload.param0.rackQualExists = "true"
$ucsServerPoolQualRack.modulePayload.param0.minRackId = "1"
$ucsServerPoolQualRack.modulePayload.param0.maxRackId = "20"

if($deployUCS) {
    Call-UCSDAPI $ucsServerPoolQualBlade
    Call-UCSDAPI $ucsServerPoolQualRack
}

<# UCS Create Server Qualification #>
$ucsServerPoolPolicyBlade = Create-UCSDModule $modulePath "createUcsServerPoolPolicy"
$ucsServerPoolPolicyRack = Create-UCSDModule $modulePath "createUcsServerPoolPolicy"

$ucsServerPoolPolicyBlade.modulePayload.param0.name = "CLUS-BLADE-POL"
$ucsServerPoolPolicyBlade.modulePayload.param0.descr = "Cisco Live Blade Qualification Policy"
$ucsServerPoolPolicyBlade.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsServerPoolPolicyBlade.modulePayload.param0.qualIdentity = ($accounts.UCS.name + ";" + $ucsOrg + ";" + $ucsOrg + "/blade-qualifier-" + $ucsServerPoolQualBlade.modulePayload.param0.name)
$ucsServerPoolPolicyBlade.modulePayload.param0.poolDn = ($accounts.UCS.name + ";" + $ucsOrg + ";" + $ucsOrg + "/compute-pool-" + $ucsServerPoolBlade.modulePayload.param0.poolName)

$ucsServerPoolPolicyRack.modulePayload.param0.name = "CLUS-RACK-POL"
$ucsServerPoolPolicyRack.modulePayload.param0.descr = "Cisco Live Rack Qualification Policy"
$ucsServerPoolPolicyRack.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsServerPoolPolicyRack.modulePayload.param0.qualIdentity = ($accounts.UCS.name + ";" + $ucsOrg + ";" + $ucsOrg + "/blade-qualifier-" + $ucsServerPoolQualRack.modulePayload.param0.name)
$ucsServerPoolPolicyRack.modulePayload.param0.poolDn = ($accounts.UCS.name + ";" + $ucsOrg + ";" + $ucsOrg + "/compute-pool-" + $ucsServerPoolRack.modulePayload.param0.poolName)

if($deployUCS) {
    Call-UCSDAPI $ucsServerPoolPolicyBlade
    Call-UCSDAPI $ucsServerPoolPolicyRack
}

<# UCS Create Local Disk Policy #>
$ucsLocalDiskPolicyRAID1 = Create-UCSDModule $modulePath "createLocalDiskConfigurationPolicy"
$ucsLocalDiskPolicyRAID5 = Create-UCSDModule $modulePath "createLocalDiskConfigurationPolicy"

$ucsLocalDiskPolicyRAID1.modulePayload.param0.name = "CLUS-DISK-RAID1"
$ucsLocalDiskPolicyRAID1.modulePayload.param0.descr = "Cisco Live Local Disk RAID1"
$ucsLocalDiskPolicyRAID1.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsLocalDiskPolicyRAID1.modulePayload.param0.mode = "raid-mirrored"
$ucsLocalDiskPolicyRAID1.modulePayload.param0.protectConfig = "false"
$ucsLocalDiskPolicyRAID1.modulePayload.param0.flexFlashState = "disable"

$ucsLocalDiskPolicyRAID5.modulePayload.param0.name = "CLUS-DISK-RAID5"
$ucsLocalDiskPolicyRAID5.modulePayload.param0.descr = "Cisco Live Local Disk RAID5"
$ucsLocalDiskPolicyRAID5.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsLocalDiskPolicyRAID5.modulePayload.param0.mode = "raid-striped-parity"
$ucsLocalDiskPolicyRAID5.modulePayload.param0.protectConfig = "false"
$ucsLocalDiskPolicyRAID5.modulePayload.param0.flexFlashState = "disable"

if($deployUCS) {
    Call-UCSDAPI $ucsLocalDiskPolicyRAID1
    Call-UCSDAPI $ucsLocalDiskPolicyRAID5
}

<# UCS Create Boot Policy #>
$ucsBootPolicyHDD = Create-UCSDModule $modulePath "ucsCreateBootPolicy"
$ucsBootPolicyLAN = Create-UCSDModule $modulePath "ucsCreateBootPolicy"
#$ucsBootPolicySAN = Create-UCSDModule $modulePath "ucsCreateBootPolicy"

$ucsBootPolicyHDD.modulePayload.param0.policyName = "CLUS-BOOT-HDD"
$ucsBootPolicyHDD.modulePayload.param0.policyDescription = "Cisco Live Boot from HDD"
$ucsBootPolicyHDD.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsBootPolicyHDD.modulePayload.param0.rebootOnOrderChange = "false"
$ucsBootPolicyHDD.modulePayload.param0.enforceNames = "false"
$ucsBootPolicyHDD.modulePayload.param0.bootMode = "legacy"
$ucsBootPolicyHDD.modulePayload.param0.bootSecurity = "false"
$ucsBootPolicyHDD.modulePayload.param0.addLocalDisk = "true"

$ucsBootPolicyLAN.modulePayload.param0.policyName = "CLUS-BOOT-LAN"
$ucsBootPolicyLAN.modulePayload.param0.policyDescription = "Cisco Live Boot from LAN"
$ucsBootPolicyLAN.modulePayload.param0.orgIdentity = ($accounts.UCS.name + ";" + $ucsOrg)
$ucsBootPolicyLAN.modulePayload.param0.rebootOnOrderChange = "false"
$ucsBootPolicyLAN.modulePayload.param0.enforceNames = "false"
$ucsBootPolicyLAN.modulePayload.param0.bootMode = "legacy"
$ucsBootPolicyLAN.modulePayload.param0.bootSecurity = "false"
$ucsBootPolicyLAN.modulePayload.param0.addPriLanBoot = "true"
$ucsBootPolicyLAN.modulePayload.param0.privNIC = "eth0"
$ucsBootPolicyLAN.modulePayload.param0.addSecLanBoot = "true"
$ucsBootPolicyLAN.modulePayload.param0.secvNIC = "eth1"

if($deployUCS) {
    Call-UCSDAPI $ucsBootPolicyHDD
    Call-UCSDAPI $ucsBootPolicyLAN
    #Call-UCSDAPI $ucsBootPolicySAN
}

<# UCS Create Storage Policy #>
$ucsStoragePolicyRAID1 = Create-UCSDModule $modulePath "ucsStoragePolicy"
$ucsStoragePolicyRAID5 = Create-UCSDModule $modulePath "ucsStoragePolicy"

$ucsStoragePolicyRAID1.modulePayload.param0.policyName = "CLUS-STOR-POL-R1"
$ucsStoragePolicyRAID1.modulePayload.param0.policyDescription = "Cisco Live Storage Policy RAID1"
$ucsStoragePolicyRAID1.modulePayload.param0.ucsAcctName = $accounts.UCS.name
$ucsStoragePolicyRAID1.modulePayload.param0.orgName = $ucsOrg
$ucsStoragePolicyRAID1.modulePayload.param0.localDiskConfigPolicy = $ucsLocalDiskPolicyRAID1.modulePayload.param0.name
$ucsStoragePolicyRAID1.modulePayload.param0.connectivityType = "Use SAN Connectivity Policy"
$ucsStoragePolicyRAID1.modulePayload.param0.noOfVhba= "0"
$ucsStoragePolicyRAID1.modulePayload.param0.sanConnPolicy = $ucsSANConnectivityPol.modulePayload.param0.name

$ucsStoragePolicyRAID5.modulePayload.param0.policyName = "CLUS-STOR-POL-R5"
$ucsStoragePolicyRAID5.modulePayload.param0.policyDescription = "Cisco Live Storage Policy RAID5"
$ucsStoragePolicyRAID5.modulePayload.param0.ucsAcctName = $accounts.UCS.name
$ucsStoragePolicyRAID5.modulePayload.param0.orgName = $ucsOrg
$ucsStoragePolicyRAID5.modulePayload.param0.localDiskConfigPolicy = $ucsLocalDiskPolicyRAID5.modulePayload.param0.name
$ucsStoragePolicyRAID5.modulePayload.param0.connectivityType = "Use SAN Connectivity Policy"
$ucsStoragePolicyRAID5.modulePayload.param0.noOfVhba= "0"
$ucsStoragePolicyRAID5.modulePayload.param0.sanConnPolicy = $ucsSANConnectivityPol.modulePayload.param0.name

if($deployUCS) {
    Call-UCSDAPI $ucsStoragePolicyRAID1
    Call-UCSDAPI $ucsStoragePolicyRAID5
}

<# UCS Create Network Policy #>
$ucsNetworkPolicy = Create-UCSDModule $modulePath "ucsNetworkPolicy"

$ucsNetworkPolicy.modulePayload.param0.policyName = "CLUS-NET-POL"
$ucsNetworkPolicy.modulePayload.param0.policyDescription = "Cisco Live Network Policy"
$ucsNetworkPolicy.modulePayload.param0.accountName = $accounts.UCS.name
$ucsNetworkPolicy.modulePayload.param0.orgDn = $ucsOrg
$ucsNetworkPolicy.modulePayload.param0.connectivityType = "Use LAN Connectivity Policy"
$ucsNetworkPolicy.modulePayload.param0.lanConnPolicy = $ucsLANConnectivityPol.modulePayload.param0.name
$ucsNetworkPolicy.modulePayload.param0.expertNoOfVnics = "0"

if($deployUCS) {
    Call-UCSDAPI $ucsNetworkPolicy
}

<# UCS Create Service Profile Template #>
$ucsSPTemplateBlade = Create-UCSDModule $modulePath "userAPICreateServiceProfileTemplate"
$ucsSPTemplateRack = Create-UCSDModule $modulePath "userAPICreateServiceProfileTemplate"

$ucsSPTemplateBlade.modulePayload.param0 = $accounts.UCS.name
$ucsSPTemplateBlade.modulePayload.param3.spTemplateName = "ESX_Template_Blade"
$ucsSPTemplateBlade.modulePayload.param3.storagePolicyName = $ucsStoragePolicyRAID1.modulePayload.param0.policyName
$ucsSPTemplateBlade.modulePayload.param3.networkPolicyName = $ucsNetworkPolicy.modulePayload.param0.policyName
$ucsSPTemplateBlade.modulePayload.param3.OrgName = $ucsOrg
$ucsSPTemplateBlade.modulePayload.param3.spTemplateType = "Updating-Template"
$ucsSPTemplateBlade.modulePayload.param3.serverPowerState = "down"
$ucsSPTemplateBlade.modulePayload.param3.uuidPool.name = $ucsUUIDPool.modulePayload.param0.name
$ucsSPTemplateBlade.modulePayload.param3.bootPolicy.name = $ucsBootPolicyHDD.modulePayload.param0.policyName

$ucsSPTemplateRack.modulePayload.param0 = $accounts.UCS.name
$ucsSPTemplateRack.modulePayload.param3.spTemplateName = "ESX_Template_Rack"
$ucsSPTemplateRack.modulePayload.param3.storagePolicyName = $ucsStoragePolicyRAID5.modulePayload.param0.policyName
$ucsSPTemplateRack.modulePayload.param3.networkPolicyName = $ucsNetworkPolicy.modulePayload.param0.policyName
$ucsSPTemplateRack.modulePayload.param3.OrgName = $ucsOrg
$ucsSPTemplateRack.modulePayload.param3.spTemplateType = "Updating-Template"
$ucsSPTemplateRack.modulePayload.param3.serverPowerState = "down"
$ucsSPTemplateRack.modulePayload.param3.uuidPool.name = $ucsUUIDPool.modulePayload.param0.name
$ucsSPTemplateRack.modulePayload.param3.bootPolicy.name = $ucsBootPolicyHDD.modulePayload.param0.policyName

if($deployUCS) {
    Call-UCSDAPI $ucsSPTemplateBlade
    Call-UCSDAPI $ucsSPTemplateRack
}

<#########################>
<#                       #>
<# Configure ACI Devices #>
<#                       #>
<#########################>

<# ACI Create VLAN Pool #>
$aciVLANPool = Create-UCSDModule $modulePath "createVlanPoolConfig"

$aciVLANPool.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciVLANPool.modulePayload.param0.vlanPoolName = "CLUS-VLAN-POOL"
$aciVLANPool.modulePayload.param0.description= "Cisco Live Physical VLAN Pool"
$aciVLANPool.modulePayload.param0.range = "1-10"

if($deployACI) {
    Call-UCSDAPI $aciVLANPool
}

<# ACI Create AEP #>
$aciAEP = Create-UCSDModule $modulePath "createAttachableEntityProfileConfig"

$aciAEP.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciAEP.modulePayload.param0.name = "CLUS-AEP"
$aciAEP.modulePayload.param0.description = "Cisco Live Attachable Entity Profile"

if($deployACI) {
    Call-UCSDAPI $aciAEP
}

<# ACI Create Physical Domain #>
$aciPhysDom = Create-UCSDModule $modulePath "createPhysicalDomainConfig"

$aciPhysDom.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciPhysDom.modulePayload.param0.name = "CLUS-PHYS-DOM"
$aciPhysDom.modulePayload.param0.entityProfile = ($accounts.ACI.name + "@" + $aciAEP.modulePayload.param0.name)
$aciPhysDom.modulePayload.param0.vlanPool = ($accounts.ACI.name + "@" + $aciVLANPool.modulePayload.param0.vlanPoolName + "@static")

if($deployACI) {
    Call-UCSDAPI $aciPhysDom
}

<# ACI Create Link Level Policy #>
$aciLinkLevelPol1G = Create-UCSDModule $modulePath "createLinkLevelPolicyConfig"
$aciLinkLevelPol10G = Create-UCSDModule $modulePath "createLinkLevelPolicyConfig"

$aciLinkLevelPol1G.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciLinkLevelPol1G.modulePayload.param0.linkLevelName = "LINKLEVEL-POL-1G"
$aciLinkLevelPol1G.modulePayload.param0.description = "Link Level Policy 1G"
$aciLinkLevelPol1G.modulePayload.param0.speed = "1G"

$aciLinkLevelPol10G.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciLinkLevelPol10G.modulePayload.param0.linkLevelName = "LINKLEVEL-POL-10G"
$aciLinkLevelPol10G.modulePayload.param0.description = "Link Level Policy 10G"
$aciLinkLevelPol10G.modulePayload.param0.speed = "10G"

if($deployACI) {
    Call-UCSDAPI $aciLinkLevelPol1G
    Call-UCSDAPI $aciLinkLevelPol10G
}

<# ACI Create CDP Policy #>
$aciCDPPolicyON = Create-UCSDModule $modulePath "createCDPInterfacePolicyConfig"
$aciCDPPolicyOFF = Create-UCSDModule $modulePath "createCDPInterfacePolicyConfig"

$aciCDPPolicyON.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciCDPPolicyON.modulePayload.param0.cdpInterfaceName = "CDP-POL-ON"
$aciCDPPolicyON.modulePayload.param0.description = "CDP Policy ON"
$aciCDPPolicyON.modulePayload.param0.adminState = "enabled"

$aciCDPPolicyOFF.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciCDPPolicyOFF.modulePayload.param0.cdpInterfaceName = "CDP-POL-OFF"
$aciCDPPolicyOFF.modulePayload.param0.description = "CDP Policy OFF"
$aciCDPPolicyOFF.modulePayload.param0.adminState = "disabled"

if($deployACI) {
    Call-UCSDAPI $aciCDPPolicyON
    Call-UCSDAPI $aciCDPPolicyOFF
}

<# ACI Create LLDP Policy #>
$aciLLDPPolicyON = Create-UCSDModule $modulePath "createLLDPInterfacePolicyConfig"
$aciLLDPPolicyOFF = Create-UCSDModule $modulePath "createLLDPInterfacePolicyConfig"

$aciLLDPPolicyON.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName = "LLDP-POL-ON"
$aciLLDPPolicyON.modulePayload.param0.description = "LLDP Policy ON"
$aciLLDPPolicyON.modulePayload.param0.receiveState = "enabled"
$aciLLDPPolicyON.modulePayload.param0.transmitState = "enabled"

$aciLLDPPolicyOFF.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciLLDPPolicyOFF.modulePayload.param0.lldpInterfaceName = "LLDP-POL-OFF"
$aciLLDPPolicyOFF.modulePayload.param0.description = "LLDP Policy OFF"
$aciLLDPPolicyOFF.modulePayload.param0.receiveState = "disabled"
$aciLLDPPolicyOFF.modulePayload.param0.transmitState = "disabled"

if($deployACI) {
    Call-UCSDAPI $aciLLDPPolicyON
    Call-UCSDAPI $aciLLDPPolicyOFF
}

<# ACI Create Port Channel Policy #>
$aciPCPolicyLACP = Create-UCSDModule $modulePath "createPortChannelPolicyConfig"

$aciPCPolicyLACP.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciPCPolicyLACP.modulePayload.param0.interfaceName = "PORTCHANNEL-POL-LACP"
$aciPCPolicyLACP.modulePayload.param0.description = "Port Channel Policy LACP Active"
$aciPCPolicyLACP.modulePayload.param0.mode = "LACP Active"

if($deployACI) {
    Call-UCSDAPI $aciPCPolicyLACP
}

<# ACI Create Interface Policy Group #>
$aciIntPolGroupInt07 = Create-UCSDModule $modulePath "createVPCInterfacePolicyGroupConfig"
$aciIntPolGroupInt23 = Create-UCSDModule $modulePath "createVPCInterfacePolicyGroupConfig"
$aciIntPolGroupInt24 = Create-UCSDModule $modulePath "createVPCInterfacePolicyGroupConfig"
$aciIntPolGroupInt47 = Create-UCSDModule $modulePath "createVPCInterfacePolicyGroupConfig"
$aciIntPolGroupInt48 = Create-UCSDModule $modulePath "createVPCInterfacePolicyGroupConfig"

$aciIntPolGroupInt07.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntPolGroupInt07.modulePayload.param0.name = "VPC-INT-POL-GRP-07"
$aciIntPolGroupInt07.modulePayload.param0.description = "VPC Interface Policy Group e1/7"
$aciIntPolGroupInt07.modulePayload.param0.linkLevelPolicy = ($accounts.ACI.name + "@" + $aciLinkLevelPol10G.modulePayload.param0.linkLevelName)
$aciIntPolGroupInt07.modulePayload.param0.cdpPolicy = ($accounts.ACI.name + "@" + $aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
$aciIntPolGroupInt07.modulePayload.param0.lldpPolicy = ($accounts.ACI.name + "@" + $aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
$aciIntPolGroupInt07.modulePayload.param0.attachedEntryProfile = ($accounts.ACI.name + "@" + $aciAEP.modulePayload.param0.name)
$aciIntPolGroupInt07.modulePayload.param0.portChannelPolicy = ($accounts.ACI.name + "@" + $aciPCPolicyLACP.modulePayload.param0.interfaceName)

$aciIntPolGroupInt23.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntPolGroupInt23.modulePayload.param0.name = "VPC-INT-POL-GRP-23"
$aciIntPolGroupInt23.modulePayload.param0.description = "VPC Interface Policy Group e1/23"
$aciIntPolGroupInt23.modulePayload.param0.linkLevelPolicy = ($accounts.ACI.name + "@" + $aciLinkLevelPol10G.modulePayload.param0.linkLevelName)
$aciIntPolGroupInt23.modulePayload.param0.cdpPolicy = ($accounts.ACI.name + "@" + $aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
$aciIntPolGroupInt23.modulePayload.param0.lldpPolicy = ($accounts.ACI.name + "@" + $aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
$aciIntPolGroupInt23.modulePayload.param0.attachedEntryProfile = ($accounts.ACI.name + "@" + $aciAEP.modulePayload.param0.name)
$aciIntPolGroupInt23.modulePayload.param0.portChannelPolicy = ($accounts.ACI.name + "@" + $aciPCPolicyLACP.modulePayload.param0.interfaceName)

$aciIntPolGroupInt24.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntPolGroupInt24.modulePayload.param0.name = "VPC-INT-POL-GRP-24"
$aciIntPolGroupInt24.modulePayload.param0.description = "VPC Interface Policy Group e1/24"
$aciIntPolGroupInt24.modulePayload.param0.linkLevelPolicy = ($accounts.ACI.name + "@" + $aciLinkLevelPol10G.modulePayload.param0.linkLevelName)
$aciIntPolGroupInt24.modulePayload.param0.cdpPolicy = ($accounts.ACI.name + "@" + $aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
$aciIntPolGroupInt24.modulePayload.param0.lldpPolicy = ($accounts.ACI.name + "@" + $aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
$aciIntPolGroupInt24.modulePayload.param0.attachedEntryProfile = ($accounts.ACI.name + "@" + $aciAEP.modulePayload.param0.name)
$aciIntPolGroupInt24.modulePayload.param0.portChannelPolicy = ($accounts.ACI.name + "@" + $aciPCPolicyLACP.modulePayload.param0.interfaceName)

$aciIntPolGroupInt47.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntPolGroupInt47.modulePayload.param0.name = "VPC-INT-POL-GRP-47"
$aciIntPolGroupInt47.modulePayload.param0.description = "VPC Interface Policy Group e1/47"
$aciIntPolGroupInt47.modulePayload.param0.linkLevelPolicy = ($accounts.ACI.name + "@" + $aciLinkLevelPol1G.modulePayload.param0.linkLevelName)
$aciIntPolGroupInt47.modulePayload.param0.cdpPolicy = ($accounts.ACI.name + "@" + $aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
$aciIntPolGroupInt47.modulePayload.param0.lldpPolicy = ($accounts.ACI.name + "@" + $aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
$aciIntPolGroupInt47.modulePayload.param0.attachedEntryProfile = ($accounts.ACI.name + "@" + $aciAEP.modulePayload.param0.name)
$aciIntPolGroupInt47.modulePayload.param0.portChannelPolicy = ($accounts.ACI.name + "@" + $aciPCPolicyLACP.modulePayload.param0.interfaceName)

$aciIntPolGroupInt48.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntPolGroupInt48.modulePayload.param0.name = "VPC-INT-POL-GRP-48"
$aciIntPolGroupInt48.modulePayload.param0.description = "VPC Interface Policy Group e1/48"
$aciIntPolGroupInt48.modulePayload.param0.linkLevelPolicy = ($accounts.ACI.name + "@" + $aciLinkLevelPol1G.modulePayload.param0.linkLevelName)
$aciIntPolGroupInt48.modulePayload.param0.cdpPolicy = ($accounts.ACI.name + "@" + $aciCDPPolicyON.modulePayload.param0.cdpInterfaceName)
$aciIntPolGroupInt48.modulePayload.param0.lldpPolicy = ($accounts.ACI.name + "@" + $aciLLDPPolicyON.modulePayload.param0.lldpInterfaceName)
$aciIntPolGroupInt48.modulePayload.param0.attachedEntryProfile = ($accounts.ACI.name + "@" + $aciAEP.modulePayload.param0.name)
$aciIntPolGroupInt48.modulePayload.param0.portChannelPolicy = ($accounts.ACI.name + "@" + $aciPCPolicyLACP.modulePayload.param0.interfaceName)

if($deployACI) {
    Call-UCSDAPI $aciIntPolGroupInt07
    Call-UCSDAPI $aciIntPolGroupInt23
    Call-UCSDAPI $aciIntPolGroupInt24
    Call-UCSDAPI $aciIntPolGroupInt47
    Call-UCSDAPI $aciIntPolGroupInt48
}

<# ACI Create Interface Profile #>
$aciIntProfileInt07 = Create-UCSDModule $modulePath "createInterfaceProfileConfig"
$aciIntProfileInt23 = Create-UCSDModule $modulePath "createInterfaceProfileConfig"
$aciIntProfileInt24 = Create-UCSDModule $modulePath "createInterfaceProfileConfig"
$aciIntProfileInt47 = Create-UCSDModule $modulePath "createInterfaceProfileConfig"
$aciIntProfileInt48 = Create-UCSDModule $modulePath "createInterfaceProfileConfig"

$aciIntProfileInt07.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntProfileInt07.modulePayload.param0.name = "CLUS-INT-PROF-07"
$aciIntProfileInt07.modulePayload.param0.description = "Cisco Live Interface Profile e1/7"

$aciIntProfileInt23.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntProfileInt23.modulePayload.param0.name = "CLUS-INT-PROF-23"
$aciIntProfileInt23.modulePayload.param0.description = "Cisco Live Interface Profile e1/23"

$aciIntProfileInt24.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntProfileInt24.modulePayload.param0.name = "CLUS-INT-PROF-24"
$aciIntProfileInt24.modulePayload.param0.description = "Cisco Live Interface Profile e1/24"

$aciIntProfileInt47.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntProfileInt47.modulePayload.param0.name = "CLUS-INT-PROF-47"
$aciIntProfileInt47.modulePayload.param0.description = "Cisco Live Interface Profile e1/47"

$aciIntProfileInt48.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciIntProfileInt48.modulePayload.param0.name = "CLUS-INT-PROF-48"
$aciIntProfileInt48.modulePayload.param0.description = "Cisco Live Interface Profile e1/48"

if($deployACI) {
    Call-UCSDAPI $aciIntProfileInt07
    Call-UCSDAPI $aciIntProfileInt23
    Call-UCSDAPI $aciIntProfileInt24
    Call-UCSDAPI $aciIntProfileInt47
    Call-UCSDAPI $aciIntProfileInt48
}

<# ACI Associate Access Ports to Interface Profile #>
$aciAccessPortToIntProfInt07 = Create-UCSDModule $modulePath "associateAccessPortSelectorToInterfaceProfileConfig"
$aciAccessPortToIntProfInt23 = Create-UCSDModule $modulePath "associateAccessPortSelectorToInterfaceProfileConfig"
$aciAccessPortToIntProfInt24 = Create-UCSDModule $modulePath "associateAccessPortSelectorToInterfaceProfileConfig"
$aciAccessPortToIntProfInt47 = Create-UCSDModule $modulePath "associateAccessPortSelectorToInterfaceProfileConfig"
$aciAccessPortToIntProfInt48 = Create-UCSDModule $modulePath "associateAccessPortSelectorToInterfaceProfileConfig"

$aciAccessPortToIntProfInt07.modulePayload.param0.interfaceProfile = ($accounts.ACI.name + "@" + $aciIntProfileInt07.modulePayload.param0.name)
$aciAccessPortToIntProfInt07.modulePayload.param0.name = "INT-SEL-1-07" 
$aciAccessPortToIntProfInt07.modulePayload.param0.description = "Interface Selector e1/7"
$aciAccessPortToIntProfInt07.modulePayload.param0.interfaceIDs = "1/7"
$aciAccessPortToIntProfInt07.modulePayload.param0.interfacePolicyGrp = ($accounts.ACI.name + "@" + $aciIntPolGroupInt07.modulePayload.param0.name + "@uni/infra/funcprof/accbundle-" + $aciIntPolGroupInt07.modulePayload.param0.name)

$aciAccessPortToIntProfInt23.modulePayload.param0.interfaceProfile = ($accounts.ACI.name + "@" + $aciIntProfileInt23.modulePayload.param0.name)
$aciAccessPortToIntProfInt23.modulePayload.param0.name = "INT-SEL-1-23" 
$aciAccessPortToIntProfInt23.modulePayload.param0.description = "Interface Selector e1/23"
$aciAccessPortToIntProfInt23.modulePayload.param0.interfaceIDs = "1/23"
$aciAccessPortToIntProfInt23.modulePayload.param0.interfacePolicyGrp = ($accounts.ACI.name + "@" + $aciIntPolGroupInt23.modulePayload.param0.name + "@uni/infra/funcprof/accbundle-" + $aciIntPolGroupInt23.modulePayload.param0.name)

$aciAccessPortToIntProfInt24.modulePayload.param0.interfaceProfile = ($accounts.ACI.name + "@" + $aciIntProfileInt24.modulePayload.param0.name)
$aciAccessPortToIntProfInt24.modulePayload.param0.name = "INT-SEL-1-24" 
$aciAccessPortToIntProfInt24.modulePayload.param0.description = "Interface Selector e1/24"
$aciAccessPortToIntProfInt24.modulePayload.param0.interfaceIDs = "1/24"
$aciAccessPortToIntProfInt24.modulePayload.param0.interfacePolicyGrp = ($accounts.ACI.name + "@" + $aciIntPolGroupInt24.modulePayload.param0.name + "@uni/infra/funcprof/accbundle-" + $aciIntPolGroupInt24.modulePayload.param0.name)

$aciAccessPortToIntProfInt47.modulePayload.param0.interfaceProfile = ($accounts.ACI.name + "@" + $aciIntProfileInt47.modulePayload.param0.name)
$aciAccessPortToIntProfInt47.modulePayload.param0.name = "INT-SEL-1-47" 
$aciAccessPortToIntProfInt47.modulePayload.param0.description = "Interface Selector e1/47"
$aciAccessPortToIntProfInt47.modulePayload.param0.interfaceIDs = "1/47"
$aciAccessPortToIntProfInt47.modulePayload.param0.interfacePolicyGrp = ($accounts.ACI.name + "@" + $aciIntPolGroupInt47.modulePayload.param0.name + "@uni/infra/funcprof/accbundle-" + $aciIntPolGroupInt47.modulePayload.param0.name)

$aciAccessPortToIntProfInt48.modulePayload.param0.interfaceProfile = ($accounts.ACI.name + "@" + $aciIntProfileInt48.modulePayload.param0.name)
$aciAccessPortToIntProfInt48.modulePayload.param0.name = "INT-SEL-1-48" 
$aciAccessPortToIntProfInt48.modulePayload.param0.description = "Interface Selector e1/48"
$aciAccessPortToIntProfInt48.modulePayload.param0.interfaceIDs = "1/48"
$aciAccessPortToIntProfInt48.modulePayload.param0.interfacePolicyGrp = ($accounts.ACI.name + "@" + $aciIntPolGroupInt48.modulePayload.param0.name + "@uni/infra/funcprof/accbundle-" + $aciIntPolGroupInt48.modulePayload.param0.name)

if($deployACI) {
    Call-UCSDAPI $aciAccessPortToIntProfInt07
    Call-UCSDAPI $aciAccessPortToIntProfInt23
    Call-UCSDAPI $aciAccessPortToIntProfInt24
    Call-UCSDAPI $aciAccessPortToIntProfInt47
    Call-UCSDAPI $aciAccessPortToIntProfInt48
}

<# ACI Create VPC Explicit Protection Group #>
$aciVPCExpProtGrp01 = Create-UCSDModule $modulePath "createVPCExplicitProtectionGroupsConfig"

$aciVPCExpProtGrp01.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciVPCExpProtGrp01.modulePayload.param0.name = "VPC-PROT-GRP-01"
$aciVPCExpProtGrp01.modulePayload.param0.id = "1"
$aciVPCExpProtGrp01.modulePayload.param0.vpcDomainPolicy = ($accounts.ACI.name + "@default")

<# Update this to read leaves from: /cloupia/api-v2/ApicFabricLeafNodeIdentity #>
#$aciVPCExpProtGrp01.modulePayload.param0.switchOne
#$aciVPCExpProtGrp01.modulePayload.param0.switchTwo

if($deployACI) {
    Call-UCSDAPI $aciVPCExpProtGrp01
}

<# ACI Create Switch Profile #>
$aciSwitchProfileInt07 = Create-UCSDModule $modulePath "createSwitchProfileConfig"
$aciSwitchProfileInt23 = Create-UCSDModule $modulePath "createSwitchProfileConfig"
$aciSwitchProfileInt24 = Create-UCSDModule $modulePath "createSwitchProfileConfig"
$aciSwitchProfileInt47 = Create-UCSDModule $modulePath "createSwitchProfileConfig"
$aciSwitchProfileInt48 = Create-UCSDModule $modulePath "createSwitchProfileConfig"

$aciSwitchProfileInt07.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciSwitchProfileInt07.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-07"
$aciSwitchProfileInt07.modulePayload.param0.description = "Cisco Live Switch Profile e1/7"

$aciSwitchProfileInt23.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciSwitchProfileInt23.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-23"
$aciSwitchProfileInt23.modulePayload.param0.description = "Cisco Live Switch Profile e1/23"

$aciSwitchProfileInt24.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciSwitchProfileInt24.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-24"
$aciSwitchProfileInt24.modulePayload.param0.description = "Cisco Live Switch Profile e1/24"

$aciSwitchProfileInt47.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciSwitchProfileInt47.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-47"
$aciSwitchProfileInt47.modulePayload.param0.description = "Cisco Live Switch Profile e1/47"

$aciSwitchProfileInt48.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciSwitchProfileInt48.modulePayload.param0.switchProfileName = "CLUS-SWITCH-PROF-48"
$aciSwitchProfileInt48.modulePayload.param0.description = "Cisco Live Switch Profile e1/48"

if($deployACI) {
    Call-UCSDAPI $aciSwitchProfileInt07
    Call-UCSDAPI $aciSwitchProfileInt23
    Call-UCSDAPI $aciSwitchProfileInt24
    Call-UCSDAPI $aciSwitchProfileInt47
    Call-UCSDAPI $aciSwitchProfileInt48
}

<# ACI Associate Switches to Switch Profile #>
$aciSwitchesToProfileInt07 = Create-UCSDModule $modulePath "associateSwitchSelectorToSwitchProfileConfig"
$aciSwitchesToProfileInt23 = Create-UCSDModule $modulePath "associateSwitchSelectorToSwitchProfileConfig"
$aciSwitchesToProfileInt24 = Create-UCSDModule $modulePath "associateSwitchSelectorToSwitchProfileConfig"
$aciSwitchesToProfileInt47 = Create-UCSDModule $modulePath "associateSwitchSelectorToSwitchProfileConfig"
$aciSwitchesToProfileInt48 = Create-UCSDModule $modulePath "associateSwitchSelectorToSwitchProfileConfig"

$aciSwitchesToProfileInt07.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt07.modulePayload.param0.switchProfileName)
$aciSwitchesToProfileInt07.modulePayload.param0.name = "101-102"

$aciSwitchesToProfileInt23.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt23.modulePayload.param0.switchProfileName)
$aciSwitchesToProfileInt23.modulePayload.param0.name = "101-102"

$aciSwitchesToProfileInt24.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt24.modulePayload.param0.switchProfileName)
$aciSwitchesToProfileInt24.modulePayload.param0.name = "101-102"

$aciSwitchesToProfileInt47.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt47.modulePayload.param0.switchProfileName)
$aciSwitchesToProfileInt47.modulePayload.param0.name = "101-102"

$aciSwitchesToProfileInt48.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt48.modulePayload.param0.switchProfileName)
$aciSwitchesToProfileInt48.modulePayload.param0.name = "101-102"

<# Update this to read leaves from: /cloupia/api-v2/ApicFabricLeafNodeIdentity #>
#$aciSwitchesToProfile.modulePayload.param0.leave = 

if($deployACI) {
    Call-UCSDAPI $aciSwitchesToProfileInt07
    Call-UCSDAPI $aciSwitchesToProfileInt23
    Call-UCSDAPI $aciSwitchesToProfileInt24
    Call-UCSDAPI $aciSwitchesToProfileInt47
    Call-UCSDAPI $aciSwitchesToProfileInt48
}

<# ACI Associate Interfaces to Switch Profile #>
$aciIntProfToSwitchProfInt07 = Create-UCSDModule $modulePath "associateInterfaceSelectorProfileToSwitchProfileConfig"
$aciIntProfToSwitchProfInt23 = Create-UCSDModule $modulePath "associateInterfaceSelectorProfileToSwitchProfileConfig"
$aciIntProfToSwitchProfInt24 = Create-UCSDModule $modulePath "associateInterfaceSelectorProfileToSwitchProfileConfig"
$aciIntProfToSwitchProfInt47 = Create-UCSDModule $modulePath "associateInterfaceSelectorProfileToSwitchProfileConfig"
$aciIntProfToSwitchProfInt48 = Create-UCSDModule $modulePath "associateInterfaceSelectorProfileToSwitchProfileConfig"

$aciIntProfToSwitchProfInt07.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt07.modulePayload.param0.switchProfileName)
$aciIntProfToSwitchProfInt07.modulePayload.param0.interfaceSelPfName = ($accounts.ACI.name + "@" + $aciIntProfileInt07.modulePayload.param0.name)

$aciIntProfToSwitchProfInt23.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt23.modulePayload.param0.switchProfileName)
$aciIntProfToSwitchProfInt23.modulePayload.param0.interfaceSelPfName = ($accounts.ACI.name + "@" + $aciIntProfileInt23.modulePayload.param0.name)

$aciIntProfToSwitchProfInt24.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt24.modulePayload.param0.switchProfileName)
$aciIntProfToSwitchProfInt24.modulePayload.param0.interfaceSelPfName = ($accounts.ACI.name + "@" + $aciIntProfileInt24.modulePayload.param0.name)

$aciIntProfToSwitchProfInt47.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt47.modulePayload.param0.switchProfileName)
$aciIntProfToSwitchProfInt47.modulePayload.param0.interfaceSelPfName = ($accounts.ACI.name + "@" + $aciIntProfileInt47.modulePayload.param0.name)

$aciIntProfToSwitchProfInt48.modulePayload.param0.switchProfile = ($accounts.ACI.name + "@" + $aciSwitchProfileInt48.modulePayload.param0.switchProfileName)
$aciIntProfToSwitchProfInt48.modulePayload.param0.interfaceSelPfName = ($accounts.ACI.name + "@" + $aciIntProfileInt48.modulePayload.param0.name)

if($deployACI) {
    Call-UCSDAPI $aciIntProfToSwitchProfInt07
    Call-UCSDAPI $aciIntProfToSwitchProfInt23
    Call-UCSDAPI $aciIntProfToSwitchProfInt24
    Call-UCSDAPI $aciIntProfToSwitchProfInt47
    Call-UCSDAPI $aciIntProfToSwitchProfInt48
}

<# ACI Create Tenant #>
$aciTenant = Create-UCSDModule $modulePath "createTenantConfig"

$aciTenant.modulePayload.param0.apicAccount = $accounts.ACI.name
$aciTenant.modulePayload.param0.name = "CiscoLive"
$aciTenant.modulePayload.param0.description = "Cisco Live Tenant"
$aciTenant.modulePayload.param0.monitoringPolicy = ($accounts.ACI.name + "@common@default")

if($deployACI) {
    Call-UCSDAPI $aciTenant
}

<# ACI Create VRF #>
$aciVRF = Create-UCSDModule $modulePath "createPrivateNetworkConfig"

$aciVRF.modulePayload.param0.tenantName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name)
$aciVRF.modulePayload.param0.privateNetwork = "CLUS-VRF"
$aciVRF.modulePayload.param0.polEnforce = "unenforced"
$aciVRF.modulePayload.param0.privateNetworkDescription = "Cisco Live VRF"
$aciVRF.modulePayload.param0.bgpTimers = ($accounts.ACI.name + "@common@default")
$aciVRF.modulePayload.param0.ospfTimers = ($accounts.ACI.name + "@common@default")
$aciVRF.modulePayload.param0.monPolicy = ($accounts.ACI.name + "@common@default")

if($deployACI) {
    Call-UCSDAPI $aciVRF
}

<# ACI Create Bridge Domain #>
$aciBDVlan01 = Create-UCSDModule $modulePath "createTenantBridgeDomain"
$aciBDVlan02 = Create-UCSDModule $modulePath "createTenantBridgeDomain"
$aciBDVlan10 = Create-UCSDModule $modulePath "createTenantBridgeDomain"

$aciBDVlan01.modulePayload.param0.tenantName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name)
$aciBDVlan01.modulePayload.param0.name = "CLUS-BD-VLAN01"
$aciBDVlan01.modulePayload.param0.description = "Cisco Live Bridge Domain Vlan 1"
$aciBDVlan01.modulePayload.param0.network = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciVRF.modulePayload.param0.privateNetwork)
$aciBDVlan01.modulePayload.param0.forwarding = "Custom"
$aciBDVlan01.modulePayload.param0.l2Unicast = "Flood"
$aciBDVlan01.modulePayload.param0.l2Multicast = "Flood"
$aciBDVlan01.modulePayload.param0.arpFlooding = "true"
$aciBDVlan01.modulePayload.param0.unicastRouting = "true"
$aciBDVlan01.modulePayload.param0.monPolicy = ($accounts.ACI.name + "@common@default")

$aciBDVlan02.modulePayload.param0.tenantName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name)
$aciBDVlan02.modulePayload.param0.name = "CLUS-BD-VLAN02"
$aciBDVlan02.modulePayload.param0.description = "Cisco Live Bridge Domain Vlan 2"
$aciBDVlan02.modulePayload.param0.network = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciVRF.modulePayload.param0.privateNetwork)
$aciBDVlan02.modulePayload.param0.forwarding = "Optimize"
$aciBDVlan02.modulePayload.param0.l2Unicast = "Flood"
$aciBDVlan02.modulePayload.param0.l2Multicast = "Flood"
$aciBDVlan02.modulePayload.param0.arpFlooding = "false"
$aciBDVlan02.modulePayload.param0.unicastRouting = "true"
$aciBDVlan02.modulePayload.param0.monPolicy = ($accounts.ACI.name + "@common@default")

$aciBDVlan10.modulePayload.param0.tenantName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name)
$aciBDVlan10.modulePayload.param0.name = "CLUS-BD-VLAN10"
$aciBDVlan10.modulePayload.param0.description = "Cisco Live Bridge Domain Vlan 10"
$aciBDVlan10.modulePayload.param0.network = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciVRF.modulePayload.param0.privateNetwork)
$aciBDVlan10.modulePayload.param0.forwarding = "Optimize"
$aciBDVlan10.modulePayload.param0.l2Unicast = "Flood"
$aciBDVlan10.modulePayload.param0.l2Multicast = "Flood"
$aciBDVlan10.modulePayload.param0.arpFlooding = "false"
$aciBDVlan10.modulePayload.param0.unicastRouting = "true"
$aciBDVlan10.modulePayload.param0.monPolicy = ($accounts.ACI.name + "@common@default")

if($deployACI) {
    Call-UCSDAPI $aciBDVlan01
    Call-UCSDAPI $aciBDVlan02
    Call-UCSDAPI $aciBDVlan10
}

<# ACI Create Subnet #>
$aciSubnetVlan01 = Create-UCSDModule $modulePath "createSubnetToBridgeNetworkConfig"
$aciSubnetVlan02 = Create-UCSDModule $modulePath "createSubnetToBridgeNetworkConfig"
$aciSubnetVlan10 = Create-UCSDModule $modulePath "createSubnetToBridgeNetworkConfig"

$aciSubnetVlan01.modulePayload.param0.bridgeDomain = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciBDVlan01.modulePayload.param0.name)
$aciSubnetVlan01.modulePayload.param0.ipAddress = "10.0.0.3"
$aciSubnetVlan01.modulePayload.param0.mask = "24"
$aciSubnetVlan01.modulePayload.param0.sharedSubnet = "false"
$aciSubnetVlan01.modulePayload.param0.publicSubnet = "false"
$aciSubnetVlan01.modulePayload.param0.privateSubnet = "true"
$aciSubnetVlan01.modulePayload.param0.description = "Cisco Live 10.0.0.X Subnet"

$aciSubnetVlan02.modulePayload.param0.bridgeDomain = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciBDVlan02.modulePayload.param0.name)
$aciSubnetVlan02.modulePayload.param0.ipAddress = "10.2.0.1"
$aciSubnetVlan02.modulePayload.param0.mask = "24"
$aciSubnetVlan02.modulePayload.param0.sharedSubnet = "false"
$aciSubnetVlan02.modulePayload.param0.publicSubnet = "false"
$aciSubnetVlan02.modulePayload.param0.privateSubnet = "true"
$aciSubnetVlan02.modulePayload.param0.description = "Cisco Live 10.2.0.X Subnet"

$aciSubnetVlan10.modulePayload.param0.bridgeDomain = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciBDVlan10.modulePayload.param0.name)
$aciSubnetVlan10.modulePayload.param0.ipAddress = "10.10.0.1"
$aciSubnetVlan10.modulePayload.param0.mask = "24"
$aciSubnetVlan10.modulePayload.param0.sharedSubnet = "false"
$aciSubnetVlan10.modulePayload.param0.publicSubnet = "false"
$aciSubnetVlan10.modulePayload.param0.privateSubnet = "true"
$aciSubnetVlan10.modulePayload.param0.description = "Cisco Live 10.10.0.X Subnet"

if($deployACI) {
    Call-UCSDAPI $aciSubnetVlan01
    Call-UCSDAPI $aciSubnetVlan02
    Call-UCSDAPI $aciSubnetVlan10
}

<# ACI Create Application Profile #>
$aciAppProfile = Create-UCSDModule $modulePath "createTenantApplicationProfileConfig"

$aciAppProfile.modulePayload.param0.tenantName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name)
$aciAppProfile.modulePayload.param0.applnProfileName = "CLUS-APP"
$aciAppProfile.modulePayload.param0.description = "Cisco Live Application"
$aciAppProfile.modulePayload.param0.monitorPolicy = ($accounts.ACI.name + "@common@default")

if($deployACI) {
    Call-UCSDAPI $aciAppProfile
}

<# ACI Create Endpoint Group #>
$aciEPGVlan01 = Create-UCSDModule $modulePath "createEPGConfig"
$aciEPGVlan02 = Create-UCSDModule $modulePath "createEPGConfig"
$aciEPGVlan10 = Create-UCSDModule $modulePath "createEPGConfig"

$aciEPGVlan01.modulePayload.param0.approfName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName)
$aciEPGVlan01.modulePayload.param0.epgName = "CLUS-VLAN-01"
$aciEPGVlan01.modulePayload.param0.epgDescription = "Cisco Live EPG Vlan 1"
$aciEPGVlan01.modulePayload.param0.customQos = ($accounts.ACI.name + "@common@default")
$aciEPGVlan01.modulePayload.param0.bridgeDomain = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciBDVlan01.modulePayload.param0.name)
$aciEPGVlan01.modulePayload.param0.monPolicy= ($accounts.ACI.name + "@common@default")

$aciEPGVlan02.modulePayload.param0.approfName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName)
$aciEPGVlan02.modulePayload.param0.epgName = "CLUS-VLAN-02"
$aciEPGVlan02.modulePayload.param0.epgDescription = "Cisco Live EPG Vlan 2"
$aciEPGVlan02.modulePayload.param0.customQos = ($accounts.ACI.name + "@common@default")
$aciEPGVlan02.modulePayload.param0.bridgeDomain = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciBDVlan02.modulePayload.param0.name)
$aciEPGVlan02.modulePayload.param0.monPolicy= ($accounts.ACI.name + "@common@default")

$aciEPGVlan10.modulePayload.param0.approfName = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName)
$aciEPGVlan10.modulePayload.param0.epgName = "CLUS-VLAN-10"
$aciEPGVlan10.modulePayload.param0.epgDescription = "Cisco Live EPG Vlan 10"
$aciEPGVlan10.modulePayload.param0.customQos = ($accounts.ACI.name + "@common@default")
$aciEPGVlan10.modulePayload.param0.bridgeDomain = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciBDVlan10.modulePayload.param0.name)
$aciEPGVlan10.modulePayload.param0.monPolicy= ($accounts.ACI.name + "@common@default")

if($deployACI) {
    Call-UCSDAPI $aciEPGVlan01
    Call-UCSDAPI $aciEPGVlan02
    Call-UCSDAPI $aciEPGVlan10
}

<# ACI Attach Physical Domain to EPG #>
$aciPhysDomToEPGVlan01 = Create-UCSDModule $modulePath "addDomainToEPGConfig"
$aciPhysDomToEPGVlan02 = Create-UCSDModule $modulePath "addDomainToEPGConfig"
$aciPhysDomToEPGVlan10 = Create-UCSDModule $modulePath "addDomainToEPGConfig"

$aciPhysDomToEPGVlan01.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan01.modulePayload.param0.epgName)
$aciPhysDomToEPGVlan01.modulePayload.param0.domainProfile = ($accounts.ACI.name + "@Physical Domain@" + $aciPhysDom.modulePayload.param0.name)
$aciPhysDomToEPGVlan01.modulePayload.param0.deployImmediacy = "On Demand"
$aciPhysDomToEPGVlan01.modulePayload.param0.resolutionImmediacy = "On Demand"

$aciPhysDomToEPGVlan02.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan02.modulePayload.param0.epgName)
$aciPhysDomToEPGVlan02.modulePayload.param0.domainProfile = ($accounts.ACI.name + "@Physical Domain@" + $aciPhysDom.modulePayload.param0.name)
$aciPhysDomToEPGVlan02.modulePayload.param0.deployImmediacy = "On Demand"
$aciPhysDomToEPGVlan02.modulePayload.param0.resolutionImmediacy = "On Demand"

$aciPhysDomToEPGVlan10.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan10.modulePayload.param0.epgName)
$aciPhysDomToEPGVlan10.modulePayload.param0.domainProfile = ($accounts.ACI.name + "@Physical Domain@" + $aciPhysDom.modulePayload.param0.name)
$aciPhysDomToEPGVlan10.modulePayload.param0.deployImmediacy = "On Demand"
$aciPhysDomToEPGVlan10.modulePayload.param0.resolutionImmediacy = "On Demand"

if($deployACI) {
    Call-UCSDAPI $aciPhysDomToEPGVlan01
    Call-UCSDAPI $aciPhysDomToEPGVlan02
    Call-UCSDAPI $aciPhysDomToEPGVlan10
}

<# ACI Attach Leaf Policy to EPG #>
<# Vlan 1 Variables #>
$aciLeafPolToEPGVlan01Port07 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan01Port23 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan01Port24 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan01Port47 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"

<# Vlan 2 Variables #>
$aciLeafPolToEPGVlan02Port07 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan02Port23 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan02Port24 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"

<# Vlan 10 Variables #>
$aciLeafPolToEPGVlan10Port07 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan10Port23 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"
$aciLeafPolToEPGVlan10Port24 = Create-UCSDModule $modulePath "addStaticPathToEPGConfig"

<# Vlan 1 VPC Mappings #>

$aciLeafPolToEPGVlan01Port07.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan01.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan01Port07.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan01Port07.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt07.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan01Port07.modulePayload.param0.encapsulation = "vlan-1"
$aciLeafPolToEPGVlan01Port07.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan01Port07.modulePayload.param0.mode = "802.1P Tagged"

$aciLeafPolToEPGVlan01Port23.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan01.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan01Port23.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan01Port23.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt23.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan01Port23.modulePayload.param0.encapsulation = "vlan-1"
$aciLeafPolToEPGVlan01Port23.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan01Port23.modulePayload.param0.mode = "802.1P Tagged"

$aciLeafPolToEPGVlan01Port24.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan01.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan01Port24.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan01Port24.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt24.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan01Port24.modulePayload.param0.encapsulation = "vlan-1"
$aciLeafPolToEPGVlan01Port24.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan01Port24.modulePayload.param0.mode = "802.1P Tagged"

$aciLeafPolToEPGVlan01Port47.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan01.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan01Port47.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan01Port47.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt47.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan01Port47.modulePayload.param0.encapsulation = "vlan-1"
$aciLeafPolToEPGVlan01Port47.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan01Port47.modulePayload.param0.mode = "802.1P Tagged"

<# Vlan 2 VPC Mappings #>

$aciLeafPolToEPGVlan02Port07.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan02.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan02Port07.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan02Port07.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt07.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan02Port07.modulePayload.param0.encapsulation = "vlan-2"
$aciLeafPolToEPGVlan02Port07.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan02Port07.modulePayload.param0.mode = "Tagged"

$aciLeafPolToEPGVlan02Port23.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan02.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan02Port23.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan02Port23.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt23.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan02Port23.modulePayload.param0.encapsulation = "vlan-2"
$aciLeafPolToEPGVlan02Port23.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan02Port23.modulePayload.param0.mode = "Tagged"

$aciLeafPolToEPGVlan02Port24.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan02.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan02Port24.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan02Port24.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt24.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan02Port24.modulePayload.param0.encapsulation = "vlan-2"
$aciLeafPolToEPGVlan02Port24.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan02Port24.modulePayload.param0.mode = "Tagged"

<# Vlan 10 VPC Mappings #>

$aciLeafPolToEPGVlan10Port07.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan10.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan10Port07.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan10Port07.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt07.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan10Port07.modulePayload.param0.encapsulation = "vlan-10"
$aciLeafPolToEPGVlan10Port07.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan10Port07.modulePayload.param0.mode = "Tagged"

$aciLeafPolToEPGVlan10Port23.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan10.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan10Port23.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan10Port23.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt23.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan10Port23.modulePayload.param0.encapsulation = "vlan-10"
$aciLeafPolToEPGVlan10Port23.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan10Port23.modulePayload.param0.mode = "Tagged"

$aciLeafPolToEPGVlan10Port24.modulePayload.param0.epg = ($accounts.ACI.name + "@" + $aciTenant.modulePayload.param0.name + "@" + $aciAppProfile.modulePayload.param0.applnProfileName + "@" + $aciEPGVlan10.modulePayload.param0.epgName)
$aciLeafPolToEPGVlan10Port24.modulePayload.param0.pathType = "Virtual Port Channel"
<# Update this to dynamically pull leaves #>
$aciLeafPolToEPGVlan10Port24.modulePayload.param0.vpcPath = ("topology/pod-1/protpaths-101-102/pathep-[" + $aciIntPolGroupInt24.modulePayload.param0.name + "]")
$aciLeafPolToEPGVlan10Port24.modulePayload.param0.encapsulation = "vlan-10"
$aciLeafPolToEPGVlan10Port24.modulePayload.param0.deploymentImmediacy = "Immediate"
$aciLeafPolToEPGVlan10Port24.modulePayload.param0.mode = "Tagged"


if($deployACI) {
    <# Vlan 1 Execute#>
    Call-UCSDAPI $aciLeafPolToEPGVlan01Port07
    Call-UCSDAPI $aciLeafPolToEPGVlan01Port23
    Call-UCSDAPI $aciLeafPolToEPGVlan01Port24
    Call-UCSDAPI $aciLeafPolToEPGVlan01Port47

    <# Vlan 2 Execute #>
    Call-UCSDAPI $aciLeafPolToEPGVlan02Port07
    Call-UCSDAPI $aciLeafPolToEPGVlan02Port23
    Call-UCSDAPI $aciLeafPolToEPGVlan02Port24

    <# Vlan 10 Execute #>
    Call-UCSDAPI $aciLeafPolToEPGVlan10Port07
    Call-UCSDAPI $aciLeafPolToEPGVlan10Port23
    Call-UCSDAPI $aciLeafPolToEPGVlan10Port24
}

<# ACI Create Contract #>
$aciContract = Create-UCSDModule $modulePath "createContractConfig"

if($deployACI) {
    #Call-UCSDAPI $aciContract
}

<# ACI Create Contract Subject #>
$aciContractSubj = Create-UCSDModule $modulePath "createContractSubjectConfig"

if($deployACI) {
    #Call-UCSDAPI $aciContractSubj
}

<# ACI Create Subject Filter #>
$aciSubjFilter = Create-UCSDModule $modulePath "createTenantFilterConfig"

if($deployACI) {
    #Call-UCSDAPI $aciSubjFilter
}

<# ACI Create Filter Rule #>
$aciFilterRule = Create-UCSDModule $modulePath "createTenantFilterRuleConfig"

if($deployACI) {
    #Call-UCSDAPI $aciFilterRule
}

<# ACI Create Add Filter To Contract #>
$aciFilterToContract = Create-UCSDModule $modulePath "addFilterToContractSubjectConfig"

if($deployACI) {
    #Call-UCSDAPI $aciFilterToContract
}

<# ACI Create Add Contract To EPG #>
$aciContractToEPG = Create-UCSDModule $modulePath "addContractToEPGConfig"

if($deployACI) {
    #Call-UCSDAPI $aciContractToEPG
}

<#########################>
<#                       #>
<# Configure MDS Devices #>
<#                       #>
<#########################>

<# MDS Enable Features #>
$mdsFeaturesA = Create-UCSDModule $modulePath "configureFeature"
#$mdsFeaturesA = Create-UCSDModule $modulePath "configureFeature"

if($deployMDS) {
    #Call-UCSDAPI $mdsFeaturesA
    #Call-UCSDAPI $mdsFeaturesB
}

<# MDS Create VSANs #>
$mdsVSANA = Create-UCSDModule $modulePath "createVSANConfig"
#$mdsVSANB = Create-UCSDModule $modulePath "createVSANConfig"

if($deployMDS) {
    #Call-UCSDAPI $mdsVSANA
    #Call-UCSDAPI $mdsVSANB
}

<# MDS Attach VSAN to Ports #>
$mdsVSANPortA = Create-UCSDModule $modulePath "fcPortVSANConfig"
#$mdsVSANPortB = Create-UCSDModule $modulePath "fcPortVSANConfig"

if($deployMDS) {
    #Call-UCSDAPI $mdsVSANPortA
    #Call-UCSDAPI $mdsVSANPortB
}

<# MDS Enable Ports #>
$mdsPortConfigA = Create-UCSDModule $modulePath "configurePort"
#$mdsPortConfigB = Create-UCSDModule $modulePath "configurePort"

if($deployMDS) {
    #Call-UCSDAPI $mdsPortConfigA
    #Call-UCSDAPI $mdsPortConfigB
}

<# MDS Create SAN Zone #>
$mdsSANZoneA = Create-UCSDModule $modulePath "createSanZone"
#$mdsSANZoneB = Create-UCSDModule $modulePath "createSanZone"

if($deployMDS) {
    #Call-UCSDAPI $mdsSANZoneA
    #Call-UCSDAPI $mdsSANZoneB
}

<# MDS Add Zone Members #>
$mdsZoneMemberA = Create-UCSDModule $modulePath "addMemberToSANZoneConfig"
#$mdsZoneMemberB = Create-UCSDModule $modulePath "addMemberToSANZoneConfig"

if($deployMDS) {
    #Call-UCSDAPI $mdsZoneMemberA
    #Call-UCSDAPI $mdsZoneMemberB
}

<# MDS Create ZoneSets #>
$mdsZoneSetA = Create-UCSDModule $modulePath "createSanZoneSet"
#$mdsZoneSetB = Create-UCSDModule $modulePath "createSanZoneSet"

if($deployMDS) {
    #Call-UCSDAPI $mdsZoneSetA
    #Call-UCSDAPI $mdsZoneSetB
}

<# MDS Add Zone to ZoneSets #>
$mdsZoneToZoneSetA = Create-UCSDModule $modulePath "addSANZoneToSetConfig"
#$mdsZoneToZoneSetB = Create-UCSDModule $modulePath "addSANZoneToSetConfig"

if($deployMDS) {
    #Call-UCSDAPI $mdsZoneToZoneSetA
    #Call-UCSDAPI $mdsZoneToZoneSetB
}

<# MDS ActivateZoneSets #>
$mdsActivateZoneSetA = Create-UCSDModule $modulePath "activateSANZoneSetConfig"
#$mdsActivateZoneSetB = Create-UCSDModule $modulePath "activateSANZoneSetConfig"

if($deployMDS) {
    #Call-UCSDAPI $mdsActivateZoneSetA
    #Call-UCSDAPI $mdsActivateZoneSetB
}
