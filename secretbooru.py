#!/usr/bin/env python
# encoding: utf-8
from flask import Flask, session, request
from flask import url_for, redirect, render_template

app = Flask(__name__)
app.config.from_object('settings')
app.config.from_object('secrets')

@app.before_request
def check_login():
	if request.endpoint != 'login' and not request.path.startswith('/static/') and ('authorized' not in session or not session['authorized']):
		return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		if request.form['password'] == app.config['SITE_PASSWORD']:
			session['authorized'] = True
		return redirect(url_for('home'))
	return render_template('login.html')

@app.route('/')
def home():
	return render_template('home.html')

if __name__ == '__main__':
	app.run()
