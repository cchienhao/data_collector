
from tornado.gen import coroutine, Return

from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.common.cacheutil import get_keys
from src.common.systemutil import get_timestamp
from src.common.queueutil import QUEUE_METHOD,kafka_queue_send
from src.common.error import FlamesError
from src.common.jsonutil import dict2json

from src.user.service import get_user_auth
from src.trigger.trigger import route, Trigger
from src.collectors.fitbit.service import FitbitAPI
from src.collectors.fitbit.constant import CACHED_PREFIX_KEY
from src.collectors.fitbit.status import USER_NOT_FOUND

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.fitbit


class FitbitTrigger(Trigger):

    def __init__(self):
        super(FitbitTrigger, self).__init__(CACHED_PREFIX_KEY)
        self.api_clnt = FitbitAPI()    

    @route("fitbit", QUEUE_METHOD.PUSH)
    def worker_init(self):
        pass

    @coroutine        
    def task_isr(self):        
        # Query all the authorized user of fitbit service.
        users = yield get_keys("%s:auth:*" % CACHED_PREFIX_KEY)
        for user in users:
            suid = user.split(":")[-1]
            # TODO: check suid format.
            auth_info = yield get_user_auth(suid, prefix=CACHED_PREFIX_KEY)
            if auth_info is None:
                raise FlamesError(USER_NOT_FOUND, user_id=suid)
            curr_time = get_timestamp()
            lat = auth_info.get('lat', 0)
            expr_time = auth_info.get('expires_in', 3600)
            # Check the auth token status.
            if curr_time - lat >= expr_time:
                # Token need be updated.
                auth_info = yield self.api_clnt.refresh_token(suid)
            for act in self.api_clnt._actions:
                task_info ={'auth': auth_info, 'suid': suid, 'action': act}
                kafka_queue_send(self.producer, dict2json(task_info), partition_key=act)
        raise Return(None)
