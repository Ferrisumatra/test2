from ChannelSelection import ChannelSelection, BouquetSelector, SilentBouquetSelector

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ActionMap import NumberActionMap
from Components.Harddisk import harddiskmanager
from Components.Input import Input
from Components.Label import Label
from Components.PluginComponent import plugins
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.Boolean import Boolean
from Components.Sources.ServiceEvent import ServiceEvent
from Components.config import config, ConfigBoolean, ConfigClock
from Components.SystemInfo import SystemInfo
from Components.UsageConfig import preferredInstantRecordPath, defaultMoviePath
from EpgSelection import EPGSelection
from Plugins.Plugin import PluginDescriptor

from Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.Dish import Dish
from Screens.EventView import EventViewEPGSelect, EventViewSimple, EventViewMovieEvent
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.TimerSelection import TimerSelection
from Screens.PictureInPicture import PictureInPicture
from Screens.PiGDummy import PiGDummy
from Screens.SplitScreen import SplitScreen
from Screens.SubtitleDisplay import SubtitleDisplay
from Screens.RdsDisplay import RdsInfoDisplay, RassInteractive
from Screens.TimeDateInput import TimeDateInput
from Screens.UnhandledKey import UnhandledKey
from ServiceReference import ServiceReference

from Tools import Notifications
from Tools.Directories import fileExists
from Tools.MovieInfoParser import getExtendedMovieDescription

from enigma import eTimer, eServiceCenter, eDVBServicePMTHandler, iServiceInformation, \
	iPlayableService, eServiceReference, eEPGCache, eActionMap

from time import time, localtime, strftime
from os import stat as os_stat, path as os_path
from bisect import insort

from RecordTimer import RecordTimerEntry, RecordTimer

# hack alert!
from Menu import MainMenu, mdom

class InfoBarDish:
	def __init__(self):
		self.dishDialog = self.session.instantiateDialog(Dish)
		self.dishDialog.setAnimationMode(0)

class InfoBarUnhandledKey:
	def __init__(self):
		self.unhandledKeyDialog = self.session.instantiateDialog(UnhandledKey)
		self.unhandledKeyDialog.setAnimationMode(0)
		self.hideUnhandledKeySymbolTimer = eTimer()
		self.hideUnhandledKeySymbolTimer.callback.append(self.unhandledKeyDialog.hide)
		self.checkUnusedTimer = eTimer()
		self.checkUnusedTimer.callback.append(self.checkUnused)
		self.onLayoutFinish.append(self.unhandledKeyDialog.hide)
		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.actionA) #highest prio
		eActionMap.getInstance().bindAction('', 0x7FFFFFFF, self.actionB) #lowest prio
		self.flags = (1<<1);
		self.uflags = 0;

	#this function is called on every keypress!
	def actionA(self, key, flag):
		if flag != 4:
			if self.flags & (1<<1):
				self.flags = self.uflags = 0
			self.flags |= (1<<flag)
			if flag == 1: # break
				self.checkUnusedTimer.start(0, True)
		return 0

	#this function is only called when no other action has handled this key
	def actionB(self, key, flag):
		if flag != 4:
			self.uflags |= (1<<flag)

	def checkUnused(self):
		if self.flags == self.uflags:
			self.unhandledKeyDialog.show()
			self.hideUnhandledKeySymbolTimer.start(2000, True)

class InfoBarShowHide:
	""" InfoBar show/hide control, accepts toggleShow and hide actions, might start
	fancy animations. """
	STATE_HIDDEN = 0
	STATE_HIDING = 1
	STATE_SHOWING = 2
	STATE_SHOWN = 3

	def __init__(self):
		self["ShowHideActions"] = ActionMap( ["InfobarShowHideActions"] ,
			{
				"toggleShow": self.toggleShow,
				"hide": self.hide,
			}, 1) # lower prio to make it possible to override ok and cancel..

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evStart: self.serviceStarted,
			})

		self.__state = self.STATE_SHOWN
		self.__locked = 0

		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.doTimerHide)
		self.hideTimer.start(5000, True)

		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)
		self.unlockTimer = eTimer()
		self.unlockTimer.callback.append(self.unlockEXIT)

	def unlockEXIT(self):
		self.exit_locked = False
		self.unlockTimer.stop()

	def serviceStarted(self):
		if self.execing:
			if config.usage.show_infobar_on_zap.value:
				if self.session.pipshown and self.session.is_splitscreen:
					if config.usage.show_infobar_on_splitscreen.value:
						self.doShow()
				else:
					self.doShow()

	def __onShow(self):
		self.__state = self.STATE_SHOWN
		self.startHideTimer()

	def startHideTimer(self):
		if self.__state == self.STATE_SHOWN and not self.__locked:
			idx = config.usage.infobar_timeout.index
			if idx:
				self.hideTimer.start(idx*1000, True)

	def __onHide(self):
		self.__state = self.STATE_HIDDEN
		self.exit_locked = True
		self.unlockTimer.start(500, True)

	def doShow(self):
		self.show()
		self.startHideTimer()

	def doTimerHide(self):
		self.hideTimer.stop()
		if self.__state == self.STATE_SHOWN:
			self.hide()

	def toggleShow(self):
		if self.__state == self.STATE_SHOWN:
			self.hide()
			self.hideTimer.stop()
		elif self.__state == self.STATE_HIDDEN:
			self.show()
			if config.usage.disable_infobar_timeout_okbutton.value:
				self.hideTimer.stop()

	def lockShow(self):
		self.__locked = self.__locked + 1
		if self.execing:
			self.show()
			self.hideTimer.stop()

	def unlockShow(self):
		self.__locked = self.__locked - 1
		if self.execing:
			self.startHideTimer()

#	def startShow(self):
#		self.instance.m_animation.startMoveAnimation(ePoint(0, 600), ePoint(0, 380), 100)
#		self.__state = self.STATE_SHOWN
#
#	def startHide(self):
#		self.instance.m_animation.startMoveAnimation(ePoint(0, 380), ePoint(0, 600), 100)
#		self.__state = self.STATE_HIDDEN

