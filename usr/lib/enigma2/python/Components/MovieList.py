from GUIComponent import GUIComponent
from Tools.FuzzyDate import FuzzyTime
from Tools.FindPicon import findPicon
from Tools.Bytes2Human import bytes2human
from ServiceReference import ServiceReference
from Components.MultiContent import MultiContentEntryText, MultiContentEntryProgress, MultiContentEntryPixmapAlphaTest
from Components.config import config
from skin import parseAvailableSkinColor, parseColor
import skin
from enigma import eListboxPythonMultiContent, eListbox, gFont, iServiceInformation, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, BT_FIXRATIO, BT_SCALE, eServiceReference, eServiceCenter

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, fileExists, SCOPE_CURRENT_SKIN
import os

from datetime import datetime
import NavigationInstance
from timer import TimerEntry

import struct

MEDIAFILES_MOVIE = ("ts", "avi", "divx", "mpg", "mpeg", "mkv", "mp4", "mov", "iso")
MEDIAFILES_MUSIC = ("mp3", "m4a", "mp2", "wav", "ogg", "flac")

class MovieList(GUIComponent):
	SORT_ALPHANUMERIC = 1
	SORT_ALPHANUMERIC_INVERS = 2
	SORT_RECORDED = 3
	SORT_RECORDED_INVERS = 4

	LISTTYPE_ORIGINAL = 1
	LISTTYPE_COMPACT_DESCRIPTION = 2
	LISTTYPE_COMPACT = 3
	LISTTYPE_MINIMAL = 4
	LISTTYPE_MINIMALVTI = 5

	HIDE_DESCRIPTION = 1
	SHOW_DESCRIPTION = 2

	def __init__(self, root, list_type=None, sort_type=None, descr_state=None):
		GUIComponent.__init__(self)
		self.list_type = list_type or self.LISTTYPE_ORIGINAL
		self.descr_state = descr_state or self.HIDE_DESCRIPTION
		self.sort_type = sort_type or self.SORT_RECORDED

		self.selected_entries = []

		self.getMovieListConfig()

		self.l = eListboxPythonMultiContent()
		self.tags = set()
		
		if root is not None:
			self.reload(root)
		
		self.redrawList()
		self.l.setBuildFunc(self.buildMovieListEntry)
		
		self.onSelectionChanged = [ ]

		self.folder_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_folder.png"))
		self.symlink_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_link.png"))
		self.music_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/music.png"))
		self.movie_new_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_new.png"))
		self.movie_seen_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_seen.png"))
		self.movie_start_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_start.png"))
		self.movie_rec_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_rec.png"))
		self.movie_dvd_icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_dvd.png"))
		self.movie_selected = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/movie_select.png"))

		self.UnwatchedColor = parseAvailableSkinColor("foreground") or 0xffffff
		self.WatchingColor = parseAvailableSkinColor("yellow") or 0xbab329
		self.FinishedColor = parseAvailableSkinColor("green") or 0x389416
		self.RecordingColor = parseAvailableSkinColor("red") or 0xf23d21
		self.SelectedColor = parseAvailableSkinColor("orange") or 0xffa500

	def applySkin(self, desktop, parent):
		attribs = []
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "UnwatchedColor":
					self.UnwatchedColor = parseColor(value).argb()
				elif attrib == "WatchingColor":
					self.WatchingColor = parseColor(value).argb()
				elif attrib == "FinishedColor":
					self.FinishedColor = parseColor(value).argb()
				elif attrib == "RecordingColor":
					self.RecordingColor = parseColor(value).argb()
				elif attrib == "SelectedColor":
					self.SelectedColor = parseColor(value).argb()
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return GUIComponent.applySkin(self, desktop, parent)

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def setListType(self, type):
		self.list_type = type

	def setDescriptionState(self, val):
		self.descr_state = val

	def setSortType(self, type):
		self.sort_type = type

	def getMovieListConfig(self):
		self.show_dir = config.usage.movielist_show_dir.value
		self.show_icon = config.usage.movielist_show_icon.value
		self.show_progress = config.usage.movielist_show_progress.value
		self.progress_seen = config.usage.movielist_progress_seen.value
		self.colorized = config.usage.movielist_show_color.value
		self.show_picon = config.usage.movielist_show_picon.value
		self.only_day = config.usage.movielist_only_day.value
		self.duration_in_min = config.usage.movielist_duration_in_min.value
		self.show_duration = config.usage.movielist_show_duration.value
		self.show_channel_info = config.usage.movielist_show_channel_info.value
		self.show_recording_date = config.usage.movielist_show_recording_date.value
		self.show_file_size = config.usage.movielist_show_file_size.value
		self.show_last_stop_time = config.usage.movielist_show_last_stop_time.value
		self.show_trash_dir = config.usage.movielist_show_trash_dir.value

	def redrawList(self):
		if self.list_type == MovieList.LISTTYPE_ORIGINAL:
			font, size = skin.parameters.get("MovieListOriginalFont1", ('Regular', 20))
			self.l.setFont(0, gFont(font, size))
			font, size = skin.parameters.get("MovieListOriginalFont2", ('Regular', 18))
			self.l.setFont(1, gFont(font, size))
			font, size = skin.parameters.get("MovieListOriginalFont3", ('Regular', 16))
			self.l.setFont(2, gFont(font, size))
			self.l.setItemHeight(int(skin.parameters.get("MovieListOriginalItemHeight", (75,))[0]))
		elif self.list_type == MovieList.LISTTYPE_COMPACT_DESCRIPTION or self.list_type == MovieList.LISTTYPE_COMPACT:
			font, size = skin.parameters.get("MovieListCompactFont1", ('Regular', 20))
			self.l.setFont(0, gFont(font, size))
			font, size = skin.parameters.get("MovieListCompactFont2", ('Regular', 14))
			self.l.setFont(1, gFont(font, size))
			self.l.setItemHeight(int(skin.parameters.get("MovieListCompactItemHeight", (43,))[0]))
		elif self.list_type == MovieList.LISTTYPE_MINIMALVTI:
			font, size = skin.parameters.get("MovieListMinimalFont1", ('Regular', 22))
			self.l.setFont(0, gFont(font, size))
			font, size = skin.parameters.get("MovieListMinimalFont2", ('Regular', 20))
			self.l.setFont(1, gFont(font, size))
			self.l.setItemHeight(int(skin.parameters.get("MovieListMinimalItemHeight", (30,))[0]))
		else:
			font, size = skin.parameters.get("MovieListFont1", ('Regular', 20))
			self.l.setFont(0, gFont(font, size))
			font, size = skin.parameters.get("MovieListFont2", ('Regular', 16))
			self.l.setFont(1, gFont(font, size))
			self.l.setItemHeight(int(skin.parameters.get("MovieListItemHeight", (25,))[0]))

	def getMovieLen(self, moviename):
		if fileExists(moviename + ".cuts"):
			try:
				f = open(moviename + ".cuts", "rb")
				packed = f.read()
				f.close()
				while len(packed) > 0:
					packedCue = packed[:12]
					packed = packed[12:]
					cue = struct.unpack('>QI', packedCue)
					if cue[1] == 5:
						movie_len = cue[0]/90000
						return movie_len
			except Exception, ex:
				print "[MOVIELIST] failure at getting movie length from cut list"
		return -1

	def getProgress(self, moviename, movie_len):
		cut_list = []
		if fileExists(moviename + ".cuts"):
			try:
				f = open(moviename + ".cuts", "rb")
				packed = f.read()
				f.close()
				
				while len(packed) > 0:
					packedCue = packed[:12]
					packed = packed[12:]
					cue = struct.unpack('>QI', packedCue)
					cut_list.append(cue)
			except Exception, ex:
				print "[MOVIELIST] failure at downloading cut list"

		last_end_point = None

		if len(cut_list):
			for (pts, what) in cut_list:
				if what == 3:
					last_end_point = pts/90000 # in seconds

		try:   # we have to check if movie_len is an integer, if not set play_progress to 0 and deactivate progress view
			movie_len = int(movie_len)
		except ValueError:
			play_progress = 0
			movie_len = -1

		if movie_len > 0 and last_end_point is not None:
			play_progress = (last_end_point*100) / movie_len
		else:
			play_progress = 0

		if play_progress > 100:
			play_progress = 100
		return (play_progress)

	def resetProgress(self, service):
		if service is not None:
			moviename = os.path.realpath(service.getPath())
			cut_list = ''
			if fileExists(moviename + ".cuts"):
				try:
					f = open(moviename + ".cuts", "rb")
					packed = f.read()
					f.close()
					while len(packed) > 0:
						packedCue = packed[:12]
						packed = packed[12:]
						cue = struct.unpack('>QI', packedCue)
						if cue[1] != 3:
							cut_list += struct.pack('>QI', cue[0], cue[1])
					if len(cut_list) > 0:
						f = open(moviename + ".cuts", "wb")
						f.write(cut_list)
						f.close()
					else:  # if there is only cue type 3 we have to delete whole cuts file
						os.remove(moviename + ".cuts")
				except Exception, ex:
					print "[MOVIELIST] failure at editing cut list"


	def buildMovieListEntry(self, serviceref, info, begin, len):

		width = self.l.getItemSize().width()

		is_dvd = None
		filepath = os.path.realpath(serviceref.getPath())
		possible_path = ("VIDEO_TS", "video_ts", "VIDEO_TS.IFO", "video_ts.ifo")
		for mypath in possible_path:
			if os.path.exists(os.path.join(filepath, mypath)):
				is_dvd = True
				break

		if self.show_dir:
			if serviceref.flags & eServiceReference.mustDescent:
				res = [ None ]
				if self.show_icon:
					if os.path.islink(serviceref.getPath().rstrip('/')):
						png = self.symlink_icon
					else:
						png = self.folder_icon
					
					x,y,w,h = skin.parameters.get("MovieListDirIcon", (0,2,20,20))
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, png))
					x,y,w,h = skin.parameters.get("MovieListDirectoryIcon", (25,0,width - 40,30))
					res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 0, flags = RT_HALIGN_LEFT, text=serviceref.getName()))
											
				else:
					x,y,w,h = skin.parameters.get("MovieListDirectoryNoIcon", (0,0,width - 182,30))
					res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 0, flags = RT_HALIGN_LEFT, text=serviceref.getName()))
				return res
		else:
			if serviceref.flags & eServiceReference.mustDescent:
				return None

		is_music = False
		if self.show_icon:
			filetype = serviceref.toString().split('.')
			filetype = filetype[-1].lower()
			if filetype == "iso":
				png = self.movie_dvd_icon
			elif filetype in MEDIAFILES_MOVIE:
				png = self.movie_new_icon
			elif filetype in MEDIAFILES_MUSIC:
				png = self.music_icon
				is_music = True
			elif is_dvd == True:
				png = self.movie_dvd_icon
			else:
				png = None

		moviename = os.path.realpath(serviceref.getPath())
		if info is not None:
			if len <= 0: #recalc len when not already done
				cur_idx = self.l.getCurrentSelectionIndex()
				x = self.list[cur_idx]
				if config.usage.load_length_of_movies_in_moviellist.value:
					len = x[1].getLength(x[0]) #recalc the movie length...
					if len < 0:
						len = self.getMovieLen(moviename)
				else:
					len = 0 #dont recalc movielist to speedup loading the list
				self.list[cur_idx] = (x[0], x[1], x[2], len) #update entry in list... so next time we don't need to recalc
		
		if len > 0:
			clean_len = len
			if self.duration_in_min:
				len = "%d min" % (len / 60)
			else:
				len = "%d:%02d" % (len / 60, len % 60)
		else:
			len = ""
			clean_len = ""

		if self.show_progress != "progress_off":
			last_end_point = self.getProgress(moviename, clean_len)
			progress_string = str(last_end_point) + "% "
		else:
			last_end_point = 0

		if self.show_last_stop_time and clean_len != "":
			if self.show_progress == "progress_off":
				last_end_point = self.getProgress(moviename, clean_len)
			last_end = (last_end_point * clean_len) / 100
			if self.duration_in_min:
				len = "%d / %d min" % (last_end/60, clean_len / 60)
			else:
				len = "%d:%02d / %d:%02d" % (last_end / 60, last_end % 60, clean_len / 60, clean_len % 60)

		if self.show_file_size and not (serviceref.flags & eServiceReference.mustDescent):
			f = os.path.realpath(serviceref.getPath())
			try:
				stat = os.stat(f)
			except OSError:
				stat = None
			f_size = "--"
			if stat:
				f_size = bytes2human(stat.st_size, 1)

		# check if we are executing a timer (code from TimerEntry.py TimerList.py)
		is_recording = False 
		if NavigationInstance.instance.getRecordings():
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				if timer.state == TimerEntry.StateRunning:
					if timer.justplay:
						pass
					else:
						timerfile = os.path.realpath(timer.Filename + ".ts")
						if timerfile == moviename:
							is_recording = True

		res = [ None ]

		is_selected = False
		if serviceref in self.selected_entries:
			is_selected = True
		# set icons depending of current playstate
		if self.show_icon:
			if is_recording == True:
				png = self.movie_rec_icon
			elif last_end_point > self.progress_seen:
				png = self.movie_seen_icon
			elif last_end_point > 1:
				png = self.movie_start_icon
			if is_selected:
				png = self.movie_selected
		color = None
		if self.colorized:
			if is_recording == True:
				color = self.RecordingColor
			elif last_end_point > self.progress_seen:
				color = self.FinishedColor
			elif last_end_point > 1:
				color = self.WatchingColor
			else:
				color = self.UnwatchedColor

		if is_selected:
			color = self.SelectedColor

		if info is not None:
			txt = info.getName(serviceref)
			name, ext = os.path.splitext(txt)
			ext = ext.lstrip('.')
			if ext in MEDIAFILES_MOVIE or ext in MEDIAFILES_MUSIC:
				txt = name.replace("_", " ")
			service = ServiceReference(info.getInfoString(serviceref, iServiceInformation.sServiceref))
			description = info.getInfoString(serviceref, iServiceInformation.sDescription)
			tags = info.getInfoString(serviceref, iServiceInformation.sTags)

		begin_string = ""
		if begin > 0:
			if is_recording == True:
				begin_string = _("recording...")
				if self.only_day:
					begin_string = _("REC")
			else:
				if self.list_type != MovieList.LISTTYPE_MINIMALVTI:
					t = FuzzyTime(begin)
					begin_string = t[0] + ", " + t[1]
				else:
					d = datetime.fromtimestamp(begin)
					if self.only_day:
						begin_string = d.strftime("%d.%m.%y")
					else:
						begin_string = d.strftime("%d.%m.%y-%H:%M")

		if last_end_point == None:
			last_end_point = 0

		# begin offset calculation for icons and progress 
		offset = 0
		if self.show_icon:
			offset = skin.parameters.get("MovieListIconXOffset", (25,))[0]

		extra_y_offset = 0
		if self.list_type == MovieList.LISTTYPE_MINIMALVTI:
			extra_y_offset = skin.parameters.get("MovieListProgressBarXtraYOffsetVTIStyle", (2,))[0]

		if ( self.show_progress == "progress_percent" or self.show_progress == "progress_bar" ) and is_music == False:
			if self.show_progress == "progress_bar":
				x,y,w,h = skin.parameters.get("MovieListProgress", (0, extra_y_offset + 7,60,10))
				b = skin.parameters.get("MovieListProgressBorder", (2,))[0]
				res.append(MultiContentEntryProgress(pos=(offset + x, y), size = (w,h), percent = last_end_point, borderWidth = b, foreColor = color))	
			elif self.show_progress == "progress_percent":
				x,y,w,h = skin.parameters.get("MovieListProgressPercent", (0,0,60,23))
				res.append(MultiContentEntryText(pos=(offset + x, y), size=(w, h), font = 0, flags = RT_HALIGN_LEFT, text=progress_string, color = color))
			offset += w + 4

		if self.show_icon:
			x,y,w,h = skin.parameters.get("MovieListIcon", (0,3,20,20))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, png))

		duration_size = 0
		if self.show_duration:
			x, y, z = skin.parameters.get("MovieListDurationSize", (90, 150, 130))
			duration_size = x
			if self.show_last_stop_time:
				duration_size = y
				if self.duration_in_min:
					duration_size = z
		if self.list_type == MovieList.LISTTYPE_ORIGINAL:
			x,y,w,h = skin.parameters.get("MovieListOriginalTitle", (0, 0, width - 182, 30))
			res.append(MultiContentEntryText(pos=(offset+x, y), size=(w - offset, h), font = 0, flags = RT_HALIGN_LEFT, color = color, text=txt))
			if self.tags:
				x,y,w,h = skin.parameters.get("MovieListOriginalTags", (width - 180,0,180,30))
				res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 2, flags = RT_HALIGN_RIGHT, text = tags))
				if service is not None:
					x,y,w,h = skin.parameters.get("MovieListOriginalServiceTags", (200, 50, 200, 30))
					res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))
			else:
				if service is not None:
					x,y,w,h = skin.parameters.get("MovieListOriginalServiceTags", (width - 180, 0, 180, 30))
					res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 2, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))
			x,y,w,h = skin.parameters.get("MovieListOriginalDescription", (0, 30, width, 20))
			res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=1, flags=RT_HALIGN_LEFT, text=description))
			x,y,w,h = skin.parameters.get("MovieListOriginalBegin", (0,50, 200, 20))
			res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=1, flags=RT_HALIGN_LEFT, text=begin_string))
			x,y,w,h = skin.parameters.get("MovieListOriginalLength", (width + 2, 50, 0, 20))
			res.append(MultiContentEntryText(pos=(x - duration_size, y), size=(duration_size + w, h), font=1, flags=RT_HALIGN_RIGHT, text=len))
		elif self.list_type == MovieList.LISTTYPE_COMPACT_DESCRIPTION:
			x,y,w,h = skin.parameters.get("MovieListCompactDescTitle", (0, 0, width - 122, 23))
			res.append(MultiContentEntryText(pos=(offset + x, y), size=(w-offset-duration_size, h), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))
			x,y,w,h = skin.parameters.get("MovieListCompactDescDescription", (0, 25, width - 212, 17))
			res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=1, flags=RT_HALIGN_LEFT, text=description))
			x,y,w,h = skin.parameters.get("MovieListCompactDescBegin", (width - 120, 6, 120, 20))
			res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))
			if service is not None:
				x,y,w,h = skin.parameters.get("MovieListCompactDescService", (width - 212, 25, 154, 17))
				res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))
				x,y,w,h = skin.parameters.get("MovieListCompactDescLength", (width, 25, 0, 20))
			res.append(MultiContentEntryText(pos=(x - duration_size, y), size=(duration_size + w, h), font=1, flags=RT_HALIGN_RIGHT, text=len))
		elif self.list_type == MovieList.LISTTYPE_COMPACT:
			x,y,w,h = skin.parameters.get("MovieListCompactTitle", (0, 0, width - 77, 23))
			res.append(MultiContentEntryText(pos=(offset+x, y), size=(w - offset - duration_size, h), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))
			if self.tags:
				x,y,w,h = skin.parameters.get("MovieListCompactTags", (width - 200, 25, 200, 17))
				res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 1, flags = RT_HALIGN_RIGHT, text = tags))
				if service is not None:
					x,y,w,h = skin.parameters.get("MovieListCompactServiceTags", (200, 25, 200, 17))
					res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))
			else:
				if service is not None:
					x,y,w,h = skin.parameters.get("MovieListCompactService", (width - 200, 25, 200, 17))
					res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))
			x,y,w,h = skin.parameters.get("MovieListCompactBegin", (0, 25, 200, 17))
			res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=1, flags=RT_HALIGN_LEFT, text=begin_string))
			x,y,w,h = skin.parameters.get("MovieListCompactLength", (width, 0, 0, 22))
			res.append(MultiContentEntryText(pos=(x - duration_size, y), size=(duration_size + w, h), font=0, flags=RT_HALIGN_RIGHT, text=len))
		elif self.list_type == MovieList.LISTTYPE_MINIMALVTI:
			x, y, z = skin.parameters.get("MovieListChannelSize", (110, 50, 0))
			channel_size = x
			if self.show_picon:
				channel_size = y
			if not self.show_channel_info:
				channel_size = z
			x, y = skin.parameters.get("MovieListNameXtraSize", (0, 60))
			xtra_size = x
			if width > 850 and not self.show_picon:
				xtra_size = y
			x, y = skin.parameters.get("MovieListFileSize", (0, 100))
			file_size = x
			if self.show_file_size:
				file_size = y
			x, y, z = skin.parameters.get("MovieListBeginStringSize", (160, 110, 0))
			begin_string_size = x
			if self.only_day:
				begin_string_size = y
			if not self.show_recording_date:
				begin_string_size = z
			if self.descr_state == MovieList.SHOW_DESCRIPTION and description != "":
				txt = txt + " - " + description
			x,y,w,h = skin.parameters.get("MovieListMinimalVTITitle", (0, 0, width - 25, 30))
			res.append(MultiContentEntryText(pos=(offset+x, y), size=(w - begin_string_size  - duration_size - offset - channel_size  - xtra_size  - file_size, h), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))
			if self.show_recording_date:
				x,y,w,h = skin.parameters.get("MovieListMinimalVTIBegin", (width - 5, 0, 0, 30))
				res.append(MultiContentEntryText(pos=(x  - duration_size - begin_string_size - file_size, y), size=(w + begin_string_size, h), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))
			if self.show_duration:
				x,y,w,h = skin.parameters.get("MovieListMinimalVTILength", (width,0,0,30))
				res.append(MultiContentEntryText(pos=(x - duration_size - file_size, y), size=(w + duration_size, h), font=1, flags=RT_HALIGN_RIGHT, text=len))
			if self.show_file_size:
				x,y,w,h = skin.parameters.get("MovieListMinimalVTISize", (width,0,0,30))
				res.append(MultiContentEntryText(pos=(x - file_size, y), size=(w + file_size, h), font=1, flags=RT_HALIGN_RIGHT, text=f_size))
			if self.show_channel_info and service:
				if self.show_picon:
					picon = findPicon(service.ref.toString())
					if fileExists(picon):
						x,y,w,h = skin.parameters.get("MovieListMinimalVTIPicon", (width - 40,0,50,30))
						res.append(MultiContentEntryPixmapAlphaTest(pos = (x -  duration_size - begin_string_size - xtra_size - file_size, y),size = (w, h), png = LoadPixmap(picon), options = BT_SCALE | BT_FIXRATIO))
				else:
					x,y,w,h = skin.parameters.get("MovieListMinimalVTIService", (width - 105,0,0,30))
					res.append(MultiContentEntryText(pos=(x - duration_size - begin_string_size - xtra_size - file_size, y), size=(channel_size + xtra_size + w, h), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))
		else:
			assert(self.list_type == MovieList.LISTTYPE_MINIMAL)
			if self.descr_state == MovieList.SHOW_DESCRIPTION:
				x,y,w,h = skin.parameters.get("MovieListMinimalTitleDesc", (0,0,width - 146,23))
				res.append(MultiContentEntryText(pos=(offset + x, y), size=(w - offset, h), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))
				x,y,w,h = skin.parameters.get("MovieListMinimalBegin", (width - 145,4,145,20))
				res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))
			else:
				x,y,w,h = skin.parameters.get("MovieListMinimalTitle", (0,0,width - 77,23))
				res.append(MultiContentEntryText(pos=(offset + x, y), size=(w - offset, h), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))
				x,y,w,h = skin.parameters.get("MovieListMinimalLength", (width - 75,0,75,20))
				res.append(MultiContentEntryText(pos=(x, y), size=(w, h), font=0, flags=RT_HALIGN_RIGHT, text=len))
		
		return res

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and l[0] and l[1] and l[1].getEvent(l[0])

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	def getCurrentDuration(self):
		l = self.l.getCurrentSelection()
		dur = ""
		if len(l) >= 4:
			dur = l[3]
			if dur > 0:
				if self.duration_in_min:
					dur = "%d min" % (dur / 60)
				else:
					dur = "%d:%02d" % (dur / 60, dur % 60)
			else:
				dur = ""
		return dur

	def getCurrentPlayList(self):
		if hasattr(self, 'list'):
			ref_list = []
			for l in self.list:
				if l[0].flags & eServiceReference.mustDescent:
					continue
				if l[0].getPath().split(".")[-1].lower() == "iso":
					continue
				ref_list.append(l[0])
			return ref_list
		return None

	def getCurrentList(self):
		if hasattr(self, 'list'):
			ref_list = []
			for l in self.list:
				ref_list.append(l[0])
			return ref_list
		return None

	def getSelectedEntries(self):
		return self.selected_entries

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)

	def reload(self, root = None, filter_tags = None):
		self.getMovieListConfig()
		if root is not None:
			self.load(root, filter_tags)
		else:
			self.load(self.root, filter_tags)
		self.l.setList(self.list)

	def removeService(self, service):
		for l in self.list[:]:
			if l[0] == service:
				self.list.remove(l)
		self.l.setList(self.list)

	def __len__(self):
		return len(self.list)

	def load(self, root, filter_tags):
		# this lists our root service, then building a 
		# nice list
		
		self.list = [ ]
		self.serviceHandler = eServiceCenter.getInstance()
		
		self.root = root
		list = self.serviceHandler.list(root)
		if list is None:
			print "listing of movies failed"
			list = [ ]	
			return
		tags = set()

		if self.show_dir:
			dirs = []

		while 1:
			serviceref = list.getNext()
			if not serviceref.valid():
				break
			is_dvd = None
			if serviceref.flags & eServiceReference.mustDescent:
				filepath = os.path.realpath(serviceref.getPath())
				possible_path = ("VIDEO_TS", "video_ts", "VIDEO_TS.IFO", "video_ts.ifo")
				for mypath in possible_path:
					if os.path.exists(os.path.join(filepath, mypath)):
						is_dvd = True
						serviceref = eServiceReference(4097, 0, filepath)
						break

			if is_dvd is None:
				if self.show_dir:
					if serviceref.flags & eServiceReference.mustDescent:
						tempDir = serviceref.getPath()
						parts = tempDir.split("/")
						dirName = parts[-2]
						if not self.show_trash_dir:
							if dirName == "movie_trash":
								continue
						serviceref.setName(dirName)
						dirs.append((serviceref, None, -1, -1))
						continue
				else:
					if serviceref.flags & eServiceReference.mustDescent:
						continue

			if serviceref.getPath().split(".")[-1].lower() == "iso":
				serviceref = eServiceReference(4097, 0, serviceref.getPath())
		
			info = self.serviceHandler.info(serviceref)
			if info is None:
				continue
			
			begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
		
			# convert space-seperated list of tags into a set
			this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
			if this_tags == ['']:
				this_tags = []
			this_tags = set(this_tags)
			tags |= this_tags
		
			# filter_tags is either None (which means no filter at all), or 
			# a set. In this case, all elements of filter_tags must be present,
			# otherwise the entry will be dropped.			
			if filter_tags is not None and not this_tags.issuperset(filter_tags):
				continue
		
			self.list.append((serviceref, info, begin, -1))
		
		if self.sort_type == MovieList.SORT_ALPHANUMERIC:
			self.list.sort(key=self.buildAlphaNumericSortKey)
		elif self.sort_type == MovieList.SORT_ALPHANUMERIC_INVERS:
			self.list.sort(key=self.buildAlphaNumericSortKey)
			self.list.reverse()
		elif self.sort_type == MovieList.SORT_RECORDED_INVERS:
			self.list.sort(key=lambda x: -x[2])
			self.list.reverse()
		else:
			self.list.sort(key=lambda x: -x[2])
		
		if self.show_dir:
			dirs.sort(key=self.sortDirs, reverse=True)
			for servicedirs in dirs:
				self.list.insert(0,servicedirs)
			tmp = self.root.getPath()
			if len(tmp) > 1:
				tt = eServiceReference(eServiceReference.idFile, eServiceReference.flagDirectory, ".." )
				tt.setName("..")
				tmpRoot = os.path.dirname(tmp[:-1])
				if len(tmpRoot) > 1:
					tmpRoot = tmpRoot + "/"
				tt.setPath(tmpRoot)
				self.list.insert(0,(tt,None,-1,-1))

		# finally, store a list of all tags which were found. these can be presented
		# to the user to filter the list
		self.tags = tags

	def sortDirs(self, listentry):
		return listentry[0].getName().lower()

	def buildAlphaNumericSortKey(self, x):
		ref = x[0]
		info = self.serviceHandler.info(ref)
		name = info and info.getName(ref)
		return (name and name.lower() or "", -x[2])

	def moveTo(self, serviceref):
		count = 0
		for x in self.list:
			if x[0] == serviceref:
				self.instance.moveSelectionTo(count)
				return True
			count += 1
		return False
	
	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)
