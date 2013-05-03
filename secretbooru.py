#!/usr/bin/env python
# encoding: utf-8
import os, re
from datetime import datetime
from flask import Flask, session, request, g
from flask import url_for, redirect, abort, render_template, flash
from pysqlcipher import dbapi2

app = Flask(__name__)
app.config.from_object('settings')
app.config.from_object('secrets')

site_root = os.path.abspath(os.path.dirname(__file__))
path = lambda filename: os.path.join(site_root, filename)

class Post(object):
	id = 0
	added = None
	rating = 'q'
	key = None
	
	def __init__(self, id, added_ut, rating, key):
		self.id = id
		self.added = datetime.fromtimestamp(added_ut)
		self.rating = rating
	
	@classmethod
	def get(cls, id):
		c = g.db.cursor()
		rec = c.execute("SELECT ROWID, added, rating, key FROM posts WHERE ROWID = ?", [id]).fetchone()
		if rec is None:
			return None
		return cls(rec[0], rec[1], rec[2])

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

@app.route('/login/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		#if request.form['password'] == app.config['SITE_PASSWORD']:
		#	session['authorized'] = True
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

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/posts/')
def posts():
	posts = None
	return render_template('posts.html', posts=posts)

@app.route('/posts/<int:id>/')
def post(id):
	post = Post.get(id)
	if post is None:
		abort(404)
	return render_template('post.html', post=post)

if __name__ == '__main__':
	app.run()
