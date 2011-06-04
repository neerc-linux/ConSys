from __future__ import unicode_literals

import signal
import sys

from PyQt4 import QtCore, QtGui

from consys.common import log
from consys.common import configuration

_log = log.getLogger(__name__)

def run():
    log.init('admin.log')    
    
    try:
        _log.info('Working directory: {0}'.format(configuration.workingdir()))
        _log.info('Configuration file: {0}'.format(configuration.filename()))
        _log.info('Initializing ConSys admin...')
        global qtapp
        qtapp = QtGui.QApplication(sys.argv)
        from consys.common import qt4reactor
        qt4reactor.install()
        from consys.common import app
        from consys.admin import login
        app.startup()
        app.dispatch_loop()
        _log.info('Terminating ConSys admin...')
    except Exception:
        _log.exception('Unhandled exception in main thread, exiting')
            