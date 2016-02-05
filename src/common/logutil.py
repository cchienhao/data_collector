'''
Created on May 27, 2013

@author: Kevin Chien
'''
import re
import socket
import logging.config
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler, SysLogHandler

from src.common.fileutil import get_filepaths_from_pythonpath
from src.common.systemutil import get_home

def initialize(config_file = None):
    """
    Initialize logging module. If _HOME environment variable is set, logging home directory will be _HOME/logs.
    Otherwise, logging home directory will be CurrentDir/logs.
    """
    if not config_file:
        config_file = 'logging.conf'
    logging_paths = get_filepaths_from_pythonpath(config_file)
    flames_home = get_home()
    
    for logging_path in logging_paths:
        logging.config.fileConfig(logging_path, {'flames_home': flames_home})

def get_logger(cls):
    """
    Generate a logger object by the given class. The logger name will be the full qualified class name.
    @param cls: A class to generate the logger.
    @type cls: C{class}
    @return: A logger by the given class.
    @rtype: U{Logger<http://docs.python.org/2/library/logging.html#logger-objects>}
    """
    if hasattr(cls, '__module__') and hasattr(cls, '__name__'):
        logger = logging.getLogger(cls.__module__ + '.' + cls.__name__)
    else:
        logger = logging.getLogger(str(cls))
        
    return logger

class ModuleStreamHandler(StreamHandler):
    """
    A class extends U{logging.StreamHandler<http://docs.python.org/2/library/logging.handlers.html#logging.StreamHandler>},
    and add a regular expression to filter the log messages by module names.
    
    The example below logs messages which are only in tornado module
    
        >>> args=('logs/access.log', '^.*tornado.*$')
        
    """
    def __init__(self, stream=None, module_name='all'):
        super(ModuleStreamHandler, self).__init__(stream)
        self.addFilter(_ModuleFilter(module_name))
        
class ModuleTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    A class extends U{logging.handlers.TimedRotatingFileHandler<http://docs.python.org/2/library/logging.handlers.html#logging.handlers.TimedRotatingFileHandler>},
    and add a regular expression to filter the log messages by module names.
    
    The example below logs messages which are only in tornado module
    
        >>> args=('logs/access.log', '^.*tornado.*$')
        
    """
    def __init__(self, filename, module_name='all', when='d', interval=1, backup_count=0, 
                 encoding=None, delay=False, utc=True):
        super(ModuleTimedRotatingFileHandler, self).__init__(filename, when, interval, backup_count, encoding, delay, utc)
        self.addFilter(_ModuleFilter(module_name))
      
class ModuleSysLogHandler(SysLogHandler):
    def __init__(self, module_name='all', address = '/dev/log', facility = SysLogHandler.LOG_USER,
                 socktype = socket.SOCK_DGRAM):
        super(ModuleSysLogHandler, self).__init__(address, facility, socktype)
        self.addFilter(_ModuleFilter(module_name))
          
class _ModuleFilter(logging.Filter):
    def __init__(self, module_name):
        logging.Filter.__init__(self)
        self.prog = None
        if module_name != 'all':
            self.prog = re.compile(module_name)

    def filter(self, record):
        if record.levelname != 'ERROR' and self.prog is not None and not self.prog.match(record.name):
            return False
        else:
            return True
