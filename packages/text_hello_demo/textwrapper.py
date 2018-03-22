#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, queue, pty, subprocess, select, os
from TouchStyle import *

# a fixed size text widget
class TextWidget(QWidget):
    class Content(object):
        def __init__(self):
            self.w = 0
            self.h = 0
            self.lines = []
            self.cursor = [ 0, 0 ]

            # start with a dummy 80x25 buffer so no
            # input gets lost
            self.resize(80, 25)
            
        def resize(self, w, h):
            # print("RESIZE", w, h)

            # expand existing lines if requied
            if self.w < w:
                for li in range(len(self.lines)):
                    self.lines[li] = self.lines[li] + [' ']*(w-self.w)

            # truncate existing lines if required
            if self.w > w:
                for li in range(len(self.lines)):
                    self.lines[li] = self.lines[li][:w]
                    
            # append empty lines if requied
            if self.h < h:
                for l in range(h - self.h):
                    self.lines.append( [' ']*w)

            # remove lines on top if required
            # TODO: make this depending on cursor position!
            #       first remove lines below the cursor
            if self.h > h:
                remove = self.h - h
                hbelow = self.h - self.cursor[1] - 1
                # print("Remove: ", remove, "Lines below cursor:", hbelow)

                # can the whole request be satisfied by lines below cursor?
                if remove <= hbelow:
                    # yes, just shrink
                    self.lines = self.lines[:h]
                else:
                    # no, remove as many as possible below, rest above
                    if hbelow: self.lines = self.lines[:-hbelow]
                    self.lines = self.lines[-h:]

                    # move cursor up by the number of lines that have
                    # been removed above it
                    # print("Cursor y", self.cursor[1], "->", self.cursor[1] - remove)
                    self.cursor[1] = self.cursor[1] - remove
            
            self.w = w
            self.h = h

        def scrollUp(self):
            self.lines = self.lines[1:]
            self.lines.append( [' ']*self.w)
            
        def cursor_right(self):
            self.cursor[0] = self.cursor[0] + 1
            if self.cursor[0] >= self.w:
                self.cursor[0] = 0
                self.cursor_down()
        
        def cursor_down(self):
            self.cursor[1] = self.cursor[1] + 1
            if(self.cursor[1] >= self.h):
                self.scrollUp()
                self.cursor[1] = self.h - 1
        
        def cursor_return(self):
            self.cursor[0] = 0

        def write(self, c):
            # cursor position may already be out of bound if font size
            # has been changed
            if self.cursor[0] < self.w and self.cursor[1] < self.h:
                self.lines[self.cursor[1]][self.cursor[0]] = c;
                    
            self.cursor_right()
            
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(qsp)
        self.content = self.Content()

        self.setFont(8)

    def setFont(self, size):
        self.fontSize = size
        
        self.font = QFont("Monospace");
        self.font.setStyleHint(QFont.TypeWriter);
        self.font.setPointSize(self.fontSize)

        metrics = QFontMetrics(self.font)
        self.cw = metrics.width("M")
        self.ch = metrics.height()

        # todo: change buffer size
        self.repaint()
        
    def paintEvent(self, event):
        self.w = int(self.width()/self.cw)
        self.h = int(self.height()/self.ch)
        
        if ((self.content.w != self.w) or
            (self.content.h != self.h)):
            # widget size has changed, reset buffer
            self.content.resize(self.w, self.h)
            
        painter = QPainter()
        painter.begin(self)

        # optional set background
        # painter.fillRect(event.rect(), QColor("black"));
             
        painter.setFont(self.font)

        for y in range(self.content.h):
            for x in range(self.content.w):
                if self.content.lines[y][x] != ' ':
                    box = QRect(x*self.cw, y*self.ch, self.cw, self.ch)
                    painter.drawText(box, Qt.AlignLeft, self.content.lines[y][x]);

        # draw cursor
        box = QRect(self.content.cursor[0]*self.cw,
                    self.content.cursor[1]*self.ch, self.cw-1, self.ch-1)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("white"))
        painter.drawRect(box);
                
        painter.end()

    def resizeFont(self, step):
        if self.fontSize + step:
            self.setFont(self.fontSize + step)
        
    def write(self, text):
        # process all characters
        for c in text:
            if c == '\n':
                self.content.cursor_down()
            elif c == '\r':
                self.content.cursor_return()
            else:
                self.content.write(c)
                
        self.repaint();
        
class TextTouchWindow(TouchWindow):
    closed = pyqtSignal()
    
    def __init__(self, title):
        TouchWindow.__init__(self, title)
                
    def close(self):
        self.closed.emit()
        TouchWindow.close(self)
 
class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        path = os.path.dirname(os.path.realpath(__file__))

        # change into current directory before running
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
 
        # Search for python snippet
        program = None
        files = [f for f in os.listdir(path) if os.path.isfile(f)]
        for f in files:
            if f != os.path.basename(__file__):
                if f.endswith(".py"):
                    program = f
                    break
        
        self.w = TextTouchWindow(program)
        self.w.closed.connect(self.on_close)
        
        #self.menu=self.w.addMenu()
        #self.menu.setStyleSheet("font-size: 24px;")
        #self.m_inc = self.menu.addAction("Bigger")
        #self.m_inc.triggered.connect(self.on_menu_inc)
        #self.m_dec = self.menu.addAction("Smaller")
        #self.m_dec.triggered.connect(self.on_menu_dec)
        
        self.text = TextWidget(self.w)
        self.w.setCentralWidget(self.text)

        if program:
            # run subprocess
            self.log_master_fd, self.log_slave_fd = pty.openpty()
            self.app_process = subprocess.Popen([ "python3", program ], stdout=self.log_slave_fd, stderr=self.log_slave_fd)

            # start a timer to monitor the ptys
            self.log_timer = QTimer()
            self.log_timer.timeout.connect(self.on_log_timer)
            self.log_timer.start(10)
        else:
            self.text.write("No python script found!")
        
        self.w.show() 
        self.exec_()

    def on_menu_inc(self):
        self.text.resizeFont(1)
        
    def on_menu_dec(self):
        self.text.resizeFont(-1)
        
    def app_is_running(self):
        if self.app_process == None:
            return False

        return self.app_process.poll() == None
    
    def on_close(self):
        if self.app_is_running():
            self.app_process.terminate()
            self.app_process.wait()
        
    def on_log_timer(self):
        # first read whatever the process may have written
        if select.select([self.log_master_fd], [], [], 0)[0]:
            output = os.read(self.log_master_fd, 100)
            if output: 
                self.text.write(str(output, "utf-8"))
        else:
            # check if process is still alive
            if not self.app_is_running():
                if self.app_process.returncode:
                    self.text.write("Application ended with return value " + str(self.app_process.returncode) + "\n")

                # close any open ptys
                os.close(self.log_master_fd)
                os.close(self.log_slave_fd)

                # remove timer
                self.log_timer = None
                
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
