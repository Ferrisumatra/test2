from Screens.Screen import Screen
from enigma import eServiceCenter, getBestPlayableServiceReference, eServiceReference, iPlayableService, getDesktop
from Components.VideoWindow import VideoWindow
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Label import Label

class SplitScreen(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		sz_w = getDesktop(0).size().width()
		if sz_w == 1280:
			sz_h = 720
			if self.session.is_audiozap:
				self.skinName = ["AudioZap", "SplitScreen"]
		elif sz_w == 1920:
			sz_h = 1080
			if self.session.is_audiozap:
				self.skinName = ["AudioZap", "SplitScreen"]
		else:
			self.skinName = ["SplitScreenSD"]
			if self.session.is_audiozap:
				self.skinName = ["AudioZapSD", "SplitScreenSD"]
			sz_w = 720
			sz_h = 576
		self["video1"] = VideoWindow(decoder = 0, fb_width = sz_w, fb_height = sz_h)
		self["video2"] = VideoWindow(decoder = 1, fb_width = sz_w, fb_height = sz_h)
		self["MasterService"] = ServiceEvent()
		self["SlaveService"] = ServiceEvent()
		self["zap_focus"] = Label()
		self.session = session
		self.currentService = None
		self.fb_w = sz_w
		self.fb_h = sz_h
		self.onLayoutFinish.append(self.LayoutFinished)

	def get_FB_Size(self, video):
		for attr_tuple in self[video].skinAttributes:
			if attr_tuple[0] == "position":
				x = attr_tuple[1].split(',')[0]
				y = attr_tuple[1].split(',')[1]
			elif attr_tuple[0] == "size":
				w = attr_tuple[1].split(',')[0]
				h = attr_tuple[1].split(',')[1]
		x = format(int(float(x) / self.fb_w * 720.0), 'x').zfill(8)
		y = format(int(float(y) / self.fb_h * 576.0), 'x').zfill(8)
		w = format(int(float(w) / self.fb_w * 720.0), 'x').zfill(8)
		h = format(int(float(h) / self.fb_h * 576.0), 'x').zfill(8)
		return [w, h, x, y]
		

	def LayoutFinished(self):
		self.prev_fb_info = self.get_FB_Size(video = "video1") 
		self.prev_fb_info_second_dec = self.get_FB_Size(video = "video2")
		self.onLayoutFinish.remove(self.LayoutFinished)
		self["video1"].instance.setOverscan(False)
		self["video2"].instance.setOverscan(False)
		self.updateServiceInfo()

	def updateServiceInfo(self):
		master_service = self.session.nav.getCurrentlyPlayingServiceReference()
		self["MasterService"].newService(master_service)

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
				self["SlaveService"].newService(service)
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
