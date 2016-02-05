'''
Created on Sep 9, 2015

@author: ycwu
'''
import uuid

from tornado.gen import coroutine

from src.core.tornadoutil import BaseHandler, route
from src.collectors.linkedin.service import LinkedinAPI
from src.common.tornadoutil import HTTP_METHOD


from src.user.service import get_user_auth, update_user_auth
from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.collectors.linkedin.constant import CACHED_PREFIX_KEY
from src.common.status import AUTH_FAILED, USER_NOT_FOUND
from src.common.error import FlamesError

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.linkedin
_app_settings['redirect_uri'] =  _config.OAuth2_redirect_uri_host + "/user/linkedin/auth/login"

_logger.debug("linkedin settings: %s", _app_settings)

class LinkedinHandler(BaseHandler, LinkedinAPI):

    def initialize(self):
        super(LinkedinHandler, self).initialize()

    @route(r'/user/linkedin/auth/login', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def auth_login(self):        
        ''' Login service with OAuth2 and binding with given service user id.
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
                self.redirect(("/v1/user/%s/linkedin/auth" % suid))
                return
        else :
            # Do not found in the query string or cookie, create a new one.
            suid = str(uuid.uuid4())
            self.set_cookie("suid", suid)

        state = self.get_argument("state", None)
        _logger.debug(state)
        code = self.get_argument("code", None)
        _logger.debug(code)
        if code:
            auth = yield self.get_authenticated_user(code, state)  
            yield update_user_auth(suid, auth, CACHED_PREFIX_KEY)
            self.redirect(("/v1/user/%s/linkedin/auth" % suid))
            return
        
        yield self.authorize_redirect(redirect_uri=_app_settings['redirect_uri'],
                                      client_id=_app_settings['client_id'],
                                      scope=_app_settings['scope'].split(), 
				      extra_params={ 'state': "abcdefg"})

    @route(r'/user/(.*)/linkedin/auth/logout', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def auth_logout(self, suid):
        ''' Logout Spotify service with given service user id.
        '''
        yield update_user_auth(suid, None, CACHED_PREFIX_KEY)
        self.clear_cookie('suid')
        self.write_result({})

    @route(r'/user/(.*)/linkedin/auth', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def get_auth(self, suid):
        ''' Get the Linkedin binding status with service user id.
        '''        
        auth = yield get_user_auth(suid, CACHED_PREFIX_KEY)
        if auth is None:
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        result = {"suid": suid, "auth": auth}          
        self.write_result(result)

    @route(r'/user/(.*)/linkedin/people', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def get_linkedin_people(self, suid):
        result = yield self.get_people(suid)
        self.write_result(result)
