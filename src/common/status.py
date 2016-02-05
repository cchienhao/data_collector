'''
Created on Aug 29 2015

@author: kevin.chien@94301.ca
'''
class FlamesStatus(object):
    def __init__(self, code, key, message):
        self.code = code
        self.key = key
        self.message = message

    def __eq__(self, other):
        if isinstance(other, FlamesStatus):
            return other.code == self.code
        
        return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
        
# server info status code
OK = FlamesStatus(0, 'common.ok', 'OK.')

# server error status code
UNEXPECTED_EXCEPTION = FlamesStatus(1000001, 'common.unexpected_exception', 'Unknown Error.')
UNKNOWN_RESOURCE = FlamesStatus(1000002, 'common.unknown_resource', 'Unknown Resource.')
PARAMETER_VALIDATED_FAILED = FlamesStatus(1000003, 'common.parameter_validated_failed',
                                        'Parameter validated error : {messages}')
AUTH_FAILED = FlamesStatus(1000004, 'common.auth_failed', "Authorization failed : {messages}")
JSON_PARSING_FAILED = FlamesStatus(1000004, 'common.json_parsing_failed', 'Parsing json string failed : {message}')
USER_DUPLICATE = FlamesStatus(1080001, "user_duplicate", "'{user_id}' is existed")
USER_NOT_FOUND = FlamesStatus(1080002, "user_not_found", "'{user_id}' is not found")


