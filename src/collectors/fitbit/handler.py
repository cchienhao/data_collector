'''
Created on Aug 29, 2015

@author: kevinchien
'''
import uuid
import base64

from tornado.gen import coroutine

from src.core.tornadoutil import BaseHandler, route, HTTP_METHOD
from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.common.error import FlamesError
from src.common.status import AUTH_FAILED
from src.collectors.fitbit.status import USER_NOT_FOUND
from src.collectors.fitbit.service import FitbitAPI
from src.collectors.fitbit.constant import CACHED_PREFIX_KEY
from src.user.service import update_user_auth, get_user_auth

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.fitbit

_logger.debug("fitbit_settings: %s",_app_settings)

class FitbitHandler(BaseHandler, FitbitAPI):
    
    def initialize(self):
        super(FitbitHandler, self).initialize()

    @route(r'/user/fitbit/auth/login', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def auth_login(self):        
        ''' Login Fitbit service with OAuth2 and binding with given service user id.
        '''
        
        error = self.get_argument('error', None)
        if error:
            raise FlamesError(AUTH_FAILED, messages=error)        
        
        suid = self.get_argument("suid", None)
        if suid is None: suid = self.get_cookie('suid', None)
        if suid:
            self.set_cookie("suid", suid)
            auth = yield get_user_auth(suid, CACHED_PREFIX_KEY)
            if auth:
                self.redirect(("/v1/user/%s/fitbit/auth" % suid))
                return        
        else :
            # Do not found in the query string or cookie, create a new one.
            suid = str(uuid.uuid4())
            self.set_cookie("suid", suid)

        code = self.get_argument("code", None)
        client_id = _app_settings['client_id']
        client_secret = self._APP_SETTINGS['consumer_secret']

        if code:
            auth = client_id+":"+client_secret
            auth = base64.b64encode(auth)
            auth = "Basic " + auth
            extr_hdr = {'Authorization': auth}
            auth = yield self.get_authenticated_user(code, extr_headers=extr_hdr)  
            yield update_user_auth(suid, auth, CACHED_PREFIX_KEY)
            self.redirect(("/v1/user/%s/fitbit/auth" % suid))
            return
        
        yield self.authorize_redirect(redirect_uri=_app_settings['redirect_uri'],
                                      client_id=client_id,
                                      scope=_app_settings['scope'].split())

    @route(r'/user/(.*)/fitbit/auth/logout', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def auth_logout(self, suid):
        ''' Logout Fitbit service with given service user id.
        '''
        update_user_auth(suid, None, CACHED_PREFIX_KEY)
        self.clear_cookie('suid')
        self.write_result({})

    @route(r'/user/(.*)/fitbit/auth', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def get_auth(self, suid):
        ''' Get the Fitbit binding status with service user id.
        '''        
        auth = yield get_user_auth(suid, CACHED_PREFIX_KEY)
        if auth is None:
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        result = {"suid": suid, "auth": auth}          
        self.write_result(result)

    @route(r'/user/(.*)/fitbit', HTTP_METHOD.GET, '>=1')
    @coroutine
    def get_user_profile(self, suid):
        profile = yield self.servc_get_user_profile(suid)
        self.write_result(profile)

    @route(r'/user/(.*)/fitbit/activities/list', HTTP_METHOD.GET, '>=1')
    @coroutine
    def get_activity_list(self, suid):
        activity = yield self.servc_get_activity_list(suid)
        self.write_result(activity)
        
    @route(r'/user/(.*)/fitbit/activities/(.*)/date/(.*)/(.*)', HTTP_METHOD.GET, '>=1')
    @coroutine
    def get_activity_type(self, suid, act_type, start_time, end_time):
        activity = yield self.servc_get_user_activity(suid, act_type, start_time, end_time)
        self.write_result(activity)

#     @route(r'/user/(.*)/fitbit/sleep/date/(.*)', HTTP_METHOD.GET, '>=1')
#     @coroutine
#     def get_sleep(self, suid, date):
#         sleep_log = yield get_sleep(suid, date)
#         self.write_result(sleep_log)

    @route(r'/user/(.*)/fitbit/sleep/(.*)/date/(.*)', HTTP_METHOD.GET, '>=1')
    @coroutine
    def get_sleep_status(self, suid, sleep_type, date):
        base, cond = self.validate_datetime(date)
        sleep_log = yield self.servc_get_sleep_item(suid, sleep_type, base, cond)
        self.write_result(sleep_log)
