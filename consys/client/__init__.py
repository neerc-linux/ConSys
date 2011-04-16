from __future__ import unicode_literals

import os
import signal
import logging
import logging.handlers

import lockfile

import consys.common.daemonise as daemonise

def run():
    # Setting up logging
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(fmt='%(asctime)s [%(name)s] -- %(message)s')
    log_file = logging.handlers.RotatingFileHandler('client.log',
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
    
    context = daemonise.getContext(
        #pidfile=lockfile.FileLock(u'consys-client.run'),
        signal_map = {
            signal.SIGUSR1: u'terminate',
        },
        files_preserve = [log_file.stream],
    )
    
    log.debug('Entering running context...')
    with context:
        try:
            log.info('Initializing ConSys client daemon...')
            from consys.client.network import SSHClient
            client = SSHClient()
            #server.serve_forever()
            log.info('Terminating ConSys client daemon...')
        except Exception:
            log.exception('Unhandled exception in main thread, exiting')
