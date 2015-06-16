# -*- coding: utf-8 -*-

# maintainer: <plnick@vuplus-support.org>

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.

import struct
from enigma import eHdmiCEC, eTimer
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigSubsection, ConfigText
from Tools.HardwareInfoVu import HardwareInfoVu
from Screens.Standby import inStandby
import Screens.Standby
from Tools import Notifications
from Tools.DreamboxHardware import getFPWasTimerWakeup
from Tools.Directories import fileExists
import time
from os import system
from __init__ import _


class HdmiCec:
	def __init__(self):
		config.hdmicec = ConfigSubsection()
		config.hdmicec.enabled = ConfigYesNo(default = False)
		config.hdmicec.logenabledserial = ConfigYesNo(default = False)
		config.hdmicec.logenabledfile = ConfigYesNo(default = False)
		config.hdmicec.tvstandby = ConfigYesNo(default = False)
		config.hdmicec.tvwakeup = ConfigYesNo(default = False)
		config.hdmicec.boxstandby = ConfigYesNo(default = False)
		config.hdmicec.enabletvrc = ConfigYesNo(default = True)
		config.hdmicec.active_source_reply = ConfigYesNo(default = True)
		config.hdmicec.avvolumecontrol = ConfigYesNo(default = False)
		config.hdmicec.disabletimerwakeup = ConfigYesNo(default = False)
		config.hdmicec.device_name = ConfigText(default = self.getDeviceName(), visible_width = 50, fixed_size = False)
		config.hdmicec.standby_message = ConfigSelection(default = "standby,inactive", 
			choices = [
			("standby,inactive", _("TV standby")),
			("standby,avpwroff,inactive,", _("TV + A/V standby")),
			("inactive", _("Source inactive")),
			("nothing", _("Nothing"))])
		config.hdmicec.deepstandby_message = ConfigSelection(default = "standby,inactive",
			choices = [
			("standby,inactive", _("TV standby")),
			("standby,avdeeppwroff,inactive", _("TV + A/V standby")),
			("inactive", _("Source inactive")),
			("nothing", _("Nothing"))])
		config.hdmicec.wakeupstandby_message = ConfigSelection(default = "wakeup,active,activevu",
			choices = [
			("wakeup,active,activevu", _("TV wakeup")),
			("wakeup,active,activevu,avpwron", _("TV + A/V wakeup")),
			("avpwron,wakeup,active,activevu", _("A/V + TV wakeup")),
			("active", _("Source active")),
			("nothing", _("Nothing"))])
		config.hdmicec.wakeupdeepstandby_message = ConfigSelection(default = "wakeup,active,activevu",
			choices = [
			("wakeup,active,activevu", _("TV wakeup")),
			("wakeup,active,activevu,avpwron", _("TV + A/V wakeup")),
			("avpwron,wakeup,active,activevu", _("A/V + TV wakeup")),
			("active", _("Source active")),
			("nothing", _("Nothing"))])
		config.hdmicec.vustandby_message = ConfigSelection(default = "vustandby",
			choices = [
			("vustandby", _("VU+ standby")),
			("vudeepstandby", _("VU+ DeepStandby")),
			("vunothing", _("Nothing"))])
		config.hdmicec.vuwakeup_message = ConfigSelection(default = "vuwakeup",
			choices = [
			("vuwakeup", _("VU+ wakeup")),
			("vunothing", _("Nothing"))])
		config.hdmicec.tvinput = ConfigSelection(default = "1",
			choices = [
			("1", "HDMI 1"),
			("2", "HDMI 2"),
			("3", "HDMI 3"),
			("4", "HDMI 4"),
			("5", "HDMI 5"),
			("6", "HDMI 6"),
			("7", "HDMI 7")])
		config.hdmicec.avinput = ConfigSelection(default ="0",
			choices = [
			("0", _("no A/V Receiver")),
			("1", "HDMI 1"),
			("2", "HDMI 2"),
			("3", "HDMI 3"),
			("4", "HDMI 4"),
			("5", "HDMI 5"),
			("6", "HDMI 6"),
			("7", "HDMI 7")])
		config.hdmicec.message_delay = ConfigSelection(default = "10",
			choices = [
			("1", "0.1 sec"),
			("5", "0.5 sec"),
			("10", "1 sec"),
			("20", "2 sec"),
			("30", "3 sec"),
			("50", "5 sec")])

		config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call = False)
		config.misc.DeepStandbyOn.addNotifier(self.enterDeepStandby, initial_call = False)
		self.activateSourceTimer()
		self.leaveDeepStandby()

	def getDeviceName(self):
		deviceList = {
			"duo": "Vu+ Duo",
			"solo": "Vu+ Solo",
			"uno": "Vu+ Uno",
			"ultimo": "Vu+ Ultimo",
			"solo2": "Vu+ Solo2",
			"duo2": "Vu+ Duo2",
			"zero": "Vu+ zero",
			"solose": "Vu+ SoloSE",
			}
		vumodel = HardwareInfoVu().get_device_name()
		return deviceList.setdefault(vumodel, "VU+")

	def sendMessages(self, messages):
		messagedelay = float(config.hdmicec.message_delay.value)/10.0
		for message in messages.split(','):
			cmd = None
			logcmd = None
			addressvaluebroadcast = int("0F",16)
			addressvalue = int("0",16)
			addressvalueav = int("5",16)
			wakeupmessage = int("04",16)
			standbymessage=int("36",16)
			activesourcemessage=int("82",16)
			inactivesourcemessage=int("9D",16)
			sendkeymessage = int("44",16)
			sendkeypwronmessage = int("6D",16)
			sendkeypwroffmessage = int("6C",16)
			activevumessage=int("85",16)
			physaddress1 = int("0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value),16)
			physaddress2 = int("0x00",16)

			if message == "wakeup":
				cmd = struct.pack('B', wakeupmessage)
				logcmd = "[VTI HDMI-CEC] ** WakeUpMessage ** send message: %x to address %x" % (wakeupmessage, addressvalue)
			elif message == "active":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('BBB', activesourcemessage,physaddress1,physaddress2)
				logcmd = "[VTI HDMI-CEC] ** ActiveSourceMessage ** send message: %x:%x:%x to address %x" % (activesourcemessage,physaddress1,physaddress2,addressvalue)
				self.delayed_Message_Timer = eTimer()
				self.delayed_Message_Timer.start(20000, True)
				self.delayed_Message_Timer.callback.append(self.delayedActiveSourceMessage)
			elif message == "standby":
				cmd = struct.pack('B', standbymessage)
				logcmd = "[VTI HDMI-CEC] ** StandByMessage ** send message: %x to address %x" % (standbymessage, addressvalue)
			elif message == "inactive":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('BBB', inactivesourcemessage,physaddress1,physaddress2)
				logcmd = "[VTI HDMI-CEC] ** InActiveSourceMessage ** send message: %x:%x:%x to address %x" % (inactivesourcemessage,physaddress1,physaddress2,addressvalue)
			elif message == "avpwron":
				cmd = struct.pack('BB', sendkeymessage,sendkeypwronmessage)
				addressvalue = addressvalueav
				logcmd = "[VTI HDMI-CEC] ** Power on A/V ** send message: %x:%x to address %x" % (sendkeymessage, sendkeypwronmessage, addressvalue)
			elif message == "avdeeppwroff":
				cmd = struct.pack('BB',sendkeymessage,sendkeypwroffmessage)
				addressvalue = addressvalueav
				logcmd = "[VTI HDMI-CEC] ** Standby A/V (Deepstandby)** send message: %x:%x to address %x" % (sendkeymessage,sendkeypwroffmessage, addressvalue)
			elif message == "avpwroff":
				addressvalue = addressvalueav
				cmd = struct.pack('BB',sendkeymessage,sendkeypwroffmessage)
				logcmd = "[VTI HDMI-CEC] ** Standby A/V ** send message: %x:%x to address %x" % (sendkeymessage,sendkeypwroffmessage, addressvalue)
			elif message == "activevu":
				addressvalue = addressvaluebroadcast
				cmd = struct.pack('B', activevumessage)
				logcmd = "[VTI HDMI-CEC] ** Active VU Message ** send message: %x to address %x" % (activevumessage,addressvalue)
			if cmd and logcmd:
				self.sendCECMessage(cmd, addressvalue, logcmd, messagedelay)

	def sendCECMessage(self, cmd, addressvalue, logcmd, delay = 0):
		eHdmiCEC.getInstance().sendMessage(addressvalue, len(cmd), str(cmd))
		if config.hdmicec.logenabledserial.value:
			print logcmd
			if config.hdmicec.logenabledfile.value:
				filelog = "echo %s >> /tmp/hdmicec.log" % (logcmd)
				system(filelog)
		time.sleep(delay)

	def delayedActiveSourceMessage(self):
		messagedelay = float(config.hdmicec.message_delay.value)/10.0
		addressvaluebroadcast = int("0F",16)
		activesourcemessage=int("82",16)
		activevumessage=int("85",16)
		addressvalue = int("0",16)
		physaddress1 = int("0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value),16)
		physaddress2 = int("0x00",16)
		addressvalue = addressvaluebroadcast
		cmd_active = struct.pack('BBB', activesourcemessage,physaddress1,physaddress2)
		logcmd_active = "[VTI HDMI-CEC] ** ActiveSourceMessage ** send message: %x:%x:%x to address %x" % (activesourcemessage,physaddress1,physaddress2,addressvalue)
		self.sendCECMessage(cmd_active, addressvalue, logcmd_active, messagedelay)
		cmd_vu_is_active = struct.pack('B', activevumessage)
		logcmd_vu_is_active = "[VTI HDMI-CEC] ** Active VU Message ** send message: %x to address %x" % (activevumessage,addressvalue)
		self.sendCECMessage(cmd_vu_is_active, addressvalue, logcmd_vu_is_active, messagedelay)

	def leaveStandby(self):
		if config.hdmicec.enabled.value:
			self.activateSourceTimer()
			self.sendMessages(config.hdmicec.wakeupstandby_message.value)

	def enterStandby(self, configElement):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.leaveStandby)
		if config.hdmicec.enabled.value:
			self.sendMessages(config.hdmicec.standby_message.value)
		if inStandby != None:
			self.sendMessages("inactive")

	def enterDeepStandby(self,configElement):
		if config.hdmicec.enabled.value:
			self.sendMessages(config.hdmicec.deepstandby_message.value)

	def leaveDeepStandby(self):
		if config.hdmicec.enabled.value:
			if not getFPWasTimerWakeup():
				self.sendMessages(config.hdmicec.wakeupdeepstandby_message.value)
			else:
				if config.hdmicec.disabletimerwakeup.value:
					print "[VTI HDMI-CEC] timer wakeup => do not power on TV / A/V receiver"
				else:
					self.sendMessages(config.hdmicec.wakeupdeepstandby_message.value)

	def activateSourceTimer(self):
		self.initial_active_source_call = True
		if config.hdmicec.active_source_reply.value == False:
			self.activeSourceTimer = eTimer()
			self.activeSourceTimer.start(60000, True)
			self.activeSourceTimer.callback.append(self.setActiveSourceCall)

	def setActiveSourceCall(self):
		self.initial_active_source_call = False

## not used
	def activeSource(self):
		if config.hdmicec.enabled.value:
			physadress1 = "0x" + str(config.hdmicec.tvinput.value) + str(config.hdmicec.avinput.value)
			physadress2 = "0x00"
			cecmessage = int('0x82',16)
			address = int('0x0F',16)
			valuethree = int(physadress1,16)
			valuefour = int(physadress2,16)
			cmd = struct.pack('BBB',cecmessage,valuethree,valuefour)
			eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
			if config.hdmicec.enabletvrc.value:
					cecmessage = int('0x8E',16)
					address = int('0',16)
					valuethree = int('0',16)
					cmd = struct.pack('BB',cecmessage,valuethree)
					eHdmiCEC.getInstance().sendMessage(address, len(cmd), str(cmd))
