from Screens.Screen import Screen
from enigma import eServiceCenter, getBestPlayableServiceReference, eServiceReference
from Components.VideoWindow import VideoWindow
from Components.Label import Label

pip_config_initialized = False

class PiGDummy(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["zap_focus"] = Label()
		self.onLayoutFinish.append(self.LayoutFinished)

	def LayoutFinished(self):
		self.onLayoutFinish.remove(self.LayoutFinished)
		self["zap_focus"].hide()

	def move(self, x, y):
		pass

	def resize(self, w, h):
		pass

	def getPosition(self):
		pass

	def getSize(self):
		pass

	def playService(self, service):
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service
		if ref:
			self.pipservice = eServiceCenter.getInstance().play(ref)
			if self.pipservice  and not self.pipservice.setTarget(1):
				self.pipservice.start()
				self.currentService = service
				return True
			else:
				self.pipservice = None
		return False

	def getCurrentService(self):
		return self.currentService

	def hideInfo(self):
		pass

	def showInfo(self):
		pass
		
	def set_zap_focus_text(self):
		pass

