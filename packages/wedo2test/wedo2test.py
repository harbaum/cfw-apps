#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys, os, pty, select, io, subprocess, time
import pygatt, binascii

from TouchStyle import *

# this is the UUID the WeDo hub sends with it's advertisement
# and which we use to identify it
WEDO_UUID_ADV="00001523-1212-EFDE-1523-785FEABCD123"

# these are the UUIDs of the services we are going to use
WEDO_UUID_3A="00001563-1212-efde-1523-785feabcd123"
WEDO_UUID_3D="00001565-1212-efde-1523-785feabcd123"

# a seperate thread runs the tools in the background
class ExecThread(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, cmd):
        super(ExecThread,self).__init__()
        self.cmd = cmd
    
    def run(self):
        try:
            # use a pty. This enforces unbuffered output and thus
            # allows for fast update
            master_fd, slave_fd = pty.openpty()
            self.proc = subprocess.Popen(self.cmd, stdout=slave_fd, stderr=slave_fd)
        except:
            self.finished.emit(False)
            return

        # listen to process' output
        while self.proc.poll() == None:
            try:
                if select.select([master_fd], [], [master_fd], .1)[0]:
                    output = os.read(master_fd, 100)
                    if output: self.output(str(output, "utf-8"))
            except InterruptedError:
                pass

        os.close(master_fd)
        os.close(slave_fd)

        self.finished.emit(self.proc.wait() == 0)
        
    def stop(self):
        self.proc.terminate()
        
    def output(self, str):
        pass

class HciTool(ExecThread):
    scan_result = pyqtSignal(str)

    def __init__(self, cmd, sudo = False):
        self.sudo = sudo
        self.rx_buf = ""
        hcitool_cmd = []
        if sudo: hcitool_cmd.append("sudo")

        hcitool_cmd.append("hcitool")
        hcitool_cmd += cmd
        super(HciTool,self).__init__(hcitool_cmd)

    def stop(self):
        if not self.proc.poll():
            if self.sudo:
                subprocess.call( [ "sudo", "pkill", "-SIGINT", "hcitool"] )
            else:
                self.proc.terminate()

    def output(self, str):
        # maintain an output buffer and search for complete strings there
        self.rx_buf += str

        lines = self.rx_buf.split('\n')
        # at least one full line?
        if len(lines) > 1:
            # keep the unterminated last line
            self.rx_buf = lines.pop()
            for l in lines:
                p = l.split()

                # result must consist of three parts, the first one must be a 17 bytes address
                # followed by "UUID128" and the UUID advertised by a wedo hub
                if len(p) == 3 and len(p[0]) == 17 and p[1] == "UUID128" and p[2] == WEDO_UUID_ADV:
                    self.scan_result.emit(l.split()[0])
                    

class ScanWidget(QWidget):
    device_select = pyqtSignal(str)
    failed = pyqtSignal()

    def __init__(self, parent=None):
        super(ScanWidget,self).__init__(parent)

        vbox = QVBoxLayout()
        vbox.setSpacing(0)

        lbl = QLabel(QCoreApplication.translate("Scanner", "Searching for WeDo 2.0 Hub.\n\nPlease press its green button to make it discoverable!"))

        lbl.setWordWrap(True)
        lbl.setObjectName("smalllabel")
        lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(lbl)

        self.setLayout(vbox)

        self.hcitool = HciTool([ "lescan" ], True)  # scan for le devices
        self.hcitool.scan_result.connect(self.on_hcitool_scan_result)
        self.hcitool.finished.connect(self.on_hcitool_result)
        self.hcitool.start()

    def stop(self):
        if self.hcitool:
            # stopping hcitool may generate an error. We want to 
            # ignore that, so we disconnect the signal handfler
            self.hcitool.finished.disconnect()
            self.hcitool.stop()
            self.hcitool = None
        
    def on_hcitool_scan_result(self, addr):
        self.device_select.emit(addr)        
        
    def on_hcitool_result(self, ok):
        # check if the command failed
        if not ok:
            # open a message box
            msg = TouchMessageBox(QCoreApplication.translate("Scanner", "Error"), self.parent())
            msg.setText(QCoreApplication.translate("Scanner",
              "Error accessing Bluetooth service. Please make sure Bluetooth is enabled."))
            msg.exec_()
            self.failed.emit()
        else:
            # everything looks fine
            # wait for thread to end before restarting it
            while self.hcitool.isRunning(): pass
            self.hcitool.start()

