# 2015.06.16 12:43:20 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/EPGPanel.py
from enigma import eEPGCache
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigText, ConfigNothing, NoSave
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Tools.LoadPixmap import LoadPixmap
from Tools import Notifications
from skin import loadSkin
from os import system
import _enigma
import new
from __init__ import _

class EPGPanel(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.session = session
        self.input_epgpath = NoSave(ConfigNothing())
        self.input_epgbackup = NoSave(ConfigNothing())
        self.input_epgrestore = NoSave(ConfigNothing())
        self.input_epgdelete = NoSave(ConfigNothing())
        self.title = _('VTI EPG Panel')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['status'] = Label()
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Save'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'DirectionActions'], {'ok': self.keyOk,
         'cancel': self.keyClose,
         'red': self.keyCancel,
         'green': self.keyClose,
         'up': self.up,
         'down': self.down}, -2)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
        self.createSetup()

    def createSetup(self):
        epgpath = str(config.misc.epgcache_filename.value).replace('/epg.dat', '')
        self.list = []
        self.epgpanelPath = getConfigListEntry(_('EPG Path :') + ' %s' % epgpath, self.input_epgpath, 'epgpath')
        self.epgpanelBackup = getConfigListEntry(_('Save EPG cache to epg.dat'), self.input_epgbackup, 'epgbackup')
        self.epgpanelRestore = getConfigListEntry(_('Load EPG data from epg.dat'), self.input_epgrestore, 'epgrestore')
        self.epgpanelDelete = getConfigListEntry(_('Delete broken epg.dat'), self.input_epgdelete, 'epgdelete')
        self.list.append(self.epgpanelPath)
        self.list.append(self.epgpanelBackup)
        self.list.append(self.epgpanelRestore)
        self.list.append(self.epgpanelDelete)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keyOk(self):
        try:
            returnValue = self['config'].l.getCurrentSelection()[2]
        except Exception as e:
            returnValue = None

        print 'epgpath'
        if returnValue == 'epgbackup':
            print '[VTIPanel] save EPG data to epg.dat'
            try:
                self.epgloadrestore = new.instancemethod(_enigma.eEPGCache_save, None, eEPGCache)
            except Exception as e:
                print '[VTIPanel] failed to save EPG data to epg.dat'
                return

            self.statustext = _('Saving of EPG cache to %s finished') % config.misc.epgcache_filename.value
        elif returnValue == 'epgrestore':
            try:
                self.epgloadrestore = new.instancemethod(_enigma.eEPGCache_load, None, eEPGCache)
            except Exception as e:
                print '[VTIPanel] failed to load EPG data from epg.dat'
                return

            self.statustext = _('Loading EPG data from %s finished') % config.misc.epgcache_filename.value
        else:
            if returnValue == 'epgdelete':
                self.session.openWithCallback(self.deleteBroken, MessageBox, _('Do you really want to delete epg.dat ?\nNote: This will restart your VU+ STB'), MessageBox.TYPE_YESNO, timeout=10)
                return
            if returnValue == 'epgpath':
                startdirectory = str(config.misc.epgcache_filename.value).replace('epg.dat', '')
                self.session.openWithCallback(self.gotEPGpath, DirChoose, startdirectory)
                return
            return
        self.epgloadrestore(eEPGCache.getInstance())
        print '[VTIPanel] EPG backup/loading finished'
        self.epgBackupfinished(self.statustext)

    def gotEPGpath(self, res):
        if res:
            config.misc.epgcache_filename.value = res
            config.misc.epgcache_filename.save()
            self.createSetup()

    def deleteBroken(self, res):
        if res == True:
            cmd = 'rm -f %s ; /sbin/reboot' % config.misc.epgcache_filename.value
            system(cmd)
        else:
            return

    def epgBackupfinished(self, statustext):
        self.text = statustext
        self['status'].setText(self.text)

    def up(self):
        self.statustext = ''
        self.epgBackupfinished(self.statustext)
        if len(self['config'].list) > 0:
            self['config'].instance.moveSelection(self['config'].instance.moveUp)

    def down(self):
        self.statustext = ''
        self.epgBackupfinished(self.statustext)
        if len(self['config'].list) > 0:
            self['config'].instance.moveSelection(self['config'].instance.moveDown)

    def changedEntry(self):
        self.statustext = ''
        self.epgBackupfinished(self.statustext)

    def keyClose(self):
        eEPGCache.getInstance().setCacheFile(config.misc.epgcache_filename.value)
        self.close()


class DirChoose(Screen):

    def __init__(self, session, initDir):
        Screen.__init__(self, session)
        self.skinName = ['DriverManagerFile', 'FileBrowser', 'EPGPathBrowser']
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
        self.title = _('VTI EPG Panel')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('OK'))

    def cancel(self):
        self.close(None)

    def green(self):
        if self['filelist'].getSelection()[1]:
            directory = self['filelist'].getSelection()[0]
            if directory.endswith('/'):
                self.fullpath = directory + 'epg.dat'
            else:
                self.fullpath = directory + '/epg.dat'
            self.close(self.fullpath)
        else:
            self['driverfile'].setText(_('Invalid Choice'))

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
        if self['filelist'].getSelection()[1]:
            self['driverfile'].setText(currFolder)
        else:
            self['driverfile'].setText(_('Invalid Choice'))
