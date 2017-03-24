#
# python driver for fischertechnik BT smart controller
#
# This can make use of the USB interface and the BT interface
#

import os
import time
import serial
import serial.tools.list_ports
import threading
import struct
import queue
import pty
import subprocess
import select
import pygatt

# ============= USB/serial parameters ==============
BTSC_VIDPID = "221d:0005"  # LNT
BAUDRATE = 115200

CMD_GET_INFORMATION        = 0x03415a41
CMD_GET_INPUT_DATA         = 0xf48a1632
CMD_SET_AND_CONFIG_OUTPUTS = 0x68ce2a04
CMD_CONFIG_INPUTS          = 0x1434ff93
CMD_SET_LEDS               = 0x904cc3d8

# ================ BT parameters ====================
# http://ofalcao.pt/blog/series/wedo-2-0-reverse-engineering
BTSC_VENDOR = "10:45:f8"   # LNT

# TODO: get these from the primary services
def btsc_uuid(a):
    return "8ae8{0:04x}-ad7d-11e6-80f5-76304dec7eb7".format(a)

def bt_uuid(a):
    return "0000{0:04x}-0000-1000-8000-00805f9b34fb".format(a)

UUID_BATT         = [   bt_uuid(0x2a19) ]
UUID_REV          = [   bt_uuid(0x2a27),   bt_uuid(0x2a26) ]
UUID_COMM_CHANNEL = [ btsc_uuid(0x7e32) ]
UUID_OUTPUT_VALUE = [ btsc_uuid(0x860c), btsc_uuid(0x8b84) ]
UUID_INPUT_CONF   = [ btsc_uuid(0x8efe), btsc_uuid(0x9084),
                      btsc_uuid(0x9200), btsc_uuid(0x9386) ]
UUID_INPUT_VALUES = [ btsc_uuid(0x9a2a), btsc_uuid(0x9bec),
                      btsc_uuid(0x9dc2), btsc_uuid(0x9f66) ]

# a seperate thread to run BT tools in the background
class ExecThread(threading.Thread):
    def __init__(self, cmd):
        threading.Thread.__init__(self) 
        self.cmd = cmd
        self.proc = None
    
    def run(self):
        try:
            # use a pty. This enforces unbuffered output and thus
            # allows for fast update
            master_fd, slave_fd = pty.openpty()
            self.proc = subprocess.Popen(self.cmd, stdout=slave_fd, stderr=slave_fd)
        except:
            # self.finished.emit(False)
            print("ExecThread Finished with error!")
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

        rc = self.proc.wait()
        
    def stop(self):
        self.proc.terminate()
        
    def output(self, str):
        pass

class HciTool(ExecThread):
    def __init__(self, cmd, sudo = False, callback = None):
        self.sudo = sudo
        self.cb = callback

        self.rx_buf = ""
        hcitool_cmd = []
        if sudo: hcitool_cmd.append("sudo")

        hcitool_cmd.append("hcitool")
        hcitool_cmd += cmd
        super(HciTool,self).__init__(hcitool_cmd)

    def stop(self):
        # the process must be running before we can stop it
        while not self.proc:
            time.sleep(0.1)
        
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
                # followed by the right name. Address must be from LNT range
                if ( len(p) >= 3 and len(p[0]) == 17 and p[0][0:8].lower() == BTSC_VENDOR and
                     p[1].lower() == "name" and " ".join(p[2:]).lower() == "bt smart controller"):
                     if self.cb: self.cb(p[0])

