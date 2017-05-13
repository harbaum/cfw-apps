#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys, os
import ftrobopy
from TxtStyle import *

FPS = 5
LED_COLS = 24
LED_ROWS = 5

MAX_BALLS = 3

TIMEOUT = 10

RATIO = LED_ROWS/LED_COLS

POLL_FREQ = 100

# the 5 pixel high ledfont
FONT = {
    ' ':( [0b00000] ),
    'A':( [0b11110, 0b00101, 0b11110] ),
    'B':( [0b11111, 0b10101, 0b01010] ),
    'C':( [0b01110, 0b10001, 0b10001] ),
    'D':( [0b11111, 0b10001, 0b01110] ),
    'E':( [0b11111, 0b10101, 0b10001] ),
    'F':( [0b11111, 0b00101, 0b00001] ),
    'G':( [0b01110, 0b10001, 0b11010] ),
    'H':( [0b11111, 0b00100, 0b11111] ),
    'I':( [0b11111] ),
    'J':( [0b10000, 0b01111] ),
    'K':( [0b11111, 0b00100, 0b11011] ),
    'L':( [0b11111, 0b10000, 0b10000] ),
    'M':( [0b11111, 0b00010, 0b00100, 0b00010, 0b11111] ),
    'N':( [0b11111, 0b00010, 0b00100, 0b11111] ),
    'O':( [0b01110, 0b10001, 0b10001, 0b01110] ),
    'P':( [0b11111, 0b00101, 0b00010] ),
    'Q':( [0b01110, 0b10001, 0b11110] ),
    'R':( [0b11111, 0b00101, 0b11010] ),
    'S':( [0b10010, 0b10101, 0b01001] ),
    'T':( [0b00001, 0b11111, 0b00001] ),
    'U':( [0b01111, 0b10000, 0b11111] ),
    'V':( [0b00111, 0b11000, 0b00111] ),
    'W':( [0b01111, 0b10000, 0b01000, 0b10000, 0b01111] ),
    'X':( [0b11011, 0b00100, 0b11011] ),
    'Y':( [0b00011, 0b11100, 0b00011] ),
    'Z':( [0b11001, 0b10101, 0b10011] ),
    '0':( [0b01110, 0b10001, 0b01110] ),
    '1':( [0b00010, 0b11111] ),
    '2':( [0b11001, 0b10101, 0b10010] ),
    '3':( [0b10001, 0b10101, 0b01010] ),
    '4':( [0b01100, 0b01010, 0b11111] ),
    '5':( [0b10111, 0b10101, 0b01001] ),
    '6':( [0b01110, 0b10101, 0b01001] ),
    '7':( [0b00001, 0b11001, 0b00111] ),
    '8':( [0b01010, 0b10101, 0b01010] ),
    '9':( [0b10010, 0b10101, 0b01110] ),
    "'":( [0b00011] ),
    "!":( [0b10111] ),
    ':':( [0b10100] ),
    '.':( [0b10000] ),
    '-':( [0b00100, 0b00100] )
}

class LEDWidget(QWidget):
    def __init__(self, parent=None):

        super(LEDWidget, self).__init__(parent)
        
        # update/scroll timer
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/FPS)

        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

        self.led_size = 0
        self.setText("PRESS START ...")

    def setText(self, msg):
        self.buffer = []
        x = 0
        for i in msg:
            for j in FONT[i]:
                self.buffer.append(j)
            self.buffer.append(0)

        self.cnt = -LED_COLS # reset counter

    def update(self):
        # increase scroll counter
        self.cnt += 1
        # all text scrolled out to the left?
        if self.cnt > len(self.buffer):
            # restart scrolling in from the right
            self.cnt = -LED_COLS

        self.repaint()

    def draw(self, size, fg_color, highlight_color):
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        # img = QImage(size, size, QImage.Format_RGB555)
        # img.fill(Qt.black);

        painter = QPainter(img)
        width = img.width()
        height = img.height()

        grad = QRadialGradient(width/2, height/2, width*0.4, width*0.4, height*0.4)
        grad.setColorAt(0, highlight_color)
        grad.setColorAt(1, fg_color)
        brush = QBrush(grad)

        painter.setPen(fg_color)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(brush)
        painter.drawEllipse(0, 0, width-1, height-1)

        painter.end()

        return img

    def heightForWidth(self,w):
        return w*RATIO
        
    def paintEvent(self, QPaintEvent):
        led_w = int(self.width()/LED_COLS)

        # check if led size matches
        if led_w != self.led_size: 
            # build the two leds if necessary
            self.led_on = self.draw(led_w, QColor("#ff8000"), Qt.white)
            self.led_off = self.draw(led_w, QColor("#402000"), QColor("#808080"))
            self.led_size = led_w

        # get top and bottom margins for proper centering
        x_off = int((self.width() - LED_COLS * led_w) / 2)
        y_off = int((self.height() - LED_ROWS * led_w) / 2)

        painter = QPainter()
        painter.begin(self)

        for j in range(LED_COLS):
            # get current column pattern
            if (j+self.cnt >= 0) and (j+self.cnt < len(self.buffer)):
                p = self.buffer[j+self.cnt]
            else:
                p = 0

            for i in range(LED_ROWS):
                if p & (1<<i) != 0: led = self.led_on
                else:               led = self.led_off

                painter.drawImage(x_off+led_w*j,y_off+led_w*i,led)
            
        painter.end()

