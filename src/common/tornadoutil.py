'''
Created on Aug 28 2015

@author: Kevin Chien
'''
import inspect
import atexit
import re
from collections import OrderedDict
import urllib as urllib_parse  # py2

import tornado.process as process

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.httpclient import HTTPError
from tornado.web import Application
from tornado import netutil, httpclient
from tornado.httpserver import HTTPServer
from tornado.web import RequestHandler, asynchronous
from tornado import escape
from tornado.httpclient import AsyncHTTPClient

from src.common.logutil import get_logger
from src.common.reflectionutil import import_resource, enum
from src.common.jsonutil import str2bool, validate, json2dict
from src.common.error import FlamesError
from src.common.status import UNKNOWN_RESOURCE, USER_NOT_FOUND
from tornado.auth import OAuth2Mixin
from tornado.gen import Return, coroutine
from src.user.service import get_user_auth, update_user_auth
#from src.common.cacheutil import get_cache, set_cache

HTTP_METHOD = enum(GET = 'GET', POST = 'POST', PUT = 'PUT', DELETE = 'DELETE')

_handler_dict = OrderedDict()
_logger = get_logger(__name__)

AsyncHTTPClient.configure(None, max_clients=100)
#AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=100)

def add_timer_routine(callback, callback_time):        
    return PeriodicCallback(callback, callback_time)
    
def del_timer_routine(timer):
    timer.stop()

def route(pattern, method = HTTP_METHOD.GET):
    """
    Decorator to declare the routing rule of handler methods.
    """
    def decorator(func):
        frm = inspect.stack()[1]
        class_name = frm[3]
        module_name = frm[0].f_back.f_globals["__name__"]
        full_class_name = module_name + '.' + class_name
        
        real_pattern = '^' + pattern + '$'

        add_handler(method, real_pattern, full_class_name, func)
        
        return asynchronous(func)
    return decorator

def add_handler(method, pattern, full_class_name, func):
    _handler_dict.setdefault(full_class_name, []).append((method, pattern, func.__name__))
    _logger.debug("register %s %s to %s.%s" % (method, pattern, full_class_name, func.__name__))

def start(settings):
    
    application = get_application(settings)
    
    http_server = HTTPServer(application)
    
    unix_socket_enabled = settings.get("unix_socket_enabled")
    sockets = []
    if unix_socket_enabled:
        server_unix_socket_file = settings.get("unix_socket_file")
        server_backlog = settings.get("backlog")
        # Use unix socket
        _logger.info('Bind unix socket file %s', server_unix_socket_file)
        socket = netutil.bind_unix_socket(server_unix_socket_file, 0600, server_backlog)
        sockets.append(socket)
    else:
        server_port = settings.get("port")
        # Normal way to enable a port for listening the request
        _logger.info('Listen on port %d', server_port)
        sockets.extend(netutil.bind_sockets(server_port))
    
    process_count = settings.get("process_count")
    if not settings.get("debug") and process_count != 1:
        if process_count <= 0:
            process_count = process.cpu_count()
        elif process_count > 1:
            _logger.info('Start %d processes', process_count) 
        process.fork_processes(process_count)
        
    http_server.add_sockets(sockets)
    
    # Start Service
    _logger.info('Start tornado server')
    try:
        IOLoop.instance().start()
    except:
        _logger.fatal('Start tornado server failed', exc_info = True)
        raise

def get_application(settings, handlers = None):
    if handlers is None:
        handlers = []
    
    modules = settings["modules"]
    
    if modules:
        for module in modules:
            handler_module_name = module.strip()
            try:
                import_resource(handler_module_name + '.handler')
            except Exception:
                _logger.warn("import module %s failed" % handler_module_name, exc_info=True)
                
    for class_name, tuple_list in _handler_dict.items():
        handlers.extend([(t[1], import_resource(class_name)) for t in tuple_list])
        
    # add handler for urls that not mapped by any other handlers
    handlers.append((r'/.*', ResourceNotFoundHandler))
    
    return Application(handlers, settings)
    
@atexit.register
def stop():
    if not IOLoop.instance()._closing:
        _logger.info('stop tornado server')
        IOLoop.instance().close()