class PyGattThread(threading.Thread):
    def __init__(self, addr):
        super(PyGattThread,self).__init__()
        self.addr = addr

        self.adapter = pygatt.GATTToolBackend()
        self.adapter.start(reset_on_start=False)
        self.running = True
        self.connected = False
        self.failed = False

        # the various bluetooth handles
        self.batt_hdl         = None
        self.comm_channel_hdl = None
        self.output_value_hdl = None
        self.input_conf_hdl   = None
        self.input_values_hdl = None

        self.tx_cond = threading.Condition()
        self.tx_data = { }
        
        self.input_batt = None
        self.input_values = None
        self.input_config = None
        self.input_lock = threading.Lock()
        
    def tx(self, obj):
        # place command in dictionary. This makes
        # sure that new commands for the same target override
        # older ones
        self.tx_cond.acquire()
        self.tx_data[obj[0]] = obj[1]
        self.tx_cond.notify()
        self.tx_cond.release()
        
    def run(self):
        try:
            self.device = self.adapter.connect(self.addr, timeout=1)
        except Exception:
            self.failed = True
            self.device = None
            self.adapter.stop()
            return

        self.device.get_handle(UUID_COMM_CHANNEL[0])
        
        # get all required handles
        try:
            # battery level
            self.batt_hdl = [ ]
            for i in UUID_BATT:
                self.batt_hdl.append(self.device.get_handle(i))

            # communication channel
            self.comm_channel_hdl = [ ]
            for i in UUID_COMM_CHANNEL:
                self.comm_channel_hdl.append(self.device.get_handle(i))

            # output value
            self.output_value_hdl = [ ]
            for i in UUID_OUTPUT_VALUE:
                self.output_value_hdl.append(self.device.get_handle(i))

            # input configuration
            self.input_conf_hdl = [ ]
            for i in UUID_INPUT_CONF:
                self.input_conf_hdl.append(self.device.get_handle(i))

            # input values
            self.input_values_hdl = [ ]
            for i in UUID_INPUT_VALUES:
                self.input_values_hdl.append(self.device.get_handle(i))

        except Exception:
            self.failed = True
            self.device = None
            self.adapter.stop()
            return

        # read hardware and software revision
        self.hw = self.device.char_read(UUID_REV[0]).partition(b'\0')[0].decode("utf-8")
        self.sw = self.device.char_read(UUID_REV[1]).partition(b'\0')[0].decode("utf-8")
    
        # finally light up the blue led to indicate connection
        self.device.char_write_handle(self.comm_channel_hdl[0], bytearray([0]))

        # request input config
        self.input_config = [ ]
        for hdl in self.input_conf_hdl:
            data_bytes = self.device.char_read_handle(hdl)
            self.input_config.append(struct.unpack( "B", data_bytes)[0])

        # request input value notifications and poll them once
        self.input_values = [ ]
        for i in range(len(UUID_INPUT_VALUES)):
            # subsribe for notifications
            self.device.subscribe(UUID_INPUT_VALUES[i], callback=self.input_callback)
            # poll inputs
            data_bytes = self.device.char_read_handle(self.input_values_hdl[i])
            self.input_values.append(struct.unpack( "<H", data_bytes)[0])
            if self.input_config[i] == 0x0a:
                self.input_values[i] /= 1000

        # request battery level notifications and poll once
        # subsribe for notifications
        self.device.subscribe(UUID_BATT[0], callback=self.input_callback)
        # poll current value
        data_bytes = self.device.char_read_handle(self.batt_hdl[0])
        self.input_batt = struct.unpack( "<B", data_bytes)[0]

        self.connected = True

        # loop forever ...
        while(self.running):
            self.tx_cond.acquire()
            while not len(self.tx_data):
                self.tx_cond.wait()
            cmds = self.tx_data
            self.tx_data = { }
            self.tx_cond.release()

            # process all commands
            for cmd in cmds:
                # motor command
                if cmd[0] == "M":
                    self.device.char_write_handle(self.output_value_hdl[int(cmd[1:])-1],
                                                  struct.pack("b", cmds[cmd]))
                    
                # input configuration command
                if cmd[0] == "I":
                    self.input_config[int(cmd[1:])-1] = cmds[cmd]
                    self.device.char_write_handle(self.input_conf_hdl[int(cmd[1:])-1],
                                                  struct.pack("b", cmds[cmd]), wait_for_response = True)

        self.adapter.stop()

    def input_callback(self, handle, data_bytes):
        self.input_lock.acquire()
        if self.batt_hdl[0] == handle:
            self.input_batt = struct.unpack( "<B", data_bytes)[0]
            
        for ivh in self.input_values_hdl:
            if ivh == handle:
                i = self.input_values_hdl.index(ivh)
                self.input_values[i] = struct.unpack( "<H", data_bytes)[0]
                if self.input_config[i] == 0x0a:
                    self.input_values[i] /= 1000
        self.input_lock.release()

    def get_input_config_and_values(self):
        self.input_lock.acquire()
        config = self.input_config
        values = self.input_values
        batt = self.input_batt
        self.input_lock.release()
        return config, values, batt

    def stop(self):
        # Make sure all motor commands have been
        # processed before ending the thread
        while len(self.tx_data):
            time.sleep(0.01)

        self.running = False
        # send one last empty event to make sure the thread wakes up
        # and terminates
        self.tx_cond.acquire()
        self.tx_cond.notify()
        self.tx_cond.release()
        
