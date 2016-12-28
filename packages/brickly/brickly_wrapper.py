#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

# Wrapper for brickly.py python code. The main purpose of
# this wrapper is to catch the output of brickly.py and send
# it to the browser as well as to a local GUI

PORT = 9002
CLIENT = ""    # any client
OUTPUT_DELAY = 0.01
MAX_HIGHLIGHTS_PER_SEC = 25

import time, sys, threading, asyncio, websockets, queue, pty, json
import os

speed = 100  # range 0 .. 100

# the websocket server is a seperate thread for handling the websocket
class websocket_server(threading.Thread): 
    def __init__(self): 
        threading.Thread.__init__(self) 
        self.clients = []
        self.queue = queue.Queue()
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
        self.websocket = websocket
        self.clients.append(websocket)

        # Client has finally connected. First
        # send all queued messages
        while not self.queue.empty():
            yield from self.websocket.send(self.queue.get())
        
        # ToDo: keep list of clients, stop
        # when last client is gone
        while(websocket.open):
            try:
                msg_str = yield from websocket.recv()
                msg = json.loads(msg_str)

                if 'speed' in msg:
                    global speed
                    speed = int(msg['speed'])

            except websockets.exceptions.ConnectionClosed:
                pass

            finally:
                pass

        # the websocket is no more ....
        self.websocket = None

    # send a message to all connected clients
    @asyncio.coroutine
    def send_async(self, str):
        yield from self.websocket.send(str)

    def send(self, allow_queueing, str):
        # If there is no client then just queue the messages. These will
        # then be sent once a client has connected
        if self.websocket:
            self.loop.call_soon_threadsafe(asyncio.async, self.send_async(str))
        elif allow_queueing:
            self.queue.put(str)

    def connected(self):
        return self.websocket != None
        
# this object will be receiving everything from stdout
class io_sink(object):
    def __init__(self, name, allow_queueing, thread):
        self.name = name
        self.allow_queueing = allow_queueing
        self.thread = thread

    def write(self, message):
        # slow down everything that allows queuing
        # to keep the system usable
        if self.allow_queueing:
            time.sleep(OUTPUT_DELAY)

        self.thread.send(self.allow_queueing, json.dumps( { self.name: message } ))

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass    

# this function is called from the blockly code itself. This feature has
# to be enabled on javascript side in the code generation. A rate limit
# makes sure the browser can cope with this
def highlightBlock(str):
    now = time.time()*1000.0
    if now > highlightBlock.last + (1000/MAX_HIGHLIGHTS_PER_SEC):
        highlightBlock.last = now

        global speed, highlight
        time.sleep((100-speed)/100)
        highlight.write(str)

highlightBlock.last = 0

thread = websocket_server()
thread.start() 

# redirect stdout and sterr to websocket server as well as into file
sys.stdout = io_sink("stdout", True, thread)
sys.stderr = io_sink("stderr", True, thread)
highlight  = io_sink("highlight", False, thread)

# connect to TXT
txt_ip = os.environ.get('TXT_IP')
txt = None
if txt_ip:
    try:
        import ftrobopy
        txt = ftrobopy.ftrobopy(txt_ip, 65000)
        # all outputs normal mode
        M = [ txt.C_OUTPUT, txt.C_OUTPUT, txt.C_OUTPUT, txt.C_OUTPUT ]
        I = [ (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ),
              (txt.C_SWITCH, txt.C_DIGITAL ) ]
        txt.setConfig(M, I)
        txt.updateConfig()
    except:
        print("TXT init failed", file=sys.stderr)
else:
    print("There is no TXT", file=sys.stderr)

# TXT specific helper routines
def setOutput(port, val):
    if not txt:
        # if no TXT could be connected just write to stderr
        print("O" + str(port+1) + "=" + str(val), file=sys.stderr)
    else:
        if val:
            pwm_val = 512
        else:   
            pwm_val = 0

        txt.setPwm(port,pwm_val)

def getInput(port):
    if not txt:
        # if no TXT could be connected just write to stderr
        print("I" + str(port+1) + "=" + str(True), file=sys.stderr)
        return True
    else:
        return not txt.getCurrentInput(port)

def playSound(snd):
    if not txt:
        # if no TXT could be connected just write to stderr
        print("SND " + str(snd), file=sys.stderr)
    else:
        txt.setSoundIndex(snd)
        txt.incrSoundCmdId()

online = False
path = os.path.dirname(os.path.realpath(__file__))
fname = os.path.join(path, "brickly.py")
stamp_fname = os.path.join(path, "brickly.stamp")
if not os.path.isfile(fname):
    fname = os.path.join(path, "default.py")
else:
    # A brickly.py was found. Now check if there's a stamp
    # that's older than brickly.py. If it is then the
    # brickly.py has never been run before which in turn
    # means that brickly_app has been launched from the
    # web interface
            
    # if no stamp exists at all then we are also running
    # online
    if not os.path.isfile(stamp_fname):
        online = True
    else:
        brickly_time = os.stat(fname).st_mtime
        stamp_time = os.stat(stamp_fname).st_mtime
        if brickly_time > stamp_time:
            online = True

stamp = open(stamp_fname, 'w')
stamp.close()

# wait for client before executing code
while not thread.connected():
    time.sleep(0.01)

# load and execute blockly code
with open(fname, encoding="UTF-8") as f:
    try:
        code_txt = f.read()
        code_txt = code_txt.replace("# highlightBlock(", "highlightBlock(");
        code = compile(code_txt, "brickly.py", 'exec')
        exec(code)
    except SyntaxError as e:
        print("Syntax error: " + str(e), file=sys.stderr)
    except:
        print("Unexpected error: " + str(sys.exc_info()), file=sys.stderr)

# program stays alive for 5 seconds after download
highlight.write("none")
time.sleep(5)

# now we could the server thread as we don't need it anymore. But letting
# it run makes the client side happy as it doesn't have to deal with a
# lost websocket connection
thread.stop()

