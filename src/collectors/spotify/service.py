'''
Created on Sep 3, 2015

@author: kevinchien
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
from src.collectors.spotify.constant import CACHED_PREFIX_KEY
from src.user.service import get_user_auth, update_user_auth
from src.common.status import USER_NOT_FOUND
from src.common.cacheutil import set_cache, get_cache
from src.common.error import FlamesError

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.spotify
_app_settings['redirect_uri'] =  _config.OAuth2_redirect_uri_host + "/user/spotify/auth/login"

class SpotifyAPI(OAuth2Mixin):
    
    _API_URL                = "https://api.spotify.com/v1"
    _OAUTH_SETTINGS_KEY     = 'spotify'
    _OAUTH_ACCESS_TOKEN_URL = "https://accounts.spotify.com/api/token"
    _OAUTH_AUTHORIZE_URL    = "https://accounts.spotify.com/authorize"
    _OAUTH_REQUEST_TOKEN_URL= "https://accounts.spotify.com/api/token" 
    _OAUTH_NO_CALLBACKS = False        

    def get_auth_http_client(self):
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.
        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()

    @coroutine
    def get_authenticated_user(self, code):
        """Handles the login for the user, returning a user object.
        """
        url = self._OAUTH_ACCESS_TOKEN_URL
        client_id = _app_settings['client_id']
        client_secret = _app_settings['consumer_secret']
        http = self.get_auth_http_client()
        auth = client_id+":"+client_secret
        auth = base64.b64encode(auth)
        auth = "Basic " + auth
        headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': auth}
        scope = " ".join(_app_settings['scope'].split())
        client_id = client_id
        body = urllib_parse.urlencode({
            #"client_id": client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _app_settings['redirect_uri'],
            "scope": scope
        })
        try :
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
        if args:
            args.update({'access_token': auth_info['access_token']})            
        else :
            args = {'access_token': auth_info['access_token']}
        url += "?" + urllib_parse.urlencode(args)             
        httpc = self.get_auth_http_client()
        try:
            if post_args is not None:
                response = yield httpc.fetch(url, method="POST",
                                             body=urllib_parse.urlencode(post_args))
            else:
                response =  yield httpc.fetch(url)
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
    def get_profile(self, suid):
        ckey = "profile"        
        result = yield get_cache(CACHED_PREFIX_KEY, suid, ckey)
        if result is None:        
            url = self._API_URL + "/me"
            result = yield self.api_request(suid, url)
            set_cache(CACHED_PREFIX_KEY, suid, ckey, result, 0)
        raise Return(result)
