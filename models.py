from datetime import datetime
from cStringIO import StringIO
from flask import g
from crypto import dencrypt, ddecrypt
from util import path

class Post(object):
	id = 0
	added = None
	rating = 'q'
	mime = 'text/plain'	#lolnope
	key = ''
	
	base_query = "SELECT ROWID, added, rating, mime, key FROM posts"
	date_format = '%Y-%m-%d %H:%M:%S'
	
	def __init__(self, id=-1, added=datetime.now(), rating='q', mime='', key=None):
		self.id = id
		self.added = added
		self.rating = rating
		self.mime = mime
		self.key = key
	
	def path(self, thumb=False):
		suffix = ''
		return path('media/%s%s' % (self.id, ('_thumb' if thumb else '')))
	
	def get_data(self, thumb=False):
		return ddecrypt(self.key, self.path(thumb))
	
	def set_data(self, data, format, thumb=False, make_thumb=True):
		if not thumb:
			self.key = dencrypt(data, self.path(thumb))
			c = g.db.cursor()
			c.execute("UPDATE posts SET key = ? WHERE ROWID = ?", (self.key, self.id))
			g.db.commit()
			
			if make_thumb:
				self.make_thumbnail(data, format)
		else:
			dencrypt(data, self.path(thumb), self.key)
	
	def make_thumbnail(self, data, format):
		import Image
		
		img = Image.open(StringIO(data))
		img.thumbnail((200, 200), Image.ANTIALIAS)
		#img.save(path('media/%s_thumb' % id), format)
		d = StringIO()
		img.save(d, format)
		self.set_data(d.getvalue(), format, thumb=True)
	
	def save(self):
		c = g.db.cursor()
		if self.id < 0:
			c.execute("INSERT INTO posts (added, rating, mime) VALUES (?, ?, ?)",
				(self.added, self.rating, self.mime))
			self.id = c.lastrowid
		else:
			c.execute("UPDATE posts SET added = ?, rating = ?, mime = ? WHERE ROWID = ?",
				(self.added, self.rating, self.mime, self.id))
		g.db.commit()
	
	@classmethod
	def get(cls, id):
		c = g.db.cursor()
		rec = c.execute(cls.base_query + " WHERE ROWID = ?", [id]).fetchone()
		if rec is None:
			return None
		return cls(*rec)
	
	@classmethod
	def all(cls):
		c = g.db.cursor()
		l = []
		for rec in c.execute(cls.base_query).fetchall():
			l.append(cls(*rec))
		return l