class NumberZapWithName(Screen):
	skin = """
		<screen name="NumberZapWithName" position="center,center" size="425,130" title="%s">
			<widget alphatest="blend" position="300,35" render="Picon" size="100,60" source="Service" transparent="1" zPosition="1">
				<convert type="ServiceName">Reference</convert>
			</widget>
			<widget name="servicenumber" position="10,14" size="290,30" font="Regular;24" halign="center" />
			<widget name="servicename" position="10,50" size="290,30" font="Regular;24" halign="center" />
			<widget name="servicebouquet" position="10,86" size="290,30" font="Regular;24" halign="center" />
		</screen>
		""" % (_("Channel"))

	def quit(self):
		self.Timer.stop()
		self.close(0)

	def keyOK(self):
		self.Timer.stop()
		self.close(int(self.my_number))

	def keyNumberGlobal(self, number):
		bouquet = self.bouquet
		self.my_number = int(str(self.my_number) + str(number))
		if len(str(self.my_number)) >= 4:
			self.keyOK()
		service_name, bouquet_name = self.getServiceName(self.my_number, bouquet)
		if service_name == None:
			service_name = _("not available")
		if bouquet_name == None:
			bouquet_name = _("not available")
		self.Timer.start(self.timer_duration, True)
		if config.usage.numberzap_show_picon.value:
			self["Service"].newService(self.myservice)
		self["servicenumber"].setText(str(self.my_number))
		self["servicename"].setText(str(service_name))
		self["servicebouquet"].setText(str(bouquet_name))

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if not servicelist is None:
			while num:
				serviceIterator = servicelist.getNext()
				if not serviceIterator.valid(): #check end of list
					break
				playable = not (serviceIterator.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
				if playable:
					num -= 1;
			if not num: #found service with searched number ?
				return serviceIterator, 0
		return None, num

	def getServiceName(self, number, bouquet):
		myservice = None
		serviceHandler = eServiceCenter.getInstance()
		
		if not config.usage.multibouquet.value:
			myservice, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		else:
			bouquetlist = serviceHandler.list(bouquet)
			if not bouquetlist is None:
				while number:
					bouquet = bouquetlist.getNext()
					if not bouquet.valid(): #check end of list
						break
					if bouquet.flags & eServiceReference.isDirectory:
						myservice, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		if myservice:
			self.myservice = myservice
			bouquetinfo = serviceHandler.info(bouquet)
			bouquet_name = bouquetinfo.getName(bouquet)
			info = serviceHandler.info(myservice)
			service_name = info.getName(myservice)
			return service_name, bouquet_name
		else:
			self.myservice = None
			return None, None

	def initPicons(self):
		self["Service"].newService(self.myservice)

	def __init__(self, session, number, bouquet):
		Screen.__init__(self, session)
		self["Service"] = ServiceEvent()
		self.my_number = number
		self.bouquet = bouquet
		self.field = ""
		myservice_name, bouquet_name = self.getServiceName(number, bouquet)

		self["servicenumber"] = Label(str(number))
		self["servicename"] = Label(myservice_name)
		self["servicebouquet"] = Label(bouquet_name)

		self["actions"] = NumberActionMap( [ "SetupActions" ],
			{
				"cancel": self.quit,
				"ok": self.keyOK,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal
			})

		self.timer_duration = config.usage.numberzap_timeout.value
		self.Timer = eTimer()
		self.Timer.callback.append(self.keyOK)
		self.Timer.start(self.timer_duration, True)
		if config.usage.numberzap_show_picon.value:
			self.onLayoutFinish.append(self.initPicons)

class NumberZap(Screen):
	def quit(self):
		self.Timer.stop()
		self.close(0)

	def keyOK(self):
		self.Timer.stop()
		self.close(int(self["number"].getText()))

	def keyNumberGlobal(self, number):
		self.Timer.start(self.timer_duration, True)		#reset timer
		self.field = self.field + str(number)
		self["number"].setText(self.field)
		if len(self.field) >= 4:
			self.keyOK()

	def __init__(self, session, number):
		Screen.__init__(self, session)
		self.field = str(number)

		self["channel"] = Label(_("Channel:"))

		self["number"] = Label(self.field)

		self["actions"] = NumberActionMap( [ "SetupActions" ],
			{
				"cancel": self.quit,
				"ok": self.keyOK,
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal
			})

		self.timer_duration = config.usage.numberzap_timeout.value
		self.Timer = eTimer()
		self.Timer.callback.append(self.keyOK)
		self.Timer.start(self.timer_duration, True)

class InfoBarNumberZap:
	""" Handles an initial number for NumberZapping """
	def __init__(self):
		self.init_zero_key_timer()
		self["NumberActions"] = NumberActionMap( [ "NumberActions"],
			{
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal,
			})

	def init_zero_key_timer(self):
		self.zero_pressed = False
		self.zero_key_timer = eTimer()
		self.zero_key_timer.callback.append(self.end_zero_key_timer)

	def start_zero_key_timer(self):
		if self.zero_pressed:
			self.zero_pressed = False
			self.zero_key_timer.stop()
			self.execute_zero_action(is_double = True)
		else:
			self.zero_pressed = True
			self.zero_key_timer.start(config.usage.zero_doubleclick_timeout.value)

	def end_zero_key_timer(self):
		if self.zero_pressed:
			self.zero_pressed = False
			self.execute_zero_action(is_double = False)

	def execute_zero_action(self, is_double = False):
		if isinstance(self, InfoBarPiP) and self.pipHandles0Action():
			self.pipDoHandle0Action(is_double)
		elif is_double:
			self.execute_zero_doubleclick_action()
		else:
			self.servicelist.recallPrevService()


	def keyNumberGlobal(self, number):
		if number == 0:
			self.start_zero_key_timer()
		else:
			if self.has_key("TimeshiftActions") and not self.timeshift_enabled:
				if config.usage.numberzap_show_servicename.value:
					bouquet = self.servicelist.bouquet_root
					self.session.openWithCallback(self.numberEntered, NumberZapWithName, number, bouquet)
				else:
					self.session.openWithCallback(self.numberEntered, NumberZap, number)

	def numberEntered(self, retval):
		if retval > 0:
			self.zapToNumber(retval)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if not servicelist is None:
			while num:
				serviceIterator = servicelist.getNext()
				if not serviceIterator.valid(): #check end of list
					break
				playable = not (serviceIterator.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
				if playable:
					num -= 1;
			if not num: #found service with searched number ?
				return serviceIterator, 0
		return None, num

	def zapToNumber(self, number):
		bouquet = self.servicelist.bouquet_root
		service = None
		serviceHandler = eServiceCenter.getInstance()
		# get actual playing service
		servicebeforezap = self.servicelist.getCurrentSelection()
		if not config.usage.multibouquet.value:
			service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		else:
			bouquetlist = serviceHandler.list(bouquet)
			if not bouquetlist is None:
				while number:
					bouquet = bouquetlist.getNext()
					if not bouquet.valid(): #check end of list
						break
					if bouquet.flags & eServiceReference.isDirectory:
						service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		if not service is None:
			if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			if config.usage.overzap_notplayable.value:
				# from ServiceInfo.py get service info
				serviceinfo = serviceHandler.info(service)
				# check if playing is possible => if so, break and zap
				if serviceinfo.isPlayable(service, servicebeforezap):
					self.servicelist.setCurrentSelection(service) #select the service in servicelist
					self.servicelist.zap()
			else:
				self.servicelist.setCurrentSelection(service) #select the service in servicelist
				self.servicelist.zap()

config.misc.initialchannelselection = ConfigBoolean(default = True)

from Components.MenuList import MenuList

class InfoBarZapHistory(Screen):
	ALLOW_SUSPEND = True
	
	def __init__(self, session, service_list):
		self.servicelist = service_list
		self.session = session
		Screen.__init__(self, session)
		self.title = _("Zap History")
		self["ServiceEvent"] = ServiceEvent()
		self["ZapHistoryList"] = MenuList([])
		self["ZapHistoryList"].onSelectionChanged.append(self.selectionChanged)
		self["ZapHistoryList"].enableWrapAround = True
		self["ZAPHistoryActions"] = ActionMap(["OkCancelActions"],
			{
				"cancel": self.keyCancel,
				"ok": self.zapTo,
			})
		self["EPGActions"] = ActionMap(["InfobarEPGActions"],
			{
				"showEventInfo": self.openEPG,
			})
		self.onLayoutFinish.append(self.createList)

	def createList(self):
		cur_ref = self.session.nav.getCurrentlyPlayingServiceReference()
		i = 0
		selection_idx = None
		zap_list = []
		for x in reversed(self.servicelist):
			path = x[:]
			ref = path.pop()
			new_service = (ServiceReference(ref).getServiceName(), ref)
			if new_service not in zap_list:
				zap_list.append(new_service)
			if cur_ref is not None and cur_ref == ref and selection_idx is None:
				selection_idx = i
			i += 1
		self["ZapHistoryList"].setList(zap_list)
		if selection_idx is not None:
			self["ZapHistoryList"].moveToIndex(selection_idx)

	def selectionChanged(self):
		cur = self["ZapHistoryList"].getCurrent()[1]
		self["ServiceEvent"].newService(cur)

	def keyCancel(self):
		self.close(None)

	def zapTo(self):
		idx = self["ZapHistoryList"].getSelectionIndex()
		idx = len(self.servicelist) - (idx + 1)
		self.close(idx)

	def openEPG(self):
		ref = cur = self["ZapHistoryList"].getCurrent()[1]
		self.session.open(EPGSelection, ref)

class InfoBarChannelSelection:
	""" ChannelSelection - handles the channelSelection dialog and the initial
	channelChange actions which open the channelSelection dialog """
	def __init__(self):
		#instantiate forever
		self.servicelist = self.session.instantiateDialog(ChannelSelection)

		self.exit_locked = False

		if config.misc.initialchannelselection.value:
			self.onShown.append(self.firstRun)

		self["ChannelSelectActions"] = HelpableActionMap(self, "InfobarChannelSelection",
			{
				"switchChannelUp": (self.switchChannelUp, _("open servicelist(up)")),
				"switchChannelDown": (self.switchChannelDown, _("open servicelist(down)")),
				"zapUp": (self.zapUp, _("previous channel")),
				"zapDown": (self.zapDown, _("next channel")),
				"historyBack": (self.historyBack, _("previous channel in history")),
				"historyNext": (self.historyNext, _("next channel in history")),
				"openServiceList": (self.openServiceList, _("open servicelist")),
                                "showFavourites": (self.showFavourites, _("show Favourites")),
                                "zapHistory": (self.showZapHistory, _("Zap Histoy")),
			})

	def showZapHistory(self):
		if config.usage.enable_zaphistory.value and not self.shown and not self.session.pipshown and not self.exit_locked:
			self.session.openWithCallback(self.zapToHistoryEntry, InfoBarZapHistory, self.servicelist.history)

	def zapToHistoryEntry(self, idx = None):
		if idx is not None:
			self.servicelist.historyIndex(idx)

	def showFavourites(self):
		if config.usage.show_favourites_bouquetup.value:
			self.servicelist.showFavourites()
		self.openServiceList()
	def showTvChannelList(self, zap=False):
		self.servicelist.setModeTv()
		if zap:
			self.servicelist.zap()
		if config.usage.show_servicelist_at_modeswitch.value:
			self.session.execDialog(self.servicelist)

	def showRadioChannelList(self, zap=False):
		self.servicelist.setModeRadio()
		if zap:
			self.servicelist.zap()
		if config.usage.show_servicelist_at_modeswitch.value:
			self.session.execDialog(self.servicelist)

	def firstRun(self):
		self.onShown.remove(self.firstRun)
		config.misc.initialchannelselection.value = False
		config.misc.initialchannelselection.save()
		self.switchChannelDown()

	def historyBack(self):
		self.servicelist.historyBack()

	def historyNext(self):
		self.servicelist.historyNext()

	def switchChannelUp(self):
		self.servicelist.moveUp()
		self.session.execDialog(self.servicelist)

	def switchChannelDown(self):
		self.servicelist.moveDown()
		self.session.execDialog(self.servicelist)

	def openServiceList(self):
		self.session.execDialog(self.servicelist)

	def zapUp(self):
		if self.servicelist.inBouquet():
			if not self.session.pip_zap_main and isinstance(self, InfoBarPiP) and self.session.pipshown:
				prev = self.session.pip.getCurrentService()
			else:
				prev = self.servicelist.getCurrentSelection()
			# get playing service (not string version)
			prevclean = prev
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value:
						if self.servicelist.atBegin():
							self.servicelist.prevBouquet()
					self.servicelist.moveUp()
					cur = self.servicelist.getCurrentSelection()
					if cur.toString().startswith("-1"):
						self.servicelist.prevBouquet()
						self.servicelist.moveUp()
						cur = self.servicelist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						if config.usage.overzap_notplayable.value:
							# from ServiceInfo.py get service info
							serviceinfo = eServiceCenter.getInstance().info(cur)
							if serviceinfo is not None:
								# check if playing is possible => if so, break and zap
								if serviceinfo.isPlayable(cur, prevclean):
									break
						else:
							break
		else:
			self.servicelist.moveUp()
		self.servicelist.zap()

	def zapDown(self):
		if self.servicelist.inBouquet():
			if not self.session.pip_zap_main and isinstance(self, InfoBarPiP) and self.session.pipshown:
				prev = self.session.pip.getCurrentService()
			else:
				prev = self.servicelist.getCurrentSelection()
			# get playing service (not string version)
			prevclean = prev
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
						self.servicelist.nextBouquet()
					else:
						self.servicelist.moveDown()
					cur = self.servicelist.getCurrentSelection()
					if cur.toString().startswith("-1"):
						self.servicelist.nextBouquet()
						cur = self.servicelist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						if config.usage.overzap_notplayable.value:
							# from ServiceInfo.py get service info
							serviceinfo = eServiceCenter.getInstance().info(cur)
							if serviceinfo is not None:
								# check if playing is possible => if so, break and zap
								if serviceinfo.isPlayable(cur, prevclean):
									break
						else:
							break
		else:
			self.servicelist.moveDown()
		self.servicelist.zap()

class InfoBarMenu:
	""" Handles a menu action, to open the (main) menu """
	def __init__(self):
		self["MenuActions"] = HelpableActionMap(self, "InfobarMenuActions",
			{
				"mainMenu": (self.mainMenu, _("Enter main menu...")),
			})
		self.session.infobar = None

	def mainMenu(self):
		print "loading mainmenu XML..."
		menu = mdom.getroot()
		assert menu.tag == "menu", "root element in menu must be 'menu'!"

		self.session.infobar = self
		# so we can access the currently active infobar from screens opened from within the mainmenu
		# at the moment used from the SubserviceSelection

		self.session.openWithCallback(self.mainMenuClosed, MainMenu, menu)

	def mainMenuClosed(self, *val):
		self.session.infobar = None

class InfoBarSimpleEventView:
	""" Opens the Eventview for now/next """
	def __init__(self):
		self["EPGActions"] = HelpableActionMap(self, "InfobarEPGActions",
			{
				"showEventInfo": (self.openEventView, _("show event details")),
				"showInfobarOrEpgWhenInfobarAlreadyVisible": self.showEventInfoWhenNotVisible,
			})

	def showEventInfoWhenNotVisible(self):
		if self.shown:
			self.openEventView()
		else:
			self.toggleShow()
			return 1

	def openEventView(self):
		epglist = [ ]
		self.epglist = epglist
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		info = service.info()
		ptr=info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr=info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		if epglist:
			self.session.open(EventViewSimple, epglist[0], ServiceReference(ref), self.eventViewCallback)
		elif ref.toString().startswith("4097"):
			seek = self.getSeek()
			length = ""
			if seek:
				length = seek.getLength()
				if not length[0] and length[1] > 1:
					length = length[1] / 90000
					if config.usage.movielist_duration_in_min.value:
						length = "%d min" % (int(length)/60)
					else:
						length = "%02d:%02d:%02d" % (length/3600, length%3600/60, length%60)
			name, ext_desc = getExtendedMovieDescription(ref)
			self.session.open(EventViewMovieEvent, name, ext_desc, length)

	def eventViewCallback(self, setEvent, setService, val): #used for now/next displaying
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0] = epglist[1]
			epglist[1] = tmp
			setEvent(epglist[0])

class SimpleServicelist:
	def __init__(self, services):
		self.services = services
		self.length = len(services)
		self.current = 0

	def selectService(self, service):
		if not self.length:
			self.current = -1
			return False
		else:
			self.current = 0
			while self.services[self.current].ref != service:
				self.current += 1
				if self.current >= self.length:
					return False
		return True

	def nextService(self):
		if not self.length:
			return
		if self.current+1 < self.length:
			self.current += 1
		else:
			self.current = 0

	def prevService(self):
		if not self.length:
			return
		if self.current-1 > -1:
			self.current -= 1
		else:
			self.current = self.length - 1

	def currentService(self):
		if not self.length or self.current >= self.length:
			return None
		return self.services[self.current]

	def currentServiceidx(self):
		if not self.length or self.current >= self.length:
			return None
		return self.current

	def selectServiceidx(self, idx):
		if idx >= self.length:
			return False
		else:
			self.current = idx
		return True

class InfoBarEPG:
	""" EPG - Opens an EPG list when the showEPGList action fires """
	def __init__(self):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedEventInfo: self.__evEventInfoChanged,
			})

		self.has_gmepg = False
		self.isEPGBar = None
		self.EPGBar_PiP_on = False
		self.is_now_next = False
		self.dlg_stack = [ ]
		self.bouquetSel = None
		self.eventView = None
		self["EPGActions"] = HelpableActionMap(self, "InfobarEPGActions",
			{
				"showEPGBar": (self.openEPGBar, _("show service EPGBar...")),
				"showEventInfo": (self.open_selected_EPG_view, _("show EPG...")),
				"showEventInfoPlugin": (self.showEventInfoPlugins, _("list of EPG views...")),
				"showInfobarOrEpgWhenInfobarAlreadyVisible": self.showEventInfoWhenNotVisible,
			})

	def showEventInfoWhenNotVisible(self):
		if self.shown:
			self.openEventView()
		else:
			self.toggleShow()
			return 1

	def zapToService(self, service, check_correct_bouquet = False):
		if not service is None:
			if self.isEPGBar and (config.usage.pip_in_EPGBar.value or self.EPGBar_PiP_on):
				self.showPiP()
			if check_correct_bouquet: # be sure to be in correct bouquet if zapping in SINGLEEPG or EPGBAR (we do not call the bouquetchangeCB !!!)
				self.epg_bouquet = self.bouquetSearchHelper(service)[1]
			if self.servicelist.getRoot() != self.epg_bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != self.epg_bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(self.epg_bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
			self.servicelist.zap()

	def getBouquetServices(self, bouquet):
		services = [ ]
		servicelist = eServiceCenter.getInstance().list(bouquet)
		if not servicelist is None:
			while True:
				service = servicelist.getNext()
				if not service.valid(): #check if end of list
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker): #ignore non playable services
					continue
				services.append(ServiceReference(service))
		return services

	def openBouquetEPG(self, bouquet, withCallback=True):
		services = self.getBouquetServices(bouquet)
		if services:
			self.epg_bouquet = bouquet
			if withCallback:
				self.dlg_stack.append(self.session.openWithCallback(self.closed, EPGSelection, services, self.zapToService, None, self.changeBouquetCB))
			else:
				self.session.open(EPGSelection, services, self.zapToService, None, self.changeBouquetCB)

	def changeBouquetCB(self, direction, epg):
		if self.bouquetSel:
			if direction > 0:
				self.bouquetSel.down()
			else:
				self.bouquetSel.up()
			bouquet = self.bouquetSel.getCurrent()
			services = self.getBouquetServices(bouquet)
			if services:
				self.epg_bouquet = bouquet
				epg.setServices(services)

	def closed(self, ret=False):
		closedScreen = self.dlg_stack.pop()
		if self.bouquetSel and closedScreen == self.bouquetSel:
			self.bouquetSel = None
		elif self.eventView and closedScreen == self.eventView:
			self.eventView = None
		if ret:
			dlgs=len(self.dlg_stack)
			if dlgs > 0:
				self.dlg_stack[dlgs-1].close(dlgs > 1)

	def openMultiServiceEPG(self, withCallback=True):
		bouquets = self.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
		if config.usage.multiepg_ask_bouquet.value:
			self.openMultiServiceEPGAskBouquet(bouquets, cnt, withCallback)
		else:
			self.openMultiServiceEPGSilent(bouquets, cnt, withCallback)

	def openMultiServiceEPGAskBouquet(self, bouquets, cnt, withCallback):
		if cnt > 1: # show bouquet list
			if withCallback:
				self.bouquetSel = self.session.openWithCallback(self.closed, BouquetSelector, bouquets, self.openBouquetEPG, enableWrapAround=True)
				self.dlg_stack.append(self.bouquetSel)
			else:
				self.bouquetSel = self.session.open(BouquetSelector, bouquets, self.openBouquetEPG, enableWrapAround=True)
		elif cnt == 1:
			self.openBouquetEPG(bouquets[0][1], withCallback)

	def openMultiServiceEPGSilent(self, bouquets, cnt, withCallback):
		root = self.servicelist.getRoot()
		rootstr = root.toCompareString()
		current = 0
		for bouquet in bouquets:
			if bouquet[1].toCompareString() == rootstr:
				break
			current += 1
		if current >= cnt:
			current = 0
		if cnt > 1: # create bouquet list for bouq+/-
			self.bouquetSel = SilentBouquetSelector(bouquets, True, self.servicelist.getBouquetNumOffset(root))
		if cnt >= 1:
			self.openBouquetEPG(root, withCallback)

	def changeServiceCB(self, direction, epg):
		if self.serviceSel:
			if direction > 0:
				self.serviceSel.nextService()
			else:
				self.serviceSel.prevService()
			epg.setService(self.serviceSel.currentService())
			if (config.usage.pip_in_EPGBar.value or self.EPGBar_PiP_on) and self.isEPGBar:
				new_ref = self.serviceSel.currentService().ref
				self.handleEPGPiP(new_ref)

	def SingleServiceEPGClosed(self, ret=False):
		if self.session.pipshown:
			self.showPiP()
		self.EPGBar_PiP_on = False
		self.isEPGBar = None
		self.serviceSel = None

	def EPGBarNumberZap(self, number, epg):
		if config.usage.quickzap_bouquet_change.value:
			self.myepg = epg
			if config.usage.numberzap_show_servicename.value:
				bouquet = self.servicelist.bouquet_root
				self.session.openWithCallback(self.EPGBarnumberEntered, NumberZapWithName, number, bouquet)
			else:
				self.session.openWithCallback(self.EPGBarnumberEntered, NumberZap, number)
	
	def EPGBarnumberEntered(self, number):
		if int(number):
			self.serviceSel.selectServiceidx(number - 1)
			new_service = self.serviceSel.currentService()
			self.myepg.setService(new_service)
			if (config.usage.pip_in_EPGBar.value or self.EPGBar_PiP_on) and self.isEPGBar:
				self.handleEPGPiP(new_service.ref)
		self.myepg = None

	def bouquetSearchHelper(self, ref, withBouquets = None):
		bouquets = self.servicelist.getBouquetList()
		service_idx = self.serviceSel.currentServiceidx()
		list_len = 0
		for bouquet in bouquets:
			list_len += len(self.getBouquetServices(bouquet[1]))
			if list_len >= service_idx + 1:
				self.epg_bouquet = bouquet[1]
				break
		if withBouquets:
			return bouquet, bouquets
		else:
			return bouquet

	def bouquetSwitcher(self, service, direction, epg):
		if service and config.usage.quickzap_bouquet_change.value:
			(cur_bouquet, bouquets) = self.bouquetSearchHelper(service, withBouquets=True)
			if len(bouquets) > 1 and (cur_bouquet in bouquets):
				cur_idx = bouquets.index(cur_bouquet)
				if direction < 0:
					next_idx = cur_idx - 1
					if next_idx < 0:
						next_idx = len(bouquets) - 1
				else:
					next_idx = cur_idx + 1
					if next_idx == len(bouquets):
						next_idx = 0
				new_bouquet = bouquets[next_idx]
				list_leng = 0
				for bouquet in bouquets:
					bouquet_len = len(self.getBouquetServices(bouquet[1]))
					list_leng += bouquet_len
					if bouquet == new_bouquet:
						new_service_idx = list_leng - bouquet_len
						break
				self.serviceSel.selectServiceidx(new_service_idx)
				new_service = self.serviceSel.currentService()
				epg.setService(new_service)
				if (config.usage.pip_in_EPGBar.value or self.EPGBar_PiP_on) and self.isEPGBar:
					self.handleEPGPiP(new_service.ref)

	def handleEPGPiP(self, new_ref):
		ref=self.session.nav.getCurrentlyPlayingServiceReference()
		if ref == new_ref:
			if self.session.pipshown:
				self.showPiP()
		else:
			if not self.session.pipshown:
				self.showPiP()
			if self.session.pipshown and new_ref:
				self.session.pip.playService(new_ref)

	def togglePiP(self, ref):
		if self.session.pipshown:
			self.EPGBar_PiP_on = False
		else:
			self.EPGBar_PiP_on = True
		self.showPiP()
		if self.session.pipshown and ref:
			self.session.pip.playService(ref)

	def openEPGBar(self):
		if self.shown:
			self.toggleShow()
		self.isEPGBar = True
		self.openSingleServiceEPG(self.isEPGBar)

	def openSingleServiceEPG(self, isEPGBar = None):
		ref=self.session.nav.getCurrentlyPlayingServiceReference()
		if ref:
			if self.servicelist.getMutableList() is not None: # bouquet in channellist
				current_path = self.servicelist.getRoot()
				self.epg_bouquet = current_path
				if config.usage.quickzap_bouquet_change.value:
					bouquets = self.servicelist.getBouquetList()
					services = []
					for bouquet in bouquets:
						tmp_services = self.getBouquetServices(bouquet[1])
						services.extend(tmp_services)
				else:
					services = self.getBouquetServices(current_path)
				self.serviceSel = SimpleServicelist(services)
				if self.serviceSel.selectService(ref):
					self.session.openWithCallback(self.SingleServiceEPGClosed, EPGSelection, ref, zapFunc = self.zapToService, serviceChangeCB = self.changeServiceCB, isEPGBar = self.isEPGBar, switchBouquet = self.bouquetSwitcher, EPGNumberZap = self.EPGBarNumberZap, togglePiP = self.togglePiP)
				else:
					self.session.openWithCallback(self.SingleServiceEPGClosed, EPGSelection, ref, zapFunc = self.zapToService, isEPGBar = isEPGBar, togglePiP = self.togglePiP)
			else:
				self.session.open(EPGSelection, ref)

	def showEventInfoPlugins(self):
		list = [(p.name, boundFunction(self.runPlugin, p)) for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EVENTINFO)]

		if list:
			list.append((_("show service EPGBar..."), self.openEPGBar))
			list.append((_("show single service EPG..."), self.openSingleServiceEPG))
			list.append((_("Multi EPG"), self.openMultiServiceEPG))
			self.session.openWithCallback(self.EventInfoPluginChosen, ChoiceBox, title=_("Please choose an extension..."), list = list, skin_name = "EPGExtensionsList")
		else:
			self.openSingleServiceEPG()

	def runPlugin(self, plugin):
		plugin(session = self.session, servicelist = self.servicelist)
		
	def EventInfoPluginChosen(self, answer):
		if answer is not None:
			answer[1]()

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def getNowNext(self):
		epglist = [ ]
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		ptr = info and info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr = info and info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		self.epglist = epglist

	def __evEventInfoChanged(self):
		if self.is_now_next and len(self.dlg_stack) == 1:
			self.getNowNext()
			assert self.eventView
			if self.epglist:
				self.eventView.setEvent(self.epglist[0])

	def openEventView(self):
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.getNowNext()
		epglist = self.epglist
		if not epglist:
			self.is_now_next = False
			epg = eEPGCache.getInstance()
			ptr = ref and ref.valid() and epg.lookupEventTime(ref, -1)
			if ptr:
				epglist.append(ptr)
				ptr = epg.lookupEventTime(ref, ptr.getBeginTime(), +1)
				if ptr:
					epglist.append(ptr)
		else:
			self.is_now_next = True
		if epglist:
			self.eventView = self.session.openWithCallback(self.closed, EventViewEPGSelect, self.epglist[0], ServiceReference(ref), self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)
			self.dlg_stack.append(self.eventView)
		else:
			print "no epg for the service avail.. so we show multiepg instead of eventinfo"
			self.openMultiServiceEPG(False)

	def eventViewCallback(self, setEvent, setService, val): #used for now/next displaying
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0]=epglist[1]
			epglist[1]=tmp
			setEvent(epglist[0])

	def open_selected_EPG_view(self):
		if self.has_gmepg is False:
			list = [(p.name, boundFunction(self.runPlugin, p)) for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EVENTINFO)]
			for x in list:
				if x[0] == _("Graphical Multi EPG"):
					self.has_gmepg = x[1]
		if config.usage.epg_default_view.value == "multiepg":
			self.openMultiServiceEPG()
		elif config.usage.epg_default_view.value == "singleepg":
			self.openSingleServiceEPG()
		elif config.usage.epg_default_view.value == "epgbar":
			self.openEPGBar()
		elif self.has_gmepg and config.usage.epg_default_view.value == "graphicalmultiepg":
			self.has_gmepg()
		else:
			self.openEventView()

