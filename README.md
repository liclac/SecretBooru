SecretBooru
===========

SecretBooru is a 'booru clone similar to [Gelbooru](http://gelbooru.com/) and [Danbooru](http://danbooru.donmai.us/), that encrypts stored images and decrypts them on the fly.

Security
--------
In a few points, SecretBooru:

* Encrypts every image with an unique key
* Stores keys along with the image metadata and tags in a database
* Encrypts the database with an user-provided password
* Doesn't "know" the correct password
* Regenerates the session key on every launch

Note: I'm no security expert or anything. I just came up with a fun idea and built it.

Requirements
------------
Native Packages:

* Python 2.7
* libjpeg (for PIL)
* libpng (for PIL)

PyPi Packages (install with `pip`)`:

* Flask
* PIL
* pycrypto
* pysqlcipher

Installation
------------
* Install Python 2.7 (it doesn't run on 3.x yet)
* Install libjpeg and libpng
* Install pip
* Run `pip install flask PIL pycrypto pysqlcipher`
* In the installation directory, run `python cmd.py createdb "<YOUR PASSWORD HERE>"`

Usage
-----
* In the installation directory, run `python secretbooru.py`
* Open `localhost:5000` in your browser
