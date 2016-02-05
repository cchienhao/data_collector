'''
Created on Sep 9, 2015

@author: ycwu
'''

import urllib as urllib_parse  # py2
import base64
import urlparse

from tornado.ioloop import IOLoop
from tornado.auth import OAuth2Mixin
from tornado.gen import coroutine, Return
from tornado import httpclient
from tornado.web import HTTPError

from src.common.jsonutil import json2dict
from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.common.status import USER_NOT_FOUND
from src.common.error import FlamesError

from src.collectors.facebook.constant import CACHED_PREFIX_KEY
from src.user.service import get_user_auth, update_user_auth

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.facebook
_app_settings['redirect_uri'] =  _config.OAuth2_redirect_uri_host + "/user/facebook/auth/login"


class FacebookAPI(OAuth2Mixin):
    
    _API_URL = "https://graph.facebook.com/v2.4"
    _OAUTH_SETTINGS_KEY = 'facebook'
    _OAUTH_ACCESS_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
    _OAUTH_AUTHORIZE_URL = "https://www.facebook.com/dialog/oauth"
    _OAUTH_REQUEST_TOKEN_URL = "https://graph.facebook.com/oauth/access_token" 
    _OAUTH_NO_CALLBACKS = False        

    _actions = ["get_fb_fitness"]

    def get_auth_http_client(self):
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.
        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient(io_loop=IOLoop.instance())

    @coroutine
    def get_authenticated_user(self, code):
        """Handles the login for the user, returning a user object.
        """
        url = self._OAUTH_ACCESS_TOKEN_URL
        client_id = _app_settings['client_id']
        client_secret = _app_settings['consumer_secret']
        http = self.get_auth_http_client()
        auth = client_id + ":" + client_secret
        auth = base64.b64encode(auth)
        auth = "Basic " + auth
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 
                   'Authorization': auth, 'x-li-format': 'json'}
        # scope = " ".join(_app_settings['scope'].split())
        client_id = client_id
        body = urllib_parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "format" : "json",
            "redirect_uri": _app_settings['redirect_uri']
        })
        try :
            response = yield http.fetch(url, method="POST", headers=headers,
                                        body=body)
        except Exception as e:
            _logger.error("Request %s %s" % (url, e))
            raise e
        # TODO: check the response status code.
        token = dict(urlparse.parse_qsl(response.body)).get('access_token')
        expire_time = dict(urlparse.parse_qsl(response.body)).get('expires')
        ret_dict = {
            "access_token": token,
	        "expires_in": expire_time
        }
        raise Return(ret_dict)
    
    @coroutine
    def refresh_token(self, suid):
        auth_info = yield get_user_auth(suid, CACHED_PREFIX_KEY)
        if auth_info is None:
            _logger.warn("There is no login user info.")
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        url = self._OAUTH_ACCESS_TOKEN_URL
 
        httpc = httpclient.AsyncHTTPClient()
        post_args = {
            "grant_type": "fb_exchange_token",
            "client_id": _app_settings['client_id'],
            "client_secret": _app_settings['consumer_secret'],
            "fb_exchange_token":auth_info['access_token']
#            "refresh_token": auth_info['refresh_token']
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
    def api_request(self, suid, url, post_args=None, resend=False, auth_info=None, **args):
        
        if auth_info is None:        
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
                response = yield httpc.fetch(url)
            result = json2dict(response.body)
        except HTTPError as e:
            if e.code == 401 and resend == False:            
                auth_info = yield self.refresh_token(suid)
                # Update the auth token, and send request again.                
                yield update_user_auth(suid, auth_info, CACHED_PREFIX_KEY);
                result = yield self.api_request(suid, url, post_args,
                                                resend=True, **args)
                raise Return(result)
            _logger.error(e)
            raise e            
        except Exception as e:
            _logger.error(url)
            if e.response :
                _logger.error(e.response.body)
            else :
                _logger.error(e)
            raise e

        #_logger.info("Request %s done." % (url))
        raise Return(result)

    @coroutine
    def get_fb_profile(self, suid, auth_info=None):
        query_fields = "id,name,email,birthday,hometown,education,gender,age_range,posts,likes"
        url = self._API_URL + "/me"
        result = yield self.api_request(suid, url, fields=query_fields, 
                                        auth_info=auth_info)
        raise Return(result)

    @coroutine
    def get_fb_fitness(self, suid, auth_info=None):
        url = self._API_URL + "/me"
        result = yield self.api_request(suid, url, fields="fitness.runs", 
                                        auth_info=auth_info)
        raise Return(result)
