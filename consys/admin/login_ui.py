# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'consys/admin/login.ui'
#
# Created: Sat Jun  4 22:13:45 2011
#      by: PyQt4 UI code generator 4.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName(_fromUtf8("LoginDialog"))
        LoginDialog.resize(344, 186)
        LoginDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(LoginDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.labelServerAddress = QtGui.QLabel(LoginDialog)
        self.labelServerAddress.setObjectName(_fromUtf8("labelServerAddress"))
        self.gridLayout.addWidget(self.labelServerAddress, 0, 0, 1, 1)
        self.editServerAddress = QtGui.QLineEdit(LoginDialog)
        self.editServerAddress.setObjectName(_fromUtf8("editServerAddress"))
        self.gridLayout.addWidget(self.editServerAddress, 0, 1, 1, 1)
        self.labelServerPort = QtGui.QLabel(LoginDialog)
        self.labelServerPort.setObjectName(_fromUtf8("labelServerPort"))
        self.gridLayout.addWidget(self.labelServerPort, 1, 0, 1, 1)
        self.labelLogin = QtGui.QLabel(LoginDialog)
        self.labelLogin.setObjectName(_fromUtf8("labelLogin"))
        self.gridLayout.addWidget(self.labelLogin, 2, 0, 1, 1)
        self.editLogin = QtGui.QLineEdit(LoginDialog)
        self.editLogin.setObjectName(_fromUtf8("editLogin"))
        self.gridLayout.addWidget(self.editLogin, 2, 1, 1, 1)
        self.labelPassword = QtGui.QLabel(LoginDialog)
        self.labelPassword.setObjectName(_fromUtf8("labelPassword"))
        self.gridLayout.addWidget(self.labelPassword, 3, 0, 1, 1)
        self.editPassword = QtGui.QLineEdit(LoginDialog)
        self.editPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.editPassword.setObjectName(_fromUtf8("editPassword"))
        self.gridLayout.addWidget(self.editPassword, 3, 1, 1, 1)
        self.spinServerPort = QtGui.QSpinBox(LoginDialog)
        self.spinServerPort.setMinimum(1)
        self.spinServerPort.setMaximum(65535)
        self.spinServerPort.setProperty(_fromUtf8("value"), 2222)
        self.spinServerPort.setObjectName(_fromUtf8("spinServerPort"))
        self.gridLayout.addWidget(self.spinServerPort, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.widget = QtGui.QWidget(LoginDialog)
        self.widget.setMaximumSize(QtCore.QSize(16777215, 35))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(145, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.buttonLogin = QtGui.QPushButton(self.widget)
        self.buttonLogin.setObjectName(_fromUtf8("buttonLogin"))
        self.horizontalLayout.addWidget(self.buttonLogin)
        self.buttonExit = QtGui.QPushButton(self.widget)
        self.buttonExit.setObjectName(_fromUtf8("buttonExit"))
        self.horizontalLayout.addWidget(self.buttonExit)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(LoginDialog)
        QtCore.QObject.connect(self.buttonExit, QtCore.SIGNAL(_fromUtf8("clicked()")), LoginDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)
        LoginDialog.setTabOrder(self.editServerAddress, self.spinServerPort)
        LoginDialog.setTabOrder(self.spinServerPort, self.editLogin)
        LoginDialog.setTabOrder(self.editLogin, self.editPassword)
        LoginDialog.setTabOrder(self.editPassword, self.buttonLogin)
        LoginDialog.setTabOrder(self.buttonLogin, self.buttonExit)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QtGui.QApplication.translate("LoginDialog", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.labelServerAddress.setText(QtGui.QApplication.translate("LoginDialog", "Server", None, QtGui.QApplication.UnicodeUTF8))
        self.editServerAddress.setText(QtGui.QApplication.translate("LoginDialog", "localhost", None, QtGui.QApplication.UnicodeUTF8))
        self.labelServerPort.setText(QtGui.QApplication.translate("LoginDialog", "Server port", None, QtGui.QApplication.UnicodeUTF8))
        self.labelLogin.setText(QtGui.QApplication.translate("LoginDialog", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.editLogin.setText(QtGui.QApplication.translate("LoginDialog", "admin", None, QtGui.QApplication.UnicodeUTF8))
        self.labelPassword.setText(QtGui.QApplication.translate("LoginDialog", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonLogin.setText(QtGui.QApplication.translate("LoginDialog", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonExit.setText(QtGui.QApplication.translate("LoginDialog", "Exit", None, QtGui.QApplication.UnicodeUTF8))

