#!/usr/bin/env python
# encoding: utf-8
import os, re
from flask import Flask, session, request, g
from flask import url_for, redirect, render_template, flash
from pysqlcipher import dbapi2

app = Flask(__name__)
app.config.from_object('settings')
app.config.from_object('secrets')

site_root = os.path.abspath(os.path.dirname(__file__))
path = lambda filename: os.path.join(site_root, filename)

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
	post = None
	return render_template('post.html', post=post)

if __name__ == '__main__':
	app.run()
