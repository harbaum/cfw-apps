#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 3Dprt.py - 3D printer driver for Fischertechnik TXT
# (c) 2016 by Till Harbaum <till@harbaum.org>
#
# Update: scp 3dprt.py root@txt:/opt/ftc/apps/user/dd8a2020-10f7-4d9f-ad2f-2177ce6c60ff

import sys, time, select
import serial, functools
from TouchStyle import *

# get sane defaults for the printer device
if 'FT3DPRINTER' in os.environ:
    PORT=os.environ.get('FT3DPRINTER')
else:
    if platform.machine() == "armv7l":
        PORT="/dev/ttyACM0"
    else:
        PORT="/tmp/com_app"

BAUDRATE=250000

HOTEND_MAX_TEMP=250.0
HOTEND_TEMP=195.0

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))

# a seperate thread controls the printer
class PrinterThread(QThread):
    rx = pyqtSignal(str)
    connection_ok = pyqtSignal()
    connection_failed = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self):
        super(PrinterThread,self).__init__()
        self.output_queue = []
        self.outputs = []
        self.inputs = [ ]
        self.rx_line_buf = ""
        self.wakeup_pipe = os.pipe()
        self.file = None
        self.line_number = 0
        self.outstanding = None

    def ack_line(self, n):
        print("ACK", n)
        ok = (n == self.outstanding)
        # TODO: handle missed lines!!
        self.outstanding = None    # outstanding line has been ack'd
        return ok
        
    def checksum(self,s):
        return functools.reduce(lambda x,y:x^y, map(ord, s))

    def send_cmd(self, cmd):
        # add line number and checksum
        cmd_str = "N"+str(self.line_number)+" "             # line number
        cmd_str += cmd
        cmd_str += "*" + str(self.checksum(cmd_str)) + "\n" # checksum + return
        
        print("TX:", cmd_str, end="")
        self.outstanding = self.line_number
        self.s.write(cmd_str.encode())

        self.line_number += 1                               # increae line number

    def wakeup(self):
        os.write(self.wakeup_pipe[1], b'\0')

    def tx(self, cmd):
        if self.s:
#            if not self.outputs:
#                # only send if we are not waiting for an ack/ok
#                if not self.outstanding:
#                    # send directly if nothing is currently being sent
#                    self.send_cmd(cmd)
#                    self.outputs = [ self.s ]
#                    # send trigger to select as it's currently blocking
#                    # since it listens for reads only
#                    self.wakeup()
#            else:
#                # otherwise append to list of queued commands
#                self.output_queue.append(cmd)

            # never send directly (tx is called from outside the thread).
            # Always let the thread do this
            self.output_queue.append(cmd)
            if not self.outputs:
                # if thread is not waiting for output to become ready, then
                # wake it up to do this
                self.outputs = [ self.s ]
                self.wakeup()

    def get_next_command_from_file(self):
        if not self.file:
            return None

        # fetch a line
        while True:
            # check if there are still command fragments in the buffer
            if self.codes:
                # a command is complete if we have a current
                # command code and if there's a next command
                # found (or the end of the file)
                code = self.codes.pop(0)

                # check if this is a command code
                if code[0] == 'M' or code[0] == 'G':
                    result = None
                    # save current command to return it
                    if self.command_code:
                        # try to keep track of layer for progress bar
                        result = (self.command_code, self.command_parm)

                    # start buffering a new command
                    self.command_code = code
                    self.command_parm = []

                    # return current command
                    if result:
                        return result
                else:
                    self.command_parm.append(code)

            else:
                line = self.file.readline()
                if not line:  # reached and of file
                    self.file = None
                    self.progress.emit(100)

                    # return the last command still buffered
                    return (self.command_code, self.command_parm)
                else:
                    self.progress.emit(100.0 * self.file.tell() / self.filesize)

                code_line = line.split(';')[0].strip()
                if code_line != "":
                    # seperate line into single codes
                    self.codes = code_line.split()

    def file_cmd_tx(self, cmd):
        # assemble complete command string
        cmd_str = cmd[0]                                 # command
        for i in cmd[1]: cmd_str += " "+i                # parameters
        return cmd_str

    def stop_print(self):
        self.file = None

        # disabel hardware
        self.tx("M104 S0")  # turn off hotend
        self.tx("M84")      # turn off all motors

    def do_print(self, name):
        if self.s:
            self.command_code = None
            self.command_parm = []
            self.codes = []

            filename = os.path.join(LOCAL_PATH, "gcodes", name) + ".gcode"
            self.filesize = os.path.getsize(filename)
            self.file = open(filename, 'r')

            # send trigger to select as it's currently blocking
            # since it listens for reads only
            self.wakeup()

    def run(self):
        try:
            # The Serial object that the printer is communicating on.
            self.s = serial.Serial(PORT, BAUDRATE, timeout=3)
            self.connection_ok.emit()
            self.inputs = [ self.s, self.wakeup_pipe[0] ]
            self.tx("M110")  # reset line numbering

        except serial.serialutil.SerialException:
            self.s = None
            self.connection_failed.emit()

        while(self.s != None):
            # Wait for at least one of the sockets to be ready
            r, w, e = select.select(self.inputs, self.outputs, self.inputs)

            # this was just an event to interrupt the select call
            # ignore the data itself
            if self.wakeup_pipe[0] in r:
                os.read(self.wakeup_pipe[0], 1)

            if self.s in r:
                k = self.s.read().decode()
                if k == '\n':
                    # received a complete command ...
                    self.rx.emit(self.rx_line_buf.strip())
                    self.rx_line_buf = ""
                elif k != '\r': 
                    self.rx_line_buf += k

            if self.s in w:
                if not self.outstanding:
                    # check if there's more in the queue to be sent
                    if self.output_queue:
                        c = self.output_queue.pop(0)
                        self.send_cmd(c)
                    elif self.file:
                        # if there's an open file, then get something
                        # to send
                        cmd = self.get_next_command_from_file()
                        if cmd:
                            cmd_str = self.file_cmd_tx(cmd)
                            self.send_cmd(cmd_str)

                    # if nothing is to be sent, remove descriptor from list
                    if not self.output_queue and not self.file:
                        self.outputs = [ ]

            if self.s in e:
                print("Client connection lost ...")
                self.s = None

            # if there's a file open then we sure have something to write
            if self.file:
                self.outputs = [ self.s ]

class Printer(QObject):
    progress = pyqtSignal(int)
    connection_ok = pyqtSignal()
    connection_failed = pyqtSignal()
    temperature = pyqtSignal(float)
    position = pyqtSignal(float,float,float)

    def __init__(self, parent=None):
        super(Printer,self).__init__(parent)

        # start background thread to monitor the
        # printer
        self.thread = PrinterThread()

        # connection to server thread to receive data
        self.thread.rx[str].connect(self.on_rx)
        self.thread.connection_ok.connect(self.on_connected)
        self.thread.connection_failed.connect(self.on_connection_failed)
        self.thread.progress[int].connect(self.on_progress)

        self.thread.start()

        # start a qtimer to poll the temperature
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000)

    def on_timer(self):
        self.thread.tx("M105")             # request hotend temp every second

    def on_rx(self, str):
        print("RX:", str)

        new_x = None
        new_y = None
        new_z = None

        # check for special reply messages
        if(str[:6].lower() == "error:"):
            print(">>>>> ERROR", str[6:])
        elif str[:2].lower() == "ok":
            items = str.split()
            if len(items) > 1 and items[1].isdigit():
                self.thread.ack_line(int(items[1]))
        elif str[:8].lower() == "extruder":
            pass ## dunno what to do with htis
        else:
            # received a reply from the printer
            # parse it
            items = str.split()

            # parse all items
            for i in items:
                if ':' in i:
                    code,val = i.split(':')
                    if code == 'C':
                        pass  # dunno what this is
                    elif code == 'T':
                        self.temperature.emit(float(val))
                    elif code == 'X':
                        new_x = float(val)
                    elif code == 'Y':
                        new_y = float(val)
                    elif code == 'Z':
                        new_z = float(val)
                    elif code == 'E':
                        pass  # ignore extruder position
                    elif code == 'B':
                        pass  # we don't care for the bed temperature
                    elif code == '@':
                        pass  # whatever that is
                    elif code == 'TargetExtr0':
                        pass  # ignore echo of extruder temperature
                    else:
                        print("unknown:", i)
                elif i[0] == '/':
                    # repetierfirmware sends e.g. /[target temp]
                    pass

        # if any of the coordinates have change report it
        if new_x != None or new_y != None or new_z != None:
            self.position.emit(new_x, new_y, new_z)

    def on_connected(self):
        #print("PRINTER: Printer connected")
        self.connection_ok.emit()

    def on_connection_failed(self):
        #print("PRINTER: Printer connection failed")
        self.connection_failed.emit()

    def on_cmd_out(self, cmd):
        # print("PRINTER: request to send cmd", cmd)
        self.thread.tx(cmd)

    def on_progress(self, val):
        self.progress[int].emit(val)

    def do_print(self, name):
        self.thread.do_print(name)

    def stop(self):
        self.thread.stop_print()
        
class ExpandingButton(QPushButton):
    def __init__(self, str = None, parent = None):
        QPushButton.__init__(self, str, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

class StepButton(ExpandingButton):
    param = pyqtSignal(str)

    def __init__(self, name, axis, dir, parent = None):
        ExpandingButton.__init__(self, None, parent)
        self.control = parent
        pix = QPixmap(os.path.join(LOCAL_PATH, "dir" + name + ".png"))
        icn = QIcon(pix)
        self.setIcon(icn)
        self.setIconSize(pix.size())

        self.clicked.connect(self.on_clicked)
        self.axis = axis
        self.dir = dir

    def on_clicked(self):
        s = self.axis + str(self.dir * self.control.get_step_factor())
        self.param.emit(s)

class HomeButton(ExpandingButton):
    param = pyqtSignal(str)

    def __init__(self, name, axis, parent = None):
        ExpandingButton.__init__(self, None, parent)

        pix = QPixmap(os.path.join(LOCAL_PATH, "home" + name + ".png"))
        icn = QIcon(pix)
        self.setIcon(icn)
        self.setIconSize(pix.size())

        self.clicked.connect(self.on_clicked)
        self.axis = axis

    def on_clicked(self):
        self.param.emit(self.axis)

class ManualWidget(QWidget):
    cmd = pyqtSignal(str)

    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        # a widget combining all controls vertically
        layout = QVBoxLayout()
        layout.setContentsMargins(2,2,2,2)

        # the three current coordinates
        coo_w = QWidget()
        coo = QHBoxLayout()
        coo.setContentsMargins(0,0,0,0)
        coo_w.setLayout(coo)
        self.x = QLabel("")
        self.x.setObjectName("tinylabel")
        self.x.setAlignment(Qt.AlignCenter)
        coo.addWidget(self.x)
        self.y = QLabel("")
        self.y.setObjectName("tinylabel")
        self.y.setAlignment(Qt.AlignCenter)
        coo.addWidget(self.y)
        self.z = QLabel("")
        self.z.setObjectName("tinylabel")
        self.z.setAlignment(Qt.AlignCenter)
        coo.addWidget(self.z)

        layout.addWidget(coo_w)
        layout.addStretch()

        # a widget combining x/y and z controls side by side
        move_w = QWidget()
        move = QHBoxLayout()
        move.setContentsMargins(0,0,0,0)
        move_w.setLayout(move)

        # a grid containing the x/y direction buttons
        xy_grid_w = QWidget()
        xy_grid = QGridLayout()
        xy_grid_w.setLayout(xy_grid)
        xy_grid.setSpacing(4)
        xy_grid.setContentsMargins(0,0,0,0)

        # X/Y axes
        up = StepButton("_up", "Y", 1, self)
        up.param[str].connect(self.on_dir_clicked)
        xy_grid.addWidget(up,0,1)
        down = StepButton("_down", "Y", -1, self)
        down.param[str].connect(self.on_dir_clicked)
        xy_grid.addWidget(down,2,1)
        left = StepButton("_left", "X", -1, self)
        left.param[str].connect(self.on_dir_clicked)
        xy_grid.addWidget(left,1,0)
        right = StepButton("_right", "X", 1, self)
        right.param[str].connect(self.on_dir_clicked)
        xy_grid.addWidget(right,1,2)

        home_x = HomeButton("_x", "X", self)
        home_x.param[str].connect(self.on_home_clicked)
        xy_grid.addWidget(home_x,2,0)
        home_y = HomeButton("_y", "Y", self)
        home_y.param[str].connect(self.on_home_clicked)
        xy_grid.addWidget(home_y,2,2)
        home = HomeButton("", None, self)
        home.param[str].connect(self.on_home_clicked)
        xy_grid.addWidget(home,0,0)

        move.addWidget(xy_grid_w)
        move.addStretch()

        # a grid containing the z direction buttons
        z_grid_w = QWidget()
        z_grid = QGridLayout()
        z_grid_w.setLayout(z_grid)
        z_grid.setSpacing(4)
        z_grid.setContentsMargins(0,0,0,0)

        # Z axis
        z_up = StepButton("_up", "Z", 1, self)
        z_up.param[str].connect(self.on_dir_clicked)
        z_grid.addWidget(z_up,0,0)
        z_down = StepButton("_down", "Z", -1, self)
        z_down.param[str].connect(self.on_dir_clicked)
        z_grid.addWidget(z_down,2,0)

        home_z = HomeButton("_z", "Z", self)
        home_z.param[str].connect(self.on_home_clicked)
        z_grid.addWidget(home_z,1,0)

        move.addWidget(z_grid_w)

        # Extruder?

        layout.addWidget(move_w)
        layout.addStretch()

        # Step slider
        step_w = QWidget()
        step = QHBoxLayout()
        step.setContentsMargins(0,0,0,0)
        step_w.setLayout(step)

        step_label = QLabel("Step:")
        step_label.setObjectName("tinylabel")
        step.addWidget(step_label)

        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setPageStep(1)
        self.step_slider.setRange(0,3)   # 0.1,1,10,100
        self.step_slider.setValue(1)     # 1
        self.step_slider.valueChanged.connect(self.on_step_changed)
        step.addWidget(self.step_slider)

        self.step_label = QLabel(str(self.slider_get_step()) + "mm")
        self.step_label.setObjectName("tinylabel")
        self.step_label.setFixedWidth(50)
        self.step_label.setAlignment(Qt.AlignCenter)
        step.addWidget(self.step_label)

        layout.addWidget(step_w)
        layout.addStretch()

        # Temperature "progress bar" and hotend control
        hotend_w = QWidget()
        hotend = QHBoxLayout()
        hotend.setContentsMargins(0,0,0,0)
        hotend_w.setLayout(hotend)

        self.he = QToolButton()
        self.he.setProperty("on", False)
        pix = QPixmap(os.path.join(LOCAL_PATH, "hotend_off.png"))
        self.he.setIcon(QIcon(pix))
        self.he.setIconSize(pix.size())
        self.he.clicked.connect(self.on_hotend_toggle)
        hotend.addWidget(self.he)

        self.temp = QProgressBar()
        self.temp.setRange(0,HOTEND_MAX_TEMP)
        self.temp.setValue(0)
        self.temp.setFormat("- °C")
        self.temp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hotend.addWidget(self.temp)

        # extrude and reverse extrude
        ext_in = StepButton("_up", "E", -1, self)
        ext_in.param[str].connect(self.on_ext_clicked)
        hotend.addWidget(ext_in)
        ext_out = StepButton("_down", "E", +1, self)
        ext_out.param[str].connect(self.on_ext_clicked)
        hotend.addWidget(ext_out)

        layout.addWidget(hotend_w)

        # initialize some output
        self.show_temperature(0)
        self.show_position(None,None,None)

        self.setLayout(layout)

    def on_hotend_toggle(self):
        # change state of hotend
        new_state = not self.sender().property("on")
        self.sender().setProperty("on", new_state)
        if new_state:
            self.cmd.emit("M104 S" + str(HOTEND_TEMP))
            pix = QPixmap(os.path.join(LOCAL_PATH, "hotend_on.png"))
        else:
            self.cmd.emit("M104 S0")
            pix = QPixmap(os.path.join(LOCAL_PATH, "hotend_off.png"))
        self.sender().setIcon(QIcon(pix))

    def slider_get_step(self):
        factors = [ 0.1, 1, 10, 100 ]
        return factors[self.step_slider.value()]

    def on_step_changed(self, val):
        if val < 2:
            self.step_label.setText(str(self.slider_get_step()) + "mm")
        else:
            self.step_label.setText(str(int(self.slider_get_step()/10)) + "cm")

    def get_step_factor(self):
        return self.slider_get_step()

    def on_dir_clicked(self, str):
        self.cmd.emit("G91")
        self.cmd.emit("G0 " + str + " F3000")
        self.cmd.emit("G90")
        self.cmd.emit("M114")

    def on_ext_clicked(self, str):
        self.cmd.emit("G0 " + str + " F100")

    def on_home_clicked(self, str):
        if not str:
            self.cmd.emit("G28")
            self.cmd.emit("G92 E0")
        else:
            self.cmd.emit("G28 " + str + "0") 
        self.cmd.emit("M114")
            
    def show_position(self, x, y, z):
        if x != None: self.x.setText("X:{0:.2f}".format(x))
        else:         self.x.setText("X:-")
        if y != None: self.y.setText("Y:{0:.2f}".format(y))
        else:         self.y.setText("Y:-")
        if z != None: self.z.setText("Z:{0:.2f}".format(z))
        else:         self.z.setText("Z:-")

    def show_temperature(self, temp):
        if temp > HOTEND_MAX_TEMP: temp = HOTEND_MAX_TEMP
        if temp < 0: temp = 0
        v = temp / HOTEND_MAX_TEMP;
        style = "QProgressBar { font: bold 16px; color: black; border: 3px inset lightgrey; } QProgressBar::chunk {background: QLinearGradient(x1: 0, y1: 0, x2: 1, y2: 0,stop: 0 #0f0,stop: "

        if(v < 0.5):
            # 0..0.5 = from green to yellow
            style += "1 rgb("+str(2*v*255)+",255,0)"
        else:
            # 0.5..1 = from green to yellow and then to red
            style += str(1.5-v)+" #ff0,stop: 1 rgb(255,"+str( 2*(1-v)*255 )+",0)"

        style += "); }"
        self.temp.setStyleSheet(style)
        self.temp.setValue(temp)

        # check if hotend is supposed to be on. Then also display
        # target temperature
        # if self.he.property("on"):
        # self.temp.setFormat("{0:.2f}".format(temp)+"\r\n/"+str(HOTEND_TEMP)+" °C")
        # else:
        self.temp.setFormat("{0:.2f}°C".format(temp))

import cProfile

# a seperate thread parses the gcode
class GcodeThread(QThread):
    finished = pyqtSignal(bool,object)
    
    def __init__(self, name):
        super(GcodeThread,self).__init__()
        self.running = True
        self.error = None
        self.name = name

    def run(self):
        self.reset()
        with open(os.path.join(LOCAL_PATH, "gcodes", self.name) + ".gcode", 'r') as f:
            for line in f:
                if not self.running or self.error:
                    self.finished.emit(False, self.error)
                    return
                
                self.parse_file_line(line)
                
            self.process_command()
            self.print_result()
        
    def stop(self):
        self.running = False

    def reset(self):
        # values used during parse
        self.command = None
        self.units = 1     # mm
        self.abs = True
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.e = 0.0
        self.f = 0.0   # feed rate

        # "result" values
        self.esum = 0.0          # total extruded
        self.layers = { }
        self.xmin = float("inf")
        self.xmax = float("-inf")
        self.ymin = float("inf")
        self.ymax = float("-inf")
        self.zmin = float("inf")
        self.zmax = float("-inf")
        self.time = 0.0
        
    # process 'M' gcode
    def process_command_m(self, id, parms):
        if id == 82:
            # print("Extruder absolute mode")
            pass
        elif id == 84:
            # print("Stop idle hold")
            pass
        elif id == 104:
            # print("Extruder temp: {0:.1f}°C".format(float(parms['S'])))
            pass
        elif id == 106:
            # print("Fan on: {0:.1f}%".format(float(parms['S'])/2.55))
            pass
        elif id == 107:
            # print("Fan off")
            pass
        elif id == 109:
            # print("Extruder temp wait: {0:.1f}°C".format(float(parms['S'])))
            pass
        else:
            print("M", id, parms)
            self.error = "Unsupported GCode M"+str(id)
        
    def check_limits(self):
        # check for upper and lower coordinate limits
        if self.x > self.xmax: self.xmax = self.x
        if self.x < self.xmin: self.xmin = self.x
        if self.y > self.ymax: self.ymax = self.y
        if self.y < self.ymin: self.ymin = self.y
        if self.z > self.zmax: self.zmax = self.z
        if self.z < self.zmin: self.zmin = self.z
        self.layers[self.z] = True
            
    # process 'G' gcode
    def process_command_g(self, id, parms):
        if id == 0 or id == 1:
            # check limits from point where extruding starts ...
            if 'E' in parms: self.check_limits()

            # remember previous position to determine travel distance
            prev_x = self.x
            prev_y = self.y
            prev_z = self.z
            
            if self.abs:
                if 'X' in parms: self.x = self.units * float(parms['X'])
                if 'Y' in parms: self.y = self.units * float(parms['Y'])
                if 'Z' in parms: self.z = self.units * float(parms['Z'])
                if 'E' in parms: self.e = self.units * float(parms['E'])
                if 'F' in parms: self.f = self.units * float(parms['F']) / 60.0  # in mm/s
            else:
                # stop parser
                self.error = "relative movement is unsupported"

            # ... to point where extruding ends
            if 'E' in parms: self.check_limits()

            # and sum up time
            dist = ((self.x - prev_x)**2 + (self.y - prev_y)**2 + (self.z - prev_z)**2)**0.5
            self.time += dist/self.f   # distance in mm and feedrate in mm/s -> time in s
            
        elif id == 21:
            self.units = 1       # mm
        elif id == 28:
            self.x = 0.0         # home all axes
            self.y = 0.0
            self.z = 0.0
        elif id == 90:
            self.abs = True      # absolute positioning
        elif id == 91:
            self.abs = False     # relative positioning
        elif id == 92:
            # set position
            if 'X' in parms: self.x = self.units * float(parms['X'])
            if 'Y' in parms: self.y = self.units * float(parms['Y'])
            if 'Z' in parms: self.z = self.units * float(parms['Z'])

            # extruder is a little more complex and we need to remember
            # previously extruded filament before reseting the extruder position
            if 'E' in parms:
                if self.e > 0: self.esum += self.e
                self.e = self.units * float(parms['E'])
        else:
            print("G", id, parms)
            self.error = "Unsupported GCode G"+str(id)
            
    # process the last buffered command
    def process_command(self):
        if self.command:
            if self.command[0] == 'M':
                self.process_command_m(int(self.command[1:]), self.parameters)
            elif self.command[0] == 'G':
                self.process_command_g(int(self.command[1:]), self.parameters)
            
            self.command = None
 
    def parse_code(self, cmd):
        if cmd[0] == 'M' or cmd[0] == 'G':
            # execute previous code
            self.process_command()
            self.command = cmd
            self.parameters = { }
        else:
            self.parameters[cmd[0]] = cmd[1:]

    def parse_code_line(self, line):
        # split into single codes
        for cmd in line.split():
            self.parse_code(cmd.strip())
        
    def parse_file_line(self, line):
        # ignore everything after semicolon
        code_line = line.split(';')[0].strip()

        if code_line != "":
            self.parse_code_line(code_line)

    def print_result(self):
        # assemble results
        result = {}
        result["filament"] = self.esum
        result["size"] = (self.xmax - self.xmin, self.ymax - self.ymin,
                          self.zmax - self.zmin)
        result["layers"] = len(self.layers)
        result["time"] = self.time
        result["name"] = self.name
        
        self.finished.emit(True, result)
         
# a simple gcode file parser. Parses the file in the background
# to keep the UI fluid
class GCode(QObject):
    info = pyqtSignal(bool,object)
    
    def __init__(self, name = None, parent = None):
        super(GCode,self).__init__(parent)
        self.name = name

        # start parser thread
        self.thread = GcodeThread(name)

        # connect to threads output
        self.thread.finished[bool,object].connect(self.on_finished)

        self.thread.start()
        
    def __del__(self):
        self.thread.stop()
        while self.thread.isRunning():
            pass

    def on_finished(self, ok, result):
        # forward signal
        self.info.emit(ok, result)

class PrintDialog(TouchDialog):
    def __init__(self, info, printer, parent = None):
        TouchDialog.__init__(self, "Printing", parent)
        self.info = info
        self.printer = printer

        layout = QVBoxLayout()

        layout.addStretch()

        img = QLabel()
        pix = QPixmap(os.path.join(LOCAL_PATH, "gcodes", info["name"]) + ".png")
        img.setPixmap(pix)
        img.setAlignment(Qt.AlignCenter)
        layout.addWidget(img)

        name = QLabel(info["name"])
        name.setObjectName("tinylabel")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        layout.addStretch()

        # a prograss bar
        self.progress = QProgressBar()
        self.progress.setRange(0,100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        layout.addStretch()

        # a big stop/close button
        self.sbut = QPushButton("Stop!")
        self.sbut.clicked.connect(self.close)
        layout.addWidget(self.sbut)

        self.centralWidget.setLayout(layout)

    def close(self):
        # tell printer object to stop printing
        self.printer.stop()
        TouchDialog.close(self)

    def show_progress(self, progress):
        self.progress.setValue(progress)
        # disable stop button if done
        if progress == 100:
            self.sbut.setDisabled(True)
        
class SelectorWidget(QWidget):
    do_print = pyqtSignal(object)

    def __init__(self, printer, parent = None):
        QWidget.__init__(self, parent)
        self.printer = printer
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        # add a hbox with arrows and image
        image_box = QWidget()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,0,0,0)
        image_box.setLayout(hbox)

        # scan for files to be selected
        self.objects = [ ]
        gcodes_path = os.path.join(LOCAL_PATH, "gcodes")
        for file in os.listdir(gcodes_path):
            if file.endswith(".gcode"):
                # check if there's a matching png
                png = os.path.splitext(os.path.join(gcodes_path, file))[0] + ".png"
                if os.path.isfile(png):
                    self.objects.append(os.path.splitext(file)[0])

        if len(self.objects) > 0:
            lbut = ExpandingButton()
            pix = QPixmap(os.path.join(LOCAL_PATH, "dir_left.png"))
            icn = QIcon(pix)
            lbut.setIcon(icn)
            lbut.setIconSize(pix.size())
            lbut.clicked.connect(self.on_prev)

            hbox.addWidget(lbut)
            self.img = QLabel()
            hbox.addWidget(self.img)

            rbut = ExpandingButton()
            pix = QPixmap(os.path.join(LOCAL_PATH, "dir_right.png"))
            icn = QIcon(pix)
            rbut.setIcon(icn)
            rbut.setIconSize(pix.size())
            hbox.addWidget(rbut)
            rbut.clicked.connect(self.on_next)

            layout.addStretch()

            self.name = QLabel("")
            self.name.setWordWrap(True)
            self.name.setAlignment(Qt.AlignCenter)
            self.name.setObjectName("tinylabel")
            layout.addWidget(self.name)

            layout.addWidget(image_box)

            # the info texts
            self.lbl_layers = QLabel()
            self.lbl_layers.setAlignment(Qt.AlignCenter)
            self.lbl_layers.setObjectName("tinylabel")
            layout.addWidget(self.lbl_layers)

            self.lbl_size = QLabel()
            self.lbl_size.setAlignment(Qt.AlignCenter)
            self.lbl_size.setObjectName("tinylabel")
            layout.addWidget(self.lbl_size)

            self.lbl_time = QLabel()
            self.lbl_time.setAlignment(Qt.AlignCenter)
            self.lbl_time.setObjectName("tinylabel")
            layout.addWidget(self.lbl_time)

            self.lbl_filament = QLabel()
            self.lbl_filament.setAlignment(Qt.AlignCenter)
            self.lbl_filament.setObjectName("tinylabel")
            layout.addWidget(self.lbl_filament)

            layout.addStretch()

            self.pbut = QPushButton("Print!")
            self.pbut.setDisabled(True)
            self.pbut.clicked.connect(self.on_print)
            layout.addWidget(self.pbut)

            self.index = 0
            self.select(self.index)
        else:
            lbl = QLabel("No object files found!")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

    def on_prev(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.objects)-1

        self.select(self.index)

    def on_next(self):
        self.index += 1
        if self.index == len(self.objects):
            self.index = 0

        self.select(self.index)

    def select(self, index):
        name = self.objects[index]
        self.name.setText(name)

        # get image file name
        img = os.path.join(LOCAL_PATH, "gcodes", name) + ".png"
        pix = QPixmap(img)
        self.img.setPixmap(pix)

        self.pbut.setDisabled(True)
        self.lbl_layers.setText("")
        self.lbl_size.setText("Please wait.")
        self.lbl_time.setText("Analysing object ...")
        self.lbl_filament.setText("")

        # start background parser
        self.gcode = GCode(name)
        # connect to parsers output
        self.gcode.info[bool,object].connect(self.on_gcode_info)

    def on_gcode_info(self,ok,info):
        if ok:
            if not "layers" in info: layers_str = "unknown"
            else: layers_str = str(info["layers"])
            self.lbl_layers.setText("Layers: " + layers_str)

            if not "size" in info: size_str = "unknown"
            else:
                size_str = "{0:.1f} * {1:.1f} * {2:.1f}mm³".format(info["size"][0], info["size"][1], info["size"][2])
            self.lbl_size.setText("Size: " + size_str)

            if not "time" in info: time_str = "unknown"
            else:
                qtime = QTime(0,0)
                qtime = qtime.addSecs(info["time"])
                time_str = "ca. " + qtime.toString()
                
            self.lbl_time.setText("Time: " + time_str)

            if not "filament" in info: filament_str = "unknown"
            else: 
                filament = info["filament"]
                if filament > 1000:
                    filament_str = "{0:.1f}m / ~{1:.1f}g".format(filament/1000, filament/330)
                else:
                    filament_str = "{0:.1f}cm / ~{1:.1f}g".format(filament/10, filament/330)

            self.lbl_filament.setText("Filament: " + filament_str)

            # finally enable the print button
            self.pbut.setEnabled(True)
            self.pbut.setProperty("info", info)
        else:
            print("GCode parsing failed", info)

    def on_print(self):
        info = self.sender().property("info")
        dialog = PrintDialog(info, self.printer, self)
        self.printer.progress[int].connect(dialog.show_progress)
        # tell printer object what to print
        self.do_print[object].emit(info["name"])
        dialog.exec_()
        
class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        # create the empty main window
        self.w = TouchWindow("3DPrt")

        menu = self.w.addMenu()
        menu_manual = menu.addAction("Manual")
        menu_manual.triggered.connect(self.on_manual)

        # create printer object. This will establish
        # a connection to the printer and start a
        # background process if required
        self.printer = Printer(self.w)

        # connect signals from printer object
        self.printer.connection_ok.connect(self.on_connected)
        self.printer.connection_failed.connect(self.on_connection_failed)

        self.w.show()
        self.exec_()        

    def on_connected(self):
        s = SelectorWidget(self.printer, self.w)
        # connect selector widget with printer object
        s.do_print[object].connect(self.printer.do_print)
        self.w.setCentralWidget(s)

    def on_manual(self):
        dialog = TouchDialog("Manual", self.w)

        # connection ok, draw main gui
        m = ManualWidget(self.w)
        dialog.setCentralWidget(m)

        # forward user generated commands to printer
        m.cmd[str].connect(self.printer.on_cmd_out)

        # send printer replies to gui
        self.printer.temperature[float].connect(m.show_temperature)
        self.printer.position[float,float,float].connect(m.show_position)

        # request a positiom
        self.printer.on_cmd_out("M114")

        dialog.exec_()

    def on_connection_failed(self):
        # the connection to the printer finally failed
        # display error message
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()
        err = QLabel("Error")
        err.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(err)
        lbl = QLabel("No printer controller found. " + 
                     "Please make sure it is " + 
                     "connected to the TXTs USB1 port.")
        lbl.setObjectName("smalllabel")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        
        self.vbox.addWidget(lbl)
        self.vbox.addStretch()
        self.w.centralWidget.setLayout(self.vbox)

    def on_msg(self, msg):
        pass
 
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
