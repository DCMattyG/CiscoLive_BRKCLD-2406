"""
Copyright 2008-2011 VMware, Inc.  All rights reserved. -- VMware Confidential

VMware OVFTool component installer.
"""

DEST = LIBDIR/'vmware-ovftool'

class OVFTool(Installer):
   """
   This class contains the installer logic for the OVFTool component.
   """
   def InitializeInstall(self, old, new, upgrade):
       self.AddTarget('File', '*', DEST)
       self.AddTarget('Link', DEST/'ovftool', BINDIR/'ovftool')

       self.SetPermission(DEST/'ovftool', BINARY)
       self.SetPermission(DEST/'ovftool.bin', BINARY)
