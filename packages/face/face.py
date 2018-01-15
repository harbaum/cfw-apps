#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys, numpy, cv2
from TxtStyle import *

WIDTH=240
HEIGHT=(WIDTH*3/4)
FPS=10

CAM_DEV = os.environ.get('FTC_CAM')
if CAM_DEV == None: CAM_DEV = 0
else:               CAM_DEV = int(CAM_DEV)

class CamWidget(QWidget):
    def __init__(self, parent=None):

        super(CamWidget, self).__init__(parent)

        base = os.path.dirname(os.path.realpath(__file__))
        cascPath = os.path.join(base, "haarcascade_frontalface_default.xml")
        self.faceCascade = cv2.CascadeClassifier(cascPath)

        # initialize camera
        print("CAM", CAM_DEV)
        self.cap = cv2.VideoCapture(CAM_DEV)
        if self.cap.isOpened():
            self.cap.set(3,WIDTH)
            self.cap.set(4,HEIGHT)
            self.cap.set(5,FPS)

        print("CAP:", self.cap, self.cap.isOpened())
            
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/FPS)

        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

    def sizeHint(self):
        return QSize(WIDTH,HEIGHT)

    def heightForWidth(self,w):
        return w*3/4
        
    def grab(self):
        frame = self.cap.read()[1]

        # do detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect faces
        faces = self.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
 
        # expand/shrink to widget size
        wsize = (self.size().width(), self.size().height())
        self.cvImage = cv2.resize(frame, wsize)

        height, width, byteValue = self.cvImage.shape
        bytes_per_line = byteValue * width

        # hsv to rgb
        cv2.cvtColor(self.cvImage, cv2.COLOR_BGR2RGB, self.cvImage)
        self.mQImage = QImage(self.cvImage, width, height,
                              bytes_per_line, QImage.Format_RGB888)

#        cv_img = cv2.cvtColor(self.cvImage, cv2.COLOR_RGB2GRAY)
#        raw = Image.fromarray(cv_img)

    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)

        if not self.cap.isOpened():
            painter.drawText(QRect(QPoint(0,0), self.size()),
                             Qt.AlignCenter, "No camera");
        else:
            self.grab()
            painter.drawImage(0,0,self.mQImage)
            
        painter.end()

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        # create the empty main window
        self.w = TxtWindow("Face")

        self.cw = CamWidget()

        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0,0,0,0)

        vbox.addWidget(self.cw)
        vbox.addStretch()

        self.lbl = QLabel()
        self.lbl.setObjectName("smalllabel")
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setWordWrap(True)
        vbox.addWidget(self.lbl)
        vbox.addStretch()
    
        self.w.centralWidget.setLayout(vbox)
        
        self.w.show()
        self.exec_()        

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
