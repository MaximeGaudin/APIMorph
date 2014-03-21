#! /usr/bin/env python 

from bottle import route, run, template, post, HTTPResponse, request, get, default_app, delete
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps
import pdb

import re

DEFAULT_PAGE_SIZE=20

client = MongoClient() 
db = client.apimorph

def build_uri(scheme, hostname, path):
  return "{0}://{1}{2}".format(scheme, hostname, path)

def parse_URI(URI):
  split = URI.split('/');
  return (split[-2], split[-1])

def resource_to_response(resource, denormalized, collection_name, hostname):
  resource_id = str(resource['_id'])
  del resource['_id']

  links = []
  links.append({ "rel": "self", "href": build_uri("http", hostname, "/{0}/{1}".format(collection_name, resource_id)) })

  if '_links' in resource:
    links.extend(resource['_links'])
    del resource['_links']

  for l in links:
    if l['rel'] in denormalized:
      resource_name, uuid = parse_URI(l['href'])
      try:
        reference = db[resource_name].find_one({'_id': ObjectId(uuid)})

        if reference is not None:
          unwrapped = resource_to_response(reference, [], resource_name, hostname)
          resource[l['rel']] = unwrapped
          links.remove(l)
      except: pass

    else:
      if 'http' not in l['href']:
        l['href'] = 'http://{0}'.format(hostname) + l['href']

  output = { "_links": links }
  output = dict(output.items() + resource.items())
  return output


def content_to_response(content, collection_name, denormalized, page, page_size, hostname):
  a = [resource_to_response(record, denormalized, collection_name, hostname) for record in content]

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
  hostname = request.get_header('host')
  body=resource_to_response(request.json, [], resource, hostname)

  headers={
      "Content-Type": "application/json; charset=utf8",
      "Location": "/users/{0}".format(resource_id)
      }

  return HTTPResponse(status=201, headers=headers, body=body)


@get('/<resource>')
def list_handler(resource):
  sorts = []
  for sort in request.query.getall('sort'):
    s = sort.split(',')
    sort_field = s[0]
    sort_order = 'ASC'
    if len(s) > 1: sort_order = s[1]
    sorts.append((sort_field, {'ASC': 1, 'DESC': -1}[sort_order]))

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

  if len(sorts) == 0:
    content = db[resource].find(exacts)
  else:
    content = db[resource].find(exacts).sort(sorts)

  denormalized = request.query.getall('unwrap')
  page = int(request.query.get('page', 1))
  page_size = int(request.query.get('size', DEFAULT_PAGE_SIZE))
  hostname = request.get_header('host')
  results = content_to_response(content, resource, denormalized, page, page_size, hostname)
  headers = { "Content-Type": "application/json; charset=utf8" }

  return HTTPResponse(status=200, body=dumps(results), headers=headers)


@get('/<resource>/<id>')
def get_handler(resource, id):
  headers = { "Content-Type": "application/json; charset=utf8" }
  denormalized = request.query.getall('unwrap')

  try:
    content = db[resource].find_one({'_id': ObjectId(id)})
    hostname = request.get_header('host')
    return HTTPResponse(status=200, headers=headers, body=dumps(resource_to_response(content, denormalized, resource, hostname)))
  except Exception as e:
    print e
    return HTTPResponse(status=404, headers=headers)


@delete('/<resource>/<id>')
def delete_handler(resource, id):
  try:
    content = db[resource].remove({'_id': ObjectId(id)})
    return HTTPResponse(status=204)
  except:
    return HTTPResponse(status=404)

@delete('/<resource>')
def delete_endpoint_handler(resource):
  db[resource].drop()

if __name__ == '__main__':
  run(host='localhost', port=8091, reloader=True, debug=True)

application = default_app()
