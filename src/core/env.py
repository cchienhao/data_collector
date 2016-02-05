import os
import sys
import glob
import getpass

current_user = getpass.getuser()
# if current_user != 'bee':
#     print "The program can be run as bee account only, but the current user is %s" % current_user
#     sys.exit(1)
        
join = os.path.join
base = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
base = os.path.dirname(base)

os.environ['FLAMES_HOME'] = base
os.environ['PYTHON_EGG_CACHE'] = base + '/tmp'

activate_this = '/usr/local/lib/qcloud-api-venv/bin/activate_this.py'
if os.path.exists(activate_this):
    execfile(activate_this, dict(__file__=activate_this))

for path in glob.glob(join(base, 'lib/*.egg')):
    sys.path.insert(0, path)

sys.path.insert(0, join(base, 'res'))
sys.path.insert(0, join(base, 'conf.d'))
sys.path.insert(0, join(base, 'conf'))

print 'Env Variables:'
print '- FLAMES_HOME = ' + os.environ['FLAMES_HOME']
print '- PYTHON_EGG_CACHE = ' + os.environ['PYTHON_EGG_CACHE']
print ''
print 'sys.path:'
print sys.path
print ''