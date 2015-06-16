from GUIComponent import GUIComponent
from VariableText import VariableText
from os import statvfs

from enigma import eLabel
from Tools.Bytes2Human import bytes2human

# TODO: Harddisk.py has similiar functions, but only similiar.
# fix this to use same code
class DiskInfo(VariableText, GUIComponent):
	FREE = 0
	USED = 1
	TOTAL = 2
	COMBINED = 3
	
	def __init__(self, path, type, update = True):
		GUIComponent.__init__(self)
		VariableText.__init__(self)
		self.type = type
		self.path = path
		if update:
			self.update()

	def update(self):
		try:
			stat = statvfs(self.path)
		except OSError:
			return -1
		if self.type == self.FREE:
			free = (stat.f_bavail or stat.f_bfree) * stat.f_bsize
			self.setText(("%s "  + _("free diskspace")) % bytes2human(free, 1))
		elif self.type == self.USED:
			total = stat.f_blocks * stat.f_bsize
			free = (stat.f_bavail or stat.f_bfree) * stat.f_bsize
			used = total - free
			self.setText(("%s "  + _("used diskspace")) % bytes2human(used, 1))
		elif self.type == self.TOTAL:
			total = stat.f_blocks * stat.f_bsize
			self.setText(("%s "  + _("total diskspace")) % bytes2human(total, 1))
		elif self.type == self.COMBINED:
			total = stat.f_blocks * stat.f_bsize
			free = (stat.f_bavail or stat.f_bfree) * stat.f_bsize
			if total == 0:
				total = 1
			percentage = free *100 / total
			self.setText(("%s / %s (%d%%) "  + _("free diskspace")) % (bytes2human(free, 1), bytes2human(total, 1), percentage))

	GUI_WIDGET = eLabel
