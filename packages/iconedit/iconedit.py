#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys, os, configparser

from TxtStyle import *

# make sure all file access happens relative to this script
BASE = os.path.dirname(os.path.realpath(__file__))
USERAPPBASE = os.path.dirname(BASE)
print("BASE", BASE)
print("USERAPPBASE", USERAPPBASE)

class AppListWidget(QListWidget):
    selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(AppListWidget, self).__init__(parent)

        self.setUniformItemSizes(True)
        self.setViewMode(QListView.ListMode)
        self.setMovement(QListView.Static)
        self.setIconSize(QSize(32,32))
        self.setSortingEnabled(True)
        self.parent = parent

        # scan for installed apps
        self.scan_user_apps()

        # react on clicks
        self.itemClicked.connect(self.onItemClicked)

    def scan_user_apps(self):
        app_dirs = os.listdir(USERAPPBASE)
        for a in app_dirs:
            # build full path of the app dir
            app_dir = os.path.join(USERAPPBASE, a)
            # check if there's a manifest inside that dir
            manifestfile = os.path.join(app_dir, "manifest")
            if os.path.isfile(manifestfile):
                # get app name
                manifest = configparser.RawConfigParser()
                manifest.read_file(open(manifestfile, "r", encoding="utf8"))

                if manifest.has_option('app', 'name') and manifest.has_option('app', 'icon'):
                    icon_path = os.path.join(a, manifest.get('app', 'icon'))
                    icon = QIcon(os.path.join(USERAPPBASE, icon_path))
                    item = QListWidgetItem(icon, manifest.get('app', 'name'))
                    item.setData(Qt.UserRole, icon_path)
                    self.addItem(item)

    def onItemClicked(self, item):
        self.selected.emit(item.data(Qt.UserRole))

class LoadDialog(TouchDialog):
    load = pyqtSignal(str)
    
    def __init__(self, parent):
        TouchDialog.__init__(self, "Load", parent)
        applist = AppListWidget()
        applist.selected.connect(self.on_app_selected)
        self.setCentralWidget(applist)

    def on_app_selected(self, name):
        self.load.emit(name)
        self.close()
        
class ColorPopup(QFrame):
    colorChanged = pyqtSignal(QColor)
       
    class ColorWidget(QLabel):
        def __init__(self, color, parent=None):
            QLabel.__init__(self,parent)
            self.color = color

        def setColor(self, color):
            self.color = color
            self.update()
            
        def paintEvent(self, event):
            checkerSize = 8
            
            painter = QPainter()
            painter.begin(self)
            painter.setPen(Qt.NoPen)

            for y in range(int(self.height() / checkerSize + 1)):
                for x in range(int(self.width() / checkerSize + 1)):
                    if (x ^ y) & 1:
                        painter.setBrush(QBrush(QColor("white")))
                    else:
                        painter.setBrush(QBrush(QColor("darkgray")))
                        
                    painter.drawRect(x*checkerSize,y*checkerSize, checkerSize, checkerSize)
            
            painter.setBrush(QBrush(self.color))
            painter.drawRect(0,0, self.width(), self.height())
            painter.end()

            
    class ColorPickerRGBA(QWidget):
        colorChanged = pyqtSignal(QColor)
        
        def __init__(self, color, space = "RGBA", parent=None):
            QWidget.__init__(self,parent)
            self.color = color

            self.space = space
            
            grid = QGridLayout()
            grid.setVerticalSpacing(0)
            grid.setContentsMargins(0,0,0,0)

            self.slider = {}
            self.label = {}
            for c in space:
                if c == 'a':
                    self.cb = QCheckBox("None")
                    self.cb.stateChanged.connect(self.on_stateChanged)
                    grid.addWidget(self.cb, space.index(c),1)
                else:
                    self.label[c] = QLabel(c)
                    self.label[c].setObjectName("smalllabel")
                    grid.addWidget(self.label[c], space.index(c), 0)
                    self.slider[c] = QSlider(Qt.Horizontal)
                    self.slider[c].setMaximum(255)
                    self.slider[c].setProperty("channel", c)
                    self.slider[c].valueChanged.connect(self.on_valueChanged)
                    grid.addWidget(self.slider[c], space.index(c),1)
         
            self.setLayout(grid)
            self.setColor(color)

        def on_stateChanged(self, state):
            color = self.color
            if state == Qt.Checked: color.setAlpha(0)
            else:                   color.setAlpha(255)
            self.setColor(color)
            self.colorChanged.emit(color)
            
        def on_valueChanged(self):
            slider = self.sender()
            channel = slider.property("channel")
            color = self.color
            if channel == "R":   color.setRed(slider.value())
            elif channel == "G": color.setGreen(slider.value())
            elif channel == "B": color.setBlue(slider.value())
            elif channel == "A": color.setAlpha(slider.value())
            self.setColor(color)
            self.colorChanged.emit(color)

        def setColor(self, color):
            # update slider and checkbox
            for c in self.space:
                if c == 'a':
                    value = color.alpha()
                    if value < 128: self.cb.setCheckState(Qt.Checked)
                else:
                    value = None
                    if c == 'R':   value = color.red()
                    elif c == 'G': value = color.green()
                    elif c == 'B': value = color.blue()
                    elif c == 'A': value = color.alpha()

                    if value:
                        self.slider[c].setValue(value)
                    
            self.color = color
            
    def __init__(self, color, space, parent=None):
        super(ColorPopup, self).__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setObjectName("popup")

        vbox = QVBoxLayout()
        colorW = self.ColorWidget(color)
        vbox.addWidget(colorW)
        rgbaW = self.ColorPickerRGBA(color, space)
        vbox.addWidget(rgbaW)        
        rgbaW.colorChanged.connect(colorW.setColor)
        rgbaW.colorChanged.connect(self.onColorChanged)
        self.setLayout(vbox)

        # open popup below parent
        pos = parent.mapToGlobal(QPoint(0,parent.height()))
        self.move(pos)

    def onColorChanged(self, color):
        self.colorChanged.emit(color)
        