class InfoBarRdsDecoder:
	"""provides RDS and Rass support/display"""
	def __init__(self):
		self.rds_display = self.session.instantiateDialog(RdsInfoDisplay)
		self.rds_display.setAnimationMode(0)
		self.rass_interactive = None

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEnd: self.__serviceStopped,
				iPlayableService.evUpdatedRassSlidePic: self.RassSlidePicChanged
			})

		self["RdsActions"] = ActionMap(["InfobarRdsActions"],
		{
			"startRassInteractive": self.startRassInteractive
		},-1)

		self["RdsActions"].setEnabled(False)

		self.onLayoutFinish.append(self.rds_display.show)
		self.rds_display.onRassInteractivePossibilityChanged.append(self.RassInteractivePossibilityChanged)

	def RassInteractivePossibilityChanged(self, state):
		self["RdsActions"].setEnabled(state)

	def RassSlidePicChanged(self):
		if not self.rass_interactive:
			service = self.session.nav.getCurrentService()
			decoder = service and service.rdsDecoder()
			if decoder:
				decoder.showRassSlidePicture()

	def __serviceStopped(self):
		if self.rass_interactive is not None:
			rass_interactive = self.rass_interactive
			self.rass_interactive = None
			rass_interactive.close()

	def startRassInteractive(self):
		self.rds_display.hide()
		self.rass_interactive = self.session.openWithCallback(self.RassInteractiveClosed, RassInteractive)

	def RassInteractiveClosed(self, *val):
		if self.rass_interactive is not None:
			self.rass_interactive = None
			self.RassSlidePicChanged()
		self.rds_display.show()

class InfoBarSeek:
	"""handles actions like seeking, pause"""

	SEEK_STATE_PLAY = (0, 0, 0, ">")
	SEEK_STATE_PAUSE = (1, 0, 0, "||")
	SEEK_STATE_EOF = (1, 0, 0, "END")

	def __init__(self, actionmap = "InfobarSeekActions"):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evStart: self.__serviceStarted,

				iPlayableService.evEOF: self.__evEOF,
				iPlayableService.evSOF: self.__evSOF,
			})
		self.fast_winding_hint_message_showed = False

		class InfoBarSeekActionMap(HelpableActionMap):
			def __init__(self, screen, *args, **kwargs):
				HelpableActionMap.__init__(self, screen, *args, **kwargs)
				self.screen = screen

			def action(self, contexts, action):
				print "action:", action
				if action[:5] == "seek:":
					time = int(action[5:])
					self.screen.doSeekRelative(time * 90000)
					return 1
				elif action[:8] == "seekdef:":
					key = int(action[8:])
					time = (-config.seek.selfdefined_13.value, False, config.seek.selfdefined_13.value,
						-config.seek.selfdefined_46.value, False, config.seek.selfdefined_46.value,
						-config.seek.selfdefined_79.value, False, config.seek.selfdefined_79.value)[key-1]
					self.screen.doSeekRelative(time * 90000)
					return 1					
				else:
					return HelpableActionMap.action(self, contexts, action)

		self["SeekActions"] = InfoBarSeekActionMap(self, actionmap,
			{
				"playpauseService": (self.playpauseService, _("continue/pause")),
				"pauseService": (self.pauseService, _("pause")),
				"unPauseService": self.unPauseService,

				"seekFwd": (self.seekFwd, _("skip forward")),
				"seekFwdManual": (self.seekFwdManual, _("skip forward (enter time)")),
				"seekBack": (self.seekBack, _("skip backward")),
				"seekBackManual": (self.seekBackManual, _("skip backward (enter time)"))
			}, prio=-1)
			# give them a little more priority to win over color buttons

		self["SeekActions"].setEnabled(False)

		self.seekstate = self.SEEK_STATE_PLAY
		self.lastseekstate = self.SEEK_STATE_PLAY

		self.onPlayStateChanged = [ ]

		self.lockedBecauseOfSkipping = False

		self.__seekableStatusChanged()

		self.seek_to_eof = int(config.usage.stop_seek_eof.value)

	def makeStateForward(self, n):
		return (0, n, 0, ">> %dx" % n)

	def makeStateBackward(self, n):
		return (0, -n, 0, "<< %dx" % n)

	def makeStateSlowMotion(self, n):
		return (0, 0, n, "/%d" % n)

	def isStateForward(self, state):
		return state[1] > 1

	def isStateBackward(self, state):
		return state[1] < 0

	def isStateSlowMotion(self, state):
		return state[1] == 0 and state[2] > 1

	def getHigher(self, n, lst):
		for x in lst:
			if x > n:
				return x
		return False

	def getLower(self, n, lst):
		lst = lst[:]
		lst.reverse()
		for x in lst:
			if x < n:
				return x
		return False

	def showAfterSeek(self):
		if isinstance(self, InfoBarShowHide):
			self.doShow()

	def up(self):
		pass

	def down(self):
		pass

	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None

		seek = service.seek()

		if seek is None or not seek.isCurrentlySeekable():
			return None

		return seek

	def isSeekable(self):
		if self.getSeek() is None:
			return False

		if self.__class__.__name__ == "InfoBar": # if we have livestreams in bouquets --> the streams are not seekable and we want to zap the "normal" way
			if not self.timeshift_enabled:   # but timeshift is seekable ! 
				return False
		
		return True

	def __seekableStatusChanged(self):
