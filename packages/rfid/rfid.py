#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
from TouchStyle import *
import MFRC522
import ftrobopy

# the output ports
GREEN = 0
RED = 2
MOTOR = 4

# This is the default key for authentication
KEY = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
        
def dummy_reader():

    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print("Card detected")
    
    # Get the UID of the card
    (status,uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        # Print UID
        print("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
    
        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, KEY, uid)

        # Check if authenticated
        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_Read(8)
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print("Authentication error")

class SetupDialog(TouchDialog):
    def __init__(self,reader, parent):
        TouchDialog.__init__(self, "Setup", parent)

        vbox = QVBoxLayout()
        vbox.addStretch()

        self.MIFAREReader = reader

        lbl = QLabel(QCoreApplication.translate("setup", "Name:"))
        lbl.setObjectName("smalllabel")
        vbox.addWidget(lbl)
        self.name = QLineEdit("")
        self.name.setMaxLength(15)
        vbox.addWidget(self.name)

        vbox.addStretch()

        lbl = QLabel(QCoreApplication.translate("setup", "Permission:"))
        lbl.setObjectName("smalllabel")
        vbox.addWidget(lbl)
        self.check = QCheckBox(QCoreApplication.translate("setup", "enable"))
        vbox.addWidget(self.check)

        vbox.addStretch()

        lbl = QLabel(QCoreApplication.translate("setup",
                  "Place card in front of reader to write data."))
        lbl.setObjectName("tinylabel")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(lbl)

        self.centralWidget.setLayout(vbox)
                               
        self.done = False

        # start a qtimer to check for a tag to write
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(100)

    def on_timer(self):
        (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
        if status != self.MIFAREReader.MI_OK:
            return

        # Get the UID of the card
        (status,uid) = self.MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status != self.MIFAREReader.MI_OK:
            return

        # Select the scanned tag
        self.MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, 8, KEY, uid)

        # Check if authenticated
        if status == self.MIFAREReader.MI_OK:
            # Variable for the data to write
            data = []

            # Fill the data with 0xFF
            for x in range(0,16):
                data.append(0)

            if self.check.isChecked():
                data[0] = 0x42;

            for i in range(len(self.name.text())):
                data[i+1] = ord(self.name.text()[i])

            if self.MIFAREReader.MFRC522_Write(8, data):
                self.done = True
                
        self.MIFAREReader.MFRC522_StopCrypto1()
        self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)

        if self.done:
            self.timer.stop()
            print("closing")
            self.close()

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "rfid_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TouchWindow("RFID")

        self.vbox = QVBoxLayout()
        self.vbox.addStretch()

        try:
            self.MIFAREReader = MFRC522.MFRC522()
            if not self.MIFAREReader.MFRC522_Present():
                self.MIFAREReader = None

        except IOError:
            self.MIFAREReader = None

        if not self.MIFAREReader:
            lbl = QLabel(QCoreApplication.translate("main",
                         "Unable to connect to " + 
                         "RC522 RFID reader.\n\n" +
                         "Make sure one is " + 
                         "connected via USB or I²C."))
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)

        else:
            # get access to TXTs IOs if present
            txt_ip = os.environ.get('TXT_IP')
            if txt_ip == None: txt_ip = "localhost"
            try:
                self.txt = ftrobopy.ftrobopy(txt_ip, 65000)
            except:
                self.txt = None
            
            menu = self.w.addMenu()
            self.menu_cfg = menu.addAction(QCoreApplication.translate("menu", "Setup card"))
            self.menu_cfg.triggered.connect(self.setup)
    
            self.label = QLabel("")
            self.label.setObjectName("smalllabel")
            self.label.setAlignment(Qt.AlignCenter)            
            self.vbox.addWidget(self.label)

            self.icon = QLabel("")
            self.icon.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(self.icon)

            self.name = QLabel("")
            self.name.setObjectName("smalllabel")
            self.name.setAlignment(Qt.AlignCenter)            
            self.vbox.addWidget(self.name)

            self.setState("searching")
            
            # start a qtimer to poll the sensor
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.on_timer)
            self.timer.start(100)   

            # and a timer to handle lamps and motors
            self.io_timer = QTimer(self)
            self.io_timer.timeout.connect(self.on_io_event)
            self.io_timer.setSingleShot(True)
            self.io_state = None

        self.vbox.addStretch()
        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()
        self.exec_()

    def on_io_event(self):
        if self.io_state == "open":
            self.txt.setPwm(MOTOR,0)
            self.io_state = "wait"
            self.io_timer.start(2000)
            
        elif self.io_state == "wait":
            self.txt.setPwm(MOTOR+1,400)
            self.txt.setPwm(GREEN,0)
            self.io_state = "close"
            self.io_timer.start(1000)
            
        elif self.io_state == "close":
            self.txt.setPwm(MOTOR+1,0)
            self.io_state = None

        elif self.io_state == "light":
            self.txt.setPwm(RED,0)
            self.io_state = None

    def setup(self):
        self.timer.stop()
        dialog = SetupDialog(self.MIFAREReader, self.w)
        dialog.exec_()
        # wait 2 seconds before scanning again
        self.timer.start(2000)
        
    def setState(self, state, message = None):
        icon = None
        
        if state == "searching":
            self.label.setText(QCoreApplication.translate("status", "Searching ..."))
            icon = "searching"
            
        if state == "ok":
            self.label.setText(QCoreApplication.translate("status", "Accepted!"))
            icon = "granted"

            if self.txt:
                self.txt.setPwm(GREEN,512)
                self.txt.setPwm(MOTOR,400)
                self.io_state = "open"
                self.io_timer.start(1000)  # wait one second

        if state == "nok":
            self.label.setText(QCoreApplication.translate("status", "Denied!"))
            icon = "denied"
            if self.txt:
                self.txt.setPwm(RED,512)
                self.io_state = "light"
                self.io_timer.start(1000)  # wait one second
                
        if icon:
            name = os.path.join(os.path.dirname(os.path.realpath(__file__)), icon + ".png")
            pix = QPixmap(name)
            self.icon.setPixmap(pix)

        if message:
            self.name.setText(message)
        else:
            self.name.setText("")

    def on_timer(self):
        (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
        if status != self.MIFAREReader.MI_OK:
            self.setState("searching")
            self.timer.start(100)
            return

        # Get the UID of the card
        (status,uid) = self.MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status != self.MIFAREReader.MI_OK:
            self.setState("searching")
            self.timer.start(100)
            return
        
        print("UID:", uid)
        print("Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
        
        # Select the scanned tag
        self.MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, 8, KEY, uid)

        # Check if authenticated
        if status == self.MIFAREReader.MI_OK:
            data = self.MIFAREReader.MFRC522_Read(8)
            if data:
                # wait a second before scanning again
                print("Received:", data)

                name = ""
                for i in range(1,15):
                    if data[i]:
                        name = name + chr(data[i])
                            
                # check if data contains a valid "access token"
                if data[0] == 0x42:                    
                    self.setState("ok", name)
                else:
                    self.setState("nok", name)
                    
                self.timer.start(1000)
            else:
                self.setState("searching")
            
            self.MIFAREReader.MFRC522_StopCrypto1()
        else:
            # this happens most likely since the user removed
            # the card early
            self.setState("searching")
            return

        self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
            
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
