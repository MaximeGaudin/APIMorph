from main import application
from webtest import TestApp

app = TestApp(application)

def test_endpoint_creation():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  assert r.status_code == 201
  assert r.headers['Location'] != None

  r = app.get(r.headers['Location'])
  assert r.status_code == 200

