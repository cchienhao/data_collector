'''
Created on Sep 9, 2015

@author: ycwu
'''

import urllib as urllib_parse  # py2
import base64

from tornado.auth import OAuth2Mixin
from tornado.gen import coroutine, Return
from src.common.jsonutil import json2dict
from src.common.logutil import get_logger
from src.common.configutil import get_config
from tornado import httpclient
from tornado.web import HTTPError
from src.collectors.linkedin.constant import CACHED_PREFIX_KEY
from src.user.service import get_user_auth, update_user_auth
from src.common.status import USER_NOT_FOUND
from src.common.cacheutil import set_cache, get_cache
from src.common.error import FlamesError

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.linkedin

class LinkedinAPI(OAuth2Mixin):
    
    _API_URL                = "https://api.linkedin.com/v1"
    _OAUTH_SETTINGS_KEY     = 'linkedin'
    _OAUTH_ACCESS_TOKEN_URL = "https://www.linkedin.com/uas/oauth2/accessToken"
    _OAUTH_AUTHORIZE_URL    = "https://www.linkedin.com/uas/oauth2/authorization"
    _OAUTH_REQUEST_TOKEN_URL= "https://www.linkedin.com/uas/oauth2/accessToken" 
    _OAUTH_NO_CALLBACKS = False        

    def get_auth_http_client(self):
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.
        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()

    @coroutine
    def get_authenticated_user(self, code, state):
        """Handles the login for the user, returning a user object.
        """
        url = self._OAUTH_ACCESS_TOKEN_URL
        client_id = _app_settings['client_id']
        client_secret = _app_settings['consumer_secret']
        http = self.get_auth_http_client()
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
        scope = " ".join(_app_settings['scope'].split())
	client_id = client_id
        body = urllib_parse.urlencode({
            "grant_type": "authorization_code",
            "code" : code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": _app_settings['redirect_uri']
        })
        try :
            _logger.debug(body) 
            response = yield http.fetch(url, method="POST", headers=headers, 
                                        body=body)
        except Exception as e:
            _logger.error("Request %s %s" % (url, e))
            raise e
        _logger.debug(response.body)
        #TODO: check the response status code.
        raise Return(json2dict(response.body))
    
    @coroutine
    def refresh_token(self, suid):
        auth_info = yield get_user_auth(suid, CACHED_PREFIX_KEY)
        if auth_info is None:
            _logger.warn("There is no login user info.")
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        url = self._OAUTH_ACCESS_TOKEN_URL
 
        httpc = httpclient.AsyncHTTPClient()
        post_args = {
            "grant_type": "refresh_token",
            "client_id": _app_settings['client_id'],
            "client_secret": _app_settings['consumer_secret'], 
            "refresh_token": auth_info['refresh_token']
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}    
        try :
            response = yield httpc.fetch(url, method="POST", 
                                         body=urllib_parse.urlencode(post_args),
                                         headers=headers)
            result = json2dict(response.body)
            update_user_auth(suid, result, CACHED_PREFIX_KEY)
        except HTTPError as e:
            _logger.error("Request %s %s" % (url, e))
            raise e
        _logger.info("Request %s done." % (url))
        raise Return(result)    


    @coroutine
    def api_request(self, suid, url, post_args=None, resend=False, **args):
        auth_info = yield get_user_auth(suid, CACHED_PREFIX_KEY)
        if auth_info is None:
            _logger.warn("There is no login user info.")
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        oauth = "Bearer " + auth_info['access_token']
        _logger.debug(oauth)
        if args:
            url += "?" + urllib_parse.urlencode(args)
        _logger.debug(url)
        httpc = self.get_auth_http_client()
        try:
            if post_args is not None:
                response = yield httpc.fetch(url, method="POST",
                                             body=urllib_parse.urlencode(post_args))
            else:
                response = yield httpc.fetch(url, headers={'Authorization': oauth})
            result = json2dict(response.body)
        except HTTPError as e:
            if e.code == 401 and resend == False:
                auth_info = yield self.refresh_token(suid)
                # Update the auth token, and send request again.                
                yield update_user_auth(suid, auth_info, CACHED_PREFIX_KEY);
                result = yield self.api_request(suid, url, post_args,
                                                resend=True, **args)
                raise Return(result)
            raise e

        _logger.info("Request %s done." % (url))
        raise Return(result)

    @coroutine
    def get_people(self, suid):
        ckey = "profile"        
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:        
            url = self._API_URL + "/people/~"
            result = yield self.api_request(suid, url, format='json')
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)
