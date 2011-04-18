from __future__ import unicode_literals

import os
import signal

import lockfile

from consys.common import log
from consys.common import configuration
from consys.common import daemonise

_log = log.getLogger(__name__)

def run():
    log.init('client.log')
    
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
            _log.info('Initializing ConSys client daemon...')
            from consys.client import network 
            network.start_networking()
            network.dispatch_loop()
            _log.info('Terminating ConSys client daemon...')
        except Exception:
            _log.exception('Unhandled exception in main thread, exiting')
            
