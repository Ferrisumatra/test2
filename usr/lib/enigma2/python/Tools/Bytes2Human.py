# -*- coding: utf-8 -*-

def bytes2human(n, digits = 2):
	symbols = ('KB', 'MB', 'GB', 'TB', 'PB')
	prefix = {}
	for i, s in enumerate(symbols):
		prefix[s] = 1 << (i + 1) * 10
	for s in reversed(symbols):
		if n >= prefix[s]:
			if digits > 0:
				value = round((float(n) / prefix[s]),digits)
			else:
				value = n / prefix[s]
			return '%s %s' % (value, s)
	return "%s B" % n
