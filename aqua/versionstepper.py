import sys, os, pysvn
from datetime import datetime
from util import rmall
from mltools import unanonymize_email
from time import sleep

class VersionStepper:
	def __init__(self, repo_url, work_dir, reuse_work_dir=False):
		"""Check out the first version of repo_url into work_dir and
		initialize internal data structures. The directory work_dir
		is created and must not exist. It is removed when the object is
		destroyed. If reuse_work_dir is true, do not perform the initial
		checkout; assume that the work directory already exists."""
		raise NotImplementedError

	def step_revision(self, steps=1):
		"""Move steps steps forward in the repository history. If this
		would move us before the first revision, raise IndexError. If this
		would move us beyond the last revision, raise StopIteration."""
		raise NotImplementedError
	
	def update(self):
		"""Update the working copy to the curently selected revision."""
		raise NotImplementedError

	def fetch_next_revision(self):
		"""Move to the next revision in the repository history and
		update the working copy."""
		self.step_revision()
		self.update()
	
	def get_diff(self):
		"""Get the diff between the currently selected revision and the
		revision that was previously selected (not necessarily the previous
		revision)."""
		raise NotImplementedError
	
	def get_working_dir(self):
		"""Get the path name of the working directory."""
		return self.work_dir
	
	def get_revision_info(self):
		"""Return a dictionary with the following keys:
			author - who has committed the current revision
			timestamp - when was the current revision committed
			revision_id - the native id of the current revision"""
		raise NotImplementedError

	def get_revision_info_all(self):
		"""Return a list of dictionaries; the dictionary keys are
		the same as those returned by get_revision_info()."""
		raise NotImplementedError

	def __del__(self):
		"""Destructor. Cleans up as this object is destroyed."""
		rmall(self.work_dir)

class SVNVersionStepper(VersionStepper):
	def __init__(self, repo_url, work_dir, reuse_work_dir=False):
		self.repo_url = repo_url
		self.work_dir = work_dir
		self.client = pysvn.Client()
		self.rev_first = pysvn.Revision(pysvn.opt_revision_kind.number, 1)
		self.rev_head = pysvn.Revision(pysvn.opt_revision_kind.head)
		self.log = self.client.log(self.repo_url,
				revision_start = self.rev_first,
				revision_end = self.rev_head,
				discover_changed_paths=True)
		if not reuse_work_dir:
			self.client.checkout(self.repo_url, self.work_dir,
					revision = self.log[0].revision)
		self.log_index = 0
		self.old_log_index = None

	def step_revision(self, steps=1):
		if self.log_index + steps < 0:
			raise IndexError, 'Cannot move beyond first revision'
		elif self.log_index + steps >= len(self.log):
			raise StopIteration, 'Cannot move beyond last revision'
		self.old_log_index = self.log_index
		self.log_index += steps
	
	def update(self):
		log_entry = self.log[self.log_index]
		try:
			self.client.update(self.work_dir,
					revision = log_entry.revision)
		except:
			sys.stderr.write("ERROR update failed, sleeping 10 seconds")
			sleep(10)
			self.client.update(self.work_dir,
					revision = log_entry.revision)
	
	def get_diff(self):
		if self.old_log_index == None:
			return ""
		rev1 = self.log[self.log_index].revision
		rev2 = self.log[self.old_log_index].revision
		try:
			diff_text = self.client.diff_peg("/tmp/versionstepper",
					self.work_dir,
					revision_start = rev2,
					revision_end = rev1)
		except:
			sys.stderr.write("ERROR diff failed, sleeping 10 seconds")
			sleep(10)
			diff_text = self.client.diff_peg("/tmp/versionstepper",
					self.work_dir,
					revision_start = rev2,
					revision_end = rev1)
		return diff_text

	def get_revision_info(self, log_index=None):
		if not log_index:
			log_index = self.log_index
		revision_info = {
				'author': self.log[log_index].author,
				'timestamp': datetime.fromtimestamp(self.log[log_index].date),
				'revision_id': self.log[log_index].revision.number,
				}
		return revision_info

	def get_revision_info_all(self):
		revision_info_all = []
		for i in range(0, len(self.log)-1):
			revision_info_all.append(self.get_revision_info(i))
		return revision_info_all

class GitVersionStepper(VersionStepper):
	def __init__(self, repo_url, work_dir, reuse_work_dir=False):
		self.repo_url = repo_url
		self.work_dir = work_dir
		if not reuse_work_dir:
			ret = os.system("git clone --quiet %s %s" % (repo_url, work_dir))
		self._cwd = os.getcwd()
		os.chdir(self.work_dir)
		data = os.popen("git rev-list --reverse master")
		self.rev_list = []
		for line in data.readlines():
			self.rev_list.append(line.strip())
		self.rev_index = 0
		self.old_rev_index = None
		self.update()
	
	def step_revision(self, steps=1):
		if self.rev_index + steps < 0:
			raise IndexError, 'Cannot move beyond first revision'
		elif self.rev_index + steps >= len(self.rev_list):
			raise StopIteration, 'Canot move beyond last revision'
		self.old_rev_index = self.rev_index
		self.rev_index += steps

	def update(self):
		ret = os.system("git checkout -q "+ self.rev_list[self.rev_index])
		
	def get_diff(self):
		if self.old_rev_index == None:
			return ""
		rev1 = self.rev_list[self.rev_index]
		rev2 = self.rev_list[self.old_rev_index]
		data = os.popen("git diff %s %s" % (rev2, rev1))
		diff_text = data.read()
		return diff_text

	def get_revision_info(self, rev_index=None):
		if not rev_index:
			rev_index = self.rev_index
		data = os.popen("git log -1 --pretty=format:'%ae %at' "+ \
				self.rev_list[rev_index])
		line = data.readline()
		line = unanonymize_email(line)
		parts = line.split()
		timestamp = parts[-1]
		author = " ".join(parts[:-1])
		try:
			timestamp_int = int(timestamp)
		except ValueError:
			timestamp_int = 0
		revision_info = {
				'author': author,
				'timestamp': datetime.fromtimestamp(timestamp_int),
				'revision_id': self.rev_list[rev_index],
				}
		return revision_info
	
	def get_revision_info_all(self):
		revision_info_all = []
		for i in range(0, len(self.rev_list)-1):
			revision_info_all.append(self.get_revision_info(i))
		return revision_info_all

def test_svn():
	vs = SVNVersionStepper("https://svn.blender.org/svnroot/bf-blender/trunk/blender", "/tmp/blendersvn")
	while True:
		try:
			print """Revision id: %(revision_id)s
Author: %(author)s
Timestamp: %(timestamp)s""" % vs.get_revision_info()
			#vs.fetch_next_revision()
			#vs.step_revision()
			vs.step_revision(steps=10)
			vs.update()
		except StopIteration, e:
			print "End of history."
			break

def test_git():
	vs = GitVersionStepper("git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/sparse.git", "/tmp/sparsegit")
	while True:
		try:
			print """Revision id: %(revision_id)s
Author: %(author)s
Timestamp: %(timestamp)s""" % vs.get_revision_info()
			#vs.fetch_next_revision()
			#vs.step_revision()
			vs.step_revision(steps=10)
			vs.update()
		except StopIteration, e:
			print "End of history."
			break
