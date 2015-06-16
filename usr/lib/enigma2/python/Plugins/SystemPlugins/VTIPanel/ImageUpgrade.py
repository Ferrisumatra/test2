# 2015.06.16 12:45:42 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/ImageUpgrade.py
from enigma import eTimer
from BackupRestore import BackupRestoreScreen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.config import config, ConfigSelection
from Components.FileList import FileList
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.MenuList import MenuList
from Components.Console import Console as ComConsole
from Components.Sources.List import List
from Components.Task import Task, Job, job_manager
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Tools.Directories import *
from Tools.Downloader import downloadWithProgress
from Tools.HardwareInfoVu import HardwareInfoVu
from Tools.LoadPixmap import LoadPixmap
from skin import loadSkin
import urllib2
import hashlib
import os
from __init__ import _

def getDeviceName():
    hwdevice = HardwareInfoVu().get_device_name()
    if hwdevice == 'duo':
        return 'bm750'
    elif hwdevice == 'solo':
        return 'vusolo'
    elif hwdevice == 'uno':
        return 'vuuno'
    elif hwdevice == 'ultimo':
        return 'vuultimo'
    elif hwdevice == 'solo2':
        return 'vusolo2'
    elif hwdevice == 'duo2':
        return 'vuduo2'
    elif hwdevice == 'solose':
        return 'vusolose'
    elif hwdevice == 'zero':
        return 'vuzero'
    else:
        return 'noDevice'


def check_download_dir(path):
    download_dir_name = 'vti-image-download'
    path = os.path.realpath(path)
    statvfs = os.statvfs(path)
    free = statvfs.f_frsize * statvfs.f_bavail / 1048576
    if free < 500:
        return 'size'
    if path.endswith('/'):
        path = path + download_dir_name
    else:
        path = path + '/' + download_dir_name
    if not fileExists(path):
        try:
            os.makedirs(path)
        except OSError:
            pass

    if fileExists(path, mode='w'):
        return path
    else:
        return 'error'


def check_flash_files(path):
    hwdevice = HardwareInfoVu().get_device_name()
    if path.endswith('/'):
        path = path + 'vuplus/' + hwdevice + '/'
    else:
        path = path + '/vuplus/' + hwdevice + '/'
    if hwdevice in ('duo', 'solo', 'uno', 'ultimo'):
        if fileExists(path + 'kernel_cfe_auto.bin') and fileExists(path + 'root_cfe_auto.jffs2'):
            return True
    elif hwdevice in ('solo2', 'duo2', 'solose', 'zero'):
        if fileExists(path + 'kernel_cfe_auto.bin') and fileExists(path + 'root_cfe_auto.bin'):
            return True
    return False


def image_url():
    f = open('/etc/opkg/all-feed.conf', 'r')
    text_file = f.readline().strip('src/gz VTi-all ')
    f.close()
    text_file = text_file.strip()
    text_file = text_file.replace('all', 'image_download/vti_image.download')
    return text_file


def parse_download_file():
    list = []
    download_list = image_url()
    try:
        downloads = urllib2.urlopen(download_list, None, 5.0).read()
        downloads = downloads.split('\n')
    except urllib2.HTTPError:
        return (2, None)
    except urllib2.URLError:
        return (3, None)

    for line in downloads:
        if not line.startswith('#'):
            line = line.split(':::')
            if line and len(line) == 3:
                list.append((line[0], line[1], line[2]))

    return (0, list)


def parse_md5sum_file(url):
    try:
        md5sum = urllib2.urlopen(url, None, 5.0).read().strip()
    except urllib2.HTTPError:
        return
    except urllib2.URLError:
        return

    return md5sum


def get_md5_hash(file_name):
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    if fileExists(file_name):
        with open(file_name, 'rb') as f:
            buf = f.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(BLOCKSIZE)

    else:
        return
    md5_sum = hasher.hexdigest()
    return md5_sum


class downloadJob(Job):

    def __init__(self, url, file, title):
        Job.__init__(self, title)
        self.download_file = file
        self.download_job = downloadTask(self, url, self.download_file)

    def abort(self):
        self.download_job.stop()
        if os.path.exists(self.download_file):
            os.remove(self.download_file)


