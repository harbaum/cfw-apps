#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, os
from TxtStyle import *

import smbus, glob, re

class TinyLabel(QLabel):
    def __init__(self, str, parent=None):
        super(TinyLabel, self).__init__(str, parent)
        self.setObjectName("tinylabel")

class SmallLabel(QLabel):
    def __init__(self, str, parent=None):
        super(SmallLabel, self).__init__(str, parent)
        self.setObjectName("smalllabel")

class InfoWidget(QWidget):
    def __init__(self,title,parent=None):
        super(InfoWidget,self).__init__(parent)
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)
        titleW = QLabel(title)
        titleW.setStyleSheet("font-size: 16px;")
        vbox.addWidget(titleW)
        self.label = SmallLabel("")
        self.label.setStyleSheet("font-size: 20px;")
        self.label.setWordWrap(True)
        vbox.addWidget(self.label)
        self.setLayout(vbox)

    def setText(self, str):
        self.label.setText(str)
    
class ScannerWidget(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(2)
        self.grid.setContentsMargins(0,0,0,0)

        for i in range(8):
            self.grid.addWidget(TinyLabel(self.hexstr(i), self),0,i+1)
                
        for i in range(15):
            self.grid.addWidget(TinyLabel(self.hexstr(8*i), self),i+1,0)

    def hexdigit(self,i):
        return [ '0','1','2','3','4','5','6','7',
                 '8','9','a','b','c','d','e','f'][i]
        
    def hexstr(self,i):
        return self.hexdigit(i>>4)+self.hexdigit(i&15)
    
    def clear(self):
        for i in range(3,0x77):
            item = self.grid.itemAtPosition(1+int(i/8),1+int(i%8))
            if item: item.widget().deleteLater()

    def tick(self, index):
        x = TinyLabel(self.hexstr(index))
        x.setStyleSheet("QLabel { color : yellow; }");
        self.grid.addWidget(x,1+int(index/8),1+int(index%8))
     
class TreeComboBox(QComboBox):
    style = ( "font-size: 20px;"
              "background: #5c96cc;"
              "alternate-background-color: rgba(0,0,0,16);"
    )

    def __init__(self, *args):
        super().__init__(*args)

        self.__path = [0]
        self.__tree_changed = False
        self.setStyleSheet(self.style)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents);

        tree_view = QTreeView(self)
        tree_view.setHeaderHidden(True)
        tree_view.setFrameShape(QFrame.NoFrame)
        tree_view.setEditTriggers(tree_view.NoEditTriggers)
        tree_view.setAlternatingRowColors(True)
        tree_view.setSelectionBehavior(tree_view.SelectRows)
        tree_view.setWordWrap(True)
        tree_view.setAllColumnsShowFocus(True)
        self.setView(tree_view)

        self.view().viewport().installEventFilter(self)

    def showPopup(self):
        #print("SHOW")
        super().showPopup()

    def hidePopup(self):
        # print("HIDE", self.__tree_changed);

        self.__path = [ ]
        index = self.view().currentIndex()
        while index.row() >= 0:
            self.__path.insert(0, index.row())
            index = index.parent()

        #self.setCurrentIndex(self.view().currentIndex().row())
        # if the tree has changed we just reopen the popup 
        if self.__tree_changed:
            self.__tree_changed = False
            self.showPopup()
        else:
            super().hidePopup()

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonPress and object is self.view().viewport():
            index = self.view().indexAt(event.pos())
            self.__tree_changed = not self.view().visualRect(index).contains(event.pos())
        return False

    def path(self):
        return self.__path
    
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
            if self.busses[i] != None:
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