class BtSmartController(object):
    # there's one global bluetooth scanner thread
    hcitool = None

    # global list of known devices
    devices = []
        
    def scan_for_usb_devices():
        """ Find all available devices """

        # scan for usb serial ports
        btsc_ports = [ ]
        for p in serial.tools.list_ports.grep("vid:pid="+BTSC_VIDPID):
            btsc_ports.append( (p.device, p.serial_number ))

        return btsc_ports
        
    def bt_scan_callback(addr):
        if not addr in BtSmartController.devices:
            BtSmartController.devices.append(addr)

    def scan_for_devices():
        if not BtSmartController.hcitool:
            # scan for le devices
            BtSmartController.hcitool = HciTool([ "lescan" ], True, BtSmartController.bt_scan_callback)
            BtSmartController.hcitool.start()

        # get all usb devices
        devices = BtSmartController.scan_for_usb_devices()

        # and also return all bt devices
        for d in BtSmartController.devices:
            devices.append( ( d, d[9:] ) )    # the second half of the mac is our id

        return devices

    def scan_stop():
        # stop the background thread searching for BT devices
        if BtSmartController.hcitool:
            BtSmartController.hcitool.stop()
            BtSmartController.hcitool = None

    def __init__(self, dev):
        """
        Init device associated with the BtSmartController instance
        """

        self.dev = dev
        self.id = dev[1]                         # the usb serial number
        self.ser = None
        self.gatt = None

        # serial device name starts with "/dev/...", a bluetooth device address not
        if dev[0][:5] == "/dev/":
            # for now assume that anything is usb ...
            self.ser = serial.Serial(dev[0], BAUDRATE)
            self.ser.bytesize = serial.EIGHTBITS     # number of bits per bytes
            self.ser.parity = serial.PARITY_NONE     # set parity check: no parity
            self.ser.stopbits = serial.STOPBITS_ONE  # number of stop bits
            self.ser.timeout = 0.1                   # timeout block read
            self.ser.xonxoff = False                 # disable software flow control
            self.ser.rtscts = False                  # disable hardware (RTS/CTS) flow control
            self.ser.dsrdtr = False                  # disable hardware (DSR/DTR) flow control
            self.ser.writeTimeout = 0                # timeout for write

            if self.ser.isOpen():
                self.thread = SerialHandler(self.ser)
                self.thread.start()
            else:
                print("cannot open serial port ")

        else:
            # do pygatt communication in the background
            self.gatt = PyGattThread(dev[0])
            self.gatt.start()

    def __del__(self):
        if self.ser:
            self.thread.stop()
            self.ser.close()
        if self.gatt:
            self.gatt.stop()

    def connectionFailed(self):
        if self.ser:
            return False
        else:
            return self.gatt.failed

    def isConnected(self):
        if self.ser:
            # serial is immediately connected
            return True
        elif self.gatt:
            # bluetooth may take some time ...
            return self.gatt.connected

    def getInfo(self):
        reply = { }
            
        if self.ser:
            reply_bytes = self.getCmdReply( CMD_GET_INFORMATION )
            if not reply_bytes or len(reply_bytes) != 7:
                return None
        
            reply_vals = struct.unpack( ">BBHcBB", reply_bytes)
            reply["hw"] = str(reply_vals[0])
            reply["sw"] = str(reply_vals[1]) + "." + str(reply_vals[2]) + "." + reply_vals[3].decode("utf-8")
            reply["ins"] = reply_vals[4]
            reply["outs"] = reply_vals[5]
        else:
            reply["hw"] = self.gatt.hw
            reply["sw"] = self.gatt.sw

        if self.id: reply["id"] = self.id
        return reply

    def getInputData(self):
        reply = { }
        
        if self.ser:
            reply_bytes = self.getCmdReply( CMD_GET_INPUT_DATA )
            if not reply_bytes or (len(reply_bytes) % 4) != 0:
                return None

            for i in range(int(len(reply_bytes)/4)):
                i_bytes = reply_bytes[4*i:4*i+4]
                i_vals = struct.unpack( ">BBH", i_bytes)
            
                inp = { }
                inp["type"] = None
                name = "I"+str(i_vals[0]+1)
                if i_vals[1] == 0x0 and i_vals[0] == 4:
                    # channel 4 returns the battery voltage
                    name = "BAT"
                    inp["type"]  = "U"
                    inp["value"] =  i_vals[2] / 1000
                elif i_vals[1] == 0x0a:
                    inp["type"]  = "U"
                    inp["value"] =  i_vals[2] / 1000
                elif i_vals[1] == 0x0b:
                    inp["type"]  = "R"
                    inp["value"] =  i_vals[2]
                else:
                    print("unexpected input type", i_vals[1])

                if inp["type"]:
                    reply[name] = inp

        else:
            cfg_name = { 0x0a: "U", 0x0b: "R" }
            config, values,batt = self.gatt.get_input_config_and_values()
            for i in range(len(values)):
                inp = { }
                name = "I"+str(i+1)
                inp["type"] = cfg_name[config[i]]
                inp["value"] = values[i]
                reply[name] = inp

            inp = { }
            name = "BAT"
            inp["type"] = "%"
            inp["value"] = batt
            reply[name] = inp
                
        return reply

    # this is actually named "setAndConfigOutputs, but there doesn't seem
    # to be anything configurable
    def setOutputs(self, config):
        if self.ser:
            data = bytearray()
            for i in config:
                if i[0] == "M":
                    data += struct.pack(">BBh", int(i[1:])-1, 3, config[i])
        
                reply_bytes = self.getCmdReply(CMD_SET_AND_CONFIG_OUTPUTS, data)

                if not reply_bytes or len(reply_bytes) != 1:
                    return None

            return struct.unpack("B", reply_bytes)[0]
        else:
            for i in config:
                # only queue (M)otor requests
                if i[0] == "M":
                    self.gatt.tx( ( i, config[i] ) )

            return 0
    
    def configInputs(self, config):
        cfg_vals = { "U": 0x0a, "R": 0x0b }
        if self.ser:
            data = bytearray()
            for i in config:
                data += struct.pack("BB", int(i[1:])-1, cfg_vals[config[i]])
        
            reply_bytes = self.getCmdReply(CMD_CONFIG_INPUTS, data)

            if not reply_bytes or len(reply_bytes) != 1:
                return None

            return struct.unpack("B", reply_bytes)[0]
        else:
            for i in config:
                # only queue (I)nput requests
                if i[0] == "I":
                    self.gatt.tx( ( i, cfg_vals[config[i]] ) )

            return 0

    def getCmdReply(self, cmd, data = None):
        # TODO: add timeout
        self.thread.tx( cmd, data )
        # wait for result
        while True:
            reply = self.thread.get_reply( cmd )
            if reply: break
            time.sleep(0.01)
            
        return reply
            