class downloadTask(Task):

    def __init__(self, job, url, file):
        Task.__init__(self, job, 'download task')
        self.end = 100
        self.url = url
        self.local = file

    def prepare(self):
        self.error = None

    def run(self, callback):
        self.callback = callback
        self.download = downloadWithProgress(self.url, self.local)
        self.download.addProgress(self.http_progress)
        self.download.start().addCallback(self.http_finished).addErrback(self.http_failed)

    def stop(self):
        self.download.stop()

    def http_progress(self, recvbytes, totalbytes):
        self.progress = int(self.end * recvbytes / float(totalbytes))

    def http_finished(self, string = ''):
        Task.processFinished(self, 0)

    def http_failed(self, failure_instance = None, error_message = ''):
        if error_message == '' and failure_instance is not None:
            error_message = failure_instance.getErrorMessage()
            Task.processFinished(self, 1)


class DownloadTaskScreen(Screen):

    def __init__(self, session, plugin_path, tasklist, job_name):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.session = session
        self.skinName = ['ImageDownload', 'TaskListScreen']
        self.tasklist = tasklist
        self.job_name = job_name
        self['tasklist'] = List(self.tasklist)
        self['shortcuts'] = ActionMap(['SetupActions'], {'ok': self.keyCancel,
         'cancel': self.keyCancel,
         'red': self.keyCancel}, -1)
        self['key_red'] = Button(_('Cancel'))
        self['title'] = Label()
        self.onLayoutFinish.append(self.layoutFinished)
        self.onShown.append(self.setWindowTitle)
        self.onClose.append(self.__onClose)
        self.Timer = eTimer()
        self.Timer.callback.append(self.TimerFire)

    def __onClose(self):
        del self.Timer

    def layoutFinished(self):
        self['title'].setText(_('VTi Image Download'))
        self.Timer.startLongTimer(2)

    def TimerFire(self):
        self.Timer.stop()
        self.rebuildTaskList()

    def rebuildTaskList(self):
        self.tasklist = []
        for job in job_manager.getPendingJobs():
            if self.job_name == job.name:
                self.tasklist.append((job,
                 job.name,
                 job.getStatustext(),
                 int(100 * job.progress / float(job.end)),
                 str(100 * job.progress / float(job.end)) + '%'))

        if len(self.tasklist):
            self['tasklist'].setList(self.tasklist)
            self['tasklist'].updateList(self.tasklist)
            self.Timer.startLongTimer(2)
        else:
            self.close(True)

    def setWindowTitle(self):
        self.setTitle(_('VTi Image Download'))

    def keyCancel(self):
        self.session.openWithCallback(self.cancelConfirmed, MessageBox, _('Do your really want to cancel the image download ?'), MessageBox.TYPE_YESNO, default=False)

    def cancelConfirmed(self, res):
        if res:
            current = self['tasklist'].getCurrent()
            if current:
                job = current[0]
                job.abort()
                self.close(False)


class ImageFileSelector(Screen):

    def __init__(self, session, initDir, plugin_path):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.skinName = ['ImageFileSelector', 'DriverManagerFile']
        self['filelist'] = FileList(initDir, showFiles=False, inhibitMounts=False, inhibitDirs=False, showMountpoints=False)
        self['driverfile'] = Label()
        self['actions'] = ActionMap(['WizardActions',
         'DirectionActions',
         'ColorActions',
         'EPGSelectActions'], {'back': self.cancel,
         'left': self.left,
         'right': self.right,
         'up': self.up,
         'down': self.down,
         'ok': self.ok,
         'green': self.green,
         'red': self.cancel}, -1)
        self.title = _('Select image for flash process')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText('')

    def cancel(self):
        self.close(None)

    def green(self):
        folder = self['filelist'].getFilename()
        if check_flash_files(folder) and not self.is_first_entry():
            self.close(folder)
        else:
            self['driverfile'].setText(_('Invalid Choice'))

    def up(self):
        self['filelist'].up()
        self.updateFile()

    def down(self):
        self['filelist'].down()
        self.updateFile()

    def left(self):
        self['filelist'].pageUp()
        self.updateFile()

    def right(self):
        self['filelist'].pageDown()
        self.updateFile()

    def ok(self):
        if self['filelist'].canDescent():
            self['filelist'].descent()
            self.updateFile()

    def is_first_entry(self):
        if self['filelist'].getSelection() == self['filelist'].getFileList()[0][0]:
            return True
        else:
            return False

    def updateFile(self):
        self['driverfile'].setText('')
        self['key_green'].setText('')
        currFolder = self['filelist'].getSelection()[0]
        if self['filelist'].getFilename() is not None:
            filename = self['filelist'].getFilename()
            if filename.endswith('/') and check_flash_files(filename):
                if not self.is_first_entry():
                    self['driverfile'].setText(_('Install this image'))
                    self['key_green'].setText(_('Ok'))