class MultiRoutesHandler(RequestHandler):
    def initialize(self):
        self._logger = get_logger(self.__class__)

    def _get_func_name(self):
        full_class_name = self.__module__ + '.' + self.__class__.__name__
        tuple_list = _handler_dict.get(full_class_name)
        if tuple_list is None:
            raise FlamesError(UNKNOWN_RESOURCE)
        
        for t in tuple_list:
            htt_method = t[0]
            pattern = t[1]
            func_name = t[2]
            
            regex = re.compile(pattern)
            match = re.match(pattern, self.request.path)
            if htt_method == self.request.method and match:
                args = []
                kwargs = {}
        
                def unquote(s):
                    if s is None:
                        return s
                    return escape.url_unescape(s, encoding=None)
                        
                if regex.groupindex:
                    kwargs = dict(
                        (str(k), unquote(v))
                        for (k, v) in match.groupdict().items())
                else:
                    args = [unquote(s) for s in match.groups()]
                            
                return func_name, args, kwargs
        
        raise FlamesError(UNKNOWN_RESOURCE)
        
    def _execute(self, transforms, *args, **kwargs):
        """Executes this request with the given output transforms."""
        self._transforms = transforms
        try:
            # If XSRF cookies are turned on, reject form submissions without
            # the proper cookie
            if self.request.method not in ("GET", "HEAD", "OPTIONS") and \
                    self.application.settings.get("xsrf_cookies"):
                self.check_xsrf_cookie()
            self.prepare()
            if not self._finished:
                func_name, args, kwargs = self._get_func_name()
                self.path_args = [self.decode_argument(arg) for arg in args]
                self.path_kwargs = dict((k, self.decode_argument(v, name=k))
                                    for (k, v) in kwargs.items())
            
                self._logger.debug('call function ' + func_name)
                getattr(self, func_name)(
                    *self.path_args, **self.path_kwargs)
                if self._auto_finish and not self._finished:
                    self.finish()
        except Exception as e:
            self._handle_request_exception(e)
            
    def get_argument_dict(self, schema = None, validated = True):
        """Returns a dictionary of all arguments.
        The returned values are always unicode. The function does not handle array or nested arguments.
        """
        arguments = {}
        properties = schema.get('properties')
        if properties is not None:
            for prop_name, prop in properties.iteritems():
                prop_type = prop.get('type')
                value = self.get_argument(prop_name, None, strip = False)
                if value is not None:
                    if prop_type == 'integer':
                        try:
                            value = int(value)
                        except:
                            pass
                    elif prop_type == 'boolean':
                        value = str2bool(value)
                        
                    if prop.get("strip", True) and hasattr(value, 'strip'):
                        arguments[prop_name] = value.strip()
                    else:
                        arguments[prop_name] = value
        
        if validated and schema:
            validate(arguments, schema)
            
        return arguments

        
class ResourceNotFoundHandler(RequestHandler):
    def initialize(self):
        self._logger = get_logger(self.__class__)
        
    def get(self):
        self._write_result()
        
    def post(self):
        self._write_result()
        
    def put(self):
        self._write_result()
        
    def delete(self):
        self._write_result()
        
    def _write_result(self):
        self._logger.debug("Unknown resource %s %s" % (self.request.method, self.request.path))
        
        self.set_status(404)
        message = {"code": UNKNOWN_RESOURCE.code, "message": UNKNOWN_RESOURCE.message}

        self.write(message)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.finish()


