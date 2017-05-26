#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

from TouchStyle import *

PORT = 9004
CLIENT = ""    # any client
MAX_TEXT_LINES=50           # same as web ui

import time, sys, asyncio, websockets, queue, pty, json, subprocess, select

# the websocket server is a seperate tread for handling the websocket
class WebsocketServerThread(QThread):
    connected = pyqtSignal(bool)
    # TODO: one generic signal!
    key = pyqtSignal(str)
    code = pyqtSignal(str)
    
    def __init__(self): 
        super(WebsocketServerThread,self).__init__()
        self.websocket = None

    def run(self): 
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        start_server = websockets.serve(self.handler, CLIENT, PORT)
        websocketServer = self.loop.run_until_complete(start_server)

        try:
            self.loop.run_forever()
        finally:
            websocketServer.close()
            self.loop.run_until_complete(websocketServer.wait_closed())

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        
    @asyncio.coroutine
    def handler(self, websocket, path):
        # reject any further client besides the first (main) one
        if self.websocket:
            return

        self.websocket = websocket

        self.connected.emit(True)

        # run while client is connected
        while(websocket.open):
            try:
                # receive json encoded commands via websocket
                msg_str = yield from websocket.recv()
                msg = json.loads(msg_str)
                
                # print("RX:", msg)

                if 'key' in msg:
                    self.key.emit(msg['key'])

                if 'code' in msg:
                    self.code.emit(msg['code'])
                    
            except websockets.exceptions.ConnectionClosed:
                pass

            finally:
                pass
            
        # the websocket is no more ....
        self.connected.emit(False)
        self.websocket = None

    # send a message to the connected client
    @asyncio.coroutine
    def send_async(self, str):
        yield from self.websocket.send(str)

    def send(self, str):
        # If there is no client then just drop the messages.
        if self.websocket and self.websocket.open:
            self.loop.call_soon_threadsafe(asyncio.async, self.send_async(str))

    def is_connected(self):
        return self.websocket != None

class PythonInteractiveThread(QThread):
    def __init__(self, stdout_fd): 
        super(PythonInteractiveThread,self).__init__()
        self.stdout_fd = stdout_fd
        self.in_master_fd = None

    def run(self):
        # change into current directory before running
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        
        self.out_master_fd, self.out_slave_fd = pty.openpty()
        self.in_master_fd, self.in_slave_fd = pty.openpty()
        self.proc = subprocess.Popen("python3", stdin=self.in_slave_fd,
                                     stdout=self.out_slave_fd, stderr=self.out_slave_fd)

        while self.proc.poll() == None:
            try:
                output = os.read(self.out_master_fd, 100)
                if output:
                    self.stdout_fd.write(str(output, "utf-8"))
                    self.stdout_fd.flush()
            except:
                pass

        print("python done:", self.proc.poll())

    def key(self, str):
        if self.in_master_fd:
            os.write(self.in_master_fd, bytes(str, 'UTF-8'))
   
# this object will be receiving text from stdout and stderr
class io_sink(object):
    def __init__(self, name, ws, ui_queue):
        self.name = name
        self.ui_queue = ui_queue
        self.ws = ws

    def write(self, message):
        if(self.ws):
            self.ws.send(json.dumps( { self.name: message } ))
        if(self.ui_queue):
            self.ui_queue.put(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass    

# a textedit
class TextWidget(QPlainTextEdit):
    def __init__(self, ws, parent=None):
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

        # redirect stdout, stderr info to websocket server.
        # redirect stdout also to the local screen
        sys.stdout = io_sink("stdout", ws, self.ui_queue)
        # sys.stderr = io_sink("stderr", ws, self.ui_queue)
        
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
            else:
                pass

class Application(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "boa_"))
        self.installTranslator(translator)

        # start the websocket server listening for web clients to connect
        self.ws = WebsocketServerThread()
        self.ws.start()
        self.ws.connected.connect(self.on_connected)

        # create the empty main window
        self.w = TouchWindow("Boa")

        # the program text output screen
        self.text = TextWidget(self.ws, self.w)
        self.w.setCentralWidget(self.text)

        # start python interpreter not before browser
        # has connected
        self.py = None
        
        self.w.show()
        self.exec_()        

        self.ws.stop()

    def on_code_rx(self, code):
        # print("RX code:", code)
        
        # store code in file
        path = os.path.dirname(os.path.realpath(__file__))
        fname = os.path.join(path, "code.py")
        with open(fname, 'w', encoding="UTF-8") as f:
            f.write(code)
            f.close()

        # and tell interpreter to load and run it
        if self.py:
            self.py.key("exec(open('code.py').read())\n")
            
    def on_connected(self, connected):
        # send current code, so the editor gets updated
        path = os.path.dirname(os.path.realpath(__file__))
        fname = os.path.join(path, "code.py")

        # file really does exist?
        if os.path.isfile(fname):
            # load and execute locally stored blockly code
            with open(fname, encoding="UTF-8") as f:
                self.ws.send(json.dumps( { "code": f.read() } ))
        
        # browser has connected!
        if self.py:
            # send only to browser and not to local screen
            self.ws.send(json.dumps( { "stdout": "Interpreter already running\n>>> " } ))
            return
        
        # run the interactive python interpreter 
        self.py = PythonInteractiveThread(sys.stdout)
        # forward any key from websocket to interpreter
        self.ws.key.connect(self.py.key)
        self.ws.code.connect(self.on_code_rx)
        self.py.start()
        
if __name__ == "__main__":
    Application(sys.argv)
