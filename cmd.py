import os, sys, re
import urllib2
from flask import g
from pysqlcipher import dbapi2
import settings
from models import Post

from secretbooru import app, db_connect

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
	#db = dbapi2.connect(path(settings.DB_NAME))
	#db.execute("PRAGMA key = '%s'" % re.escape(password))
	db = db_connect(password)
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

def import_gbfavs(password, userID):
	import xml.etree.ElementTree as ET
	
	favIDs = []
	offset = 0
	while True:
		data = urllib2.urlopen('http://gelbooru.com/index.php?page=favorites&s=view&id=%s&pid=%s' % (userID, offset)).read()
		
		matches = re.findall(r'href=\"index\.php\?page=post&amp;s=view&amp;id=(\d+)\"', data)
		if len(matches) == 0:
			break
		favIDs += matches
		offset = offset + len(matches)
	print "Found %s Favorites!" % len(favIDs)
	
	ctx = app.test_request_context()
	ctx.push()
	
	g.db = db_connect(password)
	
	for favID in reversed(favIDs):
		print "Downloading http://gelbooru.com/index.php?page=post&s=view&id=%s" % favID
		data = urllib2.urlopen('http://gelbooru.com/index.php?page=dapi&s=post&q=index&id=%s' % favID).read()
		root = ET.fromstring(data)
		if len(root) < 1:
			print "--> Not Found!"
		
		d = root[0].attrib
		
		post = Post.download(
			url=d['file_url'],
			tagnames=d['tags'].strip().split(' '),
			rating=d['rating']
		)
	ctx.pop()

if __name__ == '__main__':
	handlers = {
		'createdb': createdb,
		'reset': reset,
		'dbshell': dbshell,
		'import-gbfavs': import_gbfavs
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
		
		print "import_gbfavs <password> <userID>"
		print "    Imports all favorites for the given Gelbooru user."
		print "    Note that UserID takes an *user ID*, not an username."
		print "    To find yours, click Account -> My Profile and check"
		print "    the 'id=' parameter in the URL."
		print " "
		
		exit()
	
	handlers[sys.argv[1]](*sys.argv[2:])
