# 2015.06.16 12:40:39 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/DriverManager.py
from enigma import eTimer
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.config import config, ConfigSelection
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.Console import Console as ComConsole
from Components.Sources.List import List
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Tools.HardwareInfoVu import HardwareInfoVu
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import *
from skin import loadSkin
#from plugin import checkvu
from os import system, listdir
import os.path
import time
import re
from __init__ import _

def getDeviceName():
    hwdevice = HardwareInfoVu().get_device_name()
    if hwdevice == 'duo':
        return 'bm750'
    elif hwdevice == 'solo':
        return 'vusolo'
    elif hwdevice == 'uno':
        return 'vuuno'
    elif hwdevice == 'ultimo':
        return 'vuultimo'
    elif hwdevice == 'solo2':
        return 'vusolo2'
    elif hwdevice == 'duo2':
        return 'vuduo2'
    elif hwdevice == 'solose':
        return 'vusolose'
    elif hwdevice == 'zero':
        return 'vuzero'
    else:
        return 'noDevice'


def getKernelVersion():
    with open('/proc/version', 'r') as f:
        kernel_version = None
        kernel_path = None
        kernel = f.readline().split()
        kernel = kernel[2].split('.')
        if len(kernel) >= 3:
            if '-' in kernel[2]:
                kernel[2] = kernel[2].split('-')[0]
            kernel_version = '%s.%s.%s' % (kernel[0], kernel[1], kernel[2])
            kernel_pathes = listdir('/lib/modules')
            if len(kernel_pathes):
                for path in kernel_pathes:
                    if path.startswith(kernel_version):
                        if os.path.isdir('/lib/modules/' + path + '/extra'):
                            kernel_path = path
                            break

    return (kernel_version, kernel_path)


kernel_version, kernel_version_path = getKernelVersion()

