#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import cgi
import cgitb
import os
import signal
import socket

cgitb.enable(format='text')

form = cgi.FieldStorage()

if "pid" in form:
    # write a valid http reply header
    print("Content-Type: text/html")
    print("")
    pid = int(form["pid"].value)
    if pid != 0:
        os.kill(pid, signal.SIGKILL)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Connect to server and send data
            sock.connect(("localhost", 9000))
            sock.sendall(bytes("stop-app\n", "UTF-8"))
        except socket.error as msg:
            pass
        finally:
            sock.close()

    print("Program stopped")
else:
    print('Status: 404 No pid not found')
    print("Content-Type: text/html")
    print("")
