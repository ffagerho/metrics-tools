#!/usr/bin/python

import sys, bts, psycopg2
from datetime import datetime

if len(sys.argv) != 6:
	print """Usage %s <bts_id> <bts_root_url> <bts_bug_url> <bts_name> <bts_type>
	bts_type = { bugzilla, gforge }""" % (sys.argv[0])
	sys.exit(1)

start_time = datetime.now()

bts_id = int(sys.argv[1])
bts_root_url = sys.argv[2]
bts_bug_url = sys.argv[3]
bts_name = sys.argv[4]
bts_type = sys.argv[5]

if bts_type.lower() == "bugzilla":
	btsType = bts.Bugzilla
elif bts_type.lower() == "gforge":
	btsType = bts.GForge
else:
	print """Unknown BTS type: %s""" % (bts_type)
	sys.exit(1)

print "Importing bugs from %s to bug tracking system %s" % \
		(bts_name, bts_id)
b = btsType(bts_root_url, bts_bug_url, bts_name)

print "Connecting to database"

dbconn = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn.set_client_encoding('UTF8')
bts_curs = dbconn.cursor()

dbconn2 = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn2.set_client_encoding('UTF8')
person_curs = dbconn2.cursor()

inserted_bugs = 0
failed_bugs = 0

for bug in b.bugs():
	# print status
	print "CONSIDERING %s" % bug

	# if this bug already exists, skip it
	bug_res = False
	bts_curs.execute("""SELECT id from bug WHERE native_id=%(id)s AND
			bts_id=%(bts_id)s""",
			{'id': bug.id, 'bts_id': bts_id})
	bug_res = bts_curs.fetchone()
	if bug_res:
		print "SKIP bug exists (%s)" % (bug.id)
		continue

	# shortcuts
	name = bug.submitter_name
	email = bug.submitter_email

	if not name:
		if email:
			name = email

	# try to find a person with the available identifiers
	name_res, email_res = (False, False)
	if name:
		person_curs.execute("""SELECT person_id FROM identifier
			WHERE data = %(name)s LIMIT 1""", {'name': name})
		name_res = person_curs.fetchone()
	if email:
		person_curs.execute("""SELECT person_id FROM identifier
			WHERE data = %(email)s LIMIT 1""", {'email': email})
		email_res = person_curs.fetchone()

	# if neither name or email gave a match, we have an unknown submitter
	if not name_res and not email_res:
		# if neither name nor email are give, the submitter is anonymous
		if not name and not email:
			print "DECISION anonymous submitter"
			person_id = None
		# otherwise, create a person with the unique identifiers
		else:
			print "DECISION new person (%s, %s)" % (name, email)
			person_curs.execute("""INSERT INTO person (name)
				VALUES (%(name)s)""", {'name': name})
			person_curs.execute("""SELECT id FROM person
				WHERE name = %(name)s""", {'name': name})
			person_id = person_curs.fetchone()[0]
			if name == email:
				items = (email, )
			else:
				items = (name, email)
			for item in items:
				person_curs.execute("""INSERT INTO identifier
					(person_id, data) VALUES (%(person_id)s, %(data)s)""",
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

	# now insert the bug
	q = bts_curs.mogrify("""INSERT INTO bug
		(native_id, bts_id, title, creation_time, "type", submitter, status,
		severity, product, component)
		VALUES
		(%(native_id)s, %(bts_id)s, %(title)s, %(creation_time)s, %(type)s,
		%(submitter)s, %(status)s, %(severity)s, %(product)s,
		%(component)s)""",
		{'native_id': bug.id,
			'bts_id': bts_id,
			'title': bug.title,
			'creation_time': bug.creation_time,
			'type': bug.type,
			'submitter': person_id,
			'status': bug.status,
			'severity': bug.severity,
			'product': bug.product,
			'component': bug.component,
			})
	bts_curs.execute(q)
	dbconn.commit()
	inserted_bugs += 1

end_time = datetime.now()
print """Inserted bugs: %d
Failed bugs: %d
Total: %d
Total time elapsed: %s
""" % (inserted_bugs, failed_bugs, inserted_bugs + failed_bugs,
		end_time - start_time),