class UsbBusses:
    def __init__(self):
        self.busses = [ ]
        BUS_PATH = "/sys/bus"
        if not os.path.isdir(BUS_PATH):
            return

        # get all usb busses, we assume that busses
        # never change during runtime
        busses = glob.glob("/sys/bus/usb/devices/usb*")
        busses.sort()
        for b in busses:
            self.busses.append( {
                "path": b,
                "busnum": self.getInt(b, "busnum")
            })

        # scan all busses for devices
        self.scan()

    def getString(self, path, name):
        file = os.path.join(path, name)
        if os.path.isfile(file):
            with open(file) as f:
                return f.readline().strip()
        return None

    def getInt(self, path, name):
        i = self.getString(path, name)
        if not i: return None
        return int(i)

    def getHex(self, path, name):
        i = self.getString(path, name)
        if not i: return None
        return int(i, 16)

    def list(self):
        return self.busses

    def scan(self):
        busses = [ ]
        for i in self.busses:
            busses.append(self.scan_device(i["path"], None, 0, 0))

        for b in busses:
            self.print_device(b)

        return busses
            
    def class_decode(self, cls):
        class2str = {
	    0x00: "Defined in Interfaces",
            0x01: "Audio",
            0x02: "Communications and CDC",
            0x03: "HID",
	    0x05: "Physical",
            0x06: "Image",
            0x07: "Printer",
            0x08: "Mass Storage",
	    0x09: "Hub",
            0x0a: "CDC-Data",
            0x0b: "Smart Card",
            0x0d: "Content Security",
	    0x0e: "Video",
            0x0f: "Personal Healthcare",
            0x10: "Audio/Video Devices",
            0xdc: "Diagnostic Device",
            0xe0: "Wireless Controller",
	    0xef: "Miscellaneous",
            0xfe: "Application Specific ",
            0xff: "Vendor Specific" }
        if cls in class2str: return class2str[cls]
        return None
        
    def scan_string(self, path, device, name):
        if self.getString(path, name):
            device[name] = self.getString(path, name)
        
    def scan_interface(self, path):
        interface = { }
        interface["ifnum"] = self.getHex(path, "bInterfaceNumber")
        interface["altset"] = self.getInt(path, "bAlternateSetting")
        interface["numeps"] = self.getInt(path, "bNumEndpoints")
        interface["class"] = self.getHex(path, "bInterfaceClass")
        interface["subclass"] = self.getString(path, "bInterfaceSubClass")
        interface["protocol"] = self.getString(path, "bInterfaceProtocol")
        if os.path.islink(os.path.join(path, "driver")):
            interface["driver"] = os.path.basename(os.path.realpath(os.path.join(path, "driver")))
        else:
            interface["driver"] = None
        interface["classname"] = self.class_decode(interface["class"])

        # endpoints don't seem to work in usb-devices either ...

        return interface
        
    def print_device(self, device):
        # this is supposed to print _exacly_ what the usb-devices command prints        
        parent = 0
        if device["parent"]: parent = device["parent"]["devnum"]
        print("\nT:  Bus={:02d} Lev={:02d} Prnt={:02d} Port={:02d} Cnt={:02d} Dev#={:3d} Spd={:3s} MxCh={:2d}".format(device["busnum"],device["level"],parent,device["port"],device["count"],device["devnum"],device["speed"],device["maxchild"]))
        print("D:  Ver={:>5s} Cls={:02x}({:s}) Sub={:s} Prot={:s} MxPS={:2d} #Cfgs={:3d}".format(device["ver"], device["devclass"], str(device["classname"]), device["devsubclass"], device["devprotocol"], device["maxps0"], device["numconfigs"]))
        print("P:  Vendor={:04x} ProdID={:04x} Rev={:02x}.{:02x}".format(device["vendid"], device["prodid"], device["rev"][0], device["rev"][1]))
        for s in [ ( "manufacturer", "Manufacturer" ), ( "product", "Product" ), ( "serial", "SerialNumber" ) ]: 
            if s[0] in device: print("S:  {:s}={:s}".format(s[1], device[s[0]]))
                                                                          
        print("C:  #Ifs={:2d} Cfg#={:2d} Atr={:s} MxPwr={:s}".format(device["numifs"], device["cfgnum"], device["attr"], device["maxpower"]))

        for interface in device["interfaces"]:
            print("I:  If#={:2d} Alt={:2d} #EPs={:2d} Cls={:02x}({:s}) Sub={:s} Prot={:s} Driver={:s}".format(interface["ifnum"], interface["altset"], interface["numeps"], interface["class"], str(interface["classname"]), interface["subclass"], interface["protocol"], str(interface["driver"])))

        for subdevice in device["subdevices"]:
            self.print_device(subdevice)
            
    def scan_device(self, devpath, parent, level, count):
        device = { }
        device["path"] = devpath
        device["parent"] = parent
        device["level"] = level
        device["count"] = count
        device["busnum"] = self.getInt(devpath, "busnum")
        device["devnum"] = self.getInt(devpath, "devnum")
        if level > 0:
            # $((${devpath##*[-.]} - 1))
            if len(devpath.split(".")) > 1: device["port"] = int(devpath.split(".")[-1])-1
            else:                           device["port"] = 0
        else:         device["port"]=0        
        device["speed"] = self.getString(devpath, "speed")
        device["maxchild"] = self.getInt(devpath, "maxchild")

        device["ver"] = self.getString(devpath, "version")
        device["devclass"] = self.getHex(devpath, "bDeviceClass")
        device["devsubclass"] = self.getString(devpath, "bDeviceSubClass")
        device["devprotocol"] = self.getString(devpath, "bDeviceProtocol")
        device["maxps0"] = self.getInt(devpath, "bMaxPacketSize0")
        device["numconfigs"] = self.getInt(devpath, "bNumConfigurations")
        device["classname"] = self.class_decode(device["devclass"])        
        
        device["vendid"] = self.getHex(devpath, "idVendor")
        device["prodid"] = self.getHex(devpath, "idProduct")
        device["rev"] = ( int(self.getString(devpath, "bcdDevice")[:2], 16), int(self.getString(devpath, "bcdDevice")[2:], 16) )

        self.scan_string(devpath, device, "manufacturer")
        self.scan_string(devpath, device, "product")
        self.scan_string(devpath, device, "serial")

        device["numifs"] = self.getInt(devpath, "bNumInterfaces")
        device["cfgnum"] = self.getInt(devpath, "bConfigurationValue")
        device["attr"] = self.getString(devpath, "bmAttributes")
        device["maxpower"] = self.getString(devpath, "bMaxPower")

	# There's not really any useful info in endpoint 00
	# self.print_endpoint(devpath, "ep_00)
        device["interfaces"] = [ ]
        interfaces = glob.glob( os.path.join(devpath,str(device["busnum"]))+"-*:?.*")
        interfaces.sort()
        for interface in interfaces:
            device["interfaces"].append(self.scan_interface(interface))
            
        device["interfaces"] = sorted(device["interfaces"], key = lambda i: i['ifnum'])

        # seach for subdevices
        device["subdevices"] = [ ]
        devcount = 0
        subdevs = glob.glob( os.path.join(devpath,str(device["busnum"]))+"-*")
        subdevs.sort()
        for subdev in subdevs:
            if re.match(os.path.join(devpath,str(device["busnum"]))+"-[0-9]+(\.[0-9]+)*$", subdev):
                devcount = devcount + 1
                device["subdevices"].append(self.scan_device(subdev, device, level+1, devcount))

        return device
        
