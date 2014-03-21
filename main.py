#! /usr/bin/env python 

from bottle import route, run, template, post, HTTPResponse, request, get, default_app
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps

client = MongoClient() 
db = client.apimorph

def resource_to_response(resource, collection_name):
  resource_id = str(resource['_id'])
  del resource['_id']

  output = {
      "links": [
        { "rel": "self", "href": "/{0}/{1}".format(collection_name, resource_id) }
        ],
      }

  output = dict(output.items() + resource.items())
  return output

def content_to_response(content, collection_name, page, page_size):
  a = [resource_to_response(record, collection_name) for record in content]

  links = []
  if(page > 1):
    links.append({ "rel": "prev", "href": "/{0}?page={1}&size={2}".format(collection_name, page-1, page_size) })
  if(page * page_size < content.count()):
    links.append({ "rel": "next", "href": "/{0}?page={1}&size={2}".format(collection_name, page+1, page_size) })

  return {
    "links": links,
    "meta": {
      "page": page,
      "size": page_size,
      "total": content.count()
      },
    "content": a[(page - 1) * page_size:page*page_size]
    }


@post('/<resource>')
def post_handler(resource):
  resource_id = db[resource].insert(request.json)
  body=dumps(request.json)
  headers={
      "Content-Type": "application/json; charset=utf8",
      "Location": "/users/{0}".format(resource_id)
      }

  return HTTPResponse(status=201, headers=headers, body=body)


@get('/<resource>')
def list_handler(resource):
  content = db[resource].find()
  page = int(request.query.get('page', 1))
  page_size = int(request.query.get('size', 20))
  results = content_to_response(content, resource, page, page_size)
  headers = { "Content-Type": "application/json; charset=utf8" }

  return HTTPResponse(status=200, body=dumps(results), headers=headers)


@get('/<resource>/<id>')
def get_handler(resource, id):
  content = db[resource].find_one({'_id': ObjectId(id)})
  headers = { "Content-Type": "application/json; charset=utf8" }

  return HTTPResponse(status=200, headers=headers, body=dumps(resource_to_response(content, resource)))


if __name__ == '__main__':
  run(host='localhost', port=8091, reloader=True, debug=True)

application = default_app()
