from MenuList import MenuList
from Components.ParentalControl import IMG_WHITESERVICE, IMG_WHITEBOUQUET, IMG_BLACKSERVICE, IMG_BLACKBOUQUET
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT
from Tools.LoadPixmap import LoadPixmap
import skin

#Now there is a list of pictures instead of one...
entryPicture = {}

entryPicture[IMG_BLACKSERVICE] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock.png"))
entryPicture[IMG_BLACKBOUQUET] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lockBouquet.png"))
entryPicture[IMG_WHITESERVICE] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/unlock.png"))
entryPicture[IMG_WHITEBOUQUET] = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/unlockBouquet.png"))

def ParentalControlEntryComponent(service, name, protectionType):
	locked = protectionType[0]
	sImage = protectionType[1]
	x,y,w,h = skin.parameters.get("ParentalControlListText", (80,5,300,50))
	res = [
		(service, name, locked),
		(eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT, name)
	]
	#Changed logic: The image is defined by sImage, not by locked anymore
	if sImage != "":
		x,y,w,h = skin.parameters.get("ParentalControlListPic", (0,0,32,32))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, entryPicture[sImage]))
	return res

class ParentalControlList(MenuList):
	def __init__(self, list, enableWrapAround = False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font, size = skin.parameters.get("ParentalControlListFont", ('Regular', 20))
		self.l.setFont(0, gFont(font, size))
		self.l.setItemHeight(int(skin.parameters.get("ParentalControlListItemHeight", (32,))[0]))

	def toggleSelectedLock(self):
		from Components.ParentalControl import parentalControl
		print "self.l.getCurrentSelection():", self.l.getCurrentSelection()
		print "self.l.getCurrentSelectionIndex():", self.l.getCurrentSelectionIndex()
		curSel = self.l.getCurrentSelection()
		if curSel[0][2]:
			parentalControl.unProtectService(self.l.getCurrentSelection()[0][0])
		else:
			parentalControl.protectService(self.l.getCurrentSelection()[0][0])
		#Instead of just negating the locked- flag, now I call the getProtectionType every time...
		self.list[self.l.getCurrentSelectionIndex()] = ParentalControlEntryComponent(curSel[0][0], curSel[0][1], parentalControl.getProtectionType(curSel[0][0]))
		self.l.setList(self.list)
