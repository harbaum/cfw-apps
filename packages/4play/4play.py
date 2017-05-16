#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# based on FourPlay from https://github.com/vojtamolda/games 

from TouchStyle import *
import random
import sys


class FourPlay:
    class Disc:
        def __init__(self, row, column, frontier):
            self.row, self.column = row, column
            self.frontier = frontier
            self.delegate = None
            self.player = None
            self.marked = False
            self.rank = 0

        def __eq__(self, other):
            return (self.row, self.column) == (other.row, other.column) if other is not None else False

        def __str__(self):
            return str(self.player) if self.player is not None else "M"

        def set(self, player, notify=False):
            self.player = player
            self.frontier.increase(self.column, notify)
            self.notify(notify)

        def clear(self, notify=False):
            self.player = None
            self.frontier.decrease(self.column, notify)
            self.notify(notify)

        def playable(self):
            retval = self in self.frontier
            return retval

        def mark(self, notify=False):
            self.marked = True
            self.notify(notify)

        def notify(self, notify=False):
            if self.delegate is not None and notify is True:
                self.delegate.updateEvent(self)

        def neighbor(self, fourPlay, location=None):
            diffRow, diffCol = location[0], location[1]
            neighborRow, neighborCol = self.row + diffRow, self.column + diffCol
            if (neighborRow, neighborCol) in fourPlay:
                return fourPlay[(neighborRow, neighborCol)]
            else:
                return None

        def crawl(self, fourPlay, direction, player, notify=False):
            if self.player == player:
                if notify is True:
                    self.mark(True)
                neighbor = self.neighbor(fourPlay, direction)
                if neighbor is not None:
                    return neighbor.crawl(fourPlay, direction, player, notify) + 1
                else:
                    return 1
            return 0

        def score(self, fourPlay, player, notify=False):
            for forward in [(+1, 0), (0, +1), (+1, +1), (+1, -1)]:
                rearward = -forward[0], -forward[1]
                numConnected = self.crawl(fourPlay, forward, player) + self.crawl(fourPlay, rearward, player) - 1
                if numConnected >= 4:
                    if notify is True:
                        self.crawl(fourPlay, forward, player, True)
                        self.crawl(fourPlay, rearward, player, True)
                    return 1
            if len(list(self.frontier)) == 0:
                return 0
            return None

        def reset(self, notify=False):
            self.player = None
            self.marked = False
            self.rank = 0
            self.notify(notify)

    class Frontier:
        def __init__(self, fourPlay):
            self.fourPlay = fourPlay
            self.frontier = []

        def __contains__(self, disc):
            return disc == self.frontier[disc.column] if disc is not None else False

        def __getitem__(self, column):
            return self.frontier[column]

        def __iter__(self):
            frontier = list(filter(lambda disc: disc is not None, self.frontier))
            random.shuffle(frontier)
            return frontier.__iter__()

        def __str__(self):
            string = ""
            for disc in self.frontier:
                string += str(disc.row) if disc is not None else "_"
            return string

        def increase(self, column, notify=False):
            disc = self.frontier[column]
            if disc is None:
                return
            discAbove = disc.neighbor(self.fourPlay, (-1, 0))
            self.frontier[column] = discAbove
            if discAbove is not None:
                discAbove.notify(notify)

        def decrease(self, column, notify=False):
            disc = self.frontier[column]
            if disc is None:
                topRowDisc = self.fourPlay[0, column]
                self.frontier[column] = topRowDisc
                topRowDisc.notify(notify)
                return
            discBelow = disc.neighbor(self.fourPlay, (+1, 0))
            self.frontier[column] = discBelow
            if discBelow is not None:
                discBelow.notify(notify)

        def reset(self):
            self.frontier = []
            for column in range(self.fourPlay.columns):
                for row in reversed(range(self.fourPlay.rows)):
                    disc = self.fourPlay[row, column]
                    if disc.player is None:
                        self.frontier.append(disc)
                        break
                else:
                    self.frontier.append(None)

    class Player:
        def __init__(self, symbol):
            self.symbol = symbol

        def __str__(self):
            return str(self.symbol)

        def play(self, fourPlay, opponent, column):
            return 0, fourPlay.frontier[column]

    class AI(Player):
        def play(self, fourPlay, opnt, selfBestResult=(-2, None), opntBestResult=(+2, None), recursionLevel=1):
            recursionLimit = 8
            for disc in fourPlay.frontier:
                # print("think ...")
                QApplication.processEvents()
                disc.set(self)
                selfResult = (disc.score(fourPlay, self), disc)
                if selfResult[0] is None:
                    if recursionLevel < recursionLimit:
                        subtreeSelfBestResult = (-selfBestResult[0], selfBestResult[1])
                        subtreeOpntBestResult = (-opntBestResult[0], opntBestResult[1])
                        opntResult = FourPlay.AI.play(opnt, fourPlay, self, subtreeOpntBestResult,
                                                      subtreeSelfBestResult, recursionLevel + 1)
                        selfResult = (-opntResult[0], selfResult[1])
                    else:
                        selfResult = (-1 / recursionLimit, selfResult[1])
                else:
                    selfResult = (selfResult[0] / recursionLevel, selfResult[1])
                disc.clear()

                if selfResult[0] > selfBestResult[0]:
                    selfBestResult = selfResult
                if opntBestResult[0] <= selfBestResult[0]:
                    break

            return selfBestResult

    def __init__(self, rows, columns):
        self.rows, self.columns = rows, columns
        self.ai = FourPlay.AI("X")
        self.player = FourPlay.Player("O")
        self.frontier = FourPlay.Frontier(self)
        self.discs = {}
        for row in range(self.rows):
            for column in range(self.columns):
                disc = FourPlay.Disc(row, column, self.frontier)
                self.discs[row, column] = disc
        self.frontier.reset()

    def __contains__(self, row_column):
        return row_column in self.discs

    def __getitem__(self, row_column):
        return self.discs[row_column]

    def __iter__(self):
        return self.discs.values().__iter__()

    def __str__(self):
        string = ""
        for row in range(self.rows):
            for column in range(self.columns):
                string += str(self[row, column])
            string += "\n"
        return string

    @classmethod
    def create(FourPlay, symbols):
        fourPlay = FourPlay(len(symbols), len(symbols[0]))
        for row, symbols_row in enumerate(symbols):
            for column, symbol in enumerate(symbols_row):
                disc = fourPlay[row, column]
                if symbol == fourPlay.ai.symbol:
                    disc.player = fourPlay.ai
                if symbol == fourPlay.player.symbol:
                    disc.player = fourPlay.player
        fourPlay.frontier.reset()
        return fourPlay

    def playRound(self, column):
        _, playerDisc = self.player.play(self, self.ai, column)
        if playerDisc:
            playerDisc.set(self.player, True)
            playerScore = playerDisc.score(self, self.player, True)
            if playerScore is not None:
                return playerScore

            _, aiDisc = self.ai.play(self, self.player)
            aiDisc.set(self.ai, True)
            aiScore = aiDisc.score(self, self.ai, True)
            if aiScore is not None:
                return -aiScore
            return None

    def reset(self):
        for disc in self:
            disc.reset(False)
        self.frontier.reset()
        for disc in self:
            disc.notify(True)


