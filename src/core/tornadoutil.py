'''
Created on May 28, 2013

@author: alex
'''
import sys
import traceback
import time

from tornado.web import RequestHandler
from tornado import escape

import src.common.tornadoutil as flames_toroado   

from src.common.logutil import get_logger
from src.common.stringutil import encoded_string_dict
from src.common.configutil import get_config
from src.common.jsonutil import dict2json
from src.common.error import FlamesError
from src.common.status import OK, UNEXPECTED_EXCEPTION, UNKNOWN_RESOURCE
from datetime import datetime
#from src.core.accesslogutil import write_access_log

_config = get_config()
logger = get_logger(__name__)

# Re-export from flames_toroado, for backward compatibility
HTTP_METHOD = flames_toroado.HTTP_METHOD 
MultiRoutesHandler = flames_toroado.MultiRoutesHandler

def route(pattern, method, version = None):
    """
    Wrap src.common.tornado.route with an additional argument 'version'
    """
    if version:
        for v in _config.api_versions:
            if eval(str(v) + version):
                real_pattern = '/v' + str(v) + pattern
    else:
        real_pattern = pattern
            
    return flames_toroado.route(real_pattern, method)

def start():
    settings = dict(_config.tornado)
    settings["modules"] = _config.enabled_modules
    settings["static_path"] = _config.home + "/static"
    settings["handlers"] = [
        ('^/version$', VersionInfoHandler)
    ]
#     server_options = {
#         "max_buffer_size": settings.get("max_buffer_size")
#     }    
    flames_toroado.start(settings)
    
class VersionInfoHandler(RequestHandler):
    def _execute(self, transforms, *args, **kwargs):
        version_info = {
            "release_version": _config.release_version,
            "release_time": _config.release_time
        }
        
        self._transforms = transforms
        self.prepare()
        self.write(version_info)
        self.finish()
    
class BaseHandler(flames_toroado.MultiRoutesHandler):
    def initialize(self):        
        self._logger = get_logger(self.__class__)
        self._finish = super(BaseHandler, self).finish
        self._start_time = time.time()
    
    def _handle_request_exception(self, e):
        message = {"code": UNEXPECTED_EXCEPTION.code, "message": UNEXPECTED_EXCEPTION.message}
        http_code = 500
        
        try:
            if isinstance(e, FlamesError):
                if e.status_code.code == UNKNOWN_RESOURCE.code:
                    http_code = 404
                    self._logger.debug("Unknown resource %s %s" % (self.request.method, self.request.path))
                else:
                    http_code = 400
                    self._logger.debug("A bee exception occurs %s" % e)
                
                kwargs = encoded_string_dict(e.kwargs)
                message = {"code": e.status_code.code, "message": e.status_code.message.format(**kwargs)}
            else:
                self._logger.exception("An unexpected exception occurs.")
        except:
            self._logger.exception("An unexpected exception occurs.")
                    
        if _config.debug_mode:
            etype, value, tb = sys.exc_info()
            exceptions = traceback.format_exception(etype, value, tb)
            
            message['stacktrace'] = ''.join(exceptions[_config.debug_stacktrace_limit:])

        self.set_status(http_code)
        self.write(message)
        self.finish()
        
    def write_result(self, result = None):
        message = {"code": OK.code, "message": OK.message}
        
        if result is not None:
            # remove all fields starts with '__'. For example: '__from__'
            if isinstance(result, list):
                [element.pop(key, None) for element in result if isinstance(element, dict) for key in element.keys() if key.startswith('__')]
            elif isinstance(result, dict):
                [result.pop(key, None) for key in result.keys() if key.startswith('__')]
            
            message['result'] = result
        
        self.write(message)
        self.finish()
        
    def write(self, chunk):
        if self._finished:
            raise RuntimeError("Cannot write() after finish().  May be caused "
                               "by using async operations without the "
                               "@asynchronous decorator.")

        chunk = dict2json(chunk)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Cache-Control", "no-store")
            
        chunk = escape.utf8(chunk)
        self._write_buffer.append(chunk)
        
    def finish(self):
        self._finish()        
        #app_id = self.app_id if hasattr(self, "app_id") else None
        #_response_time = int((time.time() - self._start_time)*1000)
        #write_access_log(self.request, self.get_status(), app_id, _response_time)

    def validate_datetime(self, date):
        ''' Parse the input date time string into base and condition parts.
            like: 
                2015-08-01/1d -> base = 2015-08-01; cond = 1d.
                2015-08-01/2015-08-02 -> base = 2015-08-01; cond = 2015-08-02.
        '''
        base=date
        cond=None        
        date_list = date.split('/')
        if len(date_list) == 2:
            base = date_list[0]
            cond = date_list[1]        
        try :
            time_st = datetime.strptime(base, '%Y-%m-%d')

        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        
        if cond and len(cond) > 4:
            try :
                datetime.strptime(cond, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return base, cond
