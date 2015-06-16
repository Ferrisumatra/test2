#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/BackupSuite.py
from Components.Label import Label
from Components.ActionMap import ActionMap, NumberActionMap
from Components.GUIComponent import GUIComponent
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigText, ConfigLocations
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.Harddisk import harddiskmanager
from Components.Console import Console as ComConsole
from Components.Ipkg import IpkgComponent
from Components.Sources.List import List
from Components.PluginComponent import plugins
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Ipkg import Ipkg
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import *
from Tools.HardwareInfoVu import HardwareInfoVu
from time import localtime, mktime, time
from enigma import eServiceReference, eServiceCenter, eDVBDB
from ServiceReference import ServiceReference
from Screens.InfoBar import InfoBar
from Components.NimManager import nimmanager
from skin import loadSkin
#from plugin import checkvu
from os import system, listdir, symlink, unlink, readlink, path as os_path, stat, mkdir, popen, makedirs, access, rename, remove, W_OK, R_OK, F_OK, chmod, walk, getcwd, chdir
from __init__ import _
config.plugins.vtipanel.backupsuite = ConfigSubsection()
config.plugins.vtipanel.backupsuite.backuprestorepath = ConfigText(default='/media/hdd/', visible_width=50, fixed_size=False)

def getBackupRestorePath():
    backuprestorepath = config.plugins.vtipanel.backupsuite.backuprestorepath.value
    if backuprestorepath.endswith('/'):
        returnpath = backuprestorepath + 'vti-backupsuite'
    else:
        returnpath = backuprestorepath + '/vti-backupsuite'
    try:
        if os_path.exists(returnpath) == False:
            makedirs(returnpath)
    except:
        returnpath = None

    return returnpath


def getDateTime():
    time = localtime()
    year = str(time.tm_year)
    month = time.tm_mon
    day = time.tm_mday
    hour = time.tm_hour
    minute = time.tm_min
    if month < 10:
        month = '0' + str(month)
    else:
        month = str(month)
    if day < 10:
        day = '0' + str(day)
    else:
        day = str(day)
    if hour < 10:
        hour = '0' + str(hour)
    else:
        hour = str(hour)
    if minute < 10:
        minute = '0' + str(minute)
    else:
        minute = str(minute)
    datetime = year + month + day + '_' + hour + '-' + minute
    return datetime


