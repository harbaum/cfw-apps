#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#

import cgi
import sys
import os
import subprocess
import json
import socket
import time

debug = False

form = cgi.FieldStorage()

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

# save xml if present
if "text" in form:
    # write code to file
    with open("brickly.xml", 'w', encoding="utf-8") as f:
        f.write(form["text"].value)
        f.close()

# save language setting if present
if "lang" in form:
    with open("lang.js", 'w') as f:
        f.write("var lang = '" + form["lang"].value + "';\n")
        f.close()

# save and run python code if present
if "code" in form:
    # write code to file
    with open("brickly.py", 'w', encoding="utf-8") as f:
        f.write(form["code"].value)
        f.close()

    # write a valid http reply header
    print("Content-Type: application/json")
    print("")

    # There are two modes of operation: 
    # 1) with a launcher process which can be told to
    #    run a certain program
    # 2) without any helper process. Thus this script forks the
    #    process into the background itself

    if current_executable == None:
        if not debug:
            # execute python program in external process
            wrapper = os.path.join(os.path.dirname(os.path.realpath(__file__)), "brickly_wrapper.py")
            proc = subprocess.Popen([wrapper], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print(json.dumps( { "pid": proc.pid } ))
        else:
            print(json.dumps( { "pid": 123 } ))
    else:
        path = os.path.join("user", os.path.basename(os.path.dirname(os.path.realpath(__file__))))
        launcher_cmd("launch " + os.path.join(path, "brickly_app.py"))
        print(json.dumps( { "pid": 0 } ))
else:
    print("Content-Type: application/json")
    print("")
