from MenuList import MenuList
import skin
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest

from enigma import eListboxPythonMultiContent, gFont
from Tools.LoadPixmap import LoadPixmap

def PluginEntryComponent(plugin):
	
		if plugin.icon is None:
			png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
		else:
			png = plugin.icon
		x,y,w,h = skin.parameters.get("PluginListName", (120,5,700,25))
		x1,y1,w1,h1 = skin.parameters.get("PluginListDescription", (120,26,700,17))
		x2,y2,w2,h2 = skin.parameters.get("PluginListIcon", (10,5,100,40))

		return [
			plugin,
			MultiContentEntryText(pos=(x, y), size=(w, h), font=0, text=plugin.name),
			MultiContentEntryText(pos=(x1, y1), size=(w1, h1), font=1, text=plugin.description),
			MultiContentEntryPixmapAlphaTest(pos=(x2, y2), size=(w2, h2), png = png)
		]
	

def PluginCategoryComponent(name, png):
	x,y,w,h = skin.parameters.get("PluginListCategoryName", (120,5,700,25))
	x1,y1,w1,h1 = skin.parameters.get("PluginListCategoryIcon", (10,0,100,50))
	return [
			name,
			MultiContentEntryText(pos=(120, 5), size=(700, 25), font=0, text=name),
			MultiContentEntryPixmapAlphaTest(pos=(10, 0), size=(100, 50), png = png)
		]
	

def PluginDownloadComponent(plugin, name):
	if plugin.icon is None:
		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
	else:
		png = plugin.icon
	
	x,y,w,h = skin.parameters.get("PluginListDownloadName", (120,5,700,25))
	x1,y1,w1,h1 = skin.parameters.get("PluginListDownloadDescription", (120,26,700,17))
	x2,y2,w2,h2 = skin.parameters.get("PluginListDownloadIcon", (10,0,100,50))
	return [
			plugin,
			MultiContentEntryText(pos=(x, y), size=(w, h), font=0, text=name),
			MultiContentEntryText(pos=(x1, y1), size=(w1, h1), font=1, text=plugin.description),
			MultiContentEntryPixmapAlphaTest(pos=(x2, y2), size=(w2, h2), png = png)
		]
	
	

class PluginList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font, size = skin.parameters.get("PluginListFont1", ('Regular', 20))
		self.l.setFont(0, gFont(font, size))
		font, size = skin.parameters.get("PluginListFont2", ('Regular', 14))
		self.l.setFont(1, gFont(font, size))
		self.l.setItemHeight(int(skin.parameters.get("PluginListItemHeight", (50,))[0]))
