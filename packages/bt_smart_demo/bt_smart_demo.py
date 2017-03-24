#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys, os, configparser
from TouchStyle import *
from busy_widget import BusyWidget

from bt_smart_controller import BtSmartController

class ConnectWidget(QWidget):
    connected = pyqtSignal(object)
    connectionFailed = pyqtSignal()

    def __init__(self, parent=None):
        super(ConnectWidget,self).__init__(parent)

        vbox = QVBoxLayout()
        vbox.setSpacing(0)

        vbox.addStretch()

        self.lbl = QLabel("")

        self.lbl.setWordWrap(True)
        self.lbl.setObjectName("smalllabel")
        self.lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl)

        vbox.addStretch()

        self.busy = BusyWidget(self)
        vbox.addWidget(self.busy)
        
        vbox.addStretch()

        self.setLayout(vbox)
        self.timer = None

    def search(self):
        self.lbl.setText(QCoreApplication.translate("Scanner", "Searching for BT smart controller."))

        if not self.search_now():
            # start a timer to frequently search for devices
            self.timer = QTimer()
            self.timer.timeout.connect(self.search_now)
            self.timer.start(1000)

    def search_now(self):
        # check for devices. This will initially only
        # return USB devices.
        devs = BtSmartController.scan_for_devices()

        if len(devs):
            if self.timer:
                self.timer.stop()
                self.timer = None

            return self.connect(devs[0])

        return False

    def connect(self, dev):
        print("CON", dev)

        self.sc = BtSmartController(dev)

        # display connecting message
        self.lbl.setText(QCoreApplication.translate("Scanner", "Connecting to BT smart controller."))

        # check if controller is connected
        if self.sc.isConnected():
            self.connected.emit(self.sc)
            return True
        else:
            self.timer = QTimer()
            self.timer.timeout.connect(self.wait_for_connection)
            self.timer.start(100)
            return False

    def wait_for_connection(self):
        if self.sc.connectionFailed():
            BtSmartController.scan_stop()
            self.sc = None

            self.timer.stop()
            self.timer = None
            self.connectionFailed.emit()
            return

        if self.sc.isConnected():
            self.timer.stop()
            self.timer = None
            self.connected.emit(self.sc)

    def stop(self):
        BtSmartController.scan_stop()
        self.sc = None

class ControlWidget(QWidget):
    done = pyqtSignal()

    class MotorSlider(QWidget):
        def __init__(self, str, parent=None):
            super(QWidget,self).__init__(parent)
            
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0,0,0,0)
            self.lbl = QLabel(str)
            self.lbl.setObjectName("smalllabel")
            hbox.addWidget(self.lbl)
            self.slider = QSlider(self)
            self.slider.setOrientation(Qt.Horizontal)
            self.slider.setMinimum(-128)
            self.slider.setMaximum(127)
            self.slider.valueChanged.connect(self.on_value_changed)
            hbox.addWidget(self.slider)
            self.setLayout(hbox)

        def on_value_changed(self, val):
            self.parent().sc.setOutputs( { self.lbl.text(): val } )

    class InputWidget(QWidget):
        def __init__(self, str, sc, parent=None):
            super(QWidget,self).__init__(parent)

            self.str = str
            
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0,0,0,0)
            self.lbl = QLabel(str)
            self.lbl.setObjectName("smalllabel")
            hbox.addWidget(self.lbl, 1)

            self.val = QLabel("---")
            self.val.setObjectName("smalllabel")
            self.val.setAlignment(Qt.AlignRight)
            hbox.addWidget(self.val, 1)

            if str != QCoreApplication.translate("Input", "Battery"):
                self.unit = QPushButton("-")
                self.unit.clicked.connect(self.on_unit_clicked)
                style = "QPushButton { font: normal 20px; }"
                self.unit.setStyleSheet(style)
            else:
                self.unit = QLabel("-")
                self.unit.setObjectName("smalllabel")
            hbox.addWidget(self.unit)
            
            self.setLayout(hbox)

        def on_unit_clicked(self):
            if self.sender().text().strip() == "R": new_mode = "U"
            else:                                   new_mode = "R"
            self.parent().sc.configInputs( { self.str: new_mode } )
            
        def set(self, data):
            if data["type"] == "R":
                if data["value"] == 65535:     # overflow
                    self.val.setText(QCoreApplication.translate("Input", "open"))
                else:
                    self.val.setText(str(data["value"]))
                self.unit.setText(" R ")
            elif data["type"] == "U":
                self.val.setText("{:.3f}".format(data["value"]))
                self.unit.setText(" V ")
            else:
                self.val.setText(str(data["value"]))
                self.unit.setText(data["type"])
            
    def __init__(self, sc, parent=None):
        super(ControlWidget,self).__init__(parent)

        self.sc = sc
        
        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0,0,0,0)

        self.i = { }
        for i in range(1,5):
            self.i["I"+str(i)] = self.InputWidget("I"+str(i), self)
            vbox.addWidget(self.i["I"+str(i)])

        vbox.addStretch()

        # add two motor sliders
        self.m = { }
        for m in range(1,3):
            self.m["M"+str(m)] = self.MotorSlider("M"+str(m), self)
            vbox.addWidget(self.m["M"+str(m)])

        vbox.addStretch()
        self.i["BAT"] = self.InputWidget(QCoreApplication.translate("Input", "Battery"), self)
        vbox.addWidget(self.i["BAT"])

        # add some hw info
        info = self.sc.getInfo()
        info_lbl = QLabel("SW:" + info["sw"] + "  HW:" +
                          info["hw"] + "  ID:" + info["id"] )
        info_lbl.setObjectName("tinylabel")
        info_lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(info_lbl)

        self.setLayout(vbox)        

        # start timer to monitor inputs
        self.timer = QTimer()
        self.timer.timeout.connect(self.input_update)
        self.timer.start(100)

    def input_update(self):
        if self.sc:
            inputs = self.sc.getInputData()
            for i in inputs:
                if i in self.i:
                    self.i[i].set(inputs[i])
        
    def stop(self):
        # switch outputs off and set inputs to resistance
        self.sc.setOutputs( { "M1": 0, "M2": 0 } )
        # self.sc.configInputs( { "I1": "R", "I2": "R", "I3": "R", "I4": "R" } )
        self.sc = None

class MainWindow(TouchWindow):
    def __init__(self):
        TouchWindow.__init__(self, QCoreApplication.translate("Main","BT smart"))
        self.controlWidget = None
        self.connectWidget = ConnectWidget()
        self.connectWidget.connected.connect(self.on_connected)
        self.connectWidget.connectionFailed.connect(self.on_connection_failed)
        self.setCentralWidget(self.connectWidget)

        # connect last used bt smart controller
        # try to load address from file
        try:
            path = os.path.dirname(os.path.realpath(__file__))
            config = configparser.ConfigParser()
            config.read(os.path.join(path, "device.ini"))
            dev = (config.get('bt_smart','device'), config.get('bt_smart','id') )
            self.connectWidget.connect( dev )            
        except Exception:
            # if anything goes wrong start a search
            self.connectWidget.search()

    def on_connection_failed(self):
        self.connectWidget.search()

    def on_connected(self, dev):
        self.connectWidget.stop()

        # save the address of the device permanently
        path = os.path.dirname(os.path.realpath(__file__))
        cfgfile = open(os.path.join(path, "device.ini"),'w')
        config = configparser.ConfigParser()
        config.add_section('bt_smart')
        config.set('bt_smart','device', dev.dev[0])
        config.set('bt_smart','id', dev.dev[1])
        config.write(cfgfile)
        cfgfile.close()

        # replace connect widget by control widget once a device
        # is connected
        self.controlWidget = ControlWidget(dev, self)
        self.controlWidget.done.connect(self.on_control_done)
        self.setCentralWidget(self.controlWidget)

        self.connectWidget = None

    def on_control_done(self):
        self.close()

    def on_scan_failure(self):
        self.close()

    def close(self):
        if self.connectWidget:
            self.connectWidget.stop()            

        if self.controlWidget:
            self.controlWidget.stop()
            
        TouchWindow.close(self)

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "bt_smart_demo_"))
        self.installTranslator(translator)
        
        # create the empty main window
        self.w = MainWindow()

        self.w.show()
        self.exec_()        

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
