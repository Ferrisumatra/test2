# 2015.06.16 12:49:57 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/ntpserver.py
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
import xml.dom.minidom
import os
from Screens.MessageBox import MessageBox

class SelectCountry(Screen):

    def __init__(self, session, xmlparse, selection):
        Screen.__init__(self, session)
        self.xmlparse = xmlparse
        self.selection = selection
        list = []
        for contenant in self.xmlparse.getElementsByTagName('contenant'):
            if str(contenant.getAttribute('cont').encode('utf8')) == self.selection:
                for country in contenant.getElementsByTagName('country'):
                    list.append(country.getAttribute('name').encode('utf8'))

        self['countrymenu'] = MenuList(list)
        self['actions'] = ActionMap(['SetupActions'], {'ok': self.selCountry,
         'cancel': self.close}, -2)
        self.onShown.append(self.setWindowTitle)

    def selCountry(self):
        if os.path.isfile('/etc/init.d/ntpupdate.sh'):
            selection_country = self['countrymenu'].getCurrent()
            for contenant in self.xmlparse.getElementsByTagName('contenant'):
                if str(contenant.getAttribute('cont').encode('utf8')) == self.selection:
                    for country in contenant.getElementsByTagName('country'):
                        if country.getAttribute('name').encode('utf8') == selection_country:
                            ntpServer = str(country.getElementsByTagName('ntp')[0].childNodes[0].data)

            print 'ntp server name is: ', ntpServer
            cmd = 'echo ' + ntpServer + ' >/etc/ntpserver'
            os.system(cmd)
            cmd = '/etc/init.d/ntpupdate.sh start'
            os.system(cmd)
            message = _('NTP server ') + ntpServer + _(' is activated.')
            mybox = self.session.openWithCallback(self.close, MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    def setWindowTitle(self):
        self.setTitle(_('NTP-Server Country Selection'))


class NTPManager(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.onShown.append(self.setWindowTitle)
        list = []
        xmlfile = '/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/ntpurls.xml'
        if os.path.isfile(xmlfile):
            xmlparse = xml.dom.minidom.parse(xmlfile)
            for contenant in xmlparse.getElementsByTagName('contenant'):
                list.append(contenant.getAttribute('cont').encode('utf8'))

            self.xmlparse = xmlparse
            self['menu'] = MenuList(list)
            self['actions'] = ActionMap(['SetupActions'], {'ok': self.selContenant,
             'cancel': self.close}, -2)
        else:
            self.close

    def setWindowTitle(self):
        self.setTitle(_('NTP-Server Contenant Selection'))

    def selContenant(self):
        selection = str(self['menu'].getCurrent())
        self.session.openWithCallback(self.close, SelectCountry, self.xmlparse, selection)
