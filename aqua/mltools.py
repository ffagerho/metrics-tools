import os, re, gzip, bz2, mailbox, rfc822, time
from os.path import join
from email.Header import decode_header
from StringIO import StringIO

class MboxFile:
	"""A class representing an mbox file."""
	def __init__(self, path):
		self.path = path
		if self.path.endswith(".bz2"):
			self.compressed_file = bz2.BZ2File(path)
			self.file = None
		elif self.path.endswith(".gz"):
			self.compressed_file = gzip.GzipFile(path)
			self.file = None
		else:
			self.compressed_file = None
			self.file = open(path, "r")
	
	def start_use(self):
		if self.compressed_file:
			self.compressed_file.seek(0)
			self.file = StringIO(self.compressed_file.read())
	
	def stop_use(self):
		self.file.close()
		self.file = None
	
	def get_file(self):
		if not self.file:
			self.start_use()
		return self.file

class MailingListArchive:
	"""A class representing a mailing list archive."""
	def __init__(self, mboxfile_list):
		self.__mboxfile_list = mboxfile_list
		self.path = mboxfile_list[0].path
	
	def messages(self):
		for mboxfile in self.__mboxfile_list:
			self.path = mboxfile.path
			mboxfile.start_use()
			mbox = mailbox.PortableUnixMailbox(mboxfile.get_file())
			for message in mbox:
				yield message
			mboxfile.stop_use()
	
def archivefactory(dir_path):
	mboxfile_list = []
	for root, dirs, files in os.walk(dir_path):
		for name in files:
			mboxfile_list.append( MboxFile(join(root, name)) )
	return MailingListArchive(mboxfile_list)

from_parts_rx = re.compile("(.*?)[ ]+[\( ]+(.*?)[\)]+")
from_parts_rx2 = re.compile("(.*?)[ ]+<(.*?)>")
def extract_from_parts(string):
	match = from_parts_rx.search(string)
	if match:
		return (match.group(2), match.group(1))
	else:
		match = from_parts_rx2.search(string)
		if match:
			return (match.group(1), match.group(2))
		else:
			return ('', string)

anon_email_rx = re.compile("(.*?) at (.*?)")
def unanonymize_email(string):
	return string.replace(" at ", "@")

email_rx = re.compile('[<\(\[ ]*([^@<\(\[": ]+@[^@>\)\]:" ]+)[>\) ]*')
def parse_from_header(string):
	replacements = (
			("(", ""), (")", ""),
			('"', ""), ("<", ""), (">", ""),
			)

	# unanonymize email
	string = string.replace(" at ", "@")

	# search for email address
	email_match = email_rx.search(string)
	if email_match:
		# address found, store it and remove it from the string
		email = email_match.group(1).strip()
		rest = string.replace(email, "")
	else:
		# address not found, store this and continue with entire string
		email = None
		rest = string

	# perform a few static replacements in the rest of the string
	for repl in replacements:
		rest = rest.replace(repl[0], repl[1])
	
	# decode MIME-encoded parts and recombine them into a name
	rest_parts = decode_header(rest)
	name = ""
	for part in rest_parts:
		name += part[0] +" "
	name = name.strip()

	# if the name is the empty string, signal this with None
	if len(name) == 0:
		name = None

	return (name, email)

class FixDateError(Exception):
	pass

def fix_date(string):
	replacements = (
			("Sab", "Sat"),
			)
	dateformat = "%Y-%m-%d %H:%M:%S"

	# first, fix up some common mistakes
	for repl in replacements:
		string = string.replace(repl[0], repl[1])

	# try normal date parsing
	date = rfc822.parsedate_tz(string)

	# if it succeeded...
	if date:
		# check that the time zone is present and sensible
		if not date[9] or abs(date[9]) > 12*60*60:
			# use UTC if not
			dateformat += " +0000"
		else:
			# time zone is sensible, use it
			dateformat += " %0+5d" % (date[9] / 60 / 60 * 100)
		# return properly formatted date string; if formatting is not
		# possible, fail
		try:
			return time.strftime(dateformat, date[:-1])
		except ValueError, e:
			raise FixDateError(e)
	else:
		# normal date parsing did not succeed
		raise FixDateError(string)

date_rx = re.compile("^(.*?)(\(.*)\)$")
date_rx2 = re.compile("^([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{1,4})$")
date_rx3 = re.compile("^(.*?) ([0-9]{2}:[0-9]{2}:[0-9]{2}) [a-zA-Z ]+ (.*?)$")
date_rx4 = re.compile("^(.*?) ([0-9]{4})$")
date_rx5 = re.compile("^.*?ISO-8859-1.*? ([0-9]+) ([0-9]+) ([0-9]+) (.*)$")
date_rx6 = re.compile("^(.*?) ([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{1,2}) (.*)$")
date_rx7 = re.compile("^(.*?) ([+-0-9]+)[ ]*\(.*?\)$")
def old_fix_date(string):
	match = date_rx.search(string)
	if False: # if match:
		return match.group(1)
	else:
		match = date_rx2.search(string)
		if match:
			return """%s-%s-%s""" % \
					(match.group(3), match.group(2), match.group(1))
		else:
			match = date_rx3.search(string)
			if match:
				return " ".join(match.groups())
			else:
				match = date_rx4.search(string)
				if match:
					return """%s -%s""" % (match.group(1), match.group(2))
				else:
					match = date_rx5.search(string)
					if match:
						return """%s-%s-%s %s""" % (match.group(3),
								match.group(2), match.group(1), match.group(4))
					else:
						match = date_rx6.search(string)
						if match:
							return """%s %s:%s:%s %s""" % (match.group(1),
									match.group(2), match.group(3),
									match.group(4), match.group(5))
						else:
							match = date_rx7.search(string)
							if match:
								if int(match.group(2).replace("+","").replace("-","")) > 1200:
									return match.group(1)
								else:
									return " ".join([match.group(1),
										match.group(2).replace("+","").replace("-","")])
							else:
								if string.endswith("test"):
									return string[:-4]
								else:
									date = rfc822.parsedate_tz(string)
									if date:
										if date[9] > 12*60*60:
											return time.strftime("%Y-%m-%d %H:%M:%S +0000", date[:-1])
										else:
											return string.replace("Sab", "Sat")
									else:
										raise FixDateError(string)
