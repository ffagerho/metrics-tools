import os, mimetypes, re, tempfile
from os.path import join
from xml.dom import minidom, Node
from datetime import datetime
from util import rmall, diffstat
from cStringIO import StringIO

heavy_metrics = set(['cccc', 'diffstats', 'static-c', 'static-python', 'filetypes'])
light_metrics = set(['vcslog'])
all_metrics = heavy_metrics | light_metrics

def dispatch(vs, metrics_set):
	results = {}
	for metric in metrics_set:
		if metric == 'cccc':
			cccc = CCCC(vs.get_working_dir())
			results[metric] = cccc.data
		elif metric == 'diffstats':
			diffstats = diffstat(vs.get_diff())
			results[metric] = {
					'files_changed': diffstats[0],
					'loc_add': diffstats[0],
					'loc_del': diffstats[0],
					}
		elif metric.startswith('static'):
			if metric == 'static-c':
				static = StaticC(vs.get_working_dir())
			elif metric == 'static-python':
				static = StaticPython(vs.get_working_dir())
			else:
				continue

			static.run()

			if static.nom == 0:
				fanin_avg = 0
			else:
				fanin_avg = static.fanin_total / static.nom

			if static.nom == 0:
				fanout_avg = 0
			else:
				fanout_avg = static.fanout_total / static.nom

			results[metric] = {
					'nom': static.nom,
					'fanin_avg': fanin_avg,
					'fanin_tot': static.fanin_total,
					'fanout_avg': fanout_avg,
					'fanout_tot': static.fanout_total,
					'ploc': static.ploc_total,
					'sloc': static.sloc_total,
					'bloc': static.bloc_total,
					'cloc': static.cloc_total,
					'cyclomatic': static.cyclomatic_total,
					'module_info': static.module_list,
					}
		elif metric == 'filetypes':
			ft = FileTypeLister(vs.get_working_dir())
			ft.run()
			results[metric] = ft.files
		elif metric == 'vcslog':
			results[metric] = vs.get_revision_info()
	return results


class Static:
	"""Class for calculating fan-in, fan-out, PLOC, SLOC, BLOC, CLOC and
	cyclomatic complexity."""

	def __init__(self, top_dir):
		self.nom = 0
		self.fanin_total = 0
		self.fanout_total = 0
		self.ploc_total = 0
		self.sloc_total = 0
		self.bloc_total = 0
		self.cloc_total = 0
		self.cyclomatic_total = 0

		self.module_list = {}
		self.top_dir = top_dir

		self.init_regexps()
	
	def init_regexps(self):
		raise NotImplementedError
	
	def path_permitted(self, path):
		if path.find("/.svn") == -1 and path.find("/.git") == -1:
			return True
		else:
			return False

	def include_filename(self, name):
		raise NotImplementedError
	
	def run(self):
		for root, dirs, files in os.walk(self.top_dir):
			if not self.path_permitted(root):
				continue
			for name in files:
				if self.include_filename(name):
					path = join(root, name)
					module_info = {
							'function_info': {},
							'fanin': 0,
							'fanout': 0,
							'ploc': 0,
							'sloc': 0,
							'bloc': 0,
							'cloc': 0,
							'cyclomatic': 0,
							}
					self.module_list[strip_prefix(self.top_dir, path)] = \
							module_info
					self.nom += 1

					f = open(path)
					data = f.read()
					f.close()

					# find functions and count their parameters
					for match in re.findall(self.function_rx, data):
						func_name = match[0]
						func_params = len(match[1].split(','))
						module_info['function_info'][func_name] = func_params
						module_info['fanin'] += func_params
						self.fanin_total += func_params

					# find and count return statements
					module_info['fanout'] = \
							len(re.findall(self.return_rx, data))
					self.fanout_total += module_info['fanout']

					# count different kinds of loc and cyclomatic complexity
					loc_data = self.comment_rx.sub(self._comment_sub, data)
					sio = StringIO(loc_data)
					for line in sio.readlines():
						module_info['ploc'] += 1
						if len(line) == 0 or line.isspace():
							module_info['bloc'] += 1
						elif line == self.comment:
							module_info['cloc'] += 1
						else:
							module_info['sloc'] += 1

						if self.function_rx.search(line) or \
								self.decision_rx.search(line):
									module_info['cyclomatic'] += 1

					self.ploc_total += module_info['ploc']
					self.bloc_total += module_info['bloc']
					self.cloc_total += module_info['cloc']
					self.sloc_total += module_info['sloc']
					self.cyclomatic_total += module_info['cyclomatic']

	def _q(self, c):
		return r"%s(\\.|[^%s])*%s" % (c, c, c)

	def _comment_sub(self, match):
		string = match.group(0)
		if string.startswith("/") or string.startswith("#"):
			return self.comment
		else:
			return string

