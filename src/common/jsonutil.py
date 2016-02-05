'''
Created on Aug 29 2015

@author: Kevin Chien
'''
import datetime
import re

import simplejson as json
#from bson.objectid import ObjectId
from jsonschema import Draft4Validator, FormatChecker
from jsonschema._format import _checks_drafts

from src.common.error import FlamesError, InvalidArgumentsError
from src.common.status import JSON_PARSING_FAILED

def decode(obj):
#     if isinstance(obj, ObjectId):
#         return str(obj)
#     elif isinstance(obj, datetime.datetime):
    if isinstance(obj, datetime.datetime):        
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    return json.JSONEncoder().default(obj)

def dict2json(d, decoder = decode):
    """
    Convert a dictionary to a json string.
    @param obj: A dictionary.
    @type obj: C{dict} 
    @return: Json string by the given dictionary.
    @rtype: C{string}
    """
    return json.dumps(d, default=decoder)

def json2dict(json_str, schema = None, validated = True):
    if json_str is None or len(json_str) == 0:
        if not validated:
            return {}
        else:
            json_str = '{}'
    
    try:
        d = json.loads(json_str)
        
        if validated and schema:
            validate(d, schema)
            
        return _narrow_dict(d, schema)
    except InvalidArgumentsError as e:
        raise e
    except Exception as e:
        raise FlamesError(JSON_PARSING_FAILED, message = e.message)

RE_PATTERN_IP = '^(\d{1,3}\.){3}\d{1,3}$'
RE_PATTERN_IPS = '^(\d{1,3}\.){3}\d{1,3}(,(\d{1,3}\.){3}\d{1,3})*$'
RE_PATTERN_PACKAGE_VERSION = '^(\d{1,3}\.){0,3}(\d{1,4})$'

#The format that we only allowed the mac address is "lower case with :"
RE_PATTERN_MAC_ADDRESS = '^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$'

@_checks_drafts("ip")
def is_ip(instance):
    if not re.match(RE_PATTERN_IP, instance):
        return False
    return True

@_checks_drafts("ippair")
def is_ips(instance):
    if not re.match(RE_PATTERN_IPS, instance):
        return False
    return True

@_checks_drafts("package_version")
def is_package_version(instance):
    if not re.match(RE_PATTERN_PACKAGE_VERSION, instance):
        return False
    return True

@_checks_drafts("mac_address")
def is_mac_address(instance):
    if not re.match(RE_PATTERN_MAC_ADDRESS, instance):
        return False
    return True

@_checks_drafts(draft3="date-time", raises=ValueError)
def is_date(instance):
    return datetime.datetime.strptime(instance, "%Y-%m-%d %H:%M:%S")

def str2bool(s):
    if s is None:
        return False
    elif s.lower() in ["1", "yes", "true", "on"]:
        return True
    else:
        return False
    
def validate(obj, schema):        
    v = Draft4Validator(schema, format_checker = FormatChecker())
    messages = []
    for error in v.iter_errors(obj):
        if error.validator == 'required':
            messages.append(error.message)
        else:
            path = list(error.path)
            if len(path) == 0:
                messages.append(error.message)
            elif len(path) >= 1:
                if not isinstance(path[len(path) - 1], int):
                    param_name = path[len(path) - 1]
                else:
                    #for param: items, jsonschema will add a list in param.
                    param_name = path[len(path) - 2]
                messages.append(str(param_name) + ' ' + error.message)
    
    if messages:
        e = InvalidArgumentsError()
        e.add_messages(messages)
        raise e

def _narrow_dict(d, schema = None):
    if schema is None:
        return d
        
    if isinstance(d, list):
        items = []
        for value in d:
            items.append(_narrow_dict(value, schema.get('items')))
        return items
    else:
        properties = schema.get('properties')
        if properties is not None:
            newdict = {}
            for prop_name, prop  in properties.iteritems():
                value = d.get(prop_name)
                if value is not None:
                    if isinstance(value, list):
                        newdict[prop_name] = _narrow_dict(value, prop.get('items')) 
                    elif isinstance(value, dict):
                        newdict[prop_name] = _narrow_dict(value, prop)
                    elif prop.get("strip", True) and hasattr(value, 'strip'):
                            newdict[prop_name] = value.strip()
                    else:
                        newdict[prop_name] = value
            return newdict
        else:
            return d