class BackupActions:

    def __init__(self, backuptype = None):
        self.executiontime = getDateTime()
        self.boxtype = HardwareInfoVu().get_device_name()
        self.executiontime += '_%s' % self.boxtype
        if backuptype == 'auto':
            self.executiontime += '.auto'

    def createPluginList(self):
        self.path = getBackupRestorePath()
        self.pluginfile = '%s/pluginlist_%s.lst' % (self.path, self.executiontime)
        if fileExists(self.pluginfile):
            cmd = 'rm -f %s' % self.pluginfile
            system(cmd)
        cmd = 'opkg list-installed | grep enigma2-plugin | cut -d " " -f 1 >> %s' % self.pluginfile
        system(cmd)
        if fileExists(self.pluginfile):
            return True
        else:
            return False

    def createSettingFile(self):
        self.path = getBackupRestorePath()
        self.settingfile = '%s/settings_%s.tar.gz' % (self.path, self.executiontime)
        if fileExists(self.settingfile):
            cmd = 'rm -f %s' % self.settingfile
            system(cmd)
        cmd = 'tar czf %s /etc/enigma2/*.tv /etc/enigma2/*.radio /etc/enigma2/whitelist /etc/enigma2/blacklist /etc/enigma2/lamedb /etc/tuxbox/satellites.xml /etc/tuxbox/terrestrial.xml /etc/tuxbox/cables.xml' % self.settingfile
        system(cmd)
        if fileExists(self.settingfile):
            return True
        else:
            return False

    def createConfigFile(self):
        self.path = getBackupRestorePath()
        self.configfile = '%s/configuration_ver_a_%s.tar.gz' % (self.path, self.executiontime)
        configplaces = ['/etc/enigma2/*',
         '/etc/CC*',
         '/usr/scam/*',
         '/etc/tuxbox/config/*',
         '/usr/keys/*',
         '/etc/ConfFS/*',
         '/usr/lib/enigma2/python/Plugins/Extensions/webradioFS/skin/mySkin/*',
         '/etc/MultiQuickButton/*',
         '/usr/lib/enigma2/python/Plugins/Extensions/Foreca/*.cfg',
         '/usr/lib/enigma2/python/Plugins/Extensions/SHOUTcast/favorites',
         '/etc/samba/*',
         '/etc/hostname',
         '/etc/passwd',
         '/etc/shadow',
         '/etc/exports',
         '/etc/fstab',
         '/etc/auto.network',
         '/etc/network/interfaces',
         '/etc/resolv.conf',
         '/etc/wpa_supplicant*.conf',
         '/usr/share/enigma2/radio.mvi',
         '/usr/share/vuplus-bootlogo/*',
         '/.qws/share/data/Arora/*',
         '/Settings/*',
         '/usr/lib/enigma2/python/Plugins/SystemPlugins/PiPServiceRelation/psr_config',
         '/usr/lib/enigma2/python/Plugins/SystemPlugins/CrashReport/settings',
         '/usr/lib/enigma2/python/Plugins/Extensions/HbbTV/bookmark.ini',
         '/etc/init.d/current_cam.sh',
         '/usr/share/enigma2/skin_default/spinner/wait*png']
        configexcludes = ['etc/enigma2/*.tv',
         'etc/enigma2/*.radio',
         'etc/enigma2/whitelist',
         'etc/enigma2/blacklist',
         'etc/enigma2/lamedb',
         'etc/tuxbox/config/enigma*',
         'etc/enigma2/*.pem',
         'etc/enigma2/profile']
        if fileExists(self.configfile):
            cmd = 'rm -f %s' % self.configfile
            system(cmd)
        cmd = 'tar czf %s' % self.configfile
        for configplace in configplaces:
            cmd += ' ' + configplace

        for configexclude in configexcludes:
            cmd += ' --exclude ' + configexclude

        system(cmd)
        configplaces = []
        configplaces.extend(self.saveAtileUserFiles())
        if len(configplaces):
            cmd = 'tar czf %s_atile_hd' % self.configfile
            for configplace in configplaces:
                cmd += ' ' + configplace

            system(cmd)
        if fileExists(self.configfile):
            return True
        else:
            return False

    def saveAtileUserFiles(self):
        package_info = '/var/lib/opkg/info/enigma2-plugin-extensions-atilehd.list'
        start_strings = ('/usr/share/enigma2/AtileHD/colors_atile_', '/usr/share/enigma2/AtileHD/font_atile_', '/usr/share/enigma2/AtileHD/allScreens/skin_', '/usr/share/enigma2/AtileHD/preview/preview_')
        search_dirs = ('/usr/share/enigma2/AtileHD', '/usr/share/enigma2/AtileHD/allScreens', '/usr/share/enigma2/AtileHD/preview')
        package_files = []
        user_files = []
        if fileExists(package_info):
            with open(package_info) as f:
                content = f.readlines()
            for f in content:
                for string in start_strings:
                    if f.startswith(string):
                        package_files.append(f.strip())
                        break

            for folder in search_dirs:
                if os_path.exists(folder):
                    files = self.listdir_fullpath(folder)
                    for f in files:
                        for string in start_strings:
                            if f.startswith(string):
                                if f not in package_files:
                                    user_files.append(f)
                                break

        return user_files

    def listdir_fullpath(self, d):
        return [ os_path.join(d, f) for f in listdir(d) ]

    def houseKeeping(self):
        flist = []
        path = getBackupRestorePath()
        if path:
            for file in listdir(path):
                if file.startswith('pluginlist') and file.endswith(self.boxtype + '.auto.lst'):
                    flist.append(file)
                elif file.startswith('settings') and file.endswith(self.boxtype + '.auto.tar.gz'):
                    flist.append(file)
                elif file.startswith('configuration') and file.endswith(self.boxtype + '.auto.tar.gz'):
                    flist.append(file)
                elif file.startswith('configuration') and file.endswith(self.boxtype + '.auto.tar.gz_atile_hd'):
                    flist.append(file)

            if len(flist):
                flist.sort(reverse=True)
                rm_flist = []
                for file_type in ('settings', 'configuration', 'pluginlist'):
                    erase_counter = 0
                    for rm_file in flist:
                        if rm_file.startswith(file_type):
                            if not rm_file.endswith('_atile_hd'):
                                erase_counter += 1
                                if erase_counter >= 4:
                                    rm_flist.append(rm_file)
                                    atile_file = rm_file + '_atile_hd'
                                    rm_flist.append(atile_file)

                if len(rm_flist):
                    for rm_file in rm_flist:
                        rm_file = path + '/' + rm_file
                        if os_path.exists(rm_file):
                            remove(rm_file)
                            print '[VTi BackupSuite] Housekeeping --> remove file %s' % rm_file


