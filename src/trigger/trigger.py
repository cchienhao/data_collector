
import inspect

from src.common.configutil import get_config
from src.common.logutil import get_logger
from src.common.reflectionutil import import_resource, get_class

from src.common.tornadoutil import add_timer_routine

from src.common.queueutil import kafka_queue_get_client, \
                                 kafka_queue_get_producer, QUEUE_METHOD

_config = get_config()
_logger = get_logger(__name__)
_trigger_dict={}
_trigger_workers={}

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
    _trigger_dict[pattern] = [full_class_name, func.__name__]
    _logger.debug("register %s %s to %s.%s" % (method, pattern, full_class_name,
                                               func.__name__))

def initialize():
    modules = _config.enabled_pull_triggers
    if modules:
        for module in modules:
            handler_module_name = module.strip()
            try:
                import_resource(handler_module_name + '.trigger')
            except Exception:
                _logger.warn("import module %s failed" % handler_module_name, exc_info=True)
    _logger.info("Trigger modules: %s" % modules)
    for class_name, tuple_list in _trigger_dict.items():
        _logger.info("%s.%s" % (class_name, tuple_list))    

def start():
    for trigger_name, trigger_desc in _trigger_dict.iteritems():
        _logger.debug("%s" % trigger_name)
        trigger_class = get_class(trigger_desc[0])
        _trigger_workers[trigger_name] = trigger_class()     

class Trigger(object):

    def __init__(self, prodc_topic):
        self.kafka_client = kafka_queue_get_client()
        self.producer = kafka_queue_get_producer(self.kafka_client, prodc_topic)
        self.enable_task_routine()

    def enable_task_routine(self):
        self.timer = add_timer_routine(self.task_isr, 20*60*1000)
        self.timer.start()

#     def task_isr(self):
#         raise NotImplementedError
