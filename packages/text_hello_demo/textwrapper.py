#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, queue, pty, subprocess, select, os
from TouchStyle import *

MAX_TEXT_LINES=50

class TextWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)
        self.setMaximumBlockCount(MAX_TEXT_LINES)
        self.setReadOnly(True)
        style = "QPlainTextEdit { font: 12px; }"
        self.setStyleSheet(style)
    
        # a timer to read the ui output queue and to update
        # the screen
        self.ui_queue = queue.Queue()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(10)

    def append_str(self, text, color=None):
        self.moveCursor(QTextCursor.End)
        if not hasattr(self, 'tf') or not self.tf:
            self.tf = self.currentCharFormat()
            self.tf.setFontWeight(QFont.Bold);
        if color:
            tf = self.currentCharFormat()
            tf.setForeground(QBrush(QColor(color)))
            self.textCursor().insertText(text, tf);
        else:
            self.textCursor().insertText(text, self.tf);
            
    def delete(self):
        self.textCursor().deletePreviousChar()
        
    def append(self, text, color=None):
        pstr = ""
        for c in text:
            # special char!
            if c in "\b\a":
                if pstr != "":
                    self.append_str(pstr, color)
                    pstr = ""
        
                if c == '\b':
                    self.delete()
            else:
                pstr = pstr + c

        if pstr != "":
            self.append_str(pstr, color)

        # put something into output queue
    def write(self, str):
        self.ui_queue.put( str )
        
        # regular timer to check for messages in the queue
        # and to output them locally
    def on_timer(self):
        while not self.ui_queue.empty():
            # get from queue
            e = self.ui_queue.get()

            # strings are just sent
            if type(e) is str:
                self.append(e)

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        path = os.path.dirname(os.path.realpath(__file__))

        # Search for python snippet
        program = None
        files = [f for f in os.listdir(path) if os.path.isfile(f)]
        for f in files:
            if f != os.path.basename(__file__):
                if f.endswith(".py"):
                    program = f
                    break
        
        self.w = TouchWindow(program)

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

    def app_is_running(self):
        if self.app_process == None:
            return False

        return self.app_process.poll() == None
        
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