class OAuth2ClientAPI(OAuth2Mixin):
    
    _API_URL                = ""
    _OAUTH_SETTINGS_KEY     = ""
    _OAUTH_ACCESS_TOKEN_URL = ""
    _OAUTH_AUTHORIZE_URL    = ""
    _OAUTH_REQUEST_TOKEN_URL= "" 
    _OAUTH_NO_CALLBACKS     = False    
    _SERVC_PREFIX           = ""
        
    _APP_SETTINGS           = {}
    
    def __init__(self, app_name, app_settings):
        self._logger = get_logger(self.__class__)
        self._APP_SETTINGS = app_settings
        self._SERVC_PREFIX = app_name

    @coroutine
    def get_authenticated_user(self, code, extr_headers={}):
        """Handles the login for the user, returning a user object.
        """
        url = self._OAUTH_ACCESS_TOKEN_URL
        client_id = self._APP_SETTINGS['client_id']
        client_secret = self._APP_SETTINGS['consumer_secret']
        http = self.get_auth_http_client()
        headers={'Content-type': 'application/x-www-form-urlencoded'}
        for hdr_name, hdr_value in extr_headers.iteritems():
            headers[hdr_name] = hdr_value

        scope = " ".join(self._APP_SETTINGS['scope'].split())

        body = urllib_parse.urlencode({
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,                                       
            "code": code,                                       
            "redirect_uri": self._APP_SETTINGS['redirect_uri'],
            "scope": scope
        })
        try :
            response = yield http.fetch(url, method="POST", headers=headers, 
                                        body=body)
        except Exception as e:
            self._logger.error("Request %s %s" % (url, e))
            raise e
#        self._logger.debug(response.body)
        #TODO: check the response status code.
        raise Return(json2dict(response.body))
    
    def get_auth_http_client(self):
        """Returns the `.AsyncHTTPClient` instance to be used for auth requests.
        May be overridden by subclasses to use an HTTP client other than
        the default.
        """
        return httpclient.AsyncHTTPClient()    
    
    @coroutine
    def refresh_token(self, suid, extr_headers={}):
        auth_info = yield get_user_auth(suid, self._SERVC_PREFIX)
        if auth_info is None:
            self._logger.warn("There is no login user info.")
            raise FlamesError(USER_NOT_FOUND, user_id=suid)
        url = self._OAUTH_ACCESS_TOKEN_URL
 
        httpc = httpclient.AsyncHTTPClient()
        post_args = {
            "grant_type": "refresh_token",
            "client_id": self._APP_SETTINGS['client_id'],
            "client_secret": self._APP_SETTINGS['consumer_secret'], 
            "refresh_token": auth_info['refresh_token']
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        for hdr_name, hdr_value in extr_headers.iteritems():
            headers[hdr_name] = hdr_value    
        try :
            response = yield httpc.fetch(url, method="POST", 
                                         body=urllib_parse.urlencode(post_args),
                                         headers=headers)
            result = json2dict(response.body)
            update_user_auth(suid, result, self._SERVC_PREFIX)
        except HTTPError as e:
            self._logger.error("Request %s %s" % (url, e))
            raise e
        self._logger.info("Request %s done." % (url))
        raise Return(result)

    @coroutine
    def api_request(self, suid, url, hdr_auth=True, post_args=None, resend=False, 
                    json_schema=None, auth_info=None, **args):

        if auth_info is None:
            auth_info = yield get_user_auth(suid, self._SERVC_PREFIX)
            if auth_info is None:
                self._logger.warn("There is no login user info.")
                raise FlamesError(USER_NOT_FOUND, user_id=suid)

        hdr = {}
        all_args = {}
        if hdr_auth:
            oauth = "Bearer " + auth_info['access_token']
            hdr = {'Authorization': oauth}
        else :
            all_args = {'access_token': auth_info['access_token']}

        if args:
            all_args.update(args)

        if all_args:
            url += "?" + urllib_parse.urlencode(all_args)
        self._logger.debug(url)
        httpc = self.get_auth_http_client()
        result = {}
        try:
            if post_args is not None:
                response = yield httpc.fetch(url, method="POST",
                                             body=urllib_parse.urlencode(post_args), 
                                             headers=hdr)
            else:
                response =  yield httpc.fetch(url,headers=hdr)
            result = json2dict(response.body, schema=json_schema, validated=True)
            self._logger.info("Request %s done." % (url))
        except HTTPError as e:
            if e.code == 401 and resend == False:            
                auth_info = yield self.refresh_token(suid)
                # Update the auth token, and send request again.                
                yield update_user_auth(suid, auth_info, self._SERVC_PREFIX);
                result = yield self.api_request(suid, url, post_args, 
                                                resend=True, **args)
            result={'code': e.code, "message": e.message}
        finally:
            raise Return(result)
