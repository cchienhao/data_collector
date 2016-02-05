'''
Created on Aug 29, 2015

@author: kevinchien
'''
import datetime
# from bson import ObjectId
from tornado.gen import Task, Return
from tornado.gen import coroutine

from src.common.logutil import get_logger
# from src.core.mongoutil import get_instance
# 
# @coroutine
# def update_auth(auth_info):
#     new_auth_info = auth_info.copy()
#     new_auth_info['updated_at'] = datetime.datetime.utcnow()        
#     
#     criteria = {"user_id": new_auth_info.get('user_id'), 
#                 "access_token": new_auth_info.get('access_token'), 
#                 "refresh_token": new_auth_info.get('refresh_token')}
#     
#     fields = {'$set': new_auth_info}
#     
#     result, error = yield Task(get_instance().auth_info.update, criteria, fields)
#     if error is not None:
#         raise error
#     
#     raise Return(result)