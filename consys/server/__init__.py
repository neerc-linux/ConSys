from __future__ import unicode_literals

import os
import signal

import lockfile

from consys.common import log
from consys.common import configuration
import consys.common.daemonise as daemonise
from consys.server.network import SSHServer

_log = log.getLogger(__name__)

def run():
    log.init('server.log')
    
    context = daemonise.getContext(
        #pidfile=lockfile.FileLock('consys-server.run'),
        signal_map = {
            signal.SIGUSR1: 'terminate',
            signal.SIGHUP: configuration.reload,
        },
    )
    
    _log.debug('Entering running context...')
    with context:
        try:
            _log.info('Initializing ConSys server daemon...')
            server = SSHServer()
            server.serve_forever()
            _log.info('Terminating ConSys server daemon...')
        except Exception:
            _log.exception("Unhandled exception in main thread, exiting")
            