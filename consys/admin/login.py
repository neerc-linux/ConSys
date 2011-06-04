'''
Login dialog code.
@author: Nikita Ofitserov
'''

from notify.all import Signal 
from PyQt4 import QtGui

from twisted.conch import error

from consys.common import configuration
from consys.common import log
from consys.common import app
from consys.admin.login_ui import Ui_LoginDialog
from consys.admin import network

_log = log.getLogger(__name__)

class LoginHandler(object):

    def on_login(self):
        self.ui.editLogin.setEnabled(False)
        self.ui.editPassword.setEnabled(False)
        self.ui.buttonLogin.setEnabled(False)
        credentials = network.Credentials(unicode(self.ui.editLogin.text()),
                                          unicode(self.ui.editPassword.text()))
        d = network.do_connect(credentials)
        def _ebConnectionFailed(failure):
            if failure.check(error.UnauthorizedLogin):
                pass
            self.ui.editPassword.selectAll()
            color = QtGui.QColor(255, 128, 128)
            highlight_background(self.ui.editLogin, color)
            highlight_background(self.ui.editPassword, color)
            self.ui.buttonLogin.setEnabled(True)
            self.ui.editPassword.setEnabled(True)
            self.ui.editLogin.setEnabled(True)
            self.ui.editPassword.setFocus()
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
        self.ui.editLogin.selectionChanged.connect(self.restore_colors)
        self.ui.editPassword.selectionChanged.connect(self.restore_colors)
        self.ui.editLogin.cursorPositionChanged.connect(self.restore_colors)
        self.ui.editPassword.cursorPositionChanged.connect(self.restore_colors)
        self.ui.editLogin.oldPalette = None
        self.ui.editPassword.oldPalette = None
        self.dialog.show()

    def restore_colors(self):
        restore_background(self.ui.editLogin)
        restore_background(self.ui.editPassword)

_handler = LoginHandler()
connection = None

successful = Signal()
'''Is fired after a successful login attempt'''

app.startup.connect(_handler.on_startup)

def highlight_background(object, color):
    object.oldPalette = object.palette()
    p = QtGui.QPalette(object.oldPalette)
    p.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
    object.setPalette(p)

def restore_background(object):
    if object.oldPalette is not None:
        object.setPalette(object.oldPalette)
        object.oldPalette = None
