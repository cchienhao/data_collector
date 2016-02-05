'''
Created on Aug 31 2015

@author: Kevin Chien
'''
from signal import signal, SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM
import sys
import getopt

import src.common.logutil as logutil
from src.common.configutil import get_config


def signal_handler(signal, frame):
    print 'catch signal ' + str(signal)
    sys.exit(0)
    
for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
    signal(sig, signal_handler)

def usage():
    print 'api.py -r <Public host>'
    sys.exit(2)

def main(argv):
    logutil.initialize()

    import src.common.configutil as configutil

    configutil.initialize("^env((?!mydas).)*\.conf$")

    import src.core.redisutil as redisutil
    import src.core.tornadoutil as tornadoutil
    import src.common.queueutil as queueutil
    import src.trigger.trigger as trigger

    print argv

    try:
        opts, args = getopt.getopt(argv,"hr:",["Public host="])
    except getopt.GetoptError:
        usage()
    servc_host = ""
    for opt, arg in opts:
        if opt in ("-r", "--public_host"):
            _config = get_config()
            servc_host = arg
            servc_port = _config.tornado.port
            _config.OAuth2_redirect_uri_host = ("http://%s:%d/v1" % (servc_host, 
                                                                     servc_port))
        else:
            usage()

    redisutil.initialize()
    queueutil.initialize()
    trigger.initialize()

    queueutil.start()
    trigger.start()    
    tornadoutil.start()
        
    
if __name__ == "__main__":
    main()
