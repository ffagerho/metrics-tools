import psycopg2

dbconn = psycopg2.connect(database="foss", user="foss",
		password="f055", host="localhost")
dbconn.set_client_encoding('UTF8')
curs = dbconn.cursor()