#		print "seekable status changed!"
		if not self.isSeekable():
			self["SeekActions"].setEnabled(False)
#			print "not seekable, return to play"
			self.setSeekState(self.SEEK_STATE_PLAY)
		else:
			self["SeekActions"].setEnabled(True)
#			print "seekable"

	def __serviceStarted(self):
		self.fast_winding_hint_message_showed = False
		self.seekstate = self.SEEK_STATE_PLAY
		self.__seekableStatusChanged()

	def setSeekState(self, state):
		service = self.session.nav.getCurrentService()

		if service is None:
			return False

		if not self.isSeekable():
			if state not in (self.SEEK_STATE_PLAY, self.SEEK_STATE_PAUSE):
				state = self.SEEK_STATE_PLAY

		pauseable = service.pause()

		if pauseable is None:
			print "not pauseable."
			state = self.SEEK_STATE_PLAY

		self.seekstate = state

		if pauseable is not None:
			if self.seekstate[0]:
				print "resolved to PAUSE"
				pauseable.pause()
			elif self.seekstate[1]:
				print "resolved to FAST FORWARD"
				pauseable.setFastForward(self.seekstate[1])
			elif self.seekstate[2]:
				print "resolved to SLOW MOTION"
				pauseable.setSlowMotion(self.seekstate[2])
			else:
				print "resolved to PLAY"
				pauseable.unpause()

		for c in self.onPlayStateChanged:
			c(self.seekstate)

		self.checkSkipShowHideLock()

		return True

	def playpauseService(self):
		if self.seekstate != self.SEEK_STATE_PLAY:
			self.unPauseService()
		else:
			self.pauseService()

	def pauseService(self):
		if self.seekstate == self.SEEK_STATE_PAUSE:
			if config.seek.on_pause.value == "play":
				self.unPauseService()
			elif config.seek.on_pause.value == "step":
				self.doSeekRelative(1)
			elif config.seek.on_pause.value == "last":
				self.setSeekState(self.lastseekstate)
				self.lastseekstate = self.SEEK_STATE_PLAY
		else:
			if self.seekstate != self.SEEK_STATE_EOF:
				self.lastseekstate = self.seekstate
			self.setSeekState(self.SEEK_STATE_PAUSE);

	def unPauseService(self):
		print "unpause"
		if self.seekstate == self.SEEK_STATE_PLAY:
			return 0
		self.setSeekState(self.SEEK_STATE_PLAY)

	def doSeek(self, pts):
		seekable = self.getSeek()
		if seekable is None:
			return
		seekable.seekTo(pts)

	def doSeekRelative(self, pts):
		seekable = self.getSeek()
		if seekable is None:
			return
		prevstate = self.seekstate

		if self.seekstate == self.SEEK_STATE_EOF:
			if prevstate == self.SEEK_STATE_PAUSE:
				self.setSeekState(self.SEEK_STATE_PAUSE)
			else:
				self.setSeekState(self.SEEK_STATE_PLAY)
				
		
		if self.seek_to_eof:
			remaining = self.calcRemainingTime()
			seek_interval = pts / 90
			if remaining < seek_interval:
				len = seekable.getLength()
				play_pos = len[1] - (self.seek_to_eof*1000 * 90)
				self.setSeekState(self.SEEK_STATE_PLAY)
				seekable.seekTo(play_pos)
				self.showAfterSeek()
				return
		
		seekable.seekRelative(pts<0 and -1 or 1, abs(pts))
		if abs(pts) > 100 and config.usage.show_infobar_on_skip.value:
			self.showAfterSeek()

	def seekFwd(self):
		seek = self.getSeek()
		if seek and not (seek.isCurrentlySeekable() & 2):
			media = 1
		else:
			media = 0
#			if not self.fast_winding_hint_message_showed and (seek.isCurrentlySeekable() & 1):
#				self.session.open(MessageBox, _("No fast winding possible yet.. but you can use the number buttons to skip forward/backward!"), MessageBox.TYPE_INFO, timeout=10)
#				self.fast_winding_hint_message_showed = True
#				return
#			return 0 # trade as unhandled action
		if self.seekstate == self.SEEK_STATE_PLAY:
			self.setSeekState(self.makeStateForward(int(config.seek.enter_forward.value)))
		elif self.seekstate == self.SEEK_STATE_PAUSE and media==0:
			if len(config.seek.speeds_slowmotion.value):
				self.setSeekState(self.makeStateSlowMotion(config.seek.speeds_slowmotion.value[-1]))
			else:
				self.setSeekState(self.makeStateForward(int(config.seek.enter_forward.value)))
		elif self.seekstate == self.SEEK_STATE_EOF:
			pass
		elif self.isStateForward(self.seekstate):
			speed = self.seekstate[1]
			if self.seekstate[2]:
				speed /= self.seekstate[2]
			if media==1 and speed == 8:
				speed = 8
				return 0 # trade as unhandled action
			else:
				speed = self.getHigher(speed, config.seek.speeds_forward.value) or config.seek.speeds_forward.value[-1]
			self.setSeekState(self.makeStateForward(speed))
		elif self.isStateBackward(self.seekstate):
			speed = -self.seekstate[1]
			if self.seekstate[2]:
				speed /= self.seekstate[2]
			speed = self.getLower(speed, config.seek.speeds_backward.value)
			if speed:
				self.setSeekState(self.makeStateBackward(speed))
			else:
				self.setSeekState(self.SEEK_STATE_PLAY)
		elif self.isStateSlowMotion(self.seekstate):
			speed = self.getLower(self.seekstate[2], config.seek.speeds_slowmotion.value) or config.seek.speeds_slowmotion.value[0]
			self.setSeekState(self.makeStateSlowMotion(speed))

	def seekBack(self):
		seek = self.getSeek()
		if seek and not (seek.isCurrentlySeekable() & 2):
			media = 1
		else:
			media = 0
#			if not self.fast_winding_hint_message_showed and (seek.isCurrentlySeekable() & 1):
#				self.session.open(MessageBox, _("No fast winding possible yet.. but you can use the number buttons to skip forward/backward!"), MessageBox.TYPE_INFO, timeout=10)
#				self.fast_winding_hint_message_showed = True
#				return
#			return 0 # trade as unhandled action
		seekstate = self.seekstate
		if seekstate == self.SEEK_STATE_PLAY and media==0:
			self.setSeekState(self.makeStateBackward(int(config.seek.enter_backward.value)))
		elif seekstate == self.SEEK_STATE_PLAY and media ==1:
			if not self.fast_winding_hint_message_showed:
				self.session.open(MessageBox, _("No rewinding possible yet.. but you can use the number buttons to skip forward/backward!"), MessageBox.TYPE_INFO, timeout=10)
				self.fast_winding_hint_message_showed = True
				return
			return 0 # trade as unhandled action
		elif seekstate == self.SEEK_STATE_EOF:
			self.setSeekState(self.makeStateBackward(int(config.seek.enter_backward.value)))
			self.doSeekRelative(-6)
		elif seekstate == self.SEEK_STATE_PAUSE and media==0:
			self.doSeekRelative(-1)
		elif self.isStateForward(seekstate):
			speed = seekstate[1]
			if seekstate[2]:
				speed /= seekstate[2]
			speed = self.getLower(speed, config.seek.speeds_forward.value)
			if speed:
				self.setSeekState(self.makeStateForward(speed))
			else:
				self.setSeekState(self.SEEK_STATE_PLAY)
		elif self.isStateBackward(seekstate):
			speed = -seekstate[1]
			if seekstate[2]:
				speed /= seekstate[2]
			speed = self.getHigher(speed, config.seek.speeds_backward.value) or config.seek.speeds_backward.value[-1]
			self.setSeekState(self.makeStateBackward(speed))
		elif self.isStateSlowMotion(seekstate):
			speed = self.getHigher(seekstate[2], config.seek.speeds_slowmotion.value)
			if speed:
				self.setSeekState(self.makeStateSlowMotion(speed))
			else:
				self.setSeekState(self.SEEK_STATE_PAUSE)

	def seekFwdManual(self):
		self.session.openWithCallback(self.fwdSeekTo, MinuteInput)

	def fwdSeekTo(self, minutes):
		print "Seek", minutes, "minutes forward"
		self.doSeekRelative(minutes * 60 * 90000)

	def seekBackManual(self):
		self.session.openWithCallback(self.rwdSeekTo, MinuteInput)

	def rwdSeekTo(self, minutes):
		print "rwdSeekTo"
		self.doSeekRelative(-minutes * 60 * 90000)

	def checkSkipShowHideLock(self):
		wantlock = self.seekstate != self.SEEK_STATE_PLAY

		if config.usage.show_infobar_on_skip.value:
			if self.lockedBecauseOfSkipping and not wantlock:
				self.unlockShow()
				self.lockedBecauseOfSkipping = False

			if wantlock and not self.lockedBecauseOfSkipping:
				self.lockShow()
				self.lockedBecauseOfSkipping = True

	def calcRemainingTime(self):
		seekable = self.getSeek()
		if seekable is not None:
			len = seekable.getLength()
			try:
				tmp = self.cueGetEndCutPosition()
				if tmp:
					len = [False, tmp]
			except:
				pass
			pos = seekable.getPlayPosition()
			speednom = self.seekstate[1] or 1
			speedden = self.seekstate[2] or 1
			if not len[0] and not pos[0]:
				if len[1] <= pos[1]:
					return 0
				time = (len[1] - pos[1])*speedden/(90*speednom)
				return time
		return False
		
	def __evEOF(self):
		if self.seekstate == self.SEEK_STATE_EOF:
			return

		# if we are seeking forward, we try to end up ~1s before the end, and pause there or seek_to_eof is set we skip back and switch to play mode.
		seekstate = self.seekstate
		if self.seekstate != self.SEEK_STATE_PAUSE:
			if self.seek_to_eof and self.seekstate != self.SEEK_STATE_PLAY:
				seekable = self.getSeek()
				if seekable:
					len = seekable.getLength()
					play_pos = len[1] - (self.seek_to_eof*1000 * 90)
					self.setSeekState(self.SEEK_STATE_PLAY)
					seekable.seekTo(play_pos)
					return
			else:
				self.setSeekState(self.SEEK_STATE_EOF)

		if seekstate not in (self.SEEK_STATE_PLAY, self.SEEK_STATE_PAUSE): # if we are seeking
			seekable = self.getSeek()
			if seekable is not None:
				seekable.seekTo(-1)
		if seekstate == self.SEEK_STATE_PLAY: # regular EOF
			self.doEofInternal(True)
		else:
			self.doEofInternal(False)

	def doEofInternal(self, playing):
		pass		# Defined in subclasses

	def __evSOF(self):
		self.setSeekState(self.SEEK_STATE_PLAY)
		self.doSeek(0)

from Screens.PVRState import PVRState, TimeshiftState

class InfoBarPVRState:
	def __init__(self, screen=PVRState, force_show = False):
		self.onPlayStateChanged.append(self.__playStateChanged)
		self.pvrStateDialog = self.session.instantiateDialog(screen)
		self.pvrStateDialog.setAnimationMode(0)
		self.onShow.append(self._mayShow)
		self.onHide.append(self.pvrStateDialog.hide)
		self.force_show = force_show

	def _mayShow(self):
		if self.execing and self.seekstate != self.SEEK_STATE_PLAY:
			self.pvrStateDialog.show()

	def __playStateChanged(self, state):
		playstateString = state[3]
		self.pvrStateDialog["state"].setText(playstateString)
		
		# if we return into "PLAY" state, ensure that the dialog gets hidden if there will be no infobar displayed
		if not config.usage.show_infobar_on_skip.value and self.seekstate == self.SEEK_STATE_PLAY and not self.force_show:
			self.pvrStateDialog.hide()
		else:
			self._mayShow()

class InfoBarTimeshiftState(InfoBarPVRState):
	def __init__(self):
		InfoBarPVRState.__init__(self, screen=TimeshiftState, force_show = True)
		self.__hideTimer = eTimer()
		self.__hideTimer.callback.append(self.__hideTimeshiftState)

	def _mayShow(self):
		if self.execing and self.timeshift_enabled:
			self.pvrStateDialog.show()
			if self.seekstate == self.SEEK_STATE_PLAY and not self.shown:
				self.__hideTimer.start(5*1000, True)

	def __hideTimeshiftState(self):
		self.pvrStateDialog.hide()