class IconBar(QWidget):
    gridChanged = pyqtSignal(QColor)
    penChanged = pyqtSignal(QColor)
        
    class IconButton(QPushButton):
        def __init__(self, name, parent = None):
            QPushButton.__init__(self, None, parent)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            pix = QPixmap(os.path.join(BASE, name + ".svg"))
            icn = QIcon(pix)
            self.setIcon(icn)
            self.setIconSize(pix.size())

    def __init__(self, grid_color = None, pen_color = QColor("black"), parent=None):
        super(IconBar, self).__init__(parent)

        # set an initial grid color
        self.grid_color = grid_color
        if not self.grid_color:
            self.grid_color = QColor(Qt.transparent)
        
        self.pen_color = pen_color
            
        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0,0,0,0)

        but = self.IconButton("icon_grid")
        but.clicked.connect(self.on_grid_clicked)
        hbox.addWidget(but)
        
        but = self.IconButton("icon_brush")
        but.clicked.connect(self.on_brush_clicked)
        hbox.addWidget(but)
        
        hbox.addStretch(2)
        self.setLayout(hbox)

    def on_brush_clicked(self):
        self.popup = ColorPopup(self.pen_color, "RGBA", self)
        self.popup.colorChanged.connect(self.onPenColorChanged)
        self.popup.show()

    def on_grid_clicked(self):
        self.popup = ColorPopup(self.grid_color, "aRGB", self)
        self.popup.colorChanged.connect(self.onGridColorChanged)
        self.popup.show()

    def onGridColorChanged(self, color):
        self.grid_color = color
        self.gridChanged.emit(color)
        
    def onPenColorChanged(self, color):
        self.pen_color = color
        self.penChanged.emit(color)
        
