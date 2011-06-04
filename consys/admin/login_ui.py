# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'consys/admin/login.ui'
#
# Created: Sun Jun  5 01:10:02 2011
#      by: PyQt4 UI code generator 4.8.3
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
        LoginDialog.setWindowModality(QtCore.Qt.WindowModal)
        LoginDialog.resize(236, 111)
        LoginDialog.setMinimumSize(QtCore.QSize(0, 0))
        LoginDialog.setMaximumSize(QtCore.QSize(16777215, 16777215))
        LoginDialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        LoginDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(LoginDialog)
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.fieldsWidget = QtGui.QWidget(LoginDialog)
        self.fieldsWidget.setObjectName(_fromUtf8("fieldsWidget"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.fieldsWidget)
        self.verticalLayout_2.setContentsMargins(0, -1, 0, 0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.editLogin = QtGui.QLineEdit(self.fieldsWidget)
        self.editLogin.setMinimumSize(QtCore.QSize(228, 23))
        self.editLogin.setInputMethodHints(QtCore.Qt.ImhNone)
        self.editLogin.setMaxLength(15)
        self.editLogin.setAlignment(QtCore.Qt.AlignCenter)
        self.editLogin.setObjectName(_fromUtf8("editLogin"))
        self.verticalLayout_2.addWidget(self.editLogin)
        self.editPassword = QtGui.QLineEdit(self.fieldsWidget)
        self.editPassword.setMinimumSize(QtCore.QSize(228, 23))
        self.editPassword.setInputMethodHints(QtCore.Qt.ImhHiddenText|QtCore.Qt.ImhNoAutoUppercase|QtCore.Qt.ImhNoPredictiveText)
        self.editPassword.setMaxLength(20)
        self.editPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.editPassword.setAlignment(QtCore.Qt.AlignCenter)
        self.editPassword.setObjectName(_fromUtf8("editPassword"))
        self.verticalLayout_2.addWidget(self.editPassword)
        self.verticalLayout.addWidget(self.fieldsWidget)
        self.bottomWidget = QtGui.QWidget(LoginDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bottomWidget.sizePolicy().hasHeightForWidth())
        self.bottomWidget.setSizePolicy(sizePolicy)
        self.bottomWidget.setObjectName(_fromUtf8("bottomWidget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.bottomWidget)
        self.horizontalLayout_2.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.buttonLogin = QtGui.QPushButton(self.bottomWidget)
        self.buttonLogin.setDefault(False)
        self.buttonLogin.setFlat(False)
        self.buttonLogin.setObjectName(_fromUtf8("buttonLogin"))
        self.horizontalLayout_2.addWidget(self.buttonLogin)
        self.verticalLayout.addWidget(self.bottomWidget)

        self.retranslateUi(LoginDialog)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)
        LoginDialog.setTabOrder(self.editLogin, self.editPassword)
        LoginDialog.setTabOrder(self.editPassword, self.buttonLogin)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QtGui.QApplication.translate("LoginDialog", "Consys", None, QtGui.QApplication.UnicodeUTF8))
        self.editLogin.setText(QtGui.QApplication.translate("LoginDialog", "admin", None, QtGui.QApplication.UnicodeUTF8))
        self.editLogin.setPlaceholderText(QtGui.QApplication.translate("LoginDialog", "login", None, QtGui.QApplication.UnicodeUTF8))
        self.editPassword.setPlaceholderText(QtGui.QApplication.translate("LoginDialog", "password", None, QtGui.QApplication.UnicodeUTF8))
        self.buttonLogin.setText(QtGui.QApplication.translate("LoginDialog", "Login", None, QtGui.QApplication.UnicodeUTF8))