class InfoBarShowMovies:

	# i don't really like this class.
	# it calls a not further specified "movie list" on up/down/movieList,
	# so this is not more than an action map
	def __init__(self):
		self["MovieListActions"] = HelpableActionMap(self, "InfobarMovieListActions",
			{
				"movieList": (self.showMovies, _("view recordings...")),
				"up": (self.showMovies, _("view recordings...")),
				"down": (self.showMovies, _("view recordings..."))
			})

# InfoBarTimeshift requires InfoBarSeek, instantiated BEFORE!

# Hrmf.
#
# Timeshift works the following way:
#                                         demux0   demux1                    "TimeshiftActions" "TimeshiftActivateActions" "SeekActions"
# - normal playback                       TUNER    unused      PLAY               enable                disable              disable
# - user presses "yellow" button.         FILE     record      PAUSE              enable                disable              enable
# - user presess pause again              FILE     record      PLAY               enable                disable              enable
# - user fast forwards                    FILE     record      FF                 enable                disable              enable
# - end of timeshift buffer reached       TUNER    record      PLAY               enable                enable               disable
# - user backwards                        FILE     record      BACK  # !!         enable                disable              enable
#

# in other words:
# - when a service is playing, pressing the "timeshiftStart" button ("yellow") enables recording ("enables timeshift"),
# freezes the picture (to indicate timeshift), sets timeshiftMode ("activates timeshift")
# now, the service becomes seekable, so "SeekActions" are enabled, "TimeshiftEnableActions" are disabled.
# - the user can now PVR around
# - if it hits the end, the service goes into live mode ("deactivates timeshift", it's of course still "enabled")
# the service looses it's "seekable" state. It can still be paused, but just to activate timeshift right
# after!
# the seek actions will be disabled, but the timeshiftActivateActions will be enabled
# - if the user rewinds, or press pause, timeshift will be activated again

# note that a timeshift can be enabled ("recording") and
# activated (currently time-shifting).


class InfoBarTimeshift:
	def __init__(self):
		self["TimeshiftActions"] = HelpableActionMap(self, "InfobarTimeshiftActions",
			{
				"timeshiftStart": (self.startTimeshift, _("start timeshift")),  # the "yellow key"
				"timeshiftStop": (self.stopTimeshift, _("stop timeshift"))      # currently undefined :), probably 'TV'
			}, prio=1)
		self["TimeshiftActivateActions"] = ActionMap(["InfobarTimeshiftActivateActions"],
			{
				"timeshiftActivateEnd": self.activateTimeshiftEnd, # something like "rewind key"
				"timeshiftActivateEndAndPause": self.activateTimeshiftEndAndPause  # something like "pause key"
			}, prio=-1) # priority over record

		self.timeshift_enabled = 0
		self.timeshift_state = 0
		self.ts_rewind_timer = eTimer()
		self.ts_rewind_timer.callback.append(self.rewindService)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged
			})

	def getTimeshift(self):
		service = self.session.nav.getCurrentService()
		return service and service.timeshift()

	def startTimeshift(self):
		print "enable timeshift"
		ts = self.getTimeshift()
		if ts is None:
			self.session.open(MessageBox, _("Timeshift not possible!"), MessageBox.TYPE_ERROR)
			print "no ts interface"
			return 0

		if self.timeshift_enabled:
			print "hu, timeshift already enabled?"
		else:
			if not ts.startTimeshift():
				self.timeshift_enabled = 1

				# we remove the "relative time" for now.
				#self.pvrStateDialog["timeshift"].setRelative(time.time())

				# PAUSE.
				#self.setSeekState(self.SEEK_STATE_PAUSE)
				self.activateTimeshiftEnd(False)

				# enable the "TimeshiftEnableActions", which will override
				# the startTimeshift actions
				self.__seekableStatusChanged()
			else:
				print "timeshift failed"

	def stopTimeshift(self):
		if not self.timeshift_enabled:
			return 0
		print "disable timeshift"
		ts = self.getTimeshift()
		if ts is None:
			return 0
		self.session.openWithCallback(self.stopTimeshiftConfirmed, ChoiceBox, \
				title=_("Stop Timeshift ?"), \
				list=((_("Stop Timeshift (deleting TS file)"), "stop_ts"), \
				(_("Stop Timeshift (keeping TS file)"), "keep_ts"), \
				(_("Continue Timeshift"), "continue_ts")))

	def stopTimeshiftConfirmed(self, confirmed):
		if not confirmed:
			return

		ts = self.getTimeshift()
		if ts is None:
			return
		if confirmed[1] == "keep_ts":
			ts.stopTimeshift(True, False)
		elif confirmed[1] == "continue_ts":
			return
		else:
			ts.stopTimeshift(True, True)
		self.timeshift_enabled = 0

		# disable actions
		self.__seekableStatusChanged()

	# activates timeshift, and seeks to (almost) the end
	def activateTimeshiftEnd(self, back = True):
		ts = self.getTimeshift()
		print "activateTimeshiftEnd"

		if ts is None:
			return

		if ts.isTimeshiftActive():
			print "!! activate timeshift called - but shouldn't this be a normal pause?"
			self.pauseService()
		else:
			print "play, ..."
			ts.activateTimeshift() # activate timeshift will automatically pause
			self.setSeekState(self.SEEK_STATE_PAUSE)

		if back:
			self.ts_rewind_timer.start(200, 1)

	def rewindService(self):
		self.setSeekState(self.makeStateBackward(int(config.seek.enter_backward.value)))

	# same as activateTimeshiftEnd, but pauses afterwards.
	def activateTimeshiftEndAndPause(self):
		print "activateTimeshiftEndAndPause"
		#state = self.seekstate
		self.activateTimeshiftEnd(False)

	def __seekableStatusChanged(self):
		enabled = False

#		print "self.isSeekable", self.isSeekable()
#		print "self.timeshift_enabled", self.timeshift_enabled

		# when this service is not seekable, but timeshift
		# is enabled, this means we can activate
		# the timeshift
		if not self.isSeekable() and self.timeshift_enabled:
			enabled = True

#		print "timeshift activate:", enabled
		self["TimeshiftActivateActions"].setEnabled(enabled)

	def __serviceStarted(self):
		self.timeshift_enabled = False
		self.__seekableStatusChanged()

from Screens.PiPSetup import PiPSetup

