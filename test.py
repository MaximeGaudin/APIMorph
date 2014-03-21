from main import application
from webtest import TestApp

app = TestApp(application)

def test_endpoint_creation():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  assert r.status_code == 201
  assert r.headers['Location'] != None

  r = app.get(r.headers['Location'])
  assert r.status_code == 200


def test_delete_endpoint():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  assert r.status_code == 201
  location = r.headers['Location']
  assert location != None

  r = app.get(location)
  assert r.status_code == 200

  r = app.delete(location)
  assert r.status_code == 204

  r = app.get(location)
  assert r.status_code == 404 