class ImageDownload(Screen):

    def __init__(self, session, plugin_path):
        Screen.__init__(self, session)
        self.skinName = ['ImageDownload', 'DriverManagerDownload']
        self.skin_path = plugin_path
        self.session = session
        self.title = _('VTI Image Flash Tool')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self.list = []
        self.list.append((None,
         _('Please wait ...'),
         _(' downloading available image information'),
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
         None))
        self['downloadmenu'] = List(self.list)
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Ok'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'DirectionActions'], {'ok': self.keyOk,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keyOk}, -2)
        self.Console = ComConsole()
        self.vudevice = getDeviceName()
        self.onLayoutFinish.append(self.init_vars)

    def init_vars(self):
        self.messagebox_title = 'VTi Image Flash Tool'
        self.is_file_list = False
        self.file_name = None
        self.image_url = None
        self.image_name = None
        self.path = None
        self.is_menu_blocked = None
        self.getImageList()

    def getImageList(self):
        self.list = []
        result, images = parse_download_file()
        self.list.append(('file_selection',
         _('Flash extracted image from storage device'),
         '',
         LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sockets.png')),
         None))
        if result == 0:
            for image in images:
                if image[0] == self.vudevice:
                    self.list.append((image[2],
                     _('Image: %s') % image[1],
                     _('Download image from vuplus-support.org and flash it'),
                     LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/sockets.png')),
                     image[1]))

        elif result == 2:
            self.list.append((None,
             _('Sorry ...'),
             _('It seems that your Internet connection is not ok, please check it'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
             None))
        elif result == 3:
            self.list.append((None,
             _('Sorry ...'),
             _('The image list can not be loaded, please be patient and try again later'),
             LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
             None))
        self['downloadmenu'].setList(self.list)

    def keyOk(self):
        image = self['downloadmenu'].getCurrent()
        if image and image[0] == 'file_selection':
            msg_txt = _('This will flash the selected image without further questions.\nYour current software installation will be deleted and overwritten\nReally continue ?')
            msg = self.session.openWithCallback(self.info_confirmed, MessageBox, msg_txt, MessageBox.TYPE_YESNO, default=False)
            msg.setTitle(self.messagebox_title)
        else:
            self.info_confirmed(True)

    def info_confirmed(self, res):
        if res:
            if self.is_menu_blocked:
                return
            no_access_dirs = []
            no_access_dirs.append('/media/net/autofs')
            if os_path.exists('/media/net/autofs'):
                for dir in listdir('/media/net/autofs'):
                    autofs_dir = '/media/net/autofs/' + dir
                    if os_path.exists(autofs_dir):
                        try:
                            listdir(autofs_dir)
                        except OSError:
                            no_access_dirs.append(autofs_dir)

            mounts = open('/proc/mounts').readlines()
            locations = []
            for mp in mounts:
                mp = mp.split(' ')
                if len(mp) >= 2:
                    if mp[1].startswith('/media/') and mp[1] != '/media/net' and mp[1] not in no_access_dirs:
                        locations.append((mp[1], mp[1], None))

            if len(locations):
                msg = self.session.openWithCallback(self.got_download_device, ChoiceBox, title=_('Please select medium to use as image location'), list=locations)
                msg.setTitle(self.messagebox_title)

    def got_download_device(self, res):
        if res:
            path = res[0]
            error_msg = _('Error at creating download destination !\nPlease select another device.')
            base_path = check_download_dir(path)
            if base_path:
                if base_path == 'size':
                    msg = self.session.open(MessageBox, _('There is to low free memory at choosen device\nPlease select another device.'), MessageBox.TYPE_ERROR)
                    msg.setTitle(self.messagebox_title)
                elif base_path == 'error':
                    msg = self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
                    msg.setTitle(self.messagebox_title)
                else:
                    image = self['downloadmenu'].getCurrent()
                    if image:
                        image_url = image[0]
                        image_name = image[4]
                        if image_name:
                            image_name = image_name.lower()
                            image_name = image_name.replace(' ', '_')
                            path = base_path + '/' + image_name
                        if not fileExists(path):
                            try:
                                os.makedirs(path)
                            except OSError:
                                pass

                        if not fileExists(path, mode='w'):
                            msg = self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
                            msg.setTitle(self.messagebox_title)
                        elif image_url == 'file_selection':
                            if check_flash_files(path):
                                path = path
                            elif fileExists(path + '/vti-image-download'):
                                path = path + '/vti-image-download'
                            else:
                                path = path
                            if not path.endswith('/'):
                                path = path + '/'
                            self.session.openWithCallback(self.image_selected, ImageFileSelector, path, self.skin_path)
                        else:
                            self.start_download(path)

    def image_selected(self, path = None):
        if path:
            if path.endswith('/'):
                path = path[:-1]
            self.path = path
            self.unzip_finished(result=None, retval=0, extra_args=None)
        else:
            self.init_vars()

    def start_download(self, path):
        image = self['downloadmenu'].getCurrent()
        if image:
            self.image_url = self['downloadmenu'].getCurrent()[0]
            self.image_name = self['downloadmenu'].getCurrent()[4]
            self.path = path
            self.file_name = os.path.join(self.path + '/', os.path.basename(self.image_url))
            if fileExists(self.file_name) and self.verify_download():
                self.download_finished(True)
            else:
                job_name = _('Download %s') % self.image_name
                job_manager.AddJob(downloadJob(self.image_url, self.file_name, job_name))
                tasklist = []
                for job in job_manager.getPendingJobs():
                    if job.name == job_name:
                        tasklist.append((job,
                         job.name,
                         job.getStatustext(),
                         int(100 * job.progress / float(job.end)),
                         str(100 * job.progress / float(job.end)) + '%'))
                        break

                if len(tasklist):
                    self.session.openWithCallback(self.download_finished, DownloadTaskScreen, self.skin_path, tasklist, job_name)

    def download_finished(self, res):
        if res:
            if self.verify_download():
                self.list = [(None,
                  _('Extracting image ...'),
                  _('Please wait ...'),
                  LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
                  None)]
                self['downloadmenu'].setList(self.list)
                cmd = '/usr/bin/unzip -o %s -d %s' % (self.file_name, self.path)
                self.Console.ePopen(cmd, self.unzip_finished)
            else:
                msg = self.session.open(MessageBox, _('Sorry, download verification failed\nPlease try again.'), MessageBox.TYPE_ERROR)
                msg.setTitle(self.messagebox_title)
                self.init_vars()
        else:
            self.init_vars()

    def verify_download(self):
        self.is_menu_blocked = True
        self.list = [(None,
          _('Verifying download ...'),
          _('Please wait ...'),
          LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/ntptime.png')),
          None)]
        self['downloadmenu'].setList(self.list)
        md5sum_online = parse_md5sum_file(self.image_url + '.md5')
        md5sum_file = get_md5_hash(self.file_name)
        if md5sum_file and md5sum_online and md5sum_file == md5sum_online:
            return True
        return False

    def unzip_finished(self, result, retval, extra_args = None):
        if retval == 0:
            if check_flash_files(self.path):
                msg_txt = _('This will flash the downloaded image.\nYour current software installation will be deleted and overwritten\nIf you cancel here the downloaded image will be stored and you flash it later\nReally continue ?')
                msg = self.session.openWithCallback(self.flash_confirmed, MessageBox, msg_txt, MessageBox.TYPE_YESNO, default=False)
                msg.setTitle(self.messagebox_title)
            else:
                self.init_vars()
                msg = self.session.open(MessageBox, _('Sorry, necessary files are missing\nPlease try again.'), MessageBox.TYPE_ERROR)
                msg.setTitle(self.messagebox_title)
        else:
            msg = self.session.open(MessageBox, _('Sorry, extracting of image failed\nPlease try again.'), MessageBox.TYPE_ERROR)
            msg.setTitle(self.messagebox_title)
            self.init_vars()

    def flash_confirmed(self, res):
        if res:
            self.session.open(BackupRestoreScreen, title=_('VTi Image Flash Process'), restorepath=self.path, image_flash=True)
        else:
            self.init_vars()

    def keyCancel(self):
        if self.Console is not None:
            if len(self.Console.appContainers):
                for name in self.Console.appContainers.keys():
                    self.Console.kill(name)

        self.close(None)
