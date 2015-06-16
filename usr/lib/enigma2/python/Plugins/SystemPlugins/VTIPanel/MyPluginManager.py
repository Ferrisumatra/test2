# 2015.06.16 12:46:31 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/MyPluginManager.py
from Components.ActionMap import ActionMap
from Components.Console import Console as ComConsole
from Components.GUIComponent import GUIComponent
from Components.Ipkg import IpkgComponent
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.PluginList import *
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from cPickle import dump, load
from os import system, path as os_path, stat, mkdir, remove, statvfs
#from plugin import checkvu
from Screens.Ipkg import Ipkg
from Screens.MessageBox import MessageBox
from Screens.PluginBrowser import *
from Screens.Screen import Screen
from skin import loadSkin
from stat import ST_MTIME
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import *
from time import time
from __init__ import _
import Screens.Standby

class MyPluginManager(Screen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.session = session
        self.skin_path = plugin_path
        self.wanted_extensions_base = ('enigma2', 'kernel-module')
        self.wanted_extensions = self.wanted_extensions_base
        self['shortcuts'] = ActionMap(['ShortcutActions', 'WizardActions'], {'ok': self.go,
         'back': self.exit,
         'red': self.exit,
         'green': self.reloadinfo,
         'yellow': self.doInstall}, -1)
        self.list = []
        self.statuslist = []
        self['list'] = List(self.list)
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = Label()
        self['key_green'].setText(_('reload package data'))
        self['key_yellow'] = Label()
        self['key_yellow'].setText('')
        self.title = _('Download or delete Software')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.start_vc = 0
        self.list_updating = True
        self.plugin_list_state = False
        self.first_run = True
        self.replacename = None
        self.greenpressed = False
        self.packetlist = []
        self.installed_packetlist = {}
        self.Console = ComConsole()
        self.cmdList = []
        self.changeList = []
        self.changed = False
        self.doSoftwareAction = False
        self.opkgupdated = False
        self.upgradablelist = []
        self.cachelist = []
        self.cache_ttl = 21600
        self.cache_file = '/tmp/packetsoftwaremanager.cache'
        self.oktext = _('\nAfter pressing OK, please wait!')
        self.unwanted_extensions = ('-dbg', '-dev', '-doc', 'busybox')
        self.ipkg = IpkgComponent()
        self.ipkg.addCallback(self.ipkgCallback)
        self.onShown.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.rebuildList)
        if self.selectionChanged not in self['list'].onSelectionChanged:
            self['list'].onSelectionChanged.append(self.selectionChanged)

    def getFreeSpace(self, mountpoint):
        if mountpoint:
            stat_info = statvfs(mountpoint)
            free_flash_space = stat_info.f_bfree * stat_info.f_bsize
            return free_flash_space

    def checkFreeSpace(self):
        free_flash_space = self.getFreeSpace('/')
        if free_flash_space < 8000000:
            human_free_space = free_flash_space / 1048576
            msg = _('There are only %d MB free FLASH space available\nInstalling or updating software can cause serious software problems !\nContinue installing/updating software (at your own risk) ?') % human_free_space
            self.session.openWithCallback(self.cbSpaceCheck, MessageBox, msg)

    def cbSpaceCheck(self, result):
        if not result:
            if os_path.exists(self.cache_file) == True:
                remove(self.cache_file)
            self.close()

    def exit(self):
        self.ipkg.stop()
        if self.Console is not None:
            if len(self.Console.appContainers):
                for name in self.Console.appContainers.keys():
                    self.Console.kill(name)

        if self.plugin_list_state == True and self.doSoftwareAction == False:
            self.setStatus('startmenu')
        elif self.plugin_list_state == True and self.doSoftwareAction == True:
            self['list'].setList(self.list)
        elif self.plugin_list_state == False and self.doSoftwareAction == True:
            self.setStatus('startmenu')
        else:
            if os_path.exists(self.cache_file) == True:
                remove(self.cache_file)
            self.reloadPluginlist()
            self.close()
        self.doSoftwareAction = False
        if len(self.cmdList):
            self['key_yellow'].setText(_('Excecute'))

    def reloadinfo(self):
        if self.plugin_list_state == True:
            self.greenpressed = True
            self.go()
        else:
            self.replacename = None
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
        if self.plugin_list_state == True:
            current = self['list'].getCurrent()
            if current:
                if current[3] == 'installed':
                    self['key_green'].setText(_('Remove'))
                elif current[3] == 'installable':
                    self['key_green'].setText(_('Install'))
                elif current[3] == 'upgradeable':
                    self['key_green'].setText(_('Upgrade'))
            else:
                self['key_green'].setText('')
        elif self.doSoftwareAction == False:
            self['key_green'].setText(_('reload package data'))

    def setStatus(self, status = None):
        if status:
            self.statuslist = []
            self.plugin_list_state = False
            divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, '750S/div-h.png'))
            if status == 'update':
                statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installable.png'))
                self.statuslist.append((_('Package list update'),
                 '',
                 _('Trying to download a new packetlist. Please wait...'),
                 '',
                 statuspng,
                 divpng))
                self['list'].setList(self.statuslist)
            elif status == 'error':
                statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/remove.png'))
                self.statuslist.append((_('Error'),
                 '',
                 _('There was an error downloading the packetlist. Please try again.'),
                 '',
                 statuspng,
                 divpng))
                self['list'].setList(self.statuslist)
            elif status == 'startmenu':
                self.statuslist.append((_('Extensions'),
                 '',
                 _('install/remove common plugins'),
                 'extensions',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_plugin.png')),
                 divpng))
                self.statuslist.append((_('Systemplugins'),
                 '',
                 _('install/remove systemplugins'),
                 'systemplugins',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_systemplugin.png')),
                 divpng))
                self.statuslist.append((_('Skins'),
                 '',
                 _('install/remove skins to change look of OSD'),
                 'skins',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_skin.png')),
                 divpng))
                self.statuslist.append((_('SoftCams'),
                 '',
                 _('install/remove softcams'),
                 'softcams',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_softcam.png')),
                 divpng))
                self.statuslist.append((_('Configurations'),
                 '',
                 _('install/remove configuration files for softcams'),
                 'configs',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_softcam_config.png')),
                 divpng))
                self.statuslist.append((_('Picons'),
                 '',
                 _('install/remove picons for OSD and graphical VFD'),
                 'picons',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_picon.png')),
                 divpng))
                self.statuslist.append((_('Settings'),
                 '',
                 _('install/remove channel lists'),
                 'settings',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_channel.png')),
                 divpng))
                self.statuslist.append((_('Kernel modules'),
                 '',
                 _('install/remove kernel modules'),
                 'kernel',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_kernel.png')),
                 divpng))
                self.statuslist.append((_('Language packages'),
                 '',
                 _('install/remove language packages for dvbapp2'),
                 'locale',
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sm_world.png')),
                 divpng))
                self['list'].setList(self.statuslist)

    def rebuildList(self):
        self.changed = False
        self.cmdList = []
        self.changeList = []
        self.upgradablelist = []
        self['key_yellow'].setText('')
        self.setStatus('update')
        self.inv_cache = 0
        if self.start_vc != 0:
            self.vc = valid_cache(self.cache_file, self.cache_ttl)
        else:
            self.vc = 0
        if self.cache_ttl > 0 and self.vc != 0:
            try:
                self.buildPacketList()
            except:
                self.inv_cache = 1

        if self.cache_ttl == 0 or self.inv_cache == 1 or self.vc == 0:
            self.run = 0
            self.wanted_extensions = self.wanted_extensions_base
            self.ipkg.startCmd(IpkgComponent.CMD_UPDATE)

    def go(self, returnValue = None):
        cur = self['list'].getCurrent()
        self.submenulist = ('systemplugins', 'extensions', 'skins', 'picons', 'settings', 'softcams', 'configs', 'drivers', 'kernel', 'locale')
        if cur:
            if self.doSoftwareAction == True:
                if self.greenpressed == True:
                    self.greenpressed = False
                    self.runInstall()
            elif cur[3] in self.submenulist:
                self.plugin_list_state = True
                if cur[3] == 'systemplugins':
                    self.wanted_extensions = 'enigma2-plugin-systemplugins-'
                elif cur[3] == 'extensions':
                    self.wanted_extensions = 'enigma2-plugin-extensions-'
                elif cur[3] == 'kernel':
                    self.wanted_extensions = 'kernel-module-'
                elif cur[3] == 'skins':
                    self.wanted_extensions = 'enigma2-plugin-skin-'
                elif cur[3] == 'picons':
                    self.wanted_extensions = 'enigma2-plugin-picons-'
                elif cur[3] == 'settings':
                    self.wanted_extensions = 'enigma2-plugin-settings-'
                elif cur[3] == 'softcams':
                    self.wanted_extensions = 'enigma2-plugin-cams-'
                elif cur[3] == 'configs':
                    self.wanted_extensions = 'enigma2-plugin-config-'
                elif cur[3] == 'drivers':
                    self.wanted_extensions = 'enigma2-plugin-drivers-'
                elif cur[3] == 'locale':
                    self.wanted_extensions = 'enigma2-locale-'
                self.replacename = self.wanted_extensions
                self.vc = valid_cache(self.cache_file, self.cache_ttl)
                self.buildPacketList()
                self.setStatus(None)
            else:
                status = cur[3]
                if self.replacename is not None:
                    package = self.wanted_extensions + cur[0]
                else:
                    package = cur[0]
                if status == 'upgradeable':
                    self.upgradablelist.append(package)
                self.changecmdList = True
                item = self['list'].getIndex()
                curcache = [package,
                 cur[1],
                 cur[2],
                 cur[3]]
                for cmdListitem in self.cmdList:
                    if str(cmdListitem).find(package) != -1:
                        self.cmdList.remove(cmdListitem)
                        self.changecmdList = False

                if package in self.upgradablelist:
                    self.changecmdList = True
                if package in self.changeList:
                    self.changeList.remove(package)
                    self.changed = False
                else:
                    self.changeList.append(package)
                    self.changed = True
                if status == 'installed':
                    if self.changed == True or package in self.upgradablelist:
                        self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'goremove')
                    else:
                        self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'installable')
                    try:
                        cacheindex = self.cachelist.index(curcache)
                        self.cachelist[cacheindex] = [package,
                         cur[1],
                         cur[2],
                         'installable']
                    except:
                        print '[VTI SoftwareManager] failed to modify packetcachefile'

                    self['key_green'].setText(_('Install'))
                    if self.changecmdList == True:
                        expert_args = ''
                        if config.usage.use_rm_force_depends.value:
                            expert_args = '--force-depends '
                        if config.usage.use_rm_autoremove.value:
                            expert_args += '--autoremove '
                        self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': expert_args + package}))
                elif status == 'upgradeable':
                    if self.changed == True:
                        self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'goinstalled')
                    else:
                        self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'installed')
                    try:
                        cacheindex = self.cachelist.index(curcache)
                        self.cachelist[cacheindex] = [package,
                         cur[1],
                         cur[2],
                         'installed']
                    except:
                        print '[VTI SoftwareManager] failed to modify packetcachefile'

                    self['key_green'].setText(_('Remove'))
                    if self.changecmdList == True:
                        self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': package}))
                elif status == 'installable':
                    if self.changed == True:
                        self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'goinstalled')
                    else:
                        self.list[item] = self.buildEntryComponent(cur[0], cur[1], cur[2], 'installed')
                    try:
                        cacheindex = self.cachelist.index(curcache)
                        self.cachelist[cacheindex] = [package,
                         cur[1],
                         cur[2],
                         'installed']
                    except:
                        print '[VTI SoftwareManager] failed to modify packetcachefile'

                    self['key_green'].setText(_('Remove'))
                    if self.changecmdList == True:
                        self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': package}))
                write_cache(self.cache_file, self.cachelist)
                self['list'].updateList(self.list)
                self.selectionChanged
                if len(self.cmdList):
                    self['key_yellow'].setText(_('Excecute'))
                else:
                    self['key_yellow'].setText('')

    def doInstall(self):
        if len(self.cmdList) and self.doSoftwareAction != True:
            self.removetextlist = ['enigma2-plugin-systemplugins-',
             'enigma2-plugin-extensions-',
             'kernel-module-',
             'enigma2-plugin-skin-',
             'enigma2-plugin-picons-',
             'enigma2-plugin-settings-',
             'enigma2-plugin-cams-',
             'enigma2-plugin-config-',
             'enigma2-plugin-drivers-',
             '--force-depends ',
             '--autoremove ']
            self.execlist = []
            self.plugin_list_state == False
            self.text = ''
            divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, '750S/div-h.png'))
            for self.textitem in self.cmdList:
                self.textitemaction = self.textitem[0]
                if self.textitemaction == 0:
                    self.textitemaction = _('Install')
                    actionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installed.png'))
                elif self.textitemaction == 2:
                    self.textitemaction = _('Remove')
                    actionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/remove.png'))
                else:
                    self.textitemaction = _('upgrade')
                self.textitempackage = self.textitem[1]
                self.textitem = self.textitempackage['package']
                for removetext in self.removetextlist:
                    self.textitem = self.textitem.replace(removetext, '')

                self.execlist.append((self.textitem,
                 self.textitemaction,
                 '',
                 '',
                 actionpng,
                 divpng))

            self['list'].setList(self.execlist)
            self['key_yellow'].setText('')
            self['key_green'].setText(_('Start'))
            self.doSoftwareAction = True

    def runInstall(self):
        self.doSoftwareAction = False
        self.session.openWithCallback(self.runInstallFinished, Ipkg, cmdList=self.cmdList)

    def runInstallFinished(self):
        needs_restart_list = ('enigma2-plugin-systemplugins-crossepg', 'enigma2-plugin-extensions-atmolightd', 'enigma2-plugin-extensions-enhancedmoviecenter', 'enigma2-plugin-extensions-epgimport', 'enigma2-plugin-extensions-grannybutton', 'enigma2-plugin-extensions-infobartunerstate', 'enigma2-plugin-extensions-lcd4linux', 'enigma2-plugin-extensions-multiquickbutton', 'enigma2-plugin-extensions-openvpn', 'enigma2-plugin-extensions-openwebif', 'enigma2-plugin-extensions-secondinfobar', 'enigma2-plugin-extensions-webbouqueteditor')
        skin_installed = False
        restart_required = False
        for x in self.cmdList:
            if len(x) > 1 and x[0] == 0:
                if x[1].has_key('package'):
                    if x[1]['package'].startswith('enigma2-plugin-skin-'):
                        skin_installed = True
                    if len([ p_name for p_name in needs_restart_list if x[1]['package'].startswith(p_name) ]):
                        restart_required = True
            if restart_required and skin_installed:
                break

        self.plugin_list_state = False
        self.changed = False
        self.cmdList = []
        self.changeList = []
        self.upgradablelist = []
        self.reloadPluginlist()
        self['key_yellow'].setText('')
        if restart_required:
            plugins.restart_required = True
        if skin_installed:
            self.session.openWithCallback(self.exitAnswerSkinChoice, MessageBox, _('A new skin was installed\n') + _('Do you want to open the skin choice list?'))
        elif not plugins.restart_required:
            if os_path.exists(self.cache_file) == True:
                remove(self.cache_file)
            self.close()
        else:
            self.session.openWithCallback(self.exitAnswer, MessageBox, _('Execution finished.\n') + _('Do you want to restart GUI ?'))

    def exitAnswerSkinChoice(self, result):
        if result:
            from Plugins.SystemPlugins.SkinSelector.plugin import SkinSelector
            self.prev_skin = config.skin.primary_skin.value
            self.session.openWithCallback(self.skinChanged, SkinSelector, silent_close=True)
        elif plugins.restart_required:
            self.session.openWithCallback(self.exitAnswer, MessageBox, _('Execution finished.\n') + _('Do you want to restart GUI ?'))
        else:
            if os_path.exists(self.cache_file) == True:
                remove(self.cache_file)
            self.close()

    def exitAnswer(self, result):
        if result:
            self.session.open(Screens.Standby.TryQuitMainloop, 3)
        else:
            self.reloadinfo()

    def skinChanged(self, res = None):
        need_restart = False
        if plugins.restart_required:
            need_restart = True
        if self.prev_skin != config.skin.primary_skin.value:
            need_restart = True
        if need_restart:
            self.session.openWithCallback(self.exitAnswer, MessageBox, _('Execution finished.\n') + _('Do you want to restart GUI ?'))
        else:
            if os_path.exists(self.cache_file) == True:
                remove(self.cache_file)
            self.close()

    def ipkgCallback(self, event, param):
        if event == IpkgComponent.EVENT_ERROR:
            self.list_updating = False
            self.setStatus('error')
        elif event == IpkgComponent.EVENT_DONE:
            if self.list_updating:
                self.list_updating = False
                if not self.Console:
                    self.Console = Console()
                cmd = 'opkg list-installed'
                self.Console.ePopen(cmd, self.IpkgListInstalled_Finished)

    def IpkgList_Finished(self, result, retval, extra_args = None):
        if len(result):
            self.packetlist = []
            for x in result.splitlines():
                split = x.split(' - ')
                if split[0].strip().startswith(self.wanted_extensions):
                    try:
                        self.packetlist.append([split[0].strip(), split[1].strip(), split[2].strip()])
                    except:
                        self.packetlist.append([split[0].strip(), split[1].strip(), ' '])

        if not self.Console:
            self.Console = Console()
        cmd = 'opkg list-upgradable'
        self.Console.ePopen(cmd, self.OpkgUpgradableList_Finished)

    def IpkgListInstalled_Finished(self, result, retval, extra_args = None):
        if len(result):
            self.installed_packetlist = {}
            for x in result.splitlines():
                split = x.split(' - ')
                if split[0].strip().startswith(self.wanted_extensions):
                    self.installed_packetlist[split[0].strip()] = split[1].strip()

        if not self.Console:
            self.Console = Console()
        cmd = "opkg list |  grep -v '^[[:space:]]'"
        self.Console.ePopen(cmd, self.IpkgList_Finished)

    def OpkgUpgradableList_Finished(self, result, retval, extra_args = None):
        self.upgradable_packetlist = {}
        if len(result):
            for x in result.splitlines():
                split = x.split(' - ')
                if split[0].strip().startswith(self.wanted_extensions):
                    self.upgradable_packetlist[split[0].strip()] = split[1].strip()

        self.opkgupdated = True
        self.buildPacketList()

    def buildEntryComponent(self, name, version, description, state):
        divpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, '750S/div-h.png'))
        self.fullname = name
        if self.replacename is not None:
            name = name.replace(self.wanted_extensions, '')
        if state == 'installed':
            if self.fullname in self.changeList:
                installedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installplugin.png'))
            else:
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
        elif state == 'goinstalled':
            state = 'installed'
            goinstalledpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/installplugin.png'))
            return (name,
             version,
             description,
             state,
             goinstalledpng,
             divpng)
        elif state == 'goremove':
            state = 'installable'
            goremovepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/removeplugin.png'))
            return (name,
             version,
             description,
             state,
             goremovepng,
             divpng)
        else:
            if self.fullname in self.changeList or self.fullname in self.upgradablelist:
                installablepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/removeplugin.png'))
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
                        if x[0].strip().startswith(self.wanted_extensions):
                            self.list.append(self.buildEntryComponent(x[0], x[1], x[2], x[3]))

                    if self.first_run == True:
                        self.first_run = False
                        self.setStatus('startmenu')
                    else:
                        self['list'].setList(self.list)
            except:
                self.inv_cache = 1

        if self.cache_ttl == 0 or self.inv_cache == 1 or self.vc == 0:
            for x in self.packetlist:
                status = ''
                if self.upgradable_packetlist.has_key(x[0].strip()):
                    status = 'upgradeable'
                    self.list.append(self.buildEntryComponent(x[0].strip(), x[1].strip(), x[2].strip(), status))
                elif self.installed_packetlist.has_key(x[0].strip()):
                    status = 'installed'
                    if x[1].strip() == self.installed_packetlist[x[0].strip()]:
                        self.list.append(self.buildEntryComponent(x[0].strip(), x[1].strip(), x[2].strip(), status))
                else:
                    status = 'installable'
                    self.list.append(self.buildEntryComponent(x[0].strip(), x[1].strip(), x[2].strip(), status))
                if self.installed_packetlist.has_key(x[0].strip()):
                    if x[1].strip() == self.installed_packetlist[x[0].strip()]:
                        self.cachelist.append([x[0].strip(),
                         x[1].strip(),
                         x[2].strip(),
                         status])
                else:
                    self.cachelist.append([x[0].strip(),
                     x[1].strip(),
                     x[2].strip(),
                     status])

            write_cache(self.cache_file, self.cachelist)
            self.first_run = False
            self.setStatus('startmenu')
        self.selectionChanged()
        if self.opkgupdated == True:
            self.opkgupdated = False
            self.checkFreeSpace()

    def reloadPluginlist(self):
        plugins.clearPluginList()
        plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))


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