class StaticC(Static):
	def init_regexps(self):
		self.function_rx = re.compile("(?P<name>\w+)(?<!if)(?<!switch)(?<!while)(?<!for)\s*\((?P<params>[^;!><\(\)]*?)\)\s*{", re.S)
		self.return_rx = re.compile("return .*?;", re.S)
		self.decision_rx = re.compile("(if)|(switch)|(while)|(for)\s*\(", re.S)

		single_quoted_string = self._q("'")
		double_quoted_string = self._q('"')
		c_comment = r"/\*.*?\*/"
		cpp_comment = r"//[^\n]*[\n]"
		hash_comment = r"#[^\n]*[\n]"
		self.comment_rx = re.compile("|".join([single_quoted_string,
			double_quoted_string, c_comment, cpp_comment, hash_comment]),
			re.DOTALL)
		self.comment = "/* COMMENT */"

	def include_filename(self, name):
		if name.endswith(".c"): # or name.endswith(".h"):
			return True
		else:
			return False

class StaticPython(Static):
	def init_regexps(self):
		self.function_rx = re.compile("def\s+(?P<name>\w+)\s*\((?P<params>.*?)\)\s*:", re.S)
		self.return_rx = re.compile("return(?:\s+.*?)?", re.S)
		self.decision_rx = re.compile("(elif)|(for)|(if)|(raise)|(while)|(yield)", re.S)

		single_quoted_string = self._q("'")
		double_quoted_string = self._q('"')
		c_comment = r"/\*.*?\*/"
		cpp_comment = r"//[^\n]*[\n]"
		hash_comment = r"#[^\n]*[\n]"
		self.comment_rx = re.compile("|".join([single_quoted_string,
			double_quoted_string, c_comment, cpp_comment, hash_comment]),
			re.DOTALL)
		self.comment = "# COMMENT #"
	
	def include_filename(self, name):
		if name.endswith(".py"):
			return True
		else:
			return False

class CCCC:
	"""Class for abstracting cccc tool."""

	def __init__(self, top_dir, defer_run=False):
		self.data = {}
		self.top_dir = top_dir
		self.tempdir = tempfile.mkdtemp(suffix=".cccc")
		self.file_list = []
		for root, dirs, files in os.walk(self.top_dir):
			if root.find("/.svn") != -1 or \
					root.find("/.git") != -1:
				continue
			for name in files:
				if name.endswith('.c') or \
						name.endswith('.h') or \
						name.endswith('.cpp'):
							self.file_list.append(join(root, name))

		if not defer_run:
			self.run()
	
	def __del__(self):
		rmall(self.tempdir)
	
	def run(self):
		start_time = datetime.now()
		cccc = os.popen("cccc --outdir=%s - >/dev/null 2>&1" % \
				self.tempdir, "w")
		for name in self.file_list:
			cccc.write("%s\n" % name)
		cccc.close()

		f = open(join(self.tempdir, "cccc.xml"))
		xmldata = f.read()
		f.close()

		dom = minidom.parseString(xmldata)
		summary = dom.getElementsByTagName("project_summary")[0]
		for metric in [("lines_of_code", "sloc"),
				("number_of_modules", "nom"),
				("McCabes_cyclomatic_complexity", "cyclomatic"),
				("lines_of_comment", "cloc"),
				("IF4", "if"),
				("rejected_lines_of_code", "rejloc"),]:
			node = summary.getElementsByTagName(metric[0])[0]
			self.data[metric[1]] = int(node.getAttribute("value"))

		module_metrics = {}
		oo_design = dom.getElementsByTagName("oo_design")[0]
		for module in oo_design.getElementsByTagName("module"):
			name = module.getElementsByTagName("name")[0].firstChild.data
			module_metrics[name] = {}
			for metric in [("weighted_methods_per_class_unity", "wmc"),
					("depth_of_inheritance_tree", "dit"),
					("number_of_children", "noc"),
					("coupling_between_objects", "cbo"),]:
				node = module.getElementsByTagName(metric[0])[0]
				module_metrics[name][metric[1]] = \
						int(node.getAttribute("value"))

		structural = dom.getElementsByTagName("structural_summary")[0]
		for module in structural.getElementsByTagName("module"):
			name = module.getElementsByTagName("name")[0].firstChild.data
			for metric in [("fan_out", "fanout"),
				("fan_in", "fanin"),
				("IF4", "if"),]:
				node = module.getElementsByTagName(metric[0])[0]
				module_metrics[name][metric[1]] = \
						int(node.getAttribute("value"))

		self.data["modules"] = module_metrics
		
		end_time = datetime.now()
		self.runtime = end_time - start_time

