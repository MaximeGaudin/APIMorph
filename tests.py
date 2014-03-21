#!/user/bin/env python
from webtest import TestApp
import json

def application(environ, start_response):
	body = json.dumps({'id': 1, 'value': 'value'})
	headers = [('Content-Type', 'application/json; charset=utf8'),
                ('Content-Length', str(len(body)))]
	start_response('201 Created', headers)
	return [body]

app = TestApp(application)

resp = app.post_json('/users/', dict(id=1, value='value'))
print(resp.request)
resp.status_int == 201
print(resp.json == {'id': 1, 'value': 'value'})