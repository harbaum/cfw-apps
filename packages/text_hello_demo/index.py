#!/usr/bin/python3
# -*- coding: utf-8 -*-

import htmlhelper as hth
import cgi, os, json, sys

# local files to be ignored when searching for python files
IGNORE = [ "htmlhelper.py", "index.py", "textwrapper.py" ]

def mainpage():
    hth.htmlhead("Python upload", "Upload a new python script")
    hth.lf(1)
    print('<img src="icon.png">')
    hth.lf(1)
    hth.separator()
    hth.lf(1)

    print('Currently installed:<br>')
    files = [f for f in os.listdir(".") if os.path.isfile(f)]
    for f in files:
        # file must not be this script itself
        if f.endswith(".py") and not f in IGNORE:
            print(f + "<br>")
    
    print('<br>Upload new python script:<br><br>')
    print('<form action="index.py" method="post" enctype="multipart/form-data">')
    print('<label>')
    hth.text("Python file:")         
    print('<input name="project" type="file" size="50" accept="application/x-python,application/python"> </label>')
    print('<button type="submit">')
    hth.text("Upload!")
    print('</button></form>')
    
    hth.lf(1)  
    hth.separator()
    hth.htmlfoot("","/","TXT Home")

def uploader(fileitem):
    
    filename = fileitem.filename    

    if filename in IGNORE:
        hth.htmlhead("Python upload", "Upload failed: <b>Filename not allowed!</b>")
        hth.htmlfoot("","index.py","Back")
    else:
        try:
            # remove previously installed file
            prev = [ ]
            files = [f for f in os.listdir(".") if os.path.isfile(f)]
            for f in files:
                # file must not be this script itself
                if f.endswith(".py") and not f in IGNORE:
                    prev.append(f)

            for f in prev:
                os.remove(f)
                    
            # and save the new one
            open(filename, 'wb').write(fileitem.file.read())
            os.chmod(filename,0o666)
            hth.htmlhead("Python upload", "Upload finished!")
            print("Removed previously installed files:<br>", prev)
            hth.htmlfoot("","index.py","Back")
        except:
            hth.htmlhead("Python upload", "Upload failed: <b>File write error!</b>")
            hth.htmlfoot("","index.py","Back")

        
# *****************************************************
# *************** Ab hier geht's los ******************
# *****************************************************

if __name__ == "__main__":
    
    form = cgi.FieldStorage()

    if "project" in form:
        uploader(form["project"])

    else:
        mainpage()
    
    
