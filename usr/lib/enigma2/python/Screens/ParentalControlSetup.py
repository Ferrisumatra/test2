from Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import NumberActionMap
from Components.config import config, getConfigListEntry, ConfigNothing, NoSave, ConfigPIN
from Components.ParentalControlList import ParentalControlEntryComponent, ParentalControlList
from Components.ParentalControl import parentalControlFolder
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.InputBox import PinInput
from Tools.BoundFunction import boundFunction
from enigma import eServiceCenter, eTimer, eServiceReference
from operator import itemgetter

class ProtectedScreen:
	def __init__(self):
		if self.isProtected():
			self.onFirstExecBegin.append(boundFunction(self.session.openWithCallback, self.pinEntered, PinInput, pinList = [self.protectedWithPin()], triesEntry = self.getTriesEntry(), title = self.getPinText(), windowTitle = _("Enter pin code")))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def getPinText(self):
		return _("Please enter the correct pin code")

	def isProtected(self):
		return True

	def protectedWithPin(self):
		return config.ParentalControl.setuppin.value

	def protectedClose_ParentalControl(self, res = None):
		self.close()

	def pinEntered(self, result):
		if result is None:
			self.protectedClose_ParentalControl()
		elif not result:
			self.session.openWithCallback(self.protectedClose_ParentalControl, MessageBox, _("The pin code you entered is wrong."), MessageBox.TYPE_ERROR)

