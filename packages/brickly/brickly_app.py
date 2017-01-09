#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

from TouchStyle import *

PORT = 9002
CLIENT = ""    # any client

FLOAT_FORMAT = "{0:.3f}"    # limit to three digits to keep the output readable
OUTPUT_DELAY = 0.01
MAX_HIGHLIGHTS_PER_SEC = 25

import time, sys, asyncio, websockets, queue, pty, json, math 
import ftrobopy_custom

# the websocket server is a seperate tread for handling the websocket
class WebsocketServerThread(QThread):
    command = pyqtSignal(str)
    setting = pyqtSignal(dict)
    python_code = pyqtSignal(str)
    blockly_code = pyqtSignal(str)
    client_connected = pyqtSignal()
    speed_changed = pyqtSignal(int)
    
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

        self.client_connected.emit()

        # run while client is connected
        while(websocket.open):
            try:
                msg_str = yield from websocket.recv()
                msg = json.loads(msg_str)

                if 'speed' in msg:
                    self.speed_changed.emit(int(msg['speed']))
                if 'lang' in msg:
                    self.setting.emit( { 'lang': msg['lang'] } )
                if 'skill' in msg:
                    self.setting.emit( { 'skill': msg['skill'] })
                if 'command' in msg:
                    self.command.emit(msg['command'])
                if 'python_code' in msg:
                    self.python_code.emit(msg['python_code'])
                if 'blockly_code' in msg:
                    self.blockly_code.emit(msg['blockly_code'])
                    
            except websockets.exceptions.ConnectionClosed:
                pass

            finally:
                pass
            
        # the websocket is no more ....
        self.websocket = None

    # send a message to the connected client
    @asyncio.coroutine
    def send_async(self, str):
        yield from self.websocket.send(str)

    def send(self, str):
        # If there is no client then just drop the messages.
        if self.websocket and self.websocket.open:
            self.loop.call_soon_threadsafe(asyncio.async, self.send_async(str))

    def connected(self):
        return self.websocket != None

