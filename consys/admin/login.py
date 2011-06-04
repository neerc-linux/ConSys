'''
Login dialog code.
@author: Nikita Ofitserov
'''

from notify.all import Signal 
from PyQt4 import QtGui

from consys.common import configuration
from consys.common import log
from consys.common import app
from consys.admin.login_ui import Ui_LoginDialog
from consys.admin import network

_log = log.getLogger(__name__)

class LoginHandler(object):

    def on_login(self):
        self.ui.buttonLogin.setEnabled(False)
        hostname = self.ui.editServerAddress.text()
        port = self.ui.spinServerPort.value()
        server_string = 'tcp:host={0}:port={1}'.format(hostname, port)
        credentials = network.Credentials(unicode(self.ui.editLogin.text()),
                                          unicode(self.ui.editPassword.text()))
        d = network.do_connect(server_string, credentials)
        def _ebConnectionFailed(failure):
            self.ui.buttonLogin.setEnabled(True)
            pass
        def _cbConnected(value):
            global connection
            connection = value
            _log.debug('Login successful')
            self.dialog.accept()
        d.addCallbacks(_cbConnected, _ebConnectionFailed)
    
    def on_login_success(self):
        del self.dialog
        successful()
    
    def on_cancelled(self):
        app.reactor.stop()
    
    def on_startup(self):
        self.dialog = QtGui.QDialog()
        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self.dialog)
        self.ui.buttonLogin.clicked.connect(self.on_login)
        self.dialog.accepted.connect(self.on_login_success)
        self.dialog.rejected.connect(self.on_cancelled)
        self.dialog.show()

_handler = LoginHandler()
connection = None

successful = Signal()
'''Is fired after a successful login attempt'''

app.startup.connect(_handler.on_startup)