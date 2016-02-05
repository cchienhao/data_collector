'''
Created on Aug 31 2015

@author: Kevin Chien
'''
import inspect
from functools import wraps

from tornado.gen import coroutine, Return

from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.core.redisutil import get_redis_client
from src.common.jsonutil import dict2json, json2dict
from src.common.systemutil import get_timestamp

ROOT_PREFIX = 'cache'
_logger = get_logger(__name__)
_config = get_config()

def cache(prefix = None, key = None, expires_in = 3600):
    """
    A decorator to cache data. 
    
    @param prefix: A prefix or namespace in Redis. If the argument is not given, function name will be used.
    @type prefix: C{string}
    @param key: The key to be used in Redis. If the argument is not given, all the arguments will be appended to generate the key.
    @type key: C{string}
    @param expires_in: How long the cached data expire. If the argument is string, it will be resolved by configutil. Otherwise, it will be used directly. 
    @type expires_in: C{int}
    """
    def _decorator(func):
        @coroutine
        @wraps(func)
        def _wrapper(*args, **kwargs):
            cached_key = _get_cached_key(func, args, kwargs, prefix, key)
                
            data = get_redis_client().get(cached_key)
            if data:
                _logger.debug("get cached result by key '%s'" % cached_key)
                try:
                    result = json2dict(data)
                except Exception:
                    _logger.warn("Fail to parse cached result to json: %s. Call function %s directly." % (data, func.__name__), exc_info=True)
                    result = yield func(*args, **kwargs)
                    
                raise Return(result)
            else:
                result = yield func(*args, **kwargs)
                
                if result is not None:
                    if isinstance(expires_in, basestring):
                        cached_expires_in = eval("_config.%s" % expires_in)
                    else:
                        cached_expires_in = expires_in
                        
                    _logger.debug("cache result by key '%s' and expired period %d" % (cached_key, cached_expires_in))
                    get_redis_client().setex(cached_key, cached_expires_in, dict2json(result))
                
                raise Return(result)
        return _wrapper
    return _decorator
    
def evict(prefix = None, key = None):
    """
    A decorator to evict cached data.
    
    @param prefix: A prefix or namespace in Redis. If the argument is not given, function name will be used.
    @type prefix: C{string}
    @param key: The key to be used in Redis. If the argument is not given, all the arguments will be appended to generate the key.
    @type key: C{string}
    """
    def _decorator(func):
        @coroutine
        @wraps(func)
        def _wrapper(*args, **kwargs):
            cached_key = _get_cached_key(func, args, kwargs, prefix, key)
            
            _logger.debug("delete cached result by key '%s'" % cached_key)
            get_redis_client().delete(cached_key)
            
            result = yield func(*args, **kwargs)
            raise Return(result)
        return _wrapper
    return _decorator

def _get_cached_key(func, args, kwargs, prefix = None, key = None):
    unwrapped_func = func.func_closure[0].cell_contents
    
    if prefix:
        cache_prefix = prefix
    else:
        cache_prefix = unwrapped_func.__name__
                
    argspec = inspect.getargspec(unwrapped_func)
    if argspec.defaults:
        args_dict = dict(zip(argspec.args[-len(argspec.defaults):], argspec.defaults))
    else:
        args_dict = {}
        
    args_dict.update(dict(zip(argspec.args, args)))
    args_dict.update(kwargs)
            
    if key:
        if isinstance(key, list):
            composited_key = '_'.join([_get_value_by_dot_notation(args_dict, sub_key) for sub_key in key])
            cached_key = "%s:%s:%s" % (ROOT_PREFIX, cache_prefix, composited_key)
        else:
            temp_key = _get_value_by_dot_notation(args_dict, key)
            if not temp_key:
                temp_key = '_'.join(str(x) for x in args_dict.values())
            cached_key = "%s:%s:%s" % (ROOT_PREFIX, cache_prefix, temp_key)
    else:
        cached_key = "%s:%s:%s" % (ROOT_PREFIX, cache_prefix, '_'.join(str(x) for x in args_dict.values()))

    return cached_key
   
def _get_value_by_dot_notation(d, key):
    value = d
    for key in key.split('.'):
        value = value.get(key)
        if value is None:
            return None
        
    return str(value)

def _get_key(prefix, user_id, field):
    return ("%s:%s:%s" % (prefix, field, user_id))

@coroutine
def get_keys(pattern=""):
    return get_redis_client().keys(pattern)    

@coroutine
def get_cache(prefix, user_id, field):
    cached_key = _get_key(prefix, user_id, field)
    data = get_redis_client().get(cached_key)    
    result = None
    if data:
        _logger.debug("get cached result by key '%s'" % cached_key)
        try:
            result = json2dict(data)
        except Exception as e:
            _logger.warn("Fail to parse cached result to json: %s." % (data), exc_info=True)
            raise e
    raise Return(result)

def set_cache(prefix, user_id, field, data={}, cached_expires_in = 3600):
    cached_key = _get_key(prefix, user_id, field)
    
    if data is not None:
        if isinstance(data, dict):
            lat = get_timestamp()
            data['lat'] = lat
        if cached_expires_in == 0:
            get_redis_client().set(cached_key, dict2json(data))
        else :
            get_redis_client().setex(cached_key, cached_expires_in, dict2json(data))
        _logger.debug("cache result by key '%s' and expired period %d" % (cached_key, cached_expires_in))
    else :
        _logger.debug("delete cached result by key '%s'" % cached_key)
        get_redis_client().delete(cached_key)
