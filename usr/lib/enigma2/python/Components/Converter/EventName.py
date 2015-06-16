from Components.Converter.Converter import Converter
from Components.Element import cached
from Tools.MovieInfoParser import getExtendedMovieDescription

class EventName(Converter, object):
	NAME = 0
	SHORT_DESCRIPTION = 1
	EXTENDED_DESCRIPTION = 2
	ID = 3
	FULL_DESCRIPTION = 4
	
	def __init__(self, type):
		Converter.__init__(self, type)
		if type == "Description":
			self.type = self.SHORT_DESCRIPTION
		elif type == "ExtendedDescription":
			self.type = self.EXTENDED_DESCRIPTION
		elif type == "FullDescription":
			self.type = self.FULL_DESCRIPTION
		elif type == "ID":
			self.type = self.ID
		else:
			self.type = self.NAME

	@cached
	def getText(self):
		event = self.source.event
		if event is None:
			if hasattr(self.source, 'service') and (self.type == self.EXTENDED_DESCRIPTION or self.type == self.FULL_DESCRIPTION):
				service = self.source.service
				if service:
					ret = getExtendedMovieDescription(service)
					return ret[1]
			elif self.type == self.NAME and hasattr(self.source, 'service'):
				service = self.source.getCurrentService()
				if service:
					sname = ((service.getPath().split('/')[-1]).rsplit('.', 1)[0]).replace('_',' ')
					return sname
			return ""
			
		ret = ""
		if self.type == self.NAME:
			ret = event.getEventName()
		elif self.type == self.SHORT_DESCRIPTION:
			ret = event.getShortDescription()
		elif self.type == self.EXTENDED_DESCRIPTION:
			ret = event.getExtendedDescription()
		elif self.type == self.FULL_DESCRIPTION:
			ext_desc = event.getExtendedDescription()
			short_desc = event.getShortDescription()
			if short_desc == "":
				ret = ext_desc
			elif ext_desc == "":
				ret = short_desc
			else:
				ret = "%s\n\n%s" % (short_desc, ext_desc)
		elif self.type == self.ID:
			ret = str(event.getEventId())
		return ret
	text = property(getText)
