
from tornado.gen import coroutine, Return

from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.common.cacheutil import get_keys
from src.common.systemutil import get_timestamp
from src.common.queueutil import QUEUE_METHOD, kafka_queue_send
from src.common.jsonutil import dict2json
from src.common.error import FlamesError

from src.collectors.fitbit.status import USER_NOT_FOUND
from src.collectors.facebook.service import FacebookAPI
from src.collectors.facebook.constant import CACHED_PREFIX_KEY

from src.user.service import get_user_auth
from src.trigger.trigger import route, Trigger

_logger = get_logger(__name__)
_config = get_config()
_app_settings = _config.fitbit


class FacebookTrigger(Trigger):

    def __init__(self):
        super(FacebookTrigger, self).__init__(CACHED_PREFIX_KEY)
        self.api_clnt = FacebookAPI()    

    @route("facebook", QUEUE_METHOD.PUSH)
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
