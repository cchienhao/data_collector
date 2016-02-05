'''
Created on Sep 3, 2015

@author: kevinchien
'''

from tornado.gen import coroutine, Return

from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.common.cacheutil import set_cache, get_cache
from src.collectors.runkeeper.constant import CACHED_PREFIX_KEY
from src.common.tornadoutil import OAuth2ClientAPI

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.runkeeper
_app_settings['redirect_uri'] =  _config.OAuth2_redirect_uri_host + "/user/runkeeper/auth/login"

class RunkeeperAPI(OAuth2ClientAPI):
        
    _OAUTH_SETTINGS_KEY     = 'runkeeper'
    _OAUTH_AUTHORIZE_URL    = "https://runkeeper.com/apps/authorize"
    _OAUTH_ACCESS_TOKEN_URL = "https://runkeeper.com/apps/token"    
    _OAUTH_REVOKE_URL       = "https://runkeeper.com/apps/de-authorize"
    _API_URL                = "https://api.runkeeper.com"
    _OAUTH_NO_CALLBACKS     = False        

    def __init__(self):
        super(RunkeeperAPI, self).__init__(self._OAUTH_SETTINGS_KEY, _app_settings)        

    def initialize(self):
        super(RunkeeperAPI, self).initialize(_app_settings)

    @coroutine
    def _servc_get_attr(self, suid, uri, attr_type=None, **kwargs):
        ckey = attr_type
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:
            url = self._API_URL + uri
            result = yield self.api_request(suid, url, **kwargs)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)

    @coroutine
    def servc_get_user_profile(self, suid):
        result = yield self._servc_get_attr(suid, "/profile", "profile")
        raise Return(result)

    @coroutine
    def servc_get_setting(self, suid):
        result = yield self._servc_get_attr(suid, "/settings", "settings")
        raise Return(result)

    @coroutine
    def servc_get_activities(self, suid):
        result = yield self._servc_get_attr(suid, "/fitnessActivities", "activities")
        raise Return(result)

    @coroutine
    def servc_get_nutrition(self, suid):
        result = yield self._servc_get_attr(suid, "/nutrition", "nutrition")
        raise Return(result)
    
    @coroutine
    def servc_get_sleep(self, suid):
        result = yield self._servc_get_attr(suid, "/sleep", "sleep")
        raise Return(result)
    
    @coroutine
    def servc_get_weight(self, suid):
        result = yield self._servc_get_attr(suid, "/weight", "weight")
        raise Return(result)

    @coroutine
    def servc_get_diabetes(self, suid):
        result = yield self._servc_get_attr(suid, "/diabetes", "diabetes")
        raise Return(result)

    @coroutine
    def servc_get_records(self, suid):
        result = yield self._servc_get_attr(suid, "/records", "records")
        raise Return(result)
