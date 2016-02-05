'''
Created on Oct 4, 2015

@author: kevinchien
'''

import threading
import inspect
from time import sleep
import time

from pykafka import KafkaClient as PyKafkaClient
from pykafka import BalancedConsumer
from pykafka.partitioners import hashing_partitioner

from tornado.gen import coroutine, Return

from src.common.logutil import get_logger
from src.common.configutil import get_config
from src.common.reflectionutil import enum, import_resource, get_class
from src.common.jsonutil import json2dict, dict2json
from Queue import Queue, Empty
from src.common.tornadoutil import add_timer_routine


QUEUE_METHOD = enum(SUB='SUB', PUSH='PUSH')

_config = get_config()
_logger = get_logger(__name__)
#_handler_dict = OrderedDict()
_handler_dict = {}

logger = get_logger(__name__)

queue_consumer_threads = []
queue_consumer_jobs = []


def route(pattern, method = QUEUE_METHOD.SUB):
    """ Decorator to declare the routing rule of handler methods.
    """
    def decorator(func):
        frm = inspect.stack()[1]
        class_name = frm[3]
        module_name = frm[0].f_back.f_globals["__name__"]
        full_class_name = module_name + '.' + class_name        
        add_handler(method, pattern, full_class_name, func)
        return func

    return decorator


def add_handler(method, pattern, full_class_name, func):
    _handler_dict[pattern] = [full_class_name, func.__name__]
    logger.debug("register %s %s to %s.%s" % (method, pattern, full_class_name, func.__name__))

# def queue_updata_offset(consumer, partition, new_offset):
#     """ Update Kafka Queue offset.     
#     """
#     partition_offset = {partition: new_offset}
#     consumer.reset_offsets(partition_offsets=partition_offset.items())

def kafka_queue_send(kafka_producer, msg, partition_key=None):
    if partition_key:    
        kafka_producer.produce(msg, partition_key=bytes(partition_key))
    else :
        kafka_producer.produce(msg)
    _logger.debug("Send message: %s" % msg)


def kafka_queue_read(kafka_consumer, limit=50, debug_info=False):
    
    def message_print(message):
        _logger.debug(message.partition)
        _logger.debug("%d %s" % (message.offset, message.value))
    
    def message_batch():
        msg_list = []
        while len(msg_list) < limit:
            message = kafka_consumer.consume(False)
            if message is None:
                break
            else:
                if debug_info is True:
                    message_print(message)
                msg_list.append(message)        
        return msg_list

    return message_batch()

def kafka_queue_get_client(hosts="ambarinode1:6667,ambarinode2:6667,ambarinode3:6667"):
    return PyKafkaClient(hosts=hosts)

def kafka_queue_get_topic(kafka_client, topic_str):
    return kafka_client.topics[topic_str]

def kafka_queue_get_producer(kafka_client, topic_str):
    topic = kafka_queue_get_topic(kafka_client, topic_str)
    return topic.get_producer(partitioner=hashing_partitioner)
    

class Worker(object):

    def __init__(self):
        self.queue = Queue()
        self.task_timer = None        
        
    @coroutine
    def worker_handler(self, task_info={}):
        """ Worker service level handler.
        """
        raise  NotImplementedError

    @coroutine
    def _task_handler(self, task_info={}):
        """ Task level handler, we do the task request and response here.
        """
        try :
            result = yield self.worker_handler(task_info)
        except Exception as e:
            result = {"error": e}
        finally:
            # Notify that this task has been done.
            self.queue.task_done()
            # Send the task result if required.
            if self.task_callback is not None:            
                self.task_callback(result, task_info)
            raise Return(None)

    def _task_iterator(self):
        """ Timer triggering function to handle the new coming task.
        """
        while True:
            task_info = self.get_task()
            if task_info is None:
                break
            self._task_handler(task_info)

    def enable_task_routine(self, task_callback=None):
        """ Add a timer to trigger tasks consuming.
        @param task_callback: callback function when this task has been done.
        """
        self.task_callback = task_callback
        self.task_timer = add_timer_routine(self._task_iterator, 1*1000)
        self.task_timer.start()        

    def add_task(self, task_info={}):
        """ Add a new task in worker processing queue.
        @param task_info: new task description
        @type task_info: dict
        """
        self.queue.put(task_info)

    def get_task(self):
        """ Get task item from worker processing queue.
        @return: Task description.
        @rtype: dict or None: no task in queue.
        """
        try :
            return self.queue.get_nowait()
        except Empty:
            return None

    def wait_all_tasks_done(self):
        """ Block until all the task in queue are processed.
        """
        self.queue.join()


