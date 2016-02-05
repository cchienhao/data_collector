'''
Created on Aug 29 2015

@author: Kevin Chien
'''

def is_empty(_str):
    """
    Convenient function to check if a str is empty
    
    Examples
    is_empty(None) = True
    is_empty("") = True
    
    is_empty(" ") = False
    is_empty("abc") = False
    is_empty("1") = False
    
    is_empty(1) = False
    """
    return not bool(_str)

def is_blank(_str):
    """
    Convenient function to check if a str is blank
    
    is_blank(None) = True
    is_blank("") = True
    is_blank(" ") = True

    is_blank("1") = False
    is_blank("abc") = False
    
    is_blank(1) # Raise AttributeError: 'int' object has no attribute 'strip'
    """
    
    return not (_str and _str.strip())

def strip(_str):
    """
    Convenient function to strip string. Accept C{None}.
    
    Examples:
    strip(None) = None
    strip("") = ""
    strip(" ") = ""
    strip(" abc") = "abc"
    strip("abc ") = "abc"
    strip("  ab  c   ") = "ab  c"
        
    strip(1)    # Raise AttributeError: 'int' object has no attribute 'strip'
    """
    if not _str:
        return _str
    return _str.strip()

def list_to_string(l):
    if len(l) == 0:
        return '[]'
    else:
        return "[%s]" % ", ".join("'%s'" % e if isinstance(e, basestring) else str(e) for e in l)
    
def encoded_string_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        v = encode_string(v)
        out_dict[k] = v
    return out_dict

def encode_string(obj):
    if isinstance(obj, (list, tuple)):
        out_list = []
        for v in obj:
            out_list.append(encode_string(v))
        return out_list
    if isinstance(obj, unicode):
        return obj.encode('utf8')
    elif isinstance(obj, str):
        # Must be encoded in UTF-8
        return obj.decode('utf8')
    else:
        return obj