class PyGattThread(QThread):
    connected = pyqtSignal(bool)

    def __init__(self, addr):
        super(PyGattThread,self).__init__()
        self.addr = addr

        self.adapter = pygatt.GATTToolBackend()
        self.adapter.start(reset_on_start=False)
        self.color = None
        self.running = True
    
        self.h3a = None
        self.h3d = None
        
    def run(self):
        try:
            self.device = self.adapter.connect(self.addr)
        except Exception:
            self.connected.emit(False)
            self.device = None
            self.adapter.stop()
            return

        # get handle
        try:
            self.h3a = self.device.get_handle(WEDO_UUID_3A)
            self.h3d = self.device.get_handle(WEDO_UUID_3D)
        except Exception:
            self.connected.emit(False)
            self.device = None
            self.adapter.stop()
            return

        # switch led to absolute mode
        col_abs_cmd = [ 0x01, 0x02, 0x06, 0x17, 0x01, 0x01, 0x00, 0x00, 0x00, 0x02, 0x01 ]
        self.device.char_write_handle(self.h3a, bytearray(col_abs_cmd))
        
        self.connected.emit(True)
            
        # loop forever ...
        while(self.running):
            if self.color != None:
                # device 6, command 4, length 3
                color_cmd = [ 0x06, 0x04, 0x03 ]
                color_cmd.append(self.color["R"])
                color_cmd.append(self.color["G"])
                color_cmd.append(self.color["B"])
                self.color = None
                self.device.char_write_handle(self.h3d, bytearray(color_cmd))

            time.sleep(0.1)

        self.adapter.stop()

    def setColor(self, c):
        self.color = c

    def stop(self):
        self.running = False

class ControlWidget(QWidget):
    done = pyqtSignal()

    class ColorSlider(QWidget):
        valueChanged = pyqtSignal(str, int)        

        def __init__(self, str, val, parent=None):
            super(QWidget,self).__init__(parent)
            hbox = QHBoxLayout()
            self.lbl = QLabel(str)
            self.lbl.setObjectName("smalllabel")
            hbox.addWidget(self.lbl)
            self.slider = QSlider(self)
            self.slider.setOrientation(Qt.Horizontal)
            self.slider.setMaximum(255)
            self.slider.setValue(val)
            self.slider.valueChanged.connect(self.on_value_changed)
            hbox.addWidget(self.slider)
            self.setLayout(hbox)

        def on_value_changed(self, val):
            self.valueChanged.emit(self.lbl.text(), val)

    def __init__(self, addr, parent=None):
        super(ControlWidget,self).__init__(parent)

        # do pygatt communication in the background
        self.gatt = PyGattThread(addr)
        self.gatt.connected.connect(self.on_device_connected)
        self.gatt.start()

        vbox = QVBoxLayout()
        vbox.setSpacing(0)

        # add the address label
        lbl = QLabel(addr)
        lbl.setObjectName("smalllabel")
        lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(lbl)

        vbox.addStretch()

        # default color is blue
        self.color = { "R": 0, "G": 0, "B": 255 }
        self.gatt.setColor(self.color)

        # add three color sliders
        self.red = self.ColorSlider("R", self.color["R"], self)
        self.red.valueChanged.connect(self.on_value_changed)
        vbox.addWidget(self.red)        
        self.green = self.ColorSlider("G", self.color["G"], self)
        self.green.valueChanged.connect(self.on_value_changed)
        vbox.addWidget(self.green)        
        self.blue = self.ColorSlider("B", self.color["B"], self)
        self.blue.valueChanged.connect(self.on_value_changed)
        vbox.addWidget(self.blue)        

        vbox.addStretch()

        self.setLayout(vbox)        

    def on_value_changed(self, c, v):
        self.color[c] = v
        if self.gatt:
            self.gatt.setColor(self.color)

    def on_device_connected(self, ok):
        if not ok:
            msg = TouchMessageBox(QCoreApplication.translate("Control", "Error"), self.parent())
            msg.setText(QCoreApplication.translate("Control",
                "Unable to connect to service. Please select the correct device and make sure it's switched on."))
            msg.exec_()

            # wait for gatttool to shut down
            self.stop()
            self.gatt = None
            self.done.emit()

    def stop(self):
        if self.gatt:
            self.gatt.stop()

            # wait for gatt thread to end
            while self.gatt.isRunning():
                pass

class MainWindow(TouchWindow):
    def __init__(self):
        TouchWindow.__init__(self, QCoreApplication.translate("Main","WeDo 2.0"))
        self.controlWidget = None
        self.scanWidget = ScanWidget()
        self.scanWidget.device_select.connect(self.on_device_selected)
        self.scanWidget.failed.connect(self.on_scan_failure)
        self.setCentralWidget(self.scanWidget)

    def on_device_selected(self, addr):
        self.scanWidget.stop()

        # replace scan widget by control widget once the 
        # user has selected a device
        self.controlWidget = ControlWidget(addr, self)
        self.controlWidget.done.connect(self.on_control_done)
        self.setCentralWidget(self.controlWidget)

        self.scanWidget = None

    def on_control_done(self):
        self.close()

    def on_scan_failure(self):
        self.close()

    def close(self):
        if self.scanWidget:
            self.scanWidget.stop()            

        if self.controlWidget:
            self.controlWidget.stop()
            
        TouchWindow.close(self)

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "wedo2test_"))
        self.installTranslator(translator)
        
        # create the empty main window
        self.w = MainWindow()

        self.w.show()
        self.exec_()        

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
