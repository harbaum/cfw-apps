#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import sys
import os
import socket
import time

# send a command to the launcher and if a reply is expected return
# the reply or None if the connection failed
def launcher_cmd(str, expect_reply=False):
    reply = None
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to server and send data
        sock.connect(("localhost", 9000))
        sock.sendall(bytes(str+"\n", "UTF-8"))
        if expect_reply:
            reply = sock.makefile().readline().strip()
        else:
            reply = True
    except socket.error as msg:
        pass
    finally:
        sock.close()

    # if no reply is expected then only return "True" or "False"
    if not expect_reply and reply == None:
        reply = False

    return reply

# request executable name of currently running app from 
# launcher. If current_executable is None, then no launcher
# is running at all. If it's "" then the launcher is running
# but no app is running. Otherwise a path like
# system/about/about.py is returned
current_executable = launcher_cmd("get-app", True)

# some app is running -> stop it
if current_executable != None and current_executable != "":
    launcher_cmd("stop-app")

    # wait for app to be stopped ...
    while launcher_cmd("get-app", True) != "":
        time.sleep(0.1)

# write a valid http reply header
print("Content-Type: text/html")
print("")

# send launch request for brickly app to launcher
path = os.path.join("user", os.path.basename(os.path.dirname(os.path.realpath(__file__))))
launcher_cmd("launch " + os.path.join(path, "brickly_app.py"))
