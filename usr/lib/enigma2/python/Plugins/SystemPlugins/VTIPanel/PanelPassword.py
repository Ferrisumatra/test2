# 2015.06.16 12:50:47 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/PanelPassword.py
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.config import config, getConfigListEntry, ConfigPassword
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from skin import loadSkin
from __init__ import _

class PanelPassword(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.title = _('Change password for VTI Panel')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Save'))
        self['key_yellow'] = StaticText(_('Deactivate'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'InputActions'], {'ok': self.keySave,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keySave,
         'yellow': self.keyDefault}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session)
        self.createSetup()

    def createSetup(self):
        self.list = []
        self.panelpassword = getConfigListEntry(_('Input your new VTI Panel password : '), config.plugins.vtipanel.panelpassword)
        self.list.append(self.panelpassword)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keyCancel(self):
        self.close()

    def keySave(self):
        config.plugins.vtipanel.panelpassword.save()
        self.close()

    def keyDefault(self):
        config.plugins.vtipanel.panelpassword.value = 'vtipanelpassword'
        config.plugins.vtipanel.panelpassword.save()
        self.close()


class InputPanelPassword(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.title = _('Input password for VTI Panel')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Ok'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'InputActions'], {'ok': self.keyGo,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keyGo}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session)
        self.createSetup()

    def createSetup(self):
        config.plugins.vtipanel.inputpanelpassword.value = ''
        self.list = []
        self.inputpanelpassword = getConfigListEntry(_('Input your VTI Panel password : '), config.plugins.vtipanel.inputpanelpassword)
        self.list.append(self.inputpanelpassword)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keyCancel(self):
        ret = None
        self.close(ret)

    def keyGo(self):
        ret = config.plugins.vtipanel.inputpanelpassword.value
        self.close(ret)
