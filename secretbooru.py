#!/usr/bin/env python
# encoding: utf-8
import os, re, struct
import urllib2
from datetime import datetime
from flask import Flask, session, request, g
from flask import url_for, redirect, abort, render_template, flash
from pysqlcipher import dbapi2
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

app = Flask(__name__)
app.config.from_object('settings')
app.config.from_object('secrets')

site_root = os.path.abspath(os.path.dirname(__file__))
path = lambda filename: os.path.join(site_root, filename)

# http://stackoverflow.com/questions/12562021/aes-decryption-padding-with-pkcs5-python
BS = AES.block_size
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[0:-ord(s[-1])]

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
		self.added = added#datetime.strptime(added, self.date_format)
		self.rating = rating
		self.mime = mime
		self.key = key
	
	def path(self, thumb=False):
		suffix = ''
		return path('media/%s%s' % (self.id, ('_thumb' if thumb else '')))
	
	def get_data(self, thumb=False):
		with open(self.path(thumb)) as f:
			iv = 'a'*AES.block_size #f.read(AES.block_size)
			cipher = AES.new(self.key, AES.MODE_CBC, iv)
			data = cipher.decrypt(unpad(f.read()))
			return data
	
	def set_data(self, data, format, thumb=False, make_thumb=True):
		c = g.db.cursor()
		rand = Random.new()
		self.key = rand.read(32)
		iv = 'a'*AES.block_size #rand.read(AES.block_size)
		c.execute("UPDATE posts SET key = ? WHERE ROWID = ?", (buffer(self.key), self.id))
		
		cipher = AES.new(self.key, AES.MODE_CBC, iv)
		cipherdata = cipher.encrypt(pad(data))
		
		with open(self.path(thumb), 'wb') as f:
			f.write(iv)
			f.write(data)
		
		g.db.commit()
		
		if not thumb and make_thumb:
			self.make_thumbnail(data, format)
	
	def make_thumbnail(self, data, format):
		from cStringIO import StringIO
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

def db_connect(password):
	db = dbapi2.connect(path(app.config['DB_NAME']))
	# TODO: Use something better than re.escape for this
	# For some reason, normal '?' placeholders don't work for PRAGMA's
	db.execute("PRAGMA key = '%s'" % re.escape(password))
	return db



@app.before_request
def before_request():
	if request.endpoint != 'login' and not request.path.startswith('/static/'):
		if 'password' not in session or not session['password']:
			return redirect(url_for('login'))
		else:
			g.db = db_connect(session['password'])

@app.teardown_request
def teardown_request(exception):
	if hasattr(g, 'db'):
		g.db.close()



@app.route('/')
def home():
	return render_template('home.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		db = db_connect(request.form['password'])
		success = True
		
		# The database will fail to decrypt if the password
		# is invalid, and then throw an error if you try
		# to query it. So... let's query it.
		try:
			db.execute("SELECT COUNT(*) FROM sqlite_master")
		except dbapi2.DatabaseError:
			success = False
			flash("Invalid Password")
		
		if success:
			session['password'] = request.form['password']
			return redirect(url_for('home'))
	return render_template('login.html')

@app.route('/logout/')
def logout():
	session.clear()
	return redirect(url_for('login'))

@app.route('/posts/')
def posts():
	posts = Post.all()
	return render_template('posts.html', posts=posts)

@app.route('/posts/<int:id>/')
def post(id):
	post = Post.get(id)
	if not post:
		abort(404)
	return render_template('post.html', post=post)

@app.route('/posts/<int:id>/image')
def image(id):
	post = Post.get(id)
	if post:
		return (post.get_data(), 200, [('Content-Type', post.mime)])
	else:
		abort(404)

@app.route('/posts/<int:id>/thumb')
def thumb(id):
	post = Post.get(id)
	if post:
		return (post.get_data(True), 200, [('Content-Type', post.mime)])
	else:
		abort(404)

@app.route('/posts/import/', methods=['GET', 'POST'])
def import_():
	from StringIO import StringIO
	import Image
	
	if request.method == 'POST':
		remote = urllib2.urlopen(request.form['url'])
		info = remote.info()
		mime = info['Content-Type']
		#key = Random.new().read(64)
		
		#c = g.db.cursor()
		#c.execute("INSERT INTO posts (rating, mime) VALUES (?, ?)", ('q', mime))
		#id = c.lastrowid
		
		#post = Post.get(id)
		#post.set_data(remote.read(), mime.split('/')[-1])
		
		#g.db.commit()
		
		post = Post()
		post.mime = mime
		post.save()
		
		post.set_data(remote.read(), mime.split('/')[-1])
		
		return redirect(url_for('post', id=post.id))
	return render_template('import.html')

if __name__ == '__main__':
	app.run()
