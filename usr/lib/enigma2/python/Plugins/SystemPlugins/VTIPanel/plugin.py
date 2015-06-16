#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/plugin.py
from Screens.About import About
from Screens.ChannelSelection import *
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Menu import Menu, boundFunction
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.PluginBrowser import *
from Screens.Ipkg import Ipkg
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import HelpableActionMap, ActionMap, NumberActionMap
from Components.Button import Button
from Components.config import config, getConfigListEntry, configfile, ConfigSelection, ConfigSubsection, ConfigText, ConfigLocations, ConfigNothing, ConfigOnOff, ConfigPassword, NoSave
from Components.Console import Console as ComConsole
from Components.ConfigList import ConfigList
from Components.Harddisk import harddiskmanager
from Components.Ipkg import IpkgComponent
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Network import iNetwork
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.PluginList import *
from Components.SelectionList import SelectionList
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN, SCOPE_METADIR
from Tools.HardwareInfo import HardwareInfo
from Tools.LoadPixmap import LoadPixmap
from enigma import eConsoleAppContainer, eTimer, quitMainloop, RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, eListbox, gFont, getDesktop, ePicLoad
from skin import loadSkin
from cPickle import dump, load
from os import system, listdir, symlink, unlink, readlink, path as os_path, stat, mkdir, popen, makedirs, access, rename, remove, W_OK, R_OK, F_OK, chmod, walk, getcwd, chdir
from random import Random
from stat import ST_MTIME
from time import sleep, time
import string
import sys
from BackupRestore import BackupSelection, RestoreMenu, BackupScreen, RestoreScreen, RestoreMenuImage, getBackupPath, getBackupPathImage, getBackupFilename, BackupRestoreScreen
from bitrate import Bitrate
from ntpserver import SelectCountry, NTPManager
from PanelPassword import InputPanelPassword
from __init__ import _, loadPluginSkin
dirlist = ['/usr/LTEMU/', '/usr/script/', '/etc/init.d/']
searchlist = ['CAMINFO',
 'CAMNAME',
 'EMUNAME',
 'CAMD_NAME']
camstarter = '/etc/rcS.d/S98CamManager'
current_cam = '/etc/init.d/current_cam.sh'
swapstarter = '/etc/rcS.d/S98SwapFile'
swaplocations = ['/media/hdd',
 '/media/hdd1',
 '/media/hdd2',
 '/media/usb',
 '/media/usb1',
 '/media/usb2']
swapsizes = [32,
 64,
 128,
 256]
newsfile = '/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/vtinews.txt'
packagetmpfile = '/tmp/package.tmp'
config.plugins.vtipanel = ConfigSubsection()
config.plugins.vtipanel.configurationbackup = ConfigSubsection()
config.plugins.vtipanel.configurationbackup.backuplocation = ConfigText(default='/media/hdd/', visible_width=50, fixed_size=False)
config.plugins.vtipanel.configurationbackup.backuplocationimage = ConfigText(default='/media/hdd/', visible_width=50, fixed_size=False)
config.plugins.vtipanel.configurationbackup.backupdirs = ConfigLocations(default=['/etc/CCcam.cfg',
 '/etc/enigma2/',
 '/etc/network/interfaces',
 '/etc/wpa_supplicant.conf',
 '/etc/resolv.conf',
 '/etc/default_gw',
 '/etc/hostname'])
config.plugins.vtipanel.menunotshown = ConfigText(default='')
config.plugins.vtipanel.menushown = ConfigText(default='')
config.plugins.vtipanel.panelpassword = ConfigPassword(default='vtipanelpassword', visible_width=50, fixed_size=False)
config.plugins.vtipanel.inputpanelpassword = NoSave(ConfigPassword(default='', visible_width=50, fixed_size=False))
baseMenuList__init__ = None
iface = None

#class checkVU():

#    def runcheck(self):
#        try:
#            from enigma import getVTiVersionString
#            vtiversion = getVTiVersionString()
#        except:
#            vtiversion = '0'

#        if len(vtiversion) < 3:
#            novalidcode.errorintypo()
#            quitMainloop(3)
#            return


#checkvu = checkVU()
from MyPluginManager import MyPluginManager
from NewsCenter import AllNews, update_notification

class VTIPanelSummary(Screen):

    def __init__(self, session, parent):
        Screen.__init__(self, session, parent=parent)
        self['entry'] = StaticText('')
        self['desc'] = StaticText('')
        self.onShow.append(self.addWatcher)
        self.onHide.append(self.removeWatcher)

    def addWatcher(self):
        self.parent.onChangedEntry.append(self.selectionChanged)
        self.parent.selectionChanged()

    def removeWatcher(self):
        self.parent.onChangedEntry.remove(self.selectionChanged)

    def selectionChanged(self, name, desc):
        self['entry'].text = name
        self['desc'].text = desc


class VTIMainMenu(Screen, ProtectedScreen):

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        if config.ParentalControl.configured.value:
            ProtectedScreen.__init__(self)
        self.skin_path = plugin_path
        self['key_red'] = StaticText(_('Software'))
        self['key_green'] = StaticText(_('News'))
        self['key_yellow'] = StaticText(_('System Tools'))
        self['key_blue'] = StaticText(_('Cam Center'))
