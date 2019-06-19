#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# helper module for webinterface
# -*- coding: utf-8 -*-
#


import sys

def htmlDecode(str):
    return str.replace("&quot;", '"').replace("&#39;", "'").replace("&lt;", '<').replace("&gt;", '>').replace("&amp;", '&');

def htmlEncode(str):
    return str.replace('&', "&amp;").replace('"', "&quot;").replace("'", "&#39;").replace('<', "&lt;").replace('>', "&gt;");

def htmlhead(progname:str, headtext:str):
    print('Content-Type: text/html')
    print('')
    print('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
    print('<html xmlns="http://www.w3.org/1999/xhtml">')
    print('<head>')
    print('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />')
    print('<meta http-equiv="cache-control" content="max-age=0" />')
    print('<meta http-equiv="cache-control" content="no-cache" />')
    print('<meta http-equiv="expires" content="0" />')
    print('<meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />')
    print('<meta http-equiv="pragma" content="no-cache" />')
    print('<title>')
    print(progname)
    print('</title>')
    print('<link rel="stylesheet" href="/txt.css" />')
    print('<link rel="icon" href="/favicon.ico" type="image/x-icon" />')
    print('</head>')
    print('<body>')  
    print('<center>')
    print('<h1><div class="outline"><font color="red">fischer</font><font color="#046ab4">technik</font>&nbsp;<font color="#fcce04">TXT</font></div></h1>')    
    print('<p/><h1>')
    print(progname)
    print('</h1><p/>')
    print(headtext)
    print('<br>')

def htmlfoot(message:str, footlink:str, footlinktext:str):
    print('<p/>' + message)
    print('<p/><a href="' + footlink + '">' + footlinktext + "</a>")
    print("</body></html>")
    
def separator():
    print("</p><hr></p>")
    
def lf(num:int=1):
    for a in range(0,num):
        print("<br>")

def text(string:str):
    #print(" "+string+" ")
    print(string)
    
def link(text:str, address:str, tags:str=""):
    print('<a href="'+address+'" '+tags+'>'+text+'</a>')
    
