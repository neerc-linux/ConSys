'''
Main admin window.
@author: Nikita Ofitserov
'''

from PyQt4 import QtGui

from twisted.internet import reactor

from consys.admin import login, hwview
from consys.admin.main_ui import Ui_MainWindow

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.hwmodel = hwview.HardwareModel()
        hwview.connect_model(self.hwmodel)
        self.ui.terminalsView.setModel(self.hwmodel)

    def closeEvent(self, *args, **kwargs):
        reactor.stop()

def on_login():
    global _window
    _window = MainWindow()
    _window.show()

login.successful.connect(on_login)
