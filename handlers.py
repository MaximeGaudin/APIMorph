from bottle import post, HTTPResponse, request, get, default_app, delete, put, route
from bson.json_util import dumps
from bson.objectid import ObjectId

from consts import * 
from utils import build_uri

from db import mongo
from db import MongoResource, ResourceList

@get('/')
def list_resources():
  available_endpoints = mongo[META_COLLECTION].find()
  
  output = { '_links': [] }
  for endpoint in available_endpoints:
    output['_links'].append({ 'rel': endpoint['rel'], 'href': endpoint['href'] })

  return output

@route('/<endpoint>/<id>', 'PATCH')
def partial_update_resource(endpoint, id):
  resource = MongoResource(endpoint, id)
  new_document = resource.document
  new_document.update(request.json)
  new_document.update({ '_id': ObjectId(id) })

  mongo[endpoint].save(new_document)
  resource = MongoResource(endpoint, id)

  headers={
      "Content-Type": "application/json; charset=utf8",
      "Location": "/users/{0}".format(id)
      }

  return HTTPResponse(status=201, headers=headers, body=dumps(resource.to_response()))


@put('/<endpoint>/<id>')
def update_resource(endpoint, id):
  new_document = request.json
  new_document.update({ '_id': ObjectId(id) })

  mongo[endpoint].save(new_document)
  resource = MongoResource(endpoint, id)

  headers={
      "Content-Type": "application/json; charset=utf8",
      "Location": "/users/{0}".format(id)
      }

  return HTTPResponse(status=201, headers=headers, body=dumps(resource.to_response()))


@post('/<endpoint>')
def create_resource(endpoint):
  endpoint_metadata = { '_id': endpoint, 'rel': endpoint, 'href': build_uri('/' + endpoint) }
  mongo[META_COLLECTION].insert(endpoint_metadata)

  resource_id = mongo[endpoint].insert(request.json)
  resource = MongoResource(endpoint, resource_id)

  headers={
      "Content-Type": "application/json; charset=utf8",
      "Location": "/users/{0}".format(resource_id)
      }

  return HTTPResponse(status=201, headers=headers, body=dumps(resource.to_response()))


def parse_sort(sort):
  order = 'ASC'
  if ',' in sort:
    field, order = sort.split(',')
  else: field = sort

  return (field, {'ASC': 1, 'DESC': -1}[order])


def get_sorts():
  sorts = []
  for sort in request.query.getall('sort'):
    sorts.append(parse_sort(sort))
  return sorts


def get_filters():
  exacts = {}
  for key, value in request.query.items():
    try:
      keys = key.split('__')
      key_type = keys[1]
      if key_type == "exact":
        exact_field = keys[0]
        exact_value = value
        exacts[exact_field] = exact_value
    except IndexError: pass

  return exacts


@get('/<endpoint>')
def read_all(endpoint):
  unwraps = request.query.getall('unwrap')
  page = int(request.query.get('page', 1))
  page_size = int(request.query.get('size', DEFAULT_PAGE_SIZE))

  headers = { "Content-Type": "application/json; charset=utf8" }
  return HTTPResponse(status=200, body=dumps(ResourceList(endpoint, filters=get_filters(), sort=get_sorts()).to_response(page, page_size)), headers=headers)


@get('/<endpoint>/<id>')
def read_by_id(endpoint, id):
  headers = { "Content-Type": "application/json; charset=utf8" }
  unwraps = request.query.getall('unwrap')

  resource = MongoResource(endpoint, id)
  if resource.document is None:
    return HTTPResponse(status=404, headers=headers)

  return HTTPResponse(status=200, headers=headers, body=dumps(resource.to_response(unwraps=unwraps)))


@delete('/<resource>/<id>')
def delete_by_id(resource, id):
  content = mongo[resource].remove({'_id': ObjectId(id)})
  return HTTPResponse(status=204)
  #except:
  #  return HTTPResponse(status=404)


@delete('/<resource>')
def delete_endpoint(resource):
  mongo[resource].drop()
