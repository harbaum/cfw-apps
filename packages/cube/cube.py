#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys, os, platform, stat, random, time
from TxtStyle import *
import pycuber as pc
import subprocess, errno
import ftrobopy
import copy
import cv2

import scanner

POWERUP_TIME = 1000   # 1 second for compressor and camera to turn on

# the output ports
COMPRESSOR=0
VALVE_GRAB=1
VALVE_PUSH=2
MOTOR_TURN=3

# the input ports
MOTOR_STOP=0

def txt_init():
    txt_ip = os.environ.get('TXT_IP')
    if txt_ip == None: txt_ip = "localhost"
    try:
        txt = ftrobopy.ftrobopy(txt_ip, 65000)
        
        # all outputs normal mode
        M = [ txt.C_OUTPUT, txt.C_OUTPUT, txt.C_OUTPUT, txt.C_OUTPUT ]
        I = [ (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ) ]
        txt.setConfig(M, I)
        txt.updateConfig()
        return txt
    except:
        return None

class AdjustWidget(QWidget):
    def __init__(self, parent=None):
        super(AdjustWidget, self).__init__(parent)
        # boundary values from scanner.py
        self.boundaries = scanner.boundaries()
        # same colors as in scanner.py
        self.colors = [ "#00FF00", "#FFFF00", "#FF8000", "#FF0000", "#0000FF" ]
        self.selected = 2

    def paintEvent(self, QPaintEvent):
        self.arr_w = 2*int(self.height()/3)
        tri_w = int(self.height()/3)
        painter = QPainter()
        painter.begin(self)

        # draw color range
        for x in range(self.width()-2*self.arr_w):
            # make xh range from 0 ...359
            xh = 359 * x / (self.width()-2*self.arr_w)
            color = QColor()
            color.setHsv(xh,255,255)

            # swap B and R since we use it that way
            # in the scanner to avoid having the critical 
            # orange/red boundaries in the ranges border
            tmp = color.red()
            color.setRed(color.blue())
            color.setBlue(tmp)

            painter.setPen(color)
            painter.drawLine(x+self.arr_w, 0, x+self.arr_w, (self.height()-tri_w)/2-1)

            color = QColor("#0000FF")
            for i in range(len(self.boundaries)):
                if xh/2 > self.boundaries[i]:
                    color = QColor(self.colors[i])

            painter.setPen(color)
            painter.drawLine(x+self.arr_w, (self.height()-tri_w)/2, x+self.arr_w, self.height()-tri_w)

        # draw triangles below
        for i in range(len(self.boundaries)):
            x = (self.width()-2*self.arr_w) * self.boundaries[i] / 179

            path = QPainterPath()
            path.moveTo(x + self.arr_w,                  self.height()-int(1*tri_w))
            path.lineTo(x + self.arr_w + int(tri_w/2),   self.height()-1)
            path.lineTo(x + self.arr_w - int(tri_w/2),   self.height()-1)
            path.lineTo(x + self.arr_w,                  self.height()-int(1*tri_w))

            # fill selected triangle in white, other in black
            fill = QColor("black")
            if i == self.selected:
                fill = QColor("white")

            painter.fillPath(path, QBrush(fill))

        # paint the left arrow
        path = QPainterPath()
        path.moveTo(0, int((self.height()-1)/3))
        path.lineTo(3*int(self.arr_w/4), 0)
        path.lineTo(3*int(self.arr_w/4), 2*int((self.height()-1)/3))
        path.lineTo(0, int((self.height()-1)/3))
        painter.fillPath(path, QBrush(QColor("black")))

        # paint the right arrow
        path = QPainterPath()
        path.moveTo(self.width()-1, int((self.height()-1)/3))
        path.lineTo(self.width()-1-3*int(self.arr_w/4), 0)
        path.lineTo(self.width()-1-3*int(self.arr_w/4), 2*int((self.height()-1)/3))
        path.lineTo(self.width()-1, int((self.height()-1)/3))
        painter.fillPath(path, QBrush(QColor("black")))

        painter.end()

    def mousePressEvent(self, event):
        x = event.pos().x()
        old_sel = self.selected

        # click in the color bar range?
        if x > self.arr_w and x < self.width() - self.arr_w:
            # search for closest boudnary
            xh = int(179 * (x-self.arr_w) / (self.width()-2*self.arr_w))
            dist = 1000
            for i in range(len(self.boundaries)):
                d = abs(self.boundaries[i] - xh)
                if d < dist:
                    dist = d
                    self.selected = i
            
            if old_sel != self.selected:
                self.update()
        
        # left arrow
        if x < self.arr_w:
            # only reduce value if it's not zero and if it's still bigger than the
            # previous value to the left
            if ((self.boundaries[self.selected] > 0) and
                ((self.selected == 0) or
                 (self.boundaries[self.selected]-1 > self.boundaries[self.selected-1]))):
                self.boundaries[self.selected] -= 1
                self.boundaries_write_file(self.boundaries)
                scanner.setBoundaries(self.boundaries)
                self.update()

        # right arrow
        if x > self.width() - self.arr_w:
            # only increase value if it's not 180 and if it's still smaller then
            # next value to the right
            if ((self.boundaries[self.selected] < 180) and
                ((self.selected == 4) or
                 (self.boundaries[self.selected]+1 < self.boundaries[self.selected+1]))):
                self.boundaries[self.selected] += 1
                self.boundaries_write_file(self.boundaries)
                scanner.setBoundaries(self.boundaries)
                self.update()

    def boundaries_write_file(self, boundaries):
        base = os.path.dirname(os.path.realpath(__file__))
        colors_dat = os.path.join(base, "colors.dat")
        try:
            with open(colors_dat, 'w') as f:
                print(str(boundaries[0])+","+
                      str(boundaries[1])+","+
                      str(boundaries[2])+","+
                      str(boundaries[3])+","+
                      str(boundaries[4]), file=f)
        except:
            pass

class LiveWidget(QWidget):
    def __init__(self, parent=None):
        super(LiveWidget, self).__init__(parent)

        # initialize camera
        self.video_device = scanner.init()

        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000)

    def sizeHint(self):
        return QSize(220,220)

    def heightForWidth(self,w):
        return w

    def close(self):
        if self.video_device:
            scanner.close(self.video_device)

    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)

        if not self.video_device:
            painter.drawText(QRect(QPoint(0,0), self.size()),
                             Qt.AlignCenter, "No camera");
        else:
            img = scanner.get_calibration_image(self.video_device)
            img = cv2.resize(img,None,fx=2, fy=2) 

            # center on widget
            height, width, byteValue = img.shape
            bytes_per_line = byteValue * width
            xoff = (self.width() - width)/2
            yoff = (self.height() - height)/2

            # hsv to rgb
            cv2.cvtColor(img, cv2.COLOR_BGR2RGB, img)
            mQImage = QImage(img, int(width), int(height),
                             bytes_per_line, QImage.Format_RGB888)

            painter.drawImage(xoff,yoff,mQImage)
            
        painter.end()


class CalibDialog(TxtDialog):
    def __init__(self,parent):

        TxtDialog.__init__(self, "Calib.", parent)

        vbox = QVBoxLayout()

        self.aw = AdjustWidget()
        vbox.addWidget(self.aw)

        self.lw = LiveWidget()
        vbox.addWidget(self.lw)

        self.centralWidget.setLayout(vbox)

    def closeEvent(self, evnt):
        self.lw.close()
        super(CalibDialog, self).closeEvent(evnt)

class AboutDialog(TxtDialog):
    def __init__(self,parent):
        text = '<h2><font color="#fcce04">Cube</font></h2>' \
               '<b>Rubiks cube solver</b><br>' \
               '2016, Till Harbaum<br>' \
               '<h2><font color="#fcce04">Credits</font></h2>' \
               '<b>' + pc.__title__ + ' ' + pc.__version__ + \
               '</b><br>Adrian Liaw<br>' \
               '<b>Two-Phase Algorithm</b>' \
               '<br>Herbert Kociemba<br>' \
               '<b>Two-Phase C port</b>' \
               '<br>Maxim Tsoy<br>' \
               '<b>App Icon</b>'\
               '<br>Booyabazooka, Meph666'

        TxtDialog.__init__(self, "About", parent)
        
        txt = QTextEdit()
        txt.setReadOnly(True)
        
        font = QFont()
        font.setPointSize(16)
        txt.setFont(font)
    
        txt.setHtml(text)

        self.setCentralWidget(txt)