class FileTypeLister:
	"""Lists files and their types."""

	def __init__(self, top_dir):
		self.top_dir = top_dir
		self.files = {}
	
	def run(self):
		for root, dirs, files in os.walk(self.top_dir):
			if root.find("/.svn") != -1 or root.find("/.git") != -1:
				continue
			for name in files:
				path = join(root, name)
				self.files[strip_prefix(self.top_dir, path)] = \
						self.file_type(path)

	def file_type(self, path):
		mime_type = mimetypes.guess_type(path)
		return {'mime_type': mime_type[0], 'compression': mime_type[1]}

def strip_prefix(prefix, string):
	if string.startswith(prefix):
		return string[len(prefix):]

### old code below ###

class FileLister:
	"""Lists files as complete paths, can identify file type."""
	def __init__(self, top_dir):
		self.__top_dir = top_dir
		self.__file_list = None
	
	def get_file_list(self):
		if self.__file_list:
			return self.__file_list
		self.__file_list = []
		for root, dirs, files in os.walk(self.__top_dir):
			self.__file_list.extend( \
					[ (join(root, name), {}) for name in files] )
		return self.__file_list

	def get_file_types_list(self):
		file_list = self.get_file_list()
		if not file_list[0][1].has_key('mimetype'):
			mimetypes.init()
			for item in file_list:
				item[1]['mimetype'] = mimetypes.guess_type(item[0])[0]
		return file_list

class PLOC:
	"""PLOC calculator; calculates physical lines of code"""
	def __init__(self, filelister):
		self.__filelister = filelister
	
	def get_file_list(self):
		return self.__filelister.get_file_list()

	def get_loc_for_file(self, path):
		try:
			f = open(path)
			loc = len(f.readlines())
			f.close()
			return loc
		except IOError:
			return -1

	def get_file_loc_list(self, key='loc'):
		for item in self.get_file_list():
			if item[1].has_key(key):
				return self.get_file_list()
			item[1][key] = self.get_loc_for_file(item[0])
		return self.get_file_list()

	def get_total_loc(self, key='loc'):
		sum = 0
		for item in self.get_file_loc_list():
			sum += item[1][key]
		return sum

def _q(c):
	return r"%s(\\.|[^%s])*%s" % (c, c, c)

def _sub(match):
	string = match.group(0)
	if string.startswith("/") or string.startswith("#"):
		if string.endswith('\n'):
			return '\n'
		elif string.endswith('\r'):
			return '\r'
		else:
			return ' '
	else:
		return string

class SLOC(PLOC):
	"""SLOC calculator; counts source lines (code)."""

	single_quoted_string = _q("'")
	double_quoted_string = _q('"')
	c_comment = r"/\*.*?\*/"
	cpp_comment = r"//[^\n]*[\n]"
	hash_comment = r"#[^\n]*[\n]"
	rx = re.compile("|".join([single_quoted_string, double_quoted_string,
		c_comment, cpp_comment, hash_comment]), re.DOTALL)

	def get_loc_for_file(self, path):
		try:
			loc = 0
			f = open(path)
			data = self.rx.sub(_sub, f.read())
			for line in data.split('\n'):
				if len(line) > 0:
					loc += 1
			f.close()
			return loc
		except IOError:
			return -1
	
	def get_file_loc_list(self):
		return PLOC.get_file_loc_list(self, 'sloc')

	def get_total_loc(self):
		return PLOC.get_total_loc(self, 'sloc')

class BLOC(PLOC):
	"""BLOC calculator; counts blank lines."""

	def get_loc_for_file(self, path):
		try:
			loc = 0
			f = open(path)
			for line in f.readlines():
				if len(line) == 0 or line.isspace():
					loc += 1
			f.close()
			return loc
		except IOError:
			return -1
	
	def get_file_loc_list(self):
		return PLOC.get_file_loc_list(self, 'bloc')

	def get_total_loc(self):
		return PLOC.get_total_loc(self, 'bloc')

class CLOC(PLOC, SLOC, BLOC):
	"""CLOC calculator; counts comment lines."""

	def get_loc_for_file(self, path):
		ploc = PLOC.get_loc_for_file(self, path)
		sloc = SLOC.get_loc_for_file(self, path)
		bloc = BLOC.get_loc_for_file(self, path)
		return ploc - sloc - bloc

	def get_file_loc_list(self):
		return PLOC.get_file_loc_list(self, 'cloc')

	def get_total_loc(self):
		return PLOC.get_total_loc(self, 'cloc')

