'''
Created on Sep 3, 2015

@author: kevinchien
'''


from tornado.gen import coroutine, Return
from src.common.configutil import get_config
from src.collectors.jawbone.constant import CACHED_PREFIX_KEY
from src.common.cacheutil import set_cache, get_cache
from src.common.tornadoutil import OAuth2ClientAPI
from schema import SCHEMA_BAND_EVENTS
from src.collectors.jawbone.schema import SCHEMA_BODY_EVENTS_DATA,\
    SCHEMA_USER_PROFILE, SCHEMA_USER_TRENDS

_config = get_config()
_app_settings = _config.jawbone


class JawboneAPI(OAuth2ClientAPI):
    
    _API_URL                = "https://jawbone.com/nudge/api/v.1.1"
    _OAUTH_SETTINGS_KEY     = 'jawbone'
    _OAUTH_ACCESS_TOKEN_URL = "https://jawbone.com/auth/oauth2/token"
    _OAUTH_AUTHORIZE_URL    = "https://jawbone.com/auth/oauth2/auth"
    _OAUTH_REQUEST_TOKEN_URL= "https://jawbone.com/auth/oauth2/token" 
    _OAUTH_NO_CALLBACKS     = False        

    def __init__(self):
        super(JawboneAPI, self).__init__(self._OAUTH_SETTINGS_KEY, _app_settings)        

    def initialize(self):
        super(JawboneAPI, self).initialize(_app_settings)

    @coroutine
    def servc_get_band_events(self, suid):
        ckey = "bandevents"
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:
            url = self._API_URL + "/users/@me/bandevents"
            result = yield self.api_request(suid, url, json_schema=SCHEMA_BAND_EVENTS)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)

    @coroutine
    def servc_get_body_events(self, suid):
        ckey = "bodyevents"
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:
            url = self._API_URL + "/users/@me/body_events"
            result = yield self.api_request(suid, url, json_schema=SCHEMA_BODY_EVENTS_DATA)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)

    @coroutine
    def servc_get_heartrates(self, suid, date):
        ckey = "heartrates.%s" % date
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:
            url = self._API_URL + "/users/@me/heartrates"
            #json_schema=SCHEMA_BODY_EVENTS_DATA
            result = yield self.api_request(suid, url, date=date)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)    

    @coroutine
    def servc_get_profile(self, suid):
        ckey = "profile"
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:
            url = self._API_URL + "/users/@me"
            result = yield self.api_request(suid, url, json_schema=SCHEMA_USER_PROFILE)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)

    @coroutine
    def servc_get_trends(self, suid, end_date, period):
        ckey = "trends.%s" % end_date
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:
            url = self._API_URL + "/users/@me/trends"
            result = yield self.api_request(suid, url, json_schema=SCHEMA_USER_TRENDS,
                                            end_date=end_date, 
                                            bucket_size='d', num_buckets=period)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)
