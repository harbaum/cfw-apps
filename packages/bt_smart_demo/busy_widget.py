# -*- coding: utf-8 -*-

from PyQt4.QtNetwork import *
from TouchStyle import *

# a rotating "i am busy" widget to be shown during network io
class BusyWidget(QWidget):
    def __init__(self, parent=None):
        super(BusyWidget, self).__init__(parent)

        self.resize(64, 64)
        self.move(QPoint(parent.width()/2-32, parent.height()/2-32))

        self.step = 0
        self.percent = -1

        # animate at 5 frames/sec
        self.atimer = QTimer(self)
        self.atimer.timeout.connect(self.animate)
        self.atimer.start(200)

        # create small circle bitmaps for animation
        self.dark = self.draw(16, QColor("#808080"))
        self.bright = self.draw(16, QColor("#fcce04"))
        
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(qsp)

    def sizeHint(self):
        return QSize(64, 64)

    def progress(self, perc):
        self.percent = perc
        self.repaint()
    
    def draw(self, size, color):
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setPen(Qt.white)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(0, 0, img.width()-1, img.height()-1)
        painter.end()

        return img

    def animate(self):
        self.step += 45
        self.repaint()

    def close(self):
        self.atimer.stop()
        super(BusyWidget, self).close()

    def paintEvent(self, event):
        radius = min(self.width(), self.height())/2 - 16
        painter = QPainter()
        painter.begin(self)

        if self.percent >= 0:
            font = painter.font()
            # half the size than the current font size 
            if font.pointSize() < 0:
                font.setPixelSize(font.pixelSize() / 3)
            else:
                font.setPointSize(font.pointSize() / 3)
            # set the modified font to the painter */
            painter.setFont(font)

            # draw text in center
            painter.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, str(self.percent)+"%" )

        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width()/2, self.height()/2)
        painter.rotate(45)
        painter.rotate(self.step)
        painter.drawImage(0,radius, self.bright)
        for i in range(7):
            painter.rotate(45)
            painter.drawImage(0,radius, self.dark)

        painter.end()