class BallWidget(QWidget):
    def __init__(self, parent=None):

        super(BallWidget, self).__init__(parent)
        
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

        self.remaining_balls = 0
        self.ball_size = 0

    def heightForWidth(self,w):
        return w/(MAX_BALLS*1.1)

    def draw(self, size):
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)

        color = QColor("#404040")   # dark grey

        grad = QRadialGradient(size*0.5, size*0.5, size*0.5, size*0.3, size*0.3)
        grad.setColorAt(0, Qt.white)
        grad.setColorAt(1, color)
        brush = QBrush(grad)

        painter.setPen(color)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(brush)

        painter.drawEllipse(1, 1, size-2, size-2)
            
        painter.end()

        return img

    def paintEvent(self, QPaintEvent):
        # determine required ball size and render it if necessary
        size = min(self.height(), self.width()/(MAX_BALLS*1.1))
        if self.ball_size != size:
            self.ball_img = self.draw(size)
            self.ball_size = size

        painter = QPainter()
        painter.begin(self)

        # draw as many balls as remaining
        spacing = (self.width() - MAX_BALLS*size)/2
        y = (self.height() - size)/2
        for i in range(self.remaining_balls):
            x = i * size
            if i != 0: x += i*spacing
            painter.drawImage(x, y, self.ball_img)
            
        painter.end()

    def setBalls(self, n):
        if n < 0: n = 0
        if n > MAX_BALLS: n = MAX_BALLS

        self.remaining_balls = n
        self.repaint()

    def balls(self):
        return self.remaining_balls

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        self.hiscore = self.read_hiscore()

        # connect to TXTs IO board
        txt_ip = os.environ.get('TXT_IP')
        if txt_ip == None: txt_ip = "localhost"
        try:    self.txt = ftrobopy.ftrobopy(txt_ip, 65000)
        except: self.txt = None

        if self.txt:
            # all outputs normal mode
            M = [ self.txt.C_OUTPUT,    self.txt.C_OUTPUT, 
                  self.txt.C_OUTPUT,    self.txt.C_OUTPUT ]
            I = [ (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH,   self.txt.C_DIGITAL ),
                  (self.txt.C_VOLTAGE,  self.txt.C_ANALOG ) ]
            self.txt.setConfig(M, I)
            self.txt.updateConfig()

        # create the empty main window
        self.w = TxtWindow("Pinball")

        self.vbox = QVBoxLayout()

        self.led = LEDWidget()
        self.vbox.addWidget(self.led)

        hbox_w = QWidget()
        hbox = QHBoxLayout()
        hbox_w.setLayout(hbox)
        hbox.addStretch(1)
        self.balls = BallWidget()
        hbox.addWidget(self.balls, 4)
        hbox.addStretch(1)
        self.vbox.addWidget(hbox_w)

        self.current_score = 0
        self.lcd = QLCDNumber(5)
        # initially display hi score
        self.lcd.display(str(self.hiscore))
        self.vbox.addWidget(self.lcd)

        # start button an progress bar 
        # share the same widget location ...
        self.stack = QStackedWidget(self.w)
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.stack.setSizePolicy(qsp)

        self.pbar = QProgressBar()
        self.pbar.setTextVisible(False)
        self.stack.addWidget(self.pbar)

        self.start = QPushButton("Start")
        self.stack.addWidget(self.start)
        self.stack.setCurrentWidget(self.start)
        self.start.clicked.connect(self.on_start)

        self.vbox.addWidget(self.stack)

        self.w.centralWidget.setLayout(self.vbox)

        loop_timer = QTimer(self)
        loop_timer.timeout.connect(self.on_timeout_tick)
        loop_timer.start(TIMEOUT*1000/100)

        self.w.show()
        self.exec_()

    def read_hiscore(self):
        hi_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)), "hiscore.dat")
        try:
            with open(hi_fname) as f:
                score = int(next(f))
                return score
        except:
            return 0
        
    def isRunning(self):
        # a game is running if the progress bar is
        # visible
        return self.stack.currentWidget() == self.pbar

    def on_start(self):
        # start game
        self.led.setText("GO!")
        self.balls.setBalls(MAX_BALLS)          # reload balls
        self.stack.setCurrentWidget(self.pbar)  # raise progressbar widget
        self.pbar.setValue(0)                   # progress bar not running
        self.scoreReset()                       # reset score to zero

        Pal = QPalette(self.lcd.palette())
        Pal.setColor(QPalette.WindowText, Qt.white)
        self.lcd.setSegmentStyle(QLCDNumber.Filled)
        self.lcd.setPalette(Pal)

        # light lamps and start compressor
        self.txt.setPwm(2,512)
        self.txt.setPwm(5,512)
        self.txt.setPwm(6,512)

        # reset button state
        self.left = False     # assume button is not pressed
        self.right = False    # -"-
        self.loop = False     # assume light bar is blocked
        self.drop = False     # -"-
        self.color = False    # color sensor hasn't detected anything
        
        self.ball_in_game = False  # no ball in game yet
        
        # start input poll timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(1000/POLL_FREQ)

        # play sound
        self.txt.setSoundIndex(11)
        self.txt.incrSoundCmdId()

    def end(self):
        self.timer.stop()
        
        # switch off lamps and stop compressor and release flipper
        self.txt.setPwm(2,0)
        self.txt.setPwm(3,0)
        self.txt.setPwm(4,0)
        self.txt.setPwm(5,0)
        self.txt.setPwm(6,0)

        self.stack.setCurrentWidget(self.start)  # raise start button widget

        # self hi score
        if self.current_score > self.hiscore:
            self.hiscore = self.current_score
            self.led.setText("NEW HIGH SCORE "+str(self.hiscore))
            # save hiscore to card
            hi_fname = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    "hiscore.dat")
            try:
                with open(hi_fname, "w") as f:
                    f.write(str(self.hiscore))
                    f.close()
            except:
                pass
            
    def scoreReset(self):
        self.current_score = 0
        self.lcd.display(self.current_score)

    def scoreAdd(self, n):
        if self.isRunning():
            self.current_score += n
            self.lcd.display(self.current_score)
            if self.current_score > self.hiscore:
                Pal = QPalette(self.lcd.palette())
                Pal.setColor(QPalette.WindowText, Qt.red)
                self.lcd.setSegmentStyle(QLCDNumber.Filled)
                self.lcd.setPalette(Pal)
                self.txt.setSoundIndex(3)
                self.txt.incrSoundCmdId()

    def on_timeout_tick(self):
        # timeout counter runs down ...
        if self.pbar.value() > 0:
            self.pbar.setValue(self.pbar.value()-1)
            
    def triggerTimeout(self):
        # ignore any further even within the first 2% of the timer
        # running (100ms for a 5sec timeout) to ignore spikes
        if self.pbar.value() < 99:
            # loop light bar has been passes while the counter
            # was still running down: SCORE the time left
            if self.pbar.value() > 0:
                self.led.setText("SUPER!!!")
                self.scoreAdd(self.pbar.value())

            self.pbar.setValue(100)
            
    def poll(self):
        # read buttons and control valves
        left = self.txt.getCurrentInput(0)
        if left != self.left:
            if left:  self.txt.setPwm(3,512)
            else:     self.txt.setPwm(3,0)
            self.left = left

        right = self.txt.getCurrentInput(1)
        if right != self.right:
            if right: self.txt.setPwm(4,512)
            else:     self.txt.setPwm(4,0)
            self.right = right

        # read light bars
        loop = self.txt.getCurrentInput(2)
        if loop != self.loop:
            # check if loop light bar has just been blocked
            if not loop:
                # play sound
                self.txt.setSoundIndex(9)
                self.txt.incrSoundCmdId()

                if not self.ball_in_game:
                    self.ball_in_game = True
        
                self.led.setText("HIT AGAIN")
                self.triggerTimeout()
            self.loop = loop

        drop = self.txt.getCurrentInput(3)
        if drop != self.drop:
            # check if drop light bar has just been blocked
            if not drop and self.ball_in_game:
                # loose one ball
                self.balls.setBalls(self.balls.balls()-1)
                self.ball_in_game = False
                self.pbar.setValue(0)   # stop any running progress bar

                # play sound
                self.txt.setSoundIndex(12)
                self.txt.incrSoundCmdId()

                if self.balls.balls() == 0:
                    self.led.setText("GAME OVER")
                    # no ball left
                    self.end()
                else:
                    self.led.setText("NEXT BALL")
                    
            self.drop = drop

        # the color sensor
        color_value = self.txt.getCurrentInput(7)
        color = color_value < 1300
        if color != self.color:
            if color:
                self.scoreAdd(100)
                # play sound
                self.txt.setSoundIndex(10)
                self.txt.incrSoundCmdId()
                
            self.color = color

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
