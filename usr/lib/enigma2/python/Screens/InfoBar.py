from Tools.Profile import profile

# workaround for required config entry dependencies.
from Screens.MovieSelection import MovieSelection

from Screen import Screen

profile("LOAD:enigma")
from enigma import iPlayableService

profile("LOAD:InfoBarGenerics")
from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarRdsDecoder, \
	InfoBarEPG, InfoBarSeek, InfoBarInstantRecord, InfoBarRedButton, \
	InfoBarAudioSelection, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey, \
	InfoBarSubserviceSelection, InfoBarShowMovies, InfoBarTimeshift,  \
	InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSimpleEventView, \
	InfoBarSummarySupport, InfoBarMoviePlayerSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions, \
	InfoBarSubtitleSupport, InfoBarPiP, InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarJobman

profile("LOAD:InitBar_Components")
from Components.ActionMap import HelpableActionMap, NumberActionMap
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.SystemInfo import SystemInfo

profile("LOAD:HelpableScreen")
from Screens.HelpMenu import HelpableScreen

class InfoBar(InfoBarBase, InfoBarShowHide,
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder,
	InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton,
	HelpableScreen, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey,
	InfoBarSubserviceSelection, InfoBarTimeshift, InfoBarSeek,
	InfoBarSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions,
	InfoBarPiP, InfoBarPlugins, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarJobman,
	Screen):
	
	ALLOW_SUSPEND = True
	instance = None

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(self, "InfobarActions",
			{
				"showMovies": (self.showMovies, _("Play recorded movies...")),
				"showRadio": (self.showRadio, _("Show the radio player...")),
				"showTv": (self.showTv, _("Show the tv player...")),
				"showSubtitle":(self.showSubtitle, _("Show the Subtitle...")),
			}, prio=2)
		
		self.allowPiP = True
		self.allowPiPSwap = True
		
		for x in HelpableScreen, \
				InfoBarBase, InfoBarShowHide, \
				InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder, \
				InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarUnhandledKey, \
				InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarSubserviceSelection, \
				InfoBarTimeshift, InfoBarSeek, InfoBarSummarySupport, InfoBarTimeshiftState, \
				InfoBarTeletextPlugin, InfoBarExtensions, InfoBarPiP, InfoBarSubtitleSupport, InfoBarJobman, \
				InfoBarPlugins, InfoBarServiceErrorPopupSupport:
			x.__init__(self)

		self.helpList.append((self["actions"], "InfobarActions", [("showMovies", _("view recordings..."))]))
		self.helpList.append((self["actions"], "InfobarActions", [("showRadio", _("hear radio..."))]))

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
			})

		self.current_begin_time=0
		assert InfoBar.instance is None, "class InfoBar is a singleton class and just one instance of this class is allowed!"
		InfoBar.instance = self

	def __onClose(self):
		InfoBar.instance = None

	def __eventInfoChanged(self):
		if self.execing:
			service = self.session.nav.getCurrentService()
			old_begin_time = self.current_begin_time
			info = service and service.info()
			ptr = info and info.getEvent(0)
			self.current_begin_time = ptr and ptr.getBeginTime() or 0
			if config.usage.show_infobar_on_event_change.value:
				if old_begin_time and old_begin_time != self.current_begin_time:
					self.doShow()
			if self.session.pipshown and self.session.is_splitscreen:
				self.session.pip.updateServiceInfo()

	def __checkServiceStarted(self):
		self.__serviceStarted(True)
		self.onExecBegin.remove(self.__checkServiceStarted)

	def serviceStarted(self):  #override from InfoBarShowHide
		new = self.servicelist.newServicePlayed()
		if self.execing:
			InfoBarShowHide.serviceStarted(self)
			self.current_begin_time=0
		elif not self.__checkServiceStarted in self.onShown and new:
			self.onShown.append(self.__checkServiceStarted)

	def __checkServiceStarted(self):
		self.serviceStarted()
		self.onShown.remove(self.__checkServiceStarted)

	def showTv(self):
		self.showTvChannelList(True)

	def showRadio(self):
		if config.usage.e1like_radio_mode.value:
			self.showRadioChannelList(True)
		else:
			self.rds_display.hide() # in InfoBarRdsDecoder
			from Screens.ChannelSelection import ChannelSelectionRadio
			self.session.openWithCallback(self.ChannelSelectionRadioClosed, ChannelSelectionRadio, self)

	def ChannelSelectionRadioClosed(self, *arg):
		self.rds_display.show()  # in InfoBarRdsDecoder

	def showMovies(self):
		if self.session.pipshown:
			self.toggle_pip_zap()
		else:
			from Screens.MovieSelection import MovieSelection
			self.session.openWithCallback(self.movieSelected, MovieSelection)

	def movieSelected(self, service):
		if service is not None:
			self.session.open(MoviePlayer, service)

	def showSubtitle(self):
		from Screens.Subtitles import Subtitles
		self.session.open(Subtitles)