class DriverManager(Screen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.session = session
        self.title = _('VTI DriverManager')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.list = []
        self['menu'] = List(self.list)
        self['status'] = Label()
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('OK'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'DirectionActions'], {'ok': self.runMenuEntry,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keyCancel,
         'yellow': self.keyCancel}, -2)
        self.vudevice = getDeviceName()
        self.onLayoutFinish.append(self.createMenu)

    def getCurrent(self):
        if self.vudevice == 'bm750':
            self.origdriverfile = 'dvb-bcm7335.ko'
        elif self.vudevice == 'vusolo':
            self.origdriverfile = 'dvb-bcm7325.ko'
        elif self.vudevice == 'vuuno':
            self.origdriverfile = 'dvb-bcm7413.ko'
        elif self.vudevice == 'vuultimo':
            self.origdriverfile = 'dvb-bcm7413.ko'
        elif self.vudevice == 'vusolo2':
            self.origdriverfile = 'dvb-bcm7356.ko'
        elif self.vudevice == 'vuduo2':
            self.origdriverfile = 'dvb-bcm7424.ko'
        elif self.vudevice == 'vusolose':
            self.origdriverfile = 'dvb-bcm7241.ko'
        elif self.vudevice == 'vuzero':
            self.origdriverfile = 'dvb-bcm7362.ko'
        try:
            changingdate = time.localtime(os.path.getmtime(self.driverdir + self.origdriverfile))
            currentdriver = str(changingdate[2]) + '.' + str(changingdate[1]) + '.' + str(changingdate[0])
        except:
            currentdriver = _('not available')

        currentdriver = _('Current drivers: ') + currentdriver
        self['status'].setText(currentdriver)

    def createMenu(self):
        self.list = []
        if kernel_version and kernel_version_path:
            self.driver = ''
            self.driverdir = '/lib/modules/' + kernel_version_path + '/extra/'
            self.origdriver = 'brcmfb.ko'
            self.getCurrent()
            self.list.append(('installlocal',
             _('Install drivers from a local device'),
             _('choose drivers from local filesystem to install'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/services.png')),
             None))
            self.list.append(('downloaddriver',
             _('Download and install drivers from Vu+ website'),
             _('choose drivers for download/install'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/restoresettings.png')),
             None))
            self['menu'].setList(self.list)

    def runMenuEntry(self):
        if len(self.list):
            menuselection = self['menu'].getCurrent()[0]
            if menuselection is not None:
                if menuselection is 'installlocal':
                    startdirectory = '/media/'
                    self.session.openWithCallback(self.selectedDriver, DriverManagerFile, startdirectory, self.skin_path)
                elif menuselection is 'downloaddriver':
                    self.session.openWithCallback(self.selectedDriver, DriverManagerDownload, self.skin_path)
        else:
            msg = self.session.openWithCallback(self.keyCancel, MessageBox, _('Sorry, detection of current kernel version failed !'), type=MessageBox.TYPE_ERROR)
            msg.setTitle(_('VTI DriverManager'))

    def selectedDriver(self, res):
        if res is not None:
            self.driver = res
            msg = self.session.openWithCallback(self.installDriver, MessageBox, _('Are you sure you want to install\nfollowing drivers:\n') + self.driver)
            msg.setTitle(_('VTI DriverManager'))

    def keyCancel(self, res = None):
        self.close()

    def installDriver(self, ret = False):
        if ret == True:
            cmd = 'tar -xzvf %s -C %s' % (self.driver, self.driverdir)
            returncmd = system(cmd)
            if returncmd == 0:
                msg = self.session.openWithCallback(self.rebootSTB, MessageBox, _('Drivers successfully installed !\nYou should restart your Vu+ STB:\nReboot now ?'))
                msg.setTitle(_('VTI DriverManager'))
            else:
                msg = self.session.open(MessageBox, _('Installation of drivers failed !!!'), MessageBox.TYPE_ERROR)
                msg.setTitle(_('VTI DriverManager'))

    def rebootSTB(self, ret = False):
        if ret == True:
            self.session.open(TryQuitMainloop, 2)


class DriverManagerFile(Screen):

    def __init__(self, session, initDir, plugin_path):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self['filelist'] = FileList(initDir, inhibitMounts=False, inhibitDirs=False, showMountpoints=False)
        self['driverfile'] = Label()
        self['actions'] = ActionMap(['WizardActions',
         'DirectionActions',
         'ColorActions',
         'EPGSelectActions'], {'back': self.cancel,
         'left': self.left,
         'right': self.right,
         'up': self.up,
         'down': self.down,
         'ok': self.ok,
         'green': self.green,
         'red': self.cancel}, -1)
        self.title = _('Select a drivers to install')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('OK'))
        self.vudevice = getDeviceName()

    def cancel(self):
        self.close(None)

    def green(self):
        if self['filelist'].getSelection()[1] == True:
            self['driverfile'].setText(_('Invalid Choice'))
        else:
            directory = self['filelist'].getCurrentDirectory()
            filename = self['filelist'].getFilename()
            if directory.endswith('/'):
                self.fullpath = self['filelist'].getCurrentDirectory() + self['filelist'].getFilename()
            else:
                self.fullpath = self['filelist'].getCurrentDirectory() + '/' + self['filelist'].getFilename()
            if self.fullpath.endswith('.tar.gz') == False or filename.startswith('vuplus-dvb-modules-' + self.vudevice) == False or filename.find(kernel_version) < 0:
                self['driverfile'].setText(_('no valid drivers'))
            else:
                self.close(self.fullpath)

    def up(self):
        self['filelist'].up()
        self.updateFile()

    def down(self):
        self['filelist'].down()
        self.updateFile()

    def left(self):
        self['filelist'].pageUp()
        self.updateFile()

    def right(self):
        self['filelist'].pageDown()
        self.updateFile()

    def ok(self):
        if self['filelist'].canDescent():
            self['filelist'].descent()
            self.updateFile()
        else:
            self.green()

    def updateFile(self):
        currFolder = self['filelist'].getSelection()[0]
        if self['filelist'].getFilename() is not None:
            directory = self['filelist'].getCurrentDirectory()
            filename = self['filelist'].getFilename()
            if directory.endswith('/'):
                self.fullpath = self['filelist'].getCurrentDirectory() + self['filelist'].getFilename()
            else:
                self.fullpath = self['filelist'].getCurrentDirectory() + '/' + self['filelist'].getFilename()
            if self.fullpath.endswith('.tar.gz') == False or filename.startswith('vuplus-dvb-modules-' + self.vudevice) == False or filename.find(kernel_version) < 0:
                if self['filelist'].getSelection()[1] == True:
                    self['driverfile'].setText(currFolder)
                else:
                    self['driverfile'].setText(_('no valid drivers'))
            else:
                self['driverfile'].setText(self['filelist'].getFilename())
        else:
            currFolder = self['filelist'].getSelection()[0]
            if currFolder is not None:
                self['driverfile'].setText(currFolder)
            else:
                self['driverfile'].setText(_('no valid drivers'))


class DriverManagerDownload(Screen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.session = session
        self.title = _('VTI DriverManager')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.list = []
        self.list.append((None,
         _('Please wait ...'),
         _(' downloading available drivers information'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
         None))
        self['downloadmenu'] = List(self.list)
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Download'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'DirectionActions'], {'ok': self.keyOk,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keyOk,
         'yellow': self.keyEasteregg}, -2)
        self.Console = ComConsole()
        self.vudevice = getDeviceName()
        self.downloaddir = '/tmp/'
        self.htmlfile = 'driver.txt'
        self.location = 'http://archive.vuplus.com/download/drivers/'
        self.eastereggbutton = False
        self.onLayoutFinish.append(self.getDriver)

    def keyEasteregg(self):
        if self.eastereggbutton == True:
            print 'remove oops :-)'
            self.eastereggbutton == False
            self.list = []
            self.list.append((None,
             _('Please wait ...'),
             _(' downloading available drivers information'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
             None))
            self['downloadmenu'].setList(self.list)
            if self.location == 'http://archive.vuplus.com/download/drivers/beta/':
                self.location = 'http://archive.vuplus.com/download/drivers/'
            else:
                self.location = 'http://archive.vuplus.com/download/drivers/beta/'
            self.getDriver()
        else:
            print 'oops'
            self.eastereggbutton = True
            self.eastereggTimer = eTimer()
            self.eastereggTimer.timeout.get().append(self.endEasteregg)
            self.eastereggTimer.start(500)

    def endEasteregg(self):
        self.eastereggbutton = False

    def getDriver(self):
        cmd = 'wget %s -O %s%s' % (self.location, self.downloaddir, self.htmlfile)
        self.Console.ePopen(cmd, self.createDownloadMenu)

    def createDownloadMenu(self, result, retval, extra_args = None):
        if retval == 0:
            self.list = []
            if fileExists(self.downloaddir + self.htmlfile):
                readfile = open(self.downloaddir + self.htmlfile, 'r')
                text = readfile.read()
                readfile.close()
                cmd = 'rm %s%s' % (self.downloaddir, self.htmlfile)
                system(cmd)
            else:
                text = ''
            result = re.findall('vuplus-dvb-modules-' + self.vudevice + '-' + kernel_version + '-\\w+.tar.gz', text)
            result = list(set(result))
            result.sort(reverse=True)
            for driver in result:
                driverfilename = driver
                driver = driver.split('.tar.gz')
                driver = driver[0].split(kernel_version + '-')
                if len(driver[1]) > 8:
                    driverappendix = driver[1][8:10]
                    driverappendix = driverappendix.replace('_', '')
                    driverappendix = ' ver. ' + driverappendix
                else:
                    driverappendix = ''
                driverday = driver[1][6:8]
                drivermonth = driver[1][4:6]
                driveryear = driver[1][0:4]
                drivertext = driverday + '.' + drivermonth + '.' + driveryear + driverappendix
                self.list.append((driverfilename,
                 _('Driver : %s') % drivertext,
                 _('choose this drivers for download'),
                 LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sockets.png')),
                 None))

            self['downloadmenu'].setList(self.list)
        else:
            self.downloadError()

    def keyOk(self):
        self.driverselected = self['downloadmenu'].getCurrent()
        if self.driverselected:
            self.driverselected = self['downloadmenu'].getCurrent()[0]
        else:
            self.driverselected = None
        if not self.driverselected == None:
            self.driverselection = self.driverselected
            self.list = []
            self.list.append((None,
             _('Please wait, downloading drivers: '),
             self.driverselection,
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
             None))
            self['downloadmenu'].setList(self.list)
            cmd = 'wget %s%s -O %s%s' % (self.location,
             self.driverselection,
             self.downloaddir,
             self.driverselection)
            self.Console.ePopen(cmd, self.downloadFinished)

    def downloadFinished(self, result, retval, extra_args = None):
        if retval == 0:
            fulldriverpath = self.downloaddir + self.driverselection
            self.close(fulldriverpath)
        else:
            self.downloadError()

    def downloadError(self):
        msg = self.session.open(MessageBox, _('Download failed !\nPlease check your internet connection'), MessageBox.TYPE_ERROR)
        msg.setTitle(_('VTI DriverManager'))
        self.close(None)

    def keyCancel(self):
        if self.Console is not None:
            if len(self.Console.appContainers):
                for name in self.Console.appContainers.keys():
                    self.Console.kill(name)

        self.close(None)
