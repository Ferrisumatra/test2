from Components.Converter.Converter import Converter
from Components.Element import cached, ElementError
from Tools.Bytes2Human import bytes2human
from enigma import iServiceInformation
from ServiceReference import ServiceReference
from os import path as os_path

class MovieInfo(Converter, object):
	MOVIE_SHORT_DESCRIPTION = 0 # meta description when available.. when not .eit short description
	MOVIE_META_DESCRIPTION = 1 # just meta description when available
	MOVIE_REC_SERVICE_NAME = 2 # name of recording service
	MOVIE_REC_FILESIZE = 3 # filesize of recording
	MOVIE_REFERENCE = 4 # reverencestring of recording

	def __init__(self, type):
		if type == "ShortDescription":
			self.type = self.MOVIE_SHORT_DESCRIPTION
		elif type == "MetaDescription":
			self.type = self.MOVIE_META_DESCRIPTION
		elif type == "RecordServiceName":
			self.type = self.MOVIE_REC_SERVICE_NAME
		elif type == "FileSize":
			self.type = self.MOVIE_REC_FILESIZE
		elif type == "Reference":
			self.type = self.MOVIE_REFERENCE
		else:
			raise ElementError("'%s' is not <ShortDescription|MetaDescription|RecordServiceName|FileSize> for MovieInfo converter" % type)
		Converter.__init__(self, type)

	@cached
	def getText(self):
		service = self.source.service
		info = self.source.info
		if info and service:
			if self.type == self.MOVIE_SHORT_DESCRIPTION:
				event = self.source.event
				if event:
					descr = info.getInfoString(service, iServiceInformation.sDescription)
					if descr == "":
						return event.getShortDescription()
					else:
						return descr
			elif self.type == self.MOVIE_META_DESCRIPTION:
				return info.getInfoString(service, iServiceInformation.sDescription)
			elif self.type == self.MOVIE_REC_SERVICE_NAME:
				rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
				sname = ServiceReference(rec_ref_str).getServiceName()
				if not sname:
					service = self.source.getCurrentService()
					if service:
						sname = service.getPath().split('/')[-1]
						name, ext = os_path.splitext(sname)
						if ext in (".ts", ".avi", ".divx", ".mpg", ".mpeg", ".mkv", ".mp4", ".mov", ".iso"):
							sname = name.replace("_", " ")
				return sname
			elif self.type == self.MOVIE_REC_FILESIZE:
				filesize = info.getInfoObject(service, iServiceInformation.sFileSize)
				if filesize is not None:
					return "%s" % bytes2human(filesize,1)
			elif self.type == self.MOVIE_REFERENCE:
				return info.getInfoString(service, iServiceInformation.sServiceref)
		return ""

	text = property(getText)
