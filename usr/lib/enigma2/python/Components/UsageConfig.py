from Components.Harddisk import harddiskmanager
from Components.NimManager import nimmanager
from config import ConfigSubsection, ConfigYesNo, config, ConfigSelection, ConfigText, ConfigNumber, ConfigSet, ConfigLocations, ConfigInteger, NoSave, ConfigDirectory
from Tools.Directories import resolveFilename, SCOPE_HDD
from Tools.HardwareInfoVu import HardwareInfoVu
from enigma import Misc_Options, setTunerTypePriorityOrder, setPreferredTuner, setEnableTtCachingOnOff, eEnv;
from SystemInfo import SystemInfo
import os

def InitUsageConfig():
	config.usage = ConfigSubsection();
	config.usage.showdish = ConfigYesNo(default = True)
	config.usage.multibouquet = ConfigYesNo(default = True)
	config.usage.multiepg_ask_bouquet = ConfigYesNo(default = False)

	config.usage.quickzap_bouquet_change = ConfigYesNo(default = True)
	config.usage.e1like_radio_mode = ConfigYesNo(default = True)
	config.usage.infobar_timeout = ConfigSelection(default = "5", choices = [
		("0", _("no timeout")), ("1", "1 " + _("second")), ("2", "2 " + _("seconds")), ("3", "3 " + _("seconds")),
		("4", "4 " + _("seconds")), ("5", "5 " + _("seconds")), ("6", "6 " + _("seconds")), ("7", "7 " + _("seconds")),
		("8", "8 " + _("seconds")), ("9", "9 " + _("seconds")), ("10", "10 " + _("seconds"))])
	config.usage.show_infobar_on_zap = ConfigYesNo(default = True)
	config.usage.show_infobar_on_skip = ConfigYesNo(default = True)
	config.usage.show_infobar_on_event_change = ConfigYesNo(default = True)
	config.usage.hdd_standby = ConfigSelection(default = "60", choices = [
		("0", _("no standby")), ("10", "10 " + _("seconds")), ("30", "30 " + _("seconds")),
		("60", "1 " + _("minute")), ("120", "2 " + _("minutes")),
		("300", "5 " + _("minutes")), ("600", "10 " + _("minutes")), ("1200", "20 " + _("minutes")),
		("1800", "30 " + _("minutes")), ("3600", "1 " + _("hour")), ("7200", "2 " + _("hours")),
		("14400", "4 " + _("hours")) ])
	config.usage.output_12V = ConfigSelection(default = "do not change", choices = [
		("do not change", _("do not change")), ("off", _("off")), ("on", _("on")) ])

	zero_button_choices = [ ("standard", _("standard")),
				("swap", _("swap PiP and main picture")),
				("swapstop", _("move PiP to main picture")),
				("stop", _("stop PiP")),
				("zap_focus", _("toggle zap focus")) ]
	config.usage.pip_zero_button = ConfigSelection(default = "swap", choices = zero_button_choices)
	config.usage.pip_zero_button_doubleclick = ConfigSelection(default = "zap_focus", choices = zero_button_choices)

	config.usage.default_path = ConfigText(default = resolveFilename(SCOPE_HDD))
	config.usage.timer_path = ConfigText(default = "<default>")
	config.usage.instantrec_path = ConfigText(default = "<default>")
	config.usage.timeshift_path = ConfigText(default = "/media/hdd/")
	config.usage.allowed_timeshift_paths = ConfigLocations(default = ["/media/hdd/"])

	config.usage.on_movie_start = ConfigSelection(default = "ask", choices = [
		("ask", _("Ask user")), ("resume", _("Resume from last position")), ("beginning", _("Start from the beginning")) ])
	config.usage.on_movie_stop = ConfigSelection(default = "ask", choices = [
		("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service")) ])
	config.usage.on_movie_eof = ConfigSelection(default = "ask", choices = [
		("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service")), ("pause", _("Pause movie at end")), ("restart", _("Start from the beginning")), ("playnext", _("Start next media file")) ])

	config.usage.setup_level = ConfigSelection(default = "expert", choices = [
		("simple", _("Simple")),
		("intermediate", _("Intermediate")),
		("expert", _("Expert")) ])

	config.usage.on_long_powerpress = ConfigSelection(default = "show_menu", choices = [
		("show_menu", _("show shutdown menu")),
		("shutdown", _("immediate shutdown")),
		("standby", _("Standby")),
		("restart", _("Restart")),
		("restart_gui", _("Restart GUI")),
		("nothing", _("do nothing")) ] )
	
	config.usage.on_short_powerpress = ConfigSelection(default = "standby", choices = [
		("show_menu", _("show shutdown menu")),
		("shutdown", _("immediate shutdown")),
		("standby", _("Standby")),
		("restart", _("Restart")),
		("restart_gui", _("Restart GUI")),
		("nothing", _("do nothing")) ] )


	config.usage.alternatives_priority = ConfigSelection(default = "0", choices = [
		("0", "DVB-S/-C/-T"),
		("1", "DVB-S/-T/-C"),
		("2", "DVB-C/-S/-T"),
		("3", "DVB-C/-T/-S"),
		("4", "DVB-T/-C/-S"),
		("5", "DVB-T/-S/-C") ])

	nims = [ ("-1", _("auto")) ]
	for x in nimmanager.nim_slots:
		nims.append( (str(x.slot), x.getSlotName()) )
	config.usage.tuner_priority = ConfigSelection(default = "-1", choices = nims)

	config.usage.show_event_progress_in_servicelist = ConfigYesNo(default = False)

	config.usage.blinking_display_clock_during_recording = ConfigYesNo(default = False)

	config.usage.show_message_when_recording_starts = ConfigYesNo(default = True)

	config.usage.load_length_of_movies_in_moviellist = ConfigYesNo(default = True)
	
	def TunerTypePriorityOrderChanged(configElement):
		setTunerTypePriorityOrder(int(configElement.value))
	config.usage.alternatives_priority.addNotifier(TunerTypePriorityOrderChanged, immediate_feedback=False)

	def PreferredTunerChanged(configElement):
		setPreferredTuner(int(configElement.value))
	config.usage.tuner_priority.addNotifier(PreferredTunerChanged)

	def setHDDStandby(configElement):
		for hdd in harddiskmanager.HDDList():
			hdd[1].setIdleTime(int(configElement.value))
	config.usage.hdd_standby.addNotifier(setHDDStandby, immediate_feedback=False)

	def set12VOutput(configElement):
		if configElement.value == "on":
			Misc_Options.getInstance().set_12V_output(1)
		elif configElement.value == "off":
			Misc_Options.getInstance().set_12V_output(0)
	config.usage.output_12V.addNotifier(set12VOutput, immediate_feedback=False)

	SystemInfo["12V_Output"] = Misc_Options.getInstance().detected_12V_output()

	config.usage.keymap = ConfigText(default = eEnv.resolve("${datadir}/enigma2/keymap.xml"))

	config.seek = ConfigSubsection()
	config.seek.selfdefined_13 = ConfigNumber(default=15)
	config.seek.selfdefined_46 = ConfigNumber(default=60)
	config.seek.selfdefined_79 = ConfigNumber(default=300)

	config.seek.speeds_forward = ConfigSet(default=[2, 4, 8, 16, 32, 64, 128], choices=[2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.speeds_backward = ConfigSet(default=[2, 4, 8, 16, 32, 64, 128], choices=[1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128])
	config.seek.speeds_slowmotion = ConfigSet(default=[2, 4, 8], choices=[2, 4, 6, 8, 12, 16, 25])

	config.seek.enter_forward = ConfigSelection(default = "2", choices = ["2", "4", "6", "8", "12", "16", "24", "32", "48", "64", "96", "128"])
	config.seek.enter_backward = ConfigSelection(default = "1", choices = ["1", "2", "4", "6", "8", "12", "16", "24", "32", "48", "64", "96", "128"])

	config.seek.on_pause = ConfigSelection(default = "play", choices = [
		("play", _("Play")),
		("step", _("Singlestep (GOP)")),
		("last", _("Last speed")) ])

	config.usage.timerlist_finished_timer_position = ConfigSelection(default = "beginning", choices = [("beginning", _("at beginning")), ("end", _("at end"))])

	def updateEnterForward(configElement):
		if not configElement.value:
			configElement.value = [2]
		updateChoices(config.seek.enter_forward, configElement.value)

	config.seek.speeds_forward.addNotifier(updateEnterForward, immediate_feedback = False)

	def updateEnterBackward(configElement):
		if not configElement.value:
			configElement.value = [2]
		updateChoices(config.seek.enter_backward, configElement.value)

	config.seek.speeds_backward.addNotifier(updateEnterBackward, immediate_feedback = False)


# VTI Settings start
	config.misc.placeholder = NoSave(ConfigSelection(default = "1", choices = [("1", " ")]))
	config.misc.disable_auto_channel_list = ConfigYesNo(default = False)
	config.misc.allow_service_delete = ConfigYesNo(default = False)
	config.misc.ecm_info = ConfigYesNo(default = True)
	config.misc.enable_custom_mainmenu = ConfigYesNo(default = False)
	config.usage.enable_zaphistory = ConfigYesNo(default = True)
	config.usage.show_epg_progress_percent = ConfigYesNo(default = False)
	config.usage.servicelist_show_picon = ConfigSelection(default = "0", choices = [
		("0", _("off")),
		("100", "100x60 px"),
		("50", "50x30 px"),
		("1", _("user defined")),])
	config.usage.servicelist_picon_dir = ConfigDirectory(default = "/usr/share/enigma2/picon")
	config.usage.servicelist_two_lines = ConfigYesNo(default = False)
	config.usage.servicelist_show_event_time = ConfigYesNo(default = False)
	config.usage.servicelist_mark_rec_service = ConfigYesNo(default = True)
	config.usage.servicelist_show_rec_service_symbol = ConfigYesNo(default = True)
	config.usage.servicelist_show_servicenumber = ConfigYesNo(default = True)
	config.usage.servicelist_name_width = ConfigInteger(default = 200, limits = (1, 1920))
	config.usage.servicelist_use_matrix = ConfigYesNo(default = False)
	config.usage.servicelist_show_next_event = ConfigYesNo(default = False)
	config.usage.servicelist_show_service_type_icon = ConfigYesNo(default = False)
	config.usage.servicelist_preview_mode = ConfigYesNo(default = False)
	config.usage.servicelist_hide_service_name = ConfigYesNo(default = False)
	
	rec_button_choices = \
		[
			("record_menu", _("show record menu")),
			("running_record", _("show running records")),
			("timer_list", _("show timer list")),
			("event_record", _("add recording (stop after current event)")),
			("indefinitely_record", _("add recording (indefinitely)")),
			("manualduration_record", _("add recording (enter recording duration)")),
			("manualendtime_record", _("add recording (enter recording endtime)"))
		]
	
	config.usage.rec_button = ConfigSelection(default = "record_menu", choices = rec_button_choices)
	config.usage.rec_button_long = ConfigSelection(default = "running_record", choices = rec_button_choices)
	
	
	config.usage.remove_finished_timers = ConfigYesNo(default = True)
	config.usage.enable_eit_epg = ConfigYesNo(default = True)
	def setEITepg(configElement):
			from enigma import eEPGCache
			eEPGCache.getInstance().setEITenabled(int(config.usage.enable_eit_epg.getValue()))
	config.usage.enable_eit_epg.addNotifier(setEITepg)
	config.usage.show_nownext_eit = ConfigYesNo(default = True)
	config.usage.show_old_epg = ConfigSelection(default = "0", choices = [
		("0", _("off")),
		("3600", "1 h"),
		("21600", "6 h"),
		("43200", "12 h"),
		("86400", "24 h"),])
	def setOldEPGBuffer(configElement):
			from enigma import eEPGCache
			eEPGCache.getInstance().setOldEPG(int(config.usage.show_old_epg.getValue()))
	config.usage.show_old_epg.addNotifier(setOldEPGBuffer)

	config.usage.epg_buffer = ConfigInteger(default = 14, limits = (1, 28))
	def setEPGBufferDays(configElement):
			from enigma import eEPGCache
			eEPGCache.getInstance().setEPGBuffer(config.usage.epg_buffer.getValue())
	config.usage.epg_buffer.addNotifier(setEPGBufferDays)
	epg_choices = [
		("eventview", _("Event Description")),
		("singleepg", _("Single Service EPG")),
		("multiepg", _("Multi EPG")),
		("epgbar", _("Service EPGBar"))]
	if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/GraphMultiEPG/plugin.py'):
		epg_choices.append(("graphicalmultiepg", _("Graphical Multi EPG")))
	config.usage.epg_default_view = ConfigSelection(default = "eventview", choices = epg_choices)

	config.usage.enable_tt_caching = ConfigYesNo(default = True)
	def EnableTtCachingChanged(configElement):
		setEnableTtCachingOnOff(int(configElement.value))
	config.usage.enable_tt_caching.addNotifier(EnableTtCachingChanged)

	config.usage.stop_seek_eof = ConfigSelection(default = "20", choices = [
		("0", _("off")),
		("10", "10 " + _("seconds")),
		("20", "20 " + _("seconds")),
		("30", "30 " + _("seconds")),
		("60", "60 " + _("seconds"))])

	def updateVideoDirChoice(configElement):
		tmp = configElement.value
		tmp.append(_("off"))
		tmp.append(_("last video"))
		if config.movielist.start_videodir.value in tmp:
			default = config.movielist.start_videodir.value
		else:
			default = _("last video")
		config.movielist.start_videodir.setChoices(tmp, default)
	tmp = config.movielist.videodirs.value
	tmp.append(_("off"))
	tmp.append(_("last video"))
	config.movielist.start_videodir = ConfigSelection(default = _("last video"), choices = tmp)
	config.movielist.videodirs.addNotifier(updateVideoDirChoice)
	config.usage.movielist_folder_based_config = ConfigYesNo(default = True)
	config.usage.movielist_support_pig = ConfigYesNo(default = True)
	config.usage.movielist_last_played_movie = ConfigText(default = "")
	config.usage.movielist_select_last_movie = ConfigYesNo(default = True)
	config.usage.movielist_resume_at_eof = ConfigYesNo(default = True)
	config.usage.movielist_show_cover = ConfigYesNo(default = True)
	config.usage.movielist_show_dir = ConfigYesNo(default = True)
	config.usage.movielist_show_trash_dir = ConfigYesNo(default = False)
	config.usage.movielist_use_trash_dir = ConfigYesNo(default = False)
	config.usage.movielist_show_icon = ConfigYesNo(default = True)
	config.usage.movielist_show_color = ConfigYesNo(default = True)
	config.usage.movielist_show_picon = ConfigYesNo(default = False)
	config.usage.movielist_show_channel_info = ConfigYesNo(default = True)
	config.usage.movielist_show_recording_date = ConfigYesNo(default = True)
	config.usage.movielist_show_file_size = ConfigYesNo(default = True)
	config.usage.movielist_only_day = ConfigYesNo(default = True)
	config.usage.movielist_show_last_stop_time = ConfigYesNo(default = False)
	config.usage.movielist_show_duration = ConfigYesNo(default = True)
	config.usage.movielist_duration_in_min = ConfigYesNo(default = True)
	config.usage.movielist_progress_seen = ConfigInteger(default = 80, limits = (40, 99))
	config.usage.movielist_leave_exit = ConfigYesNo(default = True)
	config.usage.movielist_ask_movie_del = ConfigYesNo(default = False)
	config.usage.movielist_show_progress = ConfigSelection(default = "progress_bar", choices = [
		("progress_bar", _("progress bar")),
		("progress_percent", _("percent")),
		("progress_calculate", _("only calculate")),
		("progress_off", _("off"))])
	config.usage.timerlist_show_icon = ConfigYesNo(default = True)
	config.usage.timerlist_show_epg = ConfigYesNo(default = True)
	config.usage.timerlist_style = ConfigSelection(default = "0", choices = [
		("0", _("Default")),
		("1", _("Style") + " 1"),
		("2", _("Style") + " 2"),
		("3", _("Style") + " 3"),
		("4", _("Style") + " 4"),
		("5", _("Style") + " 5"),])
	config.usage.show_favourites_bouquetup = ConfigYesNo(default = False)
	config.usage.show_servicelist_at_modeswitch = ConfigYesNo(default = False)
	config.usage.use_pig = ConfigYesNo(default = False)
	config.usage.use_extended_pig = ConfigYesNo(default = False)
	config.usage.use_extended_pig_channelselection = ConfigYesNo(default = False)
	config.usage.show_infobar_on_splitscreen = ConfigYesNo(default = False)
	pip_modes = [("splitscreen", _("Split Screen")), ("audiozap", _("Audio Zap")), ("pip", _("Picture in Picture"))]
	config.usage.default_pip_mode = ConfigSelection(default = "splitscreen", choices = pip_modes)
	config.usage.default_zero_double_click_mode = ConfigSelection(default = "pip", choices = pip_modes)
	default_timeout = SystemInfo["CanPiP"] and 500 or 50
	config.usage.zero_doubleclick_timeout = ConfigInteger(default = default_timeout, limits = (50, 5000))
	config.usage.zap_pip = ConfigYesNo(default = True)
	config.usage.zap_before_record = ConfigYesNo(default = False)
	config.usage.zap_notification_record = ConfigYesNo(default = True)
	if SystemInfo["CanPiP"]:
		config.usage.pip_in_EPGBar = ConfigYesNo(default = True)
	else:
		config.usage.pip_in_EPGBar = ConfigYesNo(default = False)
	config.usage.picon_dir = ConfigDirectory(default = "/usr/share/enigma2/picon")
	config.usage.picon_scale = ConfigYesNo(default = True)
	config.usage.sort_menu_byname = ConfigYesNo(default = False)
	config.usage.sort_plugins_byname = ConfigYesNo(default = True)
	config.usage.numberzap_timeout = ConfigInteger(default = 3000, limits = (100, 20000))
	config.usage.numberzap_show_servicename = ConfigYesNo(default = True)
	config.usage.numberzap_show_picon = ConfigYesNo(default = True)
	config.usage.startup_service_leavestandby = ConfigYesNo(default = False)
	config.usage.overzap_notplayable = ConfigYesNo(default = False)
	config.usage.disable_tuner_error_popup = ConfigYesNo(default = False)
	config.usage.disable_infobar_timeout_okbutton = ConfigYesNo(default = False)
	config.usage.ask_timer_file_del = ConfigYesNo(default = True)
	config.usage.record_file_name_date_at_end = ConfigYesNo(default = False)
	config.usage.silent_rec_mode = ConfigYesNo(default = True)
	config.usage.vfd_scroll_delay = ConfigSelection(default = "10000", choices = [
		("10000", "10 " + _("seconds")),
		("20000", "20 " + _("seconds")),
		("30000", "30 " + _("seconds")),
		("60000", "1 " + _("minute")),
		("300000", "5 " + _("minutes")),
		("noscrolling", _("off"))])
	config.usage.vfd_scroll_speed = ConfigSelection(default = "300", choices = [
		("500", _("slow")),
		("300", _("normal")),
		("100", _("fast"))])

	def get_default_RC():
		device = HardwareInfoVu().get_device_name()
		if device =="duo2":
			return "2"
		elif device == "ultimo":
			return "1"
		return "0"

	config.usage.rc_style = ConfigSelection(default = get_default_RC(), choices = [
		("0", "Vu+ 1 (Duo, Solo, Uno, Solo2)"),
		("1", "Vu+ 2 (Ultimo)"),
		("2", "Vu+ 3 (Duo2)")])
	config.usage.use_force_overwrite = ConfigYesNo(default = True)
	config.usage.use_package_conffile = ConfigYesNo(default = True)
	config.usage.use_rm_force_depends = ConfigYesNo(default = False)
	config.usage.use_rm_autoremove = ConfigYesNo(default = True)
	config.usage.check_for_updates = ConfigInteger(default = 8, limits = (0, 24))
	config.usage.show_notification_for_updates = ConfigYesNo(default = True)
	config.usage.update_available = NoSave(ConfigYesNo(default = False))
	config.usage.blinking_rec_symbol_during_recording = ConfigYesNo(default = True)
	config.usage.enable_hbbtv_autostart = ConfigYesNo(default = True)
	config.subtitle = ConfigSubsection()
	config.subtitle.subtitlecolor = ConfigSelection(default = "0", choices = [
		("0", _("original")),
		("1", _("white")),
		("2", _("yellow")),
		("3", _("dark yellow")),
		("4", _("red")),
		("5", _("green")),
		("6", _("cyan")),
		("7", _("grey")),])
	config.subtitle.subtitlefontsize  = ConfigSelection(choices = ["16", "18", "20", "22", "24", "26", "28", "30", "32", "34", "36", "38", "40", "42", "44", "46", "48", "50", "54", "58", "60"], default = "30")
	config.subtitle.subtitlehalignment = ConfigSelection(choices = ["left", "center", "right"], default = "center")
	config.subtitle.dvbsubtitleyellow = ConfigYesNo(default = False)
	config.subtitle.dvbsubtitlecentered = ConfigYesNo(default = False)
	config.subtitle.dvbsubtitlebacktrans = ConfigSelection(default = "0", choices = [
		("0", _("no transparency")),
		("25", "10%"),
		("50", "20%"),
		("75", "30%"),
		("100", "40%"),
		("125", "50%"),
		("150", "60%"),
		("175", "70%"),
		("200", "80%"),
		("225", "90%"),
		("255", _("full transparency"))])
# VTI Settings end

def updateChoices(sel, choices):
	if choices:
		defval = None
		val = int(sel.value)
		if not val in choices:
			tmp = choices[:]
			tmp.reverse()
			for x in tmp:
				if x < val:
					defval = str(x)
					break
		sel.setChoices(map(str, choices), defval)

def preferredPath(path):
	if config.usage.setup_level.index < 2 or path == "<default>":
		return None  # config.usage.default_path.value, but delay lookup until usage
	elif path == "<current>":
		return config.movielist.last_videodir.value
	elif path == "<timer>":
		return config.movielist.last_timer_videodir.value
	else:
		return path

def preferredTimerPath():
	return preferredPath(config.usage.timer_path.value)

def preferredInstantRecordPath():
	return preferredPath(config.usage.instantrec_path.value)

def defaultMoviePath():
	return config.usage.default_path.value