class PaintWidget(QWidget):
    def __init__(self, parent=None):

        super(PaintWidget, self).__init__(parent)

        # initially threre is no image to display
        self.filename = None
        self.img = None

        # and initially we don't know anything about the display
        self.buffer = None
        self.grid = None
        self.pen = QColor()
        
        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

    def setPen(self, color):
        self.pen = color
        
    def setGrid(self, color):
        if color and color.alpha() < 128:
            self.grid = None
        else:
            self.grid = color

        # if the grid setting changes the entire offscreen
        # has to be redrawn
        self.createBuffer()
        self.update()
        
    def load(self,name):
        img = QImage()
        if os.path.isabs(name):
            img.load(name)
        else:
            img.load(os.path.join(USERAPPBASE, name))
        img = img.convertToFormat(QImage.Format_ARGB32);
        if img and img.width() and img.width() == img.height():
            self.filename = name
            self.img = img
            self.rez = self.img.width()
            self.createBuffer()
            self.update()

    def save(self):
        if not self.img: return
        print("Save", self.filename)
        self.img.save(os.path.join(USERAPPBASE, self.filename))
            
    def pixelRect(self, x, y, border):
        if border:
            return QRectF(self.xoff+x*self.psize+border/2,
                          self.yoff+y*self.psize+border/2,
                          self.psize, self.psize)
        return QRect(self.xoff+x*self.psize,
                     self.yoff+y*self.psize,
                     self.psize, self.psize)

        
    def setPixel(self, evt):
        # if no image is loaded nothing can be drawn
        if not self.img: return
        
        # convert to pixel coordinates
        x = int((evt.x() - self.xoff)/self.psize)
        y = int((evt.y() - self.yoff)/self.psize)
        if x >= 0 and y >= 0 and x < self.rez and y < self.rez:
            if self.buffer:
                painter = QPainter()
                painter.begin(self.buffer)
            
                if not self.grid:
                    painter.setPen(Qt.NoPen)
                    border = 0
                else:
                    pen = QPen(self.grid)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    border = 1

                # make sure we actually replace the pixel
                painter.setCompositionMode(QPainter.CompositionMode_Source)

                # update offscreen bitmap of screen content
                painter.setBrush(QBrush(self.pen))
                painter.drawRect(self.pixelRect(x,y,border))
                painter.end()

            # request screen update
            self.update(self.pixelRect(x,y,None))

            self.img.setPixel(x, y, self.pen.rgba())
 
    def mousePressEvent(self, evt):
        self.pressed = True
        self.setPixel(evt)
            
    def mouseReleaseEvent(self, evt):
        self.pressed = False

    def mouseMoveEvent(self, evt):
        if self.pressed:
            self.setPixel(evt)
            
    def heightForWidth(self,w):
        return w

    def createBuffer(self):
        self.buffer = QImage(self.size(), QImage.Format_ARGB32)
        self.buffer.fill(Qt.transparent)

        # if no image is loaded nothing can be drawn
        if not self.img: return
        
        side = min(self.buffer.width(), self.buffer.height())
        self.psize = int(side/self.rez)

        # center graphics
        self.xoff = (self.buffer.width()-self.rez*self.psize)/2
        self.yoff = (self.buffer.height()-self.rez*self.psize)/2

        # the entire new buffer has to be drawn
        painter = QPainter()
        painter.begin(self.buffer)

        painter.setRenderHint(QPainter.Antialiasing)
        alpha = self.img.alphaChannel()

        if not self.grid:
            painter.setPen(Qt.NoPen)
            border = 0
        else:
            pen = QPen(self.grid)
            pen.setWidth(1)
            painter.setPen(pen)
            border = 1

        for y in range(self.rez):
            for x in range(self.rez):
                color = QColor(self.img.pixel(x, y))
                color.setAlpha(QColor(alpha.pixel(x, y)).lightness())
                painter.setBrush(QBrush(color))
                painter.drawRect(self.pixelRect(x,y,border))
                
        painter.end()

    def paintEvent(self, event):
        # if no image is loaded nothing can be drawn
        if not self.img: return
        
        # check if the buffer is present and matches the
        # widget size
        if not self.buffer or self.buffer.size() != self.size():
            self.createBuffer()
        
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(0,0,self.buffer)
        painter.end()

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        # create the empty main window
        self.w = TxtWindow("IconEdit")
        menu = self.w.addMenu()
        menu_load = menu.addAction("Load")
        menu_load.triggered.connect(self.on_menu_load)

        self.vbox = QVBoxLayout()

        # initial values
        self.grid = None
        self.pen = QColor("yellow")
        
        self.iconBar = IconBar(self.grid, self.pen)
        self.vbox.addWidget(self.iconBar)
        
        self.vbox.addStretch()

        self.paintWidget = PaintWidget()
        self.paintWidget.setGrid(self.grid)
        self.paintWidget.setPen(self.pen)
        self.paintWidget.load(os.path.join(USERAPPBASE, name))
        img = img.convertToFormat(QImage.Format_ARGB32);
        if img and img.width() and img.width() == img.height():
            self.img = img
            self.rez = self.img.width()
            self.update()

    def pixelRect(self, x, y, border):
        if border:
            return QRectF(self.xoff+x*self.psize+border/2,
                          self.yoff+y*self.psize+border/2,
                          self.psize, self.psize)
        return QRect(self.xoff+x*self.psize,
                     self.yoff+y*self.psize,
                     self.psize, self.psize)

        
    def setPixel(self, evt):
        # if no image is loaded nothing can be drawn
        if not self.img: return
        
        # convert to pixel coordinates
        x = int((evt.x() - self.xoff)/self.psize)
        y = int((evt.y() - self.yoff)/self.psize)
        if x >= 0 and y >= 0 and x < self.rez and y < self.rez:
            if self.buffer:
                painter = QPainter()
                painter.begin(self.buffer)
            
                if not self.grid:
                    painter.setPen(Qt.NoPen)
                    border = 0
                else:
                    pen = QPen(self.grid)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    border = 1

                # make sure we actually replace the pixel
                painter.setCompositionMode(QPainter.CompositionMode_Source)

                # update offscreen bitmap of screen content
                painter.setBrush(QBrush(self.pen))
                painter.drawRect(self.pixelRect(x,y,border))
                painter.end()

            # request screen update
            self.update(self.pixelRect(x,y,None))

            self.img.setPixel(x, y, self.pen.rgba())
 
    def mousePressEvent(self, evt):
        self.pressed = True
        self.setPixel(evt)
            
    def mouseReleaseEvent(self, evt):
        self.pressed = False

    def mouseMoveEvent(self, evt):
        if self.pressed:
            self.setPixel(evt)
            
    def heightForWidth(self,w):
        return w

    def createBuffer(self):
        self.buffer = QImage(self.size(), QImage.Format_ARGB32)
        self.buffer.fill(Qt.transparent)

        # if no image is loaded nothing can be drawn
        if not self.img: return
        
        side = min(self.buffer.width(), self.buffer.height())
        self.psize = int(side/self.rez)

        # center graphics
        self.xoff = (self.buffer.width()-self.rez*self.psize)/2
        self.yoff = (self.buffer.height()-self.rez*self.psize)/2

        # the entire new buffer has to be drawn
        painter = QPainter()
        painter.begin(self.buffer)

        painter.setRenderHint(QPainter.Antialiasing)
        alpha = self.img.alphaChannel()

        if not self.grid:
            painter.setPen(Qt.NoPen)
            border = 0
        else:
            pen = QPen(self.grid)
            pen.setWidth(1)
            painter.setPen(pen)
            border = 1

        for y in range(self.rez):
            for x in range(self.rez):
                color = QColor(self.img.pixel(x, y))
                color.setAlpha(QColor(alpha.pixel(x, y)).lightness())
                painter.setBrush(QBrush(color))
                painter.drawRect(self.pixelRect(x,y,border))
                
        painter.end()

    def paintEvent(self, event):
        # if no image is loaded nothing can be drawn
        if not self.img: return
        
        # check if the buffer is present and matches the
        # widget size
        if not self.buffer or self.buffer.size() != self.size():
            self.createBuffer()
        
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(0,0,self.buffer)
        painter.end()

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        # create the empty main window
        self.w = TxtWindow("IconEdit")
        menu = self.w.addMenu()
        menu_load = menu.addAction("Load")
        menu_load.triggered.connect(self.on_menu_load)
        menu_save = menu.addAction("Save")
        menu_save.triggered.connect(self.on_menu_save)

        self.vbox = QVBoxLayout()

        # initial values
        self.grid = None
        self.pen = QColor("yellow")
        
        self.iconBar = IconBar(self.grid, self.pen)
        self.vbox.addWidget(self.iconBar)
        
        self.vbox.addStretch()

        self.paintWidget = PaintWidget()
        self.paintWidget.setGrid(self.grid)
        self.paintWidget.setPen(self.pen)
        self.paintWidget.load(os.path.join(BASE, "icon.png"))

        # connect widgets
        self.iconBar.gridChanged.connect(self.paintWidget.setGrid)
        self.iconBar.penChanged.connect(self.paintWidget.setPen)
        
        self.vbox.addWidget(self.paintWidget)

        self.vbox.addStretch()

        self.w.centralWidget.setLayout(self.vbox)

        self.w.show() 

        self.exec_()        

    def on_menu_load(self):
        dialog = LoadDialog(self.w)
        dialog.load.connect(self.on_load)
        dialog.exec_()
        
    def on_menu_save(self):
        self.paintWidget.save()
        
    def on_load(self, filename):
        self.paintWidget.load(filename)
        
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