class InfoBarExtensions:
	EXTENSION_SINGLE = 0
	EXTENSION_LIST = 1

	def __init__(self):
		self.list = []

		self["InstantExtensionsActions"] = HelpableActionMap(self, "InfobarExtensions",
			{
				"extensions": (self.showExtensionSelection, _("view extensions...")),
				"vtipanel": (self.openVTIPanel, _("open VTi Panel")),
				"vtiinfopanel": (self.openVTiInfoPanel, _("show VTi system informations")),
			}, 1) # lower priority
			
	def openVTIPanel(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/plugin.pyo"):
			try:
				from Plugins.SystemPlugins.VTIPanel.plugin import VTIMainMenu
				self.session.open(VTIMainMenu)
			except ImportError:
				self.session.open(MessageBox, _("The VTi Panel is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 10 )
		else:
			self.session.open(MessageBox, _("The VTi Panel is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 10 )

	def openVTiInfoPanel(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/InfoPanel.pyo"):
			try:
				from Plugins.SystemPlugins.VTIPanel.InfoPanel import InfoPanel
				self.session.open(InfoPanel, self)
			except ImportError:
				self.session.open(MessageBox, _("The VTi InfoPanel is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 10 )
		else:
			self.session.open(MessageBox, _("The VTI Info Panel is not installed!\nPlease install it."), type = MessageBox.TYPE_INFO,timeout = 10 )
		
	def addExtension(self, extension, key = None, type = EXTENSION_SINGLE):
		self.list.append((type, extension, key))

	def updateExtension(self, extension, key = None):
		self.extensionsList.append(extension)
		if key is not None:
			if self.extensionKeys.has_key(key):
				key = None

		if key is None:
			for x in self.availableKeys:
				if not self.extensionKeys.has_key(x):
					key = x
					break

		if key is not None:
			self.extensionKeys[key] = len(self.extensionsList) - 1

	def updateExtensions(self):
		self.extensionsList = []
		self.availableKeys = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "red", "green", "yellow", "blue" ]
		self.extensionKeys = {}
		for x in self.list:
			if x[0] == self.EXTENSION_SINGLE:
				self.updateExtension(x[1], x[2])
			else:
				for y in x[1]():
					self.updateExtension(y[0], y[1])


	def showExtensionSelection(self):
		self.updateExtensions()
		extensionsList = self.extensionsList[:]
		keys = []
		list = []
		for x in self.availableKeys:
			if self.extensionKeys.has_key(x):
				entry = self.extensionKeys[x]
				extension = self.extensionsList[entry]
				if extension[2]():
					name = str(extension[0]())
					list.append((extension[0](), extension))
					keys.append(x)
					extensionsList.remove(extension)
				else:
					extensionsList.remove(extension)
		list.extend([(x[0](), x) for x in extensionsList])

		keys += [""] * len(extensionsList)
		if config.usage.sort_plugins_byname.value:
			list.sort(key=self.sortByName)
		self.session.openWithCallback(self.extensionCallback, ChoiceBox, title=_("Please choose an extension..."), list = list, keys = keys, skin_name = "ExtensionsList")

	def extensionCallback(self, answer):
		if answer is not None:
			answer[1][1]()

	def sortByName(self, listentry):
		return listentry[0].lower()

from Tools.BoundFunction import boundFunction
import inspect

# depends on InfoBarExtensions

class InfoBarPlugins:
	def __init__(self):
		self.addExtension(extension = self.getPluginList, type = InfoBarExtensions.EXTENSION_LIST)

	def getPluginName(self, name):
		return name

	def getPluginList(self):
		l = []
		for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
		  args = inspect.getargspec(p.__call__)[0]
		  if len(args) == 1 or len(args) == 2 and isinstance(self, InfoBarChannelSelection):
			  l.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None, p.name))
		l.sort(key = lambda e: e[2]) # sort by name
		return l

	def runPlugin(self, plugin):
		if isinstance(self, InfoBarChannelSelection):
			plugin(session = self.session, servicelist = self.servicelist)
		else:
			plugin(session = self.session)

from Components.Task import job_manager
class InfoBarJobman:
	def __init__(self):
		self.addExtension(extension = self.getJobList, type = InfoBarExtensions.EXTENSION_LIST)

	def getJobList(self):
		return [((boundFunction(self.getJobName, job), boundFunction(self.showJobView, job), lambda: True), None) for job in job_manager.getPendingJobs()]

	def getJobName(self, job):
		return "%s: %s (%d%%)" % (job.getStatustext(), job.name, int(100*job.progress/float(job.end)))

	def showJobView(self, job):
		from Screens.TaskView import JobView
		job_manager.in_background = False
		self.session.openWithCallback(self.JobViewCB, JobView, job)
	
	def JobViewCB(self, in_background):
		job_manager.in_background = in_background

# depends on InfoBarExtensions
class InfoBarPiP:
	
	SERVICELIST_MAIN = 0
	SERVICELIST_PIP = 1
	
	def __init__(self):
		try:
			self.session.pipshown
		except:
			self.session.pipshown = False
		self.setPiP_globals()
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			if (self.allowPiP):
				self.addExtension((self.getShowHideName, self.showPiP, self.addPiPExt), "blue")
				self.addExtension((self.getMoveName, self.movePiP, self.canMove), "green")
				self.addExtension((self.getShowHideNameSplitScreen, self.showSplitScreen, self.splitScreenshown))
				self.addExtension((self.getShowHideNameAudioZap, self.showAudioZap, self.audioZapshown))
				self.addExtension((self.getNameTogglePiPZap, self.toggle_pip_zap, self.togglePiPZapshown))
				if (self.allowPiPSwap):
					self.addExtension((self.getSwapName, self.swapPiP, self.pipShown), "yellow")
				if config.usage.default_pip_mode.value == "splitscreen":
					hlp_txt = _("(de)activate Split Screen...")
					pip_fnc = self.showSplitScreen
				elif config.usage.default_pip_mode.value == "audiozap":
					hlp_txt = _("(de)activate Audio Zap...")
					pip_fnc = self.showAudioZap
				else:
					hlp_txt = _("(de)activate Picture in Picture...")
					pip_fnc = self.showPiP
				self["PiPActions"] = HelpableActionMap(self, "InfobarPiPActions",
				{
					"show_hide_pip": (pip_fnc, hlp_txt),
				})
			else:
				self.addExtension((self.getShowHideName, self.showPiP, self.pipShown), "blue")
				self.addExtension((self.getMoveName, self.movePiP, self.pipShown), "green")

	def setToggleHelpText(self):
		idx = 0
		actions = []
		if self.session.pipshown:
			hlp_txt = self.getNameTogglePiPZap()
		else:
			hlp_txt = _("Play recorded movies...")
		for x in self.helpList:
			if x[1] == "InfobarActions":
				for y in x[2]:
					if y[0] == "showMovies":
						actions.append(("showMovies", hlp_txt))
					else:
						actions.append(y)
				if len(actions):
					break
			idx += 1
		if len(actions) and idx < len(self.helpList):
			self.helpList[idx] = (x[0], x[1], actions)

	def togglePiPZapshown(self):
		if self.session.pipshown:
			return True
		return False

	def audioZapshown(self):
		if self.session.pipshown and not self.session.is_audiozap:
			return False
		return True

	def splitScreenshown(self):
		if self.session.pipshown:
			if  not self.session.is_splitscreen:
				return False
			if self.session.is_audiozap:
				return False
		return True
	
	def addPiPExt(self):
		if self.session.pipshown and self.session.is_splitscreen:
			return False
		return True

	def canMove(self):
		if self.session.is_splitscreen:
			return False
		return self.session.pipshown

	def pipShown(self):
		return self.session.pipshown

	def pipHandles0Action(self):
		return self.pipShown() and config.usage.pip_zero_button.value != "standard"

	def getNameTogglePiPZap(self):
		return _("Toggle zap focus (PiP, Split Screen, Audio Zap)")

	def getShowHideNameAudioZap(self):
		if self.session.is_splitscreen and self.session.is_audiozap:
			return _("Deactivate Audio Zap")
		return _("Activate Audio Zap")

	def getShowHideNameSplitScreen(self):
		if self.session.is_splitscreen:
			return _("Deactivate Split Screen")
		return _("Activate Split Screen")

	def getShowHideName(self):
		if self.session.pipshown:
			return _("Disable Picture in Picture")
		else:
			return _("Activate Picture in Picture")

	def getSwapName(self):
		return _("Swap Services")

	def getMoveName(self):
		return _("Move Picture in Picture")

	def showAudioZap(self):
		self.session.is_audiozap = True
		self.showSplitScreen()

	def showSplitScreen(self):
		self.session.is_splitscreen = True
		self.showPiP()
		if not self.session.pipshown:
			self.session.is_splitscreen = False

	def toggle_service_list(self):
		if self.slist_type == self.SERVICELIST_MAIN:
			self.slist_type = self.SERVICELIST_PIP
			if self.session.pip.servicePath:
				servicepath = self.session.pip.servicePath
			else:
				servicepath = self.servicelist.getCurrentServicePath()
			self.session.pip.main_servicePath = self.servicelist.getCurrentServicePath()
		else:
			self.slist_type = self.SERVICELIST_MAIN
			if self.session.pip.main_servicePath:
				servicepath = self.session.pip.main_servicePath
			else:
				servicepath = self.servicelist.getCurrentServicePath()
			self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
		zap = False
		self.servicelist.setCurrentServicePath(servicepath, zap)

	def toggle_pip_zap(self):
		if self.session.pipshown:
			if self.session.pip_zap_main:
				self.session.pip_zap_main = False
			else:
				self.session.pip_zap_main = True
			self.show_zap_focus_text()
			self.toggle_service_list()

	def del_hide_timer(self):
		del self.__pip_hide_timer

	def pip_hide_timer_start(self):
		self.__pip_hide_timer = eTimer()
		self.__pip_hide_timer.callback.append(self.session.pip.hideInfo)
		self.__pip_hide_timer.start(3000, True)

	def show_zap_focus_text(self):
		text = _("Zap focus: ")
		if self.session.pip_in_movieplayer:
			text += _("Live TV")
		elif self.session.is_audiozap:
			if self.session.pip_zap_main:
				text += _("Audio")
			else:
				text += _("Video")
		elif self.session.is_splitscreen:
			if self.session.pip_zap_main:
				text += _("Main window")
			else:
				text += _("Second window")
		else:
			if self.session.pip_zap_main:
				text += _("Main window")
			else:
				text += _("Mini TV")
		self.session.zap_focus_text = text
		self.session.pip.set_zap_focus_text()
		self.pip_hide_timer_start()

	def setPiP_globals(self):
		self.session.pipshown = False
		self.session.is_audiozap = False
		self.session.is_splitscreen = False
		self.session.is_pig = False
		self.session.pip_zap_main = True
		self.session.pip_in_movieplayer = False
		self.slist_type = self.SERVICELIST_MAIN

	def showPiG(self):
		self.session.is_pig = True
		self.showPiP()

	def showPiP(self):
		if self.session.pipshown:
			if self.slist_type == self.SERVICELIST_PIP:
				self.toggle_service_list()
			pip_path = self.session.pip.servicePath
			pip_ref = pip_path[len(pip_path) - 1]
			cur_ref = self.session.nav.getCurrentlyPlayingServiceReference()
			servicepath = self.servicelist.getCurrentServicePath()
			if not cur_ref and pip_ref:
				cur_ref = pip_ref
				self.session.nav.playService(cur_ref)
			if cur_ref and pip_ref and cur_ref == pip_ref:
				servicepath = pip_path
			self.del_hide_timer()
			del self.session.pip
			self.setPiP_globals()
			self.setToggleHelpText()
			if servicepath:
				zap = False
				self.servicelist.setCurrentServicePath(servicepath, zap)
			self.exit_locked = True
			self.unlockTimer.start(500, True)
		else:
			if self.session.is_splitscreen:
				self.session.pip = self.session.instantiateDialog(SplitScreen)
			elif self.session.is_pig:
				self.session.pip = self.session.instantiateDialog(PiGDummy)
			else:
				self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.setAnimationMode(0)
			self.session.pip.show()
			newservice = self.session.nav.getCurrentlyPlayingServiceReference()
			if self.session.pip.playService(newservice):
				self.session.pipshown = True
				self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
				if config.usage.zap_pip.value and not self.session.is_splitscreen and not self.session.is_audiozap:
					self.toggle_pip_zap()
				self.setToggleHelpText()
				self.show_zap_focus_text()
			else:
				self.setPiP_globals()
				del self.session.pip
			self.session.nav.playService(newservice)

	def swapPiP(self):
		swapservice = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.session.pip.servicePath:
			pipref=self.session.pip.getCurrentService()
			self.session.pip.playService(swapservice)
			self.session.nav.playService(pipref)
			self.toggle_service_list()

	def movePiP(self):
		if self.session.pipshown and not self.session.is_splitscreen:
			self.session.open(PiPSetup, pip = self.session.pip)

	def execute_zero_doubleclick_action(self):
		use = 	config.usage.default_zero_double_click_mode.value
		if use == "pip":
			self.showPiP()
		elif use == "splitscreen":
			self.showSplitScreen()
		elif use == "audiozap":
			self.showAudioZap()

	def execute_0_pip_action(self, is_double = False):
		if is_double:
			use = config.usage.pip_zero_button_doubleclick.value
		else:
			use = config.usage.pip_zero_button.value
		if "swap" == use:
			self.swapPiP()
		elif "swapstop" == use:
			self.swapPiP()
			self.showPiP()
		elif "stop" == use:
			self.showPiP()
		elif "zap_focus" == use:
			self.toggle_pip_zap()

	def pipDoHandle0Action(self, is_double = False):
		self.execute_0_pip_action(is_double)

from RecordTimer import parseEvent, RecordTimerEntry
from Screens.TimerEntry import TimerEntry
from Screens.TimerEdit import TimerEditList

class InfoBarInstantRecord:
	"""Instant Record - handles the instantRecord action in order to
	start/stop instant records"""
	def __init__(self):
		rec_button_help_string = {
				"record_menu": _("show record menu"),
				"running_record": _("show running records"),
				"timer_list": _("show timer list"),
				"event_record": _("add recording (stop after current event)"),
				"indefinitely_record": _("add recording (indefinitely)"),
				"manualduration_record": _("add recording (enter recording duration)"),
				"manualendtime_record": _("add recording (enter recording endtime)")
			}
		self["InstantRecordActions"] = HelpableActionMap(self, "InfobarInstantRecord",
			{
				"instantRecord": (self.recButton, rec_button_help_string[config.usage.rec_button.value]),
				"showRunningRecords": (self.recButtonLong, rec_button_help_string[config.usage.rec_button_long.value]),
				"stopRunningRecords": (self.stopRunningRecords, _("Stop current records...")),
			})
		self.recording = []
		self.filename = None
	
	def recButton(self, long_press = False):
		rec_button = config.usage.rec_button.value
		if long_press:
			rec_button = config.usage.rec_button_long.value
		if rec_button == "record_menu":
			self.instantRecord()
		elif rec_button == "running_record":
			self.showRunningRecords()
		elif rec_button == "timer_list":
			self.session.open(TimerEditList)
		if self.__class__.__name__ == "InfoBar":
			if rec_button == "indefinitely_record":
				self.startInstantRecording(limitEvent = False)
			elif rec_button == "event_record":
				self.startInstantRecording(limitEvent = True)
			elif rec_button == "manualduration_record":
				self.startInstantRecording(limitEvent = False)
				self.changeDuration(len(self.recording)-1)
			elif rec_button == "manualendtime_record":
				self.startInstantRecording(limitEvent = True)
				self.setEndtime(len(self.recording)-1)

	def recButtonLong(self):
		self.recButton(True)

	def stopRunningRecords(self):
		# PTS hack !
		try:
			is_PTS_active = config.plugins.pts.enabled.value
		except KeyError:
			is_PTS_active = False
		
		if self.timeshift_enabled:
			if is_PTS_active and not self.isSeekable():
				pass
			else:
				return 0
		if self.isInstantRecordRunning() and len(self.recording) > 0:
			list = self.getRecordList()
			self.session.openWithCallback(self.stopCurrentRecording, TimerSelection, list)

	def showRunningRecords(self):
		show_only_running = True
		self.session.open(TimerEditList, show_only_running)
	
	def modifyTimer(self, entry = -1):
		if entry is not None and entry != -1:
			timer = self.recording[entry]
			self.session.open(TimerEntry, timer)

	def stopCurrentRecording(self, entry = -1):
		if entry is not None and entry != -1:
			timer = self.recording[entry]
			if timer.repeated:
				timer.enable()
				timer.processRepeated(findRunningEvent = False)
				self.session.nav.RecordTimer.doActivate(timer)
			else:
				self.session.nav.RecordTimer.removeEntry(self.recording[entry])
			self.recording.remove(self.recording[entry])
			if config.usage.ask_timer_file_del.value and timer:
				self.filename = os_path.realpath(timer.Filename)
				if self.filename:
					self.session.openWithCallback(self.delTimerFiles, MessageBox, _("Do you want to delete recording files of stopped timer ?"), MessageBox.TYPE_YESNO, default = False)

	def delTimerFiles(self, result):
		if result:
			service_to_delete = eServiceReference(1, 0, self.filename + ".ts")
			self.filename = None
			serviceHandler = eServiceCenter.getInstance()
			offline = serviceHandler.offlineOperations(service_to_delete)
			if offline is not None:
				offline.deleteFromDisk(0)

	def startInstantRecording(self, limitEvent = False):
		serviceref = self.session.nav.getCurrentlyPlayingServiceReference()

		# try to get event info
		event = None
		try:
			service = self.session.nav.getCurrentService()
			epg = eEPGCache.getInstance()
			event = epg.lookupEventTime(serviceref, -1, 0)
			if event is None:
				info = service.info()
				ev = info.getEvent(0)
				event = ev
		except:
			pass

		begin = int(time())
		end = begin + 3600	# dummy
		name = "instant record"
		description = ""
		eventid = None

		if event is not None:
			curEvent = parseEvent(event)
			name = curEvent[2]
			description = curEvent[3]
			eventid = curEvent[4]
			if limitEvent:
				end = curEvent[1]
		else:
			if limitEvent:
				self.session.open(MessageBox, _("No event info found, recording indefinitely."), MessageBox.TYPE_INFO)

		if isinstance(serviceref, eServiceReference):
			serviceref = ServiceReference(serviceref)

		recording = RecordTimerEntry(serviceref, begin, end, name, description, eventid, dirname = preferredInstantRecordPath())
		recording.dontSave = True

		if event is None or limitEvent == False:
			recording.autoincrease = True
			recording.setAutoincreaseEnd()

		simulTimerList = self.session.nav.RecordTimer.record(recording)

		if simulTimerList is None:	# no conflict
			self.recording.append(recording)
		else:
			if len(simulTimerList) > 1: # with other recording
				name = simulTimerList[1].name
				name_date = ' '.join((name, strftime('%c', localtime(simulTimerList[1].begin))))
				print "[TIMER] conflicts with", name_date
				recording.autoincrease = True	# start with max available length, then increment
				if recording.setAutoincreaseEnd():
					self.session.nav.RecordTimer.record(recording)
					self.recording.append(recording)
					self.session.open(MessageBox, _("Record time limited due to conflicting timer %s") % name_date, MessageBox.TYPE_INFO)
				else:
					self.session.open(MessageBox, _("Couldn't record due to conflicting timer %s") % name, MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox, _("Couldn't record due to invalid service %s") % serviceref, MessageBox.TYPE_INFO)
			recording.autoincrease = False

	def isInstantRecordRunning(self):
		recordings = self.session.nav.getRecordings()
		if recordings:
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.state == 2:
					if not timer.justplay:
						if not timer in self.recording:
							self.recording.append(timer)
		print "self.recording:", self.recording
		if self.recording:
			for x in self.recording:
				if x.isRunning():
					return True
		return False

	def getRecordList(self):
		list = []
		recording = self.recording[:]
		for x in recording:
			if not x in self.session.nav.RecordTimer.timer_list:
				self.recording.remove(x)
			elif x.isRunning():
				list.append((x, False))
		return list

	def recordQuestionCallback(self, answer):

		if answer is None or answer[1] == "no":
			return
		list = self.getRecordList()
		
		if answer[1] == "changeduration":
			if len(self.recording) == 1:
				self.changeDuration(0)
			else:
				self.session.openWithCallback(self.changeDuration, TimerSelection, list)
		elif answer[1] == "changeendtime":
			if len(self.recording) == 1:
				self.setEndtime(0)
			else:
				self.session.openWithCallback(self.setEndtime, TimerSelection, list)
		elif answer[1] == "stop":
			if len(self.recording) == 1:
				self.stopCurrentRecording(0)
			else:
				self.session.openWithCallback(self.stopCurrentRecording, TimerSelection, list)
		elif answer[1] in ( "indefinitely" , "manualduration", "manualendtime", "event"):
			self.startInstantRecording(limitEvent = answer[1] in ("event", "manualendtime") or False)
			if answer[1] == "manualduration":
				self.changeDuration(len(self.recording)-1)
			elif answer[1] == "manualendtime":
				self.setEndtime(len(self.recording)-1)
		elif answer[1] == "modify_timer":
			if len(self.recording) == 1:
				self.modifyTimer(0)
			else:
				self.session.openWithCallback(self.modifyTimer, TimerSelection, list)
		elif answer[1] == "show_timer_list":
			self.session.open(TimerEditList)

		print "after:\n", self.recording

	def setEndtime(self, entry):
		if entry is not None and entry >= 0:
			self.selectedEntry = entry
			self.endtime=ConfigClock(default = self.recording[self.selectedEntry].end)
			dlg = self.session.openWithCallback(self.TimeDateInputClosed, TimeDateInput, self.endtime)
			dlg.setTitle(_("Please change recording endtime"))

	def TimeDateInputClosed(self, ret):
		if len(ret) > 1:
			if ret[0]:
				localendtime = localtime(ret[1])
				print "stopping recording at", strftime("%c", localendtime)
				if self.recording[self.selectedEntry].end != ret[1]:
					self.recording[self.selectedEntry].autoincrease = False
				self.recording[self.selectedEntry].end = ret[1]
				self.session.nav.RecordTimer.timeChanged(self.recording[self.selectedEntry])

	def changeDuration(self, entry):
		if entry is not None and entry >= 0:
			self.selectedEntry = entry
			self.session.openWithCallback(self.inputCallback, InputBox, title=_("How many minutes do you want to record?"), text="5", maxSize=False, type=Input.NUMBER)

	def inputCallback(self, value):
		if value is not None:
			print "stopping recording after", int(value), "minutes."
			entry = self.recording[self.selectedEntry]
			if int(value) != 0:
				entry.autoincrease = False
			entry.end = int(time()) + 60 * int(value)
			self.session.nav.RecordTimer.timeChanged(entry)

	def instantRecord(self):
		dir = preferredInstantRecordPath()
		if not dir or not fileExists(dir, 'w'):
			dir = defaultMoviePath()

		if not fileExists("/hdd", 0):
			from os import system
			print "not found /hdd"
			system("ln -s /media/hdd /hdd")
#
		try:
			stat = os_stat(dir)
		except:
			# XXX: this message is a little odd as we might be recording to a remote device
			self.session.open(MessageBox, _("No HDD found or HDD not initialized!"), MessageBox.TYPE_ERROR)
			return

		if self.__class__.__name__ == "InfoBar":
			if self.isInstantRecordRunning():
				self.session.openWithCallback(self.recordQuestionCallback, ChoiceBox, \
					title = _("Recording Menu"), \
					list=((_("show timer list"), "show_timer_list"), \
					(_("add recording (stop after current event)"), "event"), \
					(_("add recording (indefinitely)"), "indefinitely"), \
					(_("add recording (enter recording duration)"), "manualduration"), \
					(_("add recording (enter recording endtime)"), "manualendtime"), \
					(_("stop recording"), "stop"), \
					(_("change recording (timer editor)"), "modify_timer"), \
					(_("change recording (duration)"), "changeduration"), \
					(_("change recording (endtime)"), "changeendtime"), \
					(_("back"), "no")))
			else:
				self.session.openWithCallback(self.recordQuestionCallback, ChoiceBox, \
					title = _("Recording Menu"), \
					list=((_("show timer list"), "show_timer_list"), \
					(_("add recording (stop after current event)"), "event"), \
					(_("add recording (indefinitely)"), "indefinitely"), \
					(_("add recording (enter recording duration)"), "manualduration"), \
					(_("add recording (enter recording endtime)"), "manualendtime"), \
					(_("back"), "no")))
		else:
			if self.isInstantRecordRunning():
				self.session.openWithCallback(self.recordQuestionCallback, ChoiceBox, \
					title = _("Recording Menu"), \
					list=((_("show timer list"), "show_timer_list"), \
					(_("stop recording"), "stop"), \
					(_("change recording (timer editor)"), "modify_timer"), \
					(_("change recording (duration)"), "changeduration"), \
					(_("change recording (endtime)"), "changeendtime"), \
					(_("back"), "no")))
			else:
				self.session.openWithCallback(self.recordQuestionCallback, ChoiceBox, \
					title = _("Recording Menu"), \
					list=((_("show timer list"), "show_timer_list"), \
					(_("back"), "no")))

from Tools.ISO639 import LanguageCodes

class InfoBarAudioSelection:
	def __init__(self):
		self["AudioSelectionAction"] = HelpableActionMap(self, "InfobarAudioSelectionActions",
			{
				"audioSelection": (self.audioSelection, _("Audio Options...")),
			})

	def audioSelection(self):
		from Screens.AudioSelection import AudioSelection
		self.session.openWithCallback(self.audioSelected, AudioSelection, infobar=self)
		
	def audioSelected(self, ret=None):
		print "[infobar::audioSelected]", ret

class InfoBarSubserviceSelection:
	def __init__(self):
		self["SubserviceSelectionAction"] = HelpableActionMap(self, "InfobarSubserviceSelectionActions",
			{
				"subserviceSelection": (self.subserviceSelection, _("Subservice list...")),
			})

		self["SubserviceQuickzapAction"] = HelpableActionMap(self, "InfobarSubserviceQuickzapActions",
			{
				"nextSubservice": (self.nextSubservice, _("Switch to next subservice")),
				"prevSubservice": (self.prevSubservice, _("Switch to previous subservice"))
			}, -1)
		self["SubserviceQuickzapAction"].setEnabled(False)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUpdatedEventInfo: self.checkSubservicesAvail
			})

		self.bsel = None

	def checkSubservicesAvail(self):
		service = self.session.nav.getCurrentService()
		subservices = service and service.subServices()
		if not subservices or subservices.getNumberOfSubservices() == 0:
			self["SubserviceQuickzapAction"].setEnabled(False)

	def nextSubservice(self):
		self.changeSubservice(+1)

	def prevSubservice(self):
		self.changeSubservice(-1)

	def changeSubservice(self, direction):
		service = self.session.nav.getCurrentService()
		subservices = service and service.subServices()
		n = subservices and subservices.getNumberOfSubservices()
		if n and n > 0:
			selection = -1
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			idx = 0
			while idx < n:
				if subservices.getSubservice(idx).toString() == ref.toString():
					selection = idx
					break
				idx += 1
			if selection != -1:
				selection += direction
				if selection >= n:
					selection=0
				elif selection < 0:
					selection=n-1
				newservice = subservices.getSubservice(selection)
				if newservice.valid():
					del subservices
					del service
					self.session.nav.playService(newservice, False)

	def subserviceSelection(self):
		service = self.session.nav.getCurrentService()
		subservices = service and service.subServices()
		self.bouquets = self.servicelist.getBouquetList()
		n = subservices and subservices.getNumberOfSubservices()
		selection = 0
		if n and n > 0:
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			tlist = []
			idx = 0
			while idx < n:
				i = subservices.getSubservice(idx)
				if i.toString() == ref.toString():
					selection = idx
				tlist.append((i.getName(), i))
				idx += 1

			if self.bouquets and len(self.bouquets):
				keys = ["red", "blue", "",  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ] + [""] * n
				if config.usage.multibouquet.value:
					tlist = [(_("Quickzap"), "quickzap", service.subServices()), (_("Add to bouquet"), "CALLFUNC", self.addSubserviceToBouquetCallback), ("--", "")] + tlist
				else:
					tlist = [(_("Quickzap"), "quickzap", service.subServices()), (_("Add to favourites"), "CALLFUNC", self.addSubserviceToBouquetCallback), ("--", "")] + tlist
				selection += 3
			else:
				tlist = [(_("Quickzap"), "quickzap", service.subServices()), ("--", "")] + tlist
				keys = ["red", "",  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ] + [""] * n
				selection += 2

			self.session.openWithCallback(self.subserviceSelected, ChoiceBox, title=_("Please select a subservice..."), list = tlist, selection = selection, keys = keys, skin_name = "SubserviceSelection")

	def subserviceSelected(self, service):
		del self.bouquets
		if not service is None:
			if isinstance(service[1], str):
				if service[1] == "quickzap":
					from Screens.SubservicesQuickzap import SubservicesQuickzap
					self.session.open(SubservicesQuickzap, service[2])
			else:
				self["SubserviceQuickzapAction"].setEnabled(True)
				self.session.nav.playService(service[1], False)

	def addSubserviceToBouquetCallback(self, service):
		if len(service) > 1 and isinstance(service[1], eServiceReference):
			self.selectedSubservice = service
			if self.bouquets is None:
				cnt = 0
			else:
				cnt = len(self.bouquets)
			if cnt > 1: # show bouquet list
				self.bsel = self.session.openWithCallback(self.bouquetSelClosed, BouquetSelector, self.bouquets, self.addSubserviceToBouquet)
			elif cnt == 1: # add to only one existing bouquet
				self.addSubserviceToBouquet(self.bouquets[0][1])
				self.session.open(MessageBox, _("Service has been added to the favourites."), MessageBox.TYPE_INFO)

	def bouquetSelClosed(self, confirmed):
		self.bsel = None
		del self.selectedSubservice
		if confirmed:
			self.session.open(MessageBox, _("Service has been added to the selected bouquet."), MessageBox.TYPE_INFO)

	def addSubserviceToBouquet(self, dest):
		self.servicelist.addServiceToBouquet(dest, self.selectedSubservice[1])
		if self.bsel:
			self.bsel.close(True)
		else:
			del self.selectedSubservice

from Components.Sources.HbbtvApplication import HbbtvApplication
gHbbtvApplication = HbbtvApplication()
class InfoBarRedButton:
	def __init__(self):
		if SystemInfo["HasHbbTV"]:
			self["RedButtonActions"] = HelpableActionMap(self, "InfobarRedButtonActions",
				{
					"activateRedButton": (self.activateRedButton, _("Red button...")),
				})
			self["HbbtvApplication"] = gHbbtvApplication
		else:
			self["HbbtvApplication"] = Boolean(fixed=0)
			self["HbbtvApplication"].name = "" #is this a hack?
			
		self.onHBBTVActivation = [ ]
		self.onRedButtonActivation = [ ]
		self.onReadyForAIT = [ ]
		self.__et = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evHBBTVInfo: self.detectedHbbtvApplication,
				iPlayableService.evUpdatedInfo: self.updateInfomation
			})

	def updateAIT(self, orgId=0):
		for x in self.onReadyForAIT:
			try:
				x(orgId)
			except Exception, ErrMsg: 
				print ErrMsg
				#self.onReadyForAIT.remove(x)

	def updateInfomation(self):
		try:
			self["HbbtvApplication"].setApplicationName("")
			self.updateAIT()
		except Exception, ErrMsg:
			pass
		
	def detectedHbbtvApplication(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		try:
			for x in info.getInfoObject(iServiceInformation.sHBBTVUrl):
				print x
				if x[0] in (-1, 1):
					self.updateAIT(x[3])
					self["HbbtvApplication"].setApplicationName(x[1])
					break
		except Exception, ErrMsg:
			pass

	def activateRedButton(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		if info and info.getInfoString(iServiceInformation.sHBBTVUrl) != "":
			for x in self.onHBBTVActivation:
				x()
		elif False: # TODO: other red button services
			for x in self.onRedButtonActivation:
				x()

class InfoBarAdditionalInfo:
	def __init__(self):

		self["RecordingPossible"] = Boolean(fixed=harddiskmanager.HDDCount() > 0)
		self["TimeshiftPossible"] = self["RecordingPossible"]
		self["ShowTimeshiftOnYellow"] = Boolean(fixed=0)
		self["ShowAudioOnYellow"] = Boolean(fixed=1)
		self["ShowRecordOnRed"] = Boolean(fixed=0)
		self["ExtensionsAvailable"] = Boolean(fixed=1)

class InfoBarNotifications:
	def __init__(self):
		self.onExecBegin.append(self.checkNotifications)
		Notifications.notificationAdded.append(self.checkNotificationsIfExecing)
		self.onClose.append(self.__removeNotification)

	def __removeNotification(self):
		Notifications.notificationAdded.remove(self.checkNotificationsIfExecing)

	def checkNotificationsIfExecing(self):
		if self.execing:
			self.checkNotifications()

	def checkNotifications(self):
		notifications = Notifications.notifications
		if notifications:
			n = notifications[0]

			del notifications[0]
			cb = n[0]

			if n[3].has_key("onSessionOpenCallback"):
				n[3]["onSessionOpenCallback"]()
				del n[3]["onSessionOpenCallback"]

			if cb is not None:
				dlg = self.session.openWithCallback(cb, n[1], *n[2], **n[3])
			else:
				dlg = self.session.open(n[1], *n[2], **n[3])

			# remember that this notification is currently active
			d = (n[4], dlg)
			Notifications.current_notifications.append(d)
			dlg.onClose.append(boundFunction(self.__notificationClosed, d))

	def __notificationClosed(self, d):
		Notifications.current_notifications.remove(d)

class InfoBarServiceNotifications:
	def __init__(self):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEnd: self.serviceHasEnded
			})

	def serviceHasEnded(self):
		print "service end!"

		try:
			self.setSeekState(self.SEEK_STATE_PLAY)
		except:
			pass

class InfoBarCueSheetSupport:
	CUT_TYPE_IN = 0
	CUT_TYPE_OUT = 1
	CUT_TYPE_MARK = 2
	CUT_TYPE_LAST = 3
	CUT_TYPE_LENGTH = 5

	ENABLE_RESUME_SUPPORT = False

	def __init__(self, actionmap = "InfobarCueSheetActions"):
		self["CueSheetActions"] = HelpableActionMap(self, actionmap,
			{
				"jumpPreviousMark": (self.jumpPreviousMark, _("jump to previous marked position")),
				"jumpNextMark": (self.jumpNextMark, _("jump to next marked position")),
				"toggleMark": (self.toggleMark, _("toggle a cut mark at the current position"))
			}, prio=1)

		self.cut_list = [ ]
		self.is_closing = False
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evStart: self.__serviceStarted,
			})

	def __serviceStarted(self):
		if self.is_closing:
			return
		print "new service started! trying to download cuts!"
		self.downloadCuesheet()

		if self.ENABLE_RESUME_SUPPORT:
			last = None
			cue_length = None
			resume = True
			length = None

			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_LAST:
					last = pts
				elif what == self.CUT_TYPE_LENGTH:
					cue_length = pts

			if last is not None:
				self.resume_point = last
				
				l = last / 90000
				
				if not config.usage.movielist_resume_at_eof.value:
					if cue_length:
						length = cue_length / 90000
					seek = self.getSeek()
					if seek:
						length_list = seek.getLength()
						if not length_list[0] and length_list[1] > 1:
							length = length_list[1] / 90000
					if length and length > 0:
						seen = (l * 100) / length
						if config.usage.movielist_progress_seen.value <= seen:
							resume = False
				if resume and config.usage.on_movie_start.value == "ask":
					Notifications.AddNotificationWithCallback(self.playLastCB, MessageBox, _("Do you want to resume this playback?") + "\n" + (_("Resume position at %s") % ("%d:%02d:%02d" % (l/3600, l%3600/60, l%60))), timeout=10)
				elif resume and config.usage.on_movie_start.value == "resume":
