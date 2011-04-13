from __future__ import unicode_literals

import signal
import logging
import logging.handlers

import daemon
import lockfile

def run():
    # Setting up logging
    root_log = logging.getLogger()
    root_log.setLevel(logging.INFO)
    
    file_formatter = logging.Formatter(fmt='%(asctime)s [%(name)s] -- %(message)s')
    log_file = logging.handlers.RotatingFileHandler('server.log',
                    maxBytes=1024, backupCount=3)
    log_file.setLevel(logging.INFO)
    log_file.setFormatter(file_formatter)
    root_log.addHandler(log_file)
    
#    syslog_formatter = logging.Formatter(fmt='[%(name)s]: %(message)s')
#    log_syslog = logging.handlers.SysLogHandler(b'/dev/log')
#    log_syslog.setLevel(logging.INFO)
#    log_syslog.setFormatter(syslog_formatter)
#    root_log.addHandler(log_syslog)
    
    root_log.info('Logging started')
    log = logging.getLogger(__name__)
    
    context = daemon.DaemonContext(
        #pidfile=lockfile.FileLock(u'consys-server.run'),
        signal_map = {
            signal.SIGUSR1: u'terminate',
        },
        files_preserve = [log_file.stream],
    )
    
    log.debug('Entering daemon context...')
    with context:
        log.info('Initializing ConSys server daemon...')
        log.info('Terminating ConSys server daemon...')