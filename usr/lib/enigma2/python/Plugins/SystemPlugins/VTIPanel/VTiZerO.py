# 2015.06.16 12:53:51 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/VTiZerO.py
from Components.Label import Label
from Components.Language import language
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.PluginComponent import plugins
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.Ipkg import IpkgComponent
from Components.Sources.List import List
from Components.SystemInfo import SystemInfo
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Ipkg import Ipkg
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import *
from skin import loadSkin
#from plugin import checkvu
from os import system, listdir, path as os_path, stat, statvfs
from __init__ import _
import time

class VTiZerO(Screen):

    def __init__(self, session, plugin_path, is_startwizard = False, args = 0):
        Screen.__init__(self, session)
        self.skinName = ['VTiZerO', 'BackupSuite']
        self.skin_path = plugin_path
        self.session = session
#       checkvu.runcheck()
        self.title = _('VTi ZerO')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.screentype = 'mainmenu'
        if is_startwizard:
            self.reminder = False
            self.accept = True
        else:
            self.reminder = True
            self.accept = False
        self.installmode = False
        self.list = []
        self['menu'] = List(self.list)
        self['status'] = Label()
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Ok'))
        self['key_yellow'] = StaticText(_('Restore'))
        self['key_info'] = StaticText(_('Free Flash'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'ChannelSelectEPGActions'], {'ok': self.warningReminder,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keyGreen,
         'yellow': self.keyYellow,
         'showEPGList': self.keyInfo}, -2)
        self.cmdList = []
        self.ipkg = IpkgComponent()
        self.ipkg.addCallback(self.ipkgCallback)
        self.onLayoutFinish.append(self.createMenu)

    def createMenu(self):
        self.list = []
        if self.screentype == 'mainmenu':
            self.list.append(('remove_plugins',
             _('Remove preinstalled plugins'),
             _('remove nearly every preinstalled plugin and the dependencies'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
             None))
            self.list.append(('remove_wlan',
             _('Remove WLAN support'),
             _('remove WLAN plugins and drivers'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
             None))
            self.list.append(('remove_hbbtv',
             _('Remove HbbTV support'),
             _('uninstall HbbTV plugin and browser'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
             None))
            if SystemInfo['Support3DUI']:
                self.list.append(('remove_xbmc',
                 _('Remove xbmc'),
                 _('uninstall xbmc and dependend packages'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
                 None))
            self.list.append(('remove_samba',
             _('Remove samba server'),
             _('remove samba server, NOT cifs filesystem support'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
             None))
            self.list.append(('remove_usbtuner',
             _('Remove USB tuner support'),
             _('uninstall kernel modules and firmware packages for USB tuners'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
             None))
            self.list.append(('remove_lang',
             _('Remove language files'),
             _('delete translation files expect configured language'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/zero_key.png')),
             None))
        self['menu'].setList(self.list)

    def warningReminder(self):
        if self.reminder == True:
            self.reminder = False
            msg = self.session.openWithCallback(self.runMenuEntry, MessageBox, _('W A R N I N G !!!\nDo not delete stuff you need afterwards\nVTI-Team is not responsible for loss of data\nDo you accept ?'), MessageBox.TYPE_YESNO)
            msg.setTitle(_('VTi ZerO'))
        else:
            self.runMenuEntry()

    def runMenuEntry(self, ret = None):
        if ret is True or self.accept is True:
            self.accept = True
            menuselection = self['menu'].getCurrent()[0]
            if menuselection is not None:
                self.removelist = None
                if menuselection is 'remove_plugins':
                    self.removelist = ('enigma2-plugin-systemplugins-3gmodemmanager', 'enigma2-plugin-extensions-pictureplayer', 'enigma2-plugin-extensions-remotechannelstreamconverter', 'enigma2-plugin-systemplugins-ui3dsetup', 'enigma2-plugin-systemplugins-uipositionsetup', 'enigma2-plugin-systemplugins-hdmicec', 'enigma2-plugin-systemplugins-3gmodemmanager', 'enigma2-plugin-systemplugins-wirelessaccesspoint', 'enigma2-plugin-systemplugins-zappingmodeselection', 'enigma2-plugin-extensions-streamtv', 'enigma2-plugin-extensions-dlnaserver', 'enigma2-plugin-extensions-dlnabrowser', 'enigma2-plugin-systemplugins-autoresolution', 'enigma2-plugin-extensions-graphmultiepg', 'enigma2-plugin-extensions-openwebif', 'enigma2-plugin-systemplugins-commoninterfaceassignment', 'enigma2-plugin-systemplugins-videotune', 'enigma2-plugin-systemplugins-blindscan', 'enigma2-plugin-extensions-mediascanner', 'enigma2-plugin-systemplugins-videoenhancement', 'enigma2-plugin-extensions-cdinfo', 'kernel-module-cdfs', 'enigma2-plugin-systemplugins-ledbrightnesssetup', 'enigma2-plugin-skin-750s', 'enigma2-plugin-systemplugins-autoshutdown')
                elif menuselection is 'remove_hbbtv':
                    self.removelist = ('enigma2-plugin-extensions-hbbtv', 'opera-hbbtv')
                elif menuselection is 'remove_wlan':
                    self.removelist = ('enigma2-plugin-systemplugins-wirelesslansetup', 'enigma2-plugin-systemplugins-wirelesslan', 'wireless-tools', 'wpa-supplicantkernel-module-ath5k', 'firmware-htc7010', 'firmware-htc9271', 'firmware-rt2561', 'firmware-rt3070', 'firmware-rtl8721u', 'r8192cu', 'rt2870sta', 'rt73-firmware', 'zd1211-firmware', 'rt3070', 'rt5572', 'r8192cu', 'r8712u', 'wlan-rt73', 'zd1211bkernel-module-ath9k-htc', 'kernel-module-carl9170', 'kernel-module-prism2-usb', 'kernel-module-rt73usb', 'kernel-module-rt2500usb', 'kernel-module-r8192u-usb', 'kernel-module-rtl8192cu', 'kernel-module-rtl8187', 'kernel-module-r8712u', 'kernel-module-w35und', 'kernel-module-zd1211rw')
                elif menuselection is 'remove_usbtuner':
                    self.removelist = ('firmware-dvb-af9005', 'firmware-dvb-fe-af9013', 'firmware-dvb-usb-af9015', 'firmware-dvb-usb-af9035', 'firmware-dvb-usb-avertv-a800', 'firmware-dvb-usb-dib0700', 'firmware-dvb-usb-dibusb', 'firmware-dvb-usb-digitv', 'firmware-dvb-usb-nova-t-usb2', 'firmware-dvb-usb-sms1xxx-nova-dvbt', 'firmware-dvb-usb-sms1xxx-hcw-dvbt', 'firmware-dvb-usb-ttusb-budget', 'firmware-dvb-usb-umt-010', 'firmware-dvb-usb-xc5000', 'firmware-dvb-usb-wt220u-zl0353', 'firmware-drxd-a2', 'firmware-dvb-fe-ds3000', 'firmware-dvb-fe-tda10071', 'firmware-dvb-fe-xc4000', 'firmware-dvb-usb-as102', 'firmware-dvb-usb-drxd', 'firmware-dvb-usb-s6xx', 'firmware-dvb-usb-skystar-usb', 'firmware-dvb-usb-xc3028kernel-module-em28xx-dvb', 'kernel-module-dvb-usb-a800', 'kernel-module-dvb-usb-af9005', 'kernel-module-af9013', 'kernel-module-mt2060', 'kernel-module-qt1010', 'kernel-module-tda18271', 'kernel-module-mxl5005s', 'kernel-module-mc44s803', 'kernel-module-tda18218', 'kernel-module-mxl5007t', 'kernel-module-dvb-usb-af9015', 'kernel-module-tda10021', 'kernel-module-tda10023kernel-module-mt352', 'kernel-module-zl10353', 'kernel-module-tda18212', 'kernel-module-cx24116', 'kernel-module-stv0900', 'kernel-module-stv6110', 'kernel-module-stv6110x', 'kernel-module-isl6423', 'kernel-module-dvb-usb-anysee', 'kernel-module-zl10353', 'kernel-module-qt1010', 'kernel-module-dvb-usb-au6610', 'kernel-module-mxl5007t', 'kernel-module-tda18218', 'kernel-module-dvb-usb-az6027', 'kernel-module-zl10353', 'kernel-module-mxl5005s', 'kernel-module-dvb-usb-ce6230', 'kernel-module-lgdt330x', 'kernel-module-mt352', 'kernel-module-zl10353', 'kernel-module-tuner-xc2028', 'kernel-module-tuner-simple', 'kernel-module-mxl5005s', 'kernel-module-max2165', 'kernel-module-lgs8gxx', 'kernel-module-atbm8830', 'kernel-module-dvb-usb-cxusb', 'kernel-module-drxd', 'kernel-module-dvb-usb-cinergyt2', 'kernel-module-mt352', 'kernel-module-nxt6000', 'kernel-module-dvb-usb-digitv', 'kernel-module-mt2060', 'kernel-module-mt2266', 'kernel-module-tuner-xc2028', 'kernel-module-xc5000', 'kernel-module-xc4000', 'kernel-module-s5h1411', 'kernel-module-lgdt3305', 'kernel-module-mxl5007t', 'kernel-module-dvb-usb-dib0700', 'kernel-module-dvb-usb-dibusb-mb', 'kernel-module-dvb-usb-dibusb-mc', 'kernel-module-zl10353', 'kernel-module-qt1010', 'kernel-module-dvb-usb-dtv5100', 'kernel-module-dvb-usb-dtt200u', 'kernel-module-si21xx', 'kernel-module-stv0299', 'kernel-module-stv0288', 'kernel-module-stb6000', 'kernel-module-cx24116', 'kernel-module-mt312 kernel-module-zl10039', 'kernel-module-ds3000', 'kernel-module-stv0900', 'kernel-module-stv6110', 'kernel-module-dvb-usb-dw2102', 'kernel-module-ec100', 'kernel-module-mxl5005s', 'kernel-module-dvb-usb-ec168', 'kernel-module-zl10353', 'kernel-module-qt1010', 'kernel-module-dvb-usb-gl861', 'kernel-module-dvb-usb-gp8psk', 'kernel-module-mt352', 'kernel-module-qt1010', 'kernel-module-tda1004x', 'kernel-module-tda827x', 'kernel-module-dvb-usb-m920x', 'kernel-module-stv0299 kernel-module-dvb-usb-opera', 'kernel-module-stv090x kernel-module-dvb-usb-technisat-usb2', 'kernel-module-tda826x', 'kernel-module-tda10086', 'kernel-module-tda827x', 'kernel-module-lnbp21', 'kernel-module-dvb-usb-ttusb2', 'kernel-module-dvb-ttusb-budget', 'kernel-module-dvb-usb-nova-t-usb2', 'kernel-module-mt352', 'kernel-module-dvb-usb-umt-010', 'kernel-module-dvb-usb-vp702x', 'kernel-module-dvb-usb-vp7045', 'kernel-module-smsdvb', 'kernel-module-smsusb', 'kernel-module-dvb-as102', 'kernel-module-dvb-usb-a867', 'kernel-module-tm6000-dvb', 'kernel-module-dvb-usb-af9035', 'kernel-module-tua9001 kernel-module-af9033', 'enigma2-plugin-systemplugins-hmp-usb-dvb-c-t2', 'hmp-usb-dvb-t2-c', 'usbtunerhelper')
                elif menuselection is 'remove_samba':
                    self.removelist = ['sambaserver']
                elif menuselection is 'remove_lang':
                    locales_list = ('ar', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'fy', 'hr', 'hu', 'is', 'it', 'lt', 'lv', 'nl', 'no', 'pl', 'pt', 'ru', 'sk', 'sl', 'sr', 'sv', 'tr', 'uk')
                    lang = language.getLanguage()[:2]
                    self.removelist = []
                    for locale in locales_list:
                        if self.installmode == True:
                            self.removelist.append('enigma2-locale-' + locale)
                        elif locale != lang and locale != 'en':
                            self.removelist.append('enigma2-locale-' + locale)

                elif menuselection is 'remove_xbmc':
                    self.removelist = ('task-vuplus-xbmc',)
                if self.removelist is not None:
                    if self.installmode == True:
                        self.installmode = False
                        self.installPlugins()
                    else:
                        self.removePlugins()
        else:
            self.reminder = True

    def removePlugins(self):
        menuselection = self['menu'].getCurrent()[0]
        if menuselection == 'remove_hbbtv':
            try:
                from Plugins.Extensions.HbbTV.plugin import _g_helper, getCommandServer
                if _g_helper is not None:
                    _g_helper._stop_opera()

                    def fake_is_running():
                        return False

                    _g_helper._is_browser_running = fake_is_running
                    time.sleep(1)
            except:
                pass

        packages = '--force-depends --autoremove '
        self.cmdList = []
        if len(self.removelist):
            self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': packages + self.removelist[0]}))
        for package in self.removelist:
            if package == 'enigma2-plugin-systemplugins-autoresolution':
                self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': '--force-depends ' + package}))
            else:
                packages += ' ' + package

        self.cmdList.append((IpkgComponent.CMD_REMOVE, {'package': packages}))
        self.session.open(Ipkg, cmdList=self.cmdList)

    def installPlugins(self):
        self.cmdList = []
        self.cmdList.append((IpkgComponent.CMD_UPDATE, {}))
        packages = ''
        for package in self.removelist:
            packages += ' ' + package

        self.cmdList.append((IpkgComponent.CMD_INSTALL, {'package': packages}))
        self.session.open(Ipkg, cmdList=self.cmdList)

    def ipkgCallback(self, event, param):
        if event == IpkgComponent.EVENT_ERROR:
            self.setStatus('error')

    def getFreeSpace(self, mountpoint):
        if mountpoint:
            stat_info = statvfs(mountpoint)
            free_flash_space = stat_info.f_bfree * stat_info.f_bsize
            return free_flash_space

    def keyCancel(self):
        plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
        self.close()

    def keyGreen(self):
        self.warningReminder()

    def keyYellow(self):
        self.installmode = True
        self.warningReminder()

    def keyInfo(self):
        free_flash_space = self.getFreeSpace('/')
        human_free_space = free_flash_space / 1048576
        msg = _('Free space at flash memory : %d MB\n') % human_free_space
        self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
