'''
Created on Oct 6, 2015

@author: kevinchien
'''
from tornado.gen import coroutine, Return

import src.common.queueutil as queueutil
from src.common.queueutil import Worker
from src.common.logutil import get_logger
from src.collectors.fitbit.service import FitbitAPI


_logger = get_logger(__name__)

    
class FitbitWorker(Worker, FitbitAPI):
 
    def __init__(self):
        super(FitbitWorker, self).__init__()
        self._logger = _logger

    @queueutil.route("fitbit", queueutil.QUEUE_METHOD.SUB)
    def worker_init(self):
        pass
             
    @coroutine             
    def worker_handler(self, task_info={}):
        
        suid = task_info['suid']
        auth_info = task_info['auth']
        action = task_info['action']

        result = {}        
        if action == "get_user_profile":
            result = yield self.servc_get_user_profile(suid, auth_info=auth_info)
        elif action == 'get_activity_list':
            result = yield self.servc_get_activity_list(suid, auth_info=auth_info)
        elif action == 'get_user_activity':
            result = []
            for i in range(0, len(self._activity_res_list)):
                data = yield self.servc_get_user_activity(suid, self._activity_res_list[i], 
                                                          'today', '1d', auth_info)
                result.append(data)

        raise Return(result)
