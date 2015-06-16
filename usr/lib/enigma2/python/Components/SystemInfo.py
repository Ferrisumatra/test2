from enigma import eDVBResourceManager
from Tools.Directories import fileExists
from Tools.HardwareInfo import HardwareInfo
from Tools.HardwareInfoVu import HardwareInfoVu

SystemInfo = { }

#FIXMEE...
def getNumVideoDecoders():
	idx = 0
	while fileExists("/dev/dvb/adapter0/video%d"%(idx), 'f'):
		idx += 1
	return idx

SystemInfo["NumVideoDecoders"] = getNumVideoDecoders()
SystemInfo["CanMeasureFrontendInputPower"] = eDVBResourceManager.getInstance().canMeasureFrontendInputPower()


def countFrontpanelLEDs():
	leds = 0
	if fileExists("/proc/stb/fp/led_set_pattern"):
		leds += 1

	while fileExists("/proc/stb/fp/led%d_pattern" % leds):
		leds += 1

	return leds

SystemInfo["NumFrontpanelLEDs"] = countFrontpanelLEDs()
SystemInfo["FrontpanelDisplay"] = fileExists("/dev/dbox/oled0") or fileExists("/dev/dbox/lcd0")
SystemInfo["FrontpanelDisplayGrayscale"] = fileExists("/dev/dbox/oled0")
SystemInfo["DeepstandbySupport"] = HardwareInfo().get_device_name() != "dm800"
SystemInfo["GraphicVFD"] = HardwareInfoVu().get_device_name() == "ultimo" or HardwareInfoVu().get_device_name() == "duo2"
SystemInfo["HasHbbTV"] = fileExists("/usr/lib/enigma2/python/Plugins/Extensions/HbbTV/plugin.py") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/HbbTV/plugin.pyo")
SystemInfo["CanPiP"] = getNumVideoDecoders() > 1
SystemInfo["Can3DSurround"] = fileExists("/proc/stb/audio/3d_surround_choices")
SystemInfo["CanSpeakerPosition"] = fileExists("/proc/stb/audio/3d_surround_speaker_position_choices")
SystemInfo["CanAVL"] = fileExists("/proc/stb/audio/avl_choices")
SystemInfo["CanDownmixAC3"] = fileExists("/proc/stb/audio/ac3_choices")
# disable AAC downmix for now, has to be converted to AC3 in passthrough mode
SystemInfo["CanDownmixAAC"] = False #fileExists("/proc/stb/audio/aac_choices")
SystemInfo["CanMultiChannelPCM"] = fileExists("/proc/stb/audio/multichannel_pcm")
SystemInfo["Support3DUI"] = HardwareInfoVu().get_device_name() in ("solo2", "duo2", "solose")
