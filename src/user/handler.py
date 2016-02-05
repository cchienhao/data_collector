'''
Created on Aug 29, 2015

@author: kevinchien
'''

from tornado.gen import coroutine

from src.core.tornadoutil import BaseHandler, route, HTTP_METHOD
from src.common.logutil import get_logger

_logger = get_logger(__name__)

class UserHandler(BaseHandler):
    
    def initialize(self):
        super(UserHandler, self).initialize()
    
    @route(r'/user/(.*)', HTTP_METHOD.PUT, '>=1')
    @coroutine
    def add_user(self):
        ''' Create a new user account.
        '''
        pass

    @route(r'/user/(.*)', HTTP_METHOD.GET, '>=1')
    @coroutine    
    def get_user(self, user_id):
        ''' 
        '''        
        pass
    
    @route(r'/user/(.*)', HTTP_METHOD.DELETE, '>=1')
    @coroutine    
    def del_user(self, user_id):
        '''Remove user account with given user id.
        '''
        pass    
