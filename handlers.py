from bottle import post, HTTPResponse, request, get, default_app, delete
from bson.json_util import dumps
from bson.objectid import ObjectId

from consts import DEFAULT_PAGE_SIZE

from db import mongo
from db import MongoResource, ResourceList

@post('/<endpoint>')
def create_resource(endpoint):
  resource_id = mongo[endpoint].insert(request.json)
  hostname = request.get_header('host')
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
