import mediabrowser

from flask import Flask
from werkzeug.contrib.cache import SimpleCache

import os
import logging

logging.basicConfig(level=logging.INFO)
root = os.getenv("MEDIABROWSER_ROOT")
if not root:
	raise Exception('Must set MEDIABROWSER_ROOT variable')
cache = SimpleCache()
application = Flask("mediabrowser-demo")
application.register_blueprint(mediabrowser.build(root, cache))

def reverse_proxified(app):
    """
    Configure apache as:
      RequestHeader set X-Script-Name /videos
    """
    def wsgi_call(environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return app(environ, start_response)
    return wsgi_call

application = reverse_proxified(application.wsgi_app)
