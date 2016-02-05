'''
Created on Aug 28 2015

@author: Kevin Chien
'''
from urlparse import urlparse, parse_qsl, urlunparse
from urllib import urlencode

def add_query_parameters(url, query_parameters):
    returned_url = list(urlparse(url))
    returned_query_parms = dict(parse_qsl(returned_url[4]))
    
    if query_parameters:
        for qs in query_parameters:
            if query_parameters[qs] is not None:
                returned_query_parms[qs] = query_parameters[qs]
    returned_url[4] = urlencode(returned_query_parms)
    return urlunparse(returned_url)

def add_fragments(url, fragments):
    if not fragments:
        return url
    return url + "#" + urlencode(fragments)