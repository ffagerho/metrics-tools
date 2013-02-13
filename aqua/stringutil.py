def replaceUnsafeChars(s):
	s2 = ""
	for c in s:
		try:
			c2 = c.encode('latin-1', 'replace')
			c = c2
		except UnicodeDecodeError:
			c = '#'
		s2 += c
	return s2

_u2html = {}   # unicode to html mapping

def _make_u2html():
	from htmlentitydefs import entitydefs

	def c2u(c):
		if len(c) == 1:
			return unicode(c, 'latin1')
		if c.startswith('&#'):
			return unichr(int(c[2:-1]))

	for entity,val in entitydefs.items():
		_u2html[c2u(val)] = "&%s;" % entity

def htmlentityEncode(s):
	"""
	convert unicode string s to ascii, replace non-ascii characters with
	html entitydef or "?"
	"""

	if not _u2html:
		_make_u2html()
	l = [_u2html.get(c, c) for c in s]
	return ''.join(l).encode('ascii', 'replace') 
