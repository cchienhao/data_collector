'''
Created on Aug 29, 2015

@author: kevinchien
'''

from sets import Set

from src.common.cacheutil import set_cache, get_cache
from tornado.gen import coroutine, Return
from src.user.constant import CACHED_PREFIX_AUTH, CACHED_PREFIX_USER, CACHED_PREFIX_SERVC


@coroutine
def update_user_auth(suid, auth_info, prefix = CACHED_PREFIX_USER):
    ''' Update user auth information 
    '''
    # Update the user auth info.
    set_cache(prefix, suid, CACHED_PREFIX_AUTH, auth_info, 0)
    # Update user's subscribution service list. 
    user_servc_set = yield get_cache(CACHED_PREFIX_USER, suid, CACHED_PREFIX_SERVC)
    if user_servc_set is None:
        user_servc_set = Set()
    else:
        user_servc_set = Set(user_servc_set)
    if auth_info:
        user_servc_set.add(prefix)
    else:
        user_servc_set.discard(prefix)        
    set_cache(CACHED_PREFIX_USER, suid, CACHED_PREFIX_SERVC, list(user_servc_set), 0)

    
@coroutine
def get_user_auth(suid, prefix = CACHED_PREFIX_USER):
    result = yield get_cache(prefix, suid, CACHED_PREFIX_AUTH)
    raise Return(result)
