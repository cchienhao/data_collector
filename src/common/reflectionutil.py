'''
Created on Aug 29 2015

@author: Kevin Chien
'''
import types

def import_resource(full_resource_name):
    index = full_resource_name.rfind(".")
    module_name = full_resource_name[0:index]
    resource_name = full_resource_name[index + 1:len(full_resource_name)]
    
    mod = __import__(module_name, fromlist=[resource_name])
    if hasattr(mod, resource_name):
        return getattr(mod, resource_name)
    else:
        return None

def get_class(full_path):
    index = full_path.rfind('.')
    resource_name = full_path[0:index]
    class_name = full_path[index + 1:]
    module = import_resource(resource_name)
    return getattr(module, class_name)
    
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse'] = reverse
    obj = type('Enum', (), enums)
    obj.list = list(sequential) + named.values()
    return obj
    
class EqualDict(dict):
    '''
    Implement __eq__ and __ne__ functions to make dict objects compare each other by key value.
    The key value would be empty, so use compare_empty_key flag to determine whether the empty value should be compared.
    More examples can be found in test case.
    '''
    def __init__(self, d, *keys):
        super(EqualDict, self).__init__(**d)
        self.keys = keys
        
    def __eq__(self, other):
        if isinstance(other, dict):
            for key in self.keys:
                self_value = self.get(key)
                other_value = other.get(key)
                
                if self_value != other_value:
                    return False
            return True
           
        return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
            
def merge_nested_dict(x, y):
    # store a copy of x, but overwrite with y's values where applicable         
    merged = dict(x,**y)

    # if the value of merged[key] was overwritten with y[key]'s value           
    # then we need to put back any missing x[key] values                        
    for key in x.keys():
        # if this key is a dictionary, recurse                                  
        if type(x[key]) is types.DictType and y.has_key(key):
            merged[key] = merge_nested_dict(x[key],y[key])

    return merged

def dict_copy(d, source_keys, dest_keys):
    new_d = {}
    for source_key, dest_key in zip(source_keys, dest_keys):
        value =  d.get(source_key)
        if value:
            new_d[dest_key] = value

    return new_d
