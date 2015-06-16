# -*- coding: utf-8 -*-
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService, iServiceInformation
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.config import config

class AutoFrameRate(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap = {iPlayableService.evVideoFramerateChanged: self.VideoFramerateChanged})

	def VideoFramerateChanged(self):
		if config.av.videoport.value in config.av.videomode:
			if config.av.videomode[config.av.videoport.value].value in config.av.videorate:
				if config.av.videorate[config.av.videomode[config.av.videoport.value].value].value == "multi":
					service = session.nav.getCurrentService()
					info = service and service.info()
					framerate = info and info.getInfo(iServiceInformation.sFrameRate)
					if framerate in  (23976, 24000, 29970, 30000, 59940, 60000):
						self.setVideoFrameRate('60')
					else:
						self.setVideoFrameRate('50')

	def setVideoFrameRate(self, rate):
		try:
			f = open("/proc/stb/video/videomode_%shz" % rate, "r")
			multi_videomode = f.read()
			f.close()
			f = open("/proc/stb/video/videomode", "r")
			videomode = f.read()
			f.close()
			if videomode != multi_videomode:
				f = open("/proc/stb/video/videomode", "w")
				f.write(multi_videomode)
				f.close()
		except IOError:
			print "error at reading/writing /proc/stb/video.. files"

def autostart(reason, **kwargs):
	global session
	if kwargs.has_key("session") and reason == 0:
		session = kwargs["session"]
		AutoFrameRate(session)

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)]
