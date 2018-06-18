======================================================================
                 VMWARE vCenter Server Appliance 6.5
======================================================================

Copyright (c) 1998-2017 VMware, Inc. All rights reserved.

This product is protected by U.S. and international copyright and
intellectual property laws. VMware products are covered by one or more
patents listed at http://www.vmware.com/go/patents. VMware, the VMware
"boxes" logo and design, Virtual SMP and vMotion are registered
trademarks or trademarks of VMware, Inc. in the United States and/or
other jurisdictions. All other marks and names mentioned herein may be
trademarks of their respective companies.

This document provides information about the files stored in the
following packages:

VMware-VCSA-all-x.y.z-abcdefg.iso (DVD image).

NOTE: The package allows you to install the following components:

    - VMware vCenter Server Appliance

---------------------------
OTHER FILES AND DIRECTORIES
---------------------------

/vcsa                   vCenter Server Appliance data files

/vcsa-ui-installer      vCenter Server Appliance installer

/vcsa-cli-installer     vCenter Server Appliance command-line installer

/migration-assistant    vCenter Server Migration Assistant


============
INSTALLATION
============

This section contains basic information on how to install, upgrade, or
migrate the vCenter Server Appliance either by using the UI installer
or by using the command line installer.

You can deploy the vCenter Server Appliance (VCSA) on a host running
ESXi 5.5 and later by using:

a) The UI based installer
b) The command-line installer
c) Migration from vCenter Server Windows to Appliance

During deployment both methods collect user inputs, run validations,
and deploy the vCenter Server Appliance to an ESXi host.

------------------
UI Based Installer
------------------

This installer systematically guides you through the process. You can
run this installer on Windows, Linux, or Mac.

*** Windows ***

Open Windows Explorer and in the vCenter Server Appliance installation
directory, navigate to the 'vcsa-ui-installer\win32' folder.

1) Double-click on the 'installer.exe' file, or
2) From the command line, type 'installer'.

You will be guided through the deployment process.

*** Mac ***

On Mac, the 'vcsa-deploy' file is in the 'vcsa-ui-installer/mac' folder.

1) Ctrl+click on the 'Installer' app, or right-click on it, and select
   Open from the menu. If you see a warning pop-up about 'unidentified
   developer', Click Open, or

2) From the terminal, type 'open Installer.app'.

*** Linux ***

On Linux, the 'vcsa-deploy' file is in the 'vcsa-ui-installer/lin64'
folder.

1) Double-click on the 'installer' file, or
2) From the terminal, type "./installer".

----------------------
Command-Line Installer
----------------------

You can run the command-line installation on Windows, Linux, or Mac.

*** Windows ***

Open Windows Explorer and in the vCenter Server Appliance installation
directory, navigate to the 'vcsa-cli-installer\templates' folder. Open
the 'vcsa-cli-installer\templates' directory. You can see a few
example files for common setups, along with the file containing a full
list of the inputs described above (that is the full_conf.json file).

You can create new .json files or customize the existing templates
with all the inputs that fit your needs. Once you have a template file
that you want to use to deploy the vCenter Server Appliance, in the
command line terminal, navigate to the win32 folder inside
'vcsa-cli-installer' and run 'vcsa-deploy {install|upgrade|migrate}
..\templates\{name of template json file}.json'. This command starts
the installation and you can see user-friendly status messages
notifying you about the progress and letting you know if anything
has failed.

*** Mac/Linux ***

The process is very similar to the process for Windows. Use the
template files the same way as you do on Windows.

The only difference is that the 'vcsa-deploy' file is in a different
folder:

On Mac, the 'vcsa-deploy' file is in 'vcsa-cli-installer/mac' .
On Linux, the 'vcsa-deploy' file is in 'vcsa-cli-installer/lin64' .

--------------------------------------------------
Migration From vCenter Server Windows To Appliance
--------------------------------------------------

VMware Migration Assistant helps simplify the migration process from
vCenter Server running on Windows to VCSA. You can use either the
UI-based installer to perform migration or the command-line installer
for unattended migration.

Copy the Migration Assistant deliverable to the vCenter Server Windows
system and then double-click on the executable and provide the
required inputs. Then use the UI-based or the command-line installer
to perform the migration.

For MxN deployment, Platform Services Controllers have to be migrated
before the vCenter Server migration.

For more information and instructions on any of these tools, see the
vSphere Installation and Setup documentation.
