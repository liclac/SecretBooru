import os, sys, re
from pysqlcipher import dbapi2
import settings

site_root = os.path.abspath(os.path.dirname(__file__))
path = lambda filename: os.path.join(site_root, filename)

def createdb(password):
	db_path = path(settings.DB_NAME)
	if os.path.exists(db_path):
		ans = raw_input("Database Exists, overwrite? (y/N) ")
		if not ans.lower() == 'y':
			return
		os.remove(db_path)
	db = dbapi2.connect(db_path)
	# Yes, this is bad, but ? doesn't work here for some reason
	db.execute("PRAGMA key = '%s'" % re.escape(password))
	with open(path('schema.sql')) as f:
		db.executescript(f.read())

def reset(password):
	db_path = path(settings.DB_NAME)
	if os.path.exists(db_path):
		ans = raw_input("Delete all data and media? (y/N) ")
		if not ans.lower() == 'y':
			return
		os.remove(db_path)
	media_path = path('media')
	for filename in [ n for n in os.listdir(media_path) if n != '.gitkeep' ]:
		os.remove(os.path.join(media_path, filename))
	
	createdb(password)

def dbshell(password):
	db = dbapi2.connect(path(settings.DB_NAME))
	db.execute("PRAGMA key = '%s'" % re.escape(password))
	while True:
		try:
			cmd = raw_input("> ")
			if cmd == '.q':
				return
			
			res = db.execute(cmd).fetchall()
			for row in res:
				if type(row) == tuple:
					print ', '.join([str(i) for i in row])
				else:
					print row
		except Exception as e:
			print "%s: %s" % (e.__class__.__name__, e)

if __name__ == '__main__':
	handlers = {
		'createdb': createdb,
		'reset': reset,
		'dbshell': dbshell
	}
	
	if len(sys.argv) <= 1 or sys.argv[1] not in handlers:
		print "-- Commands --"
		print " "
		
		print "createdb <password>"
		print "    Creates a new database with the given password."
		print " "
		
		print "reset <password>"
		print "    Deletes all content (database and media) and"
		print "    creates a new database with the given password."
		print " "
		
		print "dbshell <password>"
		print "    Starts a database shell, decrypting the database"
		print "    with the given password."
		print " "
		
		exit()
	
	handlers[sys.argv[1]](*sys.argv[2:])
