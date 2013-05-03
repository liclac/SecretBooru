#!/usr/bin/env python
# encoding: utf-8
import os, re
import urllib2
from datetime import datetime
from flask import Flask, session, request, g
from flask import url_for, redirect, abort, render_template, flash
from pysqlcipher import dbapi2
from Crypto.Cipher import AES
from Crypto import Random

app = Flask(__name__)
app.config.from_object('settings')
app.config.from_object('secrets')

site_root = os.path.abspath(os.path.dirname(__file__))
path = lambda filename: os.path.join(site_root, filename)

class Post(object):
	id = 0
	added = None
	rating = 'q'
	mime = 'text/plain'	#lolnope
	key = None
	
	basequery = "SELECT ROWID, added, rating, mime, key FROM posts"
	
	def __init__(self, id, added, rating, mime, key):
		self.id = id
		self.added = datetime.strptime(added, '%Y-%m-%d %H:%M:%S')
		self.mime = mime
		self.rating = rating
	
	def get_data(self, thumb=False):
		with open(path('media/%s' % (self.id, '_thumb' if thumb else ''))) as f:
			return f.read()
	
	@classmethod
	def get(cls, id):
		c = g.db.cursor()
		rec = c.execute(cls.basequery + " WHERE ROWID = ?", [id]).fetchone()
		if rec is None:
			return None
		return cls(*rec)
	
	@classmethod
	def all(cls):
		c = g.db.cursor()
		l = []
		for rec in c.execute(cls.basequery).fetchall():
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
		return (post.get_data(True), 200, [('Content-Type', post.mime)])
	else:
		abort(404)

@app.route('/posts/<int:id>/thumb')
def thumb(id):
	post = Post.get(id)
	if post:
		return (post.get_data(), 200, [('Content-Type', post.mime)])
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
		key = Random.new().read(64)
		
		c = g.db.cursor()
		c.execute("INSERT INTO posts (rating, mime, key) VALUES (?, ?, ?)", ('q', mime, buffer(key)))
		id = c.lastrowid
		
		with open(path('media/%s' % id), 'wb') as local:
			data = remote.read()
			local.write(data)
			
			img = Image.open(StringIO(data))
			img.thumbnail((200, 200), Image.ANTIALIAS)
			img.save(path('media/%s_thumb' % id), mime.split('/')[-1])
			
			del img
			del data
		
		g.db.commit()
		return redirect(url_for('post', id=id))
	return render_template('import.html', post=post)

if __name__ == '__main__':
	app.run()
