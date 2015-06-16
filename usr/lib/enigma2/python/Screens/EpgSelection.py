from Screen import Screen
from Components.config import config, ConfigClock
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_SIMILAR, EPG_TYPE_MULTI, EPG_TYPE_EPGBAR
from Components.ActionMap import ActionMap, NumberActionMap
from Components.TimerSanityCheck import TimerSanityCheck
from Components.UsageConfig import preferredTimerPath
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event
from Screens.TimerEdit import TimerSanityConflict
from Screens.EventView import EventViewSimple
from Screens.MessageBox import MessageBox
from TimeDateInput import TimeDateInput
from enigma import eServiceReference
from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT
from TimerEntry import TimerEntry
from ServiceReference import ServiceReference
from time import localtime, time

mepg_config_initialized = False

class EPGSelection(Screen):
	EMPTY = 0
	ADD_TIMER = 1
	REMOVE_TIMER = 2
	ENABLE_TIMER = 3
	
	ZAP = 1

	def __init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, isEPGBar=None, switchBouquet=None, EPGNumberZap=None, togglePiP = None):
		Screen.__init__(self, session)
		self.screentitle = _("EPG Selection")
		self.bouquetChangeCB = bouquetChangeCB
		self.serviceChangeCB = serviceChangeCB
		self.switchBouquet = switchBouquet
		self.EPGNumberZap = EPGNumberZap
		self.togglePiP = None
		self.ask_time = -1 #now
		self["key_red"] = Button("")
		self.closeRecursive = False
		self.saved_title = None
		self["Service"] = ServiceEvent()
		self["Event"] = Event()
		if isinstance(service, str) and eventid != None:
			self.type = EPG_TYPE_SIMILAR
			self["key_yellow"] = Button()
			self["key_blue"] = Button()
			self["key_red"] = Button()
			self.currentService=service
			self.eventid = eventid
			self.zapFunc = None
		elif isEPGBar and (isinstance(service, eServiceReference) or isinstance(service, str)):
			self.skinName = ["EPGSelectionEPGBar_SD"]
			if session.desktop.size().width() > 720:
				self.skinName = ["EPGSelectionEPGBar_HD"]
			self.type = EPG_TYPE_EPGBAR
			self["key_yellow"] = Button()
			self["key_blue"] = Button()
			self.currentService=ServiceReference(service)
			self.zapFunc = zapFunc
			self.togglePiP = togglePiP
			self.sort_type = 0
			self.setSortDescription()
			
			self["EPGBarActions"] = ActionMap(["DirectionActions", "OkCancelActions", "InfobarSeekActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.zapTo,
				"left": self.prevService,
				"right": self.nextService,
				"playpauseService": self.setPiPService,
			},-1)
			
			self["EPGBarActions"].csel = self
			
		elif isinstance(service, eServiceReference) or isinstance(service, str):
			self.type = EPG_TYPE_SINGLE
			self["key_yellow"] = Button()
			self["key_blue"] = Button()
			self.currentService=ServiceReference(service)
			self.zapFunc = zapFunc
			self.sort_type = 0
			self.setSortDescription()
		else:
			self.skinName = "EPGSelectionMulti"
			self.type = EPG_TYPE_MULTI
			self["key_yellow"] = Button(_("Prev"))
			self["key_blue"] = Button(_("Next"))
			self["now_button"] = Pixmap()
			self["next_button"] = Pixmap()
			self["more_button"] = Pixmap()
			self["now_button_sel"] = Pixmap()
			self["next_button_sel"] = Pixmap()
			self["more_button_sel"] = Pixmap()
			self["now_text"] = Label()
			self["next_text"] = Label()
			self["more_text"] = Label()
			self["date"] = Label()
			self.services = service
			self.zapFunc = zapFunc

		self["key_green"] = Button(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		self.key_red_choice = self.EMPTY
		self["list"] = EPGList(type = self.type, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)

		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.eventSelected,
				"timerAdd": self.timerAdd,
				"timerEnableDisable": self.timerEnableDisable,
				"instantToggleTimerState" : self.instantToggleTimerState,
				"instantTimer": self.addInstantTimer,
				"yellow": self.yellowButtonPressed,
				"blue": self.blueButtonPressed,
				"info": self.infoKeyPressed,
				"red": self.zapTo,
				"input_date_time": self.enterDateTime,
				"nextBouquet": self.nextBouquet, # just used in multi epg yet
				"prevBouquet": self.prevBouquet, # just used in multi epg yet
				"nextService": self.nextService, # just used in single epg yet
				"prevService": self.prevService, # just used in single epg yet
			})
		self["actions"].csel = self
		
		if EPGNumberZap:
			self["EPGBarNumberActions"] = NumberActionMap( [ "NumberActions"],
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
			})
		
		self.onLayoutFinish.append(self.onCreate)

	def setPiPService(self):
		lst = self["list"]
		ref = lst.getCurrent()[1]
		if not ref:
			ref = self.currentService
		self.togglePiP(ref.ref)

	def keyNumberGlobal(self, number):
		self.EPGNumberZap(number, self)

	def bouquetSwitcher(self, direction):
		if direction:
			lst = self["list"]
			count = lst.getCurrentChangeCount()
			if count == 0:
				ref = lst.getCurrent()[1]
				if not ref:
					ref = self.currentService
				self.switchBouquet(ref.ref, direction, self)

	def nextBouquet(self):
		if self.bouquetChangeCB:
			self.bouquetChangeCB(1, self)
		elif self.switchBouquet:
			self.bouquetSwitcher(1)

	def prevBouquet(self):
		if self.bouquetChangeCB:
			self.bouquetChangeCB(-1, self)
		elif self.switchBouquet:
			self.bouquetSwitcher(-1)

	def nextService(self):
		if self.serviceChangeCB:
			self.serviceChangeCB(1, self)

	def prevService(self):
		if self.serviceChangeCB:
			self.serviceChangeCB(-1, self)

	def enterDateTime(self):
		if self.type == EPG_TYPE_MULTI:
			global mepg_config_initialized
			if not mepg_config_initialized:
				config.misc.prev_mepg_time=ConfigClock(default = time())
				mepg_config_initialized = True
			self.session.openWithCallback(self.onDateTimeInputClosed, TimeDateInput, config.misc.prev_mepg_time )

	def onDateTimeInputClosed(self, ret):
		if len(ret) > 1:
			if ret[0]:
				self.ask_time=ret[1]
				self["list"].fillMultiEPG(self.services, ret[1])

	def closeScreen(self):
		self.close(self.closeRecursive)

	def infoKeyPressed(self):
		cur = self["list"].getCurrent()
		event = cur[0]
		service = cur[1]
		if event is not None:
			if self.type != EPG_TYPE_SIMILAR:
				self.session.open(EventViewSimple, event, service, self.eventViewCallback, self.openSimilarList)
			else:
				self.session.open(EventViewSimple, event, service, self.eventViewCallback)

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def setServices(self, services):
		self.services = services
		self.onCreate()

	def setService(self, service):
		self.currentService = service
		self.onCreate()

	#just used in multipeg
	def onCreate(self):
		l = self["list"]
		l.recalcEntrySize()
		if self.type == EPG_TYPE_MULTI:
			l.fillMultiEPG(self.services, self.ask_time)
			l.moveToService(self.session.nav.getCurrentlyPlayingServiceReference())
		elif self.type == EPG_TYPE_SINGLE:
			service = self.currentService
			self["Service"].newService(service.ref)
			if self.saved_title is None:
				self.saved_title = self.instance.getTitle()
			title = self.saved_title + ' - ' + service.getServiceName()
			self.instance.setTitle(title)
			l.fillSingleEPG(service)
		elif self.type == EPG_TYPE_EPGBAR:
			service = self.currentService
			self["Service"].newService(service.ref)
			l.fillEPGBar(service)
		else:
			l.fillSimilarList(self.currentService, self.eventid)

		self.setTitle(self.screentitle)

	def updateList(self):
		self["list"].reload()

	def eventViewCallback(self, setEvent, setService, val):
		l = self["list"]
		old = l.getCurrent()
		if val == -1:
			self.moveUp()
		elif val == +1:
			self.moveDown()
		cur = l.getCurrent()
		if self.type == EPG_TYPE_MULTI and cur[0] is None and cur[1].ref != old[1].ref:
			self.eventViewCallback(setEvent, setService, val)
		else:
			setService(cur[1])
			setEvent(cur[0])

	def zapTo(self): # just used in multiepg
		if self.zapFunc and self.key_red_choice == self.ZAP:
			lst = self["list"]
			count = lst.getCurrentChangeCount()
			if count == 0:
				self.closeRecursive = True
				ref = lst.getCurrent()[1]
				if not ref: # this could be none if we have no event data in SingleEPG or EPGBar
					ref = self.currentService
				check_bouquet = False
				if self.type == EPG_TYPE_EPGBAR or self.type == EPG_TYPE_SINGLE:
					check_bouquet = True
				self.zapFunc(ref.ref, check_bouquet)
				if self.type == EPG_TYPE_EPGBAR:
					self.closeScreen()
				elif self.type == EPG_TYPE_SINGLE and not config.usage.servicelist_preview_mode.value:
					self.closeScreen()

	def eventSelected(self):
		self.infoKeyPressed()

	def yellowButtonPressed(self):
		if self.type == EPG_TYPE_MULTI:
			self["list"].updateMultiEPG(-1)
		elif self.type == EPG_TYPE_SINGLE or self.type == EPG_TYPE_EPGBAR:
			if self.sort_type == 0:
				self.sort_type = 1
			else:
				self.sort_type = 0
			self["list"].sortSingleEPG(self.sort_type)
			self.setSortDescription()

	def setSortDescription(self):
		if self.sort_type == 1:
			# TRANSLATORS: This must fit into the header button in the EPG-List
			self["key_yellow"].setText(_("Sort Time"))
		else:
			# TRANSLATORS: This must fit into the header button in the EPG-List
			self["key_yellow"].setText(_("Sort A-Z"))

	def blueButtonPressed(self):
		if self.type == EPG_TYPE_MULTI:
			self["list"].updateMultiEPG(1)

	def removeTimer(self, timer, instantTimer = False):
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)
		self["key_green"].setText(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		if instantTimer:
			self.updateList()

	def addInstantTimer(self):
		self.timerAdd(True)

	def timerAdd(self, instantTimer = False):
		cur = self["list"].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		
		if self.key_green_choice == self.ENABLE_TIMER:
			for timer in self.session.nav.RecordTimer.processed_timers:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr and timer.disabled == True:
					if instantTimer:
						self.removeTimer(timer, True)
					else:
						cb_func = lambda ret : not ret or self.removeTimer(timer)
						self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
		else:
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					if instantTimer:
						self.removeTimer(timer, True)
					else:
						cb_func = lambda ret : not ret or self.removeTimer(timer)
						self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
			else:
				newEntry = RecordTimerEntry(serviceref, checkOldTimers = True, dirname = preferredTimerPath(), *parseEvent(event))
				if instantTimer:
					self.session.nav.RecordTimer.saveTimer()
					self.finishedAdd((True, newEntry), True)
				else:
					self.session.openWithCallback(self.finishedAdd, TimerEntry, newEntry)

	def finishedAdd(self, answer, instantTimer = False):
		print "finished add"
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			self["key_green"].setText(_("Remove") + "\n" + _("Disable timer"))
			self.key_green_choice = self.REMOVE_TIMER
			if instantTimer:
				self.updateList()
		
		else:
			self["key_green"].setText(_("Add timer"))
			self.key_green_choice = self.ADD_TIMER
			print "Timeredit aborted"

	def instantToggleTimerState(self):
		self.timerEnableDisable(True)

	def timerEnableDisable(self, instant_toggle = False):
		cur = self["list"].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		
		if self.key_green_choice == self.REMOVE_TIMER:
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					if instant_toggle:
						self.toggleTimerState(timer, True, True)
					else:
						cb_func = lambda ret : not ret or self.toggleTimerState(timer, True, False)
						self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to disable timer:") + "\n" + event.getEventName() + " ?")
					return
		elif self.key_green_choice == self.ENABLE_TIMER:
			for timer in self.session.nav.RecordTimer.processed_timers:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr and timer.disabled == True:
					if instant_toggle:
						self.toggleTimerState(timer, False, True)
					else:
						cb_func = lambda ret : not ret or self.toggleTimerState(timer, False, False)
						self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to enable timer:") + "\n" + event.getEventName() + " ?")
					return

	def toggleTimerState(self, timer, disableTimer, instant_toggle):
		if disableTimer:
			timer.disable()
			self.session.nav.RecordTimer.timeChanged(timer)
			self["key_green"].setText(_("Remove") + "\n" + _("Enable timer"))
			self.key_green_choice = self.ENABLE_TIMER
		else:
			timer.enable()
			timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, timer)
			if not timersanitycheck.check():
				timer.disable()
				self["key_green"].setText("")
				self.key_green_choice = self.EMPTY
				simulTimerList = timersanitycheck.getSimulTimerList()
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishedEdit, TimerSanityConflict, simulTimerList)
			else:
				if timersanitycheck.doubleCheck():
					timer.disable()
					self["key_green"].setText(_("Remove") + "\n" + _("Enable timer"))
					self.key_green_choice = self.REMOVE_TIMER
			self.session.nav.RecordTimer.timeChanged(timer)
		self.updateList()

	def finishedEdit(self, answer):
		if answer[0]:
			entry = answer[1]
			timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, entry)
			success = False
			if not timersanitycheck.check():
				simulTimerList = timersanitycheck.getSimulTimerList()
				if simulTimerList is not None:
					for x in simulTimerList:
						if x.setAutoincreaseEnd(entry):
							self.session.nav.RecordTimer.timeChanged(x)
					if not timersanitycheck.check():
						simulTimerList = timersanitycheck.getSimulTimerList()
						if simulTimerList is not None:
							self.session.openWithCallback(self.finishedEdit, TimerSanityConflict, timersanitycheck.getSimulTimerList())
					else:
						success = True
			else:
				success = True
			if success:
				self.session.nav.RecordTimer.timeChanged(entry)
		else:
			print "Timeredit aborted"

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

	def moveUp(self):
		self["list"].moveUp()

	def moveDown(self):
		self["list"].moveDown()
	
	def applyButtonState(self, state):
		if state == 0:
			self["now_button"].hide()
			self["now_button_sel"].hide()
			self["next_button"].hide()
			self["next_button_sel"].hide()
			self["more_button"].hide()
			self["more_button_sel"].hide()
			self["now_text"].hide()
			self["next_text"].hide()
			self["more_text"].hide()
			self["key_red"].setText("")
		else:
			if state == 1:
				self["now_button_sel"].show()
				self["now_button"].hide()
			else:
				self["now_button"].show()
				self["now_button_sel"].hide()

			if state == 2:
				self["next_button_sel"].show()
				self["next_button"].hide()
			else:
				self["next_button"].show()
				self["next_button_sel"].hide()

			if state == 3:
				self["more_button_sel"].show()
				self["more_button"].hide()
			else:
				self["more_button"].show()
				self["more_button_sel"].hide()

	def onSelectionChanged(self):
		cur = self["list"].getCurrent()
		if cur is None:
			if self.key_green_choice != self.EMPTY:
				self["key_green"].setText("")
				self.key_green_choice = self.EMPTY
			if self.key_red_choice != self.EMPTY:
				self["key_red"].setText("")
				self.key_red_choice = self.EMPTY
			return
		event = cur[0]
		self["Event"].newEvent(event)
		if self.type == EPG_TYPE_MULTI:
			count = self["list"].getCurrentChangeCount()
			if self.ask_time != -1:
				self.applyButtonState(0)
			elif count > 1:
				self.applyButtonState(3)
			elif count > 0:
				self.applyButtonState(2)
			else:
				self.applyButtonState(1)
			days = [ _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun") ]
			datestr = ""
			if event is not None:
				now = time()
				beg = event.getBeginTime()
				nowTime = localtime(now)
				begTime = localtime(beg)
				if nowTime[2] != begTime[2]:
					datestr = '%s %d.%d.'%(days[begTime[6]], begTime[2], begTime[1])
				else:
					datestr = '%s %d.%d.'%(_("Today"), begTime[2], begTime[1])
			self["date"].setText(datestr)
			if cur[1] is None:
				self["Service"].newService(None)
			else:
				self["Service"].newService(cur[1].ref)

		if cur[1] is None or cur[1].getServiceName() == "":
			if self.key_green_choice != self.EMPTY:
				self["key_green"].setText("")
				self.key_green_choice = self.EMPTY
			if self.key_red_choice != self.EMPTY and self.type != EPG_TYPE_EPGBAR and self.type != EPG_TYPE_SINGLE:
				self["key_red"].setText("")
				self.key_red_choice = self.EMPTY
			return
		elif self.key_red_choice != self.ZAP and  (self.type == EPG_TYPE_MULTI or self.type == EPG_TYPE_EPGBAR or self.type == EPG_TYPE_SINGLE):
				if self.zapFunc:
					self["key_red"].setText(_("Zap"))
					self.key_red_choice = self.ZAP

		if event is None:
			if self.key_green_choice != self.EMPTY:
				self["key_green"].setText("")
				self.key_green_choice = self.EMPTY
			return

		serviceref = cur[1]
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		isRecordEvent = False
		isDisabled = False
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				isRecordEvent = True
				break
		if not isRecordEvent:
			for timer in self.session.nav.RecordTimer.processed_timers:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr and timer.disabled == True:
					isDisabled = True
					break
		if isDisabled:
			self["key_green"].setText(_("Remove timer") + "\n" + _("Enable timer"))
			self.key_green_choice = self.ENABLE_TIMER
		elif isRecordEvent:
			self["key_green"].setText(_("Remove timer") + "\n" + _("Disable timer"))
			self.key_green_choice = self.REMOVE_TIMER
		elif not isRecordEvent and self.key_green_choice != self.ADD_TIMER:
			self["key_green"].setText(_("Add timer"))
			self.key_green_choice = self.ADD_TIMER

