import sys, re, urllib, stringutil
from xml.dom import minidom, Node
from StringIO import StringIO
from time import sleep

class BTS:
	"""Class representing a bug tracking system."""
	def __init__(self, buglist_url, bug_url, name):
		self.buglist_url = buglist_url
		self.bug_url = bug_url
		self.name = name
	
	def bugs(self):
		"""Returns an iterable of bugs."""
		raise NotImplementedError

class Bug:
	"""Class representing a bug."""
	def __init__(self, id, creation_time, modification_time, title, type,
			status, severity, flags, product, component, submitter_name,
			submitter_email):
		self.id = id
		self.creation_time = creation_time
		self.modification_time = modification_time
		self.title = title
		self.type = type
		self.status = status
		self.severity = severity
		self.flags = flags
		self.product = product
		self.component = component
		self.submitter_name = submitter_name
		self.submitter_email = submitter_email
	
	def __repr__(self):
		return "<Bug: %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % \
				(self.id, self.creation_time, self.modification_time,
						self.title, self.type, self.status, self.severity,
						self.flags, self.product, self.component,
						self.submitter_name, self.submitter_email)

class Bugzilla(BTS):
	"""Class representing a Bugzilla bug tracking system."""
	textrx = re.compile('<thetext>(.*?)</thetext>', re.DOTALL)
	num_start_rx = re.compile('^[0-9]+,.*$')

	def bugs(self):
		try:
			url_f = urllib.urlopen(self.buglist_url)
		except IOError, e:
			sys.stderr.write("DEBUG %s, sleeping 10 seconds\n" % (e))
			sleep(10)
			url_f = urllib.urlopen(self.buglist_url)
		url_f.readline() # skip csv header
		for line in url_f.readlines():
			# check that the line is valid (it might be a csv continuing
			# line, in which case we just skip it)
			if Bugzilla.num_start_rx.match(line):
				(bug_id, rest) = line.split(",", 1)
				yield self.bugfactory(bug_id)
		url_f.close()
	
	def bug(self, bug_id):
		return self.bugfactory(bug_id)
	
	def bugfactory(self, bug_id):
		try:
			url_f = urllib.urlopen(self.bug_url % str(bug_id))
		except IOError, e:
			sys.stderr.write("DEBUG %s, sleeping 10 seconds\n" % (e))
			sleep(10)
			url_f = urllib.urlopen(self.bug_url % str(bug_id))
		xmldata = url_f.read()
		url_f.close()
		xmldata = Bugzilla.textrx.sub('<thetext />', xmldata)
		try:
			xmldata = xmldata.decode('utf8', 'replace')
		except:
			pass
		try:
			xmldata = xmldata.encode('ascii', 'replace')
		except:
			pass
		dom = minidom.parseString(xmldata)
		bug = BugzillaDomFactory(dom)
		return bug.get_bug()

class BugzillaDomFactory:
	def __init__(self, dom):
		self.__bugdata = {
				'bug_id': None, # bug_id
				'creation_time': None, # creation_ts
				'modification_time': None, # delta_ts
				'title': None, # short_desc
				'type': 'bug',
				'status': None, # bug_status
				'severity': None, # bug_severity
				'flags': None,
				'product': None, # product
				'component': None, # component
				'submitter_name': None, # reporter_realname
				'submitter_email': None, # reporter
				}
		self.__mappings = {
				'bug_id': 'bug_id',
				'creation_ts': 'creation_time',
				'delta_ts': 'modification_time',
				'short_desc': 'title',
				'bug_status': 'status',
				'bug_severity': 'severity',
				'product': 'product',
				'component': 'component',
				'reporter': 'submitter_email',
				}

		dom = dom.getElementsByTagName("bug")[0]
		for child in dom.childNodes:
			self.handleNode(child)
	
	def handleNode(self, node):
		if node.nodeType == Node.ELEMENT_NODE and \
				node.tagName in self.__mappings.keys():
			self.__bugdata[self.__mappings[node.tagName]] = \
					self.getText(node.childNodes)
	
	def getText(self, nodelist):
		string = ""
		for node in nodelist:
			if node.nodeType == Node.TEXT_NODE:
				string += node.data
		try:
			string = string.decode('utf8', 'replace')
		except:
			pass
		try:
			string = string.encode('latin1', 'replace')
		except:
			pass
		sys.stderr.write("DEBUG %s\n" % string)
		return string

	def get_bug(self):
		d = self.__bugdata
		return Bug(id = d['bug_id'],
				creation_time = d['creation_time'],
				modification_time = d['modification_time'],
				title = d['title'],
				type = d['type'],
				status = d['status'],
				severity = d['severity'],
				flags = d['flags'],
				product = d['product'],
				component = d['component'],
				submitter_name = d['submitter_name'],
				submitter_email = d['submitter_email'])

