from __future__ import unicode_literals

import signal

from consys.common import log
from consys.common import configuration
from consys.common import daemonise

_log = log.getLogger(__name__)

_config = configuration.register_section(None,
    {
        'server-pid-file': 'path(default=/var/run/consys-server.pid)',
    })

def run():
    try:
        log.init('server.log')

        context = daemonise.getContext(
            pidfile = _config['server-pid-file'],
            signal_map = {
                signal.SIGUSR1: 'terminate',
                signal.SIGHUP: configuration.reload,
            },
        )

        _log.debug('Entering running context...')
        with context:
            _log.info('Configuration file: {0}'.format(configuration.filename()))
            _log.info('Initializing ConSys server daemon...')
            from consys.common import app
            from consys.server import network, persistent, hw, connections, \
                ampserver
            app.startup()
            app.dispatch_loop()
            _log.info('Terminating ConSys server daemon...')
    except Exception:
        _log.exception('Unhandled exception in main thread, exiting')

