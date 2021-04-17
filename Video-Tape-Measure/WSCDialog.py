# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Slalo\Dropbox\PythonScripts\VTM\WSC.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(351, 309)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(70, 250, 201, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.txtEventID = QtWidgets.QLineEdit(Dialog)
        self.txtEventID.setGeometry(QtCore.QRect(40, 100, 113, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.txtEventID.setFont(font)
        self.txtEventID.setObjectName("txtEventID")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(40, 70, 301, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(40, 160, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.txtEventSubID = QtWidgets.QLineEdit(Dialog)
        self.txtEventSubID.setGeometry(QtCore.QRect(40, 190, 281, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        self.txtEventSubID.setFont(font)
        self.txtEventSubID.setObjectName("txtEventSubID")
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setGeometry(QtCore.QRect(10, 20, 331, 31))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setItalic(True)
        self.label_5.setFont(font)
        self.label_5.setStyleSheet("color: rgb(255, 0, 0);")
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Tournament Sanction Number"))
        self.label_2.setText(_translate("Dialog", "Event Sub ID"))
        self.label_5.setText(_translate("Dialog", "Scorer can provide you these values"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
