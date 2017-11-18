#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, os
from TxtStyle import *

import smbus, glob
# import struct, array, math

class Ftduino:
    # I2C address of the Ftduino's I2cSlave
    ADDR = 42;

    def __init__(self):
        busses = glob.glob("/dev/i2c-*")

        # scan all busses
        self.bus = None
        for b in busses:
            bus_num = int(b.split("-")[1])
            if bus_num:  # ignore bus 0
                try:
                    # try to open the bus
                    self.bus = smbus.SMBus(bus_num)
                    # try to access the device
                    self.bus.read_byte_data(self.ADDR, 0);
                    break
                except:
                    self.bus = None

        if not self.bus:
            raise IOError

    def setOutput(self, port, state):
        self.bus.write_byte_data(self.ADDR, port, state)
        
class TinyLabel(QLabel):
    def __init__(self, str, parent=None):
        super(TinyLabel, self).__init__(str, parent)
        self.setObjectName("tinylabel")

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "ftDuinoI2C_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TxtWindow("ftDuino I²C")

        self.vbox = QVBoxLayout()
        self.vbox.addStretch()

        try:
            self.ftduino = Ftduino()
        except IOError:
            self.ftduino = None

            lbl = QLabel("Unable to connect to " + 
                         "the ftDuino.\n\nMake sure one is " + 
                         "connected to the TXTs EXT port and runs " +
                         "the I2cSlave sketch.")
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)

        if self.ftduino:
            for b in range(8):
                cBox = QCheckBox("O"+str(b+1))
                cBox.stateChanged.connect(self.output_toggle)
                self.vbox.addWidget(cBox)
            
        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()
        self.exec_()        

    def output_toggle(self):
        output = int(self.sender().text()[1])-1
        state = self.sender().isChecked()
        self.ftduino.setOutput(output, state)
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