class Consumer(threading.Thread):

    daemon = True
    Msg_Window = 50    
    _Consumer_group = None
    _Brokers = "localhost:6667"    
    _Args = {}

    @staticmethod
    def set(brokers, consumer_group, **kafka_consumer_args):
        """ Set the consumer configuration.
        """
        Consumer._Brokers=brokers
        Consumer._Consumer_group=consumer_group
        Consumer._Args=kafka_consumer_args

    def __init__(self, topic):
        threading.Thread.__init__(self) # init the thread        
        self.topic = topic

    def task_callback(self, result, task_info={}):
        response={}        
        response['suid'] = task_info.get('suid')
        response['time'] = time.time()
        response['action'] = task_info.get('action')
        response['data'] = result
        msg = None
        
        try :
            msg = dict2json(response)
        except Exception as e:
            _logger.error("%s" % result )
            response['data'] = e
            msg = dict2json(response)
        finally:
            if msg:
                kafka_queue_send(self.kafka_producer, msg)

    def run(self):
        """ Read messages from queue and set task to worker thread.
            TODO: Remove the kafka related stuff from this function.
        """
        # Brokers should be in the uri path
        # path.strip returns type 'unicode' and pykafka expects a string, so
        # converting unicode to str
        brokers = Consumer._Brokers.strip('/').encode('ascii', 'ignore')
    
        self.kafka_client = PyKafkaClient(hosts=brokers)
        
        kafka_topic = self.kafka_client.topics[self.topic]
        self.kafka_consumer = kafka_topic.get_balanced_consumer(
                           consumer_group=Consumer._Consumer_group.encode('ascii', 'ignore'),
                           **Consumer._Args)
        produce_topic = self.kafka_client.topics[("%s-data" % self.topic)]
        self.kafka_producer = produce_topic.get_producer()        
        
        # Create the worker object.
        handler_desc = _handler_dict[self.topic]        
        worker_class = get_class(handler_desc[0])
        worker = worker_class()

        # Enable timer to consume the worker tasks.
        worker.enable_task_routine(task_callback=self.task_callback)    

        while True:
            msg_list = kafka_queue_read(self.kafka_consumer)
            if len(msg_list) == 0:
                # No data, try again later.
                sleep(1)
                continue
            
            _logger.debug(len(msg_list))
            
            for msg in msg_list:
                task_info = json2dict(msg.value)
                worker.add_task(task_info)

            # Check the worker thread working status; and commit the offset.
            # Wait for the worker consuming all the tasks.
            worker.wait_all_tasks_done()
            # Commit the kafka reading offset.
            self.kafka_consumer.commit_offsets()


def initialize():
    modules = _config.enabled_sub_queue
    if modules:
        for module in modules:
            handler_module_name = module.strip()
            try:
                import_resource(handler_module_name + '.worker')
            except Exception:
                logger.warn("import module %s failed" % handler_module_name, exc_info=True)
    _logger.info("Subscribe modules: %s" % modules)
    for class_name, tuple_list in _handler_dict.items():
        _logger.info("%s %s" % (class_name, tuple_list))


def start():
    """
        Start Queue thread to publish or subscribe from message queue.
    """
    # ToDo: Check configuration for consumer/producer settings.
    brokers        = "ambarinode1:6667,ambarinode2:6667,ambarinode3:6667"
    zookeepers     = "ambarinode1:2181,ambarinode2:2181,ambarinode3:2181"
    consumer_group = "adapters"
    topics         = ["facebook", "fitbit"]
    Consumer.set(brokers, consumer_group, zookeeper_connect=zookeepers)

    queue_consumer_threads = []
    
    for tp in topics :
        t = Consumer(tp)
        t.start()
        queue_consumer_threads.append(t)                


def stop():
    # Terminate consumer threads.
    for t in queue_consumer_threads:
        t.stop()
