import os, time, glob
from setuptools import setup, find_packages
 
PROJ_NAME = os.getenv('PROJ_NAME')
VERSION = os.getenv('VERSION', time.strftime("%Y%m%d", time.localtime()))

setup(
    name = PROJ_NAME,
    version = VERSION,
    author = '#49ers',
    zip_safe = True,
    include_package_data=True,
    
    packages = find_packages('src'),
    package_dir = {'': 'src'}
)