class BackupSuiteHelpScreen(Screen):
    skin = '\n\t\t<screen name="BackupSuiteHelpScreen" position="center,center" size="650,250">\n\t\t\t<widget name="messagetext" position="10,10" size="630,210"  font="Regular;20" halign="center" valign="center" transparent="1" />\n\t\t\t<widget source="key_red" render="Label" position="40,213" zPosition="1" size="150,40" font="Regular;20" halign="left" valign="center" transparent="1" />\n\t\t\t<widget source="key_green" render="Label" position="225,213" zPosition="1" size="150,40" font="Regular;20" halign="left" valign="center" transparent="1" />\n\t\t\t<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/pictures/button_red.png" position="10,220"  size="25,25" alphatest="on" />\n\t\t\t<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/pictures/button_green.png" position="195,220" size="25,25" alphatest="on" />\n\t\t</screen>\n\t'

    def __init__(self, session, restorefile, fullrestorepath):
        Screen.__init__(self, session)
        self.session = session
        self.restorefile = restorefile
        self.fullrestorepath = fullrestorepath
        self.title = 'VTi BackupSuite'
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['messagetext'] = Label()
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Ok'))
        self['shortcuts'] = ActionMap(['OkCancelActions', 'ColorActions'], {'red': self.keyClose,
         'green': self.keyGo,
         'ok': self.keyGo,
         'cancel': self.keyClose}, -2)
        self.onLayoutFinish.append(self.createMessage)

    def createMessage(self):
        msg = _('Are you sure you want to restore\nfollowing backup:\n') + self.restorefile + '\n\n' + _('\nSystem will restart after the restore!')
        self['messagetext'].setText(msg)

    def keyGo(self):
        cmdlist = []
        if self.fullrestorepath.find('configuration_ver_a') == -1:
            print '[VTi BackupSuite] do not restore old OE tree configuration files'
            cmdlist.append('cat /etc/fstab > /etc/fstab_backup')
            cmdlist.append('cat /etc/passwd > /etc/passwd_backup')
        cmdlist.append('mkdir -p /usr/share/enigma2/skin_default/spinner/tmp')
        cmdlist.append('mv /usr/share/enigma2/skin_default/spinner/*.png /usr/share/enigma2/skin_default/spinner/tmp')
        cmdlist.append('/etc/init.d/current_cam.sh stop ; tar -xzf %s -C /' % self.fullrestorepath)
        atilefile = self.fullrestorepath + '_atile_hd'
        if fileExists(atilefile):
            cmdlist.append('tar -xzf %s -C /' % atilefile)
        cmdlist.append('if [ ! -f /usr/share/enigma2/skin_default/spinner/wait1.png ] ; then  mv /usr/share/enigma2/skin_default/spinner/tmp/*.png /usr/share/enigma2/skin_default/spinner ; fi ; rm -rf /usr/share/enigma2/skin_default/spinner/tmp')
        cmdlist.append('rm -rf /.qws')
        cmdlist.append('if [ ! -L "/etc/resolv.conf" ] ; then rm /var/run/resolv.conf ; mv /etc/resolv.conf /var/run/resolv.conf ; ln -s /var/run/resolv.conf /etc/resolv.conf ; fi')
        if self.fullrestorepath.find('configuration_ver_a') == -1:
            cmdlist.append('cat /etc/fstab_backup > /etc/fstab ; rm /etc/fstab_backup')
            cmdlist.append('cat /etc/passwd_backup > /etc/passwd ; rm /etc/passwd_backup')
            cmdlist.append('chmod -x /etc/auto.network')
        if fileExists('/proc/stb/vmpeg/0/dst_width'):
            cmdlist.append('echo 00000000 > /proc/stb/vmpeg/0/dst_height')
            cmdlist.append('echo 00000000 > /proc/stb/vmpeg/0/dst_left')
            cmdlist.append('echo 00000000 > /proc/stb/vmpeg/0/dst_top')
            cmdlist.append('echo 00000000 > /proc/stb/vmpeg/0/dst_width')
        cmdlist.append('/etc/init.d/networking stop ; /etc/init.d/networking start ; /etc/init.d/current_cam.sh start ; killall -9 enigma2')
        for cmd in cmdlist:
            system(cmd)

    def keyClose(self):
        self.close()


