'''
Created on 31 May 2013

@author: achi
'''
import time

import redis
from redis.exceptions import ConnectionError

from src.common.logutil import get_logger
from src.common.configutil import get_config

_client = None
_config = get_config()

_logger = get_logger(__name__)

def initialize():
    global _client
    
    _logger.info('Initialize redis connection pool on %s:%d/%d.', 
             _config.redis.host, _config.redis.port, _config.redis.db_number)

    _client = redis.StrictRedis(host=_config.redis.host,
                                port=_config.redis.port,
                                db=_config.redis.db_number)
    
def get_redis_client():
    return _client
    
def get_redis_status():
    pong = None
    latency = None
    try:
        start = time.time()
        pong =_client.ping()
        end = time.time()
        latency = end - start
    except ConnectionError:
        _logger.exception("Redis connection error")
    
    return {
        "ping": pong,
        "latency": latency
    }

    