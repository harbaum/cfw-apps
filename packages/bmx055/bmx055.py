#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, os
from TxtStyle import *

import smbus
import struct, array, math

class BMX055:
    BUS = 1;

    # I2C address of the BMX055's components
    GYRO = 0x68;
    COMPASS = 0x10;
    ACCELEROMETER = 0x18;

    def __init__(self):
        # create bus
        self.bus = smbus.SMBus(self.BUS)

        if self.bus:
            gyro_chip_id = self.bus.read_byte_data(self.GYRO, 0)
            print("gyro chip id is", format(gyro_chip_id, '02x'))
            acc_chip_id = self.bus.read_byte_data(self.ACCELEROMETER, 0)
            print("accelerometer chip id is", format(acc_chip_id, '02x'))

            #self.bus.write_byte_data(self.COMPASS, 0x4b, 0x01)
            #self.bus.write_byte_data(self.COMPASS, 0x4c, 0x00)
            #compass_chip_id = self.bus.read_byte_data(self.COMPASS, 0x40)
            #print("compass chip id is", format(compass_chip_id, '02x'))
            
    def gyroscope(self):
        if not self.bus: return None
        # read and decode 3 consecutive signed 16 bit values
        b = self.bus.read_i2c_block_data(self.GYRO, 2, 6)
        return struct.unpack('hhh', array.array('B', b))

    def accelerometer(self):
        if not self.bus: return None
        # read and decode 3 consecutive signed 16 bit values
        # and one signed byte
        b = self.bus.read_i2c_block_data(self.ACCELEROMETER, 2, 7)
        return struct.unpack('hhhb', array.array('B', b))

    #def compass(self):
    #    if not self.bus: return None
    #    # read and decode 3 consecutive signed 16 bit values
    #    # this needs major post processing ...
    #    b = self.bus.read_i2c_block_data(self.COMPASS, 0x42, 8)
    #    return struct.unpack('hhhh', array.array('B', b))

class ValueWidget(QSlider):
    def __init__(self, parent=None):
        QSlider.__init__(self, Qt.Horizontal, parent)
        self.setDisabled(True)
        self.setRange(-100, 100)

class SmallLabel(QLabel):
    def __init__(self, str, parent=None):
        super(SmallLabel, self).__init__(str, parent)
        self.setObjectName("smalllabel")

class TinyLabel(QLabel):
    def __init__(self, str, parent=None):
        super(TinyLabel, self).__init__(str, parent)
        self.setObjectName("tinylabel")

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "bmx055_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TxtWindow("BMX055")

        self.vbox = QVBoxLayout()
        self.vbox.addStretch()

        try:
            self.bmx055 = BMX055()
        except IOError:
            self.bmx055 = None

            lbl = QLabel("Unable to connect to " + 
                         "BMX055 sensor. Make sure one is " + 
                         "connected to the TXTs EXT port.")
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)

        if self.bmx055: 
            # accelerometer
            lbl = TinyLabel("Accelerometer (+/-2g)", self.w)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)

            self.acc_grid_w = QWidget()
            self.acc_grid = QGridLayout()
            self.acc_grid.setVerticalSpacing(0)
            self.acc_grid_w.setLayout(self.acc_grid)
            self.acc_x_slider = ValueWidget(self.acc_grid_w)
            self.acc_grid.addWidget(TinyLabel("X:", self.acc_grid_w),0,0)
            self.acc_grid.addWidget(self.acc_x_slider,0,1)
            self.acc_y_slider = ValueWidget(self.w)
            self.acc_grid.addWidget(TinyLabel("Y:", self.acc_grid_w),1,0)
            self.acc_grid.addWidget(self.acc_y_slider,1,1)
            self.acc_z_slider = ValueWidget(self.w)
            self.acc_grid.addWidget(TinyLabel("Z:", self.acc_grid_w),2,0)
            self.acc_grid.addWidget(self.acc_z_slider,2,1)
            self.vbox.addWidget(self.acc_grid_w)

            self.angle_lbl = TinyLabel("Angle:", self.w)
            self.angle_lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(self.angle_lbl)

            # gyro
            lbl = TinyLabel("Gyroscope (+/-2k°/s)", self.w)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)

            self.gyro_grid_w = QWidget()
            self.gyro_grid = QGridLayout()
            self.gyro_grid.setVerticalSpacing(0)
            self.gyro_grid_w.setLayout(self.gyro_grid)
            self.gyro_x_slider = ValueWidget(self.gyro_grid_w)
            self.gyro_grid.addWidget(TinyLabel("X:", self.gyro_grid_w),0,0)
            self.gyro_grid.addWidget(self.gyro_x_slider,0,1)
            self.gyro_y_slider = ValueWidget(self.w)
            self.gyro_grid.addWidget(TinyLabel("Y:", self.gyro_grid_w),1,0)
            self.gyro_grid.addWidget(self.gyro_y_slider,1,1)
            self.gyro_z_slider = ValueWidget(self.w)
            self.gyro_grid.addWidget(TinyLabel("Z:", self.gyro_grid_w),2,0)
            self.gyro_grid.addWidget(self.gyro_z_slider,2,1)
            self.vbox.addWidget(self.gyro_grid_w)

            # start a qtimer to poll the sensor
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.on_timer)
            self.timer.start(100)   

        self.vbox.addStretch()
        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()
        self.exec_()        

    def on_timer(self):
        # get the accelerometer and gyroscope values
        a = self.bmx055.accelerometer()
        self.acc_x_slider.setValue(100*a[0]/32768)
        self.acc_y_slider.setValue(100*a[1]/32768)
        self.acc_z_slider.setValue(100*a[2]/32768)

        # calculate x angle from y/z acceleration
        angle = 180 * math.atan2(a[2], a[1]) / math.pi
        self.angle_lbl.setText("Angle X: {0:.2f}°".format(angle))
        
        g = self.bmx055.gyroscope()
        self.gyro_x_slider.setValue(100*g[0]/32768)
        self.gyro_y_slider.setValue(100*g[1]/32768)
        self.gyro_z_slider.setValue(100*g[2]/32768)

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
