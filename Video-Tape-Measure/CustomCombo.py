# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 16:15:32 2018

@author: slalo
"""

###############################################################################
# This class modifies QCOmboBox so that it adds what to do if RETURN is,pressed
# when editing the combobox.  Otherwise, if RETURN is pressed when not editing
# the combobox, then the RETURN will signal something else
###############################################################################

from PyQt5 import QtWidgets, QtCore

class CustomCombo(QtWidgets.QComboBox):

    enter_pressed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.enter_pressed.emit()
        else:
            QtWidgets.QComboBox.keyPressEvent(self, event) 
            # if the key is not return, handle normally
