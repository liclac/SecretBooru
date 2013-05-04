import os
import urllib2
from datetime import datetime
from cStringIO import StringIO
from flask import g
from crypto import dencrypt, ddecrypt
from util import path, zerofill_delete

class Post(object):
	id = -1
	added = None
	rating = 'q'
	mime = 'text/plain'	#lolnope
	key = ''
	
	base_query = "SELECT ROWID, added, rating, mime, key FROM posts"
	date_format = '%Y-%m-%d %H:%M:%S.%f'
	
	def __init__(self, id=-1, added=datetime.now(), rating='q', mime='', key=None):
		self.id = id
		self.added = added
		self.rating = rating
		self.mime = mime
		self.key = key
		
		if type(self.added) == str:
			self.added = datetime.strptime(added, self.date_format)
	
	def path(self, thumb=False):
		suffix = ''
		return path('media/%s%s' % (self.id, ('_thumb' if thumb else '')))
	
	def set_tags(self, tags):
		c = g.db.cursor()
		c.execute("DELETE FROM posts_tags WHERE pid = ?", (self.id,))
		for tagname in tags:
			tag = Tag.get_or_create(tagname)
			c.execute("INSERT INTO posts_tags (pid, tid) VALUES (?, ?)", (self.id, tag.id))
	
	def get_tags(self):
		c = g.db.cursor()
		rels = c.execute("SELECT tid FROM posts_tags WHERE pid = ?", (self.id,)).fetchall()
		tags = [ Tag.get_by_id(rel[0]) for rel in rels ]
		return tags
	
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
	
	def get_data(self, thumb=False):
		return ddecrypt(self.key, self.path(thumb))
	
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
	
	def delete(self):
		zerofill_delete(self.path(thumb=True))
		zerofill_delete(self.path(thumb=False))
		c = g.db.cursor()
		c.execute("DELETE FROM posts WHERE ROWID = ?", (self.id,))
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
	
	@classmethod
	def download(cls, url, tagnames=[], **kwargs):
		remote = urllib2.urlopen(url)
		info = remote.info()
		mime = info['Content-Type']
		
		post = cls(mime=mime, **kwargs)
		post.save()
		post.set_tags(tagnames)
		post.set_data(remote.read(), mime.split('/')[-1])
		
		return post

class Tag(object):
	id = -1
	name = ""
	type = ""
	
	base_query = "SELECT ROWID, name, type FROM tags"
	
	def __init__(self, id=-1, name='Untitled', type='standard'):
		self.id = id
		self.name = name
		self.type = type
	
	def get_posts(self):
		c = g.db.cursor()
		rels = c.execute("SELECT pid FROM posts_tags WHERE tid = ?", (self.id,)).fetchall()
		posts = [ Post.get(rel[0]) for rel in rels ]
		return posts
	
	# NOTE: This function does NOT commit!
	@classmethod
	def get_or_create(cls, name, type='standard'):
		c = g.db.cursor()
		rec = c.execute(cls.base_query + " WHERE name = ?", (name,)).fetchone()
		if rec is None:
			tag = cls(name=name, type=type)
			c.execute("INSERT INTO tags (name, type) VALUES (?, ?)", (tag.name, tag.type))
			tag.id = c.lastrowid
			return tag
		else:
			return cls(*rec)
	
	@classmethod
	def get_by_id(cls, id):
		c = g.db.cursor()
		rec = c.execute(cls.base_query + " WHERE ROWID = ?", (id,)).fetchone()
		if rec == None:
			return None
		else:
			return cls(*rec)
	
	@classmethod
	def all(cls):
		c = g.db.cursor()
		l = []
		for rec in c.execute(cls.base_query + " ORDER BY name ASC").fetchall():
			l.append(cls(*rec))
		return l
	
	def __str__(self):
		return "<%s>" % self.name
