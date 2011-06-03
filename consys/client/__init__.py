from __future__ import unicode_literals

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
            _log.info('Working directory: {0}'.format(configuration.workingdir()))
            _log.info('Configuration file: {0}'.format(configuration.filename()))
            _log.info('Initializing ConSys client daemon...')
            # Install GLib reactor
            from twisted.internet import glib2reactor
            glib2reactor.install()
            from consys.common import app
            from consys.client import network, persistence
            app.startup()
            app.dispatch_loop()
            _log.info('Terminating ConSys client daemon...')
        except Exception:
            _log.exception('Unhandled exception in main thread, exiting')
            
