# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 16:09:06 2017

@author: Chip Shand
"""
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QProgressBar
from PyQt5.QtWidgets import QMessageBox, QLabel, QSpinBox, QLineEdit
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QDesktopWidget, QFrame, QTextBrowser, QPushButton
from PyQt5.QtWidgets import QSizePolicy, QWidget, QGridLayout
from PyQt5.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QTextCursor
from PyQt5.QtGui import QPen, QDoubleValidator, QFont, QColor, QValidator
from PyQt5.QtCore import QTimer, Qt, QRect, QCoreApplication, QPoint, QEvent
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QDir, QMetaObject, QThread
import VTMLayout, VTMConfig, WSCDialog
from datetime import datetime, timedelta
from time import time
import xml.etree.ElementTree as et
import sys, os, cv2, json, subprocess, csv, glob, requests, socketio
from math import sqrt
import numpy as np
from pathlib import Path
from urllib.request import urlopen
from pymf import get_MF_devices
import queue #If this template is not loaded, pyinstaller may not be able to run the requests template after packaging
#import websocket  # Needed by socketio

class VideoCapture(QMainWindow, VTMLayout.Ui_MainWindow):
    def __init__(self, vidConfig):
        super(self.__class__, self).__init__()
        self.version = '1.2.1'
        self.setupUi(self)  # This is defined in design.py file automatically
        self.setFocusPolicy(Qt.StrongFocus)
        self.updateSoftware()
        self.vidConfig = vidConfig # a dictionary of default parameters defined in main()
        if getattr(sys, 'frozen', False): #If frozen baseline
            self.homePath = os.path.dirname(sys.executable)
        else: # Otherwise, if running as a script (e.g., within Spyder)
            self.homePath = os.path.dirname(__file__)
        self.manualFileName = os.path.join(self.homePath, 'VTMManual.htm')
        self.licenseFileName = os.path.join(self.homePath, 'VTMLicense.txt')
        self.historyFileName = os.path.join(self.homePath, 'VTM Release Notes.txt')
        self.iconFileName = os.path.join(self.homePath, 'VTMIconSmall.ico')
        self.connectedPic = os.path.join(self.homePath, 'WSCConnected64.png')
        self.disconnectedPic = os.path.join(self.homePath, 'WSCDisConnected64.png')
        self.logFileName = os.path.join(self.homePath, 'VTMLog.txt')
        self.configFileName = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\VTMConfig.json')
        self.setWindowIcon(QIcon(self.iconFileName))
        self.vidReplay.raise_()
        self.vidReplay.hide()
        self.actionExit.triggered.connect(self.closeApplication)
        self.actionOpenSavedVideo.triggered.connect(self.openVidFile)
        self.actionOpenSavedFrame.triggered.connect(self.openFrame)
        self.actionConfigurations.triggered.connect(self.showOptions)
        self.actionImport_Names.triggered.connect(self.loadSkierNames)
        self.actionClearSkierList.triggered.connect(self.clearNamesList)
        self.actionSaveGrid.triggered.connect(self.saveGrid)
        self.actionLoadGrid.triggered.connect(self.loadGrid)
        self.actionFlashMob.triggered.connect(self.enableFlashMob)        
        self.actionPeasInAPod.triggered.connect(self.enablePeasInAPod)
        self.actionMeterORama.triggered.connect(self.enableMeterORama)
        self.actionBigfoot.triggered.connect(self.enableBigfoot)
        self.actionDisableDistDisplay.triggered.connect(self.disableDistDisplay)
        self.actionConnect.triggered.connect(self.connect_to_wsc)
        self.actionDisconnect.triggered.connect(self.disconnect_from_wsc)
        self.actionShowPIN.triggered.connect(self.showPIN)
        self.actionManual.triggered.connect(self.showManual)
        self.actionLicense.triggered.connect(self.showLicense)
        self.actionHistory.triggered.connect(self.showHistory)
        self.actionAbout.triggered.connect(self.showAbout)
        self.chkboxSetup.toggled.connect(self.enterSetup)
        self.radbtnSurvey.toggled.connect(self.switchCoords)
        self.radbtnScreen.toggled.connect(self.switchCoords)
        self.btnCheck.clicked.connect(self.gridTransformationImg2Grd)
        self.chkboxVerify.toggled.connect(self.verifyTracker)
        self.btnHitRamp.clicked.connect(self.chooseCapSelectMeasure)
        self.btnCapFrame.clicked.connect(self.capFrame)
        self.btnClickLeft.clicked.connect(self.chooseWest)
        self.btnClickUp.clicked.connect(self.nudgeMarkerUp)
        self.btnClickRight.clicked.connect(self.chooseEast)
        self.btnClickDown.clicked.connect(self.nudgeMarkerDown)
        self.btnNextJump.clicked.connect(self.nextJump)
        self.btnReselectFrame.clicked.connect(self.reselectFrame)
        self.btnPVR.clicked.connect(self.pvrReplay)
        self.btnGrid.clicked.connect(self.switchGrids)
        self.chkboxShowHomoLevel.toggled.connect(self.toggleShowHomoLevel)
        self.chkboxShowGridAccuracy.toggled.connect(self.toggleShowGridAccuracy)
        self.chkboxShowDistancesMeters
        self.chkboxShowDistancesMeters.toggled.connect(self.toggleShowDistanceMeters)
        self.chkboxShowDistancesFeet.toggled.connect(self.toggleShowDistanceFeet)
        self.radbtnPass.toggled.connect(self.skierPassOrFall)
        self.radbtnFall.toggled.connect(self.skierPassOrFall)
        self.radbtnUL.toggled.connect(self.setFocusVidWIndow)
        self.radbtnUR.toggled.connect(self.setFocusVidWIndow)
        self.radbtnLR.toggled.connect(self.setFocusVidWIndow)
        self.radbtnLL.toggled.connect(self.setFocusVidWIndow)
        self.radbtnCheck.toggled.connect(self.setFocusVidWIndow)
        self.cboxSkierNames.enter_pressed.connect(self.enterSkierName)
        self.cboxSkierNames.currentIndexChanged.connect(self.updatePassNumber)
        self.chkboxShowBuoys.toggled.connect(self.showGridBuoys)
        self.vidSlider.valueChanged[int].connect(self.nudge)
        self.sliderBrightness.valueChanged[int].connect(self.adjustBrightness)
        self.sliderContrast.valueChanged[int].connect(self.adjustContrast)
        
        self.txtGrid1.hide()
        self.txtGrid2.hide()
        self.txtGrid3.hide()
        self.txtGrid4.hide()
        self.lblGrids.hide()
        self.lblGrids2.hide()
        self.lblGrids3.hide()
        self.lblGrids4.hide()
        
        self.lblWSC.setPixmap(QPixmap(self.disconnectedPic))

        font = self.cboxSkierNames.font()
        font.setPointSize(12)
        self.cboxSkierNames.lineEdit().setFont(font)
        self.txtSurveyULX.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyULY.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyURX.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyURY.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyLLX.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyLLY.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyLRX.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyLRY.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyCkX.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyCkY.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyRpX.textEdited.connect(self.getSurveyCoords)
        self.txtSurveyRpY.textEdited.connect(self.getSurveyCoords)
        self.validator = QDoubleValidator(notation=QDoubleValidator.StandardNotation)
        self.validator.setRange(-150.000, 150.000, 3)
                        
        self.grpboxLoupe.setFocusPolicy(Qt.NoFocus)
        self.radbtn2x.setFocusPolicy(Qt.NoFocus)
        self.radbtn3x.setFocusPolicy(Qt.NoFocus)
        self.radbtn4x.setFocusPolicy(Qt.NoFocus)
        self.radbtn5x.setFocusPolicy(Qt.NoFocus)
        #self.activeWindow = None          
        #self.vidWindow.setScaledContents(False)
        self.vidWindow.setAlignment(Qt.AlignCenter)
        #self.vidWindow.setMouseTracking(False)
        self.frameSetup.lower()
        self.frameVerify.lower()
        self.enableDisableFrameSetup(True)
        self.setSetupTabOrder(True)
        self.vidWindow.setStyleSheet("border-color: red; border-style: solid; border-width: 4px;")
        self.tracker = MouseTracker(self.vidWindow)        
        self.colorBuoys()
        
        # Create check arrow
        pixmapCk = QPixmap(100, 31)
        pixmapCk.fill(Qt.transparent)
        painterCk = QPainter(pixmapCk)
        painterCk.begin(self)
        painterCk.fillRect(1,0,100,31,Qt.white)
        painterCk.setPen(QPen(Qt.blue, 1, Qt.SolidLine))
        painterCk.drawLine(1, 15, 12, 21)
        painterCk.drawLine(2, 15, 13, 21)
        painterCk.drawLine(3, 15, 14, 21)
        painterCk.drawLine(4, 15, 15, 21)
        painterCk.drawLine(5, 15, 16, 21)
        painterCk.drawLine(1, 15, 12, 6)
        painterCk.drawLine(2, 15, 13, 6)
        painterCk.drawLine(3, 15, 14, 6)
        painterCk.drawLine(4, 15, 15, 6)
        painterCk.drawLine(5, 15, 16, 6)
        painterCk.setPen(QPen(Qt.blue, 5, Qt.SolidLine))
        painterCk.drawLine(7, 14, 30, 14)
        painterCk.setFont(QFont('Calibri', 10))
        painterCk.drawText(QPoint(40, 20), 'Check')
        painterCk.end()
        self.arrowCk = QLabel(self)
        self.arrowCk.setGeometry(QRect(100, 100, 60, 15))
        self.arrowCk.setPixmap(pixmapCk)
        self.arrowCk.adjustSize()
        self.arrowCk.hide()
        self.arrowCk.raise_()
        
        self.vidSlider.hide()
        self.lblSlider.hide()
        self.verifyLabel.hide()
        self.app = QApplication.instance()
        QApplication.instance().focusChanged.connect(self.focusChanged)
        self.screen = self.app.primaryScreen()
        self.rect = self.screen.availableGeometry()
        self.availableHeight = self.rect.height()
        self.availableWidth = self.rect.width()
        self.screen = QApplication.primaryScreen() #for Loupe screen capture
        self.timer = QTimer()
        self.fromLaunch = True  # Used only for first grid entry into the Log in self.getGridData()
        self.isSetup = False
        self.isSelectFrame = False
        self.isCapturing = False
        self.isMeasuring = False
        self.isMeasured = False
        self.pix = QImage()
        self.frame_height = 0
        self.frame_width = 0
        self.displayTime = 0.0
        self.secondsAfterESC = 0.5
        self.gridNum = 1                      # Stub until more gids implemented
        self.capGeom = QRect()
        #self.isCapCropped = False
        self.cap = cv2.VideoCapture()
        self.capReplay = cv2.VideoCapture()
        self.capReplayExist = False
        self.newLoad = False
        self.fromPVR = False
        self.isPVR = False
        self.pvrVid = None
        self.frameOnly = False
        self.frameAlreadySaved = False
        self.gridVisible = False
        self.distDisplayExists = False
        self.fromESC = False
        self.wscConnection = False
        self.pin = None
        self.jumpData = {}
        self.passData = {}
        self.startListQueue = queue.Queue()
        self.startListThread = QThread()
        self.accuracies = []
        self.capReplay = None
        self.capPix = None
        self.jumpWrittenToLog = False
        self.capFileName = os.path.join(self.vidConfig['saveDirectoryCaps'], 'temp.mp4')
        self.sliderContrastValueOld = 50.0
        self.alpha = 0.0     # Initialize lower end of brightness and contrast values
        self.beta = 255.0    # Initialize upper end of brightness and contrast values
        self.lblDescription = None
        self.btnHitRamp.setEnabled(False)
        self.btnCapFrame.setEnabled(False)
        self.btnNextJump.setEnabled(False)
        self.btnReselectFrame.setEnabled(False)
        self.grpboxOutcome.setEnabled(False)
        self.grpboxReride.setEnabled(False)
        '''self.radbtnFall.setEnabled(False)
        self.chkboxShowBuoys.setEnabled(False)'''
        self.chkboxShowHomoLevel.setEnabled(False)
        self.chkboxShowGridAccuracy.setEnabled(False)
        self.chkboxShowDistancesMeters.setEnabled(False)
        self.chkboxShowDistancesFeet.setEnabled(False)
        #self.btnGrid.setEnabled(False)
        self.btnPVR.hide()
        self.gc = {'screenUL': [0.0,0.0], 'screenUR': [0.0,0.0], 'screenLL': [0.0,0.0], 'screenLR': [0.0,0.0], 'screenCk': [0.0,0.0], \
                   'surveyUL': [0.0,0.0], 'surveyUR': [0.0,0.0], 'surveyLL': [0.0,0.0], 'surveyLR': [0.0,0.0], 'surveyCk': [0.0,0.0], \
                   'surveyRp': [0.0,0.0]}
        self.gc1 = {'screenUL': [0.0,0.0], 'screenUR': [0.0,0.0], 'screenLL': [0.0,0.0], 'screenLR': [0.0,0.0], 'screenCk': [0.0,0.0], \
                   'surveyUL': [0.0,0.0], 'surveyUR': [0.0,0.0], 'surveyLL': [0.0,0.0], 'surveyLR': [0.0,0.0], 'surveyCk': [0.0,0.0], \
                   'surveyRp': [0.0,0.0]}
        self.gc2 = {'screenUL': [0.0,0.0], 'screenUR': [0.0,0.0], 'screenLL': [0.0,0.0], 'screenLR': [0.0,0.0], 'screenCk': [0.0,0.0], \
                   'surveyUL': [0.0,0.0], 'surveyUR': [0.0,0.0], 'surveyLL': [0.0,0.0], 'surveyLR': [0.0,0.0], 'surveyCk': [0.0,0.0], \
                   'surveyRp': [0.0,0.0]}
        self.gc3 = {'screenUL': [0.0,0.0], 'screenUR': [0.0,0.0], 'screenLL': [0.0,0.0], 'screenLR': [0.0,0.0], 'screenCk': [0.0,0.0], \
                   'surveyUL': [0.0,0.0], 'surveyUR': [0.0,0.0], 'surveyLL': [0.0,0.0], 'surveyLR': [0.0,0.0], 'surveyCk': [0.0,0.0], \
                   'surveyRp': [0.0,0.0]}
        self.gc4 = {'screenUL': [0.0,0.0], 'screenUR': [0.0,0.0], 'screenLL': [0.0,0.0], 'screenLR': [0.0,0.0], 'screenCk': [0.0,0.0], \
                   'surveyUL': [0.0,0.0], 'surveyUR': [0.0,0.0], 'surveyLL': [0.0,0.0], 'surveyLR': [0.0,0.0], 'surveyCk': [0.0,0.0], \
                   'surveyRp': [0.0,0.0]}
        self.img2grd = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.grd2img = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if os.path.isfile(self.vidConfig['gridFileName1']) == True:
            self.txtGrid1.setText(vidConfig['gridDescription1'])
        if os.path.isfile(self.vidConfig['gridFileName2']) == True:
            self.txtGrid2.setText(vidConfig['gridDescription2'])
        if os.path.isfile(self.vidConfig['gridFileName3']) == True:
            self.txtGrid3.setText(vidConfig['gridDescription3'])
        if os.path.isfile(self.vidConfig['gridFileName4']) == True:
            self.txtGrid4.setText(vidConfig['gridDescription4'])
        #self.vidWindow.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Ignored ) 
        filename = os.path.join(os.path.expanduser('~'), 'Documents\\VTM\\VTM Master Names List.txt')
        self.jumps = []
        self.skierNames = []
        self.gridDescription = ''
        self.gridFileName = ''
        if getattr(sys, 'frozen', False): #If frozen with cx_Freeze
            self.workPath = os.path.dirname(sys.executable)
        else: # Otherwise, if running as a script (e.g., within Spyder)
            self.workPath = os.path.dirname(__file__)
        with open(filename, 'r') as f:
            name = f.readline()   # Get the first name in the Master Names List file
            while name != "":
                name = name.strip('\n')
                self.skierNames.append(name)
                self.cboxSkierNames.addItem(name)
                name = f.readline()   #  Do it again until all the names are read
        if len(self.skierNames) == 0:
            self.skierNames = ['Jump Skier']
            self.cboxSkierNames.addItem('Jump Skier') 
        
        # First, check to make sure the primary screen is a minimum of 1920x1080
        d = QDesktopWidget()
        geom = d.screenGeometry(-1)
        if geom.width() < 1920 or geom.height() < 1080:
            message = 'VTM requires a screen resolution of 1920x1080 or better. \n'
            message += 'Your primary screen resolution is '+ str(geom.width()) + ' x ' + str(geom.height()) + '.\n\n'
            message += 'You may run VTM on this computer if you do the following:\n\n'
            message += '1. Connect an external monitor to your computer via HDMI or DisplayPort\n\n'
            message += '2. Configure your computer to recognize the external monitor as an "extended" display\n\n'
            message += '3. Click "OK" or exit out of the Configuration window and then "Restore Down" or "unmaximize" the main window\n\n'
            message += '4. Drag the Video Tape Measure main window into the extended screen and then maximize it\n'
            msgBox = QMessageBox()
            msgBox.information(self, 'Needs High Resolution Display', message, QMessageBox.Ok)
        
        self.showMaximized()
        self.showOptions()
        self.initializeVideoStream()
        # Load Grid 1
        if self.vidConfig['gridFileName1'] != '':
            self.getGridData(self.vidConfig['gridFileName1'], 1, False)
        if self.vidConfig['pvr'] == True:
            self.btnPVR.show()
            self.startPVR()
        else:
            self.btnPVR.hide()

    def gatherStartList(self, data):
        self.startListQueue.put(data)       
        self.startListThread.started.connect(self.buildStartList)
        self.startListThread.start()
            
    def buildStartList(self):
        while self.startListQueue.empty() == False:
            data = self.startListQueue.get()
            data = json.loads(data)
            for athlete in data['startlist_athletes']:
                name = athlete['athleteName'] + ' ' + athlete['athleteDivision']
                self.updateSkierNames(name = name, appendFlag = True)
        self.startListThread.quit()

    def showPIN(self):
        if self.pin != None:
            message = 'The Daily PIN is ' + self.pin
        else:
            message = 'You are not connected to WaterSkiConnect'
        QMessageBox.information(self, 'Daily PIN', message, QMessageBox.Ok)

    def connect_to_wsc(self):
        #self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.sio = socketio.Client()
        self.ioConnect = WSC_Connect_Disconnect(self, self.sio)
        # Start listening for connect_confirm
        self.ioConnect.connect_to_waterskiconnect()
        if self.wscConnection == True:
            self.lblWSC.setPixmap(QPixmap(self.connectedPic))
            self.wscConnectionMessages()
        # Start listening for Pass Data
        self.ioPass = WSC_Pass_Data(self, self.sio)
        # Start listener for the Start List
        self.ioStartList = WSC_Start_List(self, self.sio)
        
    def disconnect_from_wsc(self):
        self.ioConnect.disconnect_from_waterskiconnect()
        if self.wscConnection == False:
            self.lblWSC.setPixmap(QPixmap(self.disconnectedPic))
            self.wscConnectionMessages()

    def wscConnectionMessages(self):
        if self.wscConnection == True:
            QMessageBox.information(self,'Connected', 'Connected to WaterSkiConnect!', QMessageBox.Ok)
        else:
            QMessageBox.information(self,'Disconnected', 'Disconnected from WaterSkiConnect.', QMessageBox.Ok)
            
    def switchCoords(self):
        if self.radbtnSurvey.isChecked() == True:  # Show survey coordinate in Setup frame
            self.txtSurveyULX.setStyleSheet('background-color: white; color: black')
            self.txtSurveyULY.setStyleSheet('background-color: white; color: black')
            self.txtSurveyURX.setStyleSheet('background-color: white; color: black')
            self.txtSurveyURY.setStyleSheet('background-color: white; color: black')
            self.txtSurveyLLX.setStyleSheet('background-color: white; color: black')
            self.txtSurveyLLY.setStyleSheet('background-color: white; color: black')
            self.txtSurveyLRX.setStyleSheet('background-color: white; color: black')
            self.txtSurveyLRY.setStyleSheet('background-color: white; color: black')
            self.txtSurveyCkX.setStyleSheet('background-color: white; color: black')
            self.txtSurveyCkY.setStyleSheet('background-color: white; color: black')
            self.txtSurveyULX.setText(str(self.gc['surveyUL'][0]))
            self.txtSurveyULY.setText(str(self.gc['surveyUL'][1]))
            self.txtSurveyURX.setText(str(self.gc['surveyUR'][0]))
            self.txtSurveyURY.setText(str(self.gc['surveyUR'][1]))
            self.txtSurveyLLX.setText(str(self.gc['surveyLL'][0]))
            self.txtSurveyLLY.setText(str(self.gc['surveyLL'][1]))
            self.txtSurveyLRX.setText(str(self.gc['surveyLR'][0]))
            self.txtSurveyLRY.setText(str(self.gc['surveyLR'][1]))
            self.txtSurveyCkX.setText(str(self.gc['surveyCk'][0]))
            self.txtSurveyCkY.setText(str(self.gc['surveyCk'][1]))         
        else:  # Show screen coordinates in Setup frame
            self.txtSurveyULX.setStyleSheet('background-color: black; color: white')
            self.txtSurveyULY.setStyleSheet('background-color: black; color: white')
            self.txtSurveyURX.setStyleSheet('background-color: black; color: white')
            self.txtSurveyURY.setStyleSheet('background-color: black; color: white')
            self.txtSurveyLLX.setStyleSheet('background-color: black; color: white')
            self.txtSurveyLLY.setStyleSheet('background-color: black; color: white')
            self.txtSurveyLRX.setStyleSheet('background-color: black; color: white')
            self.txtSurveyLRY.setStyleSheet('background-color: black; color: white')
            self.txtSurveyCkX.setStyleSheet('background-color: black; color: white')
            self.txtSurveyCkY.setStyleSheet('background-color: black; color: white')
            self.txtSurveyULX.setText(str(self.gc['screenUL'][0]))
            self.txtSurveyULY.setText(str(self.gc['screenUL'][1]))
            self.txtSurveyURX.setText(str(self.gc['screenUR'][0]))
            self.txtSurveyURY.setText(str(self.gc['screenUR'][1]))
            self.txtSurveyLLX.setText(str(self.gc['screenLL'][0]))
            self.txtSurveyLLY.setText(str(self.gc['screenLL'][1]))
            self.txtSurveyLRX.setText(str(self.gc['screenLR'][0]))
            self.txtSurveyLRY.setText(str(self.gc['screenLR'][1]))
            self.txtSurveyCkX.setText(str(self.gc['screenCk'][0]))
            self.txtSurveyCkY.setText(str(self.gc['screenCk'][1]))

    def enableFlashMob(self):
        self.flasher = True
        self.displayChoice = 'flashmob'
        if self.distDisplayExists == True:
            self.disableDistDisplay()            
        self.enableDistDisplay('flashmob')
        
    def enablePeasInAPod(self):
        self.flasher = False
        self.displayChoice = 'peasinapod'
        if self.distDisplayExists == True:
            self.disableDistDisplay()         
        self.enableDistDisplay('peasinapod')

    def enableMeterORama(self):
        self.flasher = True
        self.displayChoice = 'meterorama'
        if self.distDisplayExists == True:
            self.disableDistDisplay()         
        self.enableDistDisplay('meterorama')
        
    def enableBigfoot(self):
        self.flasher = True
        self.displayChoice = 'bigfoot'
        if self.distDisplayExists == True:
            self.disableDistDisplay()         
        self.enableDistDisplay('bigfoot')

    def enableDistDisplay(self, choice):
        if self.distDisplayExists == False:
            name = self.cboxSkierNames.currentText()
            distM = self.txtDistMeters.text()
            distF = self.txtDistFeet.text()
            self.distDisplayExists = True
            if self.flasher == True:
                self.distDisplay = DistanceDisplay()
                self.distDisplay.updateDisplay(name, distM, distF, choice)
            else:
                self.distDisplay = PeasInAPodDisplay()
                self.distDisplay.updateDisplay(name, distM, distF)
            self.distDisplay.showDisplay()
        
    def disableDistDisplay(self):
        if self.distDisplayExists == True:
            self.distDisplayExists = False
            self.distDisplay.closeDisplay()        

    def internet_on(self):
        # If can't connect to Google within one second, assume no internet connection
        try:
            urlopen('https://8.8.8.8', timeout=1)
            return True
        except: 
            return False

    def updateSoftware(self):
        # First, check if there is an updated version of the software
        if self.internet_on() == True:
            try:
                url = 'https://www.dropbox.com/sh/r3giekcdtqs03ug/AACb6qbwKlY0j4q8dGDkAqcba?dl=0/2/files/list_folder'
                u = urlopen(url)
                r = u.read().decode('utf-8')
                x = r.find('VTMSetupV')
                latestFileName = r[x:x+20]
                currentMajor = int(self.version[0])
                currentMinor = int(self.version[2])
                currentMicro = int(self.version[4])
                newMajor = int(latestFileName[11])
                newMinor = int(latestFileName[13])
                newMicro = int(latestFileName[15])
                current = currentMajor*100 + currentMinor*10 + currentMicro
                latest = newMajor*100 + newMinor*10 + newMicro    
                if latest > current:
                    currentVersion = str(currentMajor) + '.'+str(currentMinor) + '.'+str(currentMicro)
                    latestVersion = str(newMajor) + '.'+str(newMinor) + '.'+str(newMicro)
                    message = 'You are running version ' + currentVersion + '.  Version '
                    message += latestVersion + ' is available.   \n\nDo you want to download it?'
                    reply = QMessageBox.question(self,'Update Available', message, QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        latestLink = r[x-69:x+20] + '?dl=1'
                        w = DownloadWidget(latestLink, os.path.join(os.path.expanduser('~'),'Downloads\\')   + latestFileName)
                        w.show()
                        w.exec_()
    
                        message = 'Your downoad has completed.  Please follow these steps:\n'
                        message += '    1.  Close this program \n'
                        message += '    2.  Uninstall the current version of Video Tape Measure\n'
                        message += '    3.  Navigate to your Downloads directory and execute the file "' + latestFileName + '" to install the updated version'                   
                        QMessageBox.information(self, 'Download Complete!', message, QMessageBox.Ok)
            except:
                pass

    def switchGrids(self):
        # Step 1:  Set the new grid number
        currentGridNum = int(self.btnGrid.text()[-1:])
        if currentGridNum > self.vidConfig['numGrids']:  
            currentGridNum = self.vidConfig['numGrids']
        if currentGridNum == self.vidConfig['numGrids']:
            nextGridNum = 1
        else:
            nextGridNum = currentGridNum + 1
            
        # Step 2: Get the grid data
        if nextGridNum == 1:
            self.getGridData(self.vidConfig['gridFileName1'], 1, False)
        elif nextGridNum == 2:
            self.getGridData(self.vidConfig['gridFileName2'], 2, False)
        elif nextGridNum == 3:
            self.getGridData(self.vidConfig['gridFileName3'], 3, False)     
        else:
            self.getGridData(self.vidConfig['gridFileName4'], 4, False)
        self.btnGrid.setText('Grid  ' + str(nextGridNum))
        if self.txtDistMeters.text() != '':  # Check if the distance displays require update
            self.getDistance()            
        self.writeToLog('Switch')

    def pvrReplay(self):
        endTime = datetime.now()
        # Stop the current recording and get its file name and start time before the object values are overwritten
        self.pvrVid.release()
        infile = self.pvrFileName
        startTime = self.pvrStartTime

        # Start the next recording
        self.startPVR()

        pvrVidDuration = endTime - startTime
        if pvrVidDuration > timedelta(seconds=120):
            # PVR video is greater than 120 seconds.  Start time is 2 minutes prior to the end and duration is 2 minutes
            less2min = pvrVidDuration - timedelta(seconds=120)
            secs = less2min.total_seconds()
            hours = int(secs/3600.0)
            minutes = int((secs  - hours * 3600.0) / 60)
            seconds = int(secs - (hours * 3600 + minutes * 60))
            start = '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)
            duration = '00:02:00'
        else:
            # PVR video is less than 2 minutes.  Start time is the beginning and duration is length of the video
            secs = (endTime - startTime).total_seconds()
            hours = int(secs / 3600.0)
            minutes = int(secs / 60.0)
            seconds = secs - minutes * 60
            start = '00:00:00'
            duration = '{:02d}:{:02d}:{:5.3f}'.format(hours, minutes, seconds)
        ffmpegLoc = os.path.join(self.homePath, 'ffmpeg.exe') 
        pipe = subprocess.Popen([ffmpegLoc,"-v", "quiet", "-y", "-i", infile, "-vcodec", "copy", "-acodec", "copy", "-ss", start, "-t", duration, "-sn", self.capFileName])
        pipe.wait()
        self.fromPVR = True
        # Hide the jump marker
        self.markerJmp.hide()
        self.markerJmp.lower()
        self.measureMode()

    def startPVR(self):
        self.pvrStartTime = datetime.now()
        fname = datetime.strftime(self.pvrStartTime, '%Y%m%d_%H-%M-%S') + '.mp4'
        self.pvrFileName = os.path.join(self.vidConfig['pvrDirectory'], fname)
        fourcc = cv2.VideoWriter_fourcc('h','2','6','4')
        self.pvrVid = cv2.VideoWriter(self.pvrFileName, fourcc, self.vidConfig['framesPerSec'], (self.frame_width, self.frame_height))
        self.isPVR = True
        
    def focusChanged(self):
        if self.chkboxSetup.isChecked == True:
            self.btnHitRamp.setDefault(False)
            self.btnHitRamp.setEnabled(False)
            self.btnHitRamp.setStyleSheet('background-color: light gray; color gray, border: 1px gray')
            self.enterSetup()
        else:        
            if self.btnHitRamp.hasFocus() == True:      
                if self.btnHitRamp.text() == 'Skier Hits Ramp':
                    self.btnHitRamp.setStyleSheet('background-color: #00ff00; color: black; border-style: inset; border-width: 4px;')
                elif self.btnHitRamp.text() == 'Record Jump':
                    self.btnHitRamp.setStyleSheet('background-color: blue; border: 4px solid black; color: white')
            else:
                #self.btnHitRamp.setFocus(True)
                if self.btnHitRamp.text() == 'Skier Hits Ramp':
                    self.btnHitRamp.setStyleSheet('background-color: None; border-width: 1px;')
                elif self.btnHitRamp.text() == 'Record Jump':
                    self.btnHitRamp.setStyleSheet('background-color: blue; border: 1px solid black; color: white')

    def writeToLog(self, what, **kwargs):
        try:
            date = datetime.now().strftime('%Y-%m-%d')
            fileName = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\VTMLog-' + date + '.txt')
            try:
                f = open(fileName, 'a')
            except:
                message = 'Could not open log file \'' + fileName + 'for writing.'
                QMessageBox.warning(self, 'Cannot Open Log File', message, QMessageBox.Ok)
            when = datetime.now().strftime('%Y-%m-%dT%H:%M:%S - ')
            if what == 'VideoStream':
                print('\n' + when + 'Video stream initalized - capturing at {}x{} resolution.'.format(self.frame_width, self.frame_height), file = f)
            if what == 'Switch':
                print('\n' + when + 'Grid was switched to Grid Number ' + str(self.gridNum), file = f)
            if what == 'Setup':            
                print('\n' + when + 'Grid Number ' + str(self.gridNum) +  ' was successfully set up.', file = f)
            if what == 'Switch' or what == 'Setup':
                print('\n    Grid Description: ' + self.gridDescription + '\n', file = f)
                print('    Upper Left  (X, Y) Screen: ({:4d}, {:4d})'.format(self.gc['screenUL'][0], self.gc['screenUL'][1]), file = f)
                print('    Upper Left  (X, Y) Survey: ({:5.2f}, {:5.2f})\n'.format(self.gc['surveyUL'][0], self.gc['surveyUL'][1]), file = f)
                print('    Upper Right (X, Y) Screen: ({:4d}, {:4d})'.format(self.gc['screenUR'][0], self.gc['screenUR'][1]), file = f)
                print('    Upper Right (X, Y) Survey: ({:5.2f}, {:5.2f})\n'.format(self.gc['surveyUR'][0], self.gc['surveyUR'][1]), file = f)
                print('    Lower Left  (X, Y) Screen: ({:4d}, {:4d})'.format(self.gc['screenLL'][0], self.gc['screenLL'][1]), file = f)
                print('    Lower Left  (X, Y) Survey: ({:5.2f}, {:5.2f})\n'.format(self.gc['surveyLL'][0], self.gc['surveyLL'][1]), file = f)
                print('    Lower Right (X, Y) Screen: ({:4d}, {:4d})'.format(self.gc['screenLR'][0], self.gc['screenLR'][1]), file = f)
                print('    Lower Right (X, Y) Survey: ({:5.2f}, {:5.2f})\n'.format(self.gc['surveyLR'][0], self.gc['surveyLR'][1]), file = f)
                print('    Check Buoy  (X, Y) Screen: ({:4d}, {:4d})'.format(self.gc['screenCk'][0], self.gc['screenCk'][1]), file = f)
                print('    Check Buoy  (X, Y) Survey: ({:5.2f}, {:5.2f})\n'.format(self.gc['surveyCk'][0], self.gc['surveyCk'][1]), file = f)
                print('    Jump Ramp   (X, Y) Survey: ({:5.2f}, {:5.2f})\n'.format(self.gc['surveyRp'][0], self.gc['surveyRp'][1]), file = f)
                print('    Image-to-Ground transformation parameters:', file = f)
                print('    a = {:18.14f}'.format(self.img2grd[0]), file = f)
                print('    b = {:18.14f}'.format(self.img2grd[1]), file = f)
                print('    c = {:18.14f}'.format(self.img2grd[2]), file = f)
                print('    d = {:18.14f}'.format(self.img2grd[3]), file = f)
                print('    e = {:18.14f}'.format(self.img2grd[4]), file = f)
                print('    f = {:18.14f}'.format(self.img2grd[5]), file = f)
                print('    g = {:18.14f}'.format(self.img2grd[6]), file = f)
                print('    h = {:18.14f}'.format(self.img2grd[7]), file = f)
            if what == 'Jump':
                print('\n' + when + 'Skier: ' + str(self.cboxSkierNames.currentText()) + ', Jump:{:2d},  Round: {:1d}'.
                      format(self.spinBoxPass.value(), self.spinBoxRound.value()), file = f)
                if kwargs['jumpOK'] == True and kwargs['noReride'] == True:
                    if self.txtDistMeters.text() != '':
                        print('    JUMP and NO RERIDE:  Meters = {:4.1f},  Feet = {:3d},  Ground XY = ({:6.2f}, {:6.2f}),  Screen XY = ({:4d}, {:4d})'.
                              format(float(self.txtDistMeters.text()), int(self.txtDistFeet.text()),  self.jumpGroundX, self.jumpGroundY, 
                                     self.jumpScreenx, self.jumpScreeny), file = f)
                if kwargs['jumpOK'] == True and kwargs['mandatory'] == True:
                    if self.txtDistMeters.text() != '':
                        print('    JUMP and MANDATORY RERIDE:  Meters = {:4.1f},  Feet = {:3d},  Ground XY = ({:6.2f}, {:6.2f}),  Screen XY = ({:4d}, {:4d})'.
                              format(float(self.txtDistMeters.text()), int(self.txtDistFeet.text()),  self.jumpGroundX, self.jumpGroundY, 
                                     self.jumpScreenx, self.jumpScreeny), file = f)
                    else:
                        print('NO JUMP and MANDATORY RERIDE', file = f)
                if kwargs['jumpOK'] == True and kwargs['optional'] == True:
                    if self.txtDistMeters.text() != '':
                        print('    JUMP and OPTIONAL RERIDE:  Meters = {:4.1f},  Feet = {:3d},  Ground XY = ({:6.2f}, {:6.2f}),  Screen XY = ({:4d}, {:4d})'.
                              format(float(self.txtDistMeters.text()), int(self.txtDistFeet.text()),  self.jumpGroundX, self.jumpGroundY, 
                                     self.jumpScreenx, self.jumpScreeny), file = f)
                    else:
                        print('OPTIONAL RERIDE', file = f)
                if kwargs['fall'] == True and kwargs['noReride'] == True:
                    if self.txtDistMeters.text() != '':
                        print('    FALL and NO RERIDE:  Meters = {:4.1f},  Feet = {:3d},  Ground XY = ({:6.2f}, {:6.2f}),  Screen XY = ({:4d}, {:4d})'.
                              format(float(self.txtDistMeters.text()), int(self.txtDistFeet.text()),  self.jumpGroundX, self.jumpGroundY, 
                                     self.jumpScreenx, self.jumpScreeny), file = f)
                    else:
                        print('FALL and NO RERIDE', file = f)
                if kwargs['fall'] == True and kwargs['mandatory'] == True:
                    if self.txtDistMeters.text() != '':
                        print('    FALL and MANDATORY RERIDE:  Meters = {:4.1f},  Feet = {:3d},  Ground XY = ({:6.2f}, {:6.2f}),  Screen XY = ({:4d}, {:4d})'.
                              format(float(self.txtDistMeters.text()), int(self.txtDistFeet.text()),  self.jumpGroundX, self.jumpGroundY, 
                                     self.jumpScreenx, self.jumpScreeny), file = f)
                    else:
                        print('FALL and MANDATORY RERIDE', file = f)
                if kwargs['fall'] == True and kwargs['optional'] == True:
                    if self.txtDistMeters.text() != '':
                        print('    FALL and OPTIONAL RERIDE:  Meters = {:4.1f},  Feet = {:3d},  Ground XY = ({:6.2f}, {:6.2f}),  Screen XY = ({:4d}, {:4d})'.
                              format(float(self.txtDistMeters.text()), int(self.txtDistFeet.text()),  self.jumpGroundX, self.jumpGroundY, 
                                     self.jumpScreenx, self.jumpScreeny), file = f)
                    else:
                        print('FALL and OPTIONAL RERIDE', file = f)
                if kwargs['passed'] == True and kwargs['noReride'] == True:
                    print('    PASS and NO RERIDE', file = f)
                if kwargs['passed'] == True and kwargs['mandatory'] == True:
                    print('    PASS and MANDATORY RERIDE', file = f)                
                if kwargs['passed'] == True and kwargs['optional'] == True:
                    print('    PASS and OPTIONAL RERIDE', file = f)
            if what == 'Verify':
                x = int(self.txtVerifyScreenX.text())
                y = int(self.txtVerifyScreenY.text())
                X = float(self.txtImg2GrdX.text())
                Y = float(self.txtImg2GrdY.text())
                adder = self.getJumpDistanceAdder()
                meters = round(sqrt(X**2 + Y**2) + adder, 2)
                feet = int(round(meters / 0.3048, 0))
                print('\n' + when + 'Setup Verified', file = f)
                print('    Screen (x,y):  ({:4d}, {:4d})'.format(x, y), file = f)
                print('    Ground (X,Y):  ({:0.2f}, {:0.2f})'.format(X, Y), file = f)
                print('    Distance:   {:0.1f} meters or {:0d} Feet'.format(meters, feet), file = f)
            if what == 'Discipline':
                print('\n' + when + what + ' changed from "' + kwargs['old'] + '" to "' + kwargs['new'] + '".', file = f)
            if what == 'WaterSkiConnect':
                action, sid, confirmData = kwargs['wsc']

                if action == 'connected':
                    print('\n' + when + ' Connected to WaterSkiConnect', file = f)
                    print('    {:16}{}'.format('Session ID', sid), file = f)
                    print('    {:16}{}'.format('Tournament ID', confirmData['eventId']), file = f)
                    print('    {:16}{}'.format('Sub ID', confirmData['eventSubId']), file = f)
                    print('    {:16}{}'.format('Daily PIN', confirmData['pin']), file = f)
                else:
                    print('\n' + when + ' Disconnected from WaterSkiConnect', file = f)
            f.close()
        except:
            pass

    def adjustBrightness(self, value):
        diff = self.beta - self.alpha
        self.alpha = value * 2.0
        self.beta = self.alpha + diff

    def adjustContrast(self, value):
        diffCurrent = self.beta - self.alpha
        diffNew = value / 50.0 * 255
        move = (diffNew - diffCurrent) / 2.0
        self.alpha -= move
        self.beta += move

    def setFocusVidWIndow(self):
        self.vidWindow.setFocus()

    def colorBuoys(self):
        pixmap = QPixmap(39, 39)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(self.vidConfig['gridMarkColor']), 3, Qt.SolidLine))
        painter.drawEllipse(pixmap.rect().adjusted(3, 3, -3, -3))
        painter.drawPoint(pixmap.rect().center())        
        painter.end()
        self.markerUL = QLabel(self)
        self.markerUL.setPixmap(pixmap)
        self.markerUL.adjustSize()
        self.markerUL.hide()
        self.markerUL.raise_()
        self.markerUR = QLabel(self)
        self.markerUR.setPixmap(pixmap)
        self.markerUR.adjustSize()
        self.markerUR.hide()
        self.markerUR.raise_()
        self.markerLL = QLabel(self)
        self.markerLL.setPixmap(pixmap)
        self.markerLL.adjustSize()
        self.markerLL.hide()
        self.markerLL.raise_()
        self.markerLR = QLabel(self)
        self.markerLR.setPixmap(pixmap)
        self.markerLR.adjustSize()
        self.markerLR.hide()
        self.markerLR.raise_()
        self.markerCk = QLabel(self)
        self.markerCk.setPixmap(pixmap)
        self.markerCk.adjustSize()
        self.markerCk.hide()
        self.markerCk.raise_()
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(self.vidConfig['jumpMarkColor']), 3, Qt.SolidLine))
        painter.drawEllipse(pixmap.rect().adjusted(3, 3, -3, -3))
        painter.drawPoint(pixmap.rect().center())        
        painter.end()
        self.markerJmp = QLabel(self)
        self.markerJmp.setPixmap(pixmap)
        self.markerJmp.adjustSize()
        self.markerJmp.hide()
        self.markerJmp.raise_()              

    def showGridBuoys(self):
        if self.chkboxShowBuoys.isChecked() == True:
            pos = QPoint(self.gc['screenUL'][0], self.gc['screenUL'][1])
            self.markerUL.move(pos - self.markerUL.rect().center())
            self.markerUL.show()
            pos = QPoint(self.gc['screenUR'][0], self.gc['screenUR'][1])
            self.markerUR.move(pos - self.markerUR.rect().center())
            self.markerUR.show()
            pos = QPoint(self.gc['screenLL'][0], self.gc['screenLL'][1])
            self.markerLL.move(pos - self.markerLL.rect().center())
            self.markerLL.show()
            pos = QPoint(self.gc['screenLR'][0], self.gc['screenLR'][1])
            self.markerLR.move(pos - self.markerLR.rect().center())
            self.markerLR.show()
            pos = QPoint(self.gc['screenCk'][0], self.gc['screenCk'][1])
            self.markerCk.move(pos - self.markerCk.rect().center())
            self.markerCk.show()
            self.gridVisible = True
        else:
            self.markerUL.hide()
            self.markerUR.hide()
            self.markerLL.hide()
            self.markerLR.hide()
            self.markerCk.hide()
            self.gridVisible = False

    def showOptions(self):
        gridMarker = self.vidConfig['gridMarkColor']
        jumpMarker = self.vidConfig['jumpMarkColor']
        camID = self.vidConfig['cameraID']
        pvr = self.vidConfig['pvr']
        frameRate = self.vidConfig['framesPerSec']
        discipline = self.vidConfig['discipline']
        self.options = vidOptions(self.vidConfig)
        self.options.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.options.exec_()
        
        # Update configuration settings
        configDir = os.path.join(os.path.expanduser('~'),'Documents\\VTM')
        configFileName =  os.path.join(configDir,'VTMConfig.json')
        with open(configFileName, 'rt') as f:
            a = f.read()
        self.vidConfig = json.loads(a)            

        # Check if color of buoy or jump markers changed
        if gridMarker != self.vidConfig['gridMarkColor'] or jumpMarker != self.vidConfig['jumpMarkColor']:
            pixmap = QPixmap(39, 39)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor(self.vidConfig['gridMarkColor']), 3, Qt.SolidLine))
            painter.drawEllipse(pixmap.rect().adjusted(3, 3, -3, -3))
            painter.drawPoint(pixmap.rect().center())        
            painter.end()
            self.markerUL.setPixmap(pixmap)
            self.markerUR.setPixmap(pixmap)
            self.markerLL.setPixmap(pixmap)
            self.markerLR.setPixmap(pixmap)
            self.markerCk.setPixmap(pixmap)
            pixmap = QPixmap(39, 39)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor(self.vidConfig['jumpMarkColor']), 3, Qt.SolidLine))
            painter.drawEllipse(pixmap.rect().adjusted(3, 3, -3, -3))
            painter.drawPoint(pixmap.rect().center())        
            painter.end()
            self.markerJmp.setPixmap(pixmap)
        if self.vidConfig['pvr'] == True:
            self.btnPVR.show()
            if pvr == False: # If the PVR was changed from False to True, then start PVR                
                self.startPVR()                
        else:
            if pvr == True: # If the PVR was changed from True to False, then stop the PVR
                self.btnPVR.hide()
                if self.pvrVid != None:
                    self.pvrVid.release()
        if frameRate != self.vidConfig['framesPerSec']:  # If the frame rate changes, stop the existing capture and restart it with the new frame rate
            self.cap.release()
            self.initializeVideoStream()
            if self.isPVR == True:  # Need to also restart the PVR with the new frame rate
                self.pvrVid.release()
                self.startPVR()              
        if camID != self.vidConfig['cameraID']:
            self.initializeVideoStream()
            if self.isPVR == True:  # Need to also restart the PVR with the new frame rate
                self.pvrVid.release()
                self.startPVR()
        # Hide any unneeded grid descriptions
        if self.vidConfig['numGrids'] == 1:
            self.txtGrid1.show()
            self.txtGrid2.hide()
            self.txtGrid3.hide()
            self.txtGrid4.hide()
            self.lblGrids.show()
            self.lblGrids2.hide()
            self.lblGrids3.hide()
            self.lblGrids4.hide()
        elif self.vidConfig['numGrids'] == 2:
            self.txtGrid1.show()
            self.txtGrid2.show()
            self.txtGrid3.hide()
            self.txtGrid4.hide()
            self.lblGrids.show()
            self.lblGrids2.show()
            self.lblGrids3.hide()
            self.lblGrids4.hide()            
        elif self.vidConfig['numGrids'] == 3:
            self.txtGrid1.show()
            self.txtGrid2.show()
            self.txtGrid3.show()
            self.txtGrid4.hide()
            self.lblGrids.show()
            self.lblGrids2.show()
            self.lblGrids3.show()
            self.lblGrids4.hide()
        else:
            self.txtGrid1.show()
            self.txtGrid2.show()
            self.txtGrid3.show()
            self.txtGrid4.show()
            self.lblGrids.show()
            self.lblGrids2.show()
            self.lblGrids3.show()
            self.lblGrids4.show()
        if discipline != self.vidConfig['discipline']:
            if self.txtDistMeters.text() != '':
                #If the discipline changed and a distance is displayed, change the distance displayed
                if discipline == 'waterski':
                    baseMeters = self.distMeters - 2.1
                elif discipline == 'sitski':
                    baseMeters = self.distMeters - 1.9
                else:
                    baseMeters = self.distMeters
                if self.vidConfig['discipline'] == 'waterski':
                    self.distMeters = baseMeters + 2.1
                elif self.vidConfig['discipline'] == 'sitski':
                    self.distMeters = baseMeters + 1.9
                else:
                    self.distMeters = baseMeters
                self.distFeet = self.distMeters / 0.3048
                self.txtDistMeters.setText('{:0.1f}'.format(self.distMeters))        
                self.txtDistFeet.setText('{:0.0f}'.format(self.distFeet))
                # Update the external Distance Display if it is enabled
                if self.distDisplayExists == True:
                    if self.flasher == True:
                        self.distDisplay.updateDisplay(self.cboxSkierNames.currentText(),self.txtDistMeters.text(),self.txtDistFeet.text(), self.displayChoice)
                        self.distDisplay.setColor('yellow')
                    else:
                        self.distDisplay.updateDisplay('', '', '')
                        self.distDisplay.setColor('yellow')
            # Write to log that the discipline changed
            self.writeToLog('Discipline', old=discipline, new=self.vidConfig['discipline'])
        if self.chkboxShowHomoLevel.isChecked() == True or self.chkboxShowGridAccuracy.isChecked() == True or self.chkboxShowDistancesMeters.isChecked() == True or self.chkboxShowDistancesFeet.isChecked() == True:
            self.showHomologationGrid()

    def skierPassOrFall(self):
        if self.radbtnPass.isChecked() == True:
            self.radbtnFall.setChecked(False)
        if self.radbtnFall.isChecked() == True:
            self.radbtnPass.setChecked(False) 
            if self.distDisplayExists == True:
                self.distDisplay.setColor('yellow')

    def makeFileName(self, path, ext):
        # makes the file name without extension for saving video captures or frames
        date = datetime.today().strftime('%Y%m%d')
        a = str(self.cboxSkierNames.currentText())
        b = a.replace(' ','')
        c = b.replace(',','')
        skierRound = 'R' + str(self.spinBoxRound.value())
        skierJump = 'J' + str(self.spinBoxPass.value())
        filename = path + '\\' + date + '_' + c + skierRound + skierJump + ext
        return filename
    
    def msgFileExists(self, fname):
        msgBox = QMessageBox()
        msgBox.setWindowTitle('Select New Round?')
        message = 'Cannot save file "' + fname + '" because a file with the same name\n' 
        message += 'already exists. This might happen because the next Round was not selected.\n'
        message += 'Please choose what you want to do.'
        msgBox.setText(message)
        '''font = QFont()
        font.setPointSize(10)
        button = QPushButton()
        button.setFont(font)
        msgBox.addButton(QPushButton('Overwrite\nexisting file'), QMessageBox.YesRole)
        msgBox.addButton(QPushButton('Don\'t Save and\nContinue With Next Jump'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Don\'t Save. I Want\nto Fix the Problem.'), QMessageBox.RejectRole)'''
        msgBox.addButton(QPushButton('Overwrite\nexisting file'), QMessageBox.YesRole)
        msgBox.addButton(QPushButton('Don\'t Save and\nContinue With Next Jump'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Don\'t Save. I Want\nto Fix the Problem.'), QMessageBox.RejectRole)
        msgBox.setStyleSheet("QLabel{min-width: 600px;}");
        reply = msgBox.exec_()
        return reply

    def writeJumpDataToLog(self):
        meters = self.txtDistMeters.text()
        feet = self.txtDistFeet.text()
        jumpOK = self.radbtnJumpOK.isChecked()
        fall = self.radbtnFall.isChecked()
        passed = self.radbtnPass.isChecked()
        noReride = self.radbtnNoReride.isChecked()
        mandatory = self.radbtnMandatory.isChecked()
        optional = self.radbtnOptional.isChecked()
        self.writeToLog('Jump', meters=meters, feet=feet, jumpOK=jumpOK, fall=fall, passed=passed, noReride=noReride, mandatory=mandatory, optional=optional)
        return

    def nextJump(self):
        self.isMeasured = False
        self.fromPVR = False # reset the flag        
        goToNextJumpFlag = True
        saveFlagFrame = False
        saveFlagCap = False
        # Step 1: Write the current jump information to the log file
        self.writeJumpDataToLog()
        self.jumpWrittenToLog = True
        #Step 2: Reset Outcome and Reride group boxes
        self.radbtnJumpOK.setChecked(True)
        self.radbtnNoReride.setChecked(True)
        self.grpboxOutcome.setEnabled(False)
        self.grpboxReride.setEnabled(False)
        self.sliderBrightness.setEnabled(True)
        self.sliderContrast.setEnabled(True)
        # Step 3: Save the captured video if it passes asking and jump>3 checks
        if self.capReplay != None or self.capPix != None:
            if self.vidConfig['saveFrames'] == True or self.vidConfig['saveCaps'] == True:
                if self.vidConfig['saveFrames'] == True:
                    saveFlagFrame = True
                if self.vidConfig['saveCaps'] == True:
                    saveFlagCap = True
                # Step 1a: If ask before saving == True, then ask
                reply1 = None
                reply2 = None
                if saveFlagFrame == True and self.vidConfig['askSaveFrames'] == True:
                    if self.frameAlreadySaved == False:  # Prevent already saved frames to be saved
                        reply1 = QMessageBox.question(self, 'Save Measured Frame?', 'Save the Measured Frame?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        if reply1 == QMessageBox.No:
                            saveFlagFrame = False
                if self.frameOnly == False: #  Was not Capture Frame - there is a video that could be saved
                    if saveFlagCap == True and self.vidConfig['askSaveCaps'] == True:
                        reply2 = QMessageBox.question(self, 'Save Captured Video?', 'Save the Current Video?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        if reply2 == QMessageBox.No:
                            saveFlagCap = False
                jumpNum = self.spinBoxPass.value()
                if jumpNum > 3 and (reply1 == QMessageBox.Yes or reply2 == QMessageBox.Yes):
                    message = 'Jump number will exceed 3.  Usually this is done because a new skier name '
                    message += 'was not selected.  Do you want to continue saving as "Jump ' + str(jumpNum) + '"?'
                    reply3 = QMessageBox.question(self, 'Select New Skier?', message, buttons=QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No))
                    if reply3 == QMessageBox.No:  # User chose not to continue with save when jump>3
                        saveFlagFrame = False
                        saveFlagCap = False
                        goToNextJumpFlag = False
                
                filenameFrame = self.makeFileName(self.vidConfig['saveDirectoryFrames'], '.jpg')   # Get frame filename
                filenameCap = self.makeFileName(self.vidConfig['saveDirectoryCaps'], '.mp4')   # Get frame filename
                # Check to see if file already exists
                fileListFrame = os.listdir(self.vidConfig['saveDirectoryFrames'])
                fileListCap = os.listdir(self.vidConfig['saveDirectoryCaps'])
                justFileNameFrame = os.path.basename(filenameFrame)
                justFileNameCap = os.path.basename(filenameCap)
                
                if saveFlagFrame == True:
                    # Set flags for saving frame
                    if justFileNameFrame in fileListFrame:
                        reply4 = self.msgFileExists(justFileNameFrame)
                        if reply4 == 0: # Overwrite file
                            os.remove(filenameFrame)
                            saveFlagFrame = True
                            goToNextJumpFlag = True
                        elif reply4 == 1: # Don't save and continue to the next jump
                            saveFlagFrame = False
                            goToNextJumpFlag = True
                        else:  #Don't save and don't go to the next jump
                            saveFlagFrame = False
                            goToNextJumpFlag = False
                
                    # Save the frame in using JPG compression using quality setting = 80 (Qt default quality setting = 80)
                    if self.frameAlreadySaved == False:  # Prevent already frame from being saved
                        self.capPix.save(filenameFrame, 'JPG', 90)
                # Set flags for saving captured video
                if self.frameOnly == False: #  Was not Capture Frame - there is a video that could be saved
                    if saveFlagCap == True:
                        self.capReplay.release()                                        
                        if justFileNameCap in fileListCap:
                            reply5 = self.msgFileExists(justFileNameCap)
                            if reply5 == 0: # Overwrite file
                                os.remove(filenameCap)                                                        
                                saveFlagCap = True
                                goToNextJumpFlag = True
                            elif reply5 == 1: # Don't save and continue to the next jump
                                os.remove(filenameCap)
                                saveFlagCap = False
                                goToNextJumpFlag = True
                            else:  #Don't save and don't go to the next jump
                                saveFlagCap = False
                                goToNextJumpFlag = False
                        self.capReplay.release()
                        os.rename(self.capFileName, filenameCap)
        # Step 4: Reset the GUI for the next jump
        if goToNextJumpFlag == True:
            
            # Reset Capture Frame flag
            self.frameOnly = False
            
            # Clear the distances from the meters and feet text boxes
            self.txtDistMeters.setText('')
            self.txtDistFeet.setText('')
            
            # Hide the jump marker
            self.markerJmp.hide()
            self.markerJmp.lower()
            
            # Increment the jump number next to skier name
            if self.frameAlreadySaved == False:
                if self.wscConnection == False:
                    currentJumpNum = self.spinBoxPass.value()
                    nextJumpNum = currentJumpNum + 1
                    self.spinBoxPass.setValue(nextJumpNum)
            
            # Hide CapReplay video so that live video is showing again
            
            self.vidReplay.setStyleSheet('border-style: 0px solid black')
            self.vidReplay.lower()
            self.vidWindow.setStyleSheet("border-color: green; border-style: solid; border-width: 4px;")
            # Set the video border to green
            
            # Reset the SkierHitRamp and Capture Frame buttons
            self.btnHitRamp.setText('Skier Hits Ramp')
            self.btnHitRamp.setStyleSheet('background-color: #00ff00; color: black; border-style: inset; border-width: 4px;')
            self.btnHitRamp.setEnabled(True)
            self.btnCapFrame.setEnabled(True)
            self.btnHitRamp.setFocus(True)
            
            # Reset cboxSkierNames, spinBoxRound, and spinBoxPass
            if self.wscConnection == False:
                self.cboxSkierNames.setEnabled(True)
                self.spinBoxRound.setEnabled(True)
                self.spinBoxPass.setEnabled(True)

            # Reset Pass and Fall radio buttons
            self.radbtnPass.setChecked(False)
            self.radbtnFall.setChecked(False)
            
            # Reset the frame already saved flag to False
            self.frameAlreadySaved = False  
            
            # Disable Next Jump and Reselect Frame buttons
            self.btnNextJump.setEnabled(False)
            self.btnReselectFrame.setEnabled(False)
            
            # Reset isMeasuring flag to false
            self.isMeasuring = False
            
            # Enable Verify
            self.enableVerify(True)
            
            # Hide the slider
            self.vidSlider.setEnabled(False)
            self.vidSlider.hide()
            self.lblSlider.hide()

    def chooseCapSelectMeasure(self):
        # Choose what to do when the HitRamp button is clicked
        if self.btnHitRamp.text() == 'Skier Hits Ramp':
            self.skierHitsRamp()
        elif self.isCapturing == True:
            self.getCapDisplayTime()
        elif self.btnHitRamp.text()[:6] == 'Resend':
            self.resendJumpScore()
        elif self.btnHitRamp.text() == 'Record Jump':
            if self.isSetup == True:
                self.getDistance()
            else:
                message = 'Grid is not set up.  Cannot measure jump until grid is set up.'
                QMessageBox.warning(self, 'Cannot Measre Jump!', message, QMessageBox.Ok)
        
    def resendJumpScore(self):
        self.ioPass.send_jump_score(self.jumpData)

    def getCapDisplayTime(self):
        self.displayTime = time() - self.startTime

    def chooseEast(self):
        if self.isSelectFrame == True and self.btnHitRamp.text() != 'Record Jump':  # move capReplay frame forward
            self.rightNudge()
        else:  # Move grid marker right
            self.nudgeMarker('Right') 

    def chooseWest(self):
        if self.isSelectFrame == True and self.btnHitRamp.text() != 'Record Jump':  # move capReplay frame forward
            self.leftNudge()
        else:  # Move grid marker right
            self.nudgeMarker('Left') 

    def skierHitsRamp(self):        
        # Open file to write video to
        self.enableVerify(False)
        fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
        self.tempVid = cv2.VideoWriter(self.capFileName, fourcc, self.vidConfig['framesPerSec'], (self.frame_width, self.frame_height))
        self.startTime = time()
        self.stopTime = self.startTime + self.vidConfig['capLength']
        self.isCapturing = True
        self.btnHitRamp.setStyleSheet('background-color: light gray; color: black;')
        self.btnHitRamp.setText('')
        self.btnHitRamp.setFocus(True)
        self.btnCapFrame.setEnabled(False)
        self.grpboxOutcome.setEnabled(True)
        self.grpboxReride.setEnabled(True)
        self.chkboxShowHomoLevel.setChecked(False)
        self.chkboxShowGridAccuracy.setChecked(False)
        self.chkboxShowDistancesMeters.setChecked(False)
        self.chkboxShowDistancesFeet.setChecked(False)    
        self.jumpWrittenToLog = False
        if self.distDisplayExists == True:
            if self.flasher == True:
                self.distDisplay.updateDisplay('', '', '', self.displayChoice)
                self.distDisplay.setColor('yellow')
            else:
                self.distDisplay.updateDisplay('', '', '')
                self.distDisplay.setColor('yellow')
        
    def createCapReplay(self):
        self.capReplayExist = True
        self.cap_frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cap_frame_height = int(self.capReplay.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cap_length = int(self.capReplay.get(cv2.CAP_PROP_FRAME_COUNT))
        self.cap_fps = self.capReplay.get(cv2.CAP_PROP_FPS)
        
    def reselectFrame(self):
        self.showMeasure()

    def measureMode(self):
        # Step 1: initalize the captured video stream and get its properties
        self.capReplay = cv2.VideoCapture(self.capFileName)
        self.createCapReplay()
        # Step 2: Show the captured video frame, show the slider bar, and disable/enable widgets 
        self.showMeasure()       
        
    def showMeasure(self):
        self.markerJmp.hide()
        # Show the captured video window, Select Frame button, and slider
        self.vidReplay.setAlignment(Qt.AlignCenter)
        if self.fromPVR == True:
            self.vidReplay.setStyleSheet("border-color: #ff6600; border-style: solid; border-width: 8px;")
            self.vidReplay.setFrameShape(QFrame.Panel)
        else:
            self.vidReplay.setStyleSheet("border-color: blue; border-style: solid; border-width: 4px;")
        #self.fromPVR = False # reset the flag
        self.vidReplay.raise_()
        #self.markerJmp.raise_()
        self.vidReplay.show()
        self.btnHitRamp.setText('Select Frame\nand Mark Jump')
        self.btnHitRamp.setStyleSheet('background-color: light gray; border: 1px solid black; color: black')
        self.btnHitRamp.setEnabled(False)
        self.btnHitRamp.setFocus(False)        
        self.btnCapFrame.setEnabled(False)
        self.vidSlider.setEnabled(True)
        # Show the video slider
        self.vidSlider.setMinimum(0)
        self.vidSlider.blockSignals(True)
        self.vidSlider.setMaximum(self.cap_length-1)
        self.vidSlider.blockSignals(False)
        self.vidSlider.show()
        # Show the frame number label on the right
        self.lblSlider.setText(str(int(self.cap_length-1)))
        self.lblSlider.show()
        # Enable Next Jump button
        self.btnNextJump.setEnabled(True)
        self.enableVerify(False)
                
        # Position the captured video and show the frame to start frame selection
        if self.displayTime > 0.0:  # User presed the Enter key, Return key, or Spacebar
            ratio = self.displayTime / self.vidConfig['capLength']
            framePosition = int(ratio * self.cap_length)
            self.capReplay.set(cv2.CAP_PROP_POS_FRAMES, framePosition)
            self.displayTime = 0.0  # reset for next jump
            self.updateSlider()
        else:  
            if self.fromESC == True:  # User pressed ESC - position paused video to when the ESC was pressed
                framePosition = int(self.cap_length - self.secondsAfterESC * self.cap_fps - 1)
                self.capReplay.set(cv2.CAP_PROP_POS_FRAMES, framePosition)
                self.displayTime = 0.0  # reset for next jump
                self.updateSlider()
                self.fromESC = False
            else:  # If user did not press any key, then position video at middle frame
                framePosition = int(self.cap_length / 2.0)
                self.capReplay.set(cv2.CAP_PROP_POS_FRAMES, framePosition)
                self.updateSlider()
        self.capNextFrameSlot()
        
        # Set the measuring to false and selectFrame flag to True and set the focus to vidReplay label
        self.isMeasuring = True
        self.isSelectFrame = True
        self.vidReplay.setFocus()
        # Disable the North and South arrow buttons
        self.btnClickUp.setEnabled(False)
        self.btnClickDown.setEnabled(False)
        self.btnClickRight.setEnabled(True)
        self.btnClickLeft.setEnabled(True)
        if self.isSetup == False: # May not be true if loading video from file and grid not yet set up
            self.btnHitRamp.setEnabled(False)
            self.btnCapFrame.setEnabled(False)
            self.enterSetup()
           
    def capNextFrameSlot(self):
        #capPix = self.pix
        ret, frame = self.capReplay.read()
        if ret == True:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame,frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.capPix = QPixmap.fromImage(img)            
            self.capPix = self.capPix.scaled(self.vidReplay.width(), self.vidReplay.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.vidReplay.setPixmap(self.capPix)
            self.updateSlider()
            
    def capFrame(self):
        # Display current frame in vidWindow
        self.frameOnly = True
        self.jumpWrittenToLog = False
        self.vidReplay.setAlignment(Qt.AlignCenter)
        self.vidReplay.setStyleSheet("border-color: blue; border-style: solid; border-width: 4px;")
        self.vidReplay.raise_()
        self.markerJmp.raise_()
        self.vidReplay.setPixmap(self.pix)
        self.capPix = self.pix
        self.vidReplay.show()
        self.vidSlider.setEnabled(False)
        self.enableVerify(False)
        self.btnHitRamp.setText('Mark Jump')
        self.grpboxOutcome.setEnabled(True)
        self.grpboxReride.setEnabled(True)
        self.chkboxShowHomoLevel.setChecked(False)
        self.chkboxShowGridAccuracy.setChecked(False)
        self.chkboxShowDistancesMeters.setChecked(False)
        self.chkboxShowDistancesFeet.setChecked(False)    
        if self.distDisplayExists == True:
            if self.flasher == True:
                self.distDisplay.updateDisplay(self.cboxSkierNames.currentText(),self.txtDistMeters.text(),self.txtDistFeet.text(), self.displayChoice)
                self.distDisplay.setColor('yellow')
            else:
                self.distDisplay.updateDisplay('', '', '')
                self.distDisplay.setColor('yellow')
        self.measureJump()
            
    def measureJump(self):
        self.isMeasuring = True
        self.isSelectFrame = False

        self.btnCapFrame.setEnabled(False)
        self.btnNextJump.setEnabled(True)
        self.btnReselectFrame.setEnabled(True)
        self.btnClickUp.setEnabled(True)
        self.btnClickDown.setEnabled(True)
        self.btnClickRight.setEnabled(True)
        self.btnClickLeft.setEnabled(True)
        if self.vidSlider.isVisible() == True:
            self.vidSlider.setEnabled(False)
        self.vidSlider.show()
                
    def enableSetup(self,boolean):
        self.txtSurveyULX.setEnabled(boolean)
        self.txtSurveyULY.setEnabled(boolean)
        self.txtSurveyURX.setEnabled(boolean)
        self.txtSurveyURY.setEnabled(boolean)
        self.txtSurveyLLX.setEnabled(boolean)
        self.txtSurveyLLY.setEnabled(boolean)
        self.txtSurveyLRX.setEnabled(boolean)
        self.txtSurveyLRY.setEnabled(boolean)
        self.txtSurveyCkX.setEnabled(boolean)
        self.txtSurveyCkY.setEnabled(boolean)
        self.txtSurveyRpX.setEnabled(boolean)
        self.txtSurveyRpY.setEnabled(boolean)
        self.radbtnUL.setEnabled(boolean)
        self.radbtnUR.setEnabled(boolean)
        self.radbtnLL.setEnabled(boolean)
        self.radbtnLR.setEnabled(boolean)
        self.radbtnCheck.setEnabled(boolean)
        self.radbtnUL.setEnabled(boolean)
        self.chkboxSetup.setEnabled(boolean)
        self.chkboxLockGridBuoys.setEnabled(boolean)
        self.btnCheck.setEnabled(boolean)
        self.btnGrid.setEnabled(boolean)
        return
    
    def getJumpDistanceAdder(self):
        if self.vidConfig['discipline'] == 'waterski':
            return 2.1
        elif self.vidConfig['discipline'] == 'sitski':
            return 1.9
        else:
            return 0.0        

    def getDistance(self):
        # Step 1: Get marker ground coordinates
        pos = self.markerJmp.geometry()
        self.jumpScreenx = pos.x()+self.markerJmp.rect().center().x()
        self.jumpScreeny = pos.y()+self.markerJmp.rect().center().y()
        xy = self.getGroundCoords(self.jumpScreenx, self.jumpScreeny)
        self.jumpGroundX = xy[0]
        self.jumpGroundY = xy[1]
        # Step2: Get jump ramp ground coordinated
        rampx = float(self.txtSurveyRpX.text())
        rampy = float(self.txtSurveyRpY.text())
        # Step 3: Compute distance
        adder = self.getJumpDistanceAdder()
        self.distMeters = round(sqrt((xy[0]-rampx)**2 + (xy[1]-rampy)**2) + adder, 1)
        self.distFeet = self.distMeters / 0.3048
        distMetersString = '{:0.1f}'.format(self.distMeters)
        distFeetString = '{:0.0f}'.format(self.distFeet)
        self.txtDistMeters.setText(distMetersString)        
        self.txtDistFeet.setText(distFeetString)
        self.txtDistMeters.setAlignment(Qt.AlignCenter)
        self.txtDistFeet.setAlignment(Qt.AlignCenter)
        
        # Send data to the scorer via WaterSkiConnect
        if self.wscConnection == True:
            if self.passData != {}:  # If jumper info was received from WSTIMS
                self.jumpData = {'athleteId': self.passData['athleteId'],
                        'athleteName': self.cboxSkierNames.currentText(),
                        'athleteEvent': 'Jump',
                        'round': self.spinBoxRound.value(),
                        'passNumber': self.spinBoxPass.value(),
                        'score': {'distanceMetres': float(distMetersString),
                                  'distanceFeet': int(distFeetString)}}
            else:
                message = 'Cannot send jump distance to the scorer via WaterSkiConnect'
                message += '\nbecause no skier information has yet been received from' 
                message += '\nthe scoring system.'
                QMessageBox.warning(self,'Cannot Sent Score', message, QMessageBox.Ok)
            self.ioPass.send_jump_score(self.jumpData)  # send the jump score to waterskiconnect
        if self.distDisplayExists == True:
            a = self.cboxSkierNames.currentText()
            b = self.txtDistMeters.text()
            c = self.txtDistFeet.text()
            if self.flasher == True:
                self.distDisplay.updateDisplay(a, b, c, self.displayChoice)
            else:
                self.distDisplay.updateDisplay(a, b, c)
        # Step 4: Disable the Record Jump button so only one jump can be measured on the frame
        #         or enable resending the jump score to the scorer if WSC is connected
        if self.wscConnection == True:
            self.btnHitRamp.setEnabled(True)
            self.btnHitRamp.setText('Resend Jump\nDistance')
            self.btnHitRamp.setStyleSheet('background-color: #fef29a; color: black')
            self.btnReselectFrame.setEnabled(False)
            self.isMeasured = True
        else:
            self.btnHitRamp.setEnabled(False)
            self.btnHitRamp.setText('')
            self.btnHitRamp.setStyleSheet('color: None;')
            self.btnReselectFrame.setEnabled(False)
            self.isMeasured = True

    def validateEntry(self, s):
        # First, remove ',' from the string (QValidator(StandardNotation) allows commas)
        if ',' in s: 
            s.replace(',', '')
        response = self.validator.validate(s, 0)
        return response

    def fixValidation(self, txt):
        response = self.validator.validate(txt, 0)
        if response[0] == QValidator.Acceptable: # Acceptable
            if txt == '-' or txt == '':
                reply = 0.0
            else:
                reply = float(txt)
        elif response[0] == QValidator.Intermediate: # Intermediate
            reply = 'pass'
        else:   # Unacceptable
            reply = txt[:-1] # Remove invalid character from display
            QApplication.beep()   
        return reply

    def getSurveyCoords(self):
        # Each time a character is changed in any of the Grid Setup survey coordinates, all text fields are
        # read and self.gc is updated for all values'  This seemed simpler to implement than determining which 
        # valur changed and nly update that value in self.gc.  Nothing else is going on so performance is not an issue.
        # StandardNotation validator allows commas, whch causes an error.  Make values with commas = 0.0
        #if ',' in self.txtSurveyULX.text(): self.txtSurveyULX.setText('0.00')
        if ',' in self.txtSurveyULX.text(): self.txtSurveyULX.setText(self.txtSurveyULX.text().replace(',', ''))
        if ',' in self.txtSurveyULY.text(): self.txtSurveyULY.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyURX.text(): self.txtSurveyURX.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyURY.text(): self.txtSurveyURY.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyLLX.text(): self.txtSurveyLLX.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyLLY.text(): self.txtSurveyLLY.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyLRX.text(): self.txtSurveyLRX.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyLRY.text(): self.txtSurveyLRY.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyCkX.text(): self.txtSurveyCkX.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyCkY.text(): self.txtSurveyCkY.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyRpX.text(): self.txtSurveyRpX.setText(self.txtSurveyULY.text().replace(',', ''))
        if ',' in self.txtSurveyRpY.text(): self.txtSurveyRpY.setText(self.txtSurveyULY.text().replace(',', ''))
           
        response = self.fixValidation(self.txtSurveyULX.text())
        if response != 'pass':
            self.gc['surveyUL'][0] = response

        response = self.fixValidation(self.txtSurveyULY.text())
        if response != 'pass':
            self.gc['surveyUL'][1] = response

        response = self.fixValidation(self.txtSurveyURX.text())
        if response != 'pass':
            self.gc['surveyUR'][0] = response

        response = self.fixValidation(self.txtSurveyURY.text())
        if response != 'pass':
            self.gc['surveyUR'][1] = response

        response = self.fixValidation(self.txtSurveyLLX.text())
        if response != 'pass':
            self.gc['surveyLL'][0] = response

        response = self.fixValidation(self.txtSurveyLLY.text())
        if response != 'pass':
            self.gc['surveyLL'][1] = response

        response = self.fixValidation(self.txtSurveyLRX.text())
        if response != 'pass':
            self.gc['surveyLR'][0] = response

        response = self.fixValidation(self.txtSurveyLRY.text())
        if response != 'pass':
            self.gc['surveyLR'][1] = response

        response = self.fixValidation(self.txtSurveyCkX.text())
        if response != 'pass':
            self.gc['surveyCk'][0] = response

        response = self.fixValidation(self.txtSurveyCkY.text())
        if response != 'pass':
            self.gc['surveyCk'][1] = response

        response = self.fixValidation(self.txtSurveyRpX.text())
        if response != 'pass':
            self.gc['surveyRp'][0] = response

        response = self.fixValidation(self.txtSurveyRpY.text())
        if response != 'pass':
            self.gc['surveyRp'][1] = response

    def img2GrdCoords(self):
        X = [self.gc['surveyUR'][0], self.gc['surveyLR'][0], self.gc['surveyUL'][0], self.gc['surveyLL'][0]]
        Y = [self.gc['surveyUR'][1], self.gc['surveyLR'][1], self.gc['surveyUL'][1], self.gc['surveyLL'][1]]
        U = [self.gc['screenUR'][0], self.gc['screenLR'][0], self.gc['screenUL'][0], self.gc['screenLL'][0]]
        V = [self.gc['screenUR'][1], self.gc['screenLR'][1], self.gc['screenUL'][1], self.gc['screenLL'][1]]
        return X, Y, U, V
        
    
    def grd2ImgCoords(self):
        X = [self.gc['screenUR'][0], self.gc['screenLR'][0], self.gc['screenUL'][0], self.gc['screenLL'][0]]
        Y = [self.gc['screenUR'][1], self.gc['screenLR'][1], self.gc['screenUL'][1], self.gc['screenLL'][1]]
        U = [self.gc['surveyUR'][0], self.gc['surveyLR'][0], self.gc['surveyUL'][0], self.gc['surveyLL'][0]]
        V = [self.gc['surveyUR'][1], self.gc['surveyLR'][1], self.gc['surveyUL'][1], self.gc['surveyLL'][1]]
        return X, Y, U, V

    def computeTransformationCoefficients(self, X, Y, U, V):
        # Solve for coefficients        
        A = np.zeros(shape=(8,9))
        
        for i in range(4,8):
             A[i,5] = 1.0
             for j in range(0,3):
                 A[i,j] = 0.0
        for i in range(0,4):
            A[i,0] = 1.0
            for j in range(5,8):
                A[i,j] = 0.0
        try:
            for i in range(0,4):
                A[i,   3] = -U[i] * X[i]
                A[i+4 ,3] = -U[i] * Y[i]
                A[i,   4] = -V[i] * X[i]
                A[i+4, 4] = -V[i] * Y[i]
                A[i,   8] =  X[i]
                A[i+4, 8] =  Y[i]
                A[i,   1] =  U[i]
                A[i+4, 6] =  U[i]
                A[i,   2] =  V[i]
                A[i+4, 7] =  V[i]    
            # Find the rank of the first 8 columns and rows to make sure the matrix can be inverted
            b = np.zeros(shape=(8,8))
            for i in range(0,8):
                for j in range(0,8):
                    b[i,j] = A.item(i,j)
            rank = np.linalg.matrix_rank(b)
            if rank < b.shape[1]:
                message = 'Cannot setup grid!  Make sure all grid survey values are correctly '
                message += 'entered and all grid buoys are marked.'
                QMessageBox.warning(self, 'Grid Cannot Be Set Up', message, QMessageBox.Ok)
            else:
                # Compute the image to ground transformation coefficients
                flag, transformationCoefficients = self.solve(A)
            return flag, transformationCoefficients
        except:
            message = 'Can not process the input data.  Please check all grid buoy and check buoy entries and try again.'
            QMessageBox.warning(self, 'Can Not Process Grid Data', message, QMessageBox.Ok)

    def gridTransformationImg2Grd(self):

        # Get the survey coordnates from the Setup frame
        self.getSurveyCoords()
        
        # Generate the image-to-fround transormation coefficients
        X, Y, U, V = self.img2GrdCoords()
        flag, self.img2grd = self.computeTransformationCoefficients(X, Y, U, V)
        
        # Generatte the ground-to-image transofrmation coefficients
        X, Y, U, V = self.grd2ImgCoords()
        flag, self.grd2img= self.computeTransformationCoefficients(X, Y, U, V)                
        
        if flag == True:
            # Check to see if the grid passes goodness criteria
            #grdPt = self.getGroundCoords(self.gc['screenCk'][0], self.gc['screenCk'][1])                
            #distGrd = sqrt((grdPt[0] - self.gc['surveyCk'][0])**2 + (grdPt[1] - self.gc['surveyCk'][1])**2)             
            #distImg = sqrt((imgPt[0] - self.gc['screenCk'][0])**2 + (imgPt[1] - self.gc['screenCk'][1])**2)
            imgPt = self.getImageCoords(self.gc['surveyCk'][0], self.gc['surveyCk'][1])
            diffx = abs(imgPt[0] - self.gc['screenCk'][0])
            diffy = abs(imgPt[1] - self.gc['screenCk'][1])
            #print('DistGrd = ', distGrd, 'DistImg = ', distImg)
            #print('Diffx = {:.3f}   Diffy = {:.3f}     Distance = {:.3f}'.format(diffx, diffy, distImg))
  
            if diffx < 2.0 and diffy < 2.0:  # The setup passes the check
                self.chkboxLockGridBuoys.setChecked(False)
                self.writeToLog('Setup')
                self.getReadyToJump(True)
            else:  # The setup does not pass the check.  Paint the Check Arrow.
                self.isSetup = False
                self.enableVerify(False)
                self.arrowCk.setGeometry(0,0,90,35)
                imgPt = self.getImageCoords (self.gc['surveyCk'][0], self.gc['surveyCk'][1])
                self.arrowCk.move(imgPt[0]+2, imgPt[1] - 16)
                self.markerCk.setFocus()
                self.markerCk.raise_()
                self.arrowCk.show() 

    def solve(self,a):
        # Use row reduction insteead of numpy so that the solution matches VJ better
        r = 8
        try:
            for i in range(0, r):
                for j in range(i, r):
                    
                # Check if row reduction will cause a zero in diagonal in the next row
                    if i < r-1:
                        if a.item(i+1,i+1) == a.item(i,i+1):
                            # Need to find first non-match and switch rows
                            for z in range(i+2,r):    
                                if a.item(i+1,i+1) != a.item(z,i+1):
                                    for m in range(0,r+1):
                                        x = a.item(i+1,m)
                                        a[i+1,m] = a.item(z,m)
                                        a[z,m] = x
                                    break
                    # Reduce the rows        
                    b = 1.0 / a.item(i,i)
                    for k in range(0, r+1):
                        a[i,k] = b * a.item(i,k)
                    for j in range(0, r):
                        if j != i:
                            b = -a.item(j,i)
                            for k in range(0, r+1):
                                a[j,k] = a.item(j,k) + b * a.item(i,k) 
            c = []
            for i in range(0,r):
                c.append(a.item(i,r))
            return True, c
        except:
            message = 'Cannot setup grid!  Make sure all grid survey values are correctly '
            message += 'entered and all grid buoys are marked.'
            QMessageBox.warning(self, 'Grid Cannot Be Set Up', message, QMessageBox.Ok)
            c = []
            return False, c

    def enableDisableFrameSetup(self, boolean):
        self.txtSurveyULX.setEnabled(boolean)
        self.txtSurveyULY.setEnabled(boolean)
        self.txtSurveyURX.setEnabled(boolean)
        self.txtSurveyURY.setEnabled(boolean)
        self.txtSurveyLLX.setEnabled(boolean)
        self.txtSurveyLLY.setEnabled(boolean)
        self.txtSurveyLRX.setEnabled(boolean)
        self.txtSurveyLRY.setEnabled(boolean)
        self.txtSurveyCkX.setEnabled(boolean)
        self.txtSurveyCkY.setEnabled(boolean)
        self.txtSurveyRpX.setEnabled(boolean)
        self.txtSurveyRpY.setEnabled(boolean)
        self.lblSurveyULX.setEnabled(boolean)
        self.lblSurveyULY.setEnabled(boolean)
        self.lblSurveyURX.setEnabled(boolean)
        self.lblSurveyURY.setEnabled(boolean)        
        self.lblSurveyLLX.setEnabled(boolean)
        self.lblSurveyLLY.setEnabled(boolean)        
        self.lblSurveyLRX.setEnabled(boolean)
        self.lblSurveyLRY.setEnabled(boolean)        
        self.lblSurveyCkX.setEnabled(boolean)
        self.lblSurveyCkY.setEnabled(boolean)
        self.lblSurveyJpX.setEnabled(boolean)
        self.lblSurveyJpY.setEnabled(boolean)
        self.setSetupTabOrder(boolean)
        self.radbtnUL.setEnabled(boolean)
        self.radbtnUR.setEnabled(boolean)
        self.radbtnLL.setEnabled(boolean)
        self.radbtnLR.setEnabled(boolean)
        self.lblRamp.setEnabled(boolean)
        self.btnCheck.setEnabled(boolean)
        self.radbtnCheck.setEnabled(boolean)
        self.chkboxLockGridBuoys.setEnabled(boolean)       
        self.btnHitRamp.setEnabled(False)        
        if boolean == True:
            self.frameSetup.setStyleSheet('background-color: red; border: 1px solid black')
            self.radbtnSurvey.setEnabled(False)
            self.radbtnScreen.setEnabled(False)
        else:
            self.frameSetup.setStyleSheet('background-color: green; border: 1px solid black')
            self.radbtnSurvey.setEnabled(True)
            self.radbtnScreen.setEnabled(True)

    def getReadyToJump(self, checkedFlag):
        #self.setWidgetsForJump()
        self.isSetup = True
        self.chkboxShowBuoys.setChecked(True)
        self.enableVerify(True)
        self.chkboxSetup.setChecked(False)
        self.arrowCk.clearFocus()
        self.arrowCk.hide()
        self.enableDisableFrameSetup(False)
        self.enableVerify(True)
        self.vidWindow.setStyleSheet("border-color: green; border-style: solid; border-width: 4px;")
        self.btnHitRamp.setStyleSheet('background-color: #00ff00; color: black; border-style: inset; border-width: 4px;')
        self.btnHitRamp.setEnabled(True)
        self.btnHitRamp.setFocus(True)
        self.btnCapFrame.setEnabled(True)
        self.chkboxShowBuoys.setEnabled(True)
        self.chkboxShowHomoLevel.setEnabled(True) 
        self.chkboxShowGridAccuracy.setEnabled(True)
        self.chkboxShowDistancesMeters.setEnabled(True)
        self.chkboxShowDistancesFeet.setEnabled(True)
        self.btnClickUp.setEnabled(False)
        self.btnClickDown.setEnabled(False)
        self.btnClickRight.setEnabled(False)
        self.btnClickLeft.setEnabled(False)
        self.btnReselectFrame.setEnabled(False)
        if checkedFlag == True: # If this functions was enterd from checking setup (instead of loading grid from file), then show accrusy grid
            self.chkboxShowHomoLevel.setChecked(True)
            reply = QMessageBox.question(self, 'Save Grid?', 'Do you want to save the grid?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.isSetup = True
                self.saveGrid()

    def enterSetup(self):  # Grid is already setup but user wants to adjust it
        if self.chkboxSetup.isChecked() == True or self.newLoad == True:
            self.radbtnSurvey.setChecked(True)
            self.chkboxSetup.setChecked(True)
            self.enableDisableFrameSetup(True)
            self.isMeasuring = False
            self.isSetup = False
            self.isSselectFrame = False
            #self.markerCk.hide() # Clear the check buoy marker
            self.markerJmp.hide()  #Just in case it is there after measuring a jump and then loading a captured video file
            self.chkboxShowHomoLevel.setEnabled(False)
            self.chkboxShowGridAccuracy.setEnabled(False)
            self.chkboxShowDistancesMeters.setEnabled(False)
            self.chkboxShowDistancesFeet.setEnabled(False)
            self.btnHitRamp.setEnabled(False)
            self.btnHitRamp.setStyleSheet('background-color: light gray; border: 1px solid black; color: gray')
            self.vidWindow.setStyleSheet("border-color: red; border-style: solid; border-width: 4px;")
            self.btnCapFrame.setEnabled(False)
            self.btnReselectFrame.setEnabled(False)
            self.enableVerify(False)
            self.radbtnUL.setChecked(True)
            self.btnClickUp.setEnabled(True)
            self.btnClickDown.setEnabled(True)
            self.btnClickRight.setEnabled(True)
            self.btnClickLeft.setEnabled(True)
            self.clearHomoGrid()
            
    def setSetupTabOrder(self,boolean):
        if boolean == True:
            self.txtSurveyULX.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyULY.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyURX.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyURY.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyLLX.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyLLY.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyLRX.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyLRY.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyCkX.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyCkY.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyRpX.setFocusPolicy(Qt.StrongFocus)
            self.txtSurveyRpY.setFocusPolicy(Qt.StrongFocus)
            self.setTabOrder(self.txtSurveyULX, self.txtSurveyULY)
            self.setTabOrder(self.txtSurveyULY, self.txtSurveyURX)
            self.setTabOrder(self.txtSurveyURX, self.txtSurveyURY)
            self.setTabOrder(self.txtSurveyURY, self.txtSurveyLLX)
            self.setTabOrder(self.txtSurveyLLX, self.txtSurveyLLY)
            self.setTabOrder(self.txtSurveyLLY, self.txtSurveyLRX)
            self.setTabOrder(self.txtSurveyLRX, self.txtSurveyLRY)
            self.setTabOrder(self.txtSurveyLRY, self.txtSurveyCkX)
            self.setTabOrder(self.txtSurveyCkX, self.txtSurveyCkY)
            self.setTabOrder(self.txtSurveyCkY, self.txtSurveyRpX)
            self.setTabOrder(self.txtSurveyRpX, self.txtSurveyRpY)
        else:
            self.txtSurveyULX.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyULY.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyURX.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyURY.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyLLX.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyLLY.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyLRX.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyLRY.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyCkX.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyCkY.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyRpX.setFocusPolicy(Qt.ClickFocus)
            self.txtSurveyRpY.setFocusPolicy(Qt.ClickFocus)            

    def verifySetup(self, pos):
        xy = self.getGroundCoords(pos.x(), pos.y())   
        self.txtImg2GrdX.setText('{:0.2f}'.format(xy[0]))
        self.txtImg2GrdY.setText('{:0.2f}'.format(xy[1]))
        adder = self.getJumpDistanceAdder()
        distM = round(sqrt(xy[0]**2 + xy[1]**2) + adder, 1)
        distF = distM / 0.3048
        self.txtVerifyMeters.setText('{:0.1f}'.format(distM))
        self.txtVerifyFeet.setText('{:0.0f}'.format(distF))
        self.txtVerifyScreenX.setText('{:4d}'.format(int(pos.x())))
        self.txtVerifyScreenY.setText('{:4d}'.format(int(pos.y())))
        
        self.writeToLog('Verify')

    def enableVerify(self, boolean):
        self.chkboxVerify.setEnabled(boolean)
        self.txtImg2GrdX.setEnabled(boolean)
        self.txtImg2GrdY.setEnabled(boolean)
        self.txtVerifyScreenX.setEnabled(boolean)
        self.txtVerifyScreenY.setEnabled(boolean)
        self.txtVerifyMeters.setEnabled(boolean)
        self.txtVerifyFeet.setEnabled(boolean)
                           
    def verifyTracker(self):
        if self.chkboxVerify.isChecked() == True:
            self.verifyLabel.show()
            self.verifyLabel.raise_()
            self.tracker.positionChanged.connect(self.on_positionChanged)
            self.chkboxSetup.setEnabled(False)
            self.btnHitRamp.setEnabled(False)
            self.btnCapFrame.setEnabled(False)
            if self.gridVisible == True:
                self.markerCk.hide()
        else:
            self.verifyLabel.hide()
            self.chkboxSetup.setEnabled(True)
            self.btnHitRamp.setEnabled(True)
            self.btnCapFrame.setEnabled(True)
            if self.gridVisible == True:
                self.markerCk.show()
            #self.tracker.positionChanged.disconnect(self.on_positionChanged)

    def toggleShowHomoLevel(self):
        self.toggleAccuracies('HomoLevel')
            
    def toggleShowGridAccuracy(self):
        self.toggleAccuracies('NumericalAccuracies')
        
    def toggleShowDistanceMeters(self):
        self.toggleAccuracies('DistancesMeters')

    def toggleShowDistanceFeet(self):
        self.toggleAccuracies('DistancesFeet')

    def toggleAccuracies(self, flag):
        if flag == 'HomoLevel':
            if self.chkboxShowHomoLevel.isChecked() == True:
                self.chkboxShowGridAccuracy.setChecked(False)
                self.chkboxShowDistancesMeters.setChecked(False)
                self.chkboxShowDistancesFeet.setChecked(False)
                self.showHomologationGrid()
            else:
                if self.chkboxShowGridAccuracy.isChecked() == False and \
                self.chkboxShowDistancesMeters.isChecked() == False and \
                self.chkboxShowDistancesFeet.isChecked() == False:
                    self.clearHomoGrid()
        if flag == 'NumericalAccuracies':
            if self.chkboxShowGridAccuracy.isChecked() == True:
                self.chkboxShowHomoLevel.setChecked(False)
                self.chkboxShowDistancesMeters.setChecked(False)
                self.chkboxShowDistancesFeet.setChecked(False)
                self.showHomologationGrid()
            else:
                if self.chkboxShowHomoLevel.isChecked() == False and \
                self.chkboxShowDistancesMeters.isChecked() == False and \
                self.chkboxShowDistancesFeet.isChecked() == False:
                    self.clearHomoGrid()
        if flag == 'DistancesMeters':
            if self.chkboxShowDistancesMeters.isChecked() == True:
                self.chkboxShowHomoLevel.setChecked(False)
                self.chkboxShowGridAccuracy.setChecked(False)
                self.chkboxShowDistancesFeet.setChecked(False)
                self.showHomologationGrid()
            else:
                if self.chkboxShowHomoLevel.isChecked() == False and \
                self.chkboxShowGridAccuracy.isChecked() == False and \
                self.chkboxShowDistancesFeet.isChecked() == False:
                    self.clearHomoGrid()
        if flag == 'DistancesFeet':
            if self.chkboxShowDistancesFeet.isChecked() == True:
                self.chkboxShowHomoLevel.setChecked(False)
                self.chkboxShowGridAccuracy.setChecked(False)
                self.chkboxShowDistancesMeters.setChecked(False)
                self.showHomologationGrid()
            else:
                if self.chkboxShowHomoLevel.isChecked() == False and \
                self.chkboxShowGridAccuracy.isChecked() == False and \
                self.chkboxShowDistancesMeters.isChecked() == False:
                    self.clearHomoGrid()
    def clearHomoGrid(self):
        flag = not self.accuracies
        if flag == False:
            for i in range(0,11):
                for j in range(0,11):
                    item = i*11+j
                    self.accuracies[item].hide()

    def showGoodnessOfFit(self):  # Not currently used in VTM        
        xDiff = int((self.vidWindow.width() - 20 ) / 14.0)
        yDiff = int((self.vidWindow.height() - 20 ) / 7.0)        
        # Get the first set of ground coordinates
        for i in range(0,8):
            for j in range(0,15):
                xy0 = [j * xDiff + 10.0, i * yDiff + 10.0]
                XY0 = self.getGroundCoords(xy0[0], xy0[1])
                xy1 = self.getImageCoords (XY0[0], XY0[1])
                XY1 = self.getGroundCoords(xy1[0], xy1[1])
                #diff = sqrt((XY0[0] - XY1[0])**2 + (XY0[1] - XY1[1])**2)

    def showHomologationGrid(self):
        # If exiisting accuracies exist, hide them
        flag = not self.accuracies
        if flag == False:
            self.clearHomoGrid()
            
        # This function computes a 11 x 11 matrix of comparisons between true 
        # ground coordinates and ground-to-image and image-to ground computations
        x = np.zeros(shape=(11,11))
        y = np.zeros(shape=(11,11))
        homoValues = []

        # Get coordinates of left and right edges of the grid (11 points on left edge and 11 points on right edge)
        incXLeft  = self.gc['screenLL'][0] - self.gc['screenUL'][0]
        incYLeft  = self.gc['screenLL'][1] - self.gc['screenUL'][1]
        incXRight = self.gc['screenLR'][0] - self.gc['screenUR'][0]
        incYRight = self.gc['screenLR'][1] - self.gc['screenUR'][1]
        for i in range(0,11):
            x[i,0] =  self.gc['screenLL'][0] - incXLeft  * i / 10.0
            y[i,0] =  self.gc['screenLL'][1] - incYLeft  * i / 10.0
            x[i,10] = self.gc['screenLR'][0] - incXRight * i / 10.0
            y[i,10] = self.gc['screenLR'][1] - incYRight * i / 10.0
        # Create grid by evenly spacing points along horizontal lines between the left and right sides    
        for i in range(0, 11):
            # For each row, find the x and y differences between the left and right edges
            incX  =  x.item(i,10) - x.item(i,0)
            incY  =  y.item(i,10) - y.item(i,0)
            # Create the row
            for j in range(0, 11):
                x[i,j] = x.item(i,0) + incX * j / 10.0
                y[i,j] = y.item(i,0) + incY * j / 10.0
            # For each point in the matrix:
            # Step 1: Project the point to the ground and then find the distance of that point from the ramp
            # Step 2: Change the grid x-value by one pixel and do the same
            # Step 3: Change the grid y-value by one pixel and do the same
            # Step 4: Find the difference between the original point and the two offset points
            # Step 5: The distance to be displayed is the greater of these two differencs 
            for j in range(0,11):               
                grdPt0 = self.getGroundCoords(x.item(i,j), y.item(i,j))
                dist0 = sqrt(grdPt0[0]**2 + grdPt0[1]**2)
                grdPt1 = self.getGroundCoords(x.item(i,j)+1, y.item(i,j))
                dist1 = sqrt(grdPt1[0]**2 + grdPt1[1]**2)
                grdPt2 = self.getGroundCoords(x.item(i,j), y.item(i,j)+1)
                dist2 = sqrt(grdPt2[0]**2 + grdPt2[1]**2)                
                dist = max(abs(dist0-dist1), abs(dist0-dist2))
                
                if self.chkboxShowHomoLevel.isChecked() == True:  # Display homologation level
                    if dist <= 0.1:
                        homoValues.append('R')
                    elif dist <= 0.15:
                        homoValues.append('L')
                    elif dist <= 0.20:
                        homoValues.append('C')
                    else:
                        homoValues.append('X')
                if self.chkboxShowGridAccuracy.isChecked() == True:  # Display numerical differences
                    homoValues.append('{:0.2f}'.format(dist))
                if self.chkboxShowDistancesMeters.isChecked() == True:  # Display the jump distance in meters
                    if self.vidConfig['discipline'] == 'waterski':
                        distance = sqrt(grdPt0[0]**2 + grdPt0[1]**2) + 2.1
                    elif self.vidConfig['discipline'] == 'sitski':
                        distance = sqrt(grdPt0[0]**2 + grdPt0[1]**2) + 1.9
                    else:
                        distance = sqrt(grdPt0[0]**2 + grdPt0[1]**2)
                    homoValues.append('{:0.1f}'.format(distance))
                if self.chkboxShowDistancesFeet.isChecked() == True:  # Display the jump distance in feet
                    if self.vidConfig['discipline'] == 'waterski':
                        distance = sqrt(grdPt0[0]**2 + grdPt0[1]**2) + 2.1
                    elif self.vidConfig['discipline'] == 'sitski':
                        distance = sqrt(grdPt0[0]**2 + grdPt0[1]**2) + 1.9
                    else:
                        distance = sqrt(grdPt0[0]**2 + grdPt0[1]**2)                    
                    distance = int(distance / 0.3048 + 0.5) # round to nearest foot
                    homoValues.append('{:0d}'.format(distance))
                
        # Create the Qlabels
        self.accuracies = []
        for value in homoValues:
            pixmap = QPixmap(37, 37)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            if self.vidConfig['homoGridColor'] == 'red':
                color = Qt.red
            elif self.vidConfig['homoGridColor'] == 'black':
                color = Qt.black
            elif self.vidConfig['homoGridColor'] == 'yellow':
                color = Qt.yellow
            else:
                color = Qt.green
            painter.setPen(QPen(color, Qt.SolidLine))
            if self.chkboxShowHomoLevel.isChecked() == True:
                painter.setFont(QFont("Arial", 12))   # Homologation levels
            else:
                painter.setFont(QFont("Arial", 10))   # Numerical accuracy values           
            painter.drawText(pixmap.rect(), Qt.AlignCenter, value)
            painter.end()            
            m0 = QLabel(self)
            m0.setPixmap(pixmap)
            m0.adjustSize()
            self.accuracies.append(m0)
        # Plot the matrix of QLabels 
        for i in range(0,11):
            for j in range(0,11):
                #imgPt = self.getImageCoords(x.item(i,j), y.item(i,j))
                item = i*11+j
                self.accuracies[item].move(QPoint(x.item(i,j), y.item(i,j)) - self.accuracies[item].rect().center())
                self.accuracies[item].show()
        
    @pyqtSlot(QPoint)
    def on_positionChanged(self, pos):
        if self.vidWindow.underMouse() and self.chkboxVerify.isChecked() == True:
            delta = QPoint(50, -15)
            self.verifyLabel.move(pos + delta)
            self.verifyLabel.show()
        else:
            self.verifyLabel.hide()
            #self.verifyLabel.adjustSize()

    def getGroundCoords(self, x, y):
        # x and y are screen coordinates.  Get corresponding ground coordinates
        denom = self.img2grd[3] * x + self.img2grd[4] * y + 1.0
        xg =   (self.img2grd[0] + self.img2grd[1] * x + self.img2grd[2] * y) / denom
        yg =   (self.img2grd[5] + self.img2grd[6] * x + self.img2grd[7] * y) / denom
        return [xg, yg]

    def getImageCoords(self, X, Y):
        c0 = self.img2grd[0]
        c1 = self.img2grd[1]
        c2 = self.img2grd[2]
        c3 = self.img2grd[3]
        c4 = self.img2grd[4]
        c5 = self.img2grd[5]
        c6 = self.img2grd[6]
        c7 = self.img2grd[7]
        denom = (c6 * c4 - c7 * c3) * X + (c2 * c3 - c1 * c4) * Y  + c1 * c7 - c2 * c6
        xi = ((c7 - c5 * c4) * X + (c0 * c4 - c2) * Y + c2 * c5 - c0 * c7) / denom
        yi = ((c5 * c3 - c6) * X + (c1 - c0 * c3) * Y + c0 * c6 - c1 * c5) / denom
        return [xi, yi]
        
    def nudgeMarker(self, direction):
        if direction == 'Left':
            deltax = -1
            deltay =  0                
        elif direction == 'Right':
            deltax =  1
            deltay =  0
        elif direction == 'Up':
            deltax =  0
            deltay = -1
        elif direction == 'Down':
            deltax =  0
            deltay =  1
        if self.isMeasuring == True:
            pos = self.markerJmp.geometry()
            self.markerJmp.move(pos.x() + deltax, pos.y() + deltay)
            #self.markerJmp.show()            
        else:
            if self.radbtnUL.isChecked() == True or self.chkboxLockGridBuoys.isChecked() == True:
                self.isSetup = False
                self.enableVerify(False)
                pos = self.markerUL.geometry()
                self.gc['screenUL'] = [pos.x()+self.markerUL.rect().center().x()+deltax, pos.y()+self.markerUL.rect().center().y()+deltay]          
                self.markerUL.move(pos.x() + deltax, pos.y() + deltay)
                self.markerUL.show()
            if self.radbtnUR.isChecked() == True or self.chkboxLockGridBuoys.isChecked() == True:
                self.isSetup = False
                self.enableVerify(False)
                pos = self.markerUR.geometry()
                self.gc['screenUR'] = [pos.x()+self.markerUR.rect().center().x()+deltax, pos.y()+self.markerUR.rect().center().y()+deltay]          
                self.markerUR.move(pos.x() + deltax, pos.y() + deltay)
                self.markerUR.show()
            if self.radbtnLL.isChecked() == True or self.chkboxLockGridBuoys.isChecked() == True:
                self.isSetup = False
                self.enableVerify(False)
                pos = self.markerLL.geometry()
                self.gc['screenLL'] = [pos.x()+self.markerLL.rect().center().x()+deltax, pos.y()+self.markerLL.rect().center().y()+deltay]           
                self.markerLL.move(pos.x() + deltax, pos.y() + deltay)
                self.markerLL.show()
            if self.radbtnLR.isChecked() == True or self.chkboxLockGridBuoys.isChecked() == True:
                self.isSetup = False
                self.enableVerify(False)
                pos = self.markerLR.geometry()
                self.gc['screenLR'] = [pos.x()+self.markerLR.rect().center().x()+deltax, pos.y()+self.markerLR.rect().center().y()+deltay]         
                self.markerLR.move(pos.x() + deltax, pos.y() + deltay)
                self.markerLR.show()
            if self.radbtnCheck.isChecked() == True or self.chkboxLockGridBuoys.isChecked() == True:
                self.isSetup = False
                self.enableVerify(False)
                pos = self.markerCk.geometry()
                self.gc['screenCk'] = [pos.x()+self.markerCk.rect().center().x()+deltax, pos.y()+self.markerCk.rect().center().y()+deltay]       
                self.markerCk.move(pos.x() + deltax, pos.y() + deltay)
                self.markerCk.show()

    def nudgeMarkerLeft(self):
        self.nudgeMarker('Left')
        
    def nudgeMarkerUp(self):
        self.nudgeMarker('Up')
        
    def nudgeMarkerRight(self):
        self.nudgeMarker('Right')  
        
    def nudgeMarkerDown(self):
        self.nudgeMarker('Down')        

    def leftNudge(self):
        frameNow = int(self.capReplay.get(cv2.CAP_PROP_POS_FRAMES))
        frameNext = frameNow - 2
        self.nudge(frameNext)
        
    def rightNudge(self):
        frameNow = int(self.capReplay.get(cv2.CAP_PROP_POS_FRAMES))
        frameNext = frameNow  
        self.nudge(frameNext)

    def nudge(self, value):
        if value < 0:
            value = 0
        if value > self.cap_length - 1:
            value = self.cap_length - 1
        self.capReplay.set(cv2.CAP_PROP_POS_FRAMES, value)
        self.capNextFrameSlot()            

    def updateSlider(self):
        if self.capReplay.isOpened():
            frameNumber = int(self.capReplay.get(cv2.CAP_PROP_POS_FRAMES) - 1)
            self.vidSlider.blockSignals(True)
            self.vidSlider.setValue(frameNumber)
            self.vidSlider.blockSignals(False)
            self.lblSlider.setText(str(frameNumber-1))   

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        if ret == True:
            # Adjust the contrast and brightness
            cv2.normalize(frame, frame, self.alpha, self.beta, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            
            dt = datetime.now()
            dtString = datetime.strftime(dt, '%Y-%m-%d @ %H:%M:%S')
            width = int(180 / 640 * self.frame_width)
            height = int(20 / 480 * self.frame_height)
            fontSize = self.frame_height / 480 * 0.8
            col = int(3 / 170 * self.frame_width)
            row = int(height * 0.75)
            frame = cv2.rectangle(frame, (0, 0), (width, height), (0,0,0), -1)
            frame = cv2.putText(frame, dtString, (col,row), cv2.FONT_HERSHEY_PLAIN, fontSize, (255, 255, 255))
            
            # write frame to PVR
            if self.isPVR == True:
                self.pvrVid.write(frame)
                if datetime.now() - self.pvrStartTime > timedelta(seconds=3600):  # Check if new PVR file should be created
                    self.pvrVid.release()
                    self.startPVR()
                
            # write frame to temp file if capturing the jump
            if self.isCapturing == True:
                self.tempVid.write(frame)
                if time() > self.stopTime:
                    self.isCapturing = False
                    self.tempVid.release()
                    self.measureMode()     
            
            # DIsplay the video frame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame,frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.pix = QPixmap.fromImage(img)            
            '''if self.isCapCropped == True:
                pict = pict.copy(self.capGeom)'''
            self.pix = self.pix.scaled(self.vidWindow.width(), self.vidWindow.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.vidWindow.setPixmap(self.pix)
            
            # Get and display the Loupe frame
            pos = QCursor.pos()
            if self.radbtn2x.isChecked() == True:
                offset = int(self.lblLoupe.width() / 2)  # 160 / 2 = 80128
            elif self.radbtn3x.isChecked() == True:
                offset = int(self.lblLoupe.width() / 3) 
            elif self.radbtn4x.isChecked() == True:
                offset = int(self.lblLoupe.width() / 4)
            else:
                offset = int(self.lblLoupe.width() / 5)
            cropPix = self.screen.grabWindow(0, pos.x()-int(offset/2), pos.y()-int(offset/2), offset, offset)
            cropPix = cropPix.scaled(self.lblLoupe.width(), self.lblLoupe.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lblLoupe.setPixmap(cropPix)
        else:
            print('Failed frame')

    def scaleFrame(self, frame_width, frame_height, label_width, label_height):
        windowRatio = label_width / label_height
        frameRatio = frame_width / frame_height
        if  frameRatio > windowRatio:  # if window is more elngated than image frame, scale to height
            scale = label_height / frame_height
        else:
            scale = label_width  / frame_width   
        return scale
        
    def setStart(self):
        self.start()
        
    def start(self):
        millisecs = int(1000.0 / self.vidConfig['framesPerSec'])
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(millisecs)
        
    def initializeVideoStream(self):
        self.cap = cv2.VideoCapture(self.vidConfig['cameraID'])
        if self.cap.isOpened() == False:
            self.cap.release()            
            QMessageBox.critical(self, 'Oops!','Could not open video from port ' + str(self.vidConfig['cameraID']),QMessageBox.Ok)  
        else:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            #print('Dimensions = ', self.frame_width, ' x ', self.frame_height)
            self.writeToLog('VideoStream')
            self.setStart()
            
    def loadSkierNames(self):
        tempString = []
        tempNames = []
        message = 'Imported skier names will be mergerd into the Master Names List.  '
        message += 'The preferred list comes from the WSTMS jump running order by '
        message += 'clicking the "Video Run Order" button.  If the file is a ".txt"'
        message += 'or ".csv" file, refer to the manual for more information.'
        reply = QMessageBox.information(self, 'Skier Name Files', message, QMessageBox.Ok)
        
        tempString = QFileDialog.getOpenFileName(self, 'Import Skier Names','C:\\',"XML, TXT, CSV File (*.xml *.txt *.csv) ;;Any File (*.*)")
        if tempString[0] != "":
            skierFileName = tempString[0]
            fname, fextension = os.path.splitext(skierFileName)
            if fextension.lower() == '.xml':
                tempNames = self.loadXMLSkierNames(skierFileName)
            elif fextension.lower() == '.txt' or fextension.lower() == '.csv':
                firstLine = True
                with open(skierFileName, newline='') as csvfile:
                    rows = csv.reader(csvfile, delimiter='\t')
                    for row in rows:
                        if firstLine == True:
                            skipRestOfLoad = False
                            message = 'The first row in the selected file is: \n\n     ' + row[0] + '\n\n'
                            message += "Does this row look like a skier's name, a column heading, or "
                            message += 'the beginning of an XML file (starts with a "<")? '
                            msgBox = QMessageBox()
                            msgBox.setWindowTitle('File Type')
                            msgBox.setText(message)
                            msgBox.addButton('Skier Name', QMessageBox.AcceptRole)
                            msgBox.addButton('Column Heading', QMessageBox.AcceptRole)
                            msgBox.addButton('XML', QMessageBox.AcceptRole)
                            msgBox.addButton('Cancel', QMessageBox.RejectRole)
                            reply = msgBox.exec_()
                            if reply == 0:
                                tempNames.append(row[0])
                            elif reply == 2:
                                tempNames = self.loadXMLSkierNames(skierFileName)
                                skipRestOfLoad = True
                            elif reply == 3:
                                pass
                            firstLine = False
                        else:
                            if skipRestOfLoad == False:
                                tempNames.append(row[0])
            for name in tempNames:
                self.updateSkierNames(name = name, appendFlag = True)
            self.updateSkierNames(name = 'Jump Skier', appendFlag = True) # add "Jump Skier" name if not already in th elist
            
    def loadXMLSkierNames(self, skierFileName):
        names = []
        tree = et.ElementTree(file=skierFileName)
        tournament = tree.getroot()
        for event in tournament:
            for eventGroup in event:
                for division in eventGroup:
                    for skier in division:
                        names.append(skier.attrib['name'] + "   " + division.attrib['name'])    
        return names

    def enterSkierName(self):
        name = self.cboxSkierNames.currentText()
        if name not in self.skierNames:
            self.skierNames.append(name)
        self.updateSkierNames(name = name, appendFlag = True)   
        self.cboxSkierNames.setFocus(False)
                
    def clearNamesList(self):
        message = 'Do you want to clear the Master Skier Names List file?'
        reply = QMessageBox.question(self, 'Clear Names', message, QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            self.cboxSkierNames.clear()
            listFileName = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\VTM Master Names List.txt')            
            with open(listFileName, 'w') as f:
                f.write("Jump Skier")
            self.updateSkierNames(name = 'Jump Skier', appendFlag = False)

    def updateSkierNames(self, **kwargs):
        if 'name' in kwargs.keys():
            name = kwargs['name']
        '''if 'division' in kwargs.keys():
            division = kwargs['division']'''
        if 'appendFlag' in kwargs.keys():
            appendFlag = kwargs['appendFlag']
        if 'roundNumber' in kwargs.keys():
            roundNumber = int(kwargs['roundNumber'])
        if 'passNumber' in kwargs.keys():        
            passNumber = int(kwargs['passNumber'])
        updatePassRound = False
        if 'source' in kwargs.keys() and kwargs['source'] == 'pass_data':
            updatePassRound = True
        if appendFlag == True:
            if name not in self.skierNames:
                #self.skierNames.append(name + ' ' + division)
                self.skierNames.append(name)
        else:
            self.skierNames = ['Jump Skier']
        if self.wscConnection == True and updatePassRound == True:  # The name came from WSC    
            self.spinBoxPass.setValue(passNumber)
            self.spinBoxRound.setValue(roundNumber)
            self.spinBoxPass.setValue(passNumber)
            self.spinBoxRound.setValue(roundNumber)
            self.spinBoxPass.setValue(passNumber)
            self.spinBoxRound.setValue(roundNumber)
            self.cboxSkierNames.setEnabled(False)
            self.spinBoxRound.setEnabled(False)
            self.spinBoxPass.setEnabled(False)
        else:
            passNumber = self.getPassNumber()
            self.spinBoxPass.setValue(passNumber)
        self.skierNames.sort()
        self.cboxSkierNames.clear()
        self.cboxSkierNames.addItems(self.skierNames)
        index = self.skierNames.index(name)
        self.cboxSkierNames.setCurrentIndex(index)
        self.cboxSkierNames.setCurrentIndex(index)
        self.cboxSkierNames.setCurrentIndex(index)
        filename = os.path.join(os.path.expanduser('~'), 'Documents\\VTM\\VTM Master Names List.txt')
        with open(filename, 'w') as f:
            for skier in self.skierNames:
                f.write(skier + '\n')

    def doesDirExist(self, dirName, dirLoc):
        if os.path.isdir(dirLoc) == False:
            message = 'The ' + dirName + ' at "' + dirLoc + '" does not exist.\n\n'
            message += 'Possible reasons:\n'
            message += '    1.  Directories not configured properly - check settings in "Configurations..."\n'
            message += '    2.  Thumb drive containing Captures was removed from the computer'
            QMessageBox.critical(self, 'Directory Does Not Exist', message, QMessageBox.Ok)
            return False
        else:
            return True      

    def openFrame(self):
        if self.isSetup == True:
            # Step 1: Check to see if the directry exists
            tempString = []
            directoryExist = self.doesDirExist("Saved Frames Directory", self.vidConfig['saveDirectoryFrames'])
            # Step 2: If the directory exists, get the file name
            if directoryExist == True:
                tempString = QFileDialog.getOpenFileName(self, 'Open Frame File',self.vidConfig['saveDirectoryFrames'],"Frame File (*.jpg);;Any File (*.*)")
            else:
                tempString = QFileDialog.getOpenFileName(self, 'Open Frame File', os.path.join(os.path.expanduser('~'),'Documents\\VTM'), "Frame File (*.png);;Any File (*.*)")
            # Step 3: 
            if tempString[0] != "":  # File neme is returned
                frameFile = tempString[0].replace("/", "\\")
                # Step 4: Close current capRplay (if opened)
                if self.capReplayExist == True:
                    if self.capReplay.isOpened() == True:
                        self.capReplay.release()   
                pict = QPixmap(frameFile)
                '''if self.isCapCropped == True:
                    pict = pict.copy(self.capGeom)'''
                self.pix = pict.scaled(self.vidWindow.width(), self.vidWindow.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                if self.isSetup == False:  # If the grid isn't set up yet
                    self.newLoad = True
                else: 
                    self.newLoad = False
                self.frameAlreadySaved = True
                self.sliderBrightness.setEnabled(False)
                self.sliderContrast.setEnabled(False)
                self.capFrame()
        else:
            message = 'Please setup the grid prior to importing a captured picture.  You may adjust the grid after the picture is dispayed by entering Grid Setup again.'
            QMessageBox.information(self, 'Set Up Grid First', message, QMessageBox.Ok)

    def openVidFile(self):
        if self.isSetup == True:
            # Step 1: Check to see if the directry exists
            tempString = []
            directoryExist = self.doesDirExist("Captures Directory", self.vidConfig['saveDirectoryCaps'])
            # Step 2: If the directory exists, get the file name
            if directoryExist == True:
                tempString = QFileDialog.getOpenFileName(self, 'Open Video File',self.vidConfig['saveDirectoryCaps'],"Video File (*.mp4);;Any File (*.*)")
            else:
                tempString = QFileDialog.getOpenFileName(self, 'Open Video File', os.path.join(os.path.expanduser('~'),'Documents\\VTM'), "Video File (*.mp4);;Any File (*.*)")
            # Step 3: 
            if tempString[0] != "":  # File neme is returned
                vidFile = tempString[0].replace("/", "\\")
                # Step 4: Close current capRplay (if opened)
                if self.capReplayExist == True:
                    if self.capReplay.isOpened() == True:
                        self.capReplay.release()
                self.capFileName = vidFile
                if self.isSetup == False:  # If the grid isn't set up yet
                    self.newLoad = True
                else: 
                    self.newLoad = False
                self.sliderBrightness.setEnabled(False)
                self.sliderContrast.setEnabled(False)
                self.measureMode()
        else:
            message = 'Please setup the grid prior to importing a captured video.  You may adjust the grid after the video is dispayed by entering Grid Setup again.'
            QMessageBox.information(self, 'Set Up Grid First', message, QMessageBox.Ok)                
                    
    def getPassNumber(self): # Find the last pass number from the filename and increment the pass number
        # Get name (string) to ckeck for in the video directoty
        name = self.cboxSkierNames.currentText()
        if name == '': # If no name exists, then use 'TrickSkier' as the skier name
            name = 'JumpSkier' + '_R' + str(self.spinBoxRound.value())
        else:
            name = name.replace(' ', '')
            name = name.replace(',', '')    
            name += '_R' + str(self.spinBoxRound.value())
        # Check to see if the name is in the video directory
        e = []
        a = glob.glob(self.vidConfig['saveDirectoryCaps'] + name + '*.*')  # Get list of files with 'name' in filename
        if len(a) > 0:
            for b in a:
                c = b.rsplit('.', 1)[0]
                d = c.rsplit('P', 1)[1]
                e.append(int(d))
            number = max(e)+1
        else:
            number = 1
        return number
    
    def updatePassNumber(self):
        # When the Round is updated, the Pass Number needs to be updated
        if self.wscConnection == False:
            number = self.getPassNumber()
            self.spinBoxPass.setValue(number)
            
    def keyPressEvent(self, event):
        # Nudging video frames right and left
        if event.key() == Qt.Key_Left and self.isSelectFrame == True and self.isSetup == True and self.btnHitRamp.text() != 'Record Jump':
            self.leftNudge()
        if event.key() == Qt.Key_Right and self.isSelectFrame == True and self.isSetup == True and self.btnHitRamp.text() != 'Record Jump':
            self.rightNudge()
        if event.key() == Qt.Key_Escape and self.isCapturing == True:
            # Reset the stop time to when the ESC key was pressed + 0.5 seconds
            self.stopTime = time() + self.secondsAfterESC
            self.fromESC = True
        
        # Moving markers    
        if event.key() == Qt.Key_Left and (self.isSetup == False or self.isMeasuring == True):
            self.nudgeMarker('Left')
        if event.key() == Qt.Key_Right and (self.isSetup == False or self.isMeasuring == True):
            self.nudgeMarker('Right')
        if event.key() == Qt.Key_Up and (self.isSetup == False or self.isMeasuring == True):
            self.nudgeMarker('Up')
        if event.key() == Qt.Key_Down and (self.isSetup == False or self.isMeasuring == True):
            self.nudgeMarker('Down')
            
        # Keyboard shortcuts
        if event.key() == Qt.Key_R:
            if self.btnHitRamp.text() == 'Record Jump':
                self.chooseCapSelectMeasure()
        if event.key() == Qt.Key_S:
            self.reselectFrame()
        if event.key() == Qt.Key_C:
            self.btnCapFrame.setFocus(True)
            self.btnCapFrame.click()
        if event.key() == Qt.Key_N:
            self.nextJump()
       
    def closeEvent(self, event):
        event.ignore()
        self.closeApplication()

    def closeVideo(self):
        if self.cap.isOpened():
            #self.vidWindow.clear()
            try:
                self.cap.release()
                cv2.destroyAllWindows()
            except:
                print('\nError when trying to close the video')
        if self.pvrVid.isOpened():
            self.pvrVid.release()
        return

    def closeApplication(self):
        choice = QMessageBox.question(self, 'Message','Do you really want to exit?',QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            self.writeJumpDataToLog()
            if self.wscConnection == True:
                self.ioConnect.disconnect_from_waterskiconnect()
            try:      #release any video file that may be open
                self.closeVideo()
            except:
                pass
            if self.wscConnection == True:
                self.io.disconnect_from_waterskiconnect()
            QApplication.closeAllWindows()
            QCoreApplication.quit()
            sys.exit()
        else:
            pass
            
    def mousePressEvent(self, event):
        
        super().mousePressEvent(event)
        # Jump marker
        if self.isMeasuring == True and (self.vidReplay.underMouse() == True or self.markerJmp.underMouse() == True):
            if self.isMeasured == False:
                self.btnHitRamp.setStyleSheet('background-color: blue; border: 1px solid black; color: white')
                self.btnHitRamp.setText('Record Jump')
                self.btnHitRamp.setEnabled(True)
                self.btnHitRamp.setFocus(True)
                self.btnClickUp.setEnabled(True)
                self.btnClickDown.setEnabled(True)
                #self.btnCapFrame.setEnabled(False)
                self.btnReselectFrame.setEnabled(True)
                self.jumpLoc = [event.x(), event.y()]
                self.markerJmp.move(event.pos() - self.markerUL.rect().center())
                self.markerJmp.setFocus()
                self.markerJmp.raise_()
                self.markerJmp.show()
        elif self.isSetup == False and (self.vidWindow.underMouse() == True or self.vidReplay.underMouse() == True 
                                        or self.markerUL.underMouse() == True or self.markerUR.underMouse() == True
                                        or self.markerLL.underMouse() == True or self.markerLR.underMouse() == True
                                        or self.markerCk.underMouse() == True):
            if self.chkboxLockGridBuoys.isChecked() == True:
                if self.radbtnUL.isChecked() == True:
                    moveX = event.x() - self.gc['screenUL'][0]
                    moveY = event.y() - self.gc['screenUL'][1]
                elif self.radbtnUR.isChecked() == True:
                    moveX = event.x() - self.gc['screenUR'][0]
                    moveY = event.y() - self.gc['screenUR'][1]
                elif self.radbtnLL.isChecked() == True:
                    moveX = event.x() - self.gc['screenLL'][0]
                    moveY = event.y() - self.gc['screenLL'][1]            
                elif self.radbtnLR.isChecked() == True:
                    moveX = event.x() - self.gc['screenLR'][0]
                    moveY = event.y() - self.gc['screenLR'][1]
                else:
                    moveX = event.x() - self.gc['screenCk'][0]
                    moveY = event.y() - self.gc['screenCk'][1]               
                self.gc['screenUL'] = [self.gc['screenUL'][0] + moveX, self.gc['screenUL'][1] + moveY]
                self.gc['screenUR'] = [self.gc['screenUR'][0] + moveX, self.gc['screenUR'][1] + moveY]
                self.gc['screenLL'] = [self.gc['screenLL'][0] + moveX, self.gc['screenLL'][1] + moveY]
                self.gc['screenLR'] = [self.gc['screenLR'][0] + moveX, self.gc['screenLR'][1] + moveY]
                self.gc['screenCk'] = [self.gc['screenCk'][0] + moveX, self.gc['screenCk'][1] + moveY]
                self.markerUL.move(self.markerUL.pos() + QPoint(moveX, moveY))
                self.markerUR.move(self.markerUR.pos() + QPoint(moveX, moveY))
                self.markerLL.move(self.markerLL.pos() + QPoint(moveX, moveY))
                self.markerLR.move(self.markerLR.pos() + QPoint(moveX, moveY))
                self.markerCk.move(self.markerCk.pos() + QPoint(moveX, moveY))
                self.markerUL.show()
                self.markerUR.show()
                self.markerLL.show()
                self.markerLR.show()
                self.markerCk.show()
            else:
                if self.radbtnUL.isChecked() == True:
                    self.gc['screenUL'] = [event.x(), event.y()]
                    self.markerUL.move(event.pos() - self.markerUL.rect().center())
                    self.markerUL.show()
                elif self.radbtnUR.isChecked() == True:
                    self.gc['screenUR'] = [event.x(), event.y()]
                    self.markerUR.move(event.pos() - self.markerUR.rect().center())
                    self.markerUR.show()
                elif self.radbtnLL.isChecked() == True:
                    self.gc['screenLL'] = [event.x(), event.y()]
                    self.markerLL.move(event.pos() - self.markerLL.rect().center())
                    self.markerLL.show()                
                elif self.radbtnLR.isChecked() == True:
                    self.gc['screenLR'] = [event.x(), event.y()]
                    self.markerLR.move(event.pos() - self.markerLR.rect().center())
                    self.markerLR.show()
                else:
                    self.gc['screenCk'] = [event.x(), event.y()]
                    self.markerCk.move(event.pos() - self.markerCk.rect().center())
                    self.markerCk.show()
        elif self.isSetup == True and self.chkboxVerify.isChecked() == True:            
            self.verifySetup(event.pos())

    def saveGrid(self):
        # Writes the grid setup data to a file
        if self.isSetup == True:
            self.gridDialogSave = QDialog(self)
            self.gridDialogSave.setObjectName('dialogSaveGrid')
            self.gridDialogSave.setWindowTitle('Save Current Grid')
            self.gridDialogSave.resize(743, 292)
            self.gridDialogSave.buttonBox = QDialogButtonBox(self.gridDialogSave)
            self.gridDialogSave.buttonBox.setGeometry(QRect(380, 240, 341, 32))
            self.gridDialogSave.buttonBox.setOrientation(Qt.Horizontal)
            self.gridDialogSave.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
            self.gridDialogSave.buttonBox.setObjectName('buttonBox')
            font = QFont()
            font.setPointSize(12)
            self.gridDialogSave.lblGrid = QLabel(self.gridDialogSave)
            self.gridDialogSave.lblGrid.setGeometry(QRect(20, 30, 121, 31))
            self.gridDialogSave.lblGrid.setText('Save as Grid')      
            self.gridDialogSave.lblGrid.setFont(font)
            self.gridDialogSave.lblGrid.setObjectName('lblGrid')
            self.gridDialogSave.spinboxGridNum = QSpinBox(self.gridDialogSave)
            self.gridDialogSave.spinboxGridNum.setGeometry(QRect(140, 30, 51, 31))
            self.gridDialogSave.spinboxGridNum.setFont(font)
            self.gridDialogSave.spinboxGridNum.setAlignment(Qt.AlignCenter)
            self.gridDialogSave.spinboxGridNum.setMinimum(1)
            self.gridDialogSave.spinboxGridNum.setMaximum(self.vidConfig['numGrids'])
            self.gridDialogSave.spinboxGridNum.setValue(self.gridNum)
            self.gridDialogSave.spinboxGridNum.setObjectName('spinboxGridNum')
            self.gridDialogSave.lblGridDesc = QLabel(self.gridDialogSave)
            self.gridDialogSave.lblGridDesc.setGeometry(QRect(20, 90, 111, 31))
            self.gridDialogSave.lblGridDesc.setFont(font)
            self.gridDialogSave.lblGridDesc.setObjectName('lblGridDesc')
            self.gridDialogSave.lblGridDesc.setText('Description')  
            self.gridDialogSave.txtGridDescription = QLineEdit(self.gridDialogSave)
            self.gridDialogSave.txtGridDescription.setMaxLength(20)
            self.gridDialogSave.txtGridDescription.setGeometry(QRect(140, 90, 191, 31))
            font.setPointSize(11)
            self.gridDialogSave.txtGridDescription.setFont(font)
            self.gridDialogSave.txtGridDescription.setStyleSheet("color: rgb(75, 75, 75);")
            self.gridDialogSave.txtGridDescription.setText(self.gridDescription)
            self.gridDialogSave.txtGridDescription.setObjectName('txtGridDescription')
            self.gridDialogSave.lblDirectory = QLabel(self.gridDialogSave)
            self.gridDialogSave.lblDirectory.setGeometry(QRect(20, 150, 91, 31))
            self.gridDialogSave.lblDirectory.setText('Save As')
            self.gridDialogSave.lblDirectory.setFont(font)
            self.gridDialogSave.lblDirectory.setObjectName('lblDirectory')
            self.gridDialogSave.txtGridFileName = QLineEdit(self.gridDialogSave)
            self.gridDialogSave.txtGridFileName.setGeometry(QRect(140, 150, 501, 31))
            self.gridDialogSave.txtGridFileName.setStyleSheet("color: rgb(75, 75, 75);")
            self.gridDialogSave.txtGridFileName.setFont(font)
            self.gridDialogSave.txtGridFileName.setText(self.gridFileName)
            self.gridDialogSave.setObjectName('txtGridFileName')
            self.gridDialogSave.pushButton = QPushButton(self.gridDialogSave)
            self.gridDialogSave.pushButton.setGeometry(QRect(650, 150, 71, 31))
            font.setPointSize(10)
            self.gridDialogSave.pushButton.setFont(font)
            self.gridDialogSave.pushButton.setObjectName('pushButton')
            self.gridDialogSave.pushButton.setText('Find')
            self.gridDialogSave.pushButton.setFocus()
            self.gridDialogSave.pushButton.clicked.connect(self.getGridFileNameSave)
            self.gridDialogSave.buttonBox.accepted.connect(self.acceptSaveGrid)
            self.gridDialogSave.buttonBox.rejected.connect(self.rejectSaveGrid)
            QMetaObject.connectSlotsByName(self.gridDialogSave)
            self.gridDialogSave.setModal(True)
            self.gridDialogSave.show()
        else:
            message = 'A grid must successfully be set up before it can be saved.'
            QMessageBox.warning(self, 'Grid Cannot Be Saved', message, QMessageBox.Ok)

    def getGridFileNameSave(self):
        reply = QFileDialog.getSaveFileName(self, 'Save Grid File', self.vidConfig['gridsDirectory'] + '\\untitled.json', 'JSON (*.json)')    
        if reply[0] != '':
            self.gridDialogSave.txtGridFileName.setText(reply[0])
            self.gridDialogSave.buttonBox.setFocus()

    def acceptSaveGrid(self):
        # Get the grid number   
        gridNum = self.gridDialogSave.spinboxGridNum.value()
        
        description = self.gridDialogSave.txtGridDescription.text()
        if description == '':
            description = '(no grid description)'
        fname = self.gridDialogSave.txtGridFileName.text()
        checkName = fname  # to be used to check if name exists, below        
        if os.path.dirname(fname) == '':
            fname = os.path.join(self.vidConfig['gridsDirectory'],fname)
        if os.path.splitext(fname)[1] == '':
            fname = fname + '.json'

        # Write to grid setup file
        gridDict = {'gridNum': gridNum, 'gridDescription': description, 'gridFileName': fname, \
                    'gridCoordinates': self.gc, 'img2grd': self.img2grd}
        
        # Update the VTMConfig file with the grid file name
        if gridNum == 1:
            self.vidConfig['gridDescription1'] = description
        elif gridNum == 2:
            self.vidConfig['gridDescription2'] = description
        elif gridNum == 3:
            self.vidConfig['gridDescription3'] = description
        else:
            self.vidConfig['gridDescription4'] = description

        # Write the grid setup file and update the VTMConfig.json
        a = json.dumps(gridDict)
        b = json.dumps(self.vidConfig)
        if checkName == '': # If no file name
            message = 'No file name was provided.  Please try again'
            QMessageBox.warning(self, 'Grid Cannot Be Saved', message, QMessageBox.Ok)
        else:
            try:
                with open(fname, 'w') as f:
                    f.write(a)
                with open(self.configFileName, 'w') as g:
                    g.write(b)
                message = 'Grid ' + str(gridNum) + ' Was Successfully Saved!'            
                QMessageBox.information(self, 'Grid Saved', message, QMessageBox.Ok)
            except:
                message = 'Grid ' + str(gridNum) + ' Was Not Saved.'            
                QMessageBox.warning(self, 'Grid Could Not Be Saved', message, QMessageBox.Ok)
    
            # Update the VTMConfig file with the grid file name
            if gridNum == 1:
                self.vidConfig['gridDescription1'] = description
                self.txtGrid1.setText(description)
            elif gridNum == 2:
                self.vidConfig['gridDescription2'] = description
                self.txtGrid2.setText(description)
            elif gridNum == 3:
                self.vidConfig['gridDescription3'] = description
                self.txtGrid3.setText(description)
            else:
                self.vidConfig['gridDescription4'] = description
                self.txtGrid4.setText(description)
            self.showGridDescription(gridDict['gridDescription'])
            
        self.gridDialogSave.close()
        
    def rejectSaveGrid(self):
        self.gridDialogSave.close()
        
    def loadGrid(self):
        # Reads grid setup data from a file
        self.dialogGridLoad = QDialog(self)
        self.dialogGridLoad.setObjectName('dialogGridLoad')
        self.dialogGridLoad.resize(743, 188)
        self.dialogGridLoad.setWindowTitle('Load Grid')
        self.dialogGridLoad.buttonBox = QDialogButtonBox(self.dialogGridLoad)
        self.dialogGridLoad.buttonBox.setGeometry(QRect(380, 140, 341, 32))
        self.dialogGridLoad.buttonBox.setOrientation(Qt.Horizontal)
        self.dialogGridLoad.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.dialogGridLoad.buttonBox.setObjectName('buttonBox')
        self.dialogGridLoad.lblGrid = QLabel(self.dialogGridLoad)
        self.dialogGridLoad.lblGrid.setGeometry(QRect(20, 30, 121, 31))
        font = QFont()
        font.setPointSize(12)
        self.dialogGridLoad.lblGrid.setFont(font)
        self.dialogGridLoad.lblGrid.setObjectName('lblGrid')
        self.dialogGridLoad.lblGrid.setText('Grid Number')
        self.dialogGridLoad.spinboxGridNum = QSpinBox(self.dialogGridLoad)
        self.dialogGridLoad.spinboxGridNum.setGeometry(QRect(140, 30, 51, 31))
        self.dialogGridLoad.spinboxGridNum.setFont(font)
        self.dialogGridLoad.spinboxGridNum.setAlignment(Qt.AlignCenter)
        self.dialogGridLoad.spinboxGridNum.setMinimum(1)
        self.dialogGridLoad.spinboxGridNum.setMaximum(self.vidConfig['numGrids'])
        self.dialogGridLoad.spinboxGridNum.setObjectName('spinboxGridNum')
        self.dialogGridLoad.lblDirectory = QLabel(self.dialogGridLoad)
        self.dialogGridLoad.lblDirectory.setGeometry(QRect(20, 80, 91, 31))
        self.dialogGridLoad.lblDirectory.setFont(font)
        self.dialogGridLoad.lblDirectory.setObjectName('lblDirectory')
        self.dialogGridLoad.lblDirectory.setText('Grid File')
        self.dialogGridLoad.txtGridFileName = QLineEdit(self.dialogGridLoad)
        self.dialogGridLoad.txtGridFileName.setGeometry(QRect(140, 80, 501, 31))
        font.setPointSize(11)
        self.dialogGridLoad.txtGridFileName.setFont(font)
        self.dialogGridLoad.txtGridFileName.setStyleSheet("color: rgb(75, 75, 75);")
        self.dialogGridLoad.txtGridFileName.setObjectName('txtGridFileName')
        self.dialogGridLoad.btnGet = QPushButton(self.dialogGridLoad)
        self.dialogGridLoad.btnGet.setGeometry(QRect(650, 80, 71, 31))
        self.dialogGridLoad.btnGet.setText('Find')
        font.setPointSize(10)
        self.dialogGridLoad.btnGet.setFont(font)
        self.dialogGridLoad.btnGet.setObjectName('btnGet')
        self.dialogGridLoad.btnGet.clicked.connect(self.getGridFileNameLoad)
        self.dialogGridLoad.btnGet.setFocus()
        self.dialogGridLoad.buttonBox.accepted.connect(self.acceptLoadGrid)
        self.dialogGridLoad.buttonBox.rejected.connect(self.rejectLoadGrid)
        QMetaObject.connectSlotsByName(self.dialogGridLoad)
        self.dialogGridLoad.setModal(True)
        self.dialogGridLoad.show()
        
    def getGridFileNameLoad(self):
        reply = QFileDialog.getOpenFileName(self, 'Load Grid File', self.vidConfig['gridsDirectory'], 'JSON (*.json)')
        if reply[0] != '':
            self.dialogGridLoad.txtGridFileName.setText(reply[0])
            self.dialogGridLoad.buttonBox.setFocus()

    def acceptLoadGrid(self):
        fname = self.dialogGridLoad.txtGridFileName.text()
        if os.path.dirname(fname) == '':
            fname = os.path.join(self.vidConfig['gridsDirectory'],fname)
        if os.path.splitext(fname)[1] == '':
            fname = fname + '.json'
        gridNum = self.dialogGridLoad.spinboxGridNum.value()
        self.getGridData(fname, gridNum, True)
        
    def getGridData(self, fname, gridNum, fromDialog):        
        try:
            with open(fname, 'rt') as f:
                a = f.read()
            gridInfo = json.loads(a)
            
            self.gridNum = gridNum
            self.gridFileName = gridInfo['gridFileName']
            self.gridDescription = gridInfo['gridDescription']
            self.gc = gridInfo['gridCoordinates']
            self.img2grd = gridInfo['img2grd']          
            if self.gridNum == 1:
                self.gc1 = self.gc
                self.img2grd1 = self.img2grd
                self.btnGrid.setText('Grid  1')
                self.vidConfig['gridFileName1'] = fname
                self.vidConfig['gridDescription1'] = self.gridDescription
                self.txtGrid1.home(True)
                self.txtGrid1.setText(self.gridDescription)
                self.txtGrid1.setStyleSheet('background-color:  #fef29a;')
                self.txtGrid2.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid3.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid4.setStyleSheet('background-color:  rgb(255, 255, 255);')
            elif self.gridNum == 2:
                self.gc2 = self.gc
                self.img2grd2 = self.img2grd
                self.btnGrid.setText('Grid  2')
                self.vidConfig['gridFileName2'] = fname
                self.vidConfig['gridDescription2'] = self.gridDescription
                self.txtGrid2.setText(self.gridDescription)                
                self.txtGrid1.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid2.setStyleSheet('background-color:  #fef29a;')
                self.txtGrid3.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid4.setStyleSheet('background-color:  rgb(255, 255, 255);')
            elif self.gridNum == 3:
                self.gc3 = self.gc
                self.img2grd3 = self.img2grd
                self.btnGrid.setText('Grid  3')
                self.vidConfig['gridFileName3'] = fname
                self.vidConfig['gridDescription3'] = self.gridDescription
                self.txtGrid3.setText(self.gridDescription)
                self.txtGrid1.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid2.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid3.setStyleSheet('background-color:  #fef29a;')
                self.txtGrid4.setStyleSheet('background-color:  rgb(255, 255, 255);')
            else:
                self.g4 = self.gc
                self.img2grd4 = self.img2grd
                self.btnGrid.setText('Grid  4')
                self.vidConfig['gridFileName4'] = fname
                self.vidConfig['gridDescription4'] = self.gridDescription
                self.txtGrid4.setText(self.gridDescription)
                self.txtGrid1.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid2.setStyleSheet('background-color:  rgb(255, 255, 255);')                
                self.txtGrid3.setStyleSheet('background-color:  rgb(255, 255, 255);')
                self.txtGrid4.setStyleSheet('background-color:  #fef29a;')
            # Update the config file
            a = json.dumps(self.vidConfig)
            with open(self.configFileName, 'w') as f:
                f.write(a)
            if fromDialog == True: 
                self.dialogGridLoad.close()
            self.txtSurveyULX.setText(str(self.gc['surveyUL'][0]))
            self.txtSurveyULY.setText(str(self.gc['surveyUL'][1]))
            self.txtSurveyURX.setText(str(self.gc['surveyUR'][0]))
            self.txtSurveyURY.setText(str(self.gc['surveyUR'][1]))
            self.txtSurveyLLX.setText(str(self.gc['surveyLL'][0]))
            self.txtSurveyLLY.setText(str(self.gc['surveyLL'][1]))
            self.txtSurveyLRX.setText(str(self.gc['surveyLR'][0]))
            self.txtSurveyLRY.setText(str(self.gc['surveyLR'][1]))  
            self.txtSurveyCkX.setText(str(self.gc['surveyCk'][0]))
            self.txtSurveyCkY.setText(str(self.gc['surveyCk'][1])) 

            # Write the setup parameters to the log after the program is initially launched
            if self.fromLaunch == True:
                if fname != '':
                    self.writeToLog('Setup')
                self.fromLaunch = False

            # Set grid as set up and go to measuring mode
            #self.writeToLog('Setup')    
            self.showGridDescription(self.gridDescription)
            self.getReadyToJump(False)

            # Update VTMConfig.json so the grid will be loaded upon next startup
            try:
                a = json.dumps(self.vidConfig)    
                with open(self.configFileName, 'w') as f:            
                    f.write(a)
            except Exception as e:
                pass
                
            # Repaint the grid buoy markers
            self.chkboxShowBuoys.setChecked(True)
            self.showGridBuoys()
            
        except:
            if fname == '':
                message = 'Grid ' + str(gridNum) + ' is not loaded.  Please load the grid.'
            else:
                message = 'Grid ' + str(gridNum) + ' File Could Not Be Loaded!'
            QMessageBox.warning(self, 'Grid Could Not Be Loaded', message, QMessageBox.Ok)
            if fromDialog == True:
                self.dialogGridLoad.close()
            
    def showGridDescription(self, description):
        if self.lblDescription != None:  # Remove any previous description if one exists
            self.lblDescription.deleteLater()
        #if description != '':
        self.lblDescription = QLabel(self.vidWindow)     
        self.lblDescription.setStyleSheet('background-color: rgba(255,255,255,127); border-width: 1px; color: black;')
        font = QFont()
        font.setPointSize(14)
        self.lblDescription.setFont(font)
        self.lblDescription.setText(' ' + description + ' ')
        x = int((self.vidWindow.width() - self.lblDescription.sizeHint().width()) / 2.0)
        self.lblDescription.setAlignment(Qt.AlignCenter)
        self.lblDescription.move(x, 4)
        self.lblDescription.show()

    def rejectLoadGrid(self):
        self.dialogGridLoad.close()

    def showManual(self):
        try:
            manualFile = open(self.manualFileName, 'rt')
            txt = manualFile.read()
            manualFile.close()
            windowTitle = "Video Tape Measure"
            fontSize = 20
            windowWidth = 1000
            windowHeight = 500
            self.widgetManual = ShowTextWindow(txt, windowTitle, fontSize, windowWidth, windowHeight)
            self.widgetManual.show()
        except:
            dirname = os.path.join(os.path.expanduser('~')) 
            message = 'Could not find file "VTMManual.htm" in directory\n"'+ dirname + '\\Documents\\VTM\\"'
            QMessageBox.information(self, 'No Manual Found', message, QMessageBox.Ok)                  

    def showLicense(self):        
        try:
            licenseFile = open(self.licenseFileName, 'rt')
            txt = licenseFile.read()
            licenseFile.close()
            windowTitle = "Video Tape Measure Licenses"
            fontSize = 11
            windowWidth = 1000
            windowHeight = 400
            self.widgetManual = ShowTextWindow(txt, windowTitle, fontSize, windowWidth, windowHeight)
            self.widgetManual.show()
        except:
            dirname = os.path.join(os.path.expanduser('~')) 
            message = 'Could not find file "VTMLicense.txt" in directory\n"'+ dirname + '\\Documents\\VTM\\"'
            QMessageBox.information(self, 'No License File Found', message, QMessageBox.Ok)
            
    def showHistory(self):        
        try:
            historyFile = open(self.historyFileName, 'rt')
            txt = historyFile.read()
            historyFile.close()
            windowTitle = "Video Tape Measure Release History"
            fontSize = 11
            windowWidth = 1000
            windowHeight = 400
            self.widgetManual = ShowTextWindow(txt, windowTitle, fontSize, windowWidth, windowHeight)
            self.widgetManual.show()
        except:
            dirname = os.path.join(os.path.expanduser('~')) 
            message = 'Could not find file "VTMLicense.txt" in directory\n"'+ dirname + '\\Documents\\VTM\\"'
            QMessageBox.information(self, 'No License File Found', message, QMessageBox.Ok)
        
    def showAbout(self):
        txt = '\n    Video Tape Measure version ' + self.version + '\n\n'
        txt += '    Video Tape Measure (VTM) is approved by the International Waterski and \n'
        txt += '    Wakeboard Federation (IWWF) and the American Water Ski Association (AWSA) \n'
        txt += '    to measure jump distances.\n\n'
        txt += '    VTM was created by Chip Shand with coordination and consultation by Bob Corson, \n'
        txt += '    pre-approval beta testing by Dean Chappell, and IWWF testing by Donal Connolly.\n\n'
        txt += "    Please report any repeatable issues or desired enhancements to slalom@cox.net.\n"
        windowTitle = "About Video Tape Measure"
        fontSize = 12
        windowWidth = 1050
        windowHeight = 360
        self.widgetManual = ShowTextWindow(txt, windowTitle, fontSize, windowWidth, windowHeight)
        self.widgetManual.show()     
        
class PeasInAPodDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy.setVerticalStretch(0)
        self.setStyleSheet('background-color: black')
        self.setWindowIcon(QIcon('VTMIconSmall.ico'))
        self.setWindowTitle('Video Tape Measure')

        self.lblName = QLabel()
        self.lblName.setStyleSheet('background-color: black; color: yellow')
        sizePolicy.setVerticalStretch(1)
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setAlignment(Qt.AlignCenter)

        self.lblMeters = QLabel()
        self.lblMeters.setStyleSheet('background-color: black; color: yellow')
        sizePolicy.setVerticalStretch(3)
        self.lblMeters.setSizePolicy(sizePolicy)
        self.lblMeters.setAlignment(Qt.AlignCenter)
        
        self.lblFeet = QLabel()
        self.lblFeet.setStyleSheet('background-color: black; color: yellow')
        sizePolicy.setVerticalStretch(3)
        self.lblFeet.setSizePolicy(sizePolicy)
        self.lblFeet.setAlignment(Qt.AlignCenter)

        lay = QVBoxLayout(self)
        lay.addWidget(self.lblName)
        lay.addWidget(self.lblMeters)
        lay.addWidget(self.lblFeet)

        self.resize(802, 562)

    def showDisplay(self):
        self.show()
        
    def closeDisplay(self):
        self.close()

    def resizeEvent(self, event):
        fontName = QFont()
        fontDist = QFont()
        fontName.setBold(True)
        fontDist.setBold(True)
        fontName.setPixelSize(self.lblName.height() * 0.8)
        fontDist.setPixelSize(self.lblMeters.height() * 0.8)
        self.lblName.setFont(fontName)
        self.lblMeters.setFont(fontDist) 
        self.lblFeet.setFont(fontDist) 
        
    def setColor(self, color):
        self.lblMeters.setStyleSheet('color: ' + color)
        self.lblFeet.setStyleSheet('color: ' + color) 
        
    def updateDisplay(self, name, meters, feet):
        if name != 'Jump Skier':
            self.lblName.setText(name)
        if len(meters) > 0:
            self.lblMeters.setText(meters + 'm')
        else:
            self.lblMeters.setText('')  
        if len(feet) > 0:
            self.lblFeet.setText(feet + 'ft')
        else:
            self.lblFeet.setText('')
            
class DistanceDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet('background-color: black')
        self.setWindowIcon(QIcon('VTMIconSmall.ico'))
        self.setWindowTitle('Video Tape Measure')
        self.resize(751, 566)
        self.gridLayout = QGridLayout(self)
        
        self.lblName = QLabel(self)
        self.lblName.setText("")
        self.lblName.setStyleSheet('color: yellow')
        self.gridLayout.addWidget(self.lblName, 0, 0, 1, 2)
        
        self.lblDistSmall = QLabel(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.lblDistSmall.sizePolicy().hasHeightForWidth())
        self.lblDistSmall.setSizePolicy(sizePolicy)
        self.lblDistSmall.setText("")
        self.lblDistSmall.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.lblDistSmall.setStyleSheet('color: yellow')
        self.gridLayout.addWidget(self.lblDistSmall, 0, 2, 1, 2)
        
        self.lblDistance = QLabel(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(self.lblDistance.sizePolicy().hasHeightForWidth())
        self.lblDistance.setSizePolicy(sizePolicy)
        self.lblDistance.setText("")
        self.lblDistance.setAlignment(Qt.AlignCenter)
        #self.lblDistance.setStyleSheet('color: yellow')
        self.gridLayout.addWidget(self.lblDistance, 1, 0, 1, 4)
        
        self.showMeters = True      

    def showDisplay(self):
        self.show()
        
    def closeDisplay(self):
        self.close()

    def resizeEvent(self, event):
        font = QFont()
        font.setBold(True)
        font.setPixelSize(self.lblName.height() * 0.8)
        self.lblName.setFont(font)
        font.setPixelSize(self.lblDistSmall.height() * 0.8)
        self.lblDistSmall.setFont(font)
        font.setPixelSize(self.lblDistance.height() * 0.8)
        self.lblDistance.setFont(font)
        
    def updateDisplay(self, name, meters, feet, choice):
        self.name = name
        self.meters = meters
        self.feet = feet
        self.choice = choice
        if choice == 'flashmob':
            millisecs = 1500
            self.timer = QTimer()
            self.timer.setTimerType(Qt.PreciseTimer)
            self.timer.timeout.connect(self.display)
            self.timer.start(millisecs)
        elif choice == 'bigfoot':
            self.showMeters = False
            self.showFeet = True
            self.display()
        else:
            self.showMeters = True
            self.shwMeters = False
            self.display()
            
    def setColor(self, color):
        self.lblDistance.setStyleSheet('color: ' + color)      

    def display(self):
        if len(self.meters) > 0:
            if self.name != 'Jump Skier':
                self.lblName.setText(self.name)
            if self.showMeters == True:
                #self.lblDistance.setText(self.meters + 'm')
                self.lblDistance.setText(self.meters)
                self.lblDistSmall.setText(self.feet + 'ft')
                self.showMeters = False
            else:
                #self.lblDistance.setText(self.feet + 'ft')
                self.lblDistance.setText(self.feet)
                self.lblDistSmall.setText(self.meters + 'm')
                self.showMeters = True
        else:
            self.lblDistance.setText(self.meters)
            self.lblDistance.setText(self.feet)

class ShowTextWindow(QWidget):
    def __init__(self, txt, windowTitle, fontSize, width, height, parent=None):
        super(ShowTextWindow, self).__init__(parent)
        if getattr(sys, 'frozen', False): #If frozen with cx_Freeze
            self.homePath = os.path.dirname(sys.executable)
        else: # Otherwise, if running as a script (e.g., within Spyder)
            self.homePath = os.path.dirname(__file__)        
        self.iconFileName = os.path.join(self.homePath, 'VTMIconSmall.ico')
        self.setWindowIcon(QIcon(self.iconFileName))  
        self.setWindowTitle(windowTitle)
        self.setGeometry(100, 100, width, height)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.close)        
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setFontFamily("Consolas")
        self.textBrowser.setFontPointSize(fontSize)
        self.textBrowser.append(txt)
        self.textBrowser.moveCursor(QTextCursor.Start)         
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.addWidget(self.textBrowser)
        self.verticalLayout.addWidget(self.buttonBox)
        
class MouseTracker(QObject):
    positionChanged = pyqtSignal(QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QEvent.MouseMove:
            self.positionChanged.emit(e.pos())
        return super().eventFilter(o, e)
    
class DownloadWidget(QDialog):
    def __init__(self, url, filename, *args, **kwargs):
        super(DownloadWidget, self).__init__(*args, **kwargs)
        if getattr(sys, 'frozen', False): #If frozen with cx_Freeze
            self.homePath = os.path.dirname(sys.executable)
        else: # Otherwise, if running as a script (e.g., within Spyder)
            self.homePath = os.path.dirname(__file__)        
        self.iconFileName = os.path.join(self.homePath, 'VTMIconSmall.ico')
        self.setWindowIcon(QIcon(self.iconFileName))  
        self.setWindowTitle('Download Status')
        self.url = url
        self.filename = filename
        layout = QHBoxLayout(self)
        # Increase progress bar
        self.progressBar = QProgressBar(self, minimumWidth=400)
        self.progressBar.setValue(0)
        layout.addWidget(self.progressBar)
        filesize = requests.get(self.url, stream=True).headers['Content-Length']
        fileobj = open(self.filename, 'wb')
        #### Create a download thread
        self.downloadThread = downloadThread(self.url, filesize, fileobj, buffer=10240)
        self.downloadThread.download_process_signal.connect(self.set_progressbar_value)
        self.downloadThread.start()

    # Setting progress bar
    def set_progressbar_value(self, value):
        self.progressBar.setValue(value)
        if value == 100:
            QMessageBox.information(self, ' ', "Download success!")
            self.close()
            return

class downloadThread(QThread):
    download_process_signal = pyqtSignal(int)                        #Create signal

    def __init__(self, url, filesize, fileobj, buffer):
        super(downloadThread, self).__init__()
        self.url = url
        self.filesize = filesize
        self.fileobj = fileobj
        self.buffer = buffer

    def run(self):
        try:
            rsp = requests.get(self.url, stream=True)                #Streaming download mode
            offset = 0
            for chunk in rsp.iter_content(chunk_size=self.buffer):
                if not chunk: break
                self.fileobj.seek(offset)                            #Setting Pointer Position
                self.fileobj.write(chunk)                            #write file
                offset = offset + len(chunk)
                proess = offset / int(self.filesize) * 100
                self.download_process_signal.emit(int(proess))        #Sending signal
            #######################################################################
            self.fileobj.close()    #Close file
            self.exit(0)            #Close thread
        except:
            pass

class vidOptions(QDialog, VTMConfig.Ui_dialogConfig):
    def __init__(self, vidConfig):
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
        self.vidConfig = vidConfig # a dictionary of default parameters defined in main()

        # Add a few more enhancements to the popup window
        if getattr(sys, 'frozen', False): #If the script is frozen 
            self.homePath = os.path.dirname(sys.executable)
        else: # Otherwise, if running as a script (e.g., within Spyder)
            self.homePath = os.path.dirname(__file__)
        self.grpboxGrids.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxJumpColors.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxGridColors.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxHomoGridColors.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxDiscipline.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxSaveFrames.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxSaveCaps.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxGridsDirectory.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxPVRDirectory.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxFPS.setStyleSheet("QGroupBox{border: 1px solid gray;}")
        self.grpboxCapLength.setStyleSheet("QGroupBox{border: 1px solid gray;}") 
         
        # Set connections
        self.radbtnGrids1.toggled.connect(self.getNumGrids)
        self.radbtnGrids2.toggled.connect(self.getNumGrids)
        self.radbtnGrids3.toggled.connect(self.getNumGrids)
        self.radbtnGrids4.toggled.connect(self.getNumGrids)
        self.radbtnJumpRed.toggled.connect(self.getJumpMarkerColor)
        self.radbtnJumpBlack.toggled.connect(self.getJumpMarkerColor)
        self.radbtnJumpYellow.toggled.connect(self.getJumpMarkerColor)
        self.radbtnGridRed.toggled.connect(self.getGridMarkerColor)
        self.radbtnGridBlack.toggled.connect(self.getGridMarkerColor)
        self.radbtnGridYellow.toggled.connect(self.getGridMarkerColor)
        self.radbtnHomoGridRed.toggled.connect(self.getHomoGridColor)
        self.radbtnHomoGridBlack.toggled.connect(self.getHomoGridColor)
        self.radbtnHomoGridYellow.toggled.connect(self.getHomoGridColor)        
        self.radbtnWaterski.toggled.connect(self.getDiscipline)
        self.radbtnSitski.toggled.connect(self.getDiscipline)
        self.radbtnBarefoot.toggled.connect(self.getDiscipline)        
        self.grpboxSaveFrames.toggled.connect(self.getSaveFramesBool)
        self.radbtnAskFrames.toggled.connect(self.askBeforeSavingFrames)
        self.radbtnNoAskFrames.toggled.connect(self.askBeforeSavingFrames)
        self.btnSaveDirectoryFrames.clicked.connect(self.getSaveDirectoryFrames)
        self.grpboxSaveCaps.toggled.connect(self.getSaveCapsBool)
        self.grpboxPVRDirectory.toggled.connect(self.getPVRBool)
        self.radbtnAskCaps.toggled.connect(self.askBeforeSavingCaps)
        self.radbtnNoAskCaps.toggled.connect(self.askBeforeSavingCaps)
        self.btnSaveDirectoryCaps.clicked.connect(self.getSaveDirectoryCaps)
        self.btnGridsDirectory.clicked.connect(self.getGridsDirectory)
        self.btnPVRDirectory.clicked.connect(self.getPVRDirectory)
        self.radbtn05fps.toggled.connect(self.getFPS)
        self.radbtn10fps.toggled.connect(self.getFPS)
        self.radbtn15fps.toggled.connect(self.getFPS)
        self.radbtn3Sec.toggled.connect(self.getCaptureLength)
        self.radbtn5Sec.toggled.connect(self.getCaptureLength)
        self.radbtn7Sec.toggled.connect(self.getCaptureLength)
        self.buttonBox.accepted.connect(self.acceptOptionChanges)
        self.buttonBox.rejected.connect(self.rejectOptionChanges)
        
        #Initialize parameters from vidConfig
        self.numGrids = self.vidConfig['numGrids']
        self.jumpMarkColor = self.vidConfig['jumpMarkColor']
        self.gridMarkColor = self.vidConfig['gridMarkColor']
        self.homoGridColor = self.vidConfig['homoGridColor']
        self.saveFrames = self.vidConfig['saveFrames']
        self.askSaveFrames = self.vidConfig['askSaveFrames']
        self.saveDirectoryFrames = self.vidConfig['saveDirectoryFrames']
        self.saveCaps = self.vidConfig['saveCaps']
        self.askSaveCaps = self.vidConfig['askSaveCaps']
        self.saveDirectoryCaps = self.vidConfig['saveDirectoryCaps']
        self.gridsDirectory = self.vidConfig['gridsDirectory']
        self.pvr = self.vidConfig['pvr']
        self.pvrDirectory = self.vidConfig['pvrDirectory']
        self.framesPerSec = self.vidConfig['framesPerSec']
        self.capLength = self.vidConfig['capLength']
        self.cameraID = self.vidConfig['cameraID']
        self.discipline = self.vidConfig['discipline']
        
        # Set the radio buttons and values in the popup window
        if self.numGrids == 1:
            self.radbtnGrids1.setChecked(True)
        elif self.numGrids == 2:
            self.radbtnGrids2.setChecked(True)
        elif self.numGrids == 3:
            self.radbtnGrids3.setChecked(True)
        else:
            self.radbtnGrids4.setChecked(True)
        if self.vidConfig['jumpMarkColor'] == 'red':
            self.radbtnJumpRed.setChecked(True)
        elif self.vidConfig['jumpMarkColor'] == 'black':
            self.radbtnJumpBlack.setChecked(True)
        elif self.vidConfig['jumpMarkColor'] == 'yellow':
            self.radbtnJumpYellow.setChecked(True)
        else:
            self.radbtnJumpGreen.setChecked(True)            
        if self.vidConfig['gridMarkColor'] == 'red':
            self.radbtnGridRed.setChecked(True)
        elif self.vidConfig['gridMarkColor'] == 'black':
            self.radbtnGridBlack.setChecked(True)
        elif self.vidConfig['gridMarkColor'] == 'yellow':
            self.radbtnGridYellow.setChecked(True)
        else:
            self.radbtnGridGreen.setChecked(True)            
        if self.vidConfig['homoGridColor'] == 'red':
            self.radbtnHomoGridRed.setChecked(True)
        elif self.vidConfig['homoGridColor'] == 'black':
            self.radbtnHomoGridBlack.setChecked(True)
        elif self.vidConfig['homoGridColor'] == 'yellow':
            self.radbtnHomoGridYellow.setChecked(True)
        else:
            self.radbtnHomoGridGreen.setChecked(True)        
        if self.discipline == 'waterski':
            self.radbtnWaterski.setChecked(True)
        elif self.discipline == 'sitski':
            self.radbtnSitski.setChecked(True)
        else:
            self.radbtnBarefoot.setChecked(True)
        if self.vidConfig['saveFrames'] == True:
            self.grpboxSaveFrames.setChecked(True)
            self.radbtnAskFrames.setEnabled(True)
            self.radbtnNoAskFrames.setEnabled(True)
            self.lblSaveDirectoryFrames.setEnabled(True)
            self.txtSaveDirectoryFrames.setEnabled(True)
            self.btnSaveDirectoryFrames.setEnabled(True)
            self.txtSaveDirectoryFrames.setText(self.vidConfig['saveDirectoryFrames'])
        else:
            self.grpboxSaveFrames.setChecked(False)
            self.radbtnAskFrames.setEnabled(False)
            self.radbtnNoAskFrames.setEnabled(False)
            self.lblSaveDirectoryFrames.setEnabled(False)
            self.txtSaveDirectoryFrames.setEnabled(False)
            self.btnSaveDirectoryFrames.setEnabled(False)
            self.txtSaveDirectoryFrames.setText(self.vidConfig['saveDirectoryFrames'])
        if self.askSaveFrames == True:
            self.radbtnAskFrames.setChecked(True)
        else:
            self.radbtnNoAskFrames.setChecked(True)
        if self.vidConfig['saveCaps'] == True:
            self.grpboxSaveCaps.setChecked(True)
            self.radbtnAskCaps.setEnabled(True)
            self.radbtnNoAskCaps.setEnabled(True)
            self.lblSaveDirectoryCaps.setEnabled(True)
            self.txtSaveDirectoryCaps.setEnabled(True)
            self.btnSaveDirectoryCaps.setEnabled(True)
            self.txtSaveDirectoryCaps.setText(self.vidConfig['saveDirectoryCaps'])
        else:
            self.grpboxSaveCaps.setChecked(False)
            self.radbtnAskCaps.setEnabled(False)
            self.radbtnNoAskCaps.setEnabled(False)
            self.lblSaveDirectoryCaps.setEnabled(False)
            self.btnSaveDirectoryCaps.setEnabled(False)    
            self.txtSaveDirectoryCaps.setText(self.vidConfig['saveDirectoryCaps'])
        if self.askSaveCaps == True:
            self.radbtnAskCaps.setChecked(True)
        else:
            self.radbtnNoAskCaps.setChecked(True)
        self.txtGridsDirectory.setText(self.vidConfig['gridsDirectory'])
        if self.pvr == True:
            self.grpboxPVRDirectory.setChecked(True)
        else:
            self.grpboxPVRDirectory.setChecked(False)
        self.txtPVRDirectory.setText(self.vidConfig['pvrDirectory'])
        if self.vidConfig['framesPerSec'] == 5:
            self.radbtn05fps.setChecked(True)
        elif self.vidConfig['framesPerSec'] == 10:
            self.radbtn10fps.setChecked(True)
        else:
            self.radbtn15fps.setChecked(True)
        if self.vidConfig['capLength'] == 3:
            self.radbtn3Sec.setChecked(True)
        elif self.vidConfig['capLength'] == 5:
            self.radbtn5Sec.setChecked(True)   
        else:
            self.radbtn7Sec.setChecked(True)
            
        #cameraList = self.getCameraList()
        cameraList = get_MF_devices()
        for i in range(len(cameraList)):
            self.comboboxVidSource.addItem(cameraList[i])
        if len(cameraList) == 0:
            QMessageBox.critical(self, 'Oops!','No camera found!  Attach a camera.',QMessageBox.Ok)
        else:
            if len(cameraList) == 0 or len(cameraList) < self.cameraID + 1:  # The camera is not attached to the computer.  Default to port 0.
                self.cameraID = 0
            index = self.comboboxVidSource.findText(cameraList[self.cameraID], Qt.MatchFixedString)
            if index >= 0:
                self.comboboxVidSource.setCurrentIndex(index)
            
    def getNumGrids(self):
        if self.radbtnGrids1.isChecked() == True:
            self.numGrids = 1
        elif self.radbtnGrids2.isChecked() == True:
            self.numGrids = 2
        elif self.radbtnGrids3.isChecked() == True:
            self.numGrids = 3
        else:
            self.numGrids = 4
    def getJumpMarkerColor(self):
        if self.radbtnJumpRed.isChecked() == True:
            self.jumpMarkColor = 'red'
        elif self.radbtnJumpBlack.isChecked() == True:
            self.jumpMarkColor = 'black'
        elif self.radbtnJumpYellow.isChecked() == True:
            self.jumpMarkColor = 'yellow'
        else:
            self.jumpMarkColor = '#00ea00' 
            
    def getGridMarkerColor(self):
        if self.radbtnGridRed.isChecked() == True:
            self.gridMarkColor = 'red'
        elif self.radbtnGridBlack.isChecked() == True:
            self.gridMarkColor = 'black'
        elif self.radbtnGridYellow.isChecked() == True:
            self.gridMarkColor = 'yellow'
        else:
            self.gridMarkColor = '#00ea00'

    def getHomoGridColor(self):
        if self.radbtnHomoGridRed.isChecked() == True:
            self.homoGridColor = 'red'
        elif self.radbtnHomoGridBlack.isChecked() == True:
            self.homoGridColor = 'black'
        elif self.radbtnHomoGridYellow.isChecked() == True:
            self.homoGridColor = 'yellow'
        else:
            self.homoGridColor = '#00ea00'
            
    def getDiscipline(self):
        if self.radbtnWaterski.isChecked() == True:
            self.discipline = 'waterski'
        elif self.radbtnSitski.isChecked() == True:
            self.discipline = 'sitski'
        else:
            self.discipline = 'barefoot'
            
    def getSaveFramesBool(self):
        if self.grpboxSaveFrames.isChecked() == True:
            self.saveFrames = True
            self.radbtnAskFrames.setEnabled(True)
            self.radbtnNoAskFrames.setEnabled(True)
            self.lblSaveDirectoryFrames.setEnabled(True)
            self.txtSaveDirectoryFrames.setEnabled(True)
            self.btnSaveDirectoryFrames.setEnabled(True)
        else:
            self.saveFrames = False
            self.radbtnAskFrames.setEnabled(False)
            self.radbtnNoAskFrames.setEnabled(False)
            self.lblSaveDirectoryFrames.setEnabled(False)
            self.txtSaveDirectoryFrames.setEnabled(False)
            self.btnSaveDirectoryFrames.setEnabled(False)
                    
    def askBeforeSavingFrames(self):
        if self.radbtnAskFrames.isChecked() == True:
            self.askSaveFrames = True
        else:
            self.askSaveFrames = False

    def getSaveDirectoryFrames(self):
        dirName = self.getDirectory()
        if dirName != "":
            dirName = self.checkIfDirExists(dirName, 'Measured Frames')
            self.saveDirectoryFrames = dirName
            self.txtSaveDirectoryFrames.setText(dirName)    

    def getSaveCapsBool(self):
        if self.grpboxSaveCaps.isChecked() == True:
            self.saveCaps = True
            self.radbtnAskCaps.setEnabled(True)
            self.radbtnNoAskCaps.setEnabled(True)
            self.lblSaveDirectoryCaps.setEnabled(True)
            self.txtSaveDirectoryCaps.setEnabled(True)
            self.btnSaveDirectoryCaps.setEnabled(True)
        else:
            self.radbtnAskCaps.setEnabled(False)
            self.saveCaps = False
            self.radbtnNoAskCaps.setEnabled(False)
            self.lblSaveDirectoryCaps.setEnabled(False)
            self.txtSaveDirectoryCaps.setEnabled(False)
            self.btnSaveDirectoryCaps.setEnabled(False)            
            
    def getPVRBool(self):
        if self.grpboxPVRDirectory.isChecked() == True:
            self.pvr = True
        else:
            self.pvr = False

    def askBeforeSavingCaps(self):
        if self.radbtnAskCaps.isChecked() == True:
            self.askSaveCaps = True
        else:
            self.askSaveCaps = False

    def getSaveDirectoryCaps(self):
        dirName = self.getDirectory()
        if dirName != "":
            dirName = self.checkIfDirExists(dirName, 'Captured Videos')
            self.saveDirectoryFrames = dirName
            self.txtSaveDirectoryCaps.setText(dirName)
                        
    def getGridsDirectory(self):
        dirName = self.getDirectory()
        if dirName != "":
            dirName = self.checkIfDirExists(dirName, 'Grids')
            self.gridsDirectory = dirName
            self.txtGridsDirectory.setText(dirName)

    def getPVRDirectory(self):
        dirName = self.getDirectory()
        if dirName != "":
            dirName = self.checkIfDirExists(dirName, 'PVR')
            self.pvrDirectory = dirName
            self.txtPVRDirectory.setText(dirName)    
                        
    def getFPS(self):
        if self.radbtn05fps.isChecked() == True:
            self.framesPerSec = 5
        elif self.radbtn10fps.isChecked() == True:
            self.framesPerSec = 10        
        if self.radbtn15fps.isChecked() == True:
            self.framesPerSec = 15
            
    def getCaptureLength(self):
        if self.radbtn3Sec.isChecked() == True:
            self.capLength = 3
        elif self.radbtn5Sec.isChecked() == True:
            self.capLength = 5
        else:
            self.capLength = 7
           
    def acceptOptionChanges(self):
        # Update the configuration JSON file
        self.vidConfig['numGrids'] = self.numGrids
        self.vidConfig['jumpMarkColor'] = self.jumpMarkColor
        self.vidConfig['gridMarkColor'] = self.gridMarkColor
        self.vidConfig['homoGridColor'] = self.homoGridColor
        self.vidConfig['discipline'] = self.discipline
        self.vidConfig['saveFrames'] = self.saveFrames
        self.vidConfig['askSaveFrames'] = self.askSaveFrames
        if self.grpboxSaveFrames.isChecked() == True:
            dirName = self.checkIfDirExists(self.txtSaveDirectoryFrames.text(), 'Saved Frames')
            self.vidConfig['saveDirectoryFrames'] = dirName
        self.vidConfig['saveCaps'] = self.saveCaps
        self.vidConfig['askSaveCaps'] = self.askSaveCaps
        if self.grpboxSaveCaps.isChecked() == True:
            dirName = self.checkIfDirExists(self.txtSaveDirectoryCaps.text(), 'Saved Videos')
            self.vidConfig['saveDirectoryCaps'] = dirName
        dirName = self.checkIfDirExists(self.txtGridsDirectory.text(), 'Grids')
        self.vidConfig['gridsDirectory'] = self.txtGridsDirectory.text()
        self.vidConfig['pvr'] = self.pvr
        if self.grpboxPVRDirectory.isChecked() == True:
            dirName = self.checkIfDirExists(self.txtPVRDirectory.text(), 'PVR')
            self.vidConfig['pvrDirectory'] = dirName
        self.vidConfig['framesPerSec'] = self.framesPerSec
        self.vidConfig['capLength'] = self.capLength
        camID = self.comboboxVidSource.currentIndex()
        self.vidConfig['cameraID'] = camID
        a = json.dumps(self.vidConfig)   
        configFileName = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\VTMConfig.json')
        try:
            with open(configFileName, 'w') as f:            
                f.write(a)  
        except:
            message = 'Could not save the configuration file.'
            QMessageBox.warning(self, 'Configuration File Not Saved!', message, QMessageBox.Ok)
        
    def rejectOptionChanges(self):
        pass
            
    def checkIfDirExists(self, dirName, name):
        # mediaFlag = 1 means that the directory being passed if for the media card
        if os.path.isdir(dirName) == False and dirName:
            try:
                message = dirName + ' does not exist.  It will be created.'
                QMessageBox.information(self, 'Will Create Directory', message, QMessageBox.Ok)
                os.mkdir(dirName)
            except:
                msgBox = QMessageBox()
                message = name + ' Directory "' + dirName + '" does not exist.\n\n'
                dirName = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\' + name)
                message += 'The new save location will be ' + dirName
                msgBox.warning(self, 'Folder Not Found', message, QMessageBox.Ok)
                if os.path.isdir(dirName) == False:
                    try:
                        os.mkdir(dirName)
                    except:
                        message = 'Could not find create directory ' +  os.path.join(os.path.expanduser('~') + 'Documents\\VTM\\') + '".\n'
                        message += 'If VTM does not crash after this window is closed, close VTM and check to make sure '
                        message += 'the directory exists.'
                        QMessageBox.critical(self, 'Could Not Create Directory', message, QMessageBox.Ok)
        if dirName.endswith('\\') == False:
            if dirName == os.path.join(os.path.expanduser('~'),'Documents\\VTM'):
                pass
            else:
                dirName += '\\'               
        return dirName

    def getDirectory(self):
        response = QFileDialog.getExistingDirectory(self, caption = "Select Directory", directory = os.path.expanduser('~') + '\\Documents\\VTM')
        if response != "":
            string1 = response + '\\'  
            string2 =  QDir.toNativeSeparators(string1)
        else:
            string2 = ""
        return string2
    
    def closeEvent(self, event):
        #event.ignore()
        choice = QMessageBox.question(self, 'Save Configurations Changes','Do you want to save the current configurations?',QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            self.acceptOptionChanges()
        else:
            self.rejectOptionChanges()
        self.close()

class NoConnectionToWSC(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        if getattr(sys, 'frozen', False): #If frozen baseline
            homePath = os.path.dirname(sys.executable)
        else: # Otherwise, if running as a script (e.g., within Spyder)
            homePath = os.path.dirname(__file__)
        iconFileName = os.path.join(homePath, 'VTMIconSmall.ico')
        msg = '\nCannot connect to WaterSkiConnect!!!\n\n'
        msg += 'Please try the following:\n'
        msg += '   1. Check that you have an internet connection \n'
        msg += '   2. Check that the information you provided is correct.\n'
        msg += '   3. Connection may already exist. Disconnect then try again.\n'
        msgBox = QMessageBox()
        msgBox.setText(msg)
        msgBox.setWindowIcon(QIcon(iconFileName))
        msgBox.critical(self, 'Cannot Connect', msg, QMessageBox.Ok)
        
class EventData(QDialog, WSCDialog.Ui_Dialog):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically

class WSC_Connect_Disconnect():
    
    def __init__(self, a, sio):
        self.a = a
        self.sio = sio
        self.sio.event(self.connect_confirm)
    
    def is_ewscdata_on(self, url):
        # If can't connect within one second, assume no internet connection
        try:
            urlopen(url, timeout=1)
            return True
        except: 
            return False
        
    def get_waterskiconnect_data(self):
        dlg = QDialog()
        dlg.setWindowTitle('WaterSkiConnect Setup Data')
        dlg.resize(700,500)
        dlg.move(QApplication(sys.argv).primaryScreen().rect().center())
    
    def connect_to_waterskiconnect(self):    
        url = 'http://ewscdata.com:40000/'  # waterskiconnect operational server
        #url = 'http://waterskiconnect.com:40000/'  # waterskiconnect test server?
        #url = 'http://localhost:5000'  # local test erver
        #connection = is_ewscdata_on(url)
        self.a.wscConnection = True
        try:
            self.sio.connect(url, transports='websocket')
            isConnected = True
        except:
            isConnected = False  # Could not establish a connection
            self.a.wscConnection = False
        if isConnected == True:  # Connection to the server was successful
            eventForm = EventData()
            eventForm.txtEventID.setFocus(True)
            eventForm.exec_()
            eventID = eventForm.txtEventID.text()
            eventID = eventID.upper()
            while eventID[-1:].isalpha() == True:
                eventID = eventID[:-1]
            data = json.dumps({'loggingdetail': 'no',
                    'mode': 'Tournament',
                    'eventid': eventID,
                    'eventsubid': eventForm.txtEventSubID.text(),
                    'provider': 'Shand',
                    'application': 'VTM',
                    'application_key': 'BA1DEB07-42C0-41B8-B5BE-B84FB31128AD',
                    'version': self.a.version,
                    'username': 'slalom@cox.net'})        
            self.sio.emit('manual_connection_parameter', data)
            self.a.cboxSkierNames.setStyleSheet('background-color:  black; color: white;')
            self.a.spinBoxPass.setStyleSheet('background-color:  black; color: white;')
            self.a.spinBoxRound.setStyleSheet('background-color:  black; color: white;')      
        else:   #  Connection to server failed
            NoConnectionToWSC()
            
    def connect_confirm(self, data):
        data = json.loads(data)
        self.a.pin = data['pin']
        self.a.writeToLog(what = 'WaterSkiConnect', wsc = ('connected', self.sio.sid, data))
        '''print('\nConnected!!!')
        print('Data = ', data)
        print('Type = ', type(data))
        print('   {:16}{}'.format('Session ID', self.sio.sid))
        print('   {:16}{}'.format('Tournament ID', data['eventId']))
        print('   {:16}{}'.format('Sub ID', data['eventSubId']))
        print('   {:16}{}'.format('Daily PIN', data['pin']))'''
        
    def disconnect_from_waterskiconnect(self):
        if self.a.wscConnection == True:
            self.sio.disconnect()
            self.a.cboxSkierNames.setStyleSheet('background-color: white; color: black;')
            self.a.spinBoxPass.setStyleSheet('background-color: white; color: black;')
            self.a.spinBoxRound.setStyleSheet('background-color: white; color: black;')
            self.a.cboxSkierNames.setEnabled(True)
            self.a.spinBoxPass.setEnabled(True)
            self.a.spinBoxRound.setEnabled(True)
            self.a.writeToLog(what = 'WaterSkiConnect', wsc = ('disconnected', "", ""))
        self.a.wscConnection = False
        self.a.pin = None
            
class WSC_Pass_Data():
    
    def __init__(self, b, sio):
        self.b = b
        self.sio = sio
        self.sio.event(self.pass_data)
        
    def pass_data(self, data):
        self.b.passData = json.loads(data)    
        self.b.updateSkierNames(name = self.b.passData['athleteName'], 
                                division = self.b.passData['athleteDivision'],
                                appendFlag = True,
                                roundNumber = self.b.passData['round'], 
                                passNumber = self.b.passData['passNumber'], 
                                source = 'pass_data')
    
    def send_jump_score(self, data):
        self.sio.emit('jumpmeasurement_score', data)
        
class WSC_Start_List():
    
    def __init__(self, c, sio):
        self.c = c
        self.sio = sio
        self.sio.event(self.start_list)

    def start_list(self, data):
        self.c.gatherStartList(data)
        
def main():
    # Create VTM folder if it doesn't already exist
    if os.path.isdir(os.path.expanduser('~') + '\\Documents\\VTM') == False:
        os.mkdir(os.path.expanduser('~') + '\\Documents\\VTM') 
    # Get configuration parameters
    configDir = os.path.join(os.path.expanduser('~'),'Documents\\VTM')
    if not os.path.exists(configDir):
        os.makedirs(configDir)    
    namesFile = Path(os.path.join(configDir, 'VTM Master Names List.txt'))
    if not namesFile.is_file():
        open(os.path.join(configDir, 'VTM Master Names List.txt'), 'a').close()
    configFileName =  os.path.join(configDir,'VTMConfig.json')
    # Get configuration parameters
    try: # If JSON file exists, read the configuration parameters    
        with open(configFileName, 'rt') as f:
            a = f.read()
        vtmInit = json.loads(a)
        if 'numGrids' not in vtmInit:
            vtmInit['numGrids'] = 1
        if 'jumpMarkColor' not in vtmInit:
            vtmInit['jumpMarkColor'] = 'red'
        if 'gridMarkColor' not in vtmInit:
            vtmInit['gridMarkColor'] = 'black'
        if 'homoGridColor' not in vtmInit:
            vtmInit['homoGridColor'] = 'red'
        if 'saveFrames' not in vtmInit:
            vtmInit['saveFrames'] = True
        if 'askSaveFrames' not in vtmInit:
            vtmInit['askSaveFrames'] = True
        if 'saveDirectoryFrames' not in vtmInit:
            vtmInit['saveDirectoryFrames'] = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\Saved Frames')
        if 'saveCaps' not in vtmInit:
            vtmInit['saveCaps'] = True
        if 'askSaveCaps' not in vtmInit:
            vtmInit['askSaveCaps'] = True
        if 'saveDirectoryCaps' not in vtmInit:
            vtmInit['saveDirectoryCaps'] = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\Saved Captures')
        if 'gridsDirectory' not in vtmInit:
            vtmInit['gridsDirectory'] = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\Grids')
        if 'pvr' not in vtmInit:
            vtmInit['pvr'] = False
        if 'pvrDirectory' not in vtmInit:
            vtmInit['pvrDirectory'] = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\PVR')
        if 'cameraID' not in vtmInit:
            vtmInit['cameraID'] = 0    
        if 'framesPerSec' not in vtmInit:
            vtmInit['framesPerSec'] = 10
        if 'capLength' not in vtmInit:
            vtmInit['capLength'] = 5
        if 'discipline' not in vtmInit:
            vtmInit['discipline'] = 'waterski'
        if 'gridFileName1' not in vtmInit:
            vtmInit['gridFileName1'] = ''
        if 'gridFileName2' not in vtmInit:
            vtmInit['gridFileName2'] = ''
        if 'gridFileName3' not in vtmInit:
            vtmInit['gridFileName3'] = ''
        if 'gridFileName4' not in vtmInit:
            vtmInit['gridFileName4'] = ''  
        if 'gridDescription1' not in vtmInit:
            vtmInit['gridDescription1'] = ''
        if 'gridDescription2' not in vtmInit:
            vtmInit['gridDescription2'] = ''
        if 'gridDescription3' not in vtmInit:
            vtmInit['gridDescription3'] = ''
        if 'gridDescription4' not in vtmInit:
            vtmInit['gridDescription4'] = ''      
    except: # If JSON does not exist, create deault configuration parameters and write them to a file
        saveDirectoryFrames = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\Saved Frames')
        saveDirectoryCaps = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\Saved Captures')
        gridsDirectory = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\Grids')
        pvrDirectory = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\PVR')
        if not os.path.exists(saveDirectoryFrames):
            os.makedirs(saveDirectoryFrames)
        if not os.path.exists(saveDirectoryCaps):
            os.makedirs(saveDirectoryCaps)
        if not os.path.exists(gridsDirectory):
            os.makedirs(gridsDirectory)
        if not os.path.exists(pvrDirectory):
            os.makedirs(pvrDirectory)        
        os.chdir(configDir)
        vtmInit = {'numGrids': 1, 'jumpMarkColor': 'red', 'gridMarkColor': 'red', 'homoGridColor':'red', 
                   'saveFrames': True, 'askSaveFrames': True, 'saveDirectoryFrames': saveDirectoryFrames, 
                   'saveCaps': True, 'askSaveCaps': True, 'saveDirectoryCaps': saveDirectoryCaps, 
                   'gridsDirectory': gridsDirectory, 'pvr': False, 'pvrDirectory': pvrDirectory, 
                   'cameraID': 0, 'framesPerSec': 10, 'capLength': 5, 'discipline': 'waterski', 
                   'gridFileName1': '', 'gridFileName2': '', 'gridFileName3': '', 
                   'gridFileName4': '', 'gridDescription1': '', 'gridDescription2': '', 
                   'gridDescription3': '', 'gridDescription4': ''}
    # Put the config file back.  Any updates to the structure of the config file will be added
    # and the config file will be created if it doesn't already exist
    a = json.dumps(vtmInit)
    with open(configFileName, 'w') as f:
        f.write(a)
    # Log launching the program
    date = datetime.now().strftime('%Y-%m-%d')
    fileName = os.path.join(os.path.expanduser('~'),'Documents\\VTM\\VTMLog-' + date + '.txt')
    with open(fileName, 'a') as f:
        print('\n\n===========================================================', file = f)
        print('VTM launched at ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + ' local time. Discipline = "' + vtmInit['discipline'] + '".', file = f)   
    app = QApplication(sys.argv)        # A new instance of QApplication
    #global form
    form = VideoCapture(vtmInit)        # We set the form to be our VTTApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the app
    
if __name__ == '__main__':              # if we're running file directly and not importing it
    main()
