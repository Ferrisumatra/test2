from Screens.Screen import Screen
from enigma import ePoint, eSize, eServiceCenter, getBestPlayableServiceReference, eServiceReference
from Components.VideoWindow import VideoWindow
from Components.config import config, ConfigPosition
from Components.Label import Label

pip_config_initialized = False

class PictureInPicture(Screen):
	def __init__(self, session):
		global pip_config_initialized
		Screen.__init__(self, session)
		self["video"] = VideoWindow()
		self.currentService = None
		self["zap_focus"] = Label()
		if not pip_config_initialized:
			config.av.pip = ConfigPosition(default=[-1, -1, -1, -1], args = (719, 567, 720, 568))
			pip_config_initialized = True
		self.prev_fb_info = None
		self.onLayoutFinish.append(self.LayoutFinished)

	def get_FB_Size(self):
		from Tools.FBHelperTool import FBHelperTool
		fbtool = FBHelperTool()
		return fbtool.getFBSize(decoder = 1)

	def LayoutFinished(self):
		self.onLayoutFinish.remove(self.LayoutFinished)
		x = config.av.pip.value[0]
		y = config.av.pip.value[1]
		w = config.av.pip.value[2]
		h = config.av.pip.value[3]
		if x != -1 and y != -1 and w != -1 and h != -1:
			self["video"].instance.setOverscan(False)
			self.move(x, y)
			self.resize(w, h)

	def move(self, x, y):
		config.av.pip.value[0] = x
		config.av.pip.value[1] = y
		config.av.pip.save()
		self.instance.move(ePoint(x, y))

	def resize(self, w, h):
		config.av.pip.value[2] = w
		config.av.pip.value[3] = h
		config.av.pip.save()
		self.instance.resize(eSize(*(w, h)))
		self["video"].instance.resize(eSize(*(w, h)))

	def getPosition(self):
		return ((self.instance.position().x(), self.instance.position().y()))

	def getSize(self):
		return (self.instance.size().width(), self.instance.size().height())

	def playService(self, service):
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service
		if ref:
			self.pipservice = eServiceCenter.getInstance().play(ref)
			if self.pipservice and not self.pipservice.setTarget(1):
				self.pipservice.start()
				self.currentService = service
				if not self.prev_fb_info:
					self.prev_fb_info = self.get_FB_Size()
				return True
			else:
				self.pipservice = None
		return False

	def getCurrentService(self):
		return self.currentService

	def hideInfo(self):
		self["zap_focus"].hide()

	def showInfo(self):
		self["zap_focus"].show()
		
	def set_zap_focus_text(self):
		self["zap_focus"].setText(self.session.zap_focus_text)
		self.showInfo()
