from Screen import Screen
from Components.Button import Button
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.MenuList import MenuList
from Components.MovieList import MovieList
from Components.DiskInfo import DiskInfo
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.PluginComponent import plugins
from Components.config import config, ConfigSubsection, ConfigText, ConfigInteger, ConfigLocations, ConfigSet, ConfigYesNo, getConfigListEntry, ConfigSelection, NoSave, ConfigDictionarySet
from Components.ConfigList import ConfigListScreen
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.StaticText import StaticText
from Components.UsageConfig import defaultMoviePath
from Components.FileTransfer import FileTransferJob
from Components.Task import job_manager

from Plugins.Plugin import PluginDescriptor

from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox, PinInput
from Screens.LocationBox import MovieLocationBox
from Screens.FileDirBrowser import FileDirBrowser
from Screens.HelpMenu import HelpableScreen
from Screens.Setup import Setup
from Screens.TaskList import TaskListScreen

from Tools.Directories import *
from Tools.BoundFunction import boundFunction
from Tools.MovieInfoParser import getExtendedMovieDescription

from enigma import eServiceReference, eServiceCenter, eTimer, eSize, eConsoleAppContainer
import os

from timer import TimerEntry
from RecordTimer import AFTEREVENT
import NavigationInstance

bookmark_choices = [(resolveFilename(SCOPE_HDD))]
fnc_choices = [	("bookmark", _("assign bookmark")),
		("mv", _("move")),
		("cp", _("copy")),
		("rm", _("delete")),
		("sort", _("sort")),
		("trashdir", _("movie trash")),
		("mkdir", _("create folder")),
		("showdir", _("show folder")),
		("playlast", _("last video")),
		("opentasklist", _("Task list")),
		("configuration", _("Setup")),
		("looplistview", _("change list view")),
		("playmode_random", _("Shuffle play")),
		("playmode_loop", _("Play all")),
		("showtagmenu", _("show tag menu")),
		("showfirsttag", _("show first selected tag")),
		("showsecondtag", _("show second selected tag")),
		("showall", _("show all")),
		("colorkeys", _("Color Buttons")),
		("contextmenu", _("Context Menu")),
		("selectbookmark", _("select bookmark")),
		("symlink", _("create symlink")),
		("selectmode", _("toggle select mode")),
		("parentalcontrol", _("toggle parental control")),
		("off", _("off")),]

config.movielist = ConfigSubsection()
config.movielist.moviedirs_config = ConfigDictionarySet()
config.movielist.moviesort = ConfigInteger(default=MovieList.SORT_RECORDED)
config.movielist.listtype = ConfigInteger(default=MovieList.LISTTYPE_MINIMALVTI)
config.movielist.description = ConfigInteger(default=MovieList.SHOW_DESCRIPTION)
config.movielist.last_videodir = ConfigText(default=resolveFilename(SCOPE_HDD))
config.movielist.last_timer_videodir = ConfigText(default=resolveFilename(SCOPE_HDD))
config.movielist.videodirs = ConfigLocations(default=[resolveFilename(SCOPE_HDD)])
config.movielist.first_tags = ConfigText(default="")
config.movielist.second_tags = ConfigText(default="")
config.movielist.last_selected_tags = ConfigSet([], default=[])
# single key press
config.movielist.red_button = ConfigSelection(default = "rm", choices = fnc_choices, allow_invalid_choice = True)
config.movielist.green_button = ConfigSelection(default = "sort", choices = fnc_choices, allow_invalid_choice = True)
config.movielist.yellow_button = ConfigSelection(default = "mv", choices = fnc_choices, allow_invalid_choice = True)
config.movielist.blue_button = ConfigSelection(default = "mkdir", choices = fnc_choices, allow_invalid_choice = True)

config.movielist.red_bookmark = ConfigSelection(default = resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)
config.movielist.green_bookmark = ConfigSelection(default = resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)
config.movielist.yellow_bookmark = ConfigSelection(default = resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)
config.movielist.blue_bookmark = ConfigSelection(default = resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)

config.movielist.red_bookmark_friendly_name = ConfigText(default = "NFS", visible_width = 20, fixed_size = False)
config.movielist.green_bookmark_friendly_name = ConfigText(default = "Home", visible_width = 20, fixed_size = False)
config.movielist.yellow_bookmark_friendly_name = ConfigText(default = "NAS", visible_width = 20, fixed_size = False)
config.movielist.blue_bookmark_friendly_name = ConfigText(default = "Remote Vu+", visible_width = 20, fixed_size = False)

# long key press
config.movielist.red_long_button = ConfigSelection(default = "colorkeys", choices = fnc_choices, allow_invalid_choice = True)
config.movielist.green_long_button = ConfigSelection(default = "selectbookmark", choices = fnc_choices, allow_invalid_choice = True)
config.movielist.yellow_long_button = ConfigSelection(default = "looplistview", choices = fnc_choices, allow_invalid_choice = True)
config.movielist.blue_long_button = ConfigSelection(default = "opentasklist", choices = fnc_choices, allow_invalid_choice = True)

config.movielist.red_long_bookmark = ConfigSelection(default=resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)
config.movielist.green_long_bookmark = ConfigSelection(default=resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)
config.movielist.yellow_long_bookmark = ConfigSelection(default = resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)
config.movielist.blue_long_bookmark = ConfigSelection(default = resolveFilename(SCOPE_HDD), choices = bookmark_choices, allow_invalid_choice = True)

config.movielist.red_long_bookmark_friendly_name = ConfigText(default = "Bookmark Red", visible_width = 20, fixed_size = False)
config.movielist.green_long_bookmark_friendly_name = ConfigText(default = "Bookmark Green", visible_width = 20, fixed_size = False)
config.movielist.yellow_long_bookmark_friendly_name = ConfigText(default = "Bookmark Yellow", visible_width = 20, fixed_size = False)
config.movielist.blue_long_bookmark_friendly_name = ConfigText(default = "Bookmark Blue", visible_width = 20, fixed_size = False)

def setPreferredTagEditor(te):
	global preferredTagEditor
	try:
		if preferredTagEditor == None:
			preferredTagEditor = te
			print "Preferred tag editor changed to ", preferredTagEditor
		else:
			print "Preferred tag editor already set to ", preferredTagEditor
			print "ignoring ", te
	except:
		preferredTagEditor = te
		print "Preferred tag editor set to ", preferredTagEditor

def getPreferredTagEditor():
	global preferredTagEditor
	return preferredTagEditor

setPreferredTagEditor(None)

def getTrashDir(path):
	trash_dir_name = "movie_trash"
	path = os.path.realpath(path)
	path = os.path.abspath(path)
	while not os.path.ismount(path):
		path = os.path.dirname(path)
	if path.endswith("/"):
		path = path + trash_dir_name
	else:
		path = path + "/" + trash_dir_name
	if not fileExists(path):
		statvfs = os.statvfs(path.rstrip(trash_dir_name))
		free = (statvfs.f_frsize * statvfs.f_bavail) / (1024 * 1024 * 1024)
		if free < 15:
			return None
		try:
			os.makedirs(path)
		except OSError:
			pass
	if fileExists(path, mode="w"):
		return path
	else:
		return None

