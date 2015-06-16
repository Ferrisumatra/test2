from HTMLComponent import HTMLComponent
from GUIComponent import GUIComponent

from Tools.FuzzyDate import FuzzyTime

from enigma import eListboxPythonMultiContent, eListbox, gFont, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap
from timer import TimerEntry
from time import time
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Components.config import config
import skin
class TimerList(HTMLComponent, GUIComponent, object):
#
#  | <Service>     <Name of the Timer>  |
#  | <start, end>              <state>  |
#
	def buildTimerEntry(self, timer, processed):
		if config.usage.timerlist_show_icon.value:
			h_offset = int(skin.parameters.get("TimerListIconHOffset", (40,))[0])
		else:
			h_offset = int(skin.parameters.get("TimerListNoIconHOffset", (0,))[0])
		width = self.l.getItemSize().width()
		res = [ None ]
		
		timerlist_style = int(config.usage.timerlist_style.value)
		list_style_h_offset = 0
		list_style_align = RT_HALIGN_LEFT|RT_VALIGN_CENTER
		if timerlist_style:
			screentimername = timer.name
			screendesc = timer.description
			trimlength = int(skin.parameters.get("TimerListTrimLength", (60,))[0])
			
			if timerlist_style == 3 or timerlist_style == 4:
				list_style_h_offset = int(skin.parameters.get("TimerListStyle4ListStyleHOffset", (150,))[0])
				list_style_align = RT_HALIGN_RIGHT|RT_VALIGN_CENTER
			
			if timerlist_style == 4:
				trimlength += 5
				if width < 674:
					trimlength += -20
				if len(timer.description) > trimlength + 20:
					screendesc = timer.description[:trimlength - 3 + 20] + "..."
				if len(timer.name) > trimlength:
					screentimername = timer.name[:trimlength - 3] + "..."
			else:
				if width < 674 and timerlist_style != 4:
					trimlength += -20
				if len(timer.description) > trimlength:
					screendesc = timer.description[:trimlength - 3] + "..."
			
			if timerlist_style == 1:
				x,y,w,h = skin.parameters.get("TimerListStyle1Name", (0,0,width + 30,0))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.name))
				x,y,w,h = skin.parameters.get("TimerListStyle1Desc", (0,30,width,20))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, timer.service_ref.getServiceName()))
				x,y,w,h = skin.parameters.get("TimerListStyle1Desc1", (0,30,width,20))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset+x, y, w - h_offset, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, screendesc))
				
			elif timerlist_style == 2 or timerlist_style == 3:
				x,y,w,h = skin.parameters.get("TimerListStyle2Name", (0,0,width,30))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.service_ref.getServiceName() + _(": ") + timer.name))
				x,y,w,h = skin.parameters.get("TimerListStyle2Desc", (0,30,width,20))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.description))
			
			elif timerlist_style == 4:
				x,y,w,h = skin.parameters.get("TimerListStyle4Name", (0,0,width - 140,30))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset+x, y, w - h_offset, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, screentimername))
				x,y,w,h = skin.parameters.get("TimerListStyle4Desc", (0,0,width,30))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, timer.service_ref.getServiceName()))
				x,y,w,h = skin.parameters.get("TimerListStyle4Desc1", (0,30,width,20))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset+x, y, w - h_offset, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, screendesc))
				
			elif timerlist_style == 5:
				x,y,w,h = skin.parameters.get("TimerListStyle5Name", (0,0,width + 140,30))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset+x,y, w - h_offset, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, screentimername))
				x,y,w,h = skin.parameters.get("TimerListStyle5Desc", (0,0,width,30))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, timer.service_ref.getServiceName()))
			
		else:
			x,y,w,h = skin.parameters.get("TimerListNoStyleName", (0,0,width,30))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.service_ref.getServiceName()))
			x,y,w,h = skin.parameters.get("TimerListNoStyleDesc", (0,30,width,20))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, h_offset + x, y, w - h_offset, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.name))
			
		repeatedtext = ""
		days = ( _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun") )
		if timer.repeated:
			flags = timer.repeated
			count = 0
			for x in (0, 1, 2, 3, 4, 5, 6):
					if (flags & 1 == 1):
						if (count != 0):
							repeatedtext += ", "
						repeatedtext += days[x]
						count += 1
					flags = flags >> 1
			x,y,w,h = skin.parameters.get("TimerListTime", (0,50,width - 150,20))
			if timer.justplay or timer.justremind:
				if timer.end - timer.begin < 4: # rounding differences
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset + list_style_h_offset, y, w - h_offset, h, 1, list_style_align, repeatedtext + ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.begin)[1]))))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset + list_style_h_offset, y, w - h_offset, h, 1, list_style_align, repeatedtext + ((" %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60)) + _("(ZAP)")))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset + list_style_h_offset, y, w - h_offset, h, 1, list_style_align, repeatedtext + ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60))))
			x,y,w,h = skin.parameters.get("TimerListIcon", (2,34,30,30))
			if config.usage.timerlist_show_icon.value:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, self.repeat_timer))
		else:
			x,y,w,h = skin.parameters.get("TimerListTime", (0,50,width - 150,20))
			if timer.justplay or timer.justremind:
				if timer.end - timer.begin < 4:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset + list_style_h_offset, y, w - h_offset, h, 1, list_style_align, repeatedtext + (("%s, %s " + _("(ZAP)")) % (FuzzyTime(timer.begin)))))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset + list_style_h_offset, y, w - h_offset, h, 1, list_style_align, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,))) + _("(ZAP)")))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset + list_style_h_offset, y, w - h_offset, h, 1, list_style_align, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,)))))
		
		if not processed:
			if timer.state == TimerEntry.StateWaiting:
				state = _("waiting")
				if config.usage.timerlist_show_icon.value:
					png_timer = self.waiting_timer
					wait_long = (timer.begin - self.now) / 3600
					if wait_long >= 24:
						png_timer = self.waiting_timer_long
			elif timer.state == TimerEntry.StatePrepared:
				state = _("about to start")
				png_timer = self.running_timer
			elif timer.state == TimerEntry.StateRunning:
				if timer.justplay:
					state = _("zapped")
					png_timer = None
				elif timer.justremind:
					state = _("Reminder")
					png_timer = None
				else:
					state = _("recording...")
					png_timer = self.running_timer
			elif timer.state == TimerEntry.StateEnded:
				state = _("done!")
				png_timer = self.finished_timer
			else:
				state = _("<unknown>")
				png_timer = None
		else:
			state = _("done!")
			png_timer = self.finished_timer

		if timer.disabled:
			state = _("disabled")
			png_timer = self.disabled_timer

		if timerlist_style == 3 or timerlist_style == 4:
			x,y,w,h = skin.parameters.get("TimerListStateStyle4", (0,50,150,20))	
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x + h_offset, y, w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, state))
		else:
			x,y,w,h = skin.parameters.get("TimerListState", (width - 150,50,150,20))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, state))
			
		if config.usage.timerlist_show_icon.value:
			x,y,w,h = skin.parameters.get("TimerListPngTimer", (2,2,30,30))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, png_timer))
		x,y,w,h = skin.parameters.get("TimerListZapTimer", (0,0,32,32))
		if timer.justplay:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, self.zap_timer))
			
		if timer.justremind:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, self.zap_timer))
				
		if timer.disabled:
			if config.usage.timerlist_show_icon.value:
				x,y,w,h = skin.parameters.get("TimerListDisabledTimer", (2,2,30,30))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, self.disabled_timer_x))
			else:
				x,y,w,h = skin.parameters.get("TimerListRedTimer", (490,5,40,40))
				png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/redx.png"))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, png))
			
		if config.usage.timerlist_show_icon.value:
			if timer.dontSave:
				x,y,w,h = skin.parameters.get("TimerListInstantRecord", (2,34,30,30))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, self.instant_record))
		
		return res

	def __init__(self, list):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildTimerEntry)
		font, size = skin.parameters.get("TimerListFont1", ('Regular', 20))
		self.l.setFont(0, gFont(font, size))
		font, size = skin.parameters.get("TimerListFont1", ('Regular', 18))
		self.l.setFont(1, gFont(font, size))
		self.l.setItemHeight(int(skin.parameters.get("TimerListItemHeight", (70,))[0]))
		self.l.setList(list)
		
		self.running_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_red.png"))
		self.finished_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_green.png"))
		self.waiting_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_yellow.png"))
		self.waiting_timer_long = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_blue.png"))
		self.disabled_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/clock_blue.png"))
		self.disabled_timer_x = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/disabled_timer.png"))
		self.repeat_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/repeat_timer.png"))
		self.instant_record = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/instant_record.png"))
		self.zap_timer = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/zaptimer.png"))
		self.now = int(time())
		
	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]
	
	GUI_WIDGET = eListbox
	
	def postWidgetCreate(self, instance):
		instance.setContent(self.l)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	currentIndex = property(getCurrentIndex, moveToIndex)
	currentSelection = property(getCurrent)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def invalidate(self):
		self.l.invalidate()

	def entryRemoved(self, idx):
		self.l.entryRemoved(idx)

