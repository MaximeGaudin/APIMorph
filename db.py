from pymongo import MongoClient
from bson.objectid import ObjectId
from utils import build_uri, parse_URI
import copy

client = MongoClient() 
mongo = client.apimorph

class ResourceList:
  def __init__(self, collection, filters={}, sort=[]):
    self.collection = collection
    self.filters = filters 
    self.sort = sort

    self.cursor = mongo[collection].find(self.filters);
    if sort: self.cursor = self.cursor.sort(self.sort)

  def get_links(self, page, page_size):
    links = []
    if(page > 1):
      links.append({ "rel": "prev", "href": "/{0}?page={1}&size={2}".format(self.collection, page-1, page_size) })

    if(page * page_size < self.cursor.count()):
      links.append({ "rel": "next", "href": "/{0}?page={1}&size={2}".format(self.collection, page+1, page_size) })

    for link in links:
      if 'http' not in link['href']:
        link['href'] = build_uri(link['href'])

    return {'links_': links}
  
  def get_meta(self, page, page_size):
    return { "meta": { "page": page, "size": page_size, "total": self.cursor.count() } }

  def get_content(self, page, page_size, unwraps):
    page_cursor = copy.copy(self.cursor)
    page_cursor.skip((page-1) * page_size).limit(page_size)

    return {'content': [MongoResource(self.collection, record['_id']).to_response(unwraps=unwraps) for record in page_cursor]}

  def to_response(self, page, page_size, unwraps=[]):
    response = self.get_meta(page, page_size) 
    response.update(self.get_links(page, page_size)) 
    response.update(self.get_content(page, page_size, unwraps))

    return response


class MongoResource:
  def __init__(self, collection, id):
    self.collection = collection

    if isinstance(id, ObjectId):
      self.oId = id
      self.id = str(id)
    else:
      self.oId = ObjectId(id)
      self.id = str(id)

    self.document = mongo[collection].find_one({ '_id': self.oId })

  def get_links(self):
    links = []
    links.append({ 
      "rel": "self", 
      "href": "/{0}/{1}".format(self.collection, self.id)
    })

    if '_links' in self.document:
      links.extend(self.document['_links'])

    for link in links:
      if 'http' not in link['href']:
        link['href'] = build_uri(link['href'])

    return links

  def to_response(self, unwraps=[]):
    document = copy.copy(self.document)    

    del document['_id']
    document['_links'] = self.get_links()

    for link in document['_links']:
      if link['rel'] in unwraps:
        endpoint, uuid = parse_URI(link['href'])

        reference = MongoResource(endpoint, uuid)
        if reference.document is not None:
          document[link['rel']] = reference.to_response()
        document['_links'].remove(link)

    return document