class MovieListButtonConfig(Screen,ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["MovieListButtonConfig", "Setup"]
		
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["shortcuts"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyGreen,
			"cancel": self.keyRed,
			"red": self.keyRed,
			"green": self.keyGreen,
		})
		
		self.list = []
		ConfigListScreen.__init__(self, self.list,session = session, on_change = self.updateEntries)
		self.initConfig()

	def initConfig(self):
		for video_dir in config.movielist.videodirs.value:
			if video_dir not in bookmark_choices:
				bookmark_choices.append(video_dir)
		self.red_button = getConfigListEntry(_("Select %s button function:") % _("red"), config.movielist.red_button)
		self.green_button = getConfigListEntry(_("Select %s button function:") % _("green"), config.movielist.green_button)
		self.yellow_button = getConfigListEntry(_("Select %s button function:") % _("yellow"), config.movielist.yellow_button)
		self.blue_button = getConfigListEntry(_("Select %s button function:") % _("blue"), config.movielist.blue_button)
		
		self.red_long_button = getConfigListEntry(_("Select %s (long) button function:") % _("red"), config.movielist.red_long_button)
		self.green_long_button = getConfigListEntry(_("Select %s (long) button function:") % _("green"), config.movielist.green_long_button)
		self.yellow_long_button = getConfigListEntry(_("Select %s (long) button function:") % _("yellow"), config.movielist.yellow_long_button)
		self.blue_long_button = getConfigListEntry(_("Select %s (long) button function:") % _("blue"), config.movielist.blue_long_button)
		
		self.red_bookmark = getConfigListEntry(_("Bookmark for button %s:") % _("red"), config.movielist.red_bookmark)
		self.green_bookmark = getConfigListEntry(_("Bookmark for button %s:") % _("green"), config.movielist.green_bookmark)
		self.yellow_bookmark = getConfigListEntry(_("Bookmark for button %s:") % _("yellow"), config.movielist.yellow_bookmark)
		self.blue_bookmark = getConfigListEntry(_("Bookmark for button %s:") % _("blue"), config.movielist.blue_bookmark)
		
		self.red_long_bookmark = getConfigListEntry(_("Bookmark for button %s (long):") % _("red"), config.movielist.red_long_bookmark)
		self.green_long_bookmark = getConfigListEntry(_("Bookmark for button %s (long):") % _("green"), config.movielist.green_long_bookmark)
		self.yellow_long_bookmark = getConfigListEntry(_("Bookmark for button %s (long):") % _("yellow"), config.movielist.yellow_long_bookmark)
		self.blue_long_bookmark = getConfigListEntry(_("Bookmark for button %s (long):") % _("blue"), config.movielist.blue_long_bookmark)
		
		self.createSetup()

	def createSetup(self):
		self.list = []
		self.list.append(self.red_button)
		if self.red_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s:") % _("red")), config.movielist.red_bookmark_friendly_name))
			self.list.append(self.red_bookmark)
		self.list.append(self.green_button)
		if self.green_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s:") % _("green")), config.movielist.green_bookmark_friendly_name))
			self.list.append(self.green_bookmark)
		self.list.append(self.yellow_button)
		if self.yellow_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s:") % _("yellow")), config.movielist.yellow_bookmark_friendly_name))
			self.list.append(self.yellow_bookmark)
		self.list.append(self.blue_button)
		if self.blue_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s:") % _("blue")), config.movielist.blue_bookmark_friendly_name))
			self.list.append(self.blue_bookmark)
		self.list.append(self.red_long_button)
		if self.red_long_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s (long):") % _("red")), config.movielist.red_long_bookmark_friendly_name))
			self.list.append(self.red_long_bookmark)
		self.list.append(self.green_long_button)
		if self.green_long_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s (long):") % _("green")), config.movielist.green_long_bookmark_friendly_name))
			self.list.append(self.green_long_bookmark)
		self.list.append(self.yellow_long_button)
		if self.yellow_long_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s (long):") % _("yellow")), config.movielist.yellow_long_bookmark_friendly_name))
			self.list.append(self.yellow_long_bookmark)
		self.list.append(self.blue_long_button)
		if self.blue_long_button[1].value == "bookmark":
			self.list.append(getConfigListEntry(_(_("Short name for bookmark %s (long):") % _("blue")), config.movielist.blue_long_bookmark_friendly_name))
			self.list.append(self.blue_long_bookmark)
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def updateEntries(self):
		if not isinstance(self["config"].getCurrent()[1], ConfigText):
			self.createSetup()

	def keyGreen(self):
		## hack alert !! remove input box before closing
		self["config"].setCurrentIndex(0)
		for x in self["config"].list:
			x[1].save()
		self.close(True)

	def keyRed(self):
		## hack alert !! remove input box before closing
		self["config"].setCurrentIndex(0)
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO, default = False)
		else:
			self.doClose()

	def doClose(self):
		## hack alert !! remove input box before closing
		self["config"].setCurrentIndex(0)
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def cancelConfirm(self, result):
		if result:
			self.doClose()

class MovieSelectionList(Screen):
	def __init__(self, session, csel):
		Screen.__init__(self, session)
		self.skinName = ["MovieSelectionList", "MovieContextMenu"]
		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.close,
			"cancel": self.close
		})
		entries = csel.getSelectedEntries()
		if entries and len(entries):
			serviceHandler = eServiceCenter.getInstance()
			idx = 0
			for entry in entries:
				info = serviceHandler.info(entry)
				txt = info and info.getName(entry) or _("unknown")
				if idx == 0:
					menu = [(txt, self.close)]
				else:
					menu.append((txt, self.close))
				idx += 1
		else:
			menu = [(_("no selected item"), self.close)]
		self["menu"] = MenuList(menu)

