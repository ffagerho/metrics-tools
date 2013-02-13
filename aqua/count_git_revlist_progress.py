#!/usr/bin/python

import sys

if len(sys.argv) != 2:
	print "Usage: %s rev-id < rev-id-file" % (sys.argv[0])
	sys.exit(1)

rev_id = sys.argv[1]

rev_id_found = False
after_lines = 0
before_lines = 0
lines = 0

for line in sys.stdin.readlines():
	if line.strip() == rev_id:
		rev_id_found = True
	if rev_id_found:
		after_lines += 1
	else:
		before_lines += 1
	lines += 1

print """Done: %d (%d%%) To do: %d (%d%%) Total: %d""" % \
		(after_lines,
				int(float(after_lines)/float(lines)*100),
				before_lines,
				int(float(before_lines)/float(lines)*100),
				lines)
