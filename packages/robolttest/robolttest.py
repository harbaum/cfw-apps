#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import os, sys
from TxtStyle import *
from robolt import RoboLT

class SmallLabel(QLabel):
    def __init__(self, str, parent=None):
        super(SmallLabel, self).__init__(str, parent)
        self.setObjectName("smalllabel")

class InfoWidget(QWidget):
    def __init__(self,title,str,parent=None):
        super(InfoWidget,self).__init__(parent)
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(title))
        vbox.addWidget(SmallLabel(str))
        self.setLayout(vbox)

class InfoDialog(TxtDialog):
    def __init__(self,title,lt,parent=None):
        TxtDialog.__init__(self, title, parent)

        vbox = QVBoxLayout()
        vbox.addStretch()

        fw = InfoWidget("Firmware", "V" + lt.getFw())
        vbox.addWidget(fw)
        vbox.addStretch()

        ser = InfoWidget("Serial", str(lt.getSerial()))
        vbox.addWidget(ser)
        vbox.addStretch()

        bat = InfoWidget("Battery", "{:.2f} Volts".format(lt.getBattery()))
        vbox.addWidget(bat)
        vbox.addStretch()

        self.centralWidget.setLayout(vbox)

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        self.w = TxtWindow("RoboLT")

        self.vbox = QVBoxLayout()

        try:
            self.lt = RoboLT()
        except OSError as e:
            self.lt = None

        if self.lt == None:
            self.vbox.addStretch()
            err = QLabel("Error")
            err.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(err)
            lbl = QLabel("No RoboLT found. Please make sure one is connected to the TXTs USB1 port.")
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
        
            self.vbox.addWidget(lbl)
            self.vbox.addStretch()
        else:
            # everythings fine
            menu = self.w.addMenu()
            menu_info = menu.addAction("Info")
            menu_info.triggered.connect(self.show_info)

            # ---- M1 ----
            hbox1_w = QWidget()
            hbox1 = QHBoxLayout()
            hbox1_w.setLayout(hbox1)
      
            lbl = QLabel("M1")
            hbox1.addWidget(lbl)

            but_l = QPushButton("L")
            but_l.pressed.connect(self.on_m1_l_on)
            but_l.released.connect(self.on_m1_off)
            hbox1.addWidget(but_l)

            but_r = QPushButton("R")
            but_r.pressed.connect(self.on_m1_r_on)
            but_r.released.connect(self.on_m1_off)
            hbox1.addWidget(but_r)
            
            self.vbox.addWidget(hbox1_w)

            self.m1_speed_w = QSlider()
            self.m1_speed_w.setOrientation(Qt.Horizontal)
            self.m1_speed_w.setMaximum(100)
            self.m1_speed_w.setValue(50)
            self.vbox.addWidget(self.m1_speed_w)

            self.vbox.addStretch()

            # ---- M2 ----
            hbox2_w = QWidget()
            hbox2 = QHBoxLayout()
            hbox2_w.setLayout(hbox2)
      
            lbl = QLabel("M2")
            hbox2.addWidget(lbl)

            but_l = QPushButton("L")
            but_l.pressed.connect(self.on_m2_l_on)
            but_l.released.connect(self.on_m2_off)
            hbox2.addWidget(but_l)

            but_r = QPushButton("R")
            but_r.pressed.connect(self.on_m2_r_on)
            but_r.released.connect(self.on_m2_off)
            hbox2.addWidget(but_r)
            
            self.vbox.addWidget(hbox2_w)

            self.m2_speed_w = QSlider()
            self.m2_speed_w.setOrientation(Qt.Horizontal)
            self.m2_speed_w.setMaximum(100)
            self.m2_speed_w.setValue(50)
            self.vbox.addWidget(self.m2_speed_w)

            self.vbox.addStretch()

            # ---- I1-I3 ----
            hbox3_w = QWidget()
            hbox3 = QHBoxLayout()
            hbox3_w.setLayout(hbox3)
            
            i_lbl = QLabel("I:")
            hbox3.addWidget(i_lbl)
            self.i1 = QCheckBox()
            self.i1.setDisabled(True)
            hbox3.addWidget(self.i1)
            self.i2 = QCheckBox()
            self.i2.setDisabled(True)
            hbox3.addWidget(self.i2)
            self.i3 = QCheckBox()
            self.i3.setDisabled(True)
            hbox3.addWidget(self.i3)
            
            self.vbox.addWidget(hbox3_w)
            
            timer = QTimer(self)
            timer.timeout.connect(self.on_poll_inputs)
            timer.start(100);
    
        self.w.centralWidget.setLayout(self.vbox)
        self.w.show() 
        self.exec_()        
 
    def show_info(self):
        dialog = InfoDialog("Info", self.lt, self.w)
        dialog.exec_()
 
    def on_m1_l_on(self):
        self.lt.setM(1, RoboLT.Left, self.m1_speed_w.value())
        
    def on_m1_r_on(self):
        self.lt.setM(1, RoboLT.Right, self.m1_speed_w.value())

    def on_m1_off(self):
        self.lt.setM(1, RoboLT.Off)
        
    def on_m2_l_on(self):
        self.lt.setM(2, RoboLT.Left, self.m2_speed_w.value())
        
    def on_m2_r_on(self):
        self.lt.setM(2, RoboLT.Right, self.m2_speed_w.value())

    def on_m2_off(self):
        self.lt.setM(2, RoboLT.Off)
        
    def on_poll_inputs(self):
        (i1,i2,i3) = self.lt.I()
        self.i1.setChecked(i1)
        self.i2.setChecked(i2)
        self.i3.setChecked(i3)

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