# TRANSLATORS: The string "Resuming playback" flashes for a moment
# TRANSLATORS: at the start of a movie, when the user has selected
# TRANSLATORS: "Resume from last position" as start behavior.
# TRANSLATORS: The purpose is to notify the user that the movie starts
# TRANSLATORS: in the middle somewhere and not from the beginning.
# TRANSLATORS: (Some translators seem to have interpreted it as a
# TRANSLATORS: question or a choice, but it is a statement.)
					Notifications.AddNotificationWithCallback(self.playLastCB, MessageBox, _("Resuming playback"), timeout=2, type=MessageBox.TYPE_INFO)

	def playLastCB(self, answer):
		if answer == True:
			self.doSeek(self.resume_point)
		self.hideAfterResume()

	def hideAfterResume(self):
		if isinstance(self, InfoBarShowHide):
			self.hide()

	def __getSeekable(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		return service.seek()

	def cueGetCurrentPosition(self):
		seek = self.__getSeekable()
		if seek is None:
			return None
		r = seek.getPlayPosition()
		if r[0]:
			return None
		return long(r[1])

	def cueGetEndCutPosition(self):
		ret = False
		isin = True
		for cp in self.cut_list:
			if cp[1] == self.CUT_TYPE_OUT:
				if isin:
					isin = False
					ret = cp[0]
			elif cp[1] == self.CUT_TYPE_IN:
				isin = True
		return ret
		
	def jumpPreviousNextMark(self, cmp, start=False):
		current_pos = self.cueGetCurrentPosition()
		if current_pos is None:
 			return False
		mark = self.getNearestCutPoint(current_pos, cmp=cmp, start=start)
		if mark is not None:
			pts = mark[0]
		else:
			return False

		self.doSeek(pts)
		return True

	def jumpPreviousMark(self):
		# we add 5 seconds, so if the play position is <5s after
		# the mark, the mark before will be used
		self.jumpPreviousNextMark(lambda x: -x-5*90000, start=True)

	def jumpNextMark(self):
		if not self.jumpPreviousNextMark(lambda x: x-90000):
			self.doSeek(-1)

	def getNearestCutPoint(self, pts, cmp=abs, start=False):
		# can be optimized
		beforecut = True
		nearest = None
		bestdiff = -1
		instate = True
		if start:
			bestdiff = cmp(0 - pts)
			if bestdiff >= 0:
				nearest = [0, False]
		for cp in self.cut_list:
			if beforecut and cp[1] in (self.CUT_TYPE_IN, self.CUT_TYPE_OUT):
				beforecut = False
				if cp[1] == self.CUT_TYPE_IN:  # Start is here, disregard previous marks
					diff = cmp(cp[0] - pts)
					if start and diff >= 0:
						nearest = cp
						bestdiff = diff
					else:
						nearest = None
						bestdiff = -1
			if cp[1] == self.CUT_TYPE_IN:
				instate = True
			elif cp[1] == self.CUT_TYPE_OUT:
				instate = False
			elif cp[1] in (self.CUT_TYPE_MARK, self.CUT_TYPE_LAST):
				diff = cmp(cp[0] - pts)
				if instate and diff >= 0 and (nearest is None or bestdiff > diff):
					nearest = cp
					bestdiff = diff
		return nearest

	def toggleMark(self, onlyremove=False, onlyadd=False, tolerance=5*90000, onlyreturn=False):
		current_pos = self.cueGetCurrentPosition()
		if current_pos is None:
			print "not seekable"
			return

		nearest_cutpoint = self.getNearestCutPoint(current_pos)

		if nearest_cutpoint is not None and abs(nearest_cutpoint[0] - current_pos) < tolerance:
			if onlyreturn:
				return nearest_cutpoint
			if not onlyadd:
				self.removeMark(nearest_cutpoint)
		elif not onlyremove and not onlyreturn:
			self.addMark((current_pos, self.CUT_TYPE_MARK))

		if onlyreturn:
			return None

	def addMark(self, point):
		insort(self.cut_list, point)
		self.uploadCuesheet()
		self.showAfterCuesheetOperation()

	def removeMark(self, point):
		self.cut_list.remove(point)
		self.uploadCuesheet()
		self.showAfterCuesheetOperation()

	def showAfterCuesheetOperation(self):
		if isinstance(self, InfoBarShowHide):
			self.doShow()

	def __getCuesheet(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		return service.cueSheet()

	def uploadCuesheet(self):
		cue = self.__getCuesheet()

		if cue is None:
			print "upload failed, no cuesheet interface"
			return
		cue.setCutList(self.cut_list)

	def downloadCuesheet(self):
		cue = self.__getCuesheet()

		if cue is None:
			print "download failed, no cuesheet interface"
			self.cut_list = [ ]
		else:
			self.cut_list = cue.getCutList()

class InfoBarSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="global.CurrentTime" render="Label" position="62,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
		<widget source="session.RecordState" render="FixedLabel" text=" " position="62,46" size="82,18" zPosition="1" >
			<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="6,4" size="120,42" font="Regular;18" >
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.Event_Now" render="Progress" position="6,46" size="46,18" borderWidth="1" >
			<convert type="EventTime">Progress</convert>
		</widget>
	</screen>"""

# for picon:  (path="piconlcd" will use LCD picons)
#		<widget source="session.CurrentService" render="Picon" position="6,0" size="120,64" path="piconlcd" >
#			<convert type="ServiceName">Reference</convert>
#		</widget>

class InfoBarSummarySupport:
	def __init__(self):
		pass

	def createSummary(self):
		return InfoBarSummary

class InfoBarMoviePlayerSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="global.CurrentTime" render="Label" position="62,46" size="64,18" font="Regular;16" halign="right" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
		<widget source="session.RecordState" render="FixedLabel" text=" " position="62,46" size="64,18" zPosition="1" >
			<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="6,4" size="120,42" font="Regular;18" >
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.CurrentService" render="Progress" position="6,46" size="56,18" borderWidth="1" >
			<convert type="ServicePosition">Position</convert>
		</widget>
	</screen>"""

class InfoBarMoviePlayerSummarySupport:
	def __init__(self):
		pass

	def createSummary(self):
		return InfoBarMoviePlayerSummary

class InfoBarTeletextPlugin:
	def __init__(self):
		self.teletext_plugin = None

		for p in plugins.getPlugins(PluginDescriptor.WHERE_TELETEXT):
			self.teletext_plugin = p

		if self.teletext_plugin is not None:
			self["TeletextActions"] = HelpableActionMap(self, "InfobarTeletextActions",
				{
					"startTeletext": (self.startTeletext, _("View teletext..."))
				})
		else:
			print "no teletext plugin found!"

	def startTeletext(self):
		self.teletext_plugin(session=self.session, service=self.session.nav.getCurrentService())

class InfoBarSubtitleSupport(object):
	def __init__(self):
		object.__init__(self)
		self.subtitle_window = self.session.instantiateDialog(SubtitleDisplay)
		self.subtitle_window.setAnimationMode(0)
		self.__subtitles_enabled = False

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEnd: self.__serviceStopped,
				iPlayableService.evUpdatedInfo: self.__updatedInfo
			})
		self.cached_subtitle_checked = False
		self.__selected_subtitle = None

	def __serviceStopped(self):
		self.cached_subtitle_checked = False
		if self.__subtitles_enabled:
			self.subtitle_window.hide()
			self.__subtitles_enabled = False
			self.__selected_subtitle = None

	def __updatedInfo(self):
		if not self.cached_subtitle_checked:
			self.cached_subtitle_checked = True
			subtitle = self.getCurrentServiceSubtitle()
			self.setSelectedSubtitle(subtitle and subtitle.getCachedSubtitle())
			if self.__selected_subtitle:
				self.setSubtitlesEnable(True)

	def getCurrentServiceSubtitle(self):
		service = self.session.nav.getCurrentService()
		return service and service.subtitle()

	def setSubtitlesEnable(self, enable=True):
		subtitle = self.getCurrentServiceSubtitle()
		if enable:
			if self.__selected_subtitle:
				if subtitle and not self.__subtitles_enabled:
					subtitle.enableSubtitles(self.subtitle_window.instance, self.selected_subtitle)
					self.subtitle_window.show()
					self.__subtitles_enabled = True
		else:
			if subtitle:
				subtitle.disableSubtitles(self.subtitle_window.instance)
			self.__selected_subtitle = False
			self.__subtitles_enabled = False
			self.subtitle_window.hide()

	def setSelectedSubtitle(self, subtitle):
		self.__selected_subtitle = subtitle

	subtitles_enabled = property(lambda self: self.__subtitles_enabled, setSubtitlesEnable)
	selected_subtitle = property(lambda self: self.__selected_subtitle, setSelectedSubtitle)

