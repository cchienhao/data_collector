'''
Created on May 27, 2013

@author: alex
'''
import sys
import os
import glob
from config import Config, ConfigMerger, defaultMergeResolve
from ConfigParser import SafeConfigParser

from src.common.fileutil import get_filepaths_from_pythonpath
from src.common.systemutil import get_home
from src.common.logutil import get_logger

_CONFIG = Config()
_logger = get_logger(__name__)

def overwriteMergeResolve(map1, map2, key):
    rv = defaultMergeResolve(map1, map2, key)
    if rv == "mismatch" or rv == "append":
        rv = "overwrite"
    return rv

def initialize(load_test_conf = False):
    global _CONFIG
    _merger = ConfigMerger(overwriteMergeResolve)
    conf_list = []
    test_conf_list = []
    
    for path in sys.path:
        file_list = glob.glob(os.path.join(path, 'env*.conf'))
        for file_path in file_list:
            if file_path.find('_test.conf') >= 0:
                test_conf_list.append(file_path)
            else:
                conf_list.append(file_path)
    
    if load_test_conf:
        all_conf_list = conf_list + test_conf_list
    else:
        all_conf_list = conf_list
        
    _logger.debug('load config files %s', all_conf_list)
    for file_path in all_conf_list:
        f = file(file_path)
        
        try:
            cfg = Config(f)
            _merger.merge(_CONFIG, cfg)
        except:
            _logger.warn('load config file %s failed.', file_path, exc_info = True)
        
    _logger.debug('all configurations: %s', _CONFIG)
    
def get_config():
    return _CONFIG

def get_config_parser(conf_name):
    """
    Get U{ConfigParser<http://docs.python.org/2/library/configparser.html>} object by the relative configuration file name.
    The method will search PYTHONPATH to find out where the file is, 
    and create ConfigParser by the absolute file path.
    @param conf_name: A relative configuration file name.
    @type conf_name: C{string}
    @return: A configuration parser.
    @rtype: U{ConfigParser<http://docs.python.org/2/library/configparser.html>}
    """
    flames_home = get_home()
    
    conf_paths = get_filepaths_from_pythonpath(conf_name)
    parser = SafeConfigParser({'flames_home':flames_home})
    parser.read(conf_paths)
    
    return parser
