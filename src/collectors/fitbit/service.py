'''
Created on Aug 29, 2015

@author: kevinchien
'''

from tornado.gen import coroutine, Return
from src.common.configutil import get_config
from src.common.logutil import get_logger
from src.common.tornadoutil import OAuth2ClientAPI
import base64

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.fitbit
_app_settings['redirect_uri'] =  _config.OAuth2_redirect_uri_host + "/user/fitbit/auth/login"

class FitbitAPI(OAuth2ClientAPI):
    _API_URL                = "https://api.fitbit.com/1"
    _OAUTH_ACCESS_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
    _OAUTH_AUTHORIZE_URL    = "https://www.fitbit.com/oauth2/authorize"     
    _OAUTH_NO_CALLBACKS     = False        
    _OAUTH_SETTINGS_KEY     = 'fitbit'

    _activity_res_list = ['calories', 'caloriesBMR', 'steps', 'distance', 'floors', 
                          'elevation', 'minutesSedentary', 'minutesLightlyActive', 
                          'minutesFairlyActive', 'minutesVeryActive', 'activityCalories',
                          'heart']

    _actions = ["get_user_profile", "get_activity_list", "get_user_activity", 
                "get_sleep_item", "get_sleep"]

    def __init__(self):
        super(FitbitAPI, self).__init__(self._OAUTH_SETTINGS_KEY, _app_settings)        

    def initialize(self):
        super(FitbitAPI, self).initialize(_app_settings)

    @coroutine
    def refresh_token(self, suid):
        auth = _app_settings['client_id']+":"+_app_settings['consumer_secret']
        auth = base64.b64encode(auth)
        auth = "Basic " + auth
        extr_hdr = {'Authorization': auth}        
        result = yield super(FitbitAPI, self).refresh_token(suid, extr_hdr)
        raise Return(result)

    @coroutine
    def servc_get_user_profile(self, suid, auth_info=None):    
        url = ("%s/user/-/profile.json" % (self._API_URL))
        result = yield self.api_request(suid, url, auth_info=auth_info)
        raise Return(result)
    
    @coroutine
    def servc_get_activity_list(self, suid, start_date=None, end_date=None, auth_info=None):
        url = ("%s/user/%s/activities/date/%s.json" % (self._API_URL, '-', 'today'))
        result = yield self.api_request(suid, url, auth_info=auth_info)
        raise Return(result)
    
    @coroutine
    def servc_get_user_activity(self, suid, act_type, date, period, auth_info=None):
        url = ("%s/user/%s/activities/%s/date/%s/%s.json" % (self._API_URL, '-', 
                                                             act_type, date, period)) 
        result = yield self.api_request(suid, url, auth_info=auth_info)
        raise Return(result)
    
    @coroutine
    def servc_get_sleep_item(self, suid, item, base, cond, auth_info=None):
        url = ("%s/user/%s/sleep/%s/date/%s/%s.json" % (self._API_URL, '-', 
                                                        item, base, cond)) 
        result = yield self.api_request(suid, url, auth_info=auth_info)
        raise Return(result)    
    
    @coroutine
    def servc_get_sleep(self, suid, date, auth_info=None):
        url = ("%s/user/%s/sleep/date/%s.json" % (self._API_URL, '-', date))            
        result = yield self.api_request(suid, url, auth_info=auth_info)
        raise Return(result)
