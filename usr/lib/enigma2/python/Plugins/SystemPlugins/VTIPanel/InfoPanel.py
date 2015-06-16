# 2015.06.16 12:25:13 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/InfoPanel.py
from enigma import eTimer
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Console import Console
from Components.Sources.List import List
from Tools.Bytes2Human import bytes2human
from Screens.Screen import Screen
from skin import loadSkin
from __init__ import _
import os

def getVTiVersion():
    from enigma import getVTiVersionString
    vtiversion = 'VTi ' + getVTiVersionString()
    return vtiversion


def getSize(device, space_type_full):
    stat_info = os.statvfs(device)
    if space_type_full:
        size = stat_info.f_blocks * stat_info.f_bsize
    else:
        size = (stat_info.f_bavail or stat_info.f_bfree) * stat_info.f_bsize
    size = bytes2human(size)
    return size


def getMounts():
    if os.path.exists('/media/net/autofs'):
        for dir in os.listdir('/media/net/autofs'):
            autofs_dir = '/media/net/autofs/' + dir
            if os.path.exists(autofs_dir):
                try:
                    os.listdir(autofs_dir)
                except OSError:
                    print '[VTiPanel] OSError during dir listing'

    proc_mounts = '/proc/mounts'
    device_exclude = ('rootfs', 'devtmpfs', 'proc', 'sysfs', 'udev', 'devpts', 'usbdevfs', 'tmpfs', '/dev/mtdblock2')
    device_list = []
    with open(proc_mounts, 'r') as f:
        for line in f:
            line = line.strip()
            device = line.split()
            if len(device) >= 3 and device[0] not in device_exclude and device[2] != 'autofs':
                free_size = getSize(device[1], False)
                full_size = getSize(device[1], True)
                device.extend((full_size, free_size))
                device_list.append(device)

    return device_list


def getUptime():
    from datetime import timedelta
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_string = str(timedelta(seconds=uptime_seconds))
    return uptime_string


def getLoad():
    load = os.getloadavg()
    load = '%s / %s / %s' % (load[0], load[1], load[2])
    return load


def getKernel():
    with open('/proc/version', 'r') as f:
        kernel = f.readline().split()
        kernel = '%s - %s' % (kernel[2], kernel[3])
    return kernel


def getTemp():
    myfile = '/proc/stb/sensors/temp0/value'
    if os.path.exists(myfile):
        with open(myfile, 'r') as f:
            text = f.read().strip()
        return text
    else:
        return


def getFan():
    myfile = '/proc/stb/fp/fan_speed'
    if os.path.exists(myfile):
        with open(myfile, 'r') as f:
            text = f.read().strip()
        return text
    else:
        return


def getMemory():
    with open('/proc/meminfo', 'r') as f:
        tmp = []
        for line in f:
            line = line.strip().split()
            if line[0] == 'MemTotal:':
                tmp_mem = float(line[1])
                tmp.append(tmp_mem)
            if line[0] == 'MemFree:':
                tmp_mem = float(line[1])
                tmp_mem_u = tmp[0] - tmp_mem
                tmp.extend((tmp_mem_u, tmp_mem))
            if line[0] == 'SwapTotal:':
                tmp_mem = float(line[1])
                tmp.append(tmp_mem)
            if line[0] == 'SwapFree:':
                tmp_mem = float(line[1])
                tmp_mem_u = tmp[3] - tmp_mem
                tmp.extend((tmp_mem_u, tmp_mem))
                break

    mem = []
    for value in tmp:
        value = str(round(value / 1024.0, 2)) + ' MB'
        mem.append(value)

    return mem


def getNetwork():
    netlist = []
    with open('/proc/net/dev', 'r') as f:
        for line in f:
            line = line.split()
            if len(line) >= 17 and line[0].endswith(':') and line[0] != 'lo:':
                print 'Line', line[1], line[9]
                netlist.append((line[0].rstrip(':'), bytes2human(int(line[1])), bytes2human(int(line[9]))))

    return netlist


