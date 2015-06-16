from Screen import Screen
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.ChoiceList import ChoiceList, ChoiceEntryComponent
from Components.config import config, ConfigSubsection, getConfigListEntry, ConfigNothing, ConfigSelection, ConfigOnOff, ConfigSlider, NoSave
from Components.MultiContent import MultiContentEntryText
from Components.Sources.List import List
from Components.Sources.Boolean import Boolean
from Components.SystemInfo import SystemInfo

from enigma import iPlayableService, eDVBVolumecontrol

from Tools.ISO639 import LanguageCodes
from Tools.BoundFunction import boundFunction
FOCUS_CONFIG, FOCUS_STREAMS = range(2)
[PAGE_AUDIO, PAGE_SUBTITLES] = ["audio", "subtitles"]

class AudioSelection(Screen, ConfigListScreen):
	def __init__(self, session, infobar=None, page=PAGE_AUDIO):
		Screen.__init__(self, session)

		self["streams"] = List([])
		self["key_red"] = Boolean(False)
		self["key_green"] = Boolean(False)
		self["key_yellow"] = Boolean(True)
		self["key_blue"] = Boolean(False)
		
		ConfigListScreen.__init__(self, [])
		self.infobar = infobar or self.session.infobar

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedInfo: self.__updatedInfo
			})
		self.cached_subtitle_checked = False
		self.__selected_subtitle = None
        
		self["actions"] = NumberActionMap(["ColorActions", "SetupActions", "DirectionActions"],
		{
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"ok": self.keyOk,
			"cancel": self.cancel,
			"up": self.keyUp,
			"down": self.keyDown,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -2)

		self.settings = ConfigSubsection()
		choicelist = [(PAGE_AUDIO,_("audio tracks")), (PAGE_SUBTITLES,_("Subtitles"))]
		self.settings.menupage = ConfigSelection(choices = choicelist, default=page)
		self.onLayoutFinish.append(self.__layoutFinished)
		self.volctrl = eDVBVolumecontrol.getInstance()

	def __layoutFinished(self):
		self["config"].instance.setSelectionEnable(False)
		self.focus = FOCUS_STREAMS
		self.settings.menupage.addNotifier(self.fillList)

	def fillList(self, arg=None):
		streams = []
		conflist = []
		selectedidx = 0

		if self.settings.menupage.getValue() == PAGE_AUDIO:
			self.setTitle(_("Select audio track"))
			service = self.session.nav.getCurrentService()
			self.audioTracks = audio = service and service.audioTracks()
			n = audio and audio.getNumberOfTracks() or 0
			if SystemInfo["CanDownmixAC3"]:
				self.settings.downmix = ConfigOnOff(default=config.av.downmix_ac3.value)
				self.settings.downmix.addNotifier(self.changeAC3Downmix, initial_call = False)
				conflist.append(getConfigListEntry(_("Dolby Digital / DTS downmix"), self.settings.downmix))
				self["key_red"].setBoolean(True)
			
			if SystemInfo["CanDownmixAAC"]:
				self.settings.downmix_aac = ConfigOnOff(default=config.av.downmix_aac.value)
				self.settings.downmix_aac.addNotifier(self.changeAACDownmix, initial_call = False)
				conflist.append(getConfigListEntry(_("AAC downmix"), self.settings.downmix_aac))

			if n > 0:
				self.audioChannel = service.audioChannel()
				if self.audioChannel:
					choicelist = [("0",_("left")), ("1",_("stereo")), ("2", _("right"))]
					self.settings.channelmode = ConfigSelection(choices = choicelist, default = str(self.audioChannel.getCurrentChannel()))
					self.settings.channelmode.addNotifier(self.changeMode, initial_call = False)
					conflist.append(getConfigListEntry(_("Channel"), self.settings.channelmode))
					self["key_green"].setBoolean(True)
				else:
					conflist.append(('',))
					self["key_green"].setBoolean(False)
				selectedAudio = self.audioTracks.getCurrentTrack()
				for x in range(n):
					number = str(x + 1)
					i = audio.getTrackInfo(x)
					languages = i.getLanguage().split('/')
					description = i.getDescription() or _("<unknown>")
					selected = ""
					language = ""

					if selectedAudio == x:
						selected = _("Running")
						selectedidx = x

					cnt = 0
					for lang in languages:
						if cnt:
							language += ' / '
						if LanguageCodes.has_key(lang):
							language += LanguageCodes[lang][0]
						elif lang == "und":
							_("<unknown>")
						else:
							language += lang
						cnt += 1

					streams.append((x, "", number, description, language, selected))

			else:
				streams = []
				conflist.append(('',))
				self["key_green"].setBoolean(False)
			
			if SystemInfo["CanMultiChannelPCM"]:
				self.settings.multichannel_pcm = ConfigOnOff(default=config.av.multichannel_pcm.value)
				self.settings.multichannel_pcm.addNotifier(self.changeMultiChannelPCM, initial_call = False)
				conflist.append(getConfigListEntry(_("Multichannel PCM"), self.settings.multichannel_pcm))
				self["key_blue"].setBoolean(True)
			
			if SystemInfo["Can3DSurround"]:
				choicelist = [("none", _("off")), ("hdmi", _("HDMI")), ("spdif", _("SPDIF")), ("dac", _("DAC"))]
				self.settings.surround_3d = ConfigSelection(choices = choicelist, default = config.av.surround_3d.value)
				self.settings.surround_3d.addNotifier(self.change3DSurround, initial_call = False)
				conflist.append(getConfigListEntry(_("3D Surround"), self.settings.surround_3d))
				self["key_blue"].setBoolean(True)
				
			if SystemInfo["CanSpeakerPosition"] and SystemInfo["Can3DSurround"] and config.av.surround_3d.value != "none":
				choicelist = [("center", _("center")), ("wide", _("wide")), ("extrawide", _("extrawide"))]
				self.settings.speaker_position = ConfigSelection(choices = choicelist, default = config.av.surround_speaker_position.value)
				self.settings.speaker_position.addNotifier(self.changeSpeakerPosition, initial_call = False)
				conflist.append(getConfigListEntry(_("Speaker position"), self.settings.speaker_position))
				
			if SystemInfo["CanAVL"]:
				choicelist = [("none", _("off")), ("hdmi", _("HDMI")), ("spdif", _("SPDIF")), ("dac", _("DAC"))]
				self.settings.avl = ConfigSelection(choices = choicelist, default = config.av.avl.value)
				self.settings.avl.addNotifier(self.changeAVL, initial_call = False)
				conflist.append(getConfigListEntry(_("Automatic Volume Leveling (AVL)"), self.settings.avl))
			
			edid_bypass_choicelist = [("00000000", _("off")), ("00000001", _("on"))]
			self.settings.edid_bypass = ConfigSelection(choices = edid_bypass_choicelist, default = config.av.bypass_edid_checking.value)
			self.settings.edid_bypass.addNotifier(self.changeEDIDBypass, initial_call = False)
			conflist.append(getConfigListEntry(_("Bypass HDMI EDID Check"), self.settings.edid_bypass))

			self.settings.volume = NoSave(ConfigSlider(default=config.audio.volume.value, increment = 5, limits=(0,100)))
			self.settings.volume.addNotifier(self.changeVolume, initial_call = False)
			conflist.append(getConfigListEntry(_("Volume"), self.settings.volume))

		elif self.settings.menupage.getValue() == PAGE_SUBTITLES:
			self.setTitle(_("Subtitle selection"))
			conflist.append(('',))
			conflist.append(('',))
			self["key_red"].setBoolean(False)
			self["key_green"].setBoolean(False)

			if self.subtitlesEnabled():
				sel = self.infobar.selected_subtitle
			else:
				sel = None

			idx = 0
			
			subtitlelist = self.getSubtitleList()

			if len(subtitlelist):
				for x in subtitlelist:
					number = str(x[1])
					description = "?"
					language = _("<unknown>")
					selected = ""

					if sel and x == sel:
						selected = _("Running")
						selectedidx = idx
					
					if x[4] != "und":
						if LanguageCodes.has_key(x[4]):
							language = LanguageCodes[x[4]][0]
						else:
							language = x[4]

					if x[0] == 0:
						description = "DVB"
						number = "%x" % (x[1])

					elif x[0] == 1:
						description = "TTX"
						number = "%x%02x" % (x[3],x[2])

					elif x[0] == 2:
						types = (_("<unknown>"), "UTF-8 text", "SSA", "AAS", ".SRT file", "VOB", "PGS (unsupported)")
						description = types[x[2]]

					streams.append((x, "", number, description, language, selected))
					idx += 1
			
			else:
				streams = []

		conflist.append(getConfigListEntry(_("Menu"), self.settings.menupage))
		
		from Components.PluginComponent import plugins
		from Plugins.Plugin import PluginDescriptor
		
		if hasattr(self.infobar, "runPlugin"):
			class PluginCaller:
				def __init__(self, fnc, *args):
					self.fnc = fnc
					self.args = args
				def __call__(self, *args, **kwargs):
					self.fnc(*self.args)

			Plugins = [ (p.name, PluginCaller(self.infobar.runPlugin, p)) for p in plugins.getPlugins(where = PluginDescriptor.WHERE_AUDIOMENU) ]

			if len(Plugins):
				self["key_blue"].setBoolean(True)
				conflist.append(getConfigListEntry(Plugins[0][0], ConfigNothing()))
				self.plugincallfunc = Plugins[0][1]
			if len(Plugins) > 1:
				print "plugin(s) installed but not displayed in the dialog box:", Plugins[1:]

		self["config"].list = conflist
		self["config"].l.setList(conflist)

		self["streams"].list = streams
		self["streams"].setIndex(selectedidx)

	def __updatedInfo(self):
		self.fillList()

	def getSubtitleList(self):
		s = self.infobar and self.infobar.getCurrentServiceSubtitle()
		l = s and s.getSubtitleList() or [ ]
		return l

	def subtitlesEnabled(self):
		return self.infobar.subtitles_enabled

	def enableSubtitle(self, subtitles):
		if self.infobar.selected_subtitle != subtitles:
			self.infobar.subtitles_enabled = False
			self.infobar.selected_subtitle = subtitles
			if subtitles:
				self.infobar.subtitles_enabled = True

	def changeEDIDBypass(self, edid_bypass):
		if edid_bypass.getValue():
			config.av.bypass_edid_checking.value = edid_bypass.getValue()
		config.av.bypass_edid_checking.save()

	def change3DSurround(self, surround_3d):
		if surround_3d.getValue():
			config.av.surround_3d.value = surround_3d.getValue()
		config.av.surround_3d.save()
		self.__updatedInfo()

	def changeSpeakerPosition(self, speaker_position):
		if speaker_position.getValue():
			config.av.surround_speaker_position.value = speaker_position.getValue()
		config.av.surround_speaker_position.save()

	def changeAVL(self, avl):
		if avl.getValue():
			config.av.avl.value = avl.getValue()
		config.av.avl.save()

	def changeAC3Downmix(self, downmix):
		if downmix.getValue() == True:
			config.av.downmix_ac3.value = True
		else:
			config.av.downmix_ac3.value = False
		config.av.downmix_ac3.save()
		self.__updatedInfo()

	def changeMultiChannelPCM(self, multichannel_pcm):
		if multichannel_pcm.getValue() == True:
			config.av.multichannel_pcm.value = True
		else:
			config.av.multichannel_pcm.value = False
		config.av.multichannel_pcm.save()

	def changeAACDownmix(self, downmix):
		if downmix.getValue() == True:
			config.av.downmix_aac.value = True
		else:
			config.av.downmix_aac.value = False
		config.av.downmix_aac.save()

	def changeMode(self, mode):
		if mode is not None and self.audioChannel:
			self.audioChannel.selectChannel(int(mode.getValue()))

	def changeAudio(self, audio):
		track = int(audio)
		if isinstance(track, int):
			if self.session.nav.getCurrentService().audioTracks().getNumberOfTracks() > track:
				self.audioTracks.selectTrack(track)

	def changeVolume(self, direction):
		config.audio.volume.value = self.settings.volume.value
		self.volctrl.setVolume(config.audio.volume.value, config.audio.volume.value)
		if self.volctrl.isMuted() and config.audio.volume.value > 0:
			self.volctrl.volumeToggleMute()
		if not self.volctrl.isMuted() and config.audio.volume.value == 0:
			self.volctrl.volumeToggleMute()
		config.audio.volume.save()

	def keyLeft(self):
		if self.focus == FOCUS_CONFIG:
			ConfigListScreen.keyLeft(self)
		elif self.focus == FOCUS_STREAMS:
			self["streams"].setIndex(0)

	def keyRight(self, config = False):
		if config or self.focus == FOCUS_CONFIG:
			list_length = 4
			if SystemInfo["Can3DSurround"]:
				list_length += 1
			if SystemInfo["CanSpeakerPosition"]:
				list_length += 1
			if SystemInfo["CanDownmixAAC"]:
				list_length += 1
			if SystemInfo["CanAVL"]:
				list_length += 1
			if SystemInfo["CanMultiChannelPCM"]:
				list_length += 1
			if self["config"].getCurrentIndex() < list_length:
				ConfigListScreen.keyRight(self)
			elif hasattr(self, "plugincallfunc"):
				self.plugincallfunc()
		if self.focus == FOCUS_STREAMS and self["streams"].count() and config == False:
			self["streams"].setIndex(self["streams"].count()-1)

	def keyRed(self):
		if self["key_red"].getBoolean():
			self.colorkey(0)

	def keyGreen(self):
		if self["key_green"].getBoolean():
			self.colorkey(1)

	def keyYellow(self):
		if self["key_yellow"].getBoolean():
			self.colorkey(2)

	def keyBlue(self):
		if self["key_blue"].getBoolean():
			self.colorkey(3)

	def colorkey(self, idx):
		self["config"].setCurrentIndex(idx)
		self.keyRight(True)

	def keyUp(self):
		if self.focus == FOCUS_CONFIG:
			self["config"].instance.moveSelection(self["config"].instance.moveUp)
		elif self.focus == FOCUS_STREAMS:
			if self["streams"].getIndex() == 0:
				self["config"].instance.setSelectionEnable(True)
				self["streams"].style = "notselected"
				self["config"].setCurrentIndex(len(self["config"].getList())-1)
				self.focus = FOCUS_CONFIG
			else:
				self["streams"].selectPrevious()

	def keyDown(self):
		if self.focus == FOCUS_CONFIG:
			if self["config"].getCurrentIndex() < len(self["config"].getList())-1:
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
			else:
				self["config"].instance.setSelectionEnable(False)
				self["streams"].style = "default"
				self.focus = FOCUS_STREAMS
		elif self.focus == FOCUS_STREAMS:
			self["streams"].selectNext()

	def keyNumberGlobal(self, number):
		if number <= len(self["streams"].list):
			self["streams"].setIndex(number-1)
			self.keyOk()

	def keyOk(self):
		if self.focus == FOCUS_STREAMS and self["streams"].list:
			cur = self["streams"].getCurrent()
			if self.settings.menupage.getValue() == PAGE_AUDIO and cur[0] is not None:
				self.changeAudio(cur[0])
				self.__updatedInfo()
			if self.settings.menupage.getValue() == PAGE_SUBTITLES and cur[0] is not None:
				if self.infobar.selected_subtitle == cur[0]:
					self.enableSubtitle(None)
					selectedidx = self["streams"].getIndex()
					self.__updatedInfo()
					self["streams"].setIndex(selectedidx)
				else:
					self.enableSubtitle(cur[0])
					self.__updatedInfo()
			self.close(0)
		elif self.focus == FOCUS_CONFIG:
			self.keyRight()

	def cancel(self):
		self.close(0)

class SubtitleSelection(AudioSelection):
	def __init__(self, session, infobar=None):
		AudioSelection.__init__(self, session, infobar, page=PAGE_SUBTITLES)
		self.skinName = ["AudioSelection"]
