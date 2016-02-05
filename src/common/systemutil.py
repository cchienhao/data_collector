'''
Created on Aug 29 2015

@author: Kevin Chien
'''
import os
import pytz
import time

def get_home():
    return os.getenv("FLAMES_HOME", os.getcwd())

def get_l10n_home():
    return os.path.join(get_home(), 'l10n')
                                         
def get_view_home():
    return os.path.join(get_home(), 'view')

def get_tmp_dir():
    return os.path.join(get_home(), 'tmp')

def get_timestamp(tz='UTC'):
    return int(time.time())