class MovieContextMenu(Screen):
	def __init__(self, session, csel, service):
		Screen.__init__(self, session)
		self.csel = csel
		self.service = service
		self.select_mode = self.csel.getSelectMode()

		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"ok": self.okbuttonClick,
				"cancel": self.cancelClick
			})
		
		serviceHandler = eServiceCenter.getInstance()
		info = serviceHandler.info(self.service)
		name = info and info.getName(self.service) or _("unknown")
		if len(name) > 25:
			name = name[:25] + "..."
		
		if self.service.flags & eServiceReference.mustDescent:
			self.bookmark_dir = self.service.getPath()
		else:
			self.bookmark_dir = config.movielist.last_videodir.value
		bookmark_name = self.bookmark_dir
		if len(bookmark_name) > 15:
			bookmark_name = "..." + bookmark_name[-15:]

		if self.select_mode:
			menu = [(_("show selected items"), self.showSelectedMovies)]
			menu.append((_("delete selected items"), self.delete))
			menu.append((_("copy selected items"), self.copy))
			menu.append((_("move selected items"), self.remove))
			menu.append((_("play selected items"), self.playSelectedEntries))
			menu.append((_("reset play progress of selected items"), self.resetProgress))
			menu.append((_("disable select mode"), self.toggleSelectMode))
		else:
			menu = [(_("delete : %s") % name, self.delete)]
			menu.append((_("copy : %s") % name, self.copy))
			menu.append((_("move : %s") % name, self.remove))
			menu.append((_("enable select mode"), self.toggleSelectMode))
			if config.ParentalControl.moviepinactive.value:
				path = os.path.realpath(self.bookmark_dir)
				path = os.path.abspath(path)
				if not path.endswith('/'):
					path = path + '/'
				protect = config.movielist.moviedirs_config.getConfigValue(path, "protect")
				if protect == 1:
					menu.append((_("remove from parental protection") + ": " + path, self.toggleParentalControl))
				else:
					menu.append((_("add to parental protection") + ": " + path, self.toggleParentalControl))
			if not self.service.flags & eServiceReference.mustDescent:
				menu.append((_("Shuffle play"), self.playmode_random))
				menu.append((_("Play all"), self.playmode_loop))
			if self.bookmark_dir not in config.movielist.videodirs.value:
				menu.append((_("create bookmark : %s") % bookmark_name, self.create_bookmark))
			menu.append((_("create symlink"), self.create_link))
			
			moviename = os.path.realpath(self.service.getPath())
			if fileExists(moviename + ".cuts"):
				menu.append((_("reset play progress"), boundFunction(self.resetProgress)))

			menu.append((_("start last played movie"), boundFunction(self.lastPlayed)))

			menu.extend([(p.description, boundFunction(self.execPlugin, p)) for p in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST)])

		self.trash_dir = getTrashDir(service.getPath())
		movie_dir = os.path.realpath(config.movielist.last_videodir.value)
		if self.trash_dir and self.trash_dir == movie_dir:
			menu.append((_("clear movie trash"), self.deleteMovieTrashEntries))
		else:
			menu.append((_("movie trash"), self.showMovieTrash))
		menu.append((_("create folder"), self.make_dir))
		self.tasklist = []
		for job in job_manager.getPendingJobs():
			self.tasklist.append((job,job.name,job.getStatustext(),int(100*job.progress/float(job.end)) ,str(100*job.progress/float(job.end)) + "%" ))
		if len(self.tasklist):
			menu.append((_("Task list"), self.openTasklist))

		menu.append((_("customize color buttons"), boundFunction(self.customizeColorButtons)))

		movie_sort = {  MovieList.SORT_ALPHANUMERIC: (_("alphabetic sort"), boundFunction(self.sortBy, MovieList.SORT_ALPHANUMERIC)),
				MovieList.SORT_ALPHANUMERIC_INVERS: (_("alphabetic sort") + " (" +  _("reverse") + ")", boundFunction(self.sortBy, MovieList.SORT_ALPHANUMERIC_INVERS)),
				MovieList.SORT_RECORDED: (_("sort by date"), boundFunction(self.sortBy, MovieList.SORT_RECORDED)),
				MovieList.SORT_RECORDED_INVERS: (_("sort by date") + " (" +  _("reverse") + ")", boundFunction(self.sortBy, MovieList.SORT_RECORDED_INVERS))
			      }
		for sort_type, entry  in movie_sort.iteritems():
			if config.movielist.moviesort.value != sort_type:
				menu.append(entry)
		
		menu.extend((
			(_("list style default"), boundFunction(self.listType, MovieList.LISTTYPE_ORIGINAL)),
			(_("list style compact with description"), boundFunction(self.listType, MovieList.LISTTYPE_COMPACT_DESCRIPTION)),
			(_("list style compact"), boundFunction(self.listType, MovieList.LISTTYPE_COMPACT)),
			(_("list style single line"), boundFunction(self.listType, MovieList.LISTTYPE_MINIMAL)),
			(_("list style single line") + " VTi", boundFunction(self.listType, MovieList.LISTTYPE_MINIMALVTI))
		))

		if config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
			menu.append((_("hide extended description"), boundFunction(self.showDescription, MovieList.HIDE_DESCRIPTION)))
		else:
			menu.append((_("show extended description"), boundFunction(self.showDescription, MovieList.SHOW_DESCRIPTION)))

		menu.append((_("show more movie list options"), self.openMovieListOption))

		self["menu"] = MenuList(menu)

	def showMovieTrash(self):
		self.csel.selectTrashDir()
		self.close()

	def showSelectedMovies(self):
		self.session.open(MovieSelectionList, self.csel)

	def openMovieListOption(self):
		self.session.openWithCallback(self.MovieListConfigFinished, Setup, "vti_movies")

	def MovieListConfigFinished(self, ret = None):
		self.csel.list.reload()
		self.close()

	def okbuttonClick(self):
		self["menu"].getCurrent()[1]()

	def cancelClick(self):
		self.close(False)

	def customizeColorButtons(self):
		self.session.openWithCallback(self.updateButtons, MovieListButtonConfig)

	def updateButtons(self, ret = None):
		self.csel.createHelperDics()
		self.csel.updateTags()

	def playmode_random(self):
		self.csel.setPlayMode("random")
		self.close()

	def playmode_loop(self):
		self.csel.setPlayMode("loop")
		self.close()

	def toggleParentalControl(self):
		path = os.path.realpath(self.bookmark_dir)
		path = os.path.abspath(path)
		if not path.endswith('/'):
			path = path + '/'
		protect = config.movielist.moviedirs_config.getConfigValue(path, "protect")
		if protect == 1:
			config.movielist.moviedirs_config.removeConfigValue(path, "protect")
		else:
			config.movielist.moviedirs_config.changeConfigValue(path, "protect", 1)
		config.movielist.moviedirs_config.save()
		self.csel.reloadList()
		self.close()

	def sortBy(self, newType):
		config.movielist.moviesort.value = newType
		if config.usage.movielist_folder_based_config.value:
			dir_path = config.movielist.last_videodir.value
			if newType == MovieList.SORT_RECORDED:
				config.movielist.moviedirs_config.removeConfigValue(dir_path, "sort")
			else:
				config.movielist.moviedirs_config.changeConfigValue(dir_path, "sort", newType)
			config.movielist.moviedirs_config.save()
		self.csel.setSortType(newType)
		self.csel.reloadList()
		self.csel.createHelperDics()
		self.csel.updateTags()
		self.close()

	def listType(self, newType):
		config.movielist.listtype.value = newType
		if config.usage.movielist_folder_based_config.value:
			dir_path = config.movielist.last_videodir.value
			if newType == MovieList.LISTTYPE_MINIMALVTI:
				config.movielist.moviedirs_config.removeConfigValue(dir_path, "list")
			else:
				config.movielist.moviedirs_config.changeConfigValue(dir_path, "list", newType)
			config.movielist.moviedirs_config.save()
		self.csel.setListType(newType)
		self.csel.list.redrawList()
		self.csel.list.reload()
		self.close()

	def showDescription(self, newType):
		config.movielist.description.value = newType
		self.csel.setDescriptionState(newType)
		self.csel.updateDescription()
		self.close()

	def execPlugin(self, plugin):
		plugin(session=self.session, service=self.service)

	def checkFileToDelete(self, service):
		serviceHandler = eServiceCenter.getInstance()
		offline = serviceHandler.offlineOperations(service)
		info = serviceHandler.info(service)
		name = info and info.getName(service) or _("this recording")
		result = False
		if service.flags & eServiceReference.mustDescent:
			if service.getName() != "..":
				result = True
				name = service.getPath()
		else:
			if offline is not None:
				# simulate first
				if not offline.deleteFromDisk(1):
					result = True
		if self.checkPlayState(service):
			result = False
		return (result, name)

	def getTriesEntry(self):
		return config.ParentalControl.retries.moviepin

	def exe_parental_control_func(self, ret = None):
		if ret is not None and ret and self.parental_control_fnc is not None:
			self.parental_control_fnc()
		self.parental_control_fnc = None

	def checkParentalControlCB(self, ret = None):
		if ret is not None and ret:
			parentalControlFolder.deletePinEntered(ret)
			self.start_delete()

	def delete(self):
		if config.ParentalControl.deletepinactive.value:
			if not parentalControlFolder.configInitialized:
				parentalControlFolder.getConfigValues()
			if parentalControlFolder.sessionDeletePinCached:
				self.start_delete()
			else:
				self.session.openWithCallback(
					self.checkParentalControlCB,
					PinInput, triesEntry = self.getTriesEntry(),
					pinList = [config.ParentalControl.deletepin.value],
					title = _("Please enter the correct pin code"),
					windowTitle = _("Enter pin code")
				)
		else:
			self.start_delete()

	def start_delete(self):
		if self.select_mode:
			entries = self.csel.getSelectedEntries()
			self.entries2delete = []
			if entries and len(entries):
				for service in entries:
					result, name = self.checkFileToDelete(service)
					if result:
						self.entries2delete.append(service)
				if len(self.entries2delete):
					self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do you really want to delete all selected items ?"))
		else:
			result, name = self.checkFileToDelete(self.service)
			if result == True:
				if config.usage.movielist_ask_movie_del.value:
					self.deleteConfirmed(True)
				else:
					self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do you really want to delete %s?") % (name))
			else:
				self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)

	def deleteConfirmed(self, confirmed):
		if not confirmed:
			if self.select_mode:
				self.csel.toggleSelectMode()
			return self.close()

		if self.select_mode:
			self.csel.toggleSelectMode()
			if len(self.entries2delete):
				idx = 0
				result_txt = None
				for service in self.entries2delete:
					result, result_txt = self.executeFileDelete(service)
					if not result:
						idx += 1
					else:
						self.csel["list"].removeService(service)
				self.csel["freeDiskSpace"].update()
				if idx and idx < len(self.entries2delete):
					self.session.openWithCallback(self.close, MessageBox, _("Not all items could be deleted !"), MessageBox.TYPE_ERROR)
				elif idx and idx == len(self.entries2delete):
					self.session.openWithCallback(self.close, MessageBox, result_txt, MessageBox.TYPE_ERROR)
				else:
					self.close
		else:
			service = self.service
			result, result_txt = self.executeFileDelete(service)
			if not result:
				self.session.openWithCallback(self.close, MessageBox, result_txt, MessageBox.TYPE_ERROR)
			else:
				self.csel["list"].removeService(service)
				self.csel["freeDiskSpace"].update()
				self.close()

	def executeFileDelete(self, service):
		timer = self.checkTimerState(service)
		if timer:
			timer.afterEvent = AFTEREVENT.NONE
			NavigationInstance.instance.RecordTimer.removeEntry(timer)
		
		result = False
		force = True
		result_txt = _("Delete failed!")
		if config.usage.movielist_use_trash_dir.value:
			force = False
			if self.trash_dir:
				file_path = service.getPath()
				file_path = os.path.realpath(file_path)
				if file_path.startswith(self.trash_dir + "/"):
					force = True
				else:
					self.doCopy = False
					self.doFileOperationCopyMove(self.trash_dir, service)
					result = True
			else:
				result_txt = _("Delete failed, because there is no movie trash !\nDisable movie trash in configuration to delete this item")
		if force:
			if service.flags & eServiceReference.mustDescent:
				container = eConsoleAppContainer()
				container.execute("rm -rf '%s'" % service.getPath())
				result = True
			else:
				serviceHandler = eServiceCenter.getInstance()
				offline = serviceHandler.offlineOperations(service)
				if offline is not None:
					# really delete!
					if not offline.deleteFromDisk(0):
						result = True
		return (result, result_txt)

	def deleteTrashEntry(self, service):
		result, name = self.checkFileToDelete(service)
		if result == True:
			result, result_txt = self.executeFileDelete(service)
			if not result:
				self.session.openWithCallback(self.close, MessageBox, result_txt, MessageBox.TYPE_ERROR)
			else:
				self.csel["list"].removeService(service)
		else:
			self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)

	def deleteMovieTrashEntriesConfirmed(self, res):
		if res:
			if self.select_mode:
				self.csel.toggleSelectMode()
			trash_list = self.csel.getCurrentList()
			for x in trash_list:
				path = x.getPath()
				if path.startswith(self.trash_dir + "/"):
					self.deleteTrashEntry(x)
			self.csel["freeDiskSpace"].update()
			self.close()

	def deleteMovieTrashEntries(self):
		self.session.openWithCallback(self.deleteMovieTrashEntriesConfirmed, MessageBox, _("Do you really want to delete the movie trash of this device ?"))

	def resetProgress(self):
		self.csel.resetProgress()
		if self.select_mode:
			self.csel.toggleSelectMode()
		self.close()

	def lastPlayed(self):
		self.csel.playLast()
		self.close()

	def chooseDestination(self):
		self.session.openWithCallback(
			self.gotDestination,
			MovieLocationBox,
			_("Please select the destination path..."),
			config.movielist.last_videodir.value
		)

	def gotDestination(self, res):
		if res and fileExists(res):
			if self.select_mode:
				entries = self.csel.getSelectedEntries()
				if entries and len(entries):
					for service in entries:
						self.doFileOperationCopyMove(res, service)
				self.csel.toggleSelectMode()
			elif not self.select_mode:
				self.doFileOperationCopyMove(res, self.service)
			self.csel.reloadList()
			self.close()

	def doFileOperationCopyMove(self, res, service):
		src_isDir = False
		if service.flags & eServiceReference.mustDescent:
			src_isDir = True
		src_file = str(service.getPath())
		dst_file = res
		if dst_file.endswith("/"):
			dst_file = res[:-1]
		text = _("remove")
		if self.doCopy:
			text = _("copy")
		job_manager.AddJob(FileTransferJob(src_file,dst_file, src_isDir, self.doCopy, "%s : %s" % (text, src_file)))

	def chooseLinkLocation(self, res = None, source = False):
		if source:
			self.source_link = ""
			title = _("Please select the source path...")
			callback = self.chooseLinkLocation
		elif res and not source:
			self.source_link = res
			title = _("Please select the destination path...")
			callback = self.gotLinkLocation
		else:
			return
		initDir = os.path.split(os.path.realpath(config.movielist.last_videodir.value))[0]
		if initDir != "/":
			initDir += "/"
		self.session.openWithCallback(
			callback,
			FileDirBrowser,
			title = title,
			inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/proc", "/run", "/sbin", "/share", "/sys", "/tmp", "/usr", "/var"],
			initDir = initDir,
			showDirectories = True,
			showFiles = False,
		)

	def gotLinkLocation(self, res):
		error = False
		if res:
			if fileExists(res) and fileExists(self.source_link):
				src = os.path.realpath(self.source_link)
				dest = os.path.realpath(res)
				dest = os.path.join(dest, os.path.split(src)[1])
				if not os.path.exists(dest):
					if os.path.lexists(dest): # delete dangling symlinks
						os.remove(dest)
					try:
						os.symlink(src, dest)
					except OSError:
						error = True
				else:
					self.session.open(MessageBox, _("The path %s already exists.") % (dest), type = MessageBox.TYPE_ERROR, timeout = 5)
			else:
				error = True
		if error:
			self.session.open(MessageBox, _("Creating symlink failed."), type = MessageBox.TYPE_ERROR, timeout = 5)
		self.csel.reloadList()
		self.close()

	def playSelectedEntries(self):
		self.csel.playSelectedEntries()
		self.close()

	def toggleSelectMode(self):
		self.csel.toggleSelectMode()
		self.close()

	def create_link(self):
		self.chooseLinkLocation(source = True)

	def create_bookmark(self):
		self.addBookmark(self.bookmark_dir)

	def copy(self):
		self.doCopy = True
		self.chooseDestination()

	def remove(self):
		self.doCopy = False
		self.chooseDestination()

	def openTasklist(self):
		self.session.open(TaskListScreen, self.tasklist)

	def loop_sort(self):
		sort_type = config.movielist.moviesort.value + 1
		if sort_type > 4:
			sort_type = 1
		self.sortBy(sort_type)

	def loop_listview(self):
		list_type = config.movielist.listtype.value + 1
		if list_type > 5:
			list_type = 1
		self.listType(list_type)

	def createDirCallback(self, res):
		if res:
			path = os.path.join(config.movielist.last_videodir.value, res)
			if not pathExists(path):
				if not createDir(path):
					self.session.open(MessageBox, _("Creating directory %s failed.") % (path), type = MessageBox.TYPE_ERROR, timeout = 5)
			else:
				self.session.open(MessageBox, _("The path %s already exists.") % (path), type = MessageBox.TYPE_ERROR, timeout = 5)
			self.addBookmark(path)
	
	def addBookmark(self, path):
		if pathExists(path):
			if not path.endswith('/'):
				path = path + ('/')
			if path not in config.movielist.videodirs.value:
				bookmarks = config.movielist.videodirs.value
				bookmarks.append(path)
				config.movielist.videodirs.value = bookmarks
				config.movielist.videodirs.save()
				self.csel.reloadList()
		self.close()

	def make_dir(self):
		self.session.openWithCallback(self.createDirCallback, InputBox, title = _("Please enter name of the new directory"), text = "")

	def checkPlayState(self, service):
		cur = self.session.nav.getCurrentlyPlayingServiceReference()
		if cur:
			cur = os.path.realpath(cur.getPath())
			moviename = os.path.realpath(service.getPath())
			if cur == moviename:
				return True
		return False

	def checkTimerState(self, service):
		moviename = os.path.realpath(service.getPath())
		if NavigationInstance.instance.getRecordings():
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				if timer.state == TimerEntry.StateRunning:
					if timer.justplay:
						pass
					else:
						timerfile = os.path.realpath(timer.Filename + ".ts")
						if timerfile == moviename:
							return timer
		return None


