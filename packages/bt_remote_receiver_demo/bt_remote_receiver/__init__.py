#
# python driver for fischertechnik BT remote receiver
#

import os
import time
import threading
import struct
import queue
import pty
import subprocess
import select
import pygatt

# ================ BT parameters ====================
# http://ofalcao.pt/blog/series/wedo-2-0-reverse-engineering
BTSC_VENDOR = "10:45:f8"   # LNT

# TODO: get these from the primary services
def btcr_uuid(a):
    return "2e58{0:04x}-c5c5-11e6-9d9d-cec0c932ce01".format(a)

def bt_uuid(a):
    return "0000{0:04x}-0000-1000-8000-00805f9b34fb".format(a)

UUID_BATT         = [   bt_uuid(0x2a19) ]
UUID_REV          = [   bt_uuid(0x2a27),   bt_uuid(0x2a26) ]
UUID_COMM_CHANNEL = [ btcr_uuid(0x2de2) ]
UUID_OUTPUT_VALUE = [ btcr_uuid(0x3378), btcr_uuid(0x358a),
                      btcr_uuid(0x3666), btcr_uuid(0x37b0) ]

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
                     p[1].lower() == "name" and " ".join(p[2:]).lower() == "bt control receiver"):
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

        self.tx_cond = threading.Condition()
        self.tx_data = { }
        
        self.input_batt = None
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
            self.device = self.adapter.connect(self.addr, timeout=3)
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

        self.adapter.stop()
        
    def input_callback(self, handle, data_bytes):
        self.input_lock.acquire()
        if self.batt_hdl[0] == handle:
            self.input_batt = struct.unpack( "<B", data_bytes)[0]
        self.input_lock.release()
        
    def get_input_config_and_values(self):
        self.input_lock.acquire()
        batt = self.input_batt
        self.input_lock.release()
        return batt

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
        
class BtRemoteReceiver(object):
    # there's one global bluetooth scanner thread
    hcitool = None

    # global list of known devices
    devices = []
        
    def bt_scan_callback(addr):
        if not addr in BtRemoteReceiver.devices:
            BtRemoteReceiver.devices.append(addr)

    def scan_for_devices():
        if not BtRemoteReceiver.hcitool:
            # scan for le devices
            BtRemoteReceiver.hcitool = HciTool([ "lescan" ], True, BtRemoteReceiver.bt_scan_callback)
            BtRemoteReceiver.hcitool.start()

        # return all bt devices
        devices = [ ]
        for d in BtRemoteReceiver.devices:
            devices.append(d)

        return devices

    def scan_stop():
        # stop the background thread searching for BT devices
        if BtRemoteReceiver.hcitool:
            BtRemoteReceiver.hcitool.stop()
            BtRemoteReceiver.hcitool = None

    def __init__(self, dev):
        """
        Init device associated with the BtRemoteReceiver instance
        """

        self.dev = dev

        # do pygatt communication in the background
        self.gatt = PyGattThread(dev)
        self.gatt.start()

    def __del__(self):
        if self.gatt:
            self.gatt.stop()

    def connectionFailed(self):
        return self.gatt.failed

    def isConnected(self):
        if self.gatt:
            # bluetooth may take some time ...
            return self.gatt.connected

    def getInfo(self):
        reply = { }
            
        reply["hw"] = self.gatt.hw
        reply["sw"] = self.gatt.sw

        return reply

    def getInputData(self):
        reply = { }
        
        batt = self.gatt.get_input_config_and_values()
        
        inp = { }
        name = "BAT"
        inp["type"] = "%"
        inp["value"] = batt
        reply[name] = inp
                
        return reply

    
    # this is actually named "setAndConfigOutputs, but there doesn't seem
    # to be anything configurable
    def setOutputs(self, config):
        for i in config:
            # only queue (M)otor requests
            if i[0] == "M":
                self.gatt.tx( ( i, config[i] ) )

    def getCmdReply(self, cmd, data = None):
        self.thread.tx( cmd, data )
        # wait for result
        while True:
            reply = self.thread.get_reply( cmd )
            if reply: break
            time.sleep(0.01)
            
        return reply
            
