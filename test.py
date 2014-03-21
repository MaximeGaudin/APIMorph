from main import application
from webtest import TestApp
from random import randint

app = TestApp(application)

def test_endpoint_creation():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  assert r.status_int == 201
  assert r.headers['Location'] != None

  r = app.get(r.headers['Location'])
  assert r.status_int == 200


def test_delete_resource():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  location = r.headers['Location']

  assert r.status_int == 201
  assert location != None

  r = app.get(location)

  r = app.delete(location)
  assert r.status_int == 204

  r = app.get(location, status=404)

def test_delete_endpoint():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  r = app.delete('/users')
  json = app.get('/users').json

  assert 'meta' in json
  assert json['meta']['size'] == 20


def test_sort_default_order():
  app.delete('/integers')

  for i in range(0, 10):
    r = app.post_json('/integers', {'value': randint(0, 100)}) 

  asc = app.get('/integers?sort=value').json
  assert len(asc['content']) == 10

  prec = -1
  for v in asc['content']:
    assert v['value'] >= prec
    prec = v['value']


def test_sort_asc():
  app.delete('/integers')

  for i in range(0, 10):
    r = app.post_json('/integers', {'value': randint(0, 100)}) 

  asc = app.get('/integers?sort=value,ASC').json
  assert len(asc['content']) == 10

  prec = -1
  for v in asc['content']:
    assert v['value'] >= prec
    prec = v['value']


def test_sort_desc():
  desc = app.get('/integers?sort=value,DESC').json
  assert len(desc['content']) == 10

  prec = 101 
  for v in desc['content']:
    assert v['value'] <= prec
    prec = v['value']

def test_update():
  r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  assert r.status_int == 201
  location = r.headers['Location']
  assert location != None

  r = app.put_json(location, {'username': 'mgaudin', 'password': 'timeoff'})

  json = app.get(location).json
  assert json['username'] == 'mgaudin'


# def test_get_exact():
#   r = app.post_json('/users', {'username': 'ronyd', 'password': 'timeoff'})
  
#   r = app.get('/users?username__exact=ronyd', status=200)
#   for elem in r.body['content']:
#     assert elem['username'] == "ronyd"

#   r = app.get('/users?username__exact=ronyd&password__exact=timeoff', status=200)
#   for elem in r.body['content']:
#     assert elem['username'] == "ronyd"
#     assert elem['password'] == "timeoff"