class SelectionEventInfo:
	def __init__(self):
		self["Service"] = ServiceEvent()
		self.list.connectSelChanged(self.__selectionChanged)
		self.timer = eTimer()
		self.timer.callback.append(self.updateEventInfo)
		self["Cover"] = Pixmap()
		self.onShown.append(self.__selectionChanged)

	def __selectionChanged(self):
		if self.execing and config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
			self.timer.start(100, True)

	def updateEventInfo(self):
		serviceref = self.getCurrent()
		self["Service"].newService(serviceref)

from Screens.ParentalControlSetup import ProtectedScreen
from Components.ParentalControl import parentalControlFolder

class MovieSelection(Screen, HelpableScreen, SelectionEventInfo, ProtectedScreen):
	ALLOW_SUSPEND = True
	
	def __init__(self, session, selectedmovie = None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		if config.ParentalControl.configured.value:
			ProtectedScreen.__init__(self)

		self.tags = [ ]
		if selectedmovie:
			self.movie_selected = True
			self.selected_tags = config.movielist.last_selected_tags.value
		else:
			self.movie_selected = None
			self.selected_tags = None
		self.selected_tags_ele = None

		self.movemode = False
		self.bouquet_mark_edit = False

		self.delayTimer = eTimer()
		self.delayTimer.callback.append(self.updateHDDData)

		self["waitingtext"] = Label(_("Please wait... Loading list..."))

		# create optional description border and hide immediately
		self["DescriptionBorder"] = Pixmap()
		self["DescriptionBorder"].hide()

		if not selectedmovie and config.movielist.start_videodir.value != "off":
			config.movielist.last_videodir.value = config.movielist.start_videodir.value

		if not fileExists(config.movielist.last_videodir.value):
			config.movielist.last_videodir.value = defaultMoviePath()
			config.movielist.last_videodir.save()
		self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + config.movielist.last_videodir.value)

		config.movielist.moviesort.value = config.movielist.moviedirs_config.getConfigValue(config.movielist.last_videodir.value, "sort") or config.movielist.moviesort.value
		config.movielist.listtype.value = config.movielist.moviedirs_config.getConfigValue(config.movielist.last_videodir.value, "list") or config.movielist.listtype.value

		self["list"] = MovieList(None,
			config.movielist.listtype.value,
			config.movielist.moviesort.value,
			config.movielist.description.value)

		self.list = self["list"]
		self.selectedmovie = selectedmovie

		# Need list for init
		SelectionEventInfo.__init__(self)

		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		self.long_pressed = False
		self.playmode = None
		self.getMoviePlugins()
		self.use_color_key_long = False
		self.select_mode = False
		self.parental_control_locked = False
		self.createHelperDics()
		self.updateButtonTag(setButton = False)

		self["freeDiskSpace"] = DiskInfo(config.movielist.last_videodir.value, DiskInfo.COMBINED, update=False)

		if config.usage.setup_level.index >= 2: # expert+
			self["InfobarActions"] = HelpableActionMap(self, "InfobarActions", 
				{
					"showMovies": (self.doPathSelect, _("select the movie path")),
				})

		self["MovieSelectionActions"] = HelpableActionMap(self, "MovieSelectionActions",
			{
				"contextMenu": (self.doContext, _("menu")),
				"showEventInfo": (self.showEventInformation, _("show event details")),
			})

		self["ColorActionsLong"] = HelpableActionMap(self, "ColorLongActions",
			{
				"red": (self.keyRed, self.txt_dic["key_red"][1]),
				"green": (self.keyGreen, self.txt_dic["key_green"][1]),
				"yellow": (self.keyYellow, self.txt_dic["key_yellow"][1]),
				"blue": (self.keyBlue, self.txt_dic["key_blue"][1]),
				"red_long": (self.keyRedLong, self.txt_dic["key_red_long"][1]),
				"green_long": (self.keyGreenLong, self.txt_dic["key_green_long"][1]),
				"yellow_long": (self.keyYellowLong, self.txt_dic["key_yellow_long"][1]),
				"blue_long": (self.keyBlueLong, self.txt_dic["key_blue_long"][1]),
			})

		self["ChannelUpDownActions"] = HelpableActionMap(self, "ChannelUpDownActions",
			{
				"channelUp": (self.toggleColorButtons, _("Toggle short/long key press for color keys")),
				"channelDown": (self.toggleColorButtons, _("Toggle short/long key press for color keys")),
			})

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"cancel": (self.abort, _("exit movielist")),
				"ok": (self.movieSelected, _("select movie")),
			})

		self["MyActions"] = ActionMap(["InfobarSeekActions"],
			{
				"playpauseService": self.play_selected_movie,
			}, -1)

		self.onShown.append(self.go)
		self.onLayoutFinish.append(self.saveListsize)
		self.inited = False

	def keyRedLong(self):
		self.long_pressed = True
		if self.use_color_key_long:
			self.colorAction("red", config.movielist.red_button.value, longpress = True)
		else:
			self.colorAction("red_long", config.movielist.red_long_button.value, longpress = True)

	def keyGreenLong(self):
		self.long_pressed = True
		if self.use_color_key_long:
			self.colorAction("green", config.movielist.green_button.value, longpress = True)
		else:
			self.colorAction("green_long", config.movielist.green_long_button.value, longpress = True)

	def keyYellowLong(self):
		self.long_pressed = True
		if self.use_color_key_long:
			self.colorAction("yellow", config.movielist.yellow_button.value, longpress = True)
		else:
			self.colorAction("yellow_long", config.movielist.yellow_long_button.value, longpress = True)

	def keyBlueLong(self):
		self.long_pressed = True
		if self.use_color_key_long:
			self.colorAction("blue", config.movielist.blue_button.value, longpress = True)
		else:
			self.colorAction("blue_long", config.movielist.blue_long_button.value, longpress = True)

	def keyRed(self):
		if self.use_color_key_long:
			self.colorAction("red_long", config.movielist.red_long_button.value)
		else:
			self.colorAction("red", config.movielist.red_button.value)

	def keyGreen(self):
		if self.use_color_key_long:
			self.colorAction("green_long", config.movielist.green_long_button.value)
		else:
			self.colorAction("green", config.movielist.green_button.value)

	def keyYellow(self):
		if self.use_color_key_long:
			self.colorAction("yellow_long", config.movielist.yellow_long_button.value)
		else:
			self.colorAction("yellow", config.movielist.yellow_button.value)

	def keyBlue(self):
		if self.use_color_key_long:
			self.colorAction("blue_long", config.movielist.blue_long_button.value)
		else:
			self.colorAction("blue", config.movielist.blue_button.value)

	def toggleColorButtons(self):
		if self.use_color_key_long:
			self.use_color_key_long = False
		else:
			self.use_color_key_long = True
		self.setButtonTxt()

	def isProtected(self):
		return config.ParentalControl.setuppinactive.value and config.ParentalControl.config_sections.movie_list.value

	def protectedClose_ParentalControl(self, res = None):
		self.close(None)

	def createHelperDics(self):
		self.sort_text = {   MovieList.SORT_ALPHANUMERIC: " (A - Z)",
				MovieList.SORT_RECORDED: " (00:00-23:59)",
				MovieList.SORT_ALPHANUMERIC_INVERS: " (Z - A)",
				MovieList.SORT_RECORDED_INVERS: " (23:59-00:00)",
			    }
		
		self.fnc_dic = {}
		for key in fnc_choices:
			self.fnc_dic[key[0]] = key[1]
		
		self.button_dic = {
				"key_red": (config.movielist.red_button.value, config.movielist.red_bookmark_friendly_name.value),
				"key_green": (config.movielist.green_button.value, config.movielist.green_bookmark_friendly_name.value),
				"key_yellow": (config.movielist.yellow_button.value, config.movielist.yellow_bookmark_friendly_name.value),
				"key_blue": (config.movielist.blue_button.value, config.movielist.blue_bookmark_friendly_name.value),
				"key_red_long": (config.movielist.red_long_button.value, config.movielist.red_long_bookmark_friendly_name.value),
				"key_green_long": (config.movielist.green_long_button.value, config.movielist.green_long_bookmark_friendly_name.value),
				"key_yellow_long": (config.movielist.yellow_long_button.value, config.movielist.yellow_long_bookmark_friendly_name.value),
				"key_blue_long": (config.movielist.blue_long_button.value, config.movielist.blue_long_bookmark_friendly_name.value),
			}

	def updateButtonTag(self, setButton = True):
		self.txt_dic = {}
		for k,v in self.button_dic.iteritems():
			txt = ""
			hlp_txt = None
			if v[0] in self.fnc_dic:
				txt = _(self.fnc_dic[v[0]])
				if v[0] == "bookmark":
					txt = v[1]
					hlp_txt = _("Bookmark") + ": %s" % txt
				elif v[0] == "sort":
					txt += self.sort_text[config.movielist.moviesort.value]
				elif v[0] == "trashdir":
					if self.get_current_trash_dir() == config.movielist.last_videodir.value:
						txt = _("clear movie trash")
				elif v[0] == "showdir":
					if config.usage.movielist_show_dir.value:
						txt += " (%s)" % _("on")
					else:
						txt += " (%s)" % _("off")
				elif v[0] == "selectmode":
					hlp_txt = _("toggle select mode")
					if self.select_mode:
						txt = _("Select mode") + " (" + _("on") + ")"
					else:
						txt = _("Select mode") + " (" + _("off") + ")"
				elif v[0] == "showfirsttag" and self.tags:
					txt = config.movielist.first_tags.value
				elif v[0] == "showsecondtag" and self.tags:
					txt = config.movielist.second_tags.value
				elif v[0] == "showtagmenu" and self.tags:
					txt = _("Tags")+"..."
				elif v[0] == "off":
					txt = ""
					hlp_txt = _("without function")
			if not hlp_txt:
				hlp_txt = txt
			self.txt_dic[k] = (txt, hlp_txt)
		if setButton:
			self.setButtonTxt()

	def setButtonTxt(self):
		long_key = ""
		if self.use_color_key_long:
			long_key = "_long"
		buttons = ("key_red", "key_green", "key_yellow", "key_blue")
		for button in buttons:
			self[button].text = self.txt_dic[button + long_key][0]

	def updateDescription(self):
		if config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
			self["DescriptionBorder"].show()
			self["list"].instance.resize(eSize(self.listWidth, self.listHeight-self["DescriptionBorder"].instance.size().height()))
		else:
			self["Service"].newService(None)
			self["DescriptionBorder"].hide()
			self["list"].instance.resize(eSize(self.listWidth, self.listHeight))

	def showEventInformation(self):
		from Screens.EventView import EventViewSimple, EventViewMovieEvent
		from ServiceReference import ServiceReference
		evt = self["list"].getCurrentEvent()
		if evt:
			self.session.open(EventViewSimple, evt, ServiceReference(self.getCurrent()))
		else:
			current = self.getCurrent()
			if current is not None and not current.flags & eServiceReference.mustDescent:
				dur = self["list"].getCurrentDuration()
				name, ext_desc = getExtendedMovieDescription(current)
				self.session.open(EventViewMovieEvent, name, ext_desc, dur)

	def go(self):
		if not self.inited:
		# ouch. this should redraw our "Please wait..."-text.
		# this is of course not the right way to do this.
			self.delayTimer.start(10, 1)
			self.inited=True

	def saveListsize(self):
			listsize = self["list"].instance.size()
			self.listWidth = listsize.width()
			self.listHeight = listsize.height()
			self.updateDescription()

	def updateHDDData(self):
		selected_service = self.selectedmovie
		if not self.movie_selected and config.movielist.start_videodir.value == "last video":
			res, service = self.getLast()
			if res:
				selected_service = service
 		self.reloadList(selected_service)
		self["waitingtext"].visible = False

	def moveTo(self):
		self["list"].moveTo(self.selectedmovie)

	def getCurrent(self):
		return self["list"].getCurrent()

	def getCurrentPlayList(self):
		return self["list"].getCurrentPlayList()
	
	def getCurrentList(self):
		return self["list"].getCurrentList()

	def movieSelected(self):
		if self.select_mode:
			current = self.getCurrent()
			if current is not None:
				if current.flags & eServiceReference.mustDescent:
					filepath = current.getPath()
					self.gotFilename(filepath)
				else:
					if current in self["list"].selected_entries:
						self["list"].selected_entries.remove(current)
					else:
						self["list"].selected_entries.append(current)
					idx = self["list"].getCurrentIndex() + 1
					list_len = len(self["list"])
					if idx >= list_len:
						idx = list_len - 1
						self["list"].reload(self.current_ref, self.selected_tags)
					else:
						self["list"].moveToIndex(idx)
		else:
			playlist = self.getCurrentPlayList()
			current = self.getCurrent()
			playmode = self.playmode
			self.playmode = None
			if current is not None:
				filepath = current.getPath()
				if current.flags & eServiceReference.mustDescent:
					self.gotFilename(filepath)
				else:
					possible_path = ("VIDEO_TS/", "video_ts/", "VIDEO_TS.IFO", "video_ts.ifo")
					for mypath in possible_path:
						if os.path.exists(os.path.join(filepath, mypath)):
							if self.startDVDPlayer(filepath):
								return
					if filepath.lower().endswith('.iso'):
						if self.startDVDPlayer(filepath):
							return
					else:
						self.saveconfig()
						if len(playlist):
							current = (current, playlist, playmode)
						self.close(current)

	def getTriesEntry(self):
		return config.ParentalControl.retries.moviepin

	def exe_parental_control_func(self, ret = None):
		if ret is not None and ret and self.parental_control_fnc is not None:
			self.parental_control_fnc()
		self.parental_control_fnc = None

	def checkParentalControlCB(self, ret = None):
		self.parental_control_locked = False
		if ret is not None and ret:
			parentalControlFolder.moviePinEntered(ret)
			self.exe_parental_control_func(ret)

	def checkParentalControl(self, fnc):
		self.parental_control_fnc = fnc
		if not parentalControlFolder.configInitialized:
			parentalControlFolder.getConfigValues()
		if parentalControlFolder.sessionPinCached:
			self.exe_parental_control_func(True)
		else:
			self.parental_control_locked = True
			self.session.openWithCallback(
				self.checkParentalControlCB,
				PinInput, triesEntry = self.getTriesEntry(),
				pinList = [config.ParentalControl.moviepin.value],
				title = _("Please enter the correct pin code"),
				windowTitle = _("Enter pin code")
			)

	def playSelectedEntries(self):
		if self.select_mode:
			playmode = self.playmode
			self.playmode = None
			entries = self.getSelectedEntries()
			playlist = []
			if entries and len(entries):
				for entry in entries:
					filepath = entry.getPath()
					if not filepath.lower().endswith('.iso'):
						playlist.append(entry)
			self.saveconfig()
			if len(playlist):
				self.toggleSelectMode()
				current = (playlist[0], playlist, playmode)
				self.close(current)

	def play_selected_movie(self):
		if self.select_mode:
			self.playSelectedEntries()
		else:
			self.movieSelected()

	def startDVDPlayer(self, path):
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyo"):
			from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
			if path.endswith('/'):
				path = path[:-1]
			self.session.open(DVDPlayer, dvd_filelist=[path], dvd_isVTI= True)
			return True
		else:
			print "[MovieList] no DVDPlayer plugin installed"

	def doContext(self):
		current = self.getCurrent()
		if current is not None:
			self.session.open(MovieContextMenu, self, current)

	def abort(self):
		self.saveconfig()
		self.close(None)

	def saveconfig(self):
		config.movielist.last_selected_tags.value = self.selected_tags
		config.movielist.moviesort.save()
		config.movielist.listtype.save()
		config.movielist.description.save()

	def getTagDescription(self, tag):
		# TODO: access the tag database
		return tag

	def updateTags(self):
		# get a list of tags available in this list
		self.tags = list(self["list"].tags)
		self.updateButtonTag()

	def setListType(self, type):
		self["list"].setListType(type)

	def setDescriptionState(self, val):
		self["list"].setDescriptionState(val)

	def setSortType(self, type):
		self["list"].setSortType(type)

	def resetProgress(self):
		if self.select_mode:
			entries = self.getSelectedEntries()
			if entries and len(entries):
				for entry in entries:
					self["list"].resetProgress(entry)
		else:
			current = self.getCurrent()
			if current is not None:
				self["list"].resetProgress(current)

	def reloadList(self, sel = None, home = False):
		if not fileExists(config.movielist.last_videodir.value):
			path = defaultMoviePath()
			config.movielist.last_videodir.value = path
			config.movielist.last_videodir.save()
			self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + path)
			self["freeDiskSpace"].path = path
			self.folder_based_config(path)
		if sel is None:
			sel = self.getCurrent()
		if config.ParentalControl.moviepinactive.value:
			if not self.parental_control_locked:
				path = os.path.realpath(self.current_ref.getPath())
				path = os.path.abspath(path)
				if not path.endswith('/'):
					path = path + '/'
				protect = config.movielist.moviedirs_config.getConfigValue(path, "protect")
				if protect == 1:
					fnc = boundFunction(self.finish_reload_list, sel, home)
					self.checkParentalControl(fnc)
				else:
					self.finish_reload_list(sel, home)
			else:
				return
		else:
			self.finish_reload_list(sel, home)

	def finish_reload_list(self, sel, home):
		self["list"].reload(self.current_ref, self.selected_tags)
		self.setMovieListTitle()
		if not (sel and self["list"].moveTo(sel)):
			if home:
				self["list"].moveToIndex(0)
		self.updateTags()
		self["freeDiskSpace"].update()

	def setMovieListTitle(self):
		if self.select_mode:
			title = _("Select mode") + ": "
		else:
			title = _("Recorded files") + ": "
		if config.usage.setup_level.index >= 2: # expert+
			title += "  " + config.movielist.last_videodir.value
		if self.selected_tags is not None:
			title += " - " + ','.join(self.selected_tags)
		self.setTitle(title)

	def doPathSelect(self):
		self.session.openWithCallback(
			self.gotFilename,
			MovieLocationBox,
			_("Please select the movie path..."),
			config.movielist.last_videodir.value
		)

	def gotFilename(self, res):
		if res is not None and res is not config.movielist.last_videodir.value:
			if fileExists(res):
				current = self.getCurrent()
				parentDir = None
				if current is not None:
					if current.flags & eServiceReference.mustDescent:
						if current.getName() == "..":
							lastDir = config.movielist.last_videodir.value
							parentDir = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + lastDir)
				config.movielist.last_videodir.value = res
				config.movielist.last_videodir.save()
				self.folder_based_config(res)
				self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + res)
				self["freeDiskSpace"].path = res
				if parentDir is not None:
					self.reloadList(home = True, sel = parentDir)
				else:
					self.reloadList(home = True)
			else:
				self.session.open(
					MessageBox,
					_("Directory %s nonexistent.") % (res),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
					)

	def showAll(self):
		self.selected_tags_ele = None
		self.selected_tags = None
		self.reloadList(home = True)

	def showTagsN(self, tagele):
		if not self.tags:
			self.showTagWarning()
			self.long_pressed = False
		elif not tagele or (self.selected_tags and tagele.value in self.selected_tags) or not tagele.value in self.tags:
			self.showTagsMenu(tagele)
			self.long_pressed = False
		else:
			self.selected_tags_ele = tagele
			self.selected_tags = set([tagele.value])
			self.reloadList(home = True)

	def showTagsFirst(self):
		self.showTagsN(config.movielist.first_tags)

	def showTagsSecond(self):
		self.showTagsN(config.movielist.second_tags)

	def showTagsSelect(self):
		self.showTagsN(None)

	def tagChosen(self, tag):
		if tag is not None:
			self.selected_tags = set([tag[0]])
			if self.selected_tags_ele:
				self.selected_tags_ele.value = tag[0]
				self.selected_tags_ele.save()
			self.reloadList(home = True)

	def showTagsMenu(self, tagele):
		self.selected_tags_ele = tagele
		list = [(tag, self.getTagDescription(tag)) for tag in self.tags ]
		self.session.openWithCallback(self.tagChosen, ChoiceBox, title=_("Please select tag to filter..."), list = list)

	def showTagWarning(self):
		self.session.open(MessageBox, _("No tags are set on these movies."), MessageBox.TYPE_ERROR)

	def showDir(self):
		if config.usage.movielist_show_dir.value:
			config.usage.movielist_show_dir.value = False
		else:
			config.usage.movielist_show_dir.value = True
		config.usage.movielist_show_dir.save()
		self. reloadList()
		self.updateTags()

	def getLast(self):
		service = eServiceReference(config.usage.movielist_last_played_movie.value)
		serviceHandler = eServiceCenter.getInstance()
		file_path = service.getPath()
		if file_path and fileExists(file_path):
			movie_dir = os.path.split(file_path)[0] + "/"
			if config.movielist.last_videodir.value != movie_dir:
				config.movielist.last_videodir.value = movie_dir
				config.movielist.last_videodir.save()
				self.gotFilename(movie_dir)
			return (True, service)
		return (False, None)

	def selectLast(self):
		res, service = self.getLast()
		if res:
			self["list"].moveTo(service)
			return True
		return False

	def playLast(self):
		if self.selectLast():
			self.movieSelected()

	def setPlayMode(self, playmode):
		current = self.getCurrent()
		if current:
			if not current.flags & eServiceReference.mustDescent:
				self.playmode = playmode
				self.movieSelected()

	def toggleSelectMode(self):
		entries = self["list"].getSelectedEntries()
		self["list"].selected_entries = []
		if self.select_mode:
			self["list"].reload()
			self.select_mode = False
		else:
			self.select_mode = True
		self.setMovieListTitle()
		self.updateButtonTag()

	def getSelectedEntries(self):
		return self["list"].getSelectedEntries()

	def getSelectMode(self):
		return self.select_mode

	def getMoviePlugins(self):
		self.movie_plugins = {}
		for p in plugins.getPlugins([PluginDescriptor.WHERE_MOVIELIST]):
			id = "p_" + p.name.replace(' ','_')
			self.movie_plugins[id] = p
			desc = p.description
			if (id, desc) not in fnc_choices:
				fnc_choices.append((id, desc))

	def get_current_trash_dir(self):
		trash_dir = getTrashDir(config.movielist.last_videodir.value)
		if trash_dir:
			if not trash_dir.endswith("/"):
				trash_dir += "/"
			return trash_dir
		return None

	def selectTrashDir(self):
		trash_dir = self.get_current_trash_dir()
		if trash_dir:
			if  trash_dir == config.movielist.last_videodir.value:
				current = self.getCurrent()
				if current:
					MovieContextMenu(self.session, self, current).deleteMovieTrashEntries()
			else:
				self.gotFilename(trash_dir)
		else:
			self.session.open(MessageBox, _("Movie trash function is not available at this memory device !"), MessageBox.TYPE_ERROR)

	def folder_based_config(self, dir_path):
		if config.usage.movielist_folder_based_config.value:
			old_sort = config.movielist.moviesort.value
			config.movielist.moviesort.value = config.movielist.moviedirs_config.getConfigValue(dir_path, "sort") or MovieList.SORT_RECORDED
			if old_sort != config.movielist.moviesort.value:
				self["list"].setSortType(config.movielist.moviesort.value)
			old_list = config.movielist.listtype.value
			config.movielist.listtype.value = config.movielist.moviedirs_config.getConfigValue(dir_path, "list") or MovieList.LISTTYPE_MINIMALVTI
			if old_list != config.movielist.listtype.value:
				self["list"].setListType(config.movielist.listtype.value)
				self["list"].redrawList()

	def colorAction(self, color, action, longpress = False):
		if not longpress and self.long_pressed:
			self.long_pressed = False
			return
		current = self.getCurrent()
		if action == "bookmark":
			if color == "red":
				self.gotFilename(config.movielist.red_bookmark.value)
			elif color == "green":
				self.gotFilename(config.movielist.green_bookmark.value)
			elif color == "yellow":
				self.gotFilename(config.movielist.yellow_bookmark.value)
			elif color == "blue":
				self.gotFilename(config.movielist.blue_bookmark.value)
			elif color == "red_long":
				self.gotFilename(config.movielist.red_long_bookmark.value)
			elif color == "green_long":
				self.gotFilename(config.movielist.green_long_bookmark.value)
			elif color == "yellow_long":
				self.gotFilename(config.movielist.yellow_long_bookmark.value)
			elif color == "blue_long":
				self.gotFilename(config.movielist.blue_long_bookmark.value)
		elif current:
			if action == "rm":
				MovieContextMenu(self.session, self, current).delete()
				if not config.usage.movielist_ask_movie_del.value:
					self.long_pressed = False
			elif action == "cp":
				MovieContextMenu(self.session, self, current).copy()
				self.long_pressed = False
			elif action == "mv":
				MovieContextMenu(self.session, self, current).remove()
				self.long_pressed = False
			elif action == "sort":
				MovieContextMenu(self.session, self, current).loop_sort()
			elif action == "looplistview":
				MovieContextMenu(self.session, self, current).loop_listview()
			elif action == "mkdir":
				MovieContextMenu(self.session, self, current).make_dir()
				self.long_pressed = False
			elif action == "opentasklist":
				MovieContextMenu(self.session, self, current).openTasklist()
				self.long_pressed = False
			elif action == "configuration":
				MovieContextMenu(self.session, self, current).openMovieListOption()
				self.long_pressed = False
			elif action == "colorkeys":
				MovieContextMenu(self.session, self, current).customizeColorButtons()
				self.long_pressed = False
			elif action == "symlink" and not self.select_mode:
				MovieContextMenu(self.session, self, current).create_link()
				self.long_pressed = False
			elif action in self.movie_plugins and not self.select_mode:
				MovieContextMenu(self.session, self, current).execPlugin(self.movie_plugins[action])
				self.long_pressed = False
			elif action == "contextmenu":
				self.doContext()
				self.long_pressed = False
			elif action == "playmode_random":
				self.setPlayMode("random")
			elif action == "playmode_loop":
				self.setPlayMode("loop")
			elif action == "playlast" and not self.select_mode:
				self.playLast()
			elif action == "selectmode":
				self.toggleSelectMode()
			elif action == "parentalcontrol":
				MovieContextMenu(self.session, self, current).toggleParentalControl()
				self.long_pressed = False
			elif action == "trashdir":
				self.selectTrashDir()
		if action == "selectbookmark":
			self.doPathSelect()
			self.long_pressed = False
		elif action == "showall":
			self.showAll()
		elif action == "showfirsttag":
			self.showTagsFirst()
		elif action == "showsecondtag":
			self.showTagsSecond()
		elif action == "showtagmenu":
			self.showTagsSelect()
		elif action == "showdir":
			self.showDir()
