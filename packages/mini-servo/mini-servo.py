#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, os
from TxtStyle import *
import smbus, glob

class MiniServo:
    # Default I2C address of the Mini Servo Adapter
    ADDR = 17

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
                    # try to access the device by reading the test
                    # register which should return 0x5a
                    if self.bus.read_byte_data(self.ADDR, 1) == 0x5a:
                        break
                except:
                    self.bus = None

        if not self.bus:
            raise IOError

    def setValue(self, port, value):
        self.bus.write_byte_data(self.ADDR, port, value)
        
class TinyLabel(QLabel):
    def __init__(self, str, parent=None):
        super(TinyLabel, self).__init__(str, parent)
        self.setObjectName("tinylabel")

class ServoWidget(QWidget):
    def __init__(self, adapter, index, name, parent=None):
        super(QWidget,self).__init__(parent)
        self.adapter = adapter
        self.index = index
        self.name = name
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        
        self.lbl = QLabel(name)
        self.lbl.setObjectName("smalllabel")
        hbox.addWidget(self.lbl, 0)
        
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimum(62)
        self.slider.setMaximum(125)
        self.slider.setValue(int((125+62)/2))
        self.slider.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.slider, 1)
        
        self.setLayout(hbox)

        self.on_value_changed(0)

    def on_value_changed(self, val):
        self.adapter.setValue(self.index, val)

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "mini-servo_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TxtWindow("MiniServo")

        self.vbox = QVBoxLayout()
        self.vbox.addStretch()

        try:
            self.miniservo = MiniServo()
            
            self.servo1 = ServoWidget(self.miniservo, 0, "Servo 1:")
            self.vbox.addWidget(self.servo1)
            self.servo2 = ServoWidget(self.miniservo, 1, "Servo 2:")
            self.vbox.addWidget(self.servo2)
            
        except IOError:
            self.miniservo = None

            lbl = QLabel("Unable to connect to " + 
                         "the Mini Servo Adapter.\n\nMake sure one is " + 
                         "connected to the TX-Pi's/TXT's I²C port.")
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)

            
        self.vbox.addStretch()
        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()
        self.exec_()        

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
