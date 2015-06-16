# 2015.06.16 12:52:12 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/SetSkin.py


class setSkin():

    def setEyesight(self, patchtype):
        typeofpatch = patchtype
        ComponentsChoiceList = [('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 00, 800, 25, 0, RT_HALIGN_LEFT, "-"*200))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 00, 1200, 50, 0, RT_HALIGN_LEFT, "-"*200))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 45, 00, 800, 25, 0, RT_HALIGN_LEFT, text[0]))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 00, 1200, 50, 0, RT_HALIGN_LEFT, text[0]))'),
         ('res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 5, 0, 35, 25, png))', 'res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 0, 0, 0, png))'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 50))'),
         ('self.l.setItemHeight(25)', 'self.l.setItemHeight(70)')]
        ComponentsEpgList = [('self.l.setFont(0, gFont("Regular", 22))', 'self.l.setFont(0, gFont("Regular_eye", 72))'),
         ('self.l.setFont(1, gFont("Regular", 16))', 'self.l.setFont(1, gFont("Regular_eye", 72))'),
         ('(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),', '(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 70, clock_pic),'),
         ('(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),', '(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 72, clock_pic),'),
         ('(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-16, r1.top(), 21, 21, clock_pic)', '(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-16, r1.top(), 21, 70, clock_pic)')]
        ComponentsFileList = [('res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 50, 1, 900, 50, 0, RT_HALIGN_LEFT, name))'),
         ('self.l.setFont(0, gFont("Regular", 18))', 'self.l.setFont(0, gFont("Regular_eye", 40))'),
         ('self.l.setItemHeight(23)', 'self.l.setItemHeight(50)'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 1, 470, 20, 0, RT_HALIGN_LEFT, name))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 1, 900, 50, 0, RT_HALIGN_LEFT, name))'),
         ('self.l.setItemHeight(25)', 'self.l.setItemHeight(51)'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 41))')]
        ComponentsHelpMenuList = [('(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 400, 26, 0, 0, help[0]),', '(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 880, 50, 0, 0, help[0]),'),
         ('(eListboxPythonMultiContent.TYPE_TEXT, 0, 28, 400, 20, 1, 0, help[1])', '(eListboxPythonMultiContent.TYPE_TEXT, 0, 55, 880, 50, 1, 0, help[1])'),
         ('entry.append( (eListboxPythonMultiContent.TYPE_TEXT, 10, 4, 750, 28, 0, 0, help) )', 'entry.append( (eListboxPythonMultiContent.TYPE_TEXT, 10, 4, 880, 70, 0, 0, help) )'),
         ('self.l.setFont(0, gFont("Regular", 24))', 'self.l.setFont(0, gFont("Regular_eye", 50))'),
         ('self.l.setFont(1, gFont("Regular", 18))', 'self.l.setFont(1, gFont("Regular_eye", 40))'),
         ('self.l.setItemHeight(50)', 'self.l.setItemHeight(110)'),
         ('self.l.setFont(0, gFont("Regular", 24))', 'self.l.setFont(0, gFont("Regular_eye", 50))'),
         ('self.l.setItemHeight(38)', 'self.l.setItemHeight(70)')]
        ComponentsMovieList = [('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 50))'),
         ('self.l.setFont(1, gFont("Regular", 18))', 'self.l.setFont(1, gFont("Regular_eye", 50))'),
         ('self.l.setFont(2, gFont("Regular", 16))', 'self.l.setFont(2, gFont("Regular_eye", 40))'),
         ('self.l.setItemHeight(75)', 'self.l.setItemHeight(170)'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 51))'),
         ('self.l.setFont(1, gFont("Regular", 14))', 'self.l.setFont(1, gFont("Regular_eye", 49))'),
         ('self.l.setItemHeight(43)', 'self.l.setItemHeight(169)'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 51))'),
         ('self.l.setFont(1, gFont("Regular", 18))', 'self.l.setFont(1, gFont("Regular_eye", 50))'),
         ('self.l.setItemHeight(27)', 'self.l.setItemHeight(60)'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 51))'),
         ('self.l.setFont(1, gFont("Regular", 16))', 'self.l.setFont(1, gFont("Regular_eye", 48))'),
         ('self.l.setItemHeight(25)', 'self.l.setItemHeight(59)'),
         ('res.append(MultiContentEntryText(pos=(25, 0), size=(width-40, 30), font = 0, flags = RT_HALIGN_LEFT, text=serviceref.getName()))', 'res.append(MultiContentEntryText(pos=(25, 0), size=(width-40, 60), font = 0, flags = RT_HALIGN_LEFT, text=serviceref.getName()))'),
         ('res.append(MultiContentEntryText(pos=(0, 0), size=(width-182, 30), font = 0, flags = RT_HALIGN_LEFT, text=serviceref.getName()))', 'res.append(MultiContentEntryText(pos=(0, 0), size=(width-182, 60), font = 0, flags = RT_HALIGN_LEFT, text=serviceref.getName()))'),
         ('res.append(MultiContentEntryProgress(pos=(offset,7), size = (60,10), percent = last_end_point, borderWidth = 2, foreColor = color))', 'res.append(MultiContentEntryProgress(pos=(offset,15), size = (60,30), percent = last_end_point, borderWidth = 2, foreColor = color))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(60, 23), font = 0, flags = RT_HALIGN_LEFT, text=progress_string, color = color))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(60, 60), font = 0, flags = RT_HALIGN_LEFT, text=progress_string, color = color))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(width-182-offset, 30), font = 0, flags = RT_HALIGN_LEFT, color = color, text=txt))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(width-182-offset, 60), font = 0, flags = RT_HALIGN_LEFT, color = color, text=txt))'),
         ('res.append(MultiContentEntryText(pos=(width-180, 0), size=(180, 30), font = 2, flags = RT_HALIGN_RIGHT, text = tags))', 'res.append(MultiContentEntryText(pos=(width-400, 0), size=(400, 60), font = 1, flags = RT_HALIGN_RIGHT, text = tags))'),
         ('res.append(MultiContentEntryText(pos=(200, 50), size=(200, 20), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))', 'res.append(MultiContentEntryText(pos=(400, 80), size=(400, 51), font = 2, flags = RT_HALIGN_LEFT, text = service.getServiceName()))'),
         ('res.append(MultiContentEntryText(pos=(width-180, 0), size=(180, 30), font = 2, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))', 'res.append(MultiContentEntryText(pos=(width-400, 0), size=(400, 60), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))'),
         ('res.append(MultiContentEntryText(pos=(0, 30), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=description))', 'res.append(MultiContentEntryText(pos=(0, 50), size=(width, 60), font=2, flags=RT_HALIGN_LEFT, text=description))'),
         ('res.append(MultiContentEntryText(pos=(0, 50), size=(200, 20), font=1, flags=RT_HALIGN_LEFT, text=begin_string))', 'res.append(MultiContentEntryText(pos=(0, 100), size=(400, 60), font=1, flags=RT_HALIGN_LEFT, text=begin_string))'),
         ('res.append(MultiContentEntryText(pos=(width-200, 50), size=(198, 20), font=1, flags=RT_HALIGN_RIGHT, text=len))', 'res.append(MultiContentEntryText(pos=(width-400, 100), size=(400, 60), font=1, flags=RT_HALIGN_RIGHT, text=len))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(width-120-offset, 23), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(width-320-offset, 60), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))'),
         ('res.append(MultiContentEntryText(pos=(0, 25), size=(width-212, 17), font=1, flags=RT_HALIGN_LEFT, text=description))', 'res.append(MultiContentEntryText(pos=(0, 110), size=(width-412, 60), font=1, flags=RT_HALIGN_LEFT, text=description))'),
         ('res.append(MultiContentEntryText(pos=(width-120, 6), size=(120, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))', 'res.append(MultiContentEntryText(pos=(width-540, 0), size=(520, 60), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))'),
         ('res.append(MultiContentEntryText(pos=(width-212, 25), size=(154, 17), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))', 'res.append(MultiContentEntryText(pos=(width-474, 110), size=(454, 60), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))'),
         ('res.append(MultiContentEntryText(pos=(width-58, 25), size=(58, 20), font=1, flags=RT_HALIGN_RIGHT, text=len))', 'res.append(MultiContentEntryText(pos=(width-178, 60), size=(158, 60), font=1, flags=RT_HALIGN_RIGHT, text=len))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(width-77-offset, 23), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(width-77-offset, 60), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))'),
         ('res.append(MultiContentEntryText(pos=(width-200, 25), size=(200, 17), font = 1, flags = RT_HALIGN_RIGHT, text = tags))', 'res.append(MultiContentEntryText(pos=(width-420, 60), size=(400, 60), font = 1, flags = RT_HALIGN_RIGHT, text = tags))'),
         ('res.append(MultiContentEntryText(pos=(200, 25), size=(200, 17), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))', 'res.append(MultiContentEntryText(pos=(200, 60), size=(400, 60), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))'),
         ('res.append(MultiContentEntryText(pos=(width-200, 25), size=(200, 17), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))', 'res.append(MultiContentEntryText(pos=(width-420, 60), size=(400, 60), font = 1, flags = RT_HALIGN_RIGHT, text = service.getServiceName()))'),
         ('res.append(MultiContentEntryText(pos=(0, 25), size=(200, 17), font=1, flags=RT_HALIGN_LEFT, text=begin_string))', 'res.append(MultiContentEntryText(pos=(0, 60), size=(400, 60), font=1, flags=RT_HALIGN_LEFT, text=begin_string))'),
         ('res.append(MultiContentEntryText(pos=(width-75, 0), size=(75, 22), font=0, flags=RT_HALIGN_RIGHT, text=len))', 'res.append(MultiContentEntryText(pos=(width-195, 0), size=(175, 60), font=0, flags=RT_HALIGN_RIGHT, text=len))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(width-146-75-offset-115, 23), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(width-346-75-offset-115, 60), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))'),
         ('res.append(MultiContentEntryText(pos=(width-220, 4), size=(145, 22), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))', 'res.append(MultiContentEntryText(pos=(width-520, 4), size=(0, 0), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))'),
         ('res.append(MultiContentEntryText(pos=(width-80, 4), size=(75, 22), font=1, flags=RT_HALIGN_RIGHT, text=len))', 'res.append(MultiContentEntryText(pos=(width-180, 4), size=(175, 60), font=1, flags=RT_HALIGN_RIGHT, text=len))'),
         ('res.append(MultiContentEntryText(pos=(width-320, 4), size=(105, 22), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))', 'res.append(MultiContentEntryText(pos=(width-520, 4), size=(375, 60), font = 1, flags = RT_HALIGN_LEFT, text = service.getServiceName()))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(width-146-offset, 23), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(width-146-offset, 60), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))'),
         ('res.append(MultiContentEntryText(pos=(width-145, 4), size=(145, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))', 'res.append(MultiContentEntryText(pos=(width-345, 0), size=(345, 60), font=1, flags=RT_HALIGN_RIGHT, text=begin_string))'),
         ('res.append(MultiContentEntryText(pos=(offset, 0), size=(width-77-offset, 23), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))', 'res.append(MultiContentEntryText(pos=(offset, 0), size=(width-77-offset, 60), font = 0, flags = RT_HALIGN_LEFT, color = color, text = txt))'),
         ('res.append(MultiContentEntryText(pos=(width-75, 0), size=(75, 20), font=0, flags=RT_HALIGN_RIGHT, text=len))', 'res.append(MultiContentEntryText(pos=(width-275, 0), size=(275, 60), font=0, flags=RT_HALIGN_RIGHT, text=len))')]
        ComponentsPluginList = [('MultiContentEntryText(pos=(120, 5), size=(700, 25), font=0, text=plugin.name),', 'MultiContentEntryText(pos=(120, 5), size=(900, 55), font=0, text=plugin.name),'),
         ('MultiContentEntryText(pos=(120, 26), size=(700, 17), font=1, text=plugin.description),', 'MultiContentEntryText(pos=(120, 55), size=(900, 45), font=1, text=plugin.description),'),
         ('MultiContentEntryText(pos=(120, 5), size=(700, 25), font=0, text=name),', 'MultiContentEntryText(pos=(120, 5), size=(900, 55), font=0, text=name),'),
         ('MultiContentEntryText(pos=(120, 5), size=(700, 25), font=0, text=name),', 'MultiContentEntryText(pos=(120, 5), size=(900, 55), font=0, text=name),'),
         ('MultiContentEntryText(pos=(120, 26), size=(700, 17), font=1, text=plugin.description),', 'MultiContentEntryText(pos=(120, 55), size=(900, 45), font=1, text=plugin.description),'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 50))'),
         ('self.l.setFont(1, gFont("Regular", 14))', 'self.l.setFont(1, gFont("Regular_eye", 40))'),
         ('self.l.setItemHeight(50)', 'self.l.setItemHeight(110)')]
        ComponentsServiceList = [('pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/marker.png"))', 'pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/marker_eye.png"))'),
         ('self.ItemHeight = 60', 'self.ItemHeight = 130'),
         ('self.l.setElementPosition(self.l.celServiceTypePixmap, eRect(picon_width + offset, 0, 30, 30))', 'self.l.setElementPosition(self.l.celServiceTypePixmap, eRect(picon_width -5, 15, 100, 60))'),
         ('self.l.setElementPosition(self.l.celServiceNumber, eRect(picon_width, service_number_offset_y, 50, self.ItemHeight))', 'self.l.setElementPosition(self.l.celServiceNumber, eRect(15, 80, 80, self.ItemHeight))'),
         ('self.l.setElementPosition(self.l.celRecordServicePixmap, eRect(picon_width + offset + service_type_pix_offset, 0, 30, 30))', 'self.l.setElementPosition(self.l.celRecordServicePixmap, eRect(picon_width + offset + service_type_pix_offset, 20, 30, 30))'),
         ('self.l.setElementPosition(self.l.celServiceTypePixmap, eRect(picon_width + service_number_offset, 0, 30, 30))', 'self.l.setElementPosition(self.l.celServiceTypePixmap, eRect(picon_width -5, 0, 100, 30))'),
         ('self.l.setElementPosition(self.l.celRecordServicePixmap, eRect(picon_width + service_number_offset + service_type_pix_offset + progress_bar_offset, 0, 30, 30))', 'self.l.setElementPosition(self.l.celRecordServicePixmap, eRect(picon_width + service_number_offset + service_type_pix_offset + progress_bar_offset, 60, 30, 30))')]
        ComponentsTimerList = [('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.service_ref.getServiceName()))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, 100, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.service_ref.getServiceName()))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 30, width, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.name))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 150, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.name))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, width-150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.begin)[1]))))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 250, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.begin)[1]))))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, width-150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60)) + _("(ZAP)")))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 250, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60)) + _("(ZAP)")))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, width-150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60))))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 250, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin)[1], FuzzyTime(timer.end)[1], (timer.end - timer.begin) / 60))))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, width-150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s " + _("(ZAP)")) % (FuzzyTime(timer.begin)))))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 250, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s " + _("(ZAP)")) % (FuzzyTime(timer.begin)))))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, width-150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,))) + _("(ZAP)")))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 250, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,))) + _("(ZAP)")))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, width-150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,)))))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 250, width, 85, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.begin) + FuzzyTime(timer.end)[1:] + ((timer.end - timer.begin) / 60,)))))'),
         ('res.append((eListboxPythonMultiContent.TYPE_TEXT, width-150, 50, 150, 20, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, state))', 'res.append((eListboxPythonMultiContent.TYPE_TEXT, width-500, 5, 490, 85, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, state))'),
         ('res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 490, 5, 40, 40, png))', 'res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, width-500, 5, 85, 85, png))'),
         ('self.l.setFont(0, gFont("Regular", 20))', 'self.l.setFont(0, gFont("Regular_eye", 72))'),
         ('self.l.setFont(1, gFont("Regular", 18))', 'self.l.setFont(1, gFont("Regular_eye", 72))'),
         ('self.l.setItemHeight(70)', 'self.l.setItemHeight(350)')]
        ScreensMovieSelection = [('from Components.UsageConfig import defaultMoviePath', 'from Components.UsageConfig import defaultMoviePath\nfrom Components.Sources.List import List'), ('self["menu"] = MenuList(menu)', 'self["menu"] = List(menu)')]
        ScreensServiceInfo = [('(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 200, 30, 0, RT_HALIGN_LEFT, ""),', '(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 600, 70, 0, RT_HALIGN_LEFT, ""),'),
         ('(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 200, 25, 0, RT_HALIGN_LEFT, a),', '(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 600, 70, 0, RT_HALIGN_LEFT, a),'),
         ('(eListboxPythonMultiContent.TYPE_TEXT, 220, 0, 350, 25, 0, RT_HALIGN_LEFT, b)', '(eListboxPythonMultiContent.TYPE_TEXT, 620, 0, 600, 70, 0, RT_HALIGN_LEFT, b)'),
         ('self.l.setFont(0, gFont("Regular", 23))', 'self.l.setFont(0, gFont("Regular_eye", 50))'),
         ('self.l.setItemHeight(25)', 'self.l.setItemHeight(70)')]
        ComponentsFiles = ['Components/ChoiceList',
         'Components/EpgList',
         'Components/FileList',
         'Components/HelpMenuList',
         'Components/MovieList',
         'Components/PluginList',
         'Components/ServiceList',
         'Components/TimerList',
         'Screens/ServiceInfo',
         'Screens/MovieSelection']
        for componentfile in ComponentsFiles:
            filetopatch = '/usr/lib/enigma2/python/' + componentfile + '.py'
            filepatched = filetopatch
            patch = open(filetopatch, 'r')
            text = patch.read()
            patch.close()
            if componentfile == 'Components/ChoiceList':
                ComponentsList = ComponentsChoiceList
            elif componentfile == 'Components/EpgList':
                ComponentsList = ComponentsEpgList
            elif componentfile == 'Components/FileList':
                ComponentsList = ComponentsFileList
            elif componentfile == 'Components/HelpMenuList':
                ComponentsList = ComponentsHelpMenuList
            elif componentfile == 'Components/MovieList':
                ComponentsList = ComponentsMovieList
            elif componentfile == 'Components/PluginList':
                ComponentsList = ComponentsPluginList
            elif componentfile == 'Components/ServiceList':
                ComponentsList = ComponentsServiceList
            elif componentfile == 'Components/TimerList':
                ComponentsList = ComponentsTimerList
            elif componentfile == 'Screens/ServiceInfo':
                ComponentsList = ScreensServiceInfo
            elif componentfile == 'Screens/MovieSelection':
                ComponentsList = ScreensMovieSelection
            for textpart in ComponentsList:
                if typeofpatch == 'special':
                    textoriginal = textpart[0]
                    textreplace = textpart[1]
                else:
                    textoriginal = textpart[1]
                    textreplace = textpart[0]
                text = text.replace(textoriginal, textreplace)

            writepatch = open(filepatched, 'w')
            writepatch.write(text)
            writepatch.close()


setskin = setSkin()
