from __future__ import unicode_literals

import os
import signal
import logging
import logging.handlers

import daemon
import lockfile

from consys.server.network import SshServer

def run():
    # Setting up logging
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(fmt='%(asctime)s [%(name)s] -- %(message)s')
    log_file = logging.handlers.RotatingFileHandler('server.log',
                    maxBytes=1024*64, backupCount=3)
    log_file.setLevel(logging.DEBUG)
    log_file.setFormatter(file_formatter)
    root_log.addHandler(log_file)
    
#    syslog_formatter = logging.Formatter(fmt='[%(name)s]: %(message)s')
#    log_syslog = logging.handlers.SysLogHandler(b'/dev/log')
#    log_syslog.setLevel(logging.INFO)
#    log_syslog.setFormatter(syslog_formatter)
#    root_log.addHandler(log_syslog)
    
    root_log.info('Logging started')
    log = logging.getLogger(__name__)
    
    cd = os.getcwd()

    context = daemon.DaemonContext(
        #pidfile=lockfile.FileLock(u'consys-server.run'),
        signal_map = {
            signal.SIGUSR1: u'terminate',
        },
        files_preserve = [log_file.stream],
    )
    
    log.debug('Entering daemon context...')
    #if True:
    with context:
        try:
            log.info('Initializing ConSys server daemon...')
            config = {"bind-address": "0.0.0.0",
                      "listen-port": 2222,
                      "server-key": os.path.join(cd, "keys/server"),
                      "client-public-key": os.path.join(cd, "keys/client.pub"),
                      "client-user-name": "test"
                      }
            server = SshServer(config)
            server.serve_forever()
            log.info('Terminating ConSys server daemon...')
        except Exception:
            log.exception("Unhandled exception in main thread, exiting")
            