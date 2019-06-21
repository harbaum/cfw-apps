#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
from TxtStyle import *
from subprocess import call
import datetime, time
import DS3231

class TxPiHat():
    PINS = { "I1": 32, "I2": 36, "I3": 38, "I4": 40,
             "STBY": 35,
             "AIN1": 16, "AIN2": 15, "PWMA": 12,
             "BIN1": 29, "BIN2": 31, "PWMB": 33 }
    
    def __init__(self):
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            
            self.GPIO.setwarnings(False)
            self.GPIO.setmode(self.GPIO.BOARD)

            # configure I1..I4 as input
            self.GPIO.setup(self.PINS["I1"], self.GPIO.IN)
            self.GPIO.setup(self.PINS["I2"], self.GPIO.IN)
            self.GPIO.setup(self.PINS["I3"], self.GPIO.IN)
            self.GPIO.setup(self.PINS["I4"], self.GPIO.IN)

            # power up h bridge for M1 and M2
            self.GPIO.setup(self.PINS["STBY"], self.GPIO.OUT)
            self.GPIO.output(self.PINS["STBY"], self.GPIO.HIGH)

            # ---------------- M1 -----------------------
            # configure h bridge
            self.GPIO.setup(self.PINS["PWMB"], self.GPIO.OUT)
            self.pwm1 = self.GPIO.PWM(self.PINS["PWMB"], 200)  # 200 Hz
            self.pwm1.start(0)

            self.GPIO.setup(self.PINS["BIN1"], self.GPIO.OUT)
            self.GPIO.output(self.PINS["BIN1"], self.GPIO.LOW)

            self.GPIO.setup(self.PINS["BIN2"], self.GPIO.OUT)
            self.GPIO.output(self.PINS["BIN2"], self.GPIO.LOW)

            # ---------------- M2 -----------------------
            # configure h bridge
            self.GPIO.setup(self.PINS["PWMA"], self.GPIO.OUT)
            self.pwm2 = self.GPIO.PWM(self.PINS["PWMA"], 200)  # 200 Hz
            self.pwm2.start(0)

            self.GPIO.setup(self.PINS["AIN1"], self.GPIO.OUT)
            self.GPIO.output(self.PINS["AIN1"], self.GPIO.LOW)
        
            self.GPIO.setup(self.PINS["AIN2"], self.GPIO.OUT)
            self.GPIO.output(self.PINS["AIN2"], self.GPIO.LOW)
            
            self.ok = True
        except:
            self.ok = False

    def is_ok():
        return self.ok
            
    def get_input(self, i):
        return self.GPIO.input(self.PINS[i]) != 1

    def m_set_pwm(self, motor, v):
        mpwm = { "M1": self.pwm1, "M2": self.pwm2 }
        mpwm[motor].ChangeDutyCycle(v)
       
    def m_set_mode(self, motor, mode):
        mpins = { "M1": [self.PINS["BIN1"], self.PINS["BIN2"]],
                  "M2": [self.PINS["AIN1"], self.PINS["AIN2"]] }
        bits = { "Off":   [ self.GPIO.LOW,  self.GPIO.LOW  ],
                 "Left":  [ self.GPIO.HIGH, self.GPIO.LOW  ],
                 "Right": [ self.GPIO.LOW,  self.GPIO.HIGH ],
                 "Brake": [ self.GPIO.HIGH, self.GPIO.HIGH ] }
        self.GPIO.output(mpins[motor][0], bits[mode][0]);
        self.GPIO.output(mpins[motor][1], bits[mode][1]);
        
class MotorWidget(QWidget):
    MODES = [ "Off", "Left", "Right", "Brake" ]
    
    def __init__(self, hat, name, parent=None):
        super(QWidget,self).__init__(parent)
        self.name = name
        self.hat = hat
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        
        self.lbl = QLabel(name)
        self.lbl.setObjectName("smalllabel")
        hbox.addWidget(self.lbl, 0)
        
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.slider, 1)

        self.mode = QComboBox()
        self.mode.setStyleSheet("font-size: 20px;")
        for i in self.MODES: self.mode.addItem(i)
        self.mode.activated[str].connect(self.on_mode_changed)
        hbox.addWidget(self.mode, 0)
        
        self.setLayout(hbox)

    def on_value_changed(self, val):
        self.hat.m_set_pwm(self.lbl.text(), val)

    def on_mode_changed(self, val):
        self.hat.m_set_mode(self.lbl.text(), val)
        
class InputWidget(QWidget):
    def __init__(self, name, parent=None):
        super(QWidget,self).__init__(parent)
        self.name = name
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        
        self.lbl = QLabel(name)
        self.lbl.setObjectName("smalllabel")
        hbox.addWidget(self.lbl, 0)
        
        self.state = QLabel("Open")
        self.state.setStyleSheet("font-size: 24px;")
        self.state.setAlignment(Qt.AlignRight)
        hbox.addWidget(self.state, 0)
        
        self.setLayout(hbox)

    def set(self, state):
        if state: self.state.setText("Closed");
        else:     self.state.setText("Open");
        
