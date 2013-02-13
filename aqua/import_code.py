#!/usr/bin/python

import sys, os, versionstepper, metrics, mltools, psycopg2
from datetime import datetime
from random import randint
from os.path import join
from util import rmall

if len(sys.argv) < 5:
	print \
"""Usage: %s <vcs_id> <vcs_url> <vcs_type> <full_run_interval>
          [metric ...]
    vcs_type = { svn, git }
    full_run_interval = 1...n
    metric = { cccc, static-c, static-python, diffstats,
               filetypes, vcslog }""" % (sys.argv[0])
	sys.exit(1)

start_time = datetime.now()

vcs_id = int(sys.argv[1])
vcs_url = sys.argv[2]
vcs_type = sys.argv[3]
full_run_interval = int(sys.argv[4])
if full_run_interval < 1:
	full_run_interval = 1
user_metrics = set(sys.argv[5:])

if vcs_type.lower() == "svn":
	versionStepperType = versionstepper.SVNVersionStepper
elif vcs_type.lower() == "git":
	versionStepperType = versionstepper.GitVersionStepper
else:
	print """Unknown VCS type: %s""" % (vcs_type)
	sys.exit(1)

# define mappings between metrics and database tables
metric_table_mappings = {
		'cccc': 'cccc_metrics',
		'static-c': 'static_metrics',
		'static-python': 'static_metrics',
		'diffstats': 'diffstats_metrics',
		'filetypes': 'filetypes',
		'vcslog': 'revision',
		}

# define mappings between dictionary keys and table columns
pass

print "Importing code from %s to vcs %s, running full metrics every %d revision(s)" % (vcs_url, vcs_id, full_run_interval)
print "Metrics to run:", user_metrics
work_dir = join("/tmp", str(randint(100000, 999999)))
sys.stderr.write("DEBUG work_dir: %s\n" % (work_dir))

print "STATUS checking out repository"
vs = versionStepperType(vcs_url, work_dir)

print "Connecting to database"

dbconn = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn.set_client_encoding('UTF8')
metric_curs = dbconn.cursor()

dbconn2 = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn2.set_client_encoding('UTF8')
person_curs = dbconn2.cursor()

start_tick = datetime.now()
revision_counter = 0
total_revisions = 0

# print status
revision_info = vs.get_revision_info()
print "CONSIDERING rev %s, %s, revision_counter %d" % \
		(revision_info['revision_id'], revision_info['timestamp'],
				revision_counter)

