'''
Logging wrapper.

@author: Kirill Elagin
'''


from __future__ import unicode_literals

import logging
import logging.handlers


getLogger = logging.getLogger

_root_log = logging.getLogger()
_root_log.setLevel(logging.DEBUG)

_stderr_formatter = logging.Formatter(fmt='%(levelname)s: %(message)s')
_log_stderr = logging.StreamHandler()
_log_stderr.setLevel(logging.ERROR)
_log_stderr.setFormatter(_stderr_formatter)
logging.getLogger('consys.common.configuration').addHandler(_log_stderr)


def init(filename=None):
    from consys.common import daemonise
    from consys.common import configuration

    config = configuration.register_section('log', 
        {
            'syslog': 'boolean(default=False)',
        })

    if filename is not None:
        file_formatter = logging.Formatter(fmt='%(asctime)s [%(name)s] -- %(message)s')
        log_file = logging.handlers.RotatingFileHandler(filename,
                        maxBytes=1024*64, backupCount=3)
        log_file.setLevel(logging.DEBUG)
        log_file.setFormatter(file_formatter)
        _root_log.addHandler(log_file)
        daemonise.preserve_handle(log_file.stream)
    
    if config['syslog']:
        syslog_formatter = logging.Formatter(fmt='[%(name)s]: %(message)s')
        log_syslog = logging.handlers.SysLogHandler(b'/dev/log')
        log_syslog.setLevel(logging.INFO)
        log_syslog.setFormatter(syslog_formatter)
        _root_log.addHandler(log_syslog)
    
    _root_log.info('Logging started')

    # Set up twisted to use generic logging
    from twisted.python import log as twisted_log
    twisted_log.PythonLoggingObserver().start()