class DateTimeWidget(QWidget):
    def __init__(self, name, parent=None):
        super(QWidget,self).__init__(parent)
        self.name = name
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        
        self.lbl = QLabel(name)
        self.lbl.setObjectName("smalllabel")
        hbox.addWidget(self.lbl, 0)
        
        self.state = QLabel("---")
        self.state.setAlignment(Qt.AlignRight)
        self.state.setStyleSheet("font-size: 24px;")
        hbox.addWidget(self.state, 0)
        
        self.setLayout(hbox)

    def set(self, s):
        self.state.setText(s);
      
class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        # create the empty main window
        self.w = TxtWindow("TX-Pi HAT")

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(0)

        self.vbox.addStretch()
        self.hat = TxPiHat()

        # add GPIO area
        if self.hat.ok:
            lbl = QLabel("-- Motors --")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("smalllabel")
            self.vbox.addWidget(lbl)
        
            self.m1 = MotorWidget(self.hat, "M1")
            self.vbox.addWidget(self.m1)
            self.m2 = MotorWidget(self.hat, "M2")
            self.vbox.addWidget(self.m2)

            self.vbox.addStretch()

            lbl = QLabel("-- Inputs --")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("smalllabel")
            self.vbox.addWidget(lbl)

            hw = QWidget()            
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0,0,0,0)
            self.i1 = InputWidget("I1")
            hbox.addWidget(self.i1)
            self.i2 = InputWidget("I2")
            hbox.addWidget(self.i2)
            hw.setLayout(hbox)
            self.vbox.addWidget(hw)

            hw = QWidget()            
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0,0,0,0)
            self.i3 = InputWidget("I3")
            hbox.addWidget(self.i3)
            self.i4 = InputWidget("I4")
            hbox.addWidget(self.i4)
            hw.setLayout(hbox)
            self.vbox.addWidget(hw)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.input_update)
            self.timer.start(100)
        else:
            lbl = QLabel("GPIO setup failed. Is this really a Raspberry Pi?")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("smalllabel")
            self.vbox.addWidget(lbl)

        self.vbox.addStretch()
        
        # add DS3231 area
        bus = os.getenv('I2C')
        if bus == None: bus = 1   # raspberry PI default
        else:           bus = int(bus)

        try:
            self.ds3231 = DS3231.DS3231(bus, 0x68)
            self.ds3231._read(0)
            self.ds3231.ackPendingAlarm()
        except:
            self.ds3231 = None

        if self.ds3231:
            lbl = QLabel("-- DS3231 RTC --")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("smalllabel")
            self.vbox.addWidget(lbl)

            self.datew = DateTimeWidget("Date")
            self.vbox.addWidget(self.datew)
            
            self.timew = DateTimeWidget("Time")
            self.vbox.addWidget(self.timew)

            self.tempw = DateTimeWidget("Temp.")
            self.vbox.addWidget(self.tempw)

            self.rtimer = QTimer(self)
            self.rtimer.timeout.connect(self.rtc_update)
            self.rtimer.start(500)

            self.set_but = QPushButton("Set from system")
            self.set_but.setStyleSheet("font-size: 24px;")
            self.set_but.clicked.connect(self.on_rtc_set)
            self.vbox.addWidget(self.set_but)

            self.rst_but = QPushButton("Restart in 1 min")
            self.rst_but.setStyleSheet("font-size: 24px;")
            self.rst_but.clicked.connect(self.on_rtc_reboot)
            self.vbox.addWidget(self.rst_but)

        else:
            lbl = QLabel("No DS3231 RTC detected!")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("smalllabel")
            self.vbox.addWidget(lbl)           
            
        self.vbox.addStretch()
        self.w.centralWidget.setLayout(self.vbox)

        self.w.show() 

        self.exec_()        

    def on_rtc_set(self):
        self.ds3231.write_now()

    def on_rtc_reboot(self):
        print("reboot")
        self.ds3231.setAlarm(datetime.datetime.now() + datetime.timedelta(minutes=1))
        self.notify_launcher("Shutting down ...")
        call(["sudo", "poweroff"])
        
    def notify_launcher(self, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Connect to server and send data
            sock.connect(("localhost", 9000))
            sock.sendall(bytes("msg {}\n".format(msg), "UTF-8"))
        except socket.error as msg:
            print(("Unable to connect to launcher:", msg))
        finally:
            sock.close()
 
    def rtc_update(self):
        d = self.ds3231.read_datetime()
        ts = str(d.time())
        self.timew.set(ts)
        ds = str(d.date())
        self.datew.set(ds)
        ts = str(self.ds3231.getTemp()) + " °C"
        self.tempw.set(ts)
        
    def input_update(self):
        inp = [ [ "I1", self.i1 ],[ "I2", self.i2 ],
                [ "I3", self.i3 ],[ "I4", self.i4 ] ]
        for i in inp:
            i[1].set(self.hat.get_input(i[0]))
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
