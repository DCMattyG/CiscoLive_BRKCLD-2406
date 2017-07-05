VMware vCSA Command Line Interface Installer
Version 6.5.0
2016


----------------------------------------
Contents:
----------------------------------------
I.   Overview
II.  Changes Since 6.0
III. Brief Description of Options
IV.  JSON Template Files
V.   Help


----------------------------------------
I. Overview
----------------------------------------
This utility provides a command line interface for the following:
1. Installation of vCenter Server Appliance (vCSA) 6.5.0.
2. Upgrade of vCenter Server Appliance (vCSA) 5.5 and 6.0 to 6.5.0.
3. Migration of Windows vCenter installations 5.5 and 6.0 to vCSA 6.5.0.


----------------------------------------
II. Changes Since 6.0
----------------------------------------
1. Added static IPv6 upgrade support.

2. Windows to vCSA Migration:
   vCenter 5.5/6.0 on a Windows VM can be automatically migrated to vCSA.
   In the JSON template (details below), provide the Windows vCenter information in
   the vc.win fields. The command line installer will deploy the Migration
   Assistant on the Windows system, launch it, and run the migration process.

3. Pre-upgrade Planning:
   When upgrading, there is a --precheck-only option which will display estimates
   for the:
     Total disk space required for the target VM.
     Database disk space requirements.

4. Data Migration Control:
   The installer provides control over what data to transfer during the upgrade.
   Options include core, all, or core_events_tasks.  Set this option in the
   new.vcsa section, user-options subsection, vcdb.migrateSet field.

5. Remote OVA File Support:
   The vCSA installation package (OVA file) may be available as a local file or
   be on a remote server.  If it is remote, specify the URL in the new.vcsa
   section, appliance subsection, image field.

6. Logging Improvements:
   WARNING, ERROR, CRITICAL, and TRACE messages are logged to stderr.  DEBUG and
   INFO messages are logged to stdout.

7. JSON template files:
   They have been restructured for clarity.
   Windows to vCSA migration templates have been added.
   The deployment.option field is now required.  See the template help for
   details.
   The ceip.enabled property has been added.  This allows you to choose whether
   to participate in the VMware Customer Experience Improvement Program.

8. Command line options:
   The --accept-eula parameter is required.
   The --acknowledge-ceip parameter is required if the JSON template file
   has ceip.enabled set to true.


----------------------------------------
III. Brief Description of Options
----------------------------------------
1. The command line tool is located in the vcsa-cli-installer directory.  Paths
   in this document are relative to this directory.  The executables are in the
   following locations:
     Linux, 64 bit:  lin64/vcsa-deploy
     Mac OS X:       mac/vcsa-deploy
     Windows:        win32/vcsa-deploy.exe

2. High level options include:
   -h, --help:                   Show help
   --version:                    Show the version
   --supported-deployment-sizes: Display all of the supported deployment options
                                 from the OVA in the default location. If the
                                 OVA package is not found, default values are
                                 displayed

3. To do more than view the help or version, issue a sub-command on the command
   line.  Sub-commands include:
     install:  Deploy vCSA to a remote host.
     upgrade:  Upgrade an existing vCSA.
     migrate:  Migrate an existing Windows installation of vCenter Server to a
               vCSA.

4. Each sub-command has its own help.  For example, this command will display
   the installation help:

     lin64/vcsa-deploy install --help

5. To install, upgrade, or migrate, include a sub-command, desired options, and
   the path to a JSON template file which you have edited to contain detailed
   settings.  (A discussion of the JSON file may be found in the next section.)
   For example, to perform basic template verification without installing:

     lin64/vcsa-deploy install --accept-eula --verify-only <JSON file path>


----------------------------------------
IV. JSON Template Files
----------------------------------------
1. Most of the parameters related to install, upgrade, and migrate are conveyed
   to the installer via a JSON file.  Sample JSON template files have been
   included with this release.  These sample templates only contain what are
   anticipated to be the most frequent options; a full list of the template
   options, including descriptions, may be seen by running a sub-command with
   the --template-help option.  For example:

     lin64/vcsa-deploy install --template-help

2. Sample JSON template files are located in the templates directory.  They are
   organized into install, migrate, and upgrade subdirectories.  Migration and
   upgrade templates are further organized according to the release of the
   system which is being upgraded or migrated:

     templates/
         install/
                Use these templates to install a 6.5 vCSA/PSC.

                embedded_vCSA_on_*.json: Platform Services Controller (PSC) and vCSA
                                         together on one system
                PSC_on_*.json:           Only a PSC
                vCSA_on_*.json:          Only a vCSA
                *_on_ESXi.json:          Install onto the ESXi host specified in the JSON
                                         file
                *_on_VC.json:            Install onto a host managed by the vCenter
                                         instance specified in the JSON file
         migrate/
             winvc5.5/
                 Use these templates to migrate a 5.5 Windows vc/SSO to a 6.5 vCSA/PSC.

                 embedded_win_vc_to_embedded_vCSA_on_*.json: Migrate a Windows VC to Platform Services Controller (PSC) and vCSA
                                                             together on one system
                 win_sso_to_lin_PSC_on_*.json:               Migrate a Windows SSO to Linux PSC
                 win_vc_to_vCSA_on_*.json:                   Migrate a Windows VC to a vCSA
                 *_on_ESXi.json:                             Install onto the ESXi host specified in the JSON
                                                             file
                 *_on_VC.json:                               Install onto a host managed by the vCenter
                                                             instance specified in the JSON file
             winvc6.0/
                 Use these templates to migrate a 6.0 Windows vc/PSC to a 6.5 vCSA/PSC.

                 embedded_win_vc_to_embedded_vCSA_on_*.json: Migrate a Windows VC to Platform Services Controller (PSC) and vCSA
                                                             together on one system
                 win_psc_to_lin_PSC_on_*.json:               Migrate a Windows PSC to Linux PSC
                 win_vc_to_vCSA_on_*.json:                   Migrate a Windows VC to a vCSA
                 *_on_ESXi.json:                             Install onto the ESXi host specified in the JSON
                                                             file
                 *_on_VC.json:                               Install onto a host managed by the vCenter
                                                             instance specified in the JSON file
         upgrade/
             vcsa5.5/
                 Use these templates to upgrade a 5.5 vCSA/PSC to a 6.5 vCSA/PSC.

                 embedded_vCSA_on_*.json: Platform Services Controller (PSC) and vCSA
                                          together on one system
                 PSC_on_*.json:           Only a PSC
                 vCSA_on_*.json:          Only a vCSA
                 *_on_ESXi.json:          Install onto the ESXi host specified in the JSON
                                          file
                 *_on_VC.json:            Install onto a host managed by the vCenter
                                          instance specified in the JSON file
             vcsa6.0/
                 Use these templates to upgrade a 6.0 vCSA/PSC to a 6.5 vCSA/PSC.

                 embedded_vCSA_on_*.json: Platform Services Controller (PSC) and vCSA
                                          together on one system
                 PSC_on_*.json:           Only a PSC
                 vCSA_on_*.json:          Only a vCSA
                 *_on_ESXi.json:          Install onto the ESXi host specified in the JSON
                                          file
                 *_on_VC.json:            Install onto a host managed by the vCenter
                                          instance specified in the JSON file

3. JSON configuration files must be saved in UTF-8 format.

4. To ensure the correct syntax of your JSON configuration file, use a JSON
   editor.

5. Note that PSC ("Single Sign-On") nodes must be upgraded before the vCenter
   nodes which point to them.

6. If a password property in the JSON file is not present, or if the password
   content is an empty string, the installer will present a prompt to enter the
   password on the command line.


----------------------------------------
V. Help
----------------------------------------
http://www.vmware.com/support.html