#       checkvu.runcheck()
        self.correctpassword = None
        self.title = _('VTI Panel')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['actions'] = ActionMap(['ColorActions', 'SetupActions'], {'red': self.redPressed,
         'green': self.greenPressed,
         'yellow': self.yellowPressed,
         'blue': self.bluePressed,
         'ok': self.okPressed,
         'cancel': self.close}, -1)
        self.dlg = None
        self.state = {}
        self.list = []
        self.output_line = ''
        self['list'] = List(self.list)
        self.onLayoutFinish.append(self.createMENUlist)
        self.onChangedEntry = []
        self['list'].onSelectionChanged.append(self.selectionChanged)

    def isProtected(self):
        return config.ParentalControl.setuppinactive.value and config.ParentalControl.config_sections.vti_panel.value

    def inputPassword(self):
        self.session.openWithCallback(self.checkPanelPassword, InputPanelPassword, self.skin_path)

    def checkPanelPassword(self, password = None):
        if password is None:
            self.close()
        elif password == config.plugins.vtipanel.panelpassword.value:
            self.correctpassword = password
        else:
            self.inputPassword()

    def createSummary(self):
        return VTIPanelSummary

    def selectionChanged(self):
        item = self['list'].getCurrent()
        if item:
            name = item[0]
            desc = item[2]
        else:
            name = '-'
            desc = ''
        for cb in self.onChangedEntry:
            cb(name, desc)

    def createMENUlist(self):
        self.mylist = []
        divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, '750S/div-h.png'))
        self.mylist.append((_('VTI Cam Center'),
         'CamSelectMenu',
         _('select or install your favourite cam'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/camcenter.png')),
         divpng))
        self.mylist.append((_('VTI System Info'),
         'SystemInfoMenu',
         _('Infos about your Vu+ STB'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/systeminfo.png')),
         divpng))
        self.mylist.append((_('VTI System Tools'),
         'SystemToolsMenu',
         _('manage your Vu+ STB'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/systemtools.png')),
         divpng))
        self.mylist.append((_('VTI Software Tools'),
         'BackupToolsMenu',
         _('backup/restore or install software'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backuptools.png')),
         divpng))
        self.mylist.append((_('VTI Software Manager'),
         'mypluginmanager',
         _('install/download software for your Vu+'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/softwaremanager.png')),
         divpng))
        self.mylist.append((_('manual Installer'),
         'manInstallerMenu',
         _('install .tar.gz or ipkg manually'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/manualinstaller.png')),
         divpng))
        self.mylist.append((_('Plugins'),
         'PluginBrowser',
         _('open enigma2 Plugin Menu'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/addons.png')),
         None))
        self['list'].setList(self.mylist)

    def okPressed(self):
        if config.plugins.vtipanel.panelpassword.value == 'vtipanelpassword' or self.correctpassword == config.plugins.vtipanel.panelpassword.value:
            pass
        else:
            self.inputPassword()
            return
        cur = self['list'].getCurrent()
        if cur:
            name = cur[0]
            menu = cur[1]
            if menu == 'CamSelectMenu':
                self.session.open(CamSelectMenu)
            elif menu == 'PluginBrowser':
                from Screens.PluginBrowser import PluginBrowser
                self.session.open(PluginBrowser)
            elif menu == 'BackupToolsMenu':
                self.session.open(VTISubMenu, 0)
            elif menu == 'manInstallerMenu':
                self.session.openWithCallback(self.updateList, VTISubMenu, 1)
            elif menu == 'ImageToolsMenu':
                self.session.open(VTISubMenu, 2)
            elif menu == 'SystemToolsMenu':
                self.session.open(VTISubMenu, 3)
            elif menu == 'SystemInfoMenu':
                self.session.open(VTISubMenu, 4)
            elif menu == 'mypluginmanager':
                self.session.open(MyPluginManager, self.skin_path)
            else:
                message = '[VTIPanel] no menu linked to ' + name
                self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        self.setTitle(title)
        self['title'] = StaticText(title)

    def updateList(self):
        plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))

    def redPressed(self):
        if config.plugins.vtipanel.panelpassword.value == 'vtipanelpassword' or self.correctpassword == config.plugins.vtipanel.panelpassword.value:
            pass
        else:
            self.inputPassword()
            return
        self.session.open(MyPluginManager, self.skin_path)

    def greenPressed(self):
        if config.plugins.vtipanel.panelpassword.value == 'vtipanelpassword' or self.correctpassword == config.plugins.vtipanel.panelpassword.value:
            pass
        else:
            self.inputPassword()
            return
        self.session.open(AllNews, self.skin_path)

    def yellowPressed(self):
        if config.plugins.vtipanel.panelpassword.value == 'vtipanelpassword' or self.correctpassword == config.plugins.vtipanel.panelpassword.value:
            pass
        else:
            self.inputPassword()
            return
        self.session.open(VTISubMenu, 3)

    def bluePressed(self):
        if config.plugins.vtipanel.panelpassword.value == 'vtipanelpassword' or self.correctpassword == config.plugins.vtipanel.panelpassword.value:
            pass
        else:
            self.inputPassword()
            return
        self.session.open(CamSelectMenu)

    def cancel(self):
        self.close()


class VTISubMenu(Screen):
    """
    one class for all needed submenus with colored picture in front...
    menu id 0 = backuptools
    menu id 1 = man installer
    menu id 2 = imagetools
    menu id 3 = system tools
    menu id 4 = system infos
    menu id 5 = backupsuite
    menu id 6 = image_backup
    menu_id 7 = expert _backup
    """

    def __init__(self, session, menuid, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.menu = menuid
        self.title = _('VTI Sub Menu')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.list = []
        self.text = ''
        self.backupdirs = ' '.join(config.plugins.vtipanel.configurationbackup.backupdirs.value)
        if self.menu == 0:
            menuid = 0
            self.list.append(('backupsuite',
             _('VTI BackupSuite'),
             _('Restore and backup installed channellist and plugins'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoreadvanced.png')),
             None,
             menuid))
            self.list.append(('image_backup',
             _('Image Backup / Restore'),
             _('backup or flash an image'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backupimage.png')),
             None,
             menuid))
            self.list.append(('image_flasher',
             _('Image Flash Tool'),
             _('download images from vuplus-support.org and flash it'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None,
             menuid))
            self.list.append(('expert_backup',
             _('Expert Backup / Restore'),
             _('backup or restore your settings (only for experts)'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backupfiles.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI Software Tools'))
        elif self.menu == 1:
            menuid = 1
            self.list.append(('tar.gz',
             _('Install .tar.gz '),
             _('Install all .tar.gz file form /tmp '),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/targz.png')),
             None,
             menuid))
            self.list.append(('ipkg',
             _('Install Ipkg'),
             _('Install local ipkg'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ipkg.png')),
             None,
             menuid))
            self.list.append(('ipkgadv',
             _('Advanced Ipkg Install'),
             _('Install local ipkg with --force overwrite'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ipkgadv.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI manual Addon Installer'))
        elif self.menu == 2:
            menuid = 2
            self.list.append(('update-image',
             _('Update Image'),
             _('Update your STB image from Internet.'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/updateimage.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI Image Tools'))
        elif self.menu == 3:
            menuid = 3
            if fileExists(resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/DeviceManager2/plugin.pyo')):
                self.list.append(('devicemanager',
                 _('Device Manager'),
                 _("manage your HDD's and USB devices"),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/devicemanager.png')),
                 None,
                 menuid))
            if fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/Filebrowser/plugin.py')):
                self.list.append(('FileManager',
                 _('File Manager'),
                 _('open Filemanager'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/filemanager_sub.png')),
                 None,
                 menuid))
            if fileExists(resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/NetworkBrowser/NetworkBrowser.py')):
                self.list.append(('NetworkBrowser',
                 _('Network Browser'),
                 _('open NetworkBrowswer'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/networkbrowser_sub.png')),
                 None,
                 menuid))
            self.list.append(('vtizero',
             _('VTi ZerO'),
             _('Remove preinstalled packages from image'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero.png')),
             None,
             menuid))
            self.list.append(('epgpanel',
             _('EPG Settings'),
             _('set EPG path, restore or backup EPG data'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/epgpanel.png')),
             None,
             menuid))
            self.list.append(('reducemainmenu',
             _('Custom Main Menu'),
             _('delete entries from main menu of your VU+'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_kernel.png')),
             None,
             menuid))
            self.list.append(('cronmanager',
             _('Cronjob Manager'),
             _('manage cronjobs of your VU+'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/cronmanager.png')),
             None,
             menuid))
            self.list.append(('exemanager',
             _('Run Command'),
             _('run executable files of your VU+'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/exemanager.png')),
             None,
             menuid))
            self.list.append(('panelpassword',
             _('Set VTI Panel Password'),
             _('activate/change password for VTI Panel'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_systemplugin.png')),
             None,
             menuid))
            self.list.append(('passwd',
             _('Set Root Password'),
             _('set root password of your stb'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/passwd.png')),
             None,
             menuid))
            self.list.append(('services',
             _('Services'),
             _('enable/disable Systemservices'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/services.png')),
             None,
             menuid))
            self.list.append(('sundtek',
             _('USB DVB-T/C/S2 Panel'),
             _('manage Sundtek USB DVB Stick'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/dvbsundtek.png')),
             None,
             menuid))
            if fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/WebBrowser/plugin.py')):
                self.list.append(('webbrowserremove',
                 _('Remove WebBrowser'),
                 _('removes WebBrowser and dependencies'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/remove.png')),
                 None,
                 menuid))
            if fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/HbbTV/plugin.pyo')):
                self.list.append(('hbbtvremove',
                 _('Remove Opera HbbTV'),
                 _('removes Opera HbbTV and dependencies'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/remove.png')),
                 None,
                 menuid))
            self.list.append(('ipkuninstaller',
             _('IPK Uninstaller'),
             _('remove seletected package from stb'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ipkgremove.png')),
             None,
             menuid))
            if os_path.exists('/dev/sda') == True:
                self.list.append(('e2crashlog',
                 _('Purge Enigma2 Crashlogs'),
                 _('selective wipe of enigma2 crashlogs'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/crashlog.png')),
                 None,
                 menuid))
            self.list.append(('swapfile',
             _('Swapfile'),
             _('create and manage your Swapfile'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/swapfile.png')),
             None,
             menuid))
            self.list.append(('ntptime',
             _('Set NTP Time'),
             _('refresh time for enigma2 from ntp server'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
             None,
             menuid))
            self.list.append(('hddstandby',
             _('Harddisk Standby'),
             _('turns hdd immediately into standby mode'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/hddstandby.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI System Tools'))
        elif self.menu == 4:
            menuid = 4
            self.list.append(('bitrate',
             _('Bitrate Viewer'),
             _('Show Advanced Bitrate infos'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/bitrate.png')),
             None,
             menuid))
            if fileExists('/tmp/ecm.info'):
                self.list.append(('ecm',
                 _('ECM Info'),
                 _('show ecm infos from temp dir'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ecm.png')),
                 None,
                 menuid))
            self.list.append(('vtinews',
             _('News about VTI'),
             _('show Feed updates'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/news.png')),
             None,
             menuid))
            self.list.append(('vtisysteminfo',
             _('Info about current system'),
             _('show information about processes, load, mounts ...'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/exemanager.png')),
             None,
             menuid))
            self.list.append(('ps-xa',
             _('Show processes'),
             _('show running processes'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/psxa.png')),
             None,
             menuid))
            self.list.append(('mount',
             _('Show filesystem mounts'),
             _('show active mounts'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/filesys.png')),
             None,
             menuid))
            self.list.append(('hddtemp',
             _('Harddisk Temperature'),
             _('show HDD Temperature'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/hddtemp.png')),
             None,
             menuid))
            self.list.append(('who',
             _('Show Consolesessions'),
             _('show all active user sessions'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sessions.png')),
             None,
             menuid))
            self.list.append(('uptime',
             _('Show Uptime'),
             _('show operating system uptime of stb'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/uptime.png')),
             None,
             menuid))
            self.list.append(('sockets',
             _('Show Networkconnections'),
             _('show all connected sockets from ip-stack'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sockets.png')),
             None,
             menuid))
            self.list.append(('memory',
             _('Show Systemmemory Info'),
             _('show whole system memory usage'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/memory.png')),
             None,
             menuid))
            self.list.append(('networkconfig',
             _('Show Networkdetails'),
             _('shows assigned ip-adresses, routingtable and nameserver'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/nwcfg.png')),
             None,
             menuid))
            self.list.append(('df-h',
             _('Show diskspace'),
             _('show diskpace'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/df-h.png')),
             None,
             menuid))
            self.list.append(('about',
             _('Image Info'),
             _('show simple Image infos'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/about.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI System Infos'))
        elif self.menu == 5:
            menuid = 5
            self.list.append(('backupsuite_backup',
             _('VTI Backupsuite') + ' - ' + _('Backup'),
             _('Backup installed channellist and plugins'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/savesettings.png')),
             None,
             menuid))
            self.list.append(('backupsuite_restore',
             _('VTI Backupsuite') + ' - ' + _('Restore'),
             _('Restore installed channellist and plugins'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI BackupSuite'))
        elif self.menu == 6:
            menuid = 6
            self.list.append(('backup-image',
             _('Backup Image'),
             _('Backup your running STB image.'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/savesettings.png')),
             None,
             menuid))
            self.list.append(('restore-image',
             _('Restore Image'),
             _('Restore your backuped STB image.'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None,
             menuid))
            self.list.append(('backuplocationimage',
             _('Choose backup location'),
             _('Select your backup device. '),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backuplocation.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI Image Backup/Restore'))
        elif self.menu == 7:
            menuid = 7
            self.list.append(('system-backup',
             _('Backup system settings'),
             _('Backup your STB settings.'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/savesettings.png')),
             None,
             menuid))
            self.list.append(('system-restore',
             _('Restore system settings'),
             _('Restore your STB settings.'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None,
             menuid))
            self.list.append(('advancedrestore',
             _('Advanced restore'),
             _('Restore your backups by date.'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoreadvanced.png')),
             None,
             menuid))
            self.list.append(('backuplocation',
             _('Choose backup location'),
             _('Select your backup device. '),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backuplocation.png')),
             None,
             menuid))
            self.list.append(('backupfiles',
             _('Choose backup files'),
             _('Select files for backup. '),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backupfiles.png')),
             None,
             menuid))
            self.setWindowTitle(_('VTI Expert Backup/Restore'))
        self['list'] = List(self.list)
        self['key_red'] = StaticText(_('Close'))
        self['status'] = StaticText(_('\nPress OK on your remote control to continue.'))
        self['shortcuts'] = ActionMap(['ShortcutActions', 'WizardActions', 'InfobarEPGActions'], {'ok': self.go,
         'back': self.close,
         'red': self.close}, -1)
        self.onLayoutFinish.append(self.layoutFinished)
        self.backuppath = getBackupPath()
        self.backupfile = getBackupFilename()
        self.fullbackupfilename = self.backuppath + '/' + self.backupfile
        self.onChangedEntry = []
        self['list'].onSelectionChanged.append(self.selectionChanged)

    def createSummary(self):
        return VTIPanelSummary

    def selectionChanged(self):
        item = self['list'].getCurrent()
        if item:
            name = item[1]
            desc = item[2]
        else:
            name = '-'
            desc = ''
        for cb in self.onChangedEntry:
            cb(name, desc)

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        try:
            self['title'] = StaticText(title)
        except:
            print 'self["title"] was not found in skin'

    def layoutFinished(self):
        idx = 0
        self['list'].index = idx

    def go(self):
        current = self['list'].getCurrent()
        if current:
            currentEntry = current[0]
            if currentEntry == 'backupsuite':
                self.session.open(VTISubMenu, 5)
            elif currentEntry == 'image_backup':
                self.session.open(VTISubMenu, 6)
            elif currentEntry == 'expert_backup':
                self.session.open(VTISubMenu, 7)
            elif currentEntry == 'tar.gz':
                self.session.openWithCallback(self.updateList, Console, title=_('VTI .tar.gz installer'), cmdlist=["for i in /media/usb/*.tar.gz; do if [ $i != '/media/usb/*.tar.gz' ];  then echo Installing $i; tar -xzf $i -C /; else echo No tar.gz in /media/usb;  fi; done && for i in /tmp/*.tar.gz; do if [ $i != '/tmp/*.tar.gz' ];  then echo Installing $i; tar -xzf $i -C /; else echo No tar.gz in /tmp;  fi; done"])
            elif currentEntry == 'ipkg':
                self.session.openWithCallback(self.updateList, Console, title=_('VTI IPK Installer'), cmdlist=["for i in /media/usb/*.ipk; do if [ $i != '/media/usb/*.ipk' ];  then echo Installing $i; opkg -V0 install $i; else echo No IPK in /media/usb;  fi; done && for i in /tmp/*.ipk; do if [ $i != '/tmp/*.ipk' ];  then echo Installing $i; opkg -V0 install $i; else echo No IPK in /tmp;  fi; done"])
            elif currentEntry == 'ipkgadv':
                self.session.openWithCallback(self.updateList, Console, title=_('VTI IPK Installer'), cmdlist=["for i in /media/usb/*.ipk; do if [ $i != '/media/usb/*.ipk' ];  then echo Installing $i; opkg -V0 --force-overwrite install $i; else echo No IPK in /media/usb;  fi; done && for i in /tmp/*.ipk; do if [ $i != '/tmp/*.ipk' ];  then echo Installing $i; opkg -V0 --force-overwrite install $i; else echo No IPK in /tmp;  fi; done"])
            elif currentEntry == 'devicemanager':
                if fileExists(resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/DeviceManager2/plugin.pyo')):
                    try:
                        from Plugins.SystemPlugins.DeviceManager2.plugin import DeviceManager2
                    except ImportError:
                        self.session.open(MessageBox, _('The Device Manager is not installed!\nPlease install it.'), type=MessageBox.TYPE_INFO, timeout=10)
                    else:
                        self.session.open(DeviceManager2)

            elif currentEntry == 'FileManager':
                if fileExists(resolveFilename(SCOPE_PLUGINS, 'Extensions/Filebrowser/plugin.py')):
                    try:
                        from Plugins.Extensions.Filebrowser.plugin import FilebrowserScreen
                    except ImportError:
                        self.session.open(MessageBox, _('The FileManager is not installed!\nPlease install it.'), type=MessageBox.TYPE_INFO, timeout=10)
                    else:
                        self.session.open(FilebrowserScreen)

            elif currentEntry == 'NetworkBrowser':
                if fileExists(resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/NetworkBrowser/NetworkBrowser.py')):
                    try:
                        from Plugins.SystemPlugins.NetworkBrowser.NetworkBrowser import NetworkBrowser
                    except ImportError:
                        self.session.open(MessageBox, _('The NetworkBrowser is not installed!\nPlease install it.'), type=MessageBox.TYPE_INFO, timeout=10)
                    else:
                        self.adapters = iNetwork.getConfiguredAdapters()
                        if len(self.adapters) == 0:
                            iface = None
                        else:
                            iface = self.adapters[0]
                        self.session.open(NetworkBrowser, iface, plugin_path)

            elif currentEntry == 'vtizero':
                from VTiZerO import VTiZerO
                self.session.open(VTiZerO, self.skin_path)
            elif currentEntry == 'webbrowserremove':
                self.cmdList = []
                self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': '--force-depends --autoremove enigma2-plugin-extensions-webbrowser'}))
                self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': '--force-depends --autoremove vuplus-webbrowser-utils'}))
                self.session.open(Ipkg, cmdList=self.cmdList)
            elif currentEntry == 'hbbtvremove':
                self.cmdList = []
                self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': '--force-depends --autoremove enigma2-plugin-extensions-hbbtv'}))
                self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': '--force-depends --autoremove opera-hbbtv'}))
                self.session.open(Ipkg, cmdList=self.cmdList)
            elif currentEntry == 'passwd':
                self.session.open(VTIPasswdScreen)
            elif currentEntry == 'image_flasher':
                from ImageUpgrade import ImageDownload
                self.session.open(ImageDownload, self.skin_path)
            elif currentEntry == 'reducemainmenu':
                from ReduceMenu import ReduceMenuConfig
                self.session.open(ReduceMenuConfig, self.skin_path)
            elif currentEntry == 'epgpanel':
                from EPGPanel import EPGPanel
                self.session.open(EPGPanel, self.skin_path)
            elif currentEntry == 'cronmanager':
                from CronManager import CronManager
                self.session.open(CronManager, self.skin_path)
            elif currentEntry == 'exemanager':
                from ExeManager import ExeManager
                self.session.open(ExeManager, self.skin_path)
            elif currentEntry == 'panelpassword':
                from PanelPassword import PanelPassword
                self.session.open(PanelPassword, self.skin_path)
            elif currentEntry == 'services':
                self.session.open(VTIStatusListMenu, 22)
            elif currentEntry == 'sundtek':
                self.session.open(VTIStatusListMenu, 27)
            elif currentEntry == 'ipkuninstaller':
                self.session.open(VTIStatusListMenu, 24)
            elif currentEntry == 'skinremove':
                self.session.open(VTIStatusListMenu, 25)
            elif currentEntry == 'e2crashlog':
                self.session.open(VTIStatusListMenu, 26)
            elif currentEntry == 'swapfile':
                self.session.open(VTIStatusListMenu, 21)
            elif currentEntry == 'ntptime':
                self.session.open(NTPManager)
            elif currentEntry == 'hddstandby':
                cmdlist = []
                for hdd in harddiskmanager.HDDList():
                    device_path = hdd[1].getDeviceDir()
                    cmd = 'hdparm -qy ' + str(device_path)
                    cmdlist.append(cmd)

                if len(cmdlist):
                    self.session.open(Console, title=_('VTI Harddisk Standbymode'), cmdlist=cmdlist)
            elif currentEntry == 'bitrate':
                self.session.open(BitrateViewer)
            elif currentEntry == 'ecm':
                self.session.open(Console, title=_('VTI show ecm.info'), cmdlist=['for i in /tmp/ecm*info;do echo $i;echo ------------------------------------------------; cat $i; echo ================================================; done'])
            elif currentEntry == 'ps-xa':
                self.session.open(Console, title=_('VTI show running processes'), cmdlist=['ps -xa'])
            elif currentEntry == 'vtinews':
                self.session.open(AllNews, self.skin_path)
            elif currentEntry == 'vtisysteminfo':
                from InfoPanel import InfoPanel
                self.session.open(InfoPanel, self.skin_path)
            elif currentEntry == 'mount':
                self.session.open(Console, title=_('VTI show mounted filesystems'), cmdlist=['mount'])
            elif currentEntry == 'networkconfig':
                self.session.open(Console, title=_('VTI show networkconfiguration and routingtable'), cmdlist=['ip addr; iwconfig; echo ------------------------------------------------; route -n; echo ================================================; cat /etc/resolv.conf'])
            elif currentEntry == 'hddtemp':
                if os_path.exists('/dev/sda') == True:
                    msg = self.session.openWithCallback(self.hdparm, MessageBox, _("Harddiskmanufacturer, Type and it's Temperature :") + '\n\n' + self.ScanHDD() + '\n\n' + _('Are you sure to set hdd in standby mode?'), MessageBox.TYPE_YESNO)
                    msg.setTitle(_('HDD Temperature'))
                else:
                    self.session.open(MessageBox, _('No internal Harddisk detected!!!! \n\nPlease install an internal Harddisk first to be in a position to check harddisk temperature.'), MessageBox.TYPE_INFO, timeout=5)
            elif currentEntry == 'who':
                self.session.open(Console, title=_('Active Usersessions :'), cmdlist=['who'])
            elif currentEntry == 'uptime':
                msg = self.session.open(MessageBox, _('Current Time, Operating Time and Load Average :') + '\n\n' + self.ShowUptime(), MessageBox.TYPE_INFO)
                msg.setTitle(_('Uptime'))
            elif currentEntry == 'sockets':
                self.session.open(Console, title=_('VTI show network stats'), cmdlist=['netstat -t -u'])
            elif currentEntry == 'memory':
                msg = self.session.open(MessageBox, _('Current Memory Usage :') + '\n\n' + self.ShowMemoryUsage(), MessageBox.TYPE_INFO)
                msg.setTitle(_('Memory Usage'))
            elif currentEntry == 'df-h':
                self.session.open(Console, title=_('VTI show free diskspace'), cmdlist=['df -h'])
            elif currentEntry == 'about':
                self.session.open(About)
            elif currentEntry == 'backupsuite_backup':
                from BackupSuite import BackupSuite
                self.session.open(BackupSuite, self.skin_path, 'backup')
            elif currentEntry == 'backupsuite_restore':
                from BackupSuite import BackupSuite
                self.session.open(BackupSuite, self.skin_path, 'restore')
            elif currentEntry == 'backuplocationimage':
                no_access_dirs = []
                no_access_dirs.append('/media/net/autofs')
                if os_path.exists('/media/net/autofs'):
                    for dir in listdir('/media/net/autofs'):
                        autofs_dir = '/media/net/autofs/' + dir
                        if os_path.exists(autofs_dir):
                            try:
                                listdir(autofs_dir)
                            except OSError:
                                no_access_dirs.append(autofs_dir)

                mounts = open('/proc/mounts').readlines()
                locations = []
                for mp in mounts:
                    mp = mp.split(' ')
                    if len(mp) >= 2:
                        if mp[1].startswith('/media/') and mp[1] != '/media/net' and mp[1] not in no_access_dirs:
                            locations.append((mp[1], mp[1], None))

                if len(locations):
                    self.session.openWithCallback(self.backuplocationImage_choosen, ChoiceBox, title=_('Please select medium to use as backup location'), list=locations)
            elif currentEntry == 'restore-image':
                self.session.open(RestoreMenuImage, self.skin_path)
            elif currentEntry == 'backup-image':
                self.backuppath = getBackupPathImage()
                self.session.open(BackupRestoreScreen, backuppath=self.backuppath)
            elif currentEntry == 'backuplocation':
                no_access_dirs = []
                no_access_dirs.append('/media/net/autofs')
                if os_path.exists('/media/net/autofs'):
                    for dir in listdir('/media/net/autofs'):
                        autofs_dir = '/media/net/autofs/' + dir
                        if os_path.exists(autofs_dir):
                            try:
                                listdir(autofs_dir)
                            except OSError:
                                no_access_dirs.append(autofs_dir)

                mounts = open('/proc/mounts').readlines()
                locations = []
                for mp in mounts:
                    mp = mp.split(' ')
                    if len(mp) >= 2:
                        if mp[1].startswith('/media/') and mp[1] != '/media/net' and mp[1] not in no_access_dirs:
                            locations.append((mp[1], mp[1], None))

                if len(locations):
                    self.session.openWithCallback(self.backuplocation_choosen, ChoiceBox, title=_('Please select medium to use as backup location'), list=locations)
            elif currentEntry == 'backupfiles':
                self.session.openWithCallback(self.backupfiles_choosen, BackupSelection)
            elif currentEntry == 'advancedrestore':
                self.session.open(RestoreMenu, self.skin_path)
            elif currentEntry == 'system-backup':
                self.session.openWithCallback(self.backupDone, BackupScreen, runBackup=True)
            elif currentEntry == 'system-restore':
                if os_path.exists(self.fullbackupfilename):
                    self.session.openWithCallback(self.startRestore, MessageBox, _('Are you sure you want to restore your Enigma2 backup?\nEnigma2 will restart after the restore'))
                else:
                    self.session.open(MessageBox, _('Sorry no backups found!'), MessageBox.TYPE_INFO, timeout=10)
            else:
                self.session.open(MessageBox, _('Menu not implemented yet!!!! \n\nfeel free to code this menu now ;)'), MessageBox.TYPE_INFO, timeout=5)

    def askReboot(self):
        self.session.openWithCallback(self.reboot, MessageBox, _('Install/update finished.') + ' ' + _('Do you want to reboot your STB?'), MessageBox.TYPE_YESNO)

    def askRestoreImage(self, result):
        if result:
            if fileExists('/media/hdd/vuplus/duo/boot_cfe_auto.jffs2') and fileExists('/media/hdd/vuplus/duo/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/duo/root_cfe_auto.jffs2'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/solo/boot_cfe_auto.jffs2') and fileExists('/media/hdd/vuplus/solo/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/solo/root_cfe_auto.jffs2'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/uno/boot_cfe_auto.jffs2') and fileExists('/media/hdd/vuplus/uno/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/uno/root_cfe_auto.jffs2'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/ultimo/boot_cfe_auto.jffs2') and fileExists('/media/hdd/vuplus/ultimo/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/ultimo/root_cfe_auto.jffs2'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/solo2/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/solo2/root_cfe_auto.bin'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/duo2/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/duo2/root_cfe_auto.bin'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/solose/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/solose/root_cfe_auto.bin'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            elif fileExists('/media/hdd/vuplus/zero/kernel_cfe_auto.bin') and fileExists('/media/hdd/vuplus/zero/root_cfe_auto.bin'):
                self.session.open(Console, title=_('VTI Restore Image'), cmdlist=['/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/_restore.sh /media/hdd'])
            else:
                self.session.open(MessageBox, _('No image found!!!! \n\nPlease copy usb image or restore image to /media/hdd/vuplus/MODEL .'), MessageBox.TYPE_INFO, timeout=5)

    def reboot(self, result):
        if result:
            quitMainloop(3)

    def backupfiles_choosen(self, ret):
        self.backupdirs = ' '.join(config.plugins.vtipanel.configurationbackup.backupdirs.value)

    def backuplocation_choosen(self, option):
        if option is not None:
            config.plugins.vtipanel.configurationbackup.backuplocation.value = str(option[1])
        config.plugins.vtipanel.configurationbackup.backuplocation.save()
        config.plugins.vtipanel.configurationbackup.save()
        config.save()
        self.createBackupfolders()

    def backuplocationImage_choosen(self, option):
        if option is not None:
            config.plugins.vtipanel.configurationbackup.backuplocationimage.value = str(option[1])
        config.plugins.vtipanel.configurationbackup.backuplocationimage.save()
        config.plugins.vtipanel.configurationbackup.save()
        config.save()
        self.createBackupfoldersImage()

    def createBackupfolders(self):
        self.backuppath = getBackupPath()
        try:
            if os_path.exists(self.backuppath) == False:
                makedirs(self.backuppath)
        except OSError:
            self.session.open(MessageBox, _('Sorry, your backup destination is not writeable.\n\nPlease choose another one.'), MessageBox.TYPE_INFO, timeout=10)

    def createBackupfoldersImage(self):
        self.backuppath = getBackupPathImage()
        try:
            if os_path.exists(self.backuppath) == False:
                makedirs(self.backuppath)
        except OSError:
            self.session.open(MessageBox, _('Sorry, your backup destination is not writeable.\n\nPlease choose another one.'), MessageBox.TYPE_INFO, timeout=10)

    def backupDone(self, retval = None):
        if retval is True:
            self.session.open(MessageBox, _('VTI-Backup done.'), MessageBox.TYPE_INFO, timeout=10)
        else:
            self.session.open(MessageBox, _('VTI-Backup failed.'), MessageBox.TYPE_INFO, timeout=10)

    def startRestore(self, ret = False):
        if ret == True:
            self.exe = True
            self.session.open(RestoreScreen, runRestore=True)

    def updateList(self):
        plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))

    def ScanHDD(self):
        ret = ''
        try:
            for hdd in harddiskmanager.HDDList():
                device_path = hdd[1].getDeviceDir()
                device_model = hdd[1].model()
                device_size = hdd[1].capacity()
                device_temp = popen('hddtemp -q ' + str(device_path) + ' | cut -d":" -f3').readline()
                ret += '%s (%s, %s) : %s\n' % (device_path,
                 device_model,
                 device_size,
                 device_temp)

            return ret
        except:
            return _('No Harddisk or Harddisk with S.M.A.R.T capabilites detected')

    def ShowUptime(self):
        try:
            ret = ''
            out_line = popen('uptime').readline()
            ret = ret + _('At') + out_line + '\n'
            return ret
            out_line.close()
        except:
            return _('Could not grep Uptime Information from busybox')

    def ShowAllSockets(self):
        try:
            ret = ''
            out_lines = []
            out_lines = popen('netstat -t -u').readlines()
            for lidx in range(len(out_lines) - 1):
                ret = ret + out_lines[lidx] + '\n'

            return ret
            out_lines.close()
        except:
            return _('Could not grep socket information from busybox')

    def ShowMemoryUsage(self):
        try:
            ret = ''
            out_lines = []
            out_lines = popen('free').readlines()
            for lidx in range(len(out_lines) - 1):
                ret = ret + out_lines[lidx] + '\n'

            return ret
            out_lines.close()
        except:
            return _('Could not grep Memory Usage information from busybox')

    def hdparm(self, result):
        if result is None or result is False:
            pass
        else:
            for hdd in harddiskmanager.HDDList():
                device_path = hdd[1].getDeviceDir()
                cmd = 'hdparm -qy ' + str(device_path)
                system(cmd)

            return


class VTIStatusListMenu(Screen):
    """
    one class for all needed submenus with status check picture in front...
    menu id 20 = reserved..
    menu id 21 = swap menu
    menu id 22 = services menu
    menu id 23 = usb menu
    menu id 24 = ipkuninstaller menu
    menu id 25 = skinremove menu
    menu id 26 = e2crashlog menu
    menu id 27 = sundtek menu
    """

    def __init__(self, session, menuid, args = 0):
        Screen.__init__(self, session)
        self.menu = menuid
        self.skin_path = plugin_path
        self['key_red'] = Label()
        self['key_green'] = Label()
        self['key_yellow'] = Label()
        self['key_blue'] = Label()
        self['pic_red'] = Pixmap()
        self['pic_green'] = Pixmap()
        self['pic_yellow'] = Pixmap()
        self['pic_blue'] = Pixmap()
        self.title = _('VTI Status List Menu')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        if self.menu == 21:
            self['key_red'].setText(_('Stop Swap'))
            self['key_green'].setText(_('Start Swap'))
            self['key_yellow'].hide()
            self['key_blue'].hide()
            self['pic_yellow'].hide()
            self['pic_blue'].hide()
            self.setWindowTitle(_('VTI SwapFile Menu'))
            self.onShown.append(self.buildSwapList)
        elif self.menu == 22:
            self['key_red'].setText(_('Stop'))
            self['key_green'].setText(_('Start'))
            self['key_yellow'].setText(_('Restart'))
            self['key_blue'].hide()
            self['pic_blue'].hide()
            self.setWindowTitle(_('VTI Services Menu'))
            self.onShown.append(self.buildServicesList)
        elif self.menu == 24:
            self['key_red'].setText(_('Uninstall'))
            self['key_green'].setText(_('Force uninst.'))
            self['key_yellow'].hide()
            self['key_blue'].hide()
            self['pic_yellow'].hide()
            self['pic_blue'].hide()
            self.setWindowTitle(_('VTI IPK Uninstaller Menu'))
            self.onShown.append(self.buildIPKinstalledList)
        elif self.menu == 25:
            self['key_red'].setText(_('Remove Skin'))
            self['key_green'].hide()
            self['key_yellow'].hide()
            self['key_blue'].hide()
            self['pic_green'].hide()
            self['pic_yellow'].hide()
            self['pic_blue'].hide()
            self.setWindowTitle(_('VTI Skinremove Menu'))
            self.onShown.append(self.buildSkinList)
        elif self.menu == 26:
            self['key_red'].setText(_('Remove selected'))
            self['key_green'].setText(_('Remove all'))
            self['key_yellow'].setText(_('Remove older 7 Days'))
            self['key_blue'].hide()
            self['pic_blue'].hide()
            self.setWindowTitle(_('VTI Crashlogremove Menu'))
            self.onShown.append(self.buildCrashlogList)
        elif self.menu == 27:
            self['key_red'].hide()
            self['key_green'].setText(_('Ok'))
            self['key_yellow'].hide()
            self['key_blue'].hide()
            self['pic_blue'].hide()
            self['pic_red'].hide()
            self['pic_yellow'].hide()
            self.setWindowTitle(_('VTI USB DVB-Panel'))
            self.onShown.append(self.buildSundtekList)
        else:
            self['key_red'].setText(_('not in use'))
            self['key_green'].setText(_('not in use'))
            self['key_yellow'].setText(_('not in use'))
            self['key_blue'].setText(_('not in use'))
            self.setWindowTitle(_('VTI Status List Menu'))
        self['actions'] = ActionMap(['ColorActions', 'SetupActions'], {'red': self.redPressed,
         'green': self.greenPressed,
         'yellow': self.yellowPressed,
         'blue': self.bluePressed,
         'ok': self.okPressed,
         'cancel': self.close}, -1)
        self.list = []
        self.output_line = ''
        self['list'] = List(self.list)

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        try:
            self['title'] = StaticText(title)
        except:
            print 'self["title"] was not found in skin'

    def redPressed(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            if self.menu == 21:
                self.askForBuild(cur, 'stop')
            elif self.menu == 22:
                self.askForBuild(cur, 'stop')
            elif self.menu == 24:
                self.askForBuild(cur, 'stop')
            elif self.menu == 25:
                self.askForBuild(cur, 'stop')
            elif self.menu == 26:
                self.askForBuild(cur, 'stop')

    def greenPressed(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            if self.menu == 21:
                self.askForBuild(cur)
            elif self.menu == 22:
                self.askForBuild(cur, 'start')
            elif self.menu == 24:
                self.askForBuild(cur, 'start')
            elif self.menu == 26:
                self.askForBuild(cur, 'start')
            elif self.menu == 27:
                self.askForBuild(cur, 'start')

    def yellowPressed(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            if self.menu == 22:
                self.askForBuild(cur, 'restart')
            elif self.menu == 26:
                self.askForBuild(cur, 'restart')

    def bluePressed(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            print '[VTIPanel] blue pressed'

    def okPressed(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            if self.menu == 21:
                self.askForBuild(cur)
            elif self.menu == 27:
                self.askForBuild(cur, 'start')

    def buildServicesList(self):
        try:
            list = []
            exclude = ['bootup',
             'devpts.sh',
             'halt',
             'rc',
             'rcS',
             'reboot',
             'rmnologin',
             'sendsigs',
             'single',
             'sysfs.sh',
             'umountfs']
            for root, dirnames, filenames in walk('/etc/init.d'):
                filenames.sort()
                for item in filenames:
                    if item not in exclude:
                        fullname = '/etc/init.d/' + item
                        list.append((item,
                         fullname,
                         None,
                         None))

            self['list'].setList(list)
        except:
            pass

    def buildIPKinstalledList(self):
        try:
            list = []
            cmd = 'opkg list_installed > /tmp/ipkdb'
            system(cmd)
            ret = ''
            out_lines = []
            out_lines = popen('cat /tmp/ipkdb').readlines()
            for filename in out_lines:
                ret = out_lines
                list.append((filename,
                 ret,
                 None,
                 None))

            self['list'].setList(list)
            out_lines.close()
        except:
            pass

    def buildSkinList(self):
        try:
            list = []
            chdir('/usr/share/enigma2')
            for root, dirnames, filenames in walk('.'):
                for filename in filenames:
                    if filename.endswith('skin.xml'):
                        if not root == '.':
                            root = root.replace('./', '')
                            fullname = '/usr/share/enigma2/' + root
                            if not root.endswith('Vu_HD'):
                                list.append((root,
                                 fullname,
                                 None,
                                 None))

            self['list'].setList(list)
        except:
            pass

    def buildCrashlogList(self):
        try:
            list = []
            curtime = time()
            for root, dirnames, filenames in walk('/media/hdd'):
                filenames.sort()
                for item in filenames:
                    if (item.startswith('enigma2_crash_') or item.startswith('dvbapp2_crash_')) and item.endswith('.log'):
                        fullname = '/media/hdd/' + item
                        list.append((item,
                         fullname,
                         None,
                         None))

            self['list'].setList(list)
        except:
            pass

    def buildSundtekList(self):
        try:
            list = []
            for root, dirnames, filenames in walk('/usr/script'):
                filenames.sort()
                for item in filenames:
                    if item.startswith('DVB_') and item.endswith('.sh'):
                        fullname = '/usr/script/' + item
                        list.append((item,
                         fullname,
                         None,
                         None))

            self['list'].setList(list)
        except:
            pass

    def buildSwapList(self):
        list = []
        cur_swap = self.checkSwap()
        for loc in swaplocations:
            if os_path.exists(loc) == True:
                for size in swapsizes:
                    text = str(size) + _('MB swapfile on ') + loc
                    if cur_swap[0] == loc and int(cur_swap[1]) == int(size):
                        list.append((text,
                         loc,
                         str(size),
                         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/green_ok.png'))))
                    else:
                        list.append((text,
                         loc,
                         str(size),
                         None))

        self['list'].setList(list)

    def askForBuild(self, result, action = None):
        global package
        if self.menu == 21:
            try:
                self.swaptext = result[0]
                self.swaptarget = result[1]
                self.swapsize = result[2]
                if action == 'stop':
                    self.session.openWithCallback(self.stopSwap, MessageBox, _('Are you sure to delete swapfile ?'), MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(self.buildSwapfile, MessageBox, _('Are you sure to %s ?') % self.swaptext, MessageBox.TYPE_YESNO)
            except:
                pass

        elif self.menu == 22:
            try:
                bin = result[1]
                if action == 'start':
                    self.session.open(Console, title=_('VTI Start Service'), cmdlist=[bin + ' start'])
                elif action == 'stop':
                    self.session.open(Console, title=_('VTI Stop Service'), cmdlist=[bin + ' stop'])
                elif action == 'restart':
                    self.session.open(Console, title=_('VTI Restart Service'), cmdlist=[bin + ' restart'])
            except:
                pass

        elif self.menu == 24:
            try:
                package = result[0]
                if action == 'start':
                    self.session.openWithCallback(self.ipkuninstallforce, MessageBox, 'Are you sure to force uninstall of selected package: \n' + package, MessageBox.TYPE_YESNO)
                elif action == 'stop':
                    self.session.openWithCallback(self.ipkuninstall, MessageBox, 'Are you sure to uninstall selected package: \n' + package, MessageBox.TYPE_YESNO)
            except:
                pass

        elif self.menu == 25:
            try:
                skin = result[1]
                if action == 'stop':
                    self.session.open(Console, title=_('VTI Skinremoval'), cmdlist=['echo Removing Skin; rm -rf ' + skin])
            except:
                pass

        elif self.menu == 26:
            try:
                crashlog = result[1]
                crash7 = result[2]
                if action == 'start':
                    self.session.open(Console, title=_('VTI Remove Enigma2 Crashlog'), cmdlist=['echo Removing all Enigma2 Crashlogs; rm -rf /media/hdd/enigma2_crash_*.log ; rm -rf /media/hdd/dvbapp2_crash_*.log'])
                elif action == 'stop':
                    self.session.open(Console, title=_('VTI Remove Enigma2 Crashlog'), cmdlist=['echo Removing selected Enigma2 Crashlog; rm -rf ' + crashlog])
                elif action == 'restart':
                    curtime = time()
                    for root, dirnames, filenames in walk('/media/hdd'):
                        filenames.sort()
                        for item in filenames:
                            if (item.startswith('enigma2_crash_') or item.startswith('dvbapp2_crash_')) and item.endswith('.log'):
                                fullname = '/media/hdd/' + item
                                difftime = curtime - os_path.getmtime('/media/hdd/' + item)
                                if difftime >= 604800:
                                    remove(fullname)

                    self.session.open(MessageBox, _('Deleted Crashlogs older 7 Days...'), MessageBox.TYPE_INFO, timeout=5)
            except:
                pass

        elif self.menu == 27:
            try:
                bin = result[1]
                if action == 'start':
                    self.session.open(Console, title=_('VTI USB DVB-Panel'), cmdlist=[bin])
            except:
                pass

    def checkSwap(self):
        try:
            for line in open(swapstarter):
                if line.lstrip().lower().startswith('swapon'):
                    swapfile = line.lstrip('swapon ').rstrip('\n')
                    try:
                        swapfilelocation = swapfile.rstrip('/swapfile')
                        swapfilesize = os_path.getsize(swapfile) / 1024 / 1024
                        return (swapfilelocation, int(swapfilesize))
                    except:
                        pass

            return (None, -1)
        except IOError:
            return (None, -1)

    def stopSwap(self, result):
        if result is None or result is False:
            pass
        else:
            cur_swap = self.checkSwap()
            if cur_swap[0] is not None:
                swapfile = cur_swap[0] + '/swapfile'
                stopcmd = 'echo ' + _('stopping swap for ') + swapfile + ' && swapoff ' + swapfile + ' && rm -rf ' + swapstarter + ' ' + swapfile + ' && free && echo ' + _('swapfile was deleted successfully')
                self.session.open(Console, title=_('VTI create SwapFile'), cmdlist=[stopcmd])
            else:
                self.session.open(MessageBox, _('no swapfile active...'), MessageBox.TYPE_INFO, timeout=5)

    def buildSwapfile(self, result):
        if result is None or result is False:
            pass
        else:
            swapfile = self.swaptarget + '/swapfile'
            if fileExists(swapfile):
                swapoff = 'swapoff ' + swapfile
                system(swapoff)
                unlink(swapfile)
            ddcmd = 'dd if=/dev/zero of=' + swapfile + ' bs=1024k count=' + self.swapsize + ' && echo creating swap signature && mkswap ' + swapfile + ' && echo enable swap && swapon ' + swapfile + ' && free && echo ' + _('swapfile was created successfully')
            socmd = 'swapon ' + swapfile
            self.session.open(Console, title=_('VTI create SwapFile'), cmdlist=[ddcmd])
            self.enableSwap(socmd)

    def enableSwap(self, swapcmd):
        try:
            unlink(swapstarter)
        except:
            pass

        fp = file(swapstarter, 'w')
        fp.write('#!/bin/sh\n')
        fp.write(swapcmd)
        fp.write('\n')
        fp.close()
        chmod(swapstarter, 493)

    def ipkuninstall(self, result):
        if result is None or result is False:
            pass
        else:
            self.session.open(Console, title=_('VTI IPK Uninstall'), cmdlist=['opkg remove ' + package])

    def ipkuninstallforce(self, result):
        if result is None or result is False:
            pass
        else:
            self.session.open(Console, title=_('VTI IPK Uninstall ignore depencies'), cmdlist=['opkg remove -force-depends ' + package])


class CamSelectMenu(Screen):

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
#       checkvu.runcheck()
        self['key_red'] = StaticText(_('Stop Cam'))
        self['key_green'] = StaticText(_('Start Cam'))
        self['key_yellow'] = StaticText(_('Restart Cam'))
        self['key_blue'] = StaticText(_('Manage Cams'))
        self.title = _('Select Cam and press OK to activate')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['actions'] = ActionMap(['ColorActions', 'SetupActions'], {'red': self.redPressed,
         'green': self.greenPressed,
         'yellow': self.yellowPressed,
         'blue': self.bluePressed,
         'ok': self.okPressed,
         'cancel': self.cancel}, -1)
        self.dlg = None
        self.state = {}
        self.list = []
        self.output_line = ''
        self['list'] = List(self.list)
        self.link_target = ''
        self.onShown.append(self.createCAMlist)
        self.onLayoutFinish.append(self.setWindowTitle)
        self.check_camstarter()

    def createCAMlist(self, args = None):
        self.mylist = []
        self.filename = ''
        try:
            self.link_target = readlink(current_cam)
        except:
            self.link_target = ''

        for self.dir in dirlist:
            try:
                for self.filename in listdir(self.dir):
                    self.fullname = self.dir + self.filename
                    if self.filename.endswith('.sh'):
                        for self.idx in searchlist:
                            try:
                                for self.line in open(self.fullname):
                                    self.camname = ''
                                    if self.idx in self.line:
                                        try:
                                            self.overhead, self.camname = self.line.split('=')
                                        except:
                                            break

                                        self.camname = self.camname.replace('"', '').strip()
                                        if self.overhead.strip()[0] != '#' and self.overhead.strip() == self.idx and not self.fullname == current_cam:
                                            if self.camname != '':
                                                if self.link_target == self.fullname:
                                                    self.mylist.append((self.camname, self.fullname, LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/green_ok.png'))))
                                                else:
                                                    self.mylist.append((self.camname, self.fullname, ''))
                                            break

                            except IOError:
                                pass

                    elif self.filename.lower().startswith('softcam') and not self.filename.lower().endswith('none') and self.filename.lower() != 'softcam':
                        self.basename = self.filename.lstrip('softcam')
                        if self.link_target == self.fullname:
                            self.mylist.append((self.basename.lstrip('.'), self.fullname, LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/green_ok.png'))))
                        else:
                            self.mylist.append((self.basename.lstrip('.'), self.fullname, ''))

            except OSError:
                pass

        if len(self.mylist) > 1:
            self.mylist.sort(key=lambda obj: obj[0])
            self['list'].setList(self.mylist)
            if self.link_target != '':
                self['list'].setIndex(find_in_list(self.mylist, self.link_target, 1))
        else:
            self['list'].setList(self.mylist)

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        try:
            self['title'] = StaticText(title)
        except:
            pass

    def okPressed(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            name = cur[0]
            script = cur[1]
            self.stopCam(0)
            try:
                unlink(current_cam)
            except:
                pass

            self.startCam(name, script)

    def redPressed(self):
        try:
            cur = self['list'].getCurrent()
            if cur and len(cur) > 2:
                name = cur[0]
                script = cur[1]
            self.stopCam(name, 1)
        except UnboundLocalError:
            pass

    def greenPressed(self):
        self.okPressed()

    def yellowPressed(self):
        try:
            cur = self['list'].getCurrent()
            if cur and len(cur) > 2:
                name = cur[0]
                script = cur[1]
            self.restartCam(name)
        except UnboundLocalError:
            pass

    def bluePressed(self):
        plugin_prefix = ('enigma2-plugin-cams', 'enigma2-plugin-config')
        self.session.open(myPacketManager, self.skin_path, plugin_prefix)

    def cancel(self):
        self.close()

    def startCam(self, name, script):
        symlink(script, current_cam)
        self.execute_cam('start', name, 1)

    def stopCam(self, name, args = 0):
        if self.link_target != '':
            try:
                self.execute_cam('stop', name, args)
            except:
                pass

    def restartCam(self, name, args = None):
        if self.link_target != '':
            self.execute_cam('restart', name, 1)
        else:
            message = _('NO CAM ACTIVE !!! Cant restart current cam ')
            self.session.openWithCallback(self.createCAMlist, MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    def camInfo(self):
        cur = self['list'].getCurrent()
        if cur and len(cur) > 2:
            name = cur[0]
            script = cur[1]
            message = _('cam info : ') + name + _(' -- ') + script
            self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    def execute_cam(self, status, name, showbox = 0):
        message = ''
        cmd = current_cam + ' ' + status
        system(cmd)
        if status == 'start':
            message = _('Starting cam : ') + ' ' + name
        elif status == 'stop':
            try:
                unlink(current_cam)
                self.link_target = ''
            except:
                pass

            message = _('Stopping cam : ') + ' ' + name
        elif status == 'restart':
            message = _('Restarting cam : ') + ' ' + name
        if showbox == 1:
            self.session.openWithCallback(self.createCAMlist, MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    def check_camstarter(self):
        try:
            unlink('/etc/rcS.d/S98EmuManager')
        except:
            pass

        self.update = 0
        try:
            for line in open(camstarter):
                if 'cardserver' in line or 'softcam' in line:
                    self.update = 1
                    break

        except IOError:
            self.update = 1

        if self.update == 1:
            self.update_camstarter()

    def update_camstarter(self):
        try:
            if readlink(camstarter):
                unlink(camstarter)
        except OSError:
            pass

        fp = file(camstarter, 'w')
        fp.write('#!/bin/sh\n')
        fp.write('/etc/init.d/current_cam.sh start\n')
        fp.write('\n')
        fp.close()
        chmod(camstarter, 493)
        try:
            chmod(current_cam, 493)
        except OSError:
            pass


class BitrateViewer(Screen):

    def __init__(self, session, args = None):
        self.skin_path = plugin_path
        Screen.__init__(self, session)
        self.bitrate = Bitrate(session, self.refreshEvent, self.bitrateStopped)
        self.title = _('Bitrate Viewer')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['cancel'] = Button(_('Exit'))
        self['video'] = StaticText(_('Video'))
        self['audio'] = StaticText(_('Audio'))
        self['min'] = StaticText(_('Min'))
        self['max'] = StaticText(_('Max'))
        self['cur'] = StaticText(_('Current'))
        self['avg'] = StaticText(_('Average'))
        self['vmin'] = Label('')
        self['vmax'] = Label('')
        self['vavg'] = Label('')
        self['vcur'] = Label('')
        self['amin'] = Label('')
        self['amax'] = Label('')
        self['aavg'] = Label('')
        self['acur'] = Label('')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.keyCancel,
         'cancel': self.keyCancel,
         'red': self.keyCancel}, -2)
        self.onShown.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.bitrate.start)

    def refreshEvent(self):
        self['vmin'].setText(self.bitrate.vmin)
        self['vmax'].setText(self.bitrate.vmax)
        self['vavg'].setText(self.bitrate.vavg)
        self['vcur'].setText(self.bitrate.vcur)
        self['amin'].setText(self.bitrate.amin)
        self['amax'].setText(self.bitrate.amax)
        self['aavg'].setText(self.bitrate.aavg)
        self['acur'].setText(self.bitrate.acur)

    def keyCancel(self):
        self.bitrate.stop()
        self.close()

    def bitrateStopped(self, retval):
        self.close()

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        try:
            self['title'] = StaticText(title)
        except:
            print 'self["title"] was not found in skin'


class myPacketManager(Screen):

    def __init__(self, session, plugin_path, wanted_extensions, args = None):
        Screen.__init__(self, session)
        self.session = session
        self.skin_path = plugin_path
        self.wanted_extensions = wanted_extensions
        self['shortcuts'] = ActionMap(['ShortcutActions', 'WizardActions'], {'ok': self.go,
         'back': self.exit,
         'red': self.exit,
         'green': self.reload}, -1)
        self.list = []
        self.statuslist = []
        self['list'] = List(self.list)
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Reload'))
        self.title = _('Download or delete Cam')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.list_updating = True
        self.packetlist = []
        self.installed_packetlist = {}
        self.Console = ComConsole()
        self.cmdList = []
        self.cachelist = []
        self.cache_ttl = 21600
        self.cache_file = '/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/packetmanager.cache'
        self.oktext = _('\nAfter pressing OK, please wait!')
        self.unwanted_extensions = ('-dbg', '-dev', '-doc', 'busybox')
        self.ipkg = IpkgComponent()
        self.ipkg.addCallback(self.ipkgCallback)
        self.onShown.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.rebuildList)
        if self.selectionChanged not in self['list'].onSelectionChanged:
            self['list'].onSelectionChanged.append(self.selectionChanged)

    def exit(self):
        self.ipkg.stop()
        if self.Console is not None:
            if len(self.Console.appContainers):
                for name in self.Console.appContainers.keys():
                    self.Console.kill(name)

        self.close()

    def reload(self):
        if os_path.exists(self.cache_file) == True:
            remove(self.cache_file)
            self.list_updating = True
            self.rebuildList()

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        try:
            self['title'] = StaticText(title)
        except:
            print 'self["title"] was not found in skin'

    def selectionChanged(self):
        current = self['list'].getCurrent()

    def setStatus(self, status = None):
        if status:
            self.statuslist = []
            divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, '750S/div-h.png'))
            if status == 'update':
                statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installable.png'))
                self.statuslist.append((_('Trying to download a new packetlist. Please wait...'),
                 '',
                 _('Package list update'),
                 '',
                 statuspng,
                 divpng))
                self['list'].setList(self.statuslist)
            elif status == 'error':
                statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/remove.png'))
                self.statuslist.append((_('There was an error downloading the packetlist. Please try again.'),
                 '',
                 _('Error'),
                 '',
                 statuspng,
                 divpng))
                self['list'].setList(self.statuslist)

    def rebuildList(self):
        self.setStatus('update')
        self.inv_cache = 0
        self.vc = valid_cache(self.cache_file, self.cache_ttl)
        if self.cache_ttl > 0 and self.vc != 0:
            try:
                self.buildPacketList()
            except:
                self.inv_cache = 1

        if self.cache_ttl == 0 or self.inv_cache == 1 or self.vc == 0:
            self.run = 0
            self.ipkg.startCmd(IpkgComponent.CMD_UPDATE)

    def go(self, returnValue = None):
        cur = self['list'].getCurrent()
        if cur:
            status = cur[3]
            package = cur[0]
            self.cmdList = []
            if status == 'installed':
                self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': package}))
                if len(self.cmdList):
                    self.session.openWithCallback(self.runRemove, MessageBox, _('Do you want to remove the package:\n') + package + '\n' + self.oktext)
            elif status == 'upgradeable':
                self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': package}))
                if len(self.cmdList):
                    self.session.openWithCallback(self.runUpgrade, MessageBox, _('Do you want to upgrade the package:\n') + package + '\n' + self.oktext)
            elif status == 'installable':
                self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': package}))
                if len(self.cmdList):
                    self.session.openWithCallback(self.runUpgrade, MessageBox, _('Do you want to install the package:\n') + package + '\n' + self.oktext)

    def runRemove(self, result):
        if result:
            self.session.openWithCallback(self.runRemoveFinished, Ipkg, cmdList=self.cmdList)

    def runRemoveFinished(self):
        cur = self['list'].getCurrent()
        if cur:
            item = self['list'].getIndex()
            self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'installable')
            self.cachelist[item] = [cur[0],
             cur[1],
             cur[2],
             'installable']
            self['list'].setList(self.list)
            write_cache(self.cache_file, self.cachelist)
            self.reloadPluginlist()

    def runUpgrade(self, result):
        if result:
            self.session.openWithCallback(self.runUpgradeFinished, Ipkg, cmdList=self.cmdList)

    def runUpgradeFinished(self):
        cur = self['list'].getCurrent()
        if cur:
            item = self['list'].getIndex()
            self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'installed')
            self.cachelist[item] = [cur[0],
             cur[1],
             cur[2],
             'installed']
            self['list'].setList(self.list)
            write_cache(self.cache_file, self.cachelist)
            self.reloadPluginlist()

    def ipkgCallback(self, event, param):
        if event == IpkgComponent.EVENT_ERROR:
            self.list_updating = False
            self.setStatus('error')
        elif event == IpkgComponent.EVENT_DONE:
            if self.list_updating:
                self.list_updating = False
                if not self.Console:
                    self.Console = Console()
                cmd = 'opkg list'
                self.Console.ePopen(cmd, self.IpkgList_Finished)

    def IpkgList_Finished(self, result, retval, extra_args = None):
        if len(result):
            self.packetlist = []
            for x in result.splitlines():
                split = x.split(' - ')
                if split[0].strip().startswith(self.wanted_extensions):
                    try:
                        self.packetlist.append([split[0].strip(), split[1].strip(), split[2].strip()])
                    except:
                        pass

        if not self.Console:
            self.Console = Console()
        cmd = 'opkg list-installed'
        self.Console.ePopen(cmd, self.IpkgListInstalled_Finished)

    def IpkgListInstalled_Finished(self, result, retval, extra_args = None):
        if len(result):
            self.installed_packetlist = {}
            for x in result.splitlines():
                split = x.split(' - ')
                if split[0].strip().startswith(self.wanted_extensions):
                    self.installed_packetlist[split[0].strip()] = split[1].strip()

        self.buildPacketList()

    def buildEntryComponent(self, name, version, description, state):
        divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, '750S/div-h.png'))
        if state == 'installed':
            installedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installed.png'))
            return (name,
             version,
             description,
             state,
             installedpng,
             divpng)
        elif state == 'upgradeable':
            upgradeablepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/upgradeable.png'))
            return (name,
             version,
             description,
             state,
             upgradeablepng,
             divpng)
        else:
            installablepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installable.png'))
            return (name,
             version,
             description,
             state,
             installablepng,
             divpng)

    def buildPacketList(self):
        self.list = []
        self.cachelist = []
        if self.cache_ttl > 0 and self.vc != 0:
            try:
                self.cachelist = load_cache(self.cache_file)
                if len(self.cachelist) > 0:
                    for x in self.cachelist:
                        self.list.append(self.buildEntryComponent(x[0], x[1], x[2], x[3]))

                    self['list'].setList(self.list)
            except:
                self.inv_cache = 1

        if self.cache_ttl == 0 or self.inv_cache == 1 or self.vc == 0:
            for x in self.packetlist:
                status = ''
                if self.installed_packetlist.has_key(x[0].strip()):
                    if self.installed_packetlist[x[0].strip()] == x[1].strip():
                        status = 'installed'
                        self.list.append(self.buildEntryComponent(x[0].strip(), x[1].strip(), x[2].strip(), status))
                    else:
                        status = 'upgradeable'
                        self.list.append(self.buildEntryComponent(x[0].strip(), x[1].strip(), x[2].strip(), status))
                else:
                    status = 'installable'
                    self.list.append(self.buildEntryComponent(x[0].strip(), x[1].strip(), x[2].strip(), status))
                if x[0].strip().startswith(self.wanted_extensions):
                    self.cachelist.append([x[0].strip(),
                     x[1].strip(),
                     x[2].strip(),
                     status])

            write_cache(self.cache_file, self.cachelist)
            self['list'].setList(self.list)

    def reloadPluginlist(self):
        plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))


class VTIPasswdScreen(Screen):

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        self.title = _('Change Root Password')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.user = 'root'
        self.output_line = ''
        self.list = []
        self['passwd'] = ConfigList(self.list)
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Set Password'))
        self['key_yellow'] = StaticText(_('new Random'))
        self['key_blue'] = StaticText(_('virt. Keyboard'))
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'red': self.close,
         'green': self.SetPasswd,
         'yellow': self.newRandom,
         'blue': self.bluePressed,
         'cancel': self.close}, -1)
        self.buildList(self.GeneratePassword())
        self.onShown.append(self.setWindowTitle)

    def newRandom(self):
        self.buildList(self.GeneratePassword())

    def buildList(self, password):
        self.password = password
        self.list = []
        self.list.append(getConfigListEntry(_('Enter new Password'), ConfigText(default=self.password, fixed_size=False)))
        self['passwd'].setList(self.list)

    def GeneratePassword(self):
        passwdChars = string.letters + string.digits
        passwdLength = 8
        return ''.join(Random().sample(passwdChars, passwdLength))

    def SetPasswd(self):
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.runFinished)
        self.container.dataAvail.append(self.dataAvail)
        retval = self.container.execute('passwd %s' % self.user)
        if retval == 0:
            self.session.open(MessageBox, _('Sucessfully changed password for root user to:\n%s ' % self.password), MessageBox.TYPE_INFO)
        else:
            self.session.open(MessageBox, _('Unable to change/reset password for root user'), MessageBox.TYPE_ERROR)

    def dataAvail(self, data):
        self.output_line += data
        while True:
            i = self.output_line.find('\n')
            if i == -1:
                break
            self.processOutputLine(self.output_line[:i + 1])
            self.output_line = self.output_line[i + 1:]

    def processOutputLine(self, line):
        if line.find('password: '):
            self.container.write('%s\n' % self.password)

    def runFinished(self, retval):
        del self.container.dataAvail[:]
        del self.container.appClosed[:]
        del self.container
        self.close()

    def bluePressed(self):
        self.session.openWithCallback(self.VirtualKeyBoardTextEntry, VirtualKeyBoard, title=_('Enter your password here:'), text=self.password)

    def VirtualKeyBoardTextEntry(self, callback = None):
        if callback is not None and len(callback):
            self.buildList(callback)

    def setWindowTitle(self, title = None):
        if not title:
            title = self.title
        try:
            self['title'] = StaticText(title)
        except:
            pass


def find_in_list(list, search, listpos = 0):
    index = -1
    for item in list:
        index = index + 1
        if item[listpos] == search:
            return index

    return -1


def write_cache(cache_file, cache_data):
    if not os_path.isdir(os_path.dirname(cache_file)):
        try:
            mkdir(os_path.dirname(cache_file))
        except OSError:
            pass

    fd = open(cache_file, 'w')
    dump(cache_data, fd, -1)
    fd.close()


def valid_cache(cache_file, cache_ttl):
    try:
        mtime = stat(cache_file)[ST_MTIME]
    except:
        return 0

    curr_time = time()
    if curr_time - mtime > cache_ttl:
        return 0
    else:
        return 1


def load_cache(cache_file):
    fd = open(cache_file)
    cache_data = load(fd)
    fd.close()
    return cache_data


def find_in_list(list, search, listpos = 0):
    for item in list:
        if item[listpos] == search:
            return True

    return False


global_session = None

def main(session, **kwargs):
    if fileExists(camstarter):
        chmod(camstarter, 493)
    if not fileExists(current_cam):
        fp = file(current_cam, 'w')
        fp.close()
    session.open(VTIMainMenu)


def news_main(session, **kwargs):
    session.open(AllNews, plugin_path)


def MainMenuSetup(menuid, **kwargs):
    if menuid == 'vtimain':
        return [(_('VTI Panel'),
          main,
          'vti_panel',
          10), (_('Software Update'),
          news_main,
          'vti_panel_news',
          11)]
    else:
        return []


def autostart(reason, **kwargs):
    global baseMenuList__init__
    if baseMenuList__init__ is None:
        baseMenuList__init__ = Menu.__init__
    Menu.__init__ = MenuList__init__


def start_update_notification(reason, **kwargs):
    if config.usage.check_for_updates.value > 0 and kwargs.has_key('session'):
        session = kwargs['session']
        update_notification.setSession(session, plugin_path)
        update_notification.init_timer()


def sortByName(self, listentry):
    return listentry[0].lower()


def MenuList__init__(self, session, parent, *args, **kwargs):
    baseMenuList__init__(self, session, parent, *args, **kwargs)
    if self.menuID == 'mainmenu':
        plugin_list = []
        id_list = []
        for l in plugins.getPlugins([PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_EVENTINFO]):
            l.id = l.name.lower().replace(' ', '_')
            if l.id not in id_list:
                id_list.append(l.id)
                plugin_list.append((l.name,
                 boundFunction(l.__call__, session),
                 l.id,
                 10))

        list = self['menu'].list
        addlist = config.plugins.vtipanel.menushown.value
        addlist = addlist.split(',')
        for entry in plugin_list:
            if entry[2] in addlist:
                list.append(entry)

        removelist = config.plugins.vtipanel.menunotshown.value
        for removeitem in removelist.split(','):
            for item in list:
                if item[2] == 'vti_menu':
                    backupitem = item
                if item[2] == removeitem:
                    list.remove(item)

        if not len(list):
            list.append(backupitem)
        if config.usage.sort_menu_byname.value:
            list.sort(key=self.sortByName)
        else:
            list.sort(key=lambda x: int(x[3]))


def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path
    loadPluginSkin(plugin_path)
    if config.misc.enable_custom_mainmenu.value == True:
        return [PluginDescriptor(name='VTI Panel', description=_('Manage your VU+ Team Image'), icon='plugin.png', where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=main),
         PluginDescriptor(name='VTI Panel', description=_('Manage your VU+ Team Image'), where=[PluginDescriptor.WHERE_MENU], fnc=MainMenuSetup),
         PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=start_update_notification),
         PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)]
    else:
        return [PluginDescriptor(name='VTI Panel', description=_('Manage your VU+ Team Image'), icon='plugin.png', where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=main), PluginDescriptor(name='VTI Panel', description=_('Manage your VU+ Team Image'), where=[PluginDescriptor.WHERE_MENU], fnc=MainMenuSetup), PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=start_update_notification)]
