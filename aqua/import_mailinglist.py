#!/usr/bin/python

import sys, mltools, psycopg2
from datetime import datetime

if len(sys.argv) != 3:
	print "Usage: %s <mailinglist_id> <root_dir>" % (sys.argv[0])
	sys.exit(1)

start_time = datetime.now()

mailinglist_id = int(sys.argv[1])
root = sys.argv[2]
print "Importing mailing list messages from %s to mailing list %d" % \
		(root, mailinglist_id)
mailinglist = mltools.archivefactory(root)

print "Connecting to database"

dbconn = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn.set_client_encoding('ISO-8859-1')
ml_curs = dbconn.cursor()

dbconn2 = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn2.set_client_encoding('ISO-8859-1')
person_curs = dbconn2.cursor()

inserted_messages = 0
failed_messages = 0

for message in mailinglist.messages():
	# skip pseudo-message
	if message.has_key('subject') and message['subject'] == \
			"DON'T DELETE THIS MESSAGE -- FOLDER INTERNAL DATA":
		continue

	# skip messages from nobody
	if not message.has_key('from'):
		print """SKIPPED (No From header)"""
		failed_messages += 1
		continue

	# extract name and email
	name, email = mltools.parse_from_header(message['from'])

	# special hack for lists that obscure the from email address with
	# a list-specific address
	if email == 'bf-committers@blender.org' or \
			email == 'bf-python@blender.org':
		email = name

	# some data checks
	if message.has_key('subject'): subject = message['subject']
	else: subject = ''

	if message.has_key('message-id'): msgid = message['message-id']
	else: msgid = 'broken-message-id'

	try:
		if message.has_key('date'): date = mltools.fix_date(message['date'])
		else: date = '1970-01-01'
	except mltools.FixDateError, e:
		print """SKIPPED (Malformed date: %s)""" % (e)
		failed_messages += 1
		continue

	# print status
	print "CONSIDERING (%s, %s, %s, ...%s)" % \
			(name, email, date, mailinglist.path[-50:])

	if not name:
		if not email:
			# something is seriously wrong with this message, skip it
			print "SKIPPING (no name or email)"
			failed_messages += 1
			continue
		else:
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

	# if neither name or email gave a match, create the person with
	# the unique identifiers
	if not name_res and not email_res:
		print "DECISION new person (%s, %s)" % (name, email)
		person_curs.execute("""INSERT INTO person (name) VALUES (%(name)s)""",
				{'name': name})
		person_curs.execute("""SELECT id FROM person WHERE name = %(name)s""",
				{'name': name})
		person_id = person_curs.fetchone()[0]
		if name == email:
			items = (email, )
		else:
			items = (name, email)
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

	# do we have a in-reply-to header? if so, try to find messages with
	# these message-ids
	# NOT IMPLEMENTED

	# now insert the message
	ml_curs.execute("""INSERT INTO post
		(mailinglist_id, "from", subject, message_id, timestamp) VALUES
		(%(mailinglist_id)s, %(from)s, %(subject)s, %(message_id)s,
		%(timestamp)s)""",
		{'mailinglist_id': mailinglist_id,
			'from': person_id,
			'subject': subject,
			'message_id': msgid,
			'timestamp': date})
	
	dbconn.commit()
	inserted_messages += 1

stop_time = datetime.now()
print """Inserted messages: %d
Failed messages: %d
Total: %d
Total time elapsed: %s
""" % (inserted_messages,
		failed_messages,
		inserted_messages + failed_messages,
		stop_time - start_time )