while True:
	metrics_to_run = set()
	if revision_counter == 0:
		metrics_to_run = metrics.all_metrics & user_metrics
	else:
		metrics_to_run = metrics.light_metrics & user_metrics
	
	# print status
	print "DECISION run metrics %s" % (metrics_to_run)
	
	results = metrics.dispatch(vs, metrics_to_run)

	# find the person that has made this commit
	name, email = mltools.parse_from_header(revision_info['author'])
	if not name:
		if email:
			name = email
		else:
			name = "Unknown"
			email = name

	name_res, email_res = (False, False)
	if name:
		person_curs.execute("""SELECT person_id FROM identifier
			WHERE data = %(name)s LIMIT 1""", {'name': name})
		name_res = person_curs.fetchone()
	if email:
		person_curs.execute("""SELECT person_id FROM identifier
			WHERE data = %(email)s LIMIT 1""", {'email': email})
		email_res = person_curs.fetchone()
	
	# if neither name nor email gave a match, we have an unknown committer
	if not name_res and not email_res:
		# create the person with the unique indentifiers
		print "DECISION new person (%s, %s)" % (name, email)
		person_curs.execute("""INSERT INTO person (name) VALUES
			(%(name)s)""", {'name': name})
		person_curs.execute("""SELECT id FROM person WHERE name = %(name)s""",
				{'name': name})
		person_id = person_curs.fetchone()[0]
		if name and email:
			items = (name, email)
		else:
			items = (name, )
		for item in items:
			person_curs.execute("""INSERT INTO identifier (person_id, data)
				VALUES (%(person_id)s, %(data)s)""",
				{'person_id': person_id, 'data': item})
		dbconn2.commit()

	# else, if name didn't give a match but email did, add name identifier
	elif not name_res:
		print "DECISION new name identifier (%s, %s)" % (name, email)
		person_id = email_res[0]
		person_curs.execute("""INSERT INTO identifier (person_id, data)
			VALUES (%(person_id)s, %(data)s)""",
			{'person_id': person_id, 'data': name})
		dbconn2.commit()

	# else, if email didn't give a match but name did, add email identifier
	elif not email_res:
		print "DECISION new email identifier (%s, %s)" % (name, email)
		person_id = name_res[0]
		person_curs.execute("""INSERT INTO identifier (person_id, data)
			VALUES (%(person_id)s, %(data)s)""",
			{'person_id': person_id, 'data': email})
		dbconn2.commit()

	# else, they both gave a match and we just store person_id and go on
	else:
		print "DECISION person and identifier exist (%s, %s)" % (name, email)
		person_id = name_res[0]

	# insert this revision
	metric_curs.execute("""INSERT INTO revision
		(vcs_id, native_revision, timestamp, author) VALUES
		(%(vcs_id)s, %(revision_id)s, %(timestamp)s, %(person_id)s)""",
		{'vcs_id': vcs_id, 'revision_id': revision_info['revision_id'],
			'timestamp': revision_info['timestamp'], 'person_id': person_id})
	metric_curs.execute("""SELECT id FROM revision WHERE
		vcs_id = %(vcs_id)s AND native_revision = %(revision_id)s""",
		{'vcs_id': vcs_id, 'revision_id': revision_info['revision_id']})
	rev_id = metric_curs.fetchone()[0]

	for metric in results:
		if metric == 'cccc':
			# insert cccc metrics
			results[metric]['rev_id'] = rev_id
			metric_curs.execute("""INSERT INTO cccc_metrics
				(revision_id, sloc, cloc, rejloc, cyclomatic, if, nom) VALUES
				(%(rev_id)s, %(sloc)s, %(cloc)s, %(rejloc)s, %(cyclomatic)s,
				%(if)s, %(nom)s)""", results[metric])
			for module in results[metric]['modules']:
				results[metric]['modules'][module]['rev_id'] = rev_id
				results[metric]['modules'][module]['path'] = module
				metric_curs.execute("""INSERT INTO cccc_module_metrics
					(revision_id, path, cbo, dit, noc, wmc, fanin, fanout, if)
					VALUES (%(rev_id)s, %(path)s, %(cbo)s, %(dit)s, %(noc)s,
						%(wmc)s, %(fanin)s, %(fanout)s, %(if)s)""",
						results[metric]['modules'][module])
		elif metric == 'diffstats':
			# insert diffstats metrics
			results[metric]['rev_id'] = rev_id
			metric_curs.execute("""INSERT INTO diffstats_metrics
				(revision_id, files_changed, loc_add, loc_del) VALUES
				(%(rev_id)s, %(files_changed)s, %(loc_add)s, %(loc_del)s)""",
				results[metric])
		elif metric == 'filetypes':
			# insert filetypes metrics
			for file in results[metric]:
				metric_curs.execute("""INSERT INTO filetypes
					(revision_id, path, mime_type, compression) VALUES
					(%(rev_id)s, %(path)s, %(mime_type)s, %(compression)s)""",
					{'rev_id': rev_id, 'path': file,
						'mime_type': results[metric][file]['mime_type'],
						'compression': results[metric][file]['compression']})
		elif metric.startswith('static-'):
			# insert static metrics
			results[metric]['rev_id'] = rev_id
			if metric == 'static-c':
				results[metric]['statictype'] = 'c'
			elif metric == 'static-python':
				results[metric]['statictype'] = 'python'
			else:
				continue

			metric_curs.execute("""INSERT INTO static_metrics
						(revision_id, "type", sloc, ploc, bloc, cloc, nom,
						cyclomatic, fanin_tot, fanout_tot) VALUES
						(%(rev_id)s, %(statictype)s, %(sloc)s, %(ploc)s,
						%(bloc)s, %(cloc)s, %(nom)s, %(cyclomatic)s,
						%(fanin_tot)s, %(fanout_tot)s)""", results[metric])
			for module in results[metric]['module_info']:
				results[metric]['module_info'][module]['rev_id'] = rev_id
				results[metric]['module_info'][module]['path'] = module
				metric_curs.execute("""INSERT INTO static_module_metrics
						(revision_id, path, sloc, ploc, bloc, cloc, cyclomatic,
						fanin, fanout) VALUES
						(%(rev_id)s, %(path)s, %(sloc)s, %(ploc)s, %(bloc)s,
						%(cloc)s, %(cyclomatic)s, %(fanin)s, %(fanout)s)""",
						results[metric]['module_info'][module])

	total_revisions += 1
	end_tick = datetime.now()
	print """STATISTICS time elapsed last cycle: %s
STATISTICS total time elapsed: %s
STATISTICS total revisions: %d""" % (end_tick - start_tick,
		end_tick - start_time, total_revisions)
	start_tick = datetime.now()

	# print status
	revision_info = vs.get_revision_info()
	print "CONSIDERING rev %s, %s, revision_counter %d" % \
			(revision_info['revision_id'], revision_info['timestamp'],
					revision_counter)

	try:
		vs.step_revision()
		revision_counter += 1
		if revision_counter == full_run_interval:
			print "DECISION commit database transaction"
			dbconn.commit()
			print "DECISION update working directory"
			vs.update()
			revision_counter = 0
	except StopIteration, e:
		print "DECISION end of history"
		break

end_time = datetime.now()
print """Total revisions: %d
Total time elapsed: %s
""" % (total_revisions, end_time - start_time),