class QFourPlay(QWidget):
    class QDiscButton(QPushButton):
        def __init__(self, playerColorMap):
            super(QFourPlay.QDiscButton, self).__init__()
            self.playerColorMap = playerColorMap
            self.marked = False
            self.color = None
            self.playable = False
            self.highlight = False
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setFocusPolicy(Qt.NoFocus)
            self.setMouseTracking(True)

        def updateEvent(self, disc):
            self.marked = disc.marked
            self.color = self.playerColorMap[disc.player]
            self.playable = disc.playable()
            self.update()

        def clickEvent(self, clicked, disc):
            self.leaveEvent()
            self.parent().parent().playRound(disc.column)
            self.enterEvent()
            return

        def enterEvent(self, *args, **kwargs):
            if self.playable is True:
                self.highlight = True
                self.update()

        def leaveEvent(self, *args, **kwargs):
            if self.playable is True:
                self.highlight = False
                self.update()

        def paintEvent(self, paintEvent):
            painter = QPainter(self)
            painter.setBackgroundMode(Qt.TransparentMode)
            painter.setRenderHint(QPainter.Antialiasing)
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            pen = QPen()
            pen.setJoinStyle(Qt.RoundJoin)
            pen.setCapStyle(Qt.RoundCap)

            center = QPoint(self.width() / 2, self.height() / 2)
            radius = 0.45 * min(self.width(), self.height())

            pen.setColor(self.palette().color(self.color[0]))
            brush.setColor(self.palette().color(self.color[1]))
            pen.setWidth(0.15 * radius)
            if self.highlight is True:
                pen.setColor(self.palette().color(QPalette.Highlight))
            if self.marked is True:
                pen.setColor(QColor("#fcce04"))
                pen.setWidth(0.25 * radius)
            
            painter.setBrush(brush)
            painter.setPen(pen)
            painter.drawEllipse(center, radius, radius)

#            if self.marked is True:
#                brush.setColor(self.palette().color(QPalette.Background))
#                pen.setColor(self.palette().color(QPalette.Background))
#                brush.setColor(QColor("red"))
#                pen.setColor(QColor("red"))
#                painter.setPen(pen)
#                painter.setBrush(brush)
#                painter.drawEllipse(center, 0.40 * radius, 0.40 * radius)

            del painter, brush, pen

    def __init__(self):
        super(QFourPlay, self).__init__()
        self.busy = False
        self.fourPlay = None
        self.initGame()
        self.initUI()
        self.reset()

    def initGame(self):
        self.fourPlay = FourPlay(6, 7)

    def initUI(self):
        vbox = QVBoxLayout()

        gridW = QWidget()
        layout = QGridLayout()
        layout.setSpacing(4)
        gridW.setLayout(layout)

        vbox.addWidget(gridW)
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter) 
        vbox.addWidget(self.label)

        self.setLayout(vbox)
        
        playerColorMap = {None: (QPalette.Dark, QPalette.Background),
                          self.fourPlay.player: (QPalette.Highlight, QPalette.Highlight),
                          self.fourPlay.ai: (QPalette.Dark, QPalette.Dark)}

        for disc in self.fourPlay:
            button = QFourPlay.QDiscButton(playerColorMap)
            layout.addWidget(button, disc.row, disc.column)
            button.clicked.connect(lambda _, button=button, disc=disc: button.clickEvent(self, disc))
            button.updateEvent(disc)
            disc.delegate = button

    def reset(self):
        self.fourPlay.reset()
        self.label.setText(QCoreApplication.translate("result", "your turn ..."))
        self.busy = False

    def playRound(self, column):
        if self.busy: return
        
        self.busy = True
        self.label.setText(QCoreApplication.translate("result", "thinking ..."))
        gameScore = self.fourPlay.playRound(column)
        self.label.setText(QCoreApplication.translate("result", "your turn ..."))
        if gameScore is not None:
            if gameScore == +1:
                self.label.setText(QCoreApplication.translate("result", "You win"))
            if gameScore == 0:
                self.label.setText(QCoreApplication.translate("result", "Tie"))
            if gameScore == -1:
                self.label.setText(QCoreApplication.translate("result", "You loose"))
        else:
            self.busy = False
                
class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "4play_"))
        self.installTranslator(translator)

        # create the empty main window
        self.w = TouchWindow(QCoreApplication.translate("main", "4Play"))
        self.w.setCentralWidget(QFourPlay())

        menu = self.w.addMenu()
        self.menu_new = menu.addAction(QCoreApplication.translate("menu", "New"))
        self.menu_new.triggered.connect(self.w.centralWidget.reset)
 
        self.w.show() 
        self.exec_()
 
if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
