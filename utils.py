from bottle import request

def build_uri(path):
  return "{0}://{1}{2}".format(request.urlparts.scheme, request.urlparts.netloc, path)

def parse_URI(URI):
  split = URI.split('/');
  return (split[-2], split[-1])