class CubeWidget(QWidget):
    def __init__(self, cube, parent=None):
        super(CubeWidget, self).__init__(parent)
        
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

        self.cube = cube

        # draw a square
    def draw_square(self, painter, x, y, size, color, base_color):
        painter.setPen(base_color)
        painter.setBrush(color)
        painter.drawRect(x, y, size-1, size-1)

    def heightForWidth(self,w):
        return 3*w/4

    def cube_color(self, colour):
        cube2qt = {
            "red":     QColor("#FF0000"), "yellow":  QColor("#FFFF00"), "green":   QColor("#00FF00"),
            "white":   QColor("#FFFFFF"), "orange":  QColor("#FFA500"), "blue":    QColor("#0000FF"),
            "unknown": QColor("#000000")
        }
        return cube2qt[colour]

    def draw_face(self, painter, xb, yb, size, face):
        for x in range(3):
            for y in range(3):
                self.draw_square(painter, xb+size*x, yb+size*y, size, 
                                 self.cube_color( face[y][x].colour ), QColor("#000000"))

    def paintEvent(self, QPaintEvent):
        size = min(self.height()/3, self.width()/4)/3
 
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self.draw_face(painter, size*3, size*0, size, self.cube.U)
        self.draw_face(painter, size*0, size*3, size, self.cube.L)
        self.draw_face(painter, size*3, size*3, size, self.cube.F)
        self.draw_face(painter, size*6, size*3, size, self.cube.R)
        self.draw_face(painter, size*9, size*3, size, self.cube.B)
        self.draw_face(painter, size*3, size*6, size, self.cube.D)
            
        painter.end()

    def update(self, cube):
        self.cube = cube
        self.repaint()

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        # create the empty main window
        self.w = TxtWindow("Cube")

        # load default boundary values from file
        # if present
        boundaries = self.boundaries_read_from_file()
        if boundaries: scanner.setBoundaries(boundaries)

        menu = self.w.addMenu()
        menu_about = menu.addAction("About")
        menu_about.triggered.connect(self.show_about)
        menu_calib = menu.addAction("Calibration")
        menu_calib.triggered.connect(self.show_calib)

        self.vbox = QVBoxLayout()
        self.vbox.addStretch()
        
        self.txt = txt_init()

        # Create a Cube object
        self.cube = pc.Cube()

        # display cube
        self.cw = CubeWidget(self.cube)
        self.vbox.addWidget(self.cw)
        
        # display status
        self.status = QLabel("")
        self.status.setObjectName("tinylabel")
        self.status.setAlignment(Qt.AlignCenter)
        self.vbox.addWidget(self.status)

        self.vbox.addStretch()

        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.vbox.addWidget(self.btn_start)
        
        # update view and buttons
        self.ui_update()
            
        self.w.centralWidget.setLayout(self.vbox)
        self.w.show()
        self.exec_()        

    def boundaries_read_from_file(self):
        boundaries = None

        base = os.path.dirname(os.path.realpath(__file__))
        colors_dat = os.path.join(base, "colors.dat")
        try:
            with open(colors_dat, 'r') as f:
                for l in f:
                    if len(l.split(',')) == 5:
                        vals = l.split(',')
                        boundaries = [ ]
                        for i in vals:
                            boundaries.append(int(i))
        except:
            return None

        return boundaries

    def cube_do(self, cmd):
        self.cube(cmd)
        self.ui_update()

    def ui_update(self):
        self.cw.update(self.cube)

    # -------------------------------------------------------------------
    # ------------------- ckociemba integration -------------------------
    # -------------------------------------------------------------------

    # return a whole pycuber face in kociemba cube string format
    def dump_face(self, face, cmap):
        str = ""
        for y in range(3):
            for x in range(3):
                str += cmap[face[y][x].colour]
        return str

    # return kociemba cube string representation
    def dump_cube(self, cube, cmap):
        str = ""
        for i in list("URFDLB"):
            str += self.dump_face(cube.get_face(i), cmap)
        return str
            
    def kociemba(self, cube):
        base = os.path.dirname(os.path.realpath(__file__))
        executable = os.path.join(base, "kociemba")
        cachepath = os.path.join(base, "cache")

        # execute arm binary on arm
        if platform.machine() == "armv7l":
            executable += "-armv7l"; 

        # get color map of current cube as kociemba expects the center
        # pieces to be in the right position
        cmap = { }
        for i in list("UDLRBF"):
            cmap[cube.get_face(i)[1][1].colour] = i

        # check if the executable really is executable
        # as the file came from a zip during installation it
        # may not have the executable flag set
        st = os.stat(executable)
        if not (st.st_mode & stat.S_IEXEC):
            os.chmod(executable, st.st_mode | stat.S_IEXEC)

        # get cube string
        cube_str = self.dump_cube(cube, cmap)

        # run external kociemba program
        try:
            proc = subprocess.Popen([executable, cachepath, cube_str], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            response = proc.communicate()
            response_stdout = response[0].decode('UTF-8')

            if proc.returncode != 0:
                print( "Program returned an error code", proc.returncode)
                print( "Response: ", response_stdout)
                return None

        except OSError as e:
            if e.errno == errno.ENOENT:
                print( ("Unable to locate program %s" % executable) )
            else:
                print(( "Error occured \"%s\"" % str(e) ))
            return None

        except ValueError as e:
            print( "Value error occured. Check your parameters." )
            return None

        if response_stdout != "Unsolvable cube!\n":
            return pc.Formula(response_stdout)

        return None

    # -------------------------------------------------------
    # --------------- pneumatic handling (push)- ------------
    # -------------------------------------------------------
    def cube_push(self, steps=1, callback=None, parm=None):
        # if no pushes are to be done call callback immediately
        if steps == 0:
            if callback:
                if parm:
                    callback(parm)
                else:
                    callback()
            return

        # initialize timer if there isn't one yet
        if not hasattr(self, "push_timer"):
            self.push_timer = QTimer(self)
            self.push_timer.timeout.connect(self.on_push_timer)
            self.push_timer.setSingleShot(True)

        self.push_state = "on"
        if self.txt: self.txt.setPwm(VALVE_PUSH,512)
        else:        print("FAKE: PUSH VALVE OPEN")
        self.push_timer.start(500)
        
        self.push_steps = steps
        self.push_cb = callback
        self.push_parm = parm
        
    def on_push_timer(self):
        if self.push_state == "on":
            if self.txt: self.txt.setPwm(VALVE_PUSH,0)
            else:        print("FAKE: PUSH VALVE CLOSED")
            self.push_state = "released"
            self.push_timer.start(500)
            
        elif self.push_state == "released":
            self.push_steps -= 1
            if self.push_steps == 0:
                self.push_state = "off"
                if self.push_cb:
                    if self.push_parm:
                        self.push_cb(self.push_parm)
                    else:
                        self.push_cb()
            else:
                self.push_state = "on"
                if self.txt: self.txt.setPwm(VALVE_PUSH,512)
                else:        print("FAKE: PUSH VALVE OPEN")
                self.push_timer.start(500)
        else:
            print("unexpected push timer event")
            
    # -------------------------------------------------------
    # ----------------- motor handling (turns) --------------
    # -------------------------------------------------------
    def cube_turn(self, steps=1, callback=None, parm=None):
        # if no turns are to be done call callback immediately
        if steps == 0:
            if callback:
                if parm:
                    callback(parm)
                else:
                    callback()
            return
            
        # initialize timer if there isn't one yet
        if not hasattr(self, "motor_timer"):
            self.motor_timer = QTimer(self)
            self.motor_timer.timeout.connect(self.on_motor_timer)
            
        self.motor_state = "started"
        if self.txt: self.txt.setPwm(MOTOR_TURN,512)
        else:        print("FAKE: MOTOR ON")
        self.motor_steps = steps
        self.motor_timer.setSingleShot(True)
        self.motor_timer.start(100)
        self.motor_cb = callback
        self.motor_parm = parm

    def on_motor_timer(self):
        if self.motor_state == "wait4stop":
            if self.txt:
                motor_stopped = self.txt.getCurrentInput(MOTOR_STOP)
            else:
                motor_stopped = True

            if motor_stopped:
                self.motor_steps -= 1
                if self.motor_steps == 0:
                    self.motor_timer.stop()
                    self.motor_state == "stopped"
                    if self.motor_cb:
                        if self.motor_parm:
                            self.motor_cb(self.motor_parm)
                        else:
                            self.motor_cb()
                else:
                    self.motor_state = "started"
                    if self.txt: self.txt.setPwm(MOTOR_TURN,512)
                    else:        print("FAKE: MOTOR ON")
                    self.motor_timer.setSingleShot(True)
                    self.motor_timer.start(100);
            
        elif self.motor_state == "started":
            # stop motor. it will continue to run
            # until it hits the button
            if self.txt: self.txt.setPwm(MOTOR_TURN,0)
            else:        print("FAKE: MOTOR OFF")

            # use timer to poll every 100ms
            self.motor_timer.start(100);
            self.motor_timer.setSingleShot(False)

            self.motor_state = "wait4stop"

        else:
            print("unexpected motor timer event")

    # -------------------------------------------------------
    # --------- motor grab handling (face D turns) ----------
    # -------------------------------------------------------
    def face_turn(self, steps=1, callback=None, parm=None):
        # if no face turns are to be done call callback immediately
        if steps == 0:
            if callback:
                if parm:
                    callback(parm)
                else:
                    callback()
            return

        # initialize timer if there isn't one yet
        if not hasattr(self, "grab_timer"):
            self.grab_timer = QTimer(self)
            self.grab_timer.timeout.connect(self.on_grab_timer)
            self.grab_timer.setSingleShot(True)

        self.grab_state = "grabbing"
        if self.txt: self.txt.setPwm(VALVE_GRAB,512)
        else:        print("FAKE: GRAB VALVE OPEN")
        self.grab_timer.start(500)
        
        self.grab_steps = steps
        self.grab_cb = callback
        self.grab_parm = parm
            
    def on_grab_timer(self):
        if self.grab_state == "grabbing":
            self.cube_turn(self.grab_steps, self.on_grab_turn_done)
            self.grab_state = "grabbed"
        elif self.grab_state == "releasing":
            self.grab_state = "released"
            if self.grab_cb:
                if self.grab_parm:
                    self.grab_cb(self.grab_parm)
                else:
                    self.grab_cb()

    def on_grab_turn_done(self):
        self.grab_state = "releasing"
        if self.txt: self.txt.setPwm(VALVE_GRAB,0)
        else:        print("FAKE: GRAB VALVE CLOSED")
        self.grab_timer.start(500)

    def set_face(self, c, f, new_cols):
        # the neighbour faces of a face and the number of
        # rotations needed before applying it to the cube
        nb = { "U": ( ("L", "", "R"), ("B", "", "F"), 3 ),
               "D": ( ("L", "", "R"), ("F", "", "B"), 1 ),
               "L": ( ("U", "", "D"), ("F", "", "B"), 2 ),
               "R": ( ("U", "", "D"), ("B", "", "F"), 2 ),
               "F": ( ("L", "", "R"), ("U", "", "D"), 3 ),
               "B": ( ("L", "", "R"), ("D", "", "U"), 1 ) }

        # rotate the color array
        rot_cols = copy.deepcopy(new_cols)
        for i in range(nb[f][2]):
            # rotate edges
            tmp            = rot_cols[1][2]
            rot_cols[1][2] = rot_cols[0][1]
            rot_cols[0][1] = rot_cols[1][0]
            rot_cols[1][0] = rot_cols[2][1]
            rot_cols[2][1] = tmp
            # rotate corners
            tmp            = rot_cols[0][2]
            rot_cols[0][2] = rot_cols[0][0]
            rot_cols[0][0] = rot_cols[2][0]
            rot_cols[2][0] = rot_cols[2][2]
            rot_cols[2][2] = tmp
            
        # walk over all cubies
        for y in range(3):
            for x in range(3):
                code = f + nb[f][0][x] + nb[f][1][y]
                # now replace matching square on this cubie
                cubie_codes = {}
                for i in range(len(code)):
                    if code[i] == f: sq = pc.Square(rot_cols[y][x])
                    else:            sq = c[code][code[i]]
                    cubie_codes[code[i]] = pc.Square(sq)

                if len(code) == 1:
                    c[code] = pc.Centre(**cubie_codes)
                if len(code) == 2: 
                    c[code] = pc.Edge(**cubie_codes)
                if len(code) == 3: 
                    c[code] = pc.Corner(**cubie_codes)

    def is_a_valid_cube(self, faces):
        print("Checking ...")

        # convert result into pycuber cube
        c = pc.Cube()
        for i in "UDLRFB":
            self.set_face(c, i, faces[i])

        print(repr(c))
        print("This cube is solvable: ", c.is_valid())

        # use this cube!
        if c.is_valid():
            self.cube = c
            self.ui_update()
            return c

        return None
        
        # walk through all possible cube configurations given the
        # sets of possible face detections
    def search_for_valid_scan_result(self, faces):
        for u in faces[5]:
            for l in faces[1]:
                for d in faces[4]:
                    for r in faces[3]:
                        for b in faces[0]:
                            for f in faces[2]:
                                colors = { "U":u[1],"R":r[1],"D":d[1],"L":l[1],"F":f[1],"B":b[1] }
                                c = self.is_a_valid_cube( colors )
                                if c: return c

        return None

    def done(self, msg):
        # everything done, switch off hardware
        if self.txt: self.txt.setPwm(COMPRESSOR,0)
        else:        print("FAKE: COMPRESSOR OFF")

        # if no message is being supplied everything went fine
        # and we just display the time needed to solve
        if not msg:
            time = QTime(0, 0)
            time = time.addMSecs(self.timer.elapsed())
            time_str = time.toString("mm:ss.zzz")
        
            self.status.setText("Done after: " + str(time_str))
            if self.txt:
                self.txt.setSoundIndex(3)
                self.txt.incrSoundCmdId()
        else:
            self.status.setText(msg)
            if self.txt:
                self.txt.setSoundIndex(12)
                self.txt.incrSoundCmdId()

        self.btn_start.setDisabled(False)
        
    def scan_done(self, faces):
        self.status.setText("Cube scanned.")
        scanner.close(self.video_device)

        # try determine a valid scan result ...
        return self.search_for_valid_scan_result(faces)

    # -------------------------------------------------------------
    # ---- movement mapper, map face turns onto robot movements ---
    # -------------------------------------------------------------
        
    # z' is what the pneumatics do when they tilt/push the cube
    def robot_push(self, cube, formula):
        z_next = { "L":"D", "U":"L", "R":"U", "D":"R", "F":"F", "B":"B" }

        new_formula = pc.Formula()
        for i in formula:
            new_formula += i.set_face(z_next[i.face])

        return cube("z'"), new_formula

    # push n times
    def robot_push_n(self, cube, formula, n):
        for i in range(n):
            (cube, formula) = self.robot_push(cube, formula)
        return cube, formula

    # y' is what the motor does when it rotates the entire cube
    def robot_turn(self, cube, formula):
        y_next = { "L":"F", "F":"R", "R":"B", "B":"L", "U":"U", "D":"D" }

        new_formula = pc.Formula()
        for i in formula:
            new_formula += i.set_face(y_next[i.face])

        return cube("y'"), new_formula

    # turn n times
    def robot_turn_n(self, cube, formula, n):
        for i in range(n):
            (cube, formula) = self.robot_turn(cube, formula)
        return cube, formula 

    def show_cube(self, cube):
        # display current state in gui
        self.cube = cube
        self.ui_update()

    def do_solve_step(self, cube, solution):
        # turn/push steps required to get the face to be processed "down"
        face_down = { "L":(0,1), "U":(0,2), "R":(2,1), 
                      "D":(0,0), "F":(3,1), "B":(1,1)};

        # instead solve it using the movements the robot is capable of
        
        # make the face to be rotated the bottom face
        (turns, pushes) = face_down[solution[0].face]
        print("Command", solution[0], "turns:", turns, "pushes:", pushes)

        # perform turns on internal cube/solution state ...
        (cube, solution) = self.robot_turn_n(cube, solution, turns)
        # ... and in the real world
        self.cube_turn(turns, self.on_solution_turns_done, (cube, solution, pushes) )

    def on_solution_turns_done(self, parms):
        (cube, solution, pushes) = parms
        self.show_cube(cube)
        
        # perform pushes on internal cube/solution state ...
        (cube, solution) = self.robot_push_n(cube, solution, pushes)
        # ... and in the real world
        self.cube_push(pushes, self.on_solution_pushes_done, (cube, solution) )
        
    def on_solution_pushes_done(self, parms):
        (cube, solution) = parms
        self.show_cube(cube)
        
        d_face_turn = { "D":1,"D2":2,"D'":3 }

        # D is what the motor with the holder does
        # onyl D's should be left by mow
        ds = d_face_turn[solution[0]]

        # perform d face turns on internal cube/solution state ...
        for d in range(ds): cube("D")

        # ... and in the real world, forward everything but the just processed command
        self.face_turn(ds, self.on_face_turn_done, (cube, solution[1:]) )
            
    def on_face_turn_done(self, parms):
        (cube, solution) = parms
        self.show_cube(cube)
        
        print("Step done, cube now:")
        print(repr(cube))
        print("Remaining solution: ", solution)
        
        # further steps remaining?
        if len(solution) > 0:
            self.do_solve_step(cube, solution)
        else:
            print("FINISHED!!")
            self.done(None)
        
    def on_start_clicked(self):
        self.btn_start.setDisabled(True)

        self.timer = QTime()
        self.timer.start()
        self.status.setText("Initializing ...")

        # start camera and compressor
        self.video_device = scanner.init()
        if self.txt: self.txt.setPwm(COMPRESSOR,512)
        else:        print("FAKE: COMPRESSOR ON")
        if not hasattr(self, "powerup_timer"):
            self.powerup_timer = QTimer(self)
            self.powerup_timer.timeout.connect(self.on_powerup_timer)
            self.powerup_timer.setSingleShot(True)
        self.powerup_timer.start(POWERUP_TIME)
        
    def on_powerup_timer(self):
        self.status.setText("Scanning ...")

        # start scanning the cube
        # turn once to bring the cube into a well-known position
        self.cube_turn(1, self.on_scan, ("initial", 0))
        self.scan_results = []
        
    def print_face_scan_results(self, results):
        print("Number of results: ", len(results))
        for i in results:
            print("{:5.2f}".format(i[0]), i[1])

    def print_cube_scan_results(self, results):
        print("--------------------------------------------")
        print("Most likely scan result:")
        num = 1
        for i in results:
            num *= len(i)
            print(i[0][1])

        print("Number of possible results:", num)

    def on_scan(self, parm):
        print("on_scan: ", parm)

        if parm[0] != "turn":
            # scan current face
            results = scanner.do(self.video_device)
            self.scan_results.append(results)
            self.print_face_scan_results(results)

        # initially turn the cube to get it into a know orientation
        # revealing the first face
        # then push the cube three times to see the next three faces.
        # then rotate it one time and push it one time for the fifth face.
        # finally push two times for the sixth face
        if parm[0] == "initial":
            self.cube_push(1, self.on_scan, ("push", 0))
        elif parm[0] == "push":
            if parm[1] < 2:
                self.cube_push(1, self.on_scan, ("push", parm[1]+1))
            else:
                self.cube_turn(1, self.on_scan, ("turn", 0))
        elif parm[0] == "turn":
            self.cube_push(1, self.on_scan, ("turn_push", 0))
        elif parm[0] == "turn_push":
            self.cube_push(2, self.on_scan, ("final_push", 0))
        elif parm[0] == "final_push":
            self.print_cube_scan_results(self.scan_results)
            c = self.scan_done(self.scan_results)
            if c:
                print("Starting kociemba")
                solution = self.kociemba(c)
                if solution:
                    print("Solution: ", solution)
                    print(repr(c))

                    # start first step of mechanical solution
                    self.do_solve_step(c, solution)
                else:
                    self.done("No solution found")
            else:
                self.done("No valid cube found")
        else:
            print("unexpected state in on_scan")
        
    def show_about(self):
        dialog = AboutDialog(self.w)
        dialog.exec_()

    def show_calib(self):
        dialog = CalibDialog(self.w)
        dialog.exec_()
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