# this object will be receiving everything from stdout
class io_sink(object):
    def __init__(self, name, thread, ui_queue):
        self.name = name
        self.ui_queue = ui_queue
        self.thread = thread

    def write(self, message):
        # todo: slow down stdout and stderr only
        time.sleep(OUTPUT_DELAY)

        if(self.thread):
            self.thread.send(json.dumps( { self.name: message } ))
        if(self.ui_queue):
            self.ui_queue.put(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass    

class UserInterrupt(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "UserInterrupt: " + repr(self.value)

# another sperate thread executes the code itself
class RunThread(QThread):
    done = pyqtSignal()
    
    def __init__(self, ws_thread, ui_queue):
        super(RunThread,self).__init__()

        self.speed = 90  # range 0 .. 100

        self.ws_thread = ws_thread  # websocket server thread
        self.ui_queue = ui_queue    # output queue to the local gui

        # connect to TXT
        try:
            self.txt = ftrobopy_custom.ftrobopy_custom()
        except:
            self.txt = None

        if self.txt:
            # all outputs normal mode
            self.M = [ self.txt.C_OUTPUT, self.txt.C_OUTPUT,
                       self.txt.C_OUTPUT, self.txt.C_OUTPUT ]
            self.I = [ (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                       (self.txt.C_SWITCH, self.txt.C_DIGITAL ) ]
            self.txt.setConfig(self.M, self.I)
            self.txt.updateConfig()
                
        self.motor = [ None, None, None, None ]

        # redirect stdout, stderr and highlight info to websocket server.
        # redirect stdout also to the local screen
        sys.stdout = io_sink("stdout", self.ws_thread, self.ui_queue)
        sys.stderr = io_sink("stderr", self.ws_thread, None)
        self.highlight  = io_sink("highlight", self.ws_thread, None)

        if not self.txt:
            print("TXT init failed", file=sys.stderr)

    def run(self):
        self.stop_requested = False
        self.online = False
        path = os.path.dirname(os.path.realpath(__file__))
        fname = os.path.join(path, "brickly.py")
        if not os.path.isfile(fname):
            fname = os.path.join(path, "default.py")

        # load and execute locally stored blockly code
        with open(fname, encoding="UTF-8") as f:
            try:
                # replace global calls by calls into the local class
                # this could be done on javascript side but this would make
                # the bare generated python code harder to read
                global wrapper
                wrapper = self    # make self accessible to all functions of blockly code
                
                code_txt = f.read()
                code_txt = code_txt.replace("# speed", "wrapper.ws_thread.speed");
                code_txt = code_txt.replace("# highlightBlock(", "wrapper.highlightBlock(");
                code_txt = code_txt.replace("setOutput(", "wrapper.setOutput(");
                code_txt = code_txt.replace("setMotor(", "wrapper.setMotor(");
                code_txt = code_txt.replace("wait(", "wrapper.wait(");
                code_txt = code_txt.replace("print(", "wrapper.print(");
                code_txt = code_txt.replace("str(", "wrapper.str(");
                code_txt = code_txt.replace("setMotorOff(", "wrapper.setMotorOff(");
                code_txt = code_txt.replace("motorHasStopped(", "wrapper.motorHasStopped(");
                code_txt = code_txt.replace("getInput(", "wrapper.getInput(");
                code_txt = code_txt.replace("inputConvR2T(", "wrapper.inputConvR2T(");
                code_txt = code_txt.replace("playSound(", "wrapper.playSound(");

                # code = compile(code_txt, "brickly.py", 'exec')
                # exec(code, globals())

                exec(code_txt, globals())
                
            except SyntaxError as e:
                print("Syntax error: " + str(e), file=sys.stderr)
            except UserInterrupt as e:
                self.highlight.write("interrupted")
            except:
                print("Unexpected error: " + str(sys.exc_info()[1]), file=sys.stderr)

            self.done.emit()
            self.highlight.write("none")

            # shut down all outputs
            if self.txt:
                for i in range(4):
                    # switch motors off
                    if self.M[i] == self.txt.C_MOTOR:
                        self.motor[i].stop()
                    # turn outputs off
                    if self.M[i] == self.txt.C_OUTPUT:
                        self.txt.setPwm(2*i,  0)
                        self.txt.setPwm(2*i+1,0)
                
    def stop(self):
        self.stop_requested = True

    def set_speed(self, val):
        self.speed = val
            
    def wait(self, duration):
        # make sure we never pause more than 100ms to be able
        # to react fast on user interrupts
        while(duration > 0.1):
            time.sleep(0.1)
            duration -= 0.1
            if self.stop_requested:
                raise UserInterrupt(42)
            
        time.sleep(duration)

    # custom string conversion
    def str(self, arg):
        # use custom conversion for float numbers
        if type(arg) is float:
            if math.isinf(arg):
                return "∞" 
            if math.isnan(arg):
                return "???"   # this doesn't need translation ...
            else:
                return FLOAT_FORMAT.format(arg).rstrip('0').rstrip('.')
            
        return str(arg)

    def print(self, *args, **kwargs):
        argsl = list(args)  # tuples are immutable, so use a list

        # make sure floats are converted using our custom conversion
        for i in range(len(argsl)):
            if type(argsl[i]) is float:
                argsl[i] = self.str(argsl[i])

        # todo: don't call print but push data directly into queue
        print(*tuple(argsl), **kwargs)
        
    def setMotor(self,port=0,dir=1,val=0,steps=None):
        # make sure val is in 0..100 range
        val = max(-100, min(100, val))
        # and scale it to 0 ... 512 range
        pwm_val = int(5.12 * val)
        # apply direction
        if dir < 0: pwm_val = -pwm_val;
        
        if not self.txt:
            # if no TXT could be connected just write to stderr
            print("M" + str(port+1) + "=" + str(pwm_val), file=sys.stderr)
        else:
            # check if that port is in motor mode and change if not
            if self.M[port] != self.txt.C_MOTOR:
                self.M[port] = self.txt.C_MOTOR
                self.txt.setConfig(self.M, self.I)
                self.txt.updateConfig()
                # generate a motor object
                self.motor[port] = self.txt.motor(port+1)
                
            if steps:
                self.motor[port].setDistance(int(63*steps))
                
            self.motor[port].setSpeed(pwm_val)

            
    def setMotorOff(self,port=0):
        if not self.txt:
            # if no TXT could be connected just write to stderr
            print("M" + str(port+1) + "= off", file=sys.stderr)
        else:
            # make sure that the port is in motor mode
            if self.M[port] == self.txt.C_MOTOR:
                self.motor[port].stop()

    def motorHasStopped(self,port=0):
        if not self.txt:
            # if no TXT could be connected just write to stderr
            print("M" + str(port+1) + "= off?", file=sys.stderr)
            return True
        else:
            # make sure that the port is in motor mode
            if self.M[port] != self.txt.C_MOTOR:
                return True

        return self.motor[port].finished()

    def setOutput(self,port=0,val=0):
        # make sure val is in 0..100 range
        val = max(0, min(100, val))
        # and scale it to 0 ... 512 range
        pwm_val = int(5.12 * val)

        if not self.txt:
            # if no TXT could be connected just write to stderr
            print("O" + str(port+1) + "=" + str(pwm_val), file=sys.stderr)
        else:
            # check if that port is in output mode and change if not
            if self.M[int(port/2)] != self.txt.C_OUTPUT:
                self.M[int(port/2)] = self.txt.C_OUTPUT
                self.txt.setConfig(self.M, self.I)
                self.txt.updateConfig()
                # forget about any motor object that may exist
                self.motor[int(port/2)] = None                
        
            self.txt.setPwm(port,pwm_val)

    def getInput(self,type,port):
        if not self.txt:
            # if no TXT could be connected just write to stderr
            print("I" + str(port+1) + " " + type + " = 0", file=sys.stderr)
            return 0
        else:
            input_type = {
                "voltage":    ( self.txt.C_VOLTAGE,    self.txt.C_ANALOG  ),
                "switch" :    ( self.txt.C_SWITCH,     self.txt.C_DIGITAL ),
                "resistor":   ( self.txt.C_RESISTOR,   self.txt.C_ANALOG  ),
                "resistor2":  ( self.txt.C_RESISTOR2,  self.txt.C_ANALOG  ),
                "ultrasonic": ( self.txt.C_ULTRASONIC, self.txt.C_ANALOG  )
            }
        
            # check if type of port has changed and update config
            # in that case
            if self.I[port] != input_type[type]:
                self.I[port] = input_type[type]
                self.txt.setConfig(self.M, self.I)
                self.txt.updateConfig()
                time.sleep(0.1)   # wait some time so the change can take effect

            # get value
            return self.txt.getCurrentInput(port)

    def inputConvR2T(self,sys="degCelsius",val=0):
        K2C = 273.0
        B = 3900.0
        R_N = 1500.0
        T_N = K2C + 25.0

        if val == 0: return float('nan')
        
        # convert resistance to kelvin
        t = T_N * B / (B + T_N * math.log(val / R_N))

        # convert kelvin to deg celius or deg fahrenheit
        if sys == "degCelsius":      t -= K2C
        if sys == "degFahrenheit":   t = t * 9 / 5 - 459.67
        
        return t

    def playSound(self,snd):
        if not self.txt:
            # if no TXT could be connected just write to stderr
            print("SND " + str(snd), file=sys.stderr)
        else:
            if snd < 1:  snd = 1
            if snd > 29: snd = 29
            
            self.txt.setSoundIndex(snd)
            self.txt.incrSoundCmdId()
        
    # this function is called from the blockly code itself. This feature has
    # to be enabled on javascript side in the code generation. The delay 
    # limits the load on the browser/client
    def highlightBlock(self, str):
        if self.stop_requested:
            raise UserInterrupt(42)
            
        if not hasattr(self, 'last'):
            self.last = 0

        now = time.time()*1000.0
        if now > self.last + (1000/MAX_HIGHLIGHTS_PER_SEC):
            self.last = now

            time.sleep((100-self.speed)/100)
            self.highlight.write(str)
            
class Application(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        # settings that may be sent from browser
        self.settings = { }

        translator = QTranslator()
        path = os.path.dirname(os.path.realpath(__file__))
        translator.load(QLocale.system(), os.path.join(path, "brickly_"))
        self.installTranslator(translator)

        # start the websocket server listening for web clients to connect
        self.ws = WebsocketServerThread()
        self.ws.start()
        self.ws.command.connect(self.on_command)
        self.ws.setting.connect(self.on_setting)
        self.ws.client_connected.connect(self.on_client_connect)
        self.ws.python_code.connect(self.on_python_code)        # received python code
        self.ws.blockly_code.connect(self.on_blockly_code)      # received blockly code

        # create the empty main window
        w = TouchWindow("Brickly")

        menu = w.addMenu()
        self.menu_run = menu.addAction(QCoreApplication.translate("Menu","Run..."))
        self.menu_run.triggered.connect(self.on_menu_run)

        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        w.setCentralWidget(self.txt)

        # a timer to read the ui output queue and to update
        # the screen
        self.ui_queue = queue.Queue()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(10)
        
        # start the run thread executing the blockly code
        self.thread = RunThread(self.ws, self.ui_queue)
        self.thread.done.connect(self.on_program_ended)
        self.ws.speed_changed.connect(self.thread.set_speed)

        # check for launch flag and run ...
        path = os.path.dirname(os.path.realpath(__file__))
        launch_fname = os.path.join(path, "brickly.launch")
        if os.path.isfile(launch_fname):
            os.remove(launch_fname)
        else:
            self.program_run()
  
        w.show()
        self.exec_()        

        self.ws.stop()

    def write_to_file(self, name, data):
        path = os.path.dirname(os.path.realpath(__file__))
        fname = os.path.join(path, name)
        with open(fname, 'w', encoding="UTF-8") as f:
            f.write(data)
            f.close()

    def on_client_connect(self):
        # tell browser whether code is being executed
        self.ws.send(json.dumps( { "running": not self.thread.isFinished() } ))

    def on_python_code(self, str):
        self.write_to_file("brickly.py", str)
        
    def on_blockly_code(self, str):
        self.write_to_file("brickly.xml", str)
     
    def on_setting(self, setting):
        for i in setting.keys():
            self.settings[i] = setting[i]

    def on_command(self, str):
        # handle commands received from browser
        if str == "run":  self.program_run()
        if str == "stop": self.thread.stop()
        if str == "save_settings": self.save_settings()

    def save_settings(self):
        # save current settings
        settings = ""
        for i in self.settings:
            settings += "var " + i + " = "
            if type(self.settings[i]) is str:
                settings += "'"+ self.settings[i]+"'"
            else:
                settings += str(self.settings[i])
            settings += ";\n"

        self.write_to_file("settings.js", settings)

    def on_timer(self):
        while not self.ui_queue.empty():
            self.append(self.ui_queue.get())

    def append(self, str):
        self.txt.moveCursor(QTextCursor.End)
        self.txt.insertPlainText(str)

    def on_program_ended(self):
        self.menu_run.setText(QCoreApplication.translate("Menu","Run..."))
        
    def program_run(self):
        # change "Run..." to "Stop!"
        self.menu_run.setText(QCoreApplication.translate("Menu","Stop!"))
        
        # clear screen
        self.ws.send(json.dumps( { "gui_cmd": "clear" } ))
        self.txt.clear()

        # and tell web gui that the program now runs
        self.ws.send(json.dumps( { "gui_cmd": "run" } ))
        
        # and start thread (again)
        self.thread.start()

    def program_stop(self):
        self.thread.stop()

    def on_menu_run(self):
        if not self.thread.isFinished():
            self.program_stop()
        else:
            self.program_run()

if __name__ == "__main__":
    Application(sys.argv)