class ParentalControlSetup(Screen, ConfigListScreen, ProtectedScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		ProtectedScreen.__init__(self)
		# for the skin: first try ParentalControlSetup, then Setup, this allows individual skinning
		self.skinName = ["ParentalControlSetup", "Setup" ]
		self.setup_title = _("Parental control setup")
		self.onChangedEntry = [ ]
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()
		
		self.cur_idx = 0
		self["config"].onSelectionChanged.append(self.skipDivider)
		
		self["actions"] = NumberActionMap(["SetupActions"],
		{
		  "cancel": self.keyCancel,
		  "save": self.keyCancel
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def isProtected(self):
		return (config.ParentalControl.setuppinactive.value and not (config.ParentalControl.config_sections.configuration.value or config.ParentalControl.config_sections.main_menu.value)) and config.ParentalControl.configured.value

	def skipDivider(self):
		list_len = len(self["config"].list)
		idx = self["config"].getCurrentIndex()
		if self["config"].l.getCurrentSelection() == self.divider:
			if self.cur_idx < idx:
				if idx +1 < list_len:
					idx += 1
				elif idx + 1 == list_len:
					idx = 0
				self["config"].setCurrentIndex(idx)
			else:
				if idx -1 >= 0:
					idx += -1
				else:
					idx = list_len - 1
			self["config"].setCurrentIndex(idx)
		self.cur_idx = idx
	
	def createSetup(self):
		self.editListEntry = None
		self.changePin = None
		self.changeSetupPin = None
		
		self.list = []
		self.list.append(getConfigListEntry(_("Enable parental control"), config.ParentalControl.configured))
		self.editBouquetListEntry = -1
		self.reloadLists = -1
		self.divider = getConfigListEntry("- - - - - - - - - - - - - - - - - - - - - - -", NoSave(ConfigNothing()))
		self.resetMoviePinCache = getConfigListEntry(_("Reset movie / directory PIN cache"), NoSave(ConfigNothing()))
		self.changeMoviePin = getConfigListEntry(_("Change movie / directory PIN"), NoSave(ConfigNothing()))
		self.resetDeletePinCache = getConfigListEntry(_("Reset movie-delete PIN cache"), NoSave(ConfigNothing()))
		self.changeDeletePin = getConfigListEntry(_("Change movie-delete PIN"), NoSave(ConfigNothing()))
		if config.ParentalControl.configured.value:
			self.list.append(self.divider)
			self.list.append(getConfigListEntry(_("Protect setup"), config.ParentalControl.setuppinactive))
			if config.ParentalControl.setuppinactive.value:
				self.list.append(getConfigListEntry(_("Protect main menu"), config.ParentalControl.config_sections.main_menu))
				self.list.append(getConfigListEntry(_("Protect configuration"), config.ParentalControl.config_sections.configuration))
				self.list.append(getConfigListEntry(_("Protect movie list"), config.ParentalControl.config_sections.movie_list))
				self.list.append(getConfigListEntry(_("Protect timer list"), config.ParentalControl.config_sections.timer_list))
				self.list.append(getConfigListEntry(_("Protect plugin browser"), config.ParentalControl.config_sections.plugin_browser))
				self.list.append(getConfigListEntry(_("Protect standby menu"), config.ParentalControl.config_sections.standby_menu))
				self.list.append(getConfigListEntry(_("Protect VTi menu"), config.ParentalControl.config_sections.vti_menu))
				self.list.append(getConfigListEntry(_("Protect VTi Panel"), config.ParentalControl.config_sections.vti_panel))
				self.changeSetupPin = getConfigListEntry(_("Change setup PIN"), NoSave(ConfigNothing()))
				self.list.append(self.changeSetupPin)
			self.list.append(self.divider)
			self.list.append(getConfigListEntry(_("Protect services"), config.ParentalControl.servicepinactive))
			if config.ParentalControl.servicepinactive.value:
				self.list.append(getConfigListEntry(_("Parental control type"), config.ParentalControl.type))
				if config.ParentalControl.mode.value == "complex":
					self.changePin = getConfigListEntry(_("Change service PINs"), NoSave(ConfigNothing()))
					self.list.append(self.changePin)
				elif config.ParentalControl.mode.value == "simple":	
					self.changePin = getConfigListEntry(_("Change service PIN"), NoSave(ConfigNothing()))
					self.list.append(self.changePin)
				self.list.append(getConfigListEntry(_("Remember service PIN"), config.ParentalControl.storeservicepin))	
				self.list.append(getConfigListEntry(_("Remember service PIN cancel"), config.ParentalControl.storeservicepincancel))	
				self.editListEntry = getConfigListEntry(_("Edit services list"), NoSave(ConfigNothing()))
				self.list.append(self.editListEntry)
				self.editBouquetListEntry = getConfigListEntry(_("Edit bouquets list"), NoSave(ConfigNothing()))
				self.list.append(self.editBouquetListEntry)
				self.reloadLists = getConfigListEntry(_("Reload Black-/Whitelists"), NoSave(ConfigNothing()))
				self.list.append(self.reloadLists)
			self.list.append(self.divider)
			self.list.append(getConfigListEntry(_("Protect movies and directories"), config.ParentalControl.moviepinactive))
			if config.ParentalControl.moviepinactive.value:
				self.list.append(self.changeMoviePin)
				self.list.append(getConfigListEntry(_("Remember movie / directory PIN"), config.ParentalControl.storemoviepin))
				self.list.append(self.resetMoviePinCache)
			self.list.append(self.divider)
			self.list.append(getConfigListEntry(_("Protect deleting of movies"), config.ParentalControl.deletepinactive))
			if config.ParentalControl.deletepinactive.value:
				self.list.append(self.changeDeletePin)
				self.list.append(getConfigListEntry(_("Remember movie-delete PIN"), config.ParentalControl.storedeletepin))
				self.list.append(self.resetDeletePinCache)

		self["config"].list = self.list
		self["config"].setList(self.list)

	def keyOK(self):
		if self["config"].l.getCurrentSelection() == self.editListEntry:
			self.session.open(ParentalControlEditor)
		elif self["config"].l.getCurrentSelection() == self.editBouquetListEntry:
			self.session.open(ParentalControlBouquetEditor)
		elif self["config"].l.getCurrentSelection() == self.changePin:
			if config.ParentalControl.mode.value == "complex":
				pass
			else:
				self.session.open(ParentalControlChangePin, config.ParentalControl.servicepin[0], _("service PIN"))
		elif self["config"].l.getCurrentSelection() == self.changeSetupPin:
			self.session.open(ParentalControlChangePin, config.ParentalControl.setuppin, _("setup PIN"))
		elif self["config"].l.getCurrentSelection() == self.changeMoviePin:
			self.session.open(ParentalControlChangePin, config.ParentalControl.moviepin, _("movie / directory PIN"))
		elif self["config"].l.getCurrentSelection() == self.resetMoviePinCache:
			if not parentalControlFolder.configInitialized:
				parentalControlFolder.getConfigValues()
			parentalControlFolder.resetSessionPin()
			self.keyCancel()
		elif self["config"].l.getCurrentSelection() == self.changeDeletePin:
			self.session.open(ParentalControlChangePin, config.ParentalControl.deletepin, _("movie-delete PIN"))
		elif self["config"].l.getCurrentSelection() == self.resetDeletePinCache:
			if not parentalControlFolder.configInitialized:
				parentalControlFolder.getConfigValues()
			parentalControlFolder.resetSessionDeletePin()
			self.keyCancel()
		elif self["config"].l.getCurrentSelection() == self.reloadLists:
			from Components.ParentalControl import parentalControl
			parentalControl.open()
		else:
			ConfigListScreen.keyRight(self)
			self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def SetupPinMessageCallback(self, value):
		if value:
			self.session.openWithCallback(self.cancelCB, ParentalControlChangePin, config.ParentalControl.setuppin, _("setup PIN"))
		else:
			config.ParentalControl.setuppinactive.value = False
			self.keyCancel()

	def ServicePinMessageCallback(self, value):
		if value:
			self.session.openWithCallback(self.cancelCB, ParentalControlChangePin, config.ParentalControl.servicepin[0], _("service PIN"))
		else:
			config.ParentalControl.servicepinactive.value = False
			self.keyCancel()

	def MoviePinMessageCallback(self, value):
		if value:
			self.session.openWithCallback(self.cancelCB, ParentalControlChangePin, config.ParentalControl.moviepin, _("movie / directory PIN"))
		else:
			config.ParentalControl.moviepinactive.value = False
			self.keyCancel()

	def DeletePinMessageCallback(self, value):
		if value:
			self.session.openWithCallback(self.cancelCB, ParentalControlChangePin, config.ParentalControl.deletepin, _("movie-delete PIN"))
		else:
			config.ParentalControl.deletepinactive.value = False
			self.keyCancel()

	def cancelCB(self,value):
		self.keyCancel()

	def keyCancel(self):
		if config.ParentalControl.setuppinactive.value and config.ParentalControl.setuppin.value == 'aaaa':
			self.session.openWithCallback(self.SetupPinMessageCallback, MessageBox, _("No valid setup PIN found!\nDo you like to change the setup PIN now?\nWhen you say 'No' here the setup protection stay disabled!"), MessageBox.TYPE_YESNO)
		elif config.ParentalControl.servicepinactive.value and config.ParentalControl.servicepin[0].value == 'aaaa':
			self.session.openWithCallback(self.ServicePinMessageCallback, MessageBox, _("No valid service PIN found!\nDo you like to change the service PIN now?\nWhen you say 'No' here the service protection stay disabled!"), MessageBox.TYPE_YESNO)
		elif config.ParentalControl.moviepinactive.value and config.ParentalControl.moviepin.value == 'aaaa':
			self.session.openWithCallback(self.MoviePinMessageCallback, MessageBox, _("No valid movie / directory PIN found!\nDo you like to change the movie / directory PIN now?\nWhen you say 'No' here the movie / directory protection stay disabled!"), MessageBox.TYPE_YESNO)
		elif config.ParentalControl.deletepinactive.value and config.ParentalControl.deletepin.value == 'aaaa':
			self.session.openWithCallback(self.DeletePinMessageCallback, MessageBox, _("No valid movie-delete PIN found!\nDo you like to change the movie-delete PIN now?\nWhen you say 'No' here the movie / directory protection stay disabled!"), MessageBox.TYPE_YESNO)
		else:
			for x in self["config"].list:
				x[1].save()
			self.close()

	def keyNumberGlobal(self, number):
		pass

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

from Screens.ChannelSelection import service_types_tv
SPECIAL_CHAR = 96
class ParentalControlEditor(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.list = []
		self.servicelist = ParentalControlList(self.list)
		self["servicelist"] = self.servicelist;
		self.currentLetter = chr(SPECIAL_CHAR)
		self.readServiceList()
		self.chooseLetterTimer = eTimer()
		self.chooseLetterTimer.callback.append(self.chooseLetter)
		self.onLayoutFinish.append(self.LayoutFinished)

		self["actions"] = NumberActionMap(["DirectionActions", "ColorActions", "OkCancelActions", "NumberActions"],
		{
			"ok": self.select,
			"cancel": self.cancel,
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
		}, -1)

	def LayoutFinished(self):
		self.chooseLetterTimer.start(0, True)

	def cancel(self):
		self.chooseLetter()

	def select(self):
		self.servicelist.toggleSelectedLock()

	def keyNumberGlobal(self, number):
		pass

	def readServiceList(self):
		serviceHandler = eServiceCenter.getInstance()
		refstr = '%s ORDER BY name' % (service_types_tv)
		self.root = eServiceReference(refstr)
		self.servicesList = {}
		list = serviceHandler.list(self.root)
		if list is not None:
			services = list.getContent("CN", True)
			for s in services:
				key = s[1].lower()[0]
				if key < 'a' or key > 'z':
					key = chr(SPECIAL_CHAR)
				if not self.servicesList.has_key(key):
					self.servicesList[key] = []
				self.servicesList[key].append(s)
			
	def chooseLetter(self):
		mylist = []
		for x in self.servicesList.keys():
			if x == chr(SPECIAL_CHAR):
				x = (_("special characters"), x)
			else:
				x = (x, x)
			mylist.append(x)
		mylist.sort(key=itemgetter(1))
		sel = ord(self.currentLetter) - SPECIAL_CHAR
		self.session.openWithCallback(self.letterChosen, ChoiceBox, title=_("Show services beginning with"), list=mylist, keys = [], selection = sel)

	def letterChosen(self, result):
		from Components.ParentalControl import parentalControl
		if result is not None:
			self.currentLetter = result[1]
			self.list = [ParentalControlEntryComponent(x[0], x[1], parentalControl.getProtectionType(x[0])) for x in self.servicesList[result[1]]]
			self.servicelist.setList(self.list)
		else:
			parentalControl.save()
			self.close()

class ParentalControlBouquetEditor(Screen):
	#This new class allows adding complete bouquets to black- and whitelists
	#The servicereference that is stored for bouquets is their refstr as listed in bouquets.tv
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "ParentalControlEditor"
		self.list = []
		self.bouquetslist = ParentalControlList(self.list)
		self["servicelist"] = self.bouquetslist;
		self.readBouquetList()
		self.onLayoutFinish.append(self.selectBouquet)

		self["actions"] = NumberActionMap(["DirectionActions", "ColorActions", "OkCancelActions"],
		{
			"ok": self.select,
			"cancel": self.cancel
		}, -1)

	def cancel(self):
		from Components.ParentalControl import parentalControl
		parentalControl.save()
		self.close()

	def select(self):
		self.bouquetslist.toggleSelectedLock()

	def readBouquetList(self):
		serviceHandler = eServiceCenter.getInstance()
		refstr = '1:134:1:0:0:0:0:0:0:0:FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet'
		bouquetroot = eServiceReference(refstr)
		self.bouquetlist = {}
		list = serviceHandler.list(bouquetroot)
		if list is not None:
			self.bouquetlist = list.getContent("CN", True)
	
	def selectBouquet(self):
		from Components.ParentalControl import parentalControl
		self.list = [ParentalControlEntryComponent(x[0], x[1], parentalControl.getProtectionType(x[0])) for x in self.bouquetlist]
		self.bouquetslist.setList(self.list)

class ParentalControlChangePin(Screen, ConfigListScreen, ProtectedScreen):
	def __init__(self, session, pin, pinname):
		Screen.__init__(self, session)
		# for the skin: first try ParentalControlChangePin, then Setup, this allows individual skinning
		self.skinName = ["ParentalControlChangePin", "Setup" ]
		self.setup_title = _("Change pin code")
		self.onChangedEntry = [ ]

		self.pin = pin
		self.list = []
		self.pin1 = ConfigPIN(default = 1111, censor = "*")
		self.pin2 = ConfigPIN(default = 1112, censor = "*")
		self.pin1.addEndNotifier(boundFunction(self.valueChanged, 1))
		self.pin2.addEndNotifier(boundFunction(self.valueChanged, 2))
		self.list.append(getConfigListEntry(_("New PIN"), NoSave(self.pin1)))
		self.list.append(getConfigListEntry(_("Reenter new PIN"), NoSave(self.pin2)))
		ConfigListScreen.__init__(self, self.list)
		ProtectedScreen.__init__(self)
		
		self["actions"] = NumberActionMap(["DirectionActions", "ColorActions", "OkCancelActions"],
		{
			"cancel": self.cancel,
			"red": self.cancel,
			"save": self.keyOK,
		}, -1)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def valueChanged(self, pin, value):
		if pin == 1:
			self["config"].setCurrentIndex(1)
		elif pin == 2:
			self.keyOK()

	def getPinText(self):
		return _("Please enter the old PIN code")

	def isProtected(self):
		return (self.pin.value != "aaaa")

	def protectedWithPin(self):
		return self.pin.value

	def keyOK(self):
		if self.pin1.value == self.pin2.value:
			self.pin.value = self.pin1.value
			self.pin.save()
			self.session.openWithCallback(self.close, MessageBox, _("The PIN code has been changed successfully."), MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("The PIN codes you entered are different."), MessageBox.TYPE_ERROR)

	def cancel(self):
		self.close(None)

	def keyNumberGlobal(self, number):
		ConfigListScreen.keyNumberGlobal(self, number)

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary
