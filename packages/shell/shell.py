#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from TxtStyle import *
import sys

class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)
        # create the empty main window
        self.w = TxtWindow("Shell")

        self.process  = QProcess(self.w)
        self.terminal = QWidget(self.w)
    
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.terminal)
        self.w.centralWidget.setLayout(self.vbox)

        self.process.start(
            'xterm',
            ['-into', str(self.terminal.winId())]
        )
        
        self.w.show()
        self.exec_()
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)