class InfoPanel(Screen):

    def __init__(self, session, plugin_path):
        self.skin_path = plugin_path
        Screen.__init__(self, session)
        self.session = session
        self.title = 'VTi Info'
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.storagedevices = []
        self['storagelist'] = List(self.storagedevices)
        memorylist = []
        self['memory'] = List(memorylist)
        netdevlist = []
        self['netdev'] = List(netdevlist)
        toplist = []
        self['proclist'] = List(toplist)
        self.isopen = True
        self._initialpoll = True
        self.console = Console()
        self.pollProcList()
        self['vtiversion'] = Label()
        self['uptime'] = Label()
        self['load'] = Label()
        self['temp'] = Label()
        self['fan'] = Label()
        self['kernel'] = Label()
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Screenshot'))
        self['shortcuts'] = ActionMap(['OkCancelActions', 'ColorActions'], {'red': self.keyClose,
         'green': self.grabScreenshot,
         'ok': self.keyClose,
         'cancel': self.keyClose}, -2)
        self.onLayoutFinish.append(self.createInfo)

    def pollProcList(self):
        cmd = 'top -b -n1'
        self.console.ePopen(cmd, self.createProcList)

    def createProcList(self, result, retval, extra_args = None):
        if retval == 0:
            self._initialpoll = False
            if len(result):
                toplist = []
                proclist = result.split('\n')[7:][:5]
                toplist.append((_('PROCESS'),
                 _('CPU %'),
                 _('MEM %'),
                 _('PID')))
                for proc in proclist:
                    proc = proc.split()
                    if len(proc) >= 12:
                        toplist.append((str(proc[11]),
                         str(proc[8]),
                         str(proc[9]),
                         str(proc[0])))

                self['proclist'].setList(toplist)

    def createInfo(self):
        devices = getMounts()
        self.storagedevices.append((_('DEVICE'),
         _('MOUNTPOINT'),
         _('FS'),
         _('SIZE'),
         _('FREE')))
        for device in devices:
            user_friendly_device_name = device[0]
            if user_friendly_device_name == 'ubi0:rootfs':
                user_friendly_device_name = 'Flash'
            self.storagedevices.append((user_friendly_device_name,
             device[1],
             device[2],
             device[6],
             device[7]))

        self['storagelist'].setList(self.storagedevices)
        msg = _('KERNEL : ') + getKernel()
        self['kernel'].setText(msg)
        msg = _('IMAGE : ') + getVTiVersion()
        self['vtiversion'].setText(msg)
        self.updateValues()
        self.slowRefresh()

    def updateValues(self):
        memory = getMemory()
        memorylist = []
        memorylist.append(('', _('RAM'), _('SWAP')))
        memorylist.append((_('USED :'), memory[1], memory[4]))
        memorylist.append((_('FREE :'), memory[2], memory[5]))
        memorylist.append((_('TOTAL :'), memory[0], memory[3]))
        self['memory'].setList(memorylist)
        msg = _('UPTIME : ') + getUptime()
        self['uptime'].setText(msg)
        msg = _('LOAD : ') + getLoad()
        self['load'].setText(msg)
        text = getTemp()
        if text:
            msg = _('TEMP : ') + getTemp() + ' C'
            self['temp'].setText(msg)
        text = getFan()
        if text:
            msg = _('FAN : ') + getFan()
            self['fan'].setText(msg)
        if not self._initialpoll:
            self.pollProcList()
        self.updateTimer = eTimer()
        self.updateTimer.start(5000, True)
        self.updateTimer.callback.append(self.updateValues)

    def slowRefresh(self):
        netdevs = getNetwork()
        netdevlist = []
        netdevlist.append((_('DEVICE'), _('RECEIVED'), _('SENT')))
        for device in netdevs:
            netdevlist.append((device[0], device[1], device[2]))

        self['netdev'].setList(netdevlist)
        self.slow_updateTimer = eTimer()
        self.slow_updateTimer.start(10000, True)
        self.slow_updateTimer.callback.append(self.slowRefresh)

    def grabScreenshot(self):
        self['key_green'].setText('')
        from datetime import datetime
        from time import time as systime
        now = systime()
        now = datetime.fromtimestamp(now)
        now = now.strftime('%Y-%m-%d_%H-%M-%S')
        filename = '/media/hdd/vti_screenshot_sysinfo_' + now + '.png'
        cmd = 'grab -po %s' % filename
        self.console.ePopen(cmd, self.screenshotFinished)

    def screenshotFinished(self, result, retval, extra_args = None):
        self['key_green'].setText(_('Screenshot'))

    def keyClose(self):
        if self.console is not None:
            if len(self.console.appContainers):
                for name in self.console.appContainers.keys():
                    self.console.kill(name)

        self.close()
