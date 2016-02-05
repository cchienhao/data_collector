'''
Created on Jan 7, 2013

@author: alex
         Andre Lee, Jan 23, 2013
'''
from src.common.status import PARAMETER_VALIDATED_FAILED
from src.common.logutil import get_logger
from src.common.stringutil import encoded_string_dict

logger = get_logger(__name__)

class FlamesError(Exception):
    def __init__(self, status_code, **kwargs):
        self.status_code = status_code
        if kwargs:
            self.kwargs = kwargs
        else:
            self.kwargs = {}
        
        self.flames_attribute = {}
    
    def __str__(self, **kwargs):
        _return = None
        if len(self.kwargs) > 0:
            try:
                string_dict = encoded_string_dict(self.kwargs)
                _return = str(self.status_code.code) + ' : ' + self.status_code.message.format(**string_dict)
            except Exception as e:
                logger.exception('String Format Exception Occurred')

        if not _return:
            _return = str(self.status_code.code) + ' : ' + self.status_code.message
        
        return _return

    def set_attribute(self, key, value):
        # Since we couldn't distinguish and ignore the default attributes, 
        # we setup a default dictionary for storing them instead of using setattr directly.
        #setattr(self, key, value)
        
        self.flames_attribute[key] = value
    
    def set_attributes(self, **kwargs):
        pass       
    
class InvalidArgumentsError(FlamesError):
    def __init__(self):
        super(InvalidArgumentsError, self).__init__(PARAMETER_VALIDATED_FAILED)
        
    def add_messages(self, messages):
        self.kwargs.setdefault('messages', []).extend(messages)