import os, sys, re
from pysqlcipher import dbapi2
import settings

site_root = os.path.abspath(os.path.dirname(__file__))
path = lambda filename: os.path.join(site_root, filename)

def createdb(password):
	db_path = path(settings.DB_NAME)
	if os.path.exists(db_path):
		ans = raw_input("Database Exists, overwrite? (y/N)")
		if not ans.lower() == 'y':
			return
		os.remove(db_path)
	db = dbapi2.connect(db_path)
	# Yes, this is bad, but ? doesn't work here for some reason
	db.execute("PRAGMA key = '%s'" % re.escape(password))
	with open(path('schema.sql')) as f:
		db.executescript(f.read())

if __name__ == '__main__':
	handlers = {
		'createdb': createdb,
	}
	
	if len(sys.argv) <= 1 or sys.argv[1] not in handlers:
		print "-- Commands --"
		print " "
		
		print "createdb <password>"
		print "    Creates a new database with the given password."
		print " "
		
		exit()
	
	handlers[sys.argv[1]](*sys.argv[2:])
