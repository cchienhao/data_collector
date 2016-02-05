'''
Created on Sep 1, 2015

@author: kevinchien
'''

#import base64
import binascii
import time
import urllib as urllib_parse  # py2
import uuid

from tornado.gen import coroutine, Return
from tornado.auth import OAuthMixin, AuthError, _oauth10a_signature, _oauth_signature
from tornado import httpclient, escape
from tornado.httpclient import HTTPError

from src.common.configutil import get_config
from src.common.jsonutil import json2dict
from src.common.logutil import get_logger
from src.common.cacheutil import get_cache, set_cache
from src.user.service import get_user_auth

_logger = get_logger(__name__)
_config = get_config()
_withings_settings = _config.withings

CACHED_PREFIX_WITHINGS="withings"

class WithingsAPI(OAuthMixin):
    
    _OAUTH_ACCESS_TOKEN_URL = "https://oauth.withings.com/account/access_token"
    _OAUTH_AUTHORIZE_URL    = "https://oauth.withings.com/account/authorize"
    _OAUTH_REQUEST_TOKEN_URL= "https://oauth.withings.com/account/request_token" 
    _OAUTH_NO_CALLBACKS = False
    _OAUTH_SETTINGS_KEY = 'withings_oauth'
    _API_URL = "http://wbsapi.withings.net/"

    def get_auth_http_client(self):
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.
        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()
    
    def _oauth_consumer_token(self):
        return dict(key=_withings_settings['consumer_key'], 
                    secret=_withings_settings['consumer_secret'])

    @coroutine
    def _oauth_get_user_future(self, access_token):
        user = {'access_token': access_token}
        raise Return(user)

    @coroutine
    def refresh_token(self):
        pass

    def _oauth_request_parameters(self, url, access_token, parameters={},
                                  method="GET"):
        """Returns the OAuth parameters as a dict for the given request.

        parameters should include all POST arguments and query string arguments
        that will be sent with the request.
        """
        consumer_token = self._oauth_consumer_token()
        base_args = dict(
            oauth_consumer_key=escape.to_basestring(consumer_token["key"]),
            oauth_token=escape.to_basestring(access_token["key"]),
            oauth_signature_method="HMAC-SHA1",
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=escape.to_basestring(binascii.b2a_hex(uuid.uuid4().bytes)),
            oauth_version="1.0",
        )
        args = {}
        args.update(base_args)
        args.update(parameters)
        if getattr(self, "_OAUTH_VERSION", "1.0a") == "1.0a":
            signature = _oauth10a_signature(consumer_token, method, url, args,
                                            access_token)
        else:
            signature = _oauth_signature(consumer_token, method, url, args,
                                         access_token)
        base_args["oauth_signature"] = signature
        return base_args
    
    @coroutine
    def api_request(self, user_id, path, post_args=None, **kwargs):
        if path.startswith('http:') or path.startswith('https:'):
            # Raw urls are useful for e.g. search which doesn't follow the
            # usual pattern: http://search.twitter.com/search.json
            url = path
        else:
            url = self._API_URL + path
        # Add the OAuth resource request signature if we have credentials
        access_token = yield get_user_auth(user_id, CACHED_PREFIX_WITHINGS)
        if kwargs:
            kwargs.update({'userid': access_token['userid']})
        if access_token:
            all_args = {}
            all_args.update(kwargs)            
            all_args.update(post_args or {})
            method = "POST" if post_args is not None else "GET"
            oauth = self._oauth_request_parameters(url, access_token, 
                                                   all_args, method=method)
            kwargs.update(oauth)
        if kwargs:            
            url += "?" + urllib_parse.urlencode(kwargs)
        http = self.get_auth_http_client()
        try:
            if post_args is not None:
                response = yield http.fetch(url, method="POST",
                                            body=urllib_parse.urlencode(post_args))
            else:
                response =  yield http.fetch(url)
            result = json2dict(response.body)
        except HTTPError as e:
            if response.error:
                raise AuthError( "Error response %s fetching %s" % 
                                 (response.error, response.request.url))
            else :
                raise e

        _logger.info("Request %s done." % (url))
        raise Return(result)

    @coroutine
    def get_measure_data(self, user_id, type, start_time, end_time):
        type_key = ('%s.%s.%s' % (type, start_time, end_time))
        result = yield get_cache(CACHED_PREFIX_WITHINGS, user_id, type_key)
        if result is None:
            result = yield self.api_request(user_id, 'measure',  action='getmeas',
                                            startdate=start_time, enddate=end_time)
            set_cache(CACHED_PREFIX_WITHINGS, user_id, type_key, result, 0)
        raise Return(result)