class GForge(BTS):
	"""Class representing a GForge bug tracking system."""
	bug_rx = re.compile("""<tr BGCOLOR="#[EF]+"><td>([0-9]+)</td><td></td><td><a href="(.*?)">(.*?)</a></td><td>[\* ]*(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>""")
	pages_rx=re.compile("""<strong>([0-9]+)</strong></a>&nbsp;&nbsp;\*""")
	list_params = {'set': 'custom', '_assigned_to': 0, '_status': 100,
			'_sort_col': 'artifact_id', '_sort_ord': 'ASC'}

	state_rx = re.compile("""<td><strong>State:</strong><br />(.*?)</td>""")
	date_rx = re.compile("""<td><strong>Date:</strong><br />(.*?)</td>""")
	priority_rx = re.compile("""<td><strong>Priority:</strong><br />([0-9]+)</td>""")
	submitter_rx = re.compile("""<td><strong>Submitted By:</strong><br />\s*(.*?)\(<tt><a href="/users/.*?">(.*?)</a></tt>""")
	summary_rx = re.compile("""<tr><td colspan="2"><strong>Summary:</strong><br />(.*?)</td></tr>""")
	project_rx = re.compile("""<TITLE>Blender Projects: (.*?): Detail: .*?</TITLE>""")
	email_rx = re.compile("""<tr valign="top">\s*<td>Your Email Address: </td>\s*<td>\s*<strong><a href=".*?">(.*?)</a></strong>\s*</td>\s*</tr>""")

	bug_mappings = {
			'creation_time': date_rx,
			'status': state_rx,
			'severity': priority_rx,
			'title': summary_rx,
			'product': project_rx,
			}

	def _bugs(self, url, start = 0, bugs_per_page = 25):
		list_params_str = urllib.urlencode(GForge.list_params)
		url = "%s&start=%d" % (url, start)

		try:
			url_f = urllib.urlopen(url, list_params_str)
		except IOError:
			sys.stderr.write("DEBUG %s, sleeping 10 seconds\n" % (e))
			sleep(10)
			url_f = urllib.urlopen(url, list_params_str)
		data = StringIO(url_f.read().replace("</tr>", "</tr>\n"))
		url_f.close()

		for line in data:
			match = GForge.bug_rx.search(line)
			if match:
				yield self.bugfactory(match.group(1))
			elif start == 0:
				match = GForge.pages_rx.search(line)
				if match:
					pages = int(match.group(1))

		if start == 0:
			for page in range(bugs_per_page, pages * bugs_per_page,
					bugs_per_page):
				for bug in self._bugs(url, start=page):
					yield bug

	def bugs(self):
		for bug in self._bugs(self.buglist_url):
			yield bug

	def bugfactory(self, bug_id):
		try:
			url_f = urllib.urlopen(self.bug_url % str(bug_id))
		except IOError, e:
			sys.stderr.write("DEBUG %s, sleeping 10 seconds\n" % (e))
			sleep(10)
			url_f = urllib.urlopen(self.bug_url % str(bug_id))
		data = url_f.read()
		url_f.close()
		bugdata = {}
		for component in GForge.bug_mappings:
			match = GForge.bug_mappings[component].search(data)
			if match:
				bugdata[component] = match.group(1)

		match = GForge.submitter_rx.search(data)
		if match:
			submitter_name = match.group(1).strip()
			submitter_uid = match.group(2)
			submitter_email = self.email_cache(submitter_uid)
		else:
			submitter_name = None
			submitter_email = None

		return Bug(id=bug_id,
				creation_time = bugdata['creation_time'],
				modification_time = None,
				title = bugdata['title'],
				type = 'bug',
				status = bugdata['status'].upper(),
				severity = bugdata['severity'],
				flags = None,
				product = bugdata['product'],
				component = None,
				submitter_name = submitter_name,
				submitter_email = submitter_email)
	
	def email_cache(self, uid):
		try:
			if self._email_cache.has_key(uid):
				return self._email_cache[uid]
		except AttributeError:
			self._email_cache = {}

		url_parts = self.buglist_url.split("/")
		user_url = "%s//%s/users/%s" % (url_parts[0], url_parts[2], uid)

		try:
			url_f = urllib.urlopen(user_url)
		except IOError, e:
			sys.stderr.write("DEBUG %s, sleeping 10 seconds\n" % (e))
			sleep(10)
			url_f = urllib.urlopen(user_url)
		data = url_f.read()
		url_f.close()

		match = GForge.email_rx.search(data)
		if match:
			self._email_cache[uid] = match.group(1).replace(" @nospam@ ", "@")
			return self._email_cache[uid]
		else:
			return None
