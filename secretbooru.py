#!/usr/bin/env python
# encoding: utf-8
import os, re
import urllib2
from flask import Flask, session, request, g
from flask import url_for, redirect, abort, render_template, flash
from pysqlcipher import dbapi2

from models import Post
from util import path

app = Flask(__name__)
app.config.from_object('settings')
app.config.from_object('secrets')

site_root = os.path.abspath(os.path.dirname(__file__))

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
		#return (post.key, 200, [('Content-Type', 'text/plain')])
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
	if request.method == 'POST':
		remote = urllib2.urlopen(request.form['url'])
		info = remote.info()
		mime = info['Content-Type']
		
		post = Post()
		post.mime = mime
		post.save()
		
		post.set_data(remote.read(), mime.split('/')[-1])
		
		return redirect(url_for('image', id=post.id))
	return render_template('import.html')

if __name__ == '__main__':
	app.run()
