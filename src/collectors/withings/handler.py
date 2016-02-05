'''
Created on Sep 1, 2015

@author: kevinchien
'''

import uuid

from tornado.gen import coroutine

from src.core.tornadoutil import BaseHandler, route, HTTP_METHOD
from src.common.logutil import get_logger
from src.common.configutil import get_config

from src.common.error import FlamesError
from src.collectors.withings.status import USER_NOT_FOUND
from src.collectors.withings.service import WithingsAPI
from src.collectors.withings.service import CACHED_PREFIX_WITHINGS
from src.user.service import get_user_auth, update_user_auth

_logger = get_logger(__name__)
_config = get_config()
_withings_settings = _config.withings

_withings_settings['redirect_uri'] =  _config.OAuth2_redirect_uri_host + "/user/withings/auth/login"

_logger.debug("_withings_settings: %s", _withings_settings)

class WithingsHandler(BaseHandler, WithingsAPI):
    
    def initialize(self):
        super(WithingsHandler, self).initialize()

    @route(r'/user/withings/auth/login', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def auth_login(self):        
        ''' Login service with OAuth2 and binding with given service user id.
        '''
        suid = self.get_argument("suid", None)
        if suid is None: suid = self.get_cookie('suid', None)
        if suid:
            self.set_cookie("suid", suid)
            auth = yield get_user_auth(suid, CACHED_PREFIX_WITHINGS)
            if auth:
                self.redirect(("/v1/user/%s/withings/auth" % suid))
                return
        else :
            # Do not found in the query string or cookie, create a new one.
            suid = str(uuid.uuid4())
            self.set_cookie("suid", suid)
        auth_token = self.get_argument("oauth_token", None)
        if auth_token:
            auth = yield self.get_authenticated_user()  
            yield update_user_auth(suid, auth, CACHED_PREFIX_WITHINGS)
            self.redirect(("/v1/user/%s/withings/auth" % suid))
            return
        yield self.authorize_redirect(callback_uri=_withings_settings['redirect_uri'])

    @route(r'/user/(.*)/withings/auth/logout', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def auth_logout(self, suid):
        ''' Logout Withings service with given service user id.
        '''
        yield update_user_auth(suid, None, CACHED_PREFIX_WITHINGS)
        self.clear_cookie('suid')
        self.write_result({})

    @route(r'/user/(.*)/withings/auth', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def get_auth(self, suid):
        ''' Get the Fitbit binding status with service user id.
        '''        
        auth = yield get_user_auth(suid, CACHED_PREFIX_WITHINGS)
        if auth is None:
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        result = {"suid": suid, "auth": auth}          
        self.write_result(result)
        
    @route(r'/user/(.*)/withings/activities/(.*)/date/(.*)/(.*)', HTTP_METHOD.GET, '>=1')
    @coroutine
    def get_measurement(self, suid, mstype, start_time, end_time):
        result = yield self.get_measure_data(suid, mstype, start_time, end_time)
        self.write_result(result)
        