class FtcGuiApplication(TouchApplication):
    def usbDevItem(self, device):
        if "product" in device:        
            item = QStandardItem(device["product"])
        else:
            if device["classname"]:            
                item = QStandardItem("{:s} - {:04x}:{:04x}".format(
                    device["classname"].strip(), device["vendid"], device["prodid"]))
            else:
                item = QStandardItem("{:04x}:{:04x}".format(device["vendid"], device["prodid"]))
            
        for d in device["subdevices"]:
            item.appendRow(self.usbDevItem(d))

        return item
    
    def createUsbTab(self, tabwidget):
        # add the USB tab
        usb_widget = QWidget()
        vbox = QVBoxLayout()
        # vbox.setContentsMargins(0,0,0,0)
        usb_widget.setLayout(vbox)        
        tabwidget.addTab(usb_widget, "USB")

        usbBusses = UsbBusses()
        self.usbBusses = usbBusses.scan()
        
        if len(self.usbBusses) == 0:
            lbl = QLabel("No usable\nUSB busses found!")
            vbox.addWidget(lbl)
            return
        
        # show all usb busses in one big combobox
        combo = TreeComboBox()
        combo.activated.connect(self.set_usb_device)

        model = QStandardItemModel()

        for bus in self.usbBusses:
            model.appendRow(self.usbDevItem(bus))
            
        combo.setModel(model)
        vbox.addWidget(combo)

        # put contents inside a scroll area
        self.vbox_w = QWidget()
        ivbox = QVBoxLayout()
        self.vbox_w.setLayout(ivbox)

        self.usbW = { }
        for i in [
                ("bus", "Bus/Level/DevNum"),
                ("vidpid", "VID/PID/REV"),
                ("manufacturer", "Vendor"),
                ("product", "Product"),
                ("serial", "Serial number"),
                ("ver", "Version"),
                ("class", "Device class"),
                ("subclass", "Subclass/Protocol"),
                ("speed", "Speed (mbit/s)"),
                ("driver", "Driver"),
                ]:
        
            self.usbW[i[0]] = InfoWidget(i[1]);
            ivbox.addWidget(self.usbW[i[0]])

        ivbox.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.vbox_w)
        
        vbox.addWidget(scroll)
        
        self.usb_show(self.usbBusses[0])
        
    def createI2cTab(self, tabwidget):
        # add the I²C tab
        i2c_widget = QWidget()
        vbox = QVBoxLayout()
        # vbox.setContentsMargins(0,0,0,0)
        i2c_widget.setLayout(vbox)        
        tabwidget.addTab(i2c_widget, "I²C")

        self.i2cBusses = I2cBusses()

        if not self.i2cBusses.usable():
            if len(self.i2cBusses.list()) == 0:
                lbl = QLabel("No usable\nI²C busses found!")
            else:
                lbl = QLabel("Found " + str(len(self.i2cBusses.list())) + " I²C\nbusses but none is usable.")
                
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            vbox.addWidget(lbl)
            return
            
        # if we get here then there's at least one usable
        # i2c bus
            
        # drop down list containing all busses
        busses_w = QComboBox()
        busses_w.setStyleSheet("font-size: 20px;")
        busses_w.activated[str].connect(self.set_i2c_bus)
        for i in list(self.i2cBusses.list().keys()):
            busses_w.addItem(i)
        vbox.addWidget(busses_w)
        vbox.addStretch()

        model = busses_w.model()
        n = 0
        firstgood = None
        for i in self.i2cBusses.list():
            item = model.item(n)
            if self.i2cBusses.list()[item.text()] == None:
                item.setEnabled(False)
            elif firstgood == None:
                firstgood = n
                
            n = n + 1

        # select first good bus
        busses_w.setCurrentIndex(firstgood)
            
        self.scanner = ScannerWidget()
        vbox.addWidget(self.scanner)
        
        vbox.addStretch()
        self.i2cBusses.scan(self.scanner, busses_w.currentText())
    
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "BusScanner_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TxtWindow("Bus Scanner")
        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0,0,0,0)
        self.vbox.setSpacing(0)

        # create a tab widget
        tabwidget = QTabWidget()
        self.createI2cTab(tabwidget)
        self.createUsbTab(tabwidget)
        self.vbox.addWidget(tabwidget)

        self.w.centralWidget.setLayout(self.vbox)

        self.w.show()
        self.exec_()        

    def usb_show(self, dev):
        self.usbW["bus"].setText("#{:02d}/{:02d}/#{:02d}".format(dev["busnum"],dev["level"],dev["devnum"]))
            
        self.usbW["vidpid"].setText("{:04x}:{:04x} Rev. {:02x}.{:02x}".format(dev["vendid"], dev["prodid"], dev["rev"][0], dev["rev"][1]))

        for i in [ "manufacturer", "product", "serial", "driver", "speed", "ver" ]:
            if i in dev:
                self.usbW[i].setVisible(True)
                self.usbW[i].setText(dev[i])
            else:
                self.usbW[i].setVisible(False)

        if "classname" in dev:
            self.usbW["class"].setText(dev["classname"])
        else:
            self.usbW["class"].setText("{:02x}".format(dev["devclass"]))
        self.vbox_w.show()
          
        self.usbW["subclass"].setText("{:s}/{:s}".format(dev["devsubclass"], dev["devprotocol"]))
        
    def set_usb_device(self, name):
        # search for device by tree path
        b = self.usbBusses[self.sender().path()[0]]
        if len(self.sender().path()) > 1:
            for i in self.sender().path()[1:]:
                b = b["subdevices"][i]

        self.usb_show(b)
        
    def set_i2c_bus(self, name):
        self.i2cBusses.scan(self.scanner, name)
                    
    def output_toggle(self):
        output = int(self.sender().text()[1])-1
        state = self.sender().isChecked()
        self.ftduino.setOutput(output, state)
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