from EpgSelection import EPGSelection
from Screens.InfoBarGenerics import SimpleServicelist, NumberZapWithName, NumberZap
from random import randint

class MoviePlayer(InfoBarBase, InfoBarShowHide, \
		InfoBarMenu, \
		InfoBarSeek, InfoBarShowMovies, InfoBarAudioSelection, HelpableScreen, InfoBarNotifications,
		InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSimpleEventView,
		InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin,
		InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarPiP, InfoBarInstantRecord, InfoBarEPG):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True
		
	def __init__(self, session, service):
		Screen.__init__(self, session)
		
		self.allowPiP = SystemInfo["CanPiP"]
		self.allowPiPSwap = False
		try:
			import Plugins.Extensions.GraphMultiEPG.plugin
			self.zap_to_orig = Plugins.Extensions.GraphMultiEPG.plugin.zapToService
			Plugins.Extensions.GraphMultiEPG.plugin.zapToService = self.zapToServiceGMEPG
		except ImportError:
			self.zap_to_orig = False
		
		vtiactions = {
				"showEPGBar":(self.showEPGBar, _("show service EPGBar...")),
				"showSingleEPG":(self.showSingleEPG, _("show single service EPG...")),
				"setPlayMode":(self.setPlayMode, _("change play mode...")),
			}
		if self.allowPiP:
			vtiactions.update({"show_hide_pip": (self.showPiP, _("(de)activate Picture in Picture..."))})
		
		if config.usage.movielist_leave_exit.value:
			vtiactions["cancel"] = (self.hideOrExit, _("leave movie player..."))
		
		self["actionsVTi"] = HelpableActionMap(self, "MoviePlayerActionsVTi",vtiactions,-1)
		
		self["NumberActions"] = NumberActionMap( [ "NumberActions"],
			{
				"1": self.keyNumber,
				"2": self.keyNumber,
				"3": self.keyNumber,
				"4": self.keyNumber,
				"5": self.keyNumber,
				"6": self.keyNumber,
				"7": self.keyNumber,
				"8": self.keyNumber,
				"9": self.keyNumber,
				"0": self.keyNumber,
			}, -2)
		
		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"showSubtitle":(self.showSubtitle, _("Show the Subtitle...")),
				"leavePlayer": (self.leavePlayer, _("leave movie player...")),
			})

		self["ChannelUpDownActions"] = HelpableActionMap(self, "ChannelUpDownActions",
			{
				"channelUp": (self.nextMedia, _("Play next media file in directory")),
				"channelDown": (self.previousMedia, _("Play previous media file in directory")),
			})

		for x in HelpableScreen, InfoBarShowHide, InfoBarMenu, \
				InfoBarBase, InfoBarSeek, InfoBarShowMovies, \
				InfoBarAudioSelection, InfoBarNotifications, InfoBarSimpleEventView, \
				InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, \
				InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, \
				InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions, \
				InfoBarPlugins, InfoBarPiP, InfoBarInstantRecord:
			x.__init__(self)
		self.movie_playlist = None
		self.random_play = None
		self.playmode = None
		self.movie_start_config = None
		self.random_history = []
		if isinstance(service, tuple):
			self.movie_playlist = service[1]
			if len(service) >= 3:
				self.playmode = service[2]
				if self.playmode:
					self.movie_start_config = config.usage.on_movie_start.value
					config.usage.on_movie_start.value = "beginning"
			service = service[0]
		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()
		if service:
			config.usage.movielist_last_played_movie.value = service.toString()
			config.usage.movielist_last_played_movie.save()
		session.nav.playService(service)
		self.returning = False
		self.InfoBar_Instance = None
		self.orig_openSingleServiceEPG = InfoBar.openSingleServiceEPG
		InfoBar.openSingleServiceEPG = self.movieEPG
		self.got_service_sel = None
		self.__InfoBar_Instance__()
		self.onClose.append(self.__onClose)

	def hideOrExit(self):
		if self.session.pipshown:
			return
		else:
			if not self.shown:
				self.leavePlayer()
			else:
				self.toggleShow()

	def __onClose(self):
		InfoBar.openSingleServiceEPG = self.orig_openSingleServiceEPG
		if self.InfoBar_Instance:
			self.InfoBar_Instance.isEPGBar = False
		if self.zap_to_orig:
			try:
				import Plugins.Extensions.GraphMultiEPG.plugin
				Plugins.Extensions.GraphMultiEPG.plugin.zapToService = self.zap_to_orig
			except ImportError:
				pass
		self.session.nav.playService(self.lastservice)

	def handleLeave(self, how):
		if self.session.pipshown:
			self.InfoBar_Instance.showPiP()
		self.is_closing = True
		if not self.playmode and how == "ask":
			if config.usage.setup_level.index < 2: # -expert
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue")
				)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("Yes, returning to movie list"), "movielist"),
					(_("Yes, and delete this movie"), "quitanddelete"),
					(_("Yes, delete this movie and go back to movie list"), "quit_and_delete_movielist"),
					(_("Yes, and play next media file"), "playnext"),
					(_("No"), "continue"),
					(_("No, but restart from begin"), "restart"),
				)

			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
		elif self.playmode and self.playmode in ("random", "loop"):
			self.leavePlayerConfirmed([True, "playnext"])
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		self.playmode = None
		if self.movie_start_config:
			config.usage.on_movie_start.value = self.movie_start_config
			self.movie_start_config = None
		self.handleLeave(config.usage.on_movie_stop.value)

	def deleteConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "quitanddeleteconfirmed"))

	def deleteConfirmedMovieList(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "quit_and_delete_confirmed_movielist"))

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]

		if answer in ("quitanddelete", "quitanddeleteconfirmed", "quit_and_delete_movielist", "quit_and_delete_confirmed_movielist"):
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			from enigma import eServiceCenter
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(ref)
			name = info and info.getName(ref) or _("this recording")

			if answer == "quitanddelete":
				from Screens.MessageBox import MessageBox
				self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do you really want to delete %s?") % name)
				return

			elif answer == "quitanddeleteconfirmed" or answer == "quit_and_delete_confirmed_movielist":
				if not self.delete_service(ref, serviceHandler):
					return

			elif answer == "quit_and_delete_movielist":
				from Screens.MessageBox import MessageBox
				self.session.openWithCallback(self.deleteConfirmedMovieList, MessageBox, _("Do you really want to delete %s?") % name)
				return

		if answer in ("quit", "quitanddeleteconfirmed"):
			self.close()
		elif answer == "quit_and_delete_confirmed_movielist":
			ref = None
			if self.movie_playlist is not None and len(self.movie_playlist) > 1:
				cur_ref = self.session.nav.getCurrentlyPlayingServiceReference()
				new_idx = self.movie_playlist.index(cur_ref) - 1
				if new_idx < 0:
					new_idx = 0
				ref = self.movie_playlist[new_idx]
			self.session.nav.stopService()
			self.returning = True
			from Screens.MovieSelection import MovieSelection
			self.session.openWithCallback(self.movieSelected, MovieSelection, ref)
		elif answer == "movielist":
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			self.returning = True
			from Screens.MovieSelection import MovieSelection
			self.session.openWithCallback(self.movieSelected, MovieSelection, ref)
			self.session.nav.stopService()
			if config.usage.movielist_support_pig.value:
				self.session.nav.playService(self.lastservice)
			
		elif answer == "restart":
			self.doSeek(0)
			self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer == "playnext":
			self.nextMedia()

	def delete_service(self, ref, serviceHandler):
		from Screens.MessageBox import MessageBox
		if config.usage.movielist_use_trash_dir.value:
			from Screens.MovieSelection import getTrashDir
			from Components.FileTransfer import FileTransferJob
			from Components.Task import job_manager
			trash_dir = getTrashDir(ref.getPath())
			if trash_dir:
				src_file = str(ref.getPath())
				dst_file = trash_dir
				if dst_file.endswith("/"):
					dst_file = trash_dir[:-1]
				text = _("remove")
				job_manager.AddJob(FileTransferJob(src_file,dst_file, False, False, "%s : %s" % (text, src_file)))
			else:
				result_txt = _("Delete failed, because there is no movie trash !\nDisable movie trash in configuration to delete this item")
				self.session.openWithCallback(self.close, MessageBox, result_txt, MessageBox.TYPE_ERROR)
				return False
		else:
			offline = serviceHandler.offlineOperations(ref)
			if offline.deleteFromDisk(0):
				self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)
				return False
		return True

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.handleLeave(config.usage.on_movie_eof.value)

	def showMovies(self):
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		from Screens.MovieSelection import MovieSelection
		self.session.openWithCallback(self.movieSelected, MovieSelection, ref)

	def movieSelected(self, service):
		if service is not None:
			if isinstance(service, tuple):
				self.movie_playlist = service[1]
				if len(service) >= 3:
					self.playmode = service[2]
					if self.playmode:
						self.movie_start_config = config.usage.on_movie_start.value
						config.usage.on_movie_start.value = "beginning"
				service = service[0]
			self.is_closing = False
			config.usage.movielist_last_played_movie.value = service.toString()
			config.usage.movielist_last_played_movie.save()
			self.session.nav.playService(service)
			self.returning = False
		elif self.returning:
			self.close()

	def previousMedia(self):
		if self.session.pipshown:
			self.changePiPService(-1)
		else:
			self.get_next_play_ref(-1)

	def nextMedia(self):
		if self.session.pipshown:
			self.changePiPService(+1)
		else:
			self.get_next_play_ref(+1)

	def get_next_play_ref(self, direction = 1):
		new_ref = None
		if self.movie_playlist:
			cur_ref = self.session.nav.getCurrentlyPlayingServiceReference()
			playlist_len = len(self.movie_playlist)
			if self.playmode and self.playmode == "random":
				if playlist_len > 1:
					cur_idx = new_idx = self.movie_playlist.index(cur_ref)
					if not cur_idx in self.random_history:
						self.random_history.append(cur_idx)
					while 1:
						new_idx = randint(0, playlist_len -1)
						if new_idx in self.random_history:
							continue
						self.random_history.append(new_idx)
						if len(self.random_history) >= playlist_len:
							self.random_history = []
						break
					new_ref = self.movie_playlist[new_idx]
			else:
				for ref in self.movie_playlist:
					if ref == cur_ref:
						idx = self.movie_playlist.index(ref) + direction
						if idx < playlist_len and idx >= 0:
							new_ref = self.movie_playlist[idx]
						elif idx < 0:
							idx = playlist_len -1
							new_ref = self.movie_playlist[idx]
						elif idx >= playlist_len:
							new_ref = self.movie_playlist[0]
						break
		if new_ref:
			self.movieSelected(new_ref)

	def showSubtitle(self):
		from Screens.Subtitles import Subtitles
		self.session.open(Subtitles)

	def setPlayMode(self):
		if len(self.movie_playlist):
			choicelist = (
					(_("Default play mode"), "default"),
					(_("Shuffle play"), "random"),
					(_("Play all"), "loop"),
				)
			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.playModeChanged, ChoiceBox, title=_("Please select play mode :"), list = choicelist)

	def playModeChanged(self, answer):
		if answer:
			answer = answer[1]
			if answer == "default":
				if self.movie_start_config:
					config.usage.on_movie_start.value = self.movie_start_config
					self.movie_start_config = None
				self.playmode = None
			elif answer in ("loop", "random"):
				if not self.movie_start_config:
					self.movie_start_config = config.usage.on_movie_start.value
					config.usage.on_movie_start.value = "beginning"
				self.playmode = answer

	def showSingleEPG(self):
		self.showEPG(isEPGBar = False)
		
	def showEPGBar(self):
		self.showEPG(isEPGBar = True)

	def __InfoBar_Instance__(self):
		from Screens.InfoBar import InfoBar 
		self.InfoBar_Instance = InfoBar.instance
		self.servicelist = self.InfoBar_Instance.servicelist
		self.changeServiceCB = self.InfoBar_Instance.changeServiceCB
		self.bouquetSwitcher = self.InfoBar_Instance.bouquetSwitcher
		self.EPGBarNumberZap = self.InfoBar_Instance.EPGBarNumberZap
		self.EPGBar_PiP_on = self.InfoBar_Instance.EPGBar_PiP_on

	def showEPG(self, isEPGBar):
		self.InfoBar_Instance.isEPGBar = isEPGBar
		self.movieEPG(isEPGBar = isEPGBar)

	def togglePiP(self, ref):
		if self.session.pipshown:
			self.InfoBar_Instance.EPGBar_PiP_on = False
		else:
			self.InfoBar_Instance.EPGBar_PiP_on = True
		self.InfoBar_Instance.showPiP()
		if self.session.pipshown and ref:
			self.session.pip.playService(ref)

	def zapToService(self, service, check_correct_bouquet = True):
		if not service is None:
			if self.InfoBar_Instance.isEPGBar and (config.usage.pip_in_EPGBar.value or self.InfoBar_Instance.EPGBar_PiP_on):
				self.showPiP()
			self.set_service_in_ServiceList(service)
			self.InfoBar_Instance.EPGBar_PiP_on = False
			self.handleLeave("quit")

	def zapToServiceGMEPG(self, service):
		print "not implemented yet"

	def getSimpleServiceList(self):
		ref = self.lastservice
		if ref:
			if self.servicelist.getMutableList() is not None:
				current_path = self.servicelist.getRoot()
				self.epg_bouquet = current_path
				bouquets = self.servicelist.getBouquetList()
				services = []
				for bouquet in bouquets:
					tmp_services = self.getBouquetServices(bouquet[1])
					services.extend(tmp_services)
				self.got_service_sel = True
				self.InfoBar_Instance.serviceSel = SimpleServicelist(services)
				if config.usage.quickzap_bouquet_change.value:
					self.InfoBar_Instance.serviceSel_one_Bouquet = self.InfoBar_Instance.serviceSel
				else:
					services = self.getBouquetServices(current_path)
					self.InfoBar_Instance.serviceSel_one_Bouquet = SimpleServicelist(services)

	def movieEPG(self, isEPGBar = False):
		ref = self.lastservice
		if not self.got_service_sel:
			self.getSimpleServiceList()
		if ref:
			if isEPGBar:
				self.InfoBar_Instance.isEPGBar = True
				if config.usage.pip_in_EPGBar.value:
					self.InfoBar_Instance.handleEPGPiP(ref)
			if self.zap_to_orig and config.usage.epg_default_view.value == "graphicalmultiepg":
				self.InfoBar_Instance.open_selected_EPG_view()
			elif self.InfoBar_Instance.serviceSel.selectService(ref):
				self.session.openWithCallback(self.SingleServiceEPGClosed, EPGSelection, ref, zapFunc = self.zapToService, serviceChangeCB = self.changeServiceCB, isEPGBar = isEPGBar, switchBouquet = self.bouquetSwitcher, EPGNumberZap = self.EPGBarNumberZap, togglePiP = self.togglePiP)
			else:
				self.session.openWithCallback(self.SingleServiceEPGClosed, EPGSelection, ref, zapFunc = self.zapToService, isEPGBar = isEPGBar, togglePiP = self.togglePiP)
		else:
			self.session.open(EPGSelection, ref)

	def showPiP(self, ref = None):
		if self.session.pipshown:
			self.InfoBar_Instance.del_hide_timer()
			del self.session.pip
			self.InfoBar_Instance.setPiP_globals()
			self.toggleShow() # HACK / WORKAROUND for long EXIT button press, which calls short EXIT button press after button release
		else:
			if not self.got_service_sel:
				self.getSimpleServiceList()
			if not ref:
				ref = self.lastservice
			if config.usage.default_pip_mode.value == "splitscreen":
				self.InfoBar_Instance.showSplitScreen()
			else:
				self.InfoBar_Instance.showPiP()
			if self.session.pipshown and ref:
				self.InfoBar_Instance.serviceSel.selectService(ref)
				self.session.pip.playService(ref)
				self.session.pip_in_movieplayer = True
				self.InfoBar_Instance.show_zap_focus_text()

	def changePiPService(self, direction):
		if not self.got_service_sel:
			self.getSimpleServiceList()
		if self.InfoBar_Instance.serviceSel_one_Bouquet:
			if direction > 0:
				self.InfoBar_Instance.serviceSel_one_Bouquet.nextService()
			else:
				self.InfoBar_Instance.serviceSel_one_Bouquet.prevService()
			new_ref = self.InfoBar_Instance.serviceSel_one_Bouquet.currentService().ref
			self.set_service_in_ServiceList(new_ref)
			self.set_new_PiP_service(new_ref)

	def set_new_PiP_service(self, new_ref):
		ref=self.session.nav.getCurrentlyPlayingServiceReference()
		if ref == new_ref:
			if self.session.pipshown:
				self.showPiP()
		else:
			if not self.session.pipshown:
				self.showPiP()
			if self.session.pipshown and new_ref:
				self.session.pip.playService(new_ref)

	def set_service_in_ServiceList(self, service):
		self.InfoBar_Instance.epg_bouquet = self.InfoBar_Instance.bouquetSearchHelper(service)[1]
		if self.InfoBar_Instance.servicelist.getRoot() != self.InfoBar_Instance.epg_bouquet:
			self.InfoBar_Instance.servicelist.clearPath()
			if self.InfoBar_Instance.servicelist.bouquet_root != self.InfoBar_Instance.epg_bouquet:
				self.InfoBar_Instance.servicelist.enterPath(self.InfoBar_Instance.servicelist.bouquet_root)
			self.InfoBar_Instance.servicelist.enterPath(self.InfoBar_Instance.epg_bouquet)
		self.InfoBar_Instance.servicelist.setCurrentSelection(service)
		self.InfoBar_Instance.servicelist.saveChannel(service)
		self.InfoBar_Instance.servicelist.saveRoot()
		self.lastservice = service
		self.InfoBar_Instance.servicelist.addToHistory(self.lastservice)

	def keyNumber(self, number):
		if self.session.pipshown:
			if number == 0:
				self.pipDoHandle0Action()
			else:
				if config.usage.numberzap_show_servicename.value:
					bouquet = self.servicelist.bouquet_root
					self.session.openWithCallback(self.numberEntered, NumberZapWithName, number, bouquet)
				else:
					self.session.openWithCallback(self.numberEntered, NumberZap, number)
		else:
			time = None
			if number == 0:
				self.toggleMark()
			elif number == 1:
				time = -config.seek.selfdefined_13.value
			elif number == 3:
				time = config.seek.selfdefined_13.value
			elif number == 4:
				time = -config.seek.selfdefined_46.value
			elif number == 6:
				time = config.seek.selfdefined_46.value
			elif number == 7:
				time = -config.seek.selfdefined_79.value
			elif number == 9:
				time = config.seek.selfdefined_79.value
			if time:
				self.doSeekRelative(time * 90000)

	def numberEntered(self, retval):
		if retval > 0:
			if not self.got_service_sel:
				self.getSimpleServiceList()
			if self.InfoBar_Instance.serviceSel.selectServiceidx(retval - 1):
				new_ref = self.InfoBar_Instance.serviceSel.currentService().ref
				self.set_service_in_ServiceList(new_ref)
				self.set_new_PiP_service(new_ref)

	def pipDoHandle0Action(self):
		use = config.usage.pip_zero_button.value
		if "swap" == use:
			return
		elif "swapstop" == use:
			self.showPiP()
			self.close()
		elif "stop" == use:
			self.showPiP()

	def toggle_pip_zap(self):
		pass
