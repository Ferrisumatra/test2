from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigInteger, ConfigSelection, getConfigListEntry, ConfigSelectionNumber
from Components.ConfigList import ConfigListScreen
from Plugins.Plugin import PluginDescriptor

from enigma import setAnimation_current, setAnimation_speed, eTimer, gMainDC

import uuid


animation_modes = [("0",_("Disable Animations")),
	("1", _("Simple fade")),
	("2", _("Grow drop")),
	("3", _("Grow from left")),
	("4", _("Popup")),
	("5", _("Slide drop")),
	("6", _("Slide left to right")),
	("7", _("Slide top to bottom")),
	("8", _("Stripes"))]


config.misc.window_animation_default = ConfigSelection(default = "1", choices = animation_modes)
config.misc.window_animation_speed = ConfigSelectionNumber(min = 1, max = 30, stepwidth = 1, default = 10, wraparound = True)
config.misc.window_animation_startdelay = ConfigSelectionNumber(min = 0, max = 10, stepwidth = 1, default = 0, wraparound = True)

orig_Screen__show = None
orig_Screen__doClose = None
orig_InfoBar_hide = None
ANIMATION_OFF = False
ANIMATION_DISABLED = False

class AnimationSetupScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="AnimationSetup" position="center,center" size="580,400" title="Animation Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" zPosition="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" zPosition="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" zPosition="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#18188b" transparent="1" />
			<widget name="config" position="10,60" size="560,364" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):

		self.skin = AnimationSetupScreen.skin
		Screen.__init__(self, session)
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_blue"] = StaticText(_("Preview"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyclose,
				"save": self.ok,
				"ok" : self.ok,
				"blue": self.preview
			}, -3)
		self.createConfigList()

	def createConfigList(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Animation type:"), config.misc.window_animation_default))
		self.list.append(getConfigListEntry(_("Animation speed:"), config.misc.window_animation_speed))
		self.list.append(getConfigListEntry(_("Animation start delay:"), config.misc.window_animation_startdelay))
		self["config"].setList(self.list)

	def ok(self):
		for x in self.list:
			x[1].save()
		gMainDC.getInstance().setAniMode(int(config.misc.window_animation_default.value))
		setAnimation_current(int(config.misc.window_animation_default.value))
		setAnimation_speed(int(config.misc.window_animation_speed.value))
		self.close()

        def keyclose(self):
		for x in self.list:
			x[1].cancel()
		setAnimation_current(int(config.misc.window_animation_default.value))
		setAnimation_speed(int(config.misc.window_animation_speed.value))
		gMainDC.getInstance().setAniMode(int(config.misc.window_animation_default.value))
		self.close()

	def preview(self):
		global ANIMATION_OFF
		tmp_animation_off = ANIMATION_OFF
		ANIMATION_OFF = False
		setAnimation_current(int(config.misc.window_animation_default.value))
		setAnimation_speed(int(config.misc.window_animation_speed.value))
		gMainDC.getInstance().setAniMode(int(config.misc.window_animation_default.value))
		txt = _("Animation type:") + str(config.misc.window_animation_default.getText()) + "\n" + _("Animation speed:") + str(config.misc.window_animation_speed.value)
		self.session.open(MessageBox, txt, MessageBox.TYPE_INFO, timeout=3)
		ANIMATION_OFF = tmp_animation_off

def animationSetupMain(session, **kwargs):
	session.open(AnimationSetupScreen)

def startAnimationSetup(menuid):
	if menuid != "system":
		return []
	return [( _("Animations"), animationSetupMain, "animation_setup", None)]

def setAnimation(state = False):
	global ANIMATION_DISABLED
	if state:
		if ANIMATION_DISABLED:
			setAnimation_current(int(config.misc.window_animation_default.value))
		ANIMATION_DISABLED = False
			
	else:
		if not ANIMATION_DISABLED:
			setAnimation_current(0)
		ANIMATION_DISABLED = True

def Screen_show(self):
	if not hasattr(self, "screen_id"):
		self.screen_id = None
	if not self.already_shown:
		self.screen_id = self.__class__.__name__ + "_" + str(uuid.uuid1())
	global ANIMATION_OFF, ANIMATION_DISABLED
	if ANIMATION_OFF:
		setAnimation(False)
	orig_Screen__show(self)
	if ANIMATION_OFF == False and self.skinAttributes:
		for attr in self.skinAttributes:
			if attr[0] == "NoAnimationAfter" and attr[1] in ("1", "on"):
				ANIMATION_OFF = self.screen_id

def Screen_doClose(self):
	if not hasattr(self, "screen_id"):
		self.screen_id = None
	global ANIMATION_OFF
	if ANIMATION_OFF and ANIMATION_OFF == self.screen_id:
		ANIMATION_OFF = False
		setAnimation(True)
	orig_Screen__doClose(self)

def delayedStart():
	setAnimation_current(int(config.misc.window_animation_default.value))
	setAnimation_speed(int(config.misc.window_animation_speed.value))
	if int(config.misc.window_animation_default.value) > 0:
		gMainDC.getInstance().setAniMode(int(config.misc.window_animation_default.value))

def InfoBar_hide(self):
	orig_InfoBar_hide(self)
	if InfoBar.instance:
		InfoBar.hide = orig_InfoBar_hide
	delay = int(config.misc.window_animation_startdelay.value) * 1000
	if delay > 0:
		self.delay_Timer = eTimer()
		self.delay_Timer.start(delay, True)
		self.delay_Timer.callback.append(delayedStart)
	else:
		delayedStart()

def sessionAnimationSetup(session, reason, **kwargs):
	global orig_Screen__show, orig_Screen__doClose, orig_InfoBar_hide
	if orig_Screen__show is None:
		orig_Screen__show = Screen.show
	if orig_Screen__doClose is None:
		orig_Screen__doClose = Screen.doClose
	if orig_InfoBar_hide is None:
		orig_InfoBar_hide = InfoBar.hide
	Screen.show = Screen_show
	Screen.doClose = Screen_doClose
	InfoBar.hide = InfoBar_hide

def Plugins(**kwargs):
	plugin_list = [
		PluginDescriptor(
			name = "Animations",
			description = "Setup UI animations",
			where = PluginDescriptor.WHERE_MENU,
			needsRestart = False,
			fnc = startAnimationSetup),
		PluginDescriptor(
			where = PluginDescriptor.WHERE_SESSIONSTART,
			needsRestart = False,
			fnc = sessionAnimationSetup),
	]
	return plugin_list;
