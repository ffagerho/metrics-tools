import os
from cStringIO import StringIO

def rmall(dirPath):
	"""Recursively remove an entire directory tree."""
	namesHere = os.listdir(dirPath)
	for name in namesHere:
		path = os.path.join(dirPath, name)
		if not os.path.isdir(path):
			os.remove(path)
		else:
			rmall(path)
	os.rmdir(dirPath)

def diffstat(diff):
	header_stage = 0
	in_hunk = False
	files_count = 0
	add_count = 0
	del_count = 0

	buf = StringIO(diff)
	
	for line in buf.readlines():
		if line.startswith("index ") or line.startswith("Index: "):
			header_stage = 0
			in_hunk = False
		elif line.startswith("--- "):
			if header_stage == 2:
				del_count += 1
			else:
				header_stage = 1
		elif line.startswith("+++ "):
			if header_stage == 2:
				add_count += 1
			elif header_stage == 1:
				header_stage = 2
				files_count += 1
		elif line.startswith("@@ "):
			if header_stage == 2:
				in_hunk = True
		elif line.startswith("+"):
			if in_hunk:
				add_count += 1
		elif line.startswith("-"):
			if in_hunk:
				del_count += 1
				
	return (files_count, add_count, del_count)
