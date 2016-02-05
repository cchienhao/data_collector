'''
Created on May 27, 2013

@author: Kevin Chien
'''
import sys
import os
from os.path import exists

def get_filepath_from_pythonpath(filename):
    """
    Get the first absolute file path when the given file name is found.
    The method will search PYTHONPATH to find out where the file is.
    @param filename: a file name.
    @type filename: C{string}
    @return: an absolute file path.
    @rtype: C{string}
    """
    for path in sys.path:
        real_path = os.path.join(path, filename)
        if exists(real_path):
            return real_path
    
    return None

def get_filepaths_from_pythonpath(filename):
    """
    Get a list of absolute file paths when the given file name is found.
    The method will search PYTHONPATH to find out where the file is.
    @param filename: a file name.
    @type filename: C{string}
    @return: a list of absolute file paths.
    @rtype: C{list} of C{string}
    """
    real_paths = []
    for path in sys.path:
        real_path = os.path.join(path, filename)
        if exists(real_path):
            real_paths.append(real_path)
    
    if len(real_paths) == 0:
        return None
    else:
        return real_paths
    
def get_file_name(path):
    if path.endswith('/'):
        path = path[0:len(path) - 1]
        
    index = path.rfind('/')
    
    if index == 0:
        parent_path = '/'
        file_name = path[1:]
    elif index >= 0:
        parent_path = path[0:index]
        file_name = path[index + 1:]
    else:
        parent_path = ''
        file_name = path
        
    return parent_path, file_name
    