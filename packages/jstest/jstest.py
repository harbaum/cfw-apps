#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys
from TouchStyle import *
from qjoystick import QJoystick

class Axes2dWidget(QWidget):
    def __init__(self, parent=None):
        super(Axes2dWidget, self).__init__(parent)
        
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

        self.x = 0.0
        self.y = 0.0

    def heightForWidth(self,w):
        return w

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)

        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("lightgrey"))
        pen.setWidth(self.width()/20)
        painter.setPen(pen)
        painter.drawRect(self.rect())

        pen.setWidth(self.width()/40)
        pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        painter.drawLine(QPoint(self.width()/2, 0), QPoint(self.width()/2, self.height()))
        painter.drawLine(QPoint(0, self.height()/2), QPoint(self.width(), self.height()/2))
       
        # x and y range from -1 to 1
        x = (self.x + 1)/2 * self.width()
        y = (self.y + 1)/2 * self.height()
        r = self.width() / 10
        
        pen.setWidth(self.width()/100)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#fcce04")))
        painter.drawEllipse(x - r/2, y - r/2, r, r)
        
        painter.end()

    def set(self, x, y):
        if x != None: self.x = x
        if y != None: self.y = y
        self.update()

class ButtonWidget(QWidget):
    def __init__(self, parent=None):
        super(ButtonWidget, self).__init__(parent)
        
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

        self.state = False

    def heightForWidth(self,w):
        return w

    def paintEvent(self, event):
        x = 0
        y = 0
        r = self.width()
        if self.width() > self.height():
            x = (self.width() - self.height()) / 2
            r = self.height()
        if self.width() < self.height():
            y = (self.height() - self.width()) / 2
            r = self.width()

        painter = QPainter()
        painter.begin(self)

        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("lightgrey"))
        pen.setWidth(self.width()/50)
        painter.setPen(pen)
        if self.state:
            painter.setBrush(QBrush(QColor("#fcce04")))
        else:
            painter.setBrush(Qt.transparent)
        painter.drawEllipse(QRect(x,y, r,r))
        
        painter.end()

    def set(self, b):
        self.state = b
        self.update()

class TouchGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        # create the empty main window
        w = TouchWindow("Joystick")
        self.vbox = QVBoxLayout()

        # initialize joystick class
        self.js = QJoystick(self)
        
        if self.js.joysticks() == None:
            self.vbox.addStretch()
            err = QLabel("Error")
            err.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(err)
            lbl = QLabel("No joystick found. Please make sure one is connected to the TXTs USB1 port.")
            lbl.setObjectName("smalllabel")
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(lbl)
            self.vbox.addStretch()
        else:
            self.js.button_changed.connect(self.on_button_changed)
            self.js.axis_changed.connect(self.on_axis_changed)

            # drop down list containing all joysticks
            self.js_w = QComboBox()
            self.js_w.activated[str].connect(self.set_js)
            for i in self.js.joysticks():
                self.js_w.addItem(i["id"])
            self.vbox.addWidget(self.js_w)
            self.vbox.addStretch()

            self.stack_w = QStackedWidget()
            self.vbox.addWidget(self.stack_w)

            self.axis_target = { }
            self.button_target = { }
            for stick in self.js.joysticks():
                stick_w = QWidget()
                stick_vbox = QVBoxLayout()
                stick_w.setLayout(stick_vbox)

                # build a widget for each joystick

                # find axis pairs
                pairs = { "x": "y", "rx": "ry",
                          "hat0x": "hat0y", "hat1x": "hat1y",
                          "hat2x": "hat2y", "hat3x": "hat3y",
                          "tiltx": "tilty" }
                
                # a hbox for the axis pairs
                axis_pairs_w = QWidget(w)
                axis_pairs = QHBoxLayout()
                axis_pairs_w.setLayout(axis_pairs)

                axis_target = { }
                axis_list = []
                for i in stick["axis"]:
                    if i["name"] in pairs and any(a["name"] == pairs[i["name"]] for a in stick["axis"]):
                        axis_list.append(i["name"])
                        axis_list.append(pairs[i["name"]])

                        # create axis widget for this pair
                        aw = Axes2dWidget(axis_pairs_w)
                        axis_pairs.addWidget(aw)

                        axis_target[i["name"]] = ([aw, 0])
                        axis_target[pairs[i["name"]]] = ([aw, 1])

                stick_vbox.addWidget(axis_pairs_w)

                # and a vbox for the single axes
                single_axes_w = QWidget(w)
                single_axes = QVBoxLayout()
                single_axes_w.setLayout(single_axes)

                for i in stick["axis"]:
                    if not i["name"] in axis_list:
                        pb = QProgressBar()
                        pb.setTextVisible(False)
                        single_axes.addWidget(pb)
                        axis_target[i["name"]] = [ pb ]

                stick_vbox.addWidget(single_axes_w)
                stick_vbox.addStretch()

                # add button box
                but_w = QWidget()
                but = QGridLayout()
                but_w.setLayout(but)

                pos = 0
                button_target = { }
                for b in stick["button"]:
                    btn = ButtonWidget(but_w)
                    but.addWidget(btn, pos/8, pos%8)
                    button_target[b["name"]] = btn
                    pos += 1

                stick_vbox.addWidget(but_w)
                stick_vbox.addStretch()

                self.axis_target[stick["id"]] = axis_target
                self.button_target[stick["id"]] = button_target

                self.stack_w.addWidget(stick_w)
            
        w.centralWidget.setLayout(self.vbox)
        w.show()
        self.exec_()        
 
    def set_js(self, js):
        self.stack_w.setCurrentIndex(self.js_w.currentIndex())

    def on_button_changed(self, dev, name, value):
        target = self.button_target[dev["id"]][name]
        target.set(value)

    def on_axis_changed(self, dev, name, value):
        target = self.axis_target[dev["id"]][name]
        if len(target) == 1:
            # just set the progressbar value
            target[0].setValue((value+1)*50)
        else:
            # set the current axis of a 2d axis widget
            if target[1] == 0:
                target[0].set(value, None)
            else:
                target[0].set(None, value)

if __name__ == "__main__":
    TouchGuiApplication(sys.argv)
