from flask import Flask
from werkzeug.contrib.cache import SimpleCache

import mediabrowser

import os


"""Run via WSGI"""
root = os.getenv("MEDIABROWSER_ROOT")
if not root:
	raise Exception('Must set MEDIABROWSER_ROOT variable')
cache = SimpleCache()
application = Flask("mediabrowser-demo")
application.register_blueprint(mediabrowser.build(root, cache))
