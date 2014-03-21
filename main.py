#! /usr/bin/env python 

from bottle import route, run, template, post, HTTPResponse, request, get, default_app
from pymongo import MongoClient
from bson.json_util import dumps

client = MongoClient() 
db = client.apimorph

def content_to_response(content):
  a = [record for record in content]
  for r in a:
    r['_id'] = r['_id']

  return dumps({
    "links": [],
    "meta": {
      "page": 1,
      "size": 20,
      "total": content.count()
      },
    "content": a
    })


@post('/<resource>')
def post_handler(resource):
  resource_id = db[resource].insert(request.json)
  return HTTPResponse(status=201, 
      headers={
        "Content-Type": "application/json; charset=utf8",
        "Location": "/users/{0}".format(resource_id)
        }, 
      body=dumps(request.json))


@get('/<resource>')
def list_handler(resource):
  content = db[resource].find()
  return HTTPResponse(status=200, 
      headers={
        "Content-Type": "application/json; charset=utf8"
        }, body=content_to_response(content))


@get('/<resource>/<id>')
def list_handler(resource, id):
  content = db[resource].find_one(id)
  return HTTPResponse(status=200, body=content_to_response(content))


if __name__ == '__main__':
  run(host='localhost', port=8091, reloader=True, debug=True)

application = default_app()
