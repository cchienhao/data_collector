'''
Created on Oct 6, 2015

@author: kevinchien
'''

import src.common.queueutil as queueutil
from src.common.queueutil import Worker
from src.common.logutil import get_logger
from src.collectors.facebook.service import FacebookAPI
from tornado.gen import coroutine, Return

_logger = get_logger(__name__)

class FacebookWorker(Worker, FacebookAPI):
 
    def __init__(self):
        super(FacebookWorker, self).__init__()
        
    @queueutil.route("facebook", queueutil.QUEUE_METHOD.SUB)
    def worker_init(self):
        pass
             
    @coroutine             
    def worker_handler(self, task_info={}):

        suid = task_info['suid']
        auth_info = task_info['auth']
        action = task_info['action']

        result = {}        
        if action == "get_fb_fitness":
            result = yield self.get_fb_fitness(suid, auth_info=auth_info)

        raise Return(result)
