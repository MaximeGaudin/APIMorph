#! /usr/bin/env python 

import handlers
import bottle
from bottle import run, default_app

if __name__ == '__main__':
  run(host='localhost', port=8091, reloader=True, debug=True)

application = default_app()
application.catchall = False