class Cyclomatic:
	"""Cyclomatic complexity calculator; calculates the number of decision
	points in a program plus 1."""
	def __init__(self, filelister):
		self.__filelister = filelister
		self.__func_regexp = re.compile("def .+?:")
		self.__cyc_regexp = re.compile("(if)|(try)|(for)|(while)|" \
				"(return)|(continue)|(break)|(raise)")

	def get_cyc_for_file(self, path):
		try:
			cyc = 0
			f = open(path)
			for line in f.readlines():
				if self.__func_regexp.search(line) or \
						self.__cyc_regexp.search(line):
					cyc += 1
			f.close()
			return cyc
		except IOError:
			return -1
	
	def get_file_cyc_list(self):
		for item in self.__filelister.get_file_list():
			if item[1].has_key('cyc'):
				return self.__filelister.get_file_list()
			item[1]['cyc'] = self.get_cyc_for_file(item[0])
		return self.__filelister.get_file_list()

class SingleTokenCounter:
	"""Counts number of occurrences of a specified token."""
	def __init__(self, filelister, token_regexp, key):
		self._filelister = filelister
		self._token_regexp = token_regexp
		self._key = key
	
	def get_token_for_file(self, path):
		try:
			count = 0
			f = open(path)
			for line in f.readlines():
				if self._token_regexp.search(line):
					count += 1
			f.close()
			return count
		except IOError:
			return -1
	
	def get_file_token_list(self):
		for item in self._filelister.get_file_list():
			if item[1].has_key(self._key):
				return self._filelister.get_file_list()
			item[1][self._key] = self.get_token_for_file(item[0])
		return self._filelister.get_file_list()

class FunctionCounter(SingleTokenCounter):
	"""Counts number of functions in a file."""
	def __init__(self, filelister):
		self._filelister = filelister
		self._token_regexp = re.compile("def .+?:")
		self._key = 'func'
	
	def get_func_for_file(self, path):
		return self.get_token_for_file(path)

	def get_file_func_list(self):
		return self.get_file_token_list()

class ClassCounter(SingleTokenCounter):
	"""Counts number of classes in a file."""
	def __init__(self, filelister):
		self._filelister = filelister
		self._token_regexp = re.compile("class .+?:")
		self._key = 'class'

	def get_class_for_file(self, path):
		return self.get_token_for_file(path)

	def get_file_class_list(self):
		return self.get_file_token_list()

class ModuleCounter:
	"""Counts the number of Python modules. A module is a file."""
	def __init__(self, filelister):
		self.__filelister = filelister
	
	def get_module_count(self):
		count = 0
		for item in self.__filelister.get_file_list():
			if item[0].endswith('.py'):
				count += 1
		return count

class FanIn:
	"""Measures the fan-in of a module. Fan-in is the number of parameters
	to each function."""

	func_regex = re.compile("def (.*?)[ ]*\((.*)\):")

	def __init__(self, filelister):
		self.__filelister = filelister
	
	def get_fanin_for_file(self, path):
		try:
			fanin = 0
			f = open(path)
			for line in f.readlines():
				match = FanIn.func_regex.search(line)
				if match:
					fanin += len(re.split("\W+", match.group(2)))
			f.close()
			return fanin
		except IOError:
			return -1
	
	def get_file_fanin_list(self):
		for item in self.__filelister.get_file_list():
			if item[1].has_key('fanin'):
				return self.__filelister.get_file_list()
			item[1]['fanin'] = self.get_fanin_for_file(item[0])
		return self.__filelister.get_file_list()

class FanOut:
	"""Measures the fan-out of a module. Fan-out is one if the function has
	a return statement, otherwise it is zero."""
	def __init__(self, filelister):
		self.__filelister = filelister
	
	def get_fanout_for_file(self, path):
		try:
			f = open(path)
			for line in f.readlines():
				if line.find("return") >= 0:
					return 1
			f.close()
			return 0
		except IOError:
			return -1

	def get_file_fanout_list(self):
		for item in self.__filelister.get_file_list():
			if item[1].has_key('fanout'):
				return self.__filelister.get_file_list()
			item[1]['fanout'] = self.get_fanout_for_file(item[0])
		return self.__filelister.get_file_list()

class InformationFlow(FanIn, FanOut):
	"""Measures the information flow of a module, defined as fan-in
	plus fan-out."""
	def __init__(self, filelister):
		self.__filelister = filelister
	
	def get_iflow_for_file(self, path):
		return self.get_fanin_for_file(path) + self.get_fanout_for_file(path)
	
	def get_file_iflow_list(self):
		for item in self.__filelister.get_file_list():
			if item[1].has_key('iflow'):
				return self.__filelister.get_file_list()
			item[1]['iflow'] = self.get_iflow_for_file(item[0])
		return self.__filelister.get_file_list()

class HalsteadVolume:
	pass

class NOC:
	pass

class WMC:
	pass

class CBO:
	pass

class RFC:
	pass

class LCOM:
	pass

class DIT:
	pass
