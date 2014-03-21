#! /usr/bin/env python 

from bottle import route, run, template, post, HTTPResponse, request, get, default_app, delete
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps

client = MongoClient() 
db = client.apimorph

def build_uri(scheme, hostname, path):
  return "{0}://{1}{2}".format(scheme, hostname, path)

def resource_to_response(resource, collection_name, hostname):
  resource_id = str(resource['_id'])
  del resource['_id']

  output = {
      "links": [
        { "rel": "self", "href": build_uri("http", hostname, "/{0}/{1}".format(collection_name, resource_id)) }
        ],
      }

  output = dict(output.items() + resource.items())
  return output

def content_to_response(content, collection_name, page, page_size, hostname):
  a = [resource_to_response(record, collection_name, hostname) for record in content]

  links = []
  if(page > 1):
    links.append({ "rel": "prev", "href": build_uri("http", hostname, "/{0}?page={1}&size={2}".format(collection_name, page-1, page_size)) })
  if(page * page_size < content.count()):
    links.append({ "rel": "next", "href": build_uri("http", hostname, "/{0}?page={1}&size={2}".format(collection_name, page+1, page_size)) })

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
  hostname = request.get_header('host')
  results = content_to_response(content, resource, page, page_size, hostname)
  headers = { "Content-Type": "application/json; charset=utf8" }

  return HTTPResponse(status=200, body=dumps(results), headers=headers)


@get('/<resource>/<id>')
def get_handler(resource, id):
  content = db[resource].find_one({'_id': ObjectId(id)})
  hostname = request.get_header('host')
  headers = { "Content-Type": "application/json; charset=utf8" }

  return HTTPResponse(status=200, headers=headers, body=dumps(resource_to_response(content, resource, hostname)))


@delete('/<resource>/<id>')
def delete_handler(resource, id):
  try:
    content = db[resource].remove({'_id': ObjectId(id)})
    return HTTPResponse(status=204)
  except:
    return HTTPResponse(status=404)


if __name__ == '__main__':
  run(host='localhost', port=8091, reloader=True, debug=True)

application = default_app()