class SerialHandler(threading.Thread): 
    def __init__(self, ser): 
        threading.Thread.__init__(self) 
        self.ser = ser
        self.state = ( "IDLE", 0 )
        self.cmd = None
        self.len = None
        self.stopping = False
        self.stopped = False
        self.payload = None
        self.tx_queue = queue.Queue()
        self.rx_queue = queue.Queue()

    def tx(self, cmd, data = None):
        if self.state[0] == "IDLE":
            # send directly if idle
            self.tx_now( cmd, data )
        else:
            # queue otherwise
            print("Warning: queued!!!")
            self.tx_queue.put( (cmd, data) )
            # TODO: process tx queue
            
    def tx_now(self, cmd, data = None):
        # expect reply
        self.state = ( "SOF", 0 )
        if not data:
            self.ser.write( struct.pack(">HIH", 0x5aa5, cmd, 0) )
        else:
            self.ser.write( struct.pack(">HIH", 0x5aa5, cmd, len(data)) )
            self.ser.write( data )
        
    def stop(self):
        self.stopping = True
        while(not self.stopped):
            time.sleep(0.01)

    def run(self): 
        while not self.stopping:
            try:
                b = self.ser.read()
            except TypeError:
                self.stopping = True
                break
            
            # received data?
            if len(b) >= 1:
                ch = struct.unpack('B',b)[0]
                # print("RX:", ch, len(b), self.state[0])

                if self.state[0] == "IDLE":
                    print("Unexpected data while idle", ch)
                
                elif self.state[0] == "SOF":
                    if self.state[1] == 0 and ch == 0x5a:
                        self.state = ("SOF", 1)
                    elif self.state[1] == 1 and ch == 0xa5:
                        self.state = ("CMD", 0)
                        self.cmd = 0
                    else:
                        self.state = ("SOF", 0)

                elif self.state[0] == "CMD":
                    self.cmd = 256 * self.cmd + ch;
                    self.state = ("CMD", self.state[1]+1)
                    if self.state[1] == 4:
                        self.state = ( "LEN", 0)
                        self.len = 0

                elif self.state[0] == "LEN":
                    self.len = 256 * self.len + ch;
                    self.state = ("LEN", self.state[1]+1)
                    if self.state[1] == 2:
                        if not self.len:
                            self.reply_done()
                            # no payload -> just get idle
                            self.state = ( "IDLE", 0 )
                        else:
                            self.state = ( "DAT", self.len )
                            self.payload = bytearray()
                    
                elif self.state[0] == "DAT":
                    self.payload.append(ch)
                    self.state = ("DAT", self.state[1]-1)
                    if not self.state[1]:
                        self.reply_done()
                        # done with payload
                        self.state = ( "IDLE", 0 )
                    
                else:
                    print("Unknown state", '0x{0:08x}'.format(self.cmd), self.len)

        self.stopped = True
                    
    def reply_done(self):
        # print("REPLY:", '0x{0:08x}'.format(self.cmd), self.len, self.payload)
        self.rx_queue.put( (self.cmd, self.payload) )

    def get_reply(self, cmd):
        if self.rx_queue.empty():
            return None

        # fetch reply from queue
        reply = self.rx_queue.get()
        if reply[0] != cmd:
            print("unexpected reply code", reply[0], cmd)
            return None

        # return the payload
        return reply[1]