class InfoBarServiceErrorPopupSupport:
	def __init__(self):
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evTuneFailed: self.__tuneFailed,
				iPlayableService.evStart: self.__serviceStarted
			})
		self.__serviceStarted()

	def __serviceStarted(self):
		self.last_error = None
		Notifications.RemovePopup(id = "ZapError")

	def __tuneFailed(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		error = info and info.getInfo(iServiceInformation.sDVBState)

		if error == self.last_error:
			error = None
		else:
			self.last_error = error

		error = {
			eDVBServicePMTHandler.eventNoResources: _("No free tuner!"),
			eDVBServicePMTHandler.eventTuneFailed: _("Tune failed!"),
			eDVBServicePMTHandler.eventNoPAT: _("No data on transponder!\n(Timeout reading PAT)"),
			eDVBServicePMTHandler.eventNoPATEntry: _("Service not found!\n(SID not found in PAT)"),
			eDVBServicePMTHandler.eventNoPMT: _("Service invalid!\n(Timeout reading PMT)"),
			eDVBServicePMTHandler.eventNewProgramInfo: None,
			eDVBServicePMTHandler.eventTuned: None,
			eDVBServicePMTHandler.eventSOF: None,
			eDVBServicePMTHandler.eventEOF: None,
			eDVBServicePMTHandler.eventMisconfiguration: _("Service unavailable!\nCheck tuner configuration!"),
		}.get(error) #this returns None when the key not exist in the dict

		if error is not None:
			if not config.usage.disable_tuner_error_popup.value:
				Notifications.AddPopup(text = error, type = MessageBox.TYPE_ERROR, timeout = 5, id = "ZapError")
		else:
			Notifications.RemovePopup(id = "ZapError")
