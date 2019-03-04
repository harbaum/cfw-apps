#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, os
from TxtStyle import *

import smbus, glob

class TinyLabel(QLabel):
    def __init__(self, str, parent=None):
        super(TinyLabel, self).__init__(str, parent)
        self.setObjectName("tinylabel")

class ScannerWidget(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(2)
        self.grid.setContentsMargins(0,0,0,0)

        for i in range(16):
            self.grid.addWidget(TinyLabel(hex(256+16*i)[-2:], self),i+1,0)
            self.grid.addWidget(TinyLabel(hex(i)[-1:], self),0,i+1)

    def clear(self):
        for i in range(3,0x77):
            item = self.grid.itemAtPosition(1+int(i/16),1+int(i%16))
            if item: self.grid.removeItem(item)
        
    def tick(self, index):
        x = TinyLabel("X", self)
        x.setStyleSheet("QLabel { color : yellow; }");
        self.grid.addWidget(x,1+int(index/16),1+int(index%16))
            
class I2cBusses:
    def __init__(self):
        self.busses = { }
        busfiles = glob.glob("/dev/i2c-*")
        busfiles.sort()
        for b in busfiles:
            bus_num = int(b.split("-")[1])
            try:
                # try to open the bus
                bus = smbus.SMBus(bus_num)
                self.busses[b] = bus
            except:
                self.busses[b] = None

    def usable(self):
        for i in self.busses:
            if i != None:
                return True
        return False
        
    def list(self):
        return self.busses

    def scan(self, w, name):
        w.clear()
        for x in range(3,0x77):
            try:
                self.busses[name].read_byte_data(x, 0);
                w.tick(x)
            except:
                pass
                
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
        
class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "I2CScanner_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TxtWindow("I²C Scanner")

        self.vbox = QVBoxLayout()
#        self.vbox.addStretch()

        self.busses = I2cBusses()
        print("Bus names:", self.busses.list())

        if not self.busses.usable():
            if len(self.busses.list()) == 0:
                lbl = QLabel("No usable\nI²C busses found!")
            else:
                lbl = QLabel("Found " + len(self.busses.list()) + " I²C\nbusses but none is usable.")
                
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)
        else:
            # if we get here then there's at least one usable
            # i2c bus
            
            # drop down list containing all busses
            self.busses_w = QComboBox()
            self.busses_w.activated[str].connect(self.set_bus)
            for i in list(self.busses.list().keys()):
                self.busses_w.addItem(i)

            model = self.busses_w.model()
            n = 0
            firstgood = None
            for i in self.busses.list():
                item = model.item(n)
                if self.busses.list()[item.text()] == None:
                    item.setEnabled(False)
                elif firstgood == None:
                    firstgood = n
                
                n = n + 1

            # select first good bus
            self.busses_w.setCurrentIndex(firstgood)
            
            self.vbox.addWidget(self.busses_w)
            self.vbox.addStretch()
            self.scanner = ScannerWidget()
            self.vbox.addWidget(self.scanner)

            self.busses.scan(self.scanner, self.busses_w.currentText())
            
        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()
        self.exec_()        

    def set_bus(self, name):
        self.busses.scan(self.scanner, name)
                    
    def output_toggle(self):
        output = int(self.sender().text()[1])-1
        state = self.sender().isChecked()
        self.ftduino.setOutput(output, state)
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
