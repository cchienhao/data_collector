'''
Created on 

@author: Kevin Chien
'''
from src.common.status import  FlamesStatus

USER_DUPLICATE = FlamesStatus(1080001, "fitbit.user_duplicate", "'{user_id}' is existed")
USER_NOT_FOUND = FlamesStatus(1080002, "fitbit.user_not_found", "'{user_id}' is not found")