class BackupSuite(Screen):

    def __init__(self, session, plugin_path, screen_type = 'backup'):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.session = session
#       checkvu.runcheck()
        self.screentype = screen_type
        self.reloadPluginlist = False
        self.title = _('VTI BackupSuite')
        self.backupactions = BackupActions('manual')
        if self.screentype == 'restore':
            self.screentype = 'restore'
            self.title += ' (' + _('Restore') + ')'
        else:
            self.screentype = 'backup'
            self.title += ' (' + _('Backup') + ')'
        self['key_green'] = StaticText('')
        self['key_yellow'] = StaticText('')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.list = []
        self['menu'] = List(self.list)
        self['status'] = Label()
        self['key_red'] = StaticText(_('Exit'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'DirectionActions'], {'ok': self.runMenuEntry,
         'cancel': self.keyCancel,
         'red': self.keyCancel}, -2)
        self.cmdList = []
        self.Console = ComConsole()
        self.ipkg = IpkgComponent()
        self.ipkg.addCallback(self.ipkgCallback)
        self.onLayoutFinish.append(self.createMenu)

    def createMenu(self):
        self.list = []
        self.list.append(('path',
         _('Backup/restore device : %s') % config.plugins.vtipanel.backupsuite.backuprestorepath.value,
         _('set device for directory vti-backupsuite'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/backuplocation.png')),
         None))
        if self.screentype == 'backup':
            self.list.append(('createpluginlist',
             _('Backup installed plugins'),
             _('creates a list of installed plugins, skins and softcams'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/services.png')),
             None))
            self.list.append(('settingbackup',
             _('Backup channel settings'),
             _('save channel and bouquet settings'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None))
            self.list.append(('configbackup',
             _('Backup configurations'),
             _('save common configurations for GUI, plugins and softcams'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/filesys.png')),
             None))
        elif self.screentype == 'restore':
            self.list.append(('installpluginlist',
             _('Restore plugins from saved list'),
             _('installs all available plugins from online feed'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/services.png')),
             None))
            self.list.append(('settingrestore',
             _('Restore channel settings'),
             _('reload saved channel and bouquet settings'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None))
            self.list.append(('configrestore',
             _('Restore configurations'),
             _('restore common configurations for GUI, plugins and softcams'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/filesys.png')),
             None))
            self.list.append(('installlocalplugin',
             _('Install local packages'),
             _('from %s/vti-backupsuite/plugins') % config.plugins.vtipanel.backupsuite.backuprestorepath.value,
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/targz.png')),
             None))
        self.list.append(('personalscript',
         _('Run personal script'),
         _('executes your personal backup/restore scripts'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/exemanager.png')),
         None))
        self['menu'].setList(self.list)

    def runMenuEntry(self, ret = None):
        menuselection = self['menu'].getCurrent()[0]
        if menuselection is not None:
            if menuselection is 'path':
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
                    msg = self.session.openWithCallback(self.backuprestorepath_choosen, ChoiceBox, title=_('Please select medium to use as backup location'), list=locations)
                    msg.setTitle(_('VTI BackupSuite'))
            elif menuselection is 'createpluginlist':
                if self.backupactions.createPluginList() == True:
                    msg = self.session.open(MessageBox, _('List of installed plugins was created succesfully'), MessageBox.TYPE_INFO, timeout=10)
                    msg.setTitle(_('VTI BackupSuite'))
                else:
                    msg = self.session.open(MessageBox, _('Creating list of installed plugins failed'), MessageBox.TYPE_ERROR, timeout=10)
                    msg.setTitle(_('VTI BackupSuite'))
            elif menuselection is 'installpluginlist':
                self.reloadPluginlist = True
                self.restoretype = 'plugininstall'
                self.session.open(BackupSuiteRestore, self.restoretype, self.skin_path)
            elif menuselection is 'settingbackup':
                if self.backupactions.createSettingFile() == True:
                    msg = self.session.open(MessageBox, _('Settings backup finished succesfully'), MessageBox.TYPE_INFO, timeout=10)
                    msg.setTitle(_('VTI BackupSuite'))
                else:
                    msg = self.session.open(MessageBox, _('Backup settings failed'), MessageBox.TYPE_ERROR, timeout=10)
                    msg.setTitle(_('VTI BackupSuite'))
            elif menuselection is 'settingrestore':
                self.restoretype = 'settingrestore'
                self.session.open(BackupSuiteRestore, self.restoretype, self.skin_path)
            elif menuselection is 'installlocalplugin':
                self.restoretype = 'installlocalplugin'
                self.ipkg.startCmd(IpkgComponent.CMD_UPDATE)
            elif menuselection is 'configbackup':
                if self.backupactions.createConfigFile() == True:
                    msg = self.session.open(MessageBox, _('Common configuration backup finished succesfully'), MessageBox.TYPE_INFO, timeout=10)
                    msg.setTitle(_('VTI BackupSuite'))
                else:
                    msg = self.session.open(MessageBox, _('Backup of common configurations failed'), MessageBox.TYPE_ERROR, timeout=10)
                    msg.setTitle(_('VTI BackupSuite'))
            elif menuselection is 'configrestore':
                self.restoretype = 'configrestore'
                self.session.open(BackupSuiteRestore, self.restoretype, self.skin_path)
            elif menuselection is 'personalscript':
                self.restoretype = 'personalscript'
                self.session.open(BackupSuiteRestore, self.restoretype, self.skin_path)

    def installLocalPlugins(self):
        self.path = getBackupRestorePath()
        if self.path:
            self.ipklist = []
            self.pluginsinstalled = []
            self.pluginsinstalledclean = []
            self.pluginsinstalled = popen('opkg list-installed | grep enigma2-plugin | cut -d " " -f 1').readlines()
            for plugininstalled in self.pluginsinstalled:
                self.pluginsinstalledclean.append(plugininstalled.rstrip('\n'))

            self.path += '/plugins'
            if os_path.exists(self.path):
                for file in listdir(self.path):
                    if file.endswith('.ipk'):
                        self.ipklist.append(self.path + '/' + file)

                for localplugin in self.ipklist:
                    package = localplugin
                    if package not in self.pluginsinstalledclean:
                        self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': package}))
                    else:
                        print '[VTI-BackupSuite] Plugin %s is already installed' % package

                if self.cmdList:
                    self.session.open(Ipkg, cmdList=self.cmdList)
        else:
            self.session.open(MessageBox, _('Sorry, your backup destination is not writeable.\n\nPlease choose another one.'), MessageBox.TYPE_INFO, timeout=10)

    def ipkgCallback(self, event, param):
        if event == IpkgComponent.EVENT_ERROR:
            self.setStatus('error')
        elif event == IpkgComponent.EVENT_DONE:
            if self.restoretype == 'installlocalplugin':
                self.restoretype = ''
                self.installLocalPlugins()

    def backuprestorepath_choosen(self, option):
        if option is not None:
            config.plugins.vtipanel.backupsuite.backuprestorepath.value = str(option[1])
        config.plugins.vtipanel.backupsuite.backuprestorepath.save()
        config.plugins.vtipanel.backupsuite.save()
        config.save()
        self.checkFolders()

    def checkFolders(self):
        self.backuprestorepath = getBackupRestorePath()
        if not self.backuprestorepath:
            self.session.open(MessageBox, _('Sorry, your backup destination is not writeable.\n\nPlease choose another one.'), MessageBox.TYPE_INFO, timeout=10)
        self.createMenu()

    def keyCancel(self):
        if self.reloadPluginlist:
            plugins.clearPluginList()
            plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
        self.close(True)


class BackupSuiteRestore(Screen):

    def __init__(self, session, restoretype, plugin_path):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.restoretype = restoretype
        self.title = _('VTI BackupSuite')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Install'))
        self['key_yellow'] = StaticText(_('Delete'))
        self.sel = []
        self.val = []
        self.entry = False
        self.exe = False
        self.path = ''
        self['actions'] = NumberActionMap(['SetupActions'], {'ok': self.KeyOk,
         'cancel': self.keyCancel}, -1)
        self['shortcuts'] = ActionMap(['ShortcutActions'], {'red': self.keyCancel,
         'green': self.KeyOk,
         'yellow': self.deleteFile})
        self.flist = []
        self['filelist'] = MenuList(self.flist)
        self.fill_list()
        self.cmdList = []
        self.Console = ComConsole()
        self.ipkg = IpkgComponent()
        self.ipkg.addCallback(self.ipkgCallback)

    def fill_list(self):
        self.flist = []
        self.path = getBackupRestorePath()
        boxtypes = ('solo', 'duo', 'uno', 'ultimo', 'solo2', 'duo2', 'solose', 'zero')
        boxtype = HardwareInfoVu().get_device_name()
        if self.path:
            for file in listdir(self.path):
                show_file = True
                for box in boxtypes:
                    if file.find('_' + box + '.') != -1:
                        if box == boxtype:
                            show_file = True
                        else:
                            show_file = False
                        break

                if file.startswith('pluginlist') and file.endswith('.lst') and self.restoretype == 'plugininstall' and show_file:
                    self.flist.append(file)
                    self.entry = True
                elif file.startswith('settings') and file.endswith('.tar.gz') and self.restoretype == 'settingrestore' and show_file:
                    self.flist.append(file)
                    self.entry = True
                elif file.startswith('configuration') and file.endswith('.tar.gz') and self.restoretype == 'configrestore' and show_file:
                    self.flist.append(file)
                    self.entry = True
                elif file.startswith(('backup', 'restore')) and file.endswith('.sh') and self.restoretype == 'personalscript' and show_file:
                    self.flist.append(file)
                    self['key_green'] = StaticText(_('Start'))
                    self.entry = True

            self.flist.sort(reverse=True)
            self['filelist'].l.setList(self.flist)

    def KeyOk(self):
        if self.exe == False and self.entry == True:
            self.sel = self['filelist'].getCurrent()
            self.val = self.path + '/' + self.sel
            if self.restoretype == 'plugininstall':
                self.ipkg.startCmd(IpkgComponent.CMD_UPDATE)
            elif self.restoretype == 'settingrestore':
                if self.restoreSettings() == True:
                    self.session.openWithCallback(self.keyCancel, MessageBox, _('Restoring settings finished successfully'), MessageBox.TYPE_INFO, timeout=10)
                else:
                    self.session.open(MessageBox, _('Restoring settings failed'), MessageBox.TYPE_ERROR, timeout=10)
            elif self.restoretype == 'configrestore':
                self.session.open(BackupSuiteHelpScreen, self.sel, self.val)
            elif self.restoretype == 'personalscript':
                msg = self.session.openWithCallback(self.runScript, MessageBox, _('Are you sure you want to run\nfollowing script:\n') + self.sel)
                msg.setTitle(_('VTI BackupSuite'))

    def restoreSettings(self):
        filestodelete = ['/etc/enigma2/*.tv',
         '/etc/enigma2/*.radio',
         '/etc/enigma2/whitelist',
         '/etc/enigma2/blacklist',
         '/etc/enigma2/lamedb',
         '/etc/tuxbox/satellites.xml',
         '/etc/tuxbox/terrestrial.xml',
         '/etc/tuxbox/cables.xml']
        for deletefile in filestodelete:
            cmd = 'rm -f %s' % deletefile
            system(cmd)

        cmd = 'tar xzf %s -C /' % self.val
        system(cmd)
        try:
            nimmanager.readTransponders()
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            infoBarInstance = InfoBar.instance
            if infoBarInstance is not None:
                servicelist = infoBarInstance.servicelist
                root = servicelist.getRoot()
                currentref = servicelist.getCurrentSelection()
                servicelist.setRoot(root)
                servicelist.setCurrentSelection(currentref)
            return True
        except:
            return False

    def runScript(self, ret = False):
        if ret == True:
            chmod(self.val, 493)
            self.cmdlist = [self.path + '/./' + self.sel]
            self.session.openWithCallback(self.keyCancel, Console, title=_('VTI BackupSuite is running personal script ...'), cmdlist=self.cmdlist)

    def keyCancel(self, ret = False):
        self.close()

    def startRestore(self, ret = False):
        if ret == True:
            self.exe = True
            self.session.open(Console, title=_('Restore running'), cmdlist=['tar -xzf ' + self.path + '/' + self.sel + ' -C /', 'killall -9 enigma2'])

    def deleteFile(self):
        if self.exe == False and self.entry == True:
            self.sel = self['filelist'].getCurrent()
            self.val = self.path + '/' + self.sel
            self.session.openWithCallback(self.startDelete, MessageBox, _('Are you sure you want to delete\nfollowing backup:\n' + self.sel))

    def startDelete(self, ret = False):
        if ret == True:
            self.exe = True
            if os_path.exists(self.val) == True:
                remove(self.val)
            self.exe = False
            self.fill_list()

    def installPlugins(self):
        listfile = self.val
        self.plugins = []
        self.cmdList = []
        self.pluginsinstalled = []
        self.pluginsinstalledclean = []
        self.pluginsinstalled = popen('opkg list-installed | grep enigma2-plugin | cut -d " " -f 1').readlines()
        for plugininstalled in self.pluginsinstalled:
            self.pluginsinstalledclean.append(plugininstalled.rstrip('\n'))

        self.plugins = popen('cat %s' % listfile).readlines()
        self.excludedplugins = ['enigma2-plugin-extensions-webbrowser', 'enigma2-plugin-systemplugins-factorytest']
        for plugin in self.plugins:
            package = plugin.rstrip('\n')
            if package not in self.pluginsinstalledclean:
                if package.startswith('enigma2-plugin-settings') or package in self.excludedplugins:
                    print '[VTI-BackupSuite] do not restore excluded package: %s' % package
                else:
                    self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': package}))
            else:
                print '[VTI-BackupSuite] Plugin %s is already installed' % package

        self.session.openWithCallback(self.keyCancel, Ipkg, cmdList=self.cmdList)

    def ipkgCallback(self, event, param):
        if event == IpkgComponent.EVENT_ERROR:
            self.setStatus('error')
        elif event == IpkgComponent.EVENT_DONE:
            if self.restoretype == 'plugininstall':
                self.restoretype = ''
                self.installPlugins()
