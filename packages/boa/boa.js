// boa.js

"use strict";

var Boa = {};

function outputText_str(text) {
    var i = document.getElementById("interactive")
    i.value += text;
}

function outputText_bs() {
    var i = document.getElementById("interactive")
    i.value = i.value.slice(0, -1);
}

// output a text. honour backspace and ignore bell
function outputText(text) {
    var pstr = "";
    for (var i = 0, len = text.length; i < len; i++) {
	var c = text[i];
	if("\b\x07".indexOf(c) >= 0) {
	    if(pstr != "") {
		outputText_str(pstr);
		pstr = "";
	    }
	    
	    if(c == '\b')
		outputText_bs();
	} else {
	    pstr += c;
	}
    }

    if(pstr != "")
	outputText_str(pstr);
    
    var i = document.getElementById("interactive")
    i.scrollTop = i.scrollHeight;
}

function interactive_init() {
    document.getElementById("interactive").value = "";
}

function run() {
    // fetch program code from editor and send to app
    Boa.target.ws.send(JSON.stringify( { "code": Boa.editor.getValue() } ));
}

function keyPress( event ) {
    event.preventDefault();  // suppress immediate display
    Boa.target.ws.send(JSON.stringify( { "key": String.fromCharCode(event.which) } ));
}

function paste( event ) {
    // stop data from actually being pasted
    event.stopPropagation();
    event.preventDefault();

    // get pasted data via clipboard API
    var clipboardData = event.clipboardData || window.clipboardData;
    var pastedData = clipboardData.getData('Text');

    // send data as if it has been typed
    Boa.target.ws.send(JSON.stringify( { "key": pastedData } ));
}

// connect to launcher and tell it to launch the app
function target_launch_app() {
    var http = new XMLHttpRequest();
    http.open("GET", "./boa_launch.py");
    http.onreadystatechange = function() {
	if (http.readyState == XMLHttpRequest.DONE) {
	    if (http.status != 200) {
		alert("target_launch_app()\nError " + http.status + "\n" + http.statusText);
	    } else
		// app has been launched.
		// try to connect
		target_connect(false);
	    }
    }
    http.send();
}

// setup the connection to the target
function target_connect(initial) {
    // try to connect to target via websocket
    var url = "ws://"+document.location.hostname+":9004/";
    Boa.target = { }
    Boa.target.ws = new WebSocket(url);
    Boa.target.connected = false;
    
    Boa.target.ws.onmessage = function(evt) {
	// ignore empty messages
	if(evt.data.length) {
	    // console.log("WS MSG:" + evt.data)

            // the message is json encoded
            var obj = JSON.parse(evt.data);

	    if(typeof obj.stdout !== 'undefined') 
		outputText(obj.stdout);
	    
	    if(typeof obj.stderr !== 'undefined') 
		outputText(obj.stderr);

	    if(typeof obj.code !== 'undefined')
		Boa.editor.setValue(obj.code);
	}
    };
    
    Boa.target.ws.onopen = function(evt) {
	// update GUI to reflect the connected state
        Boa.target.connected = true;
    };
    
    Boa.target.ws.onerror = function(evt) {
    };
    
    Boa.target.ws.onclose = function(evt) {
        // retry if we never were successfully connected
        if(!Boa.target.connected) {
            //try to reconnect in 10ms
	    if(!initial) {
		setTimeout(function(){ target_connect(false) }, 100);
	    } else {
		// try to launch target app
		target_launch_app();
	    }
        } else {
	    // connection lost
            Boa.target.connected = false;
	    delete Boa.target.ws;
        }
    };
}; 

function target_init() {
    interactive_init();    
    target_connect(true);
}

// initialize the codemirror editor
function codemirror_init() {
    Boa.editor = CodeMirror.fromTextArea(document.getElementById("code"), {
	mode: { name: "python",
		version: 3,
		singleLineStringErrors: false},
	lineNumbers: true,
	indentUnit: 4,
	matchBrackets: true
    });
}

// initialize the novnc viewer
function vnc_init() {
    // Load supporting scripts
    WebUtil.load_scripts({
	'vnc': ["base64.js", "websock.js", "des.js", "input/keysymdef.js",
		 "input/xtscancodes.js", "input/util.js", "input/devices.js",
		 "display.js", "inflator.js", "rfb.js", "input/keysym.js"]});
    
    function FBUComplete(rfb, fbu) {
	rfb.set_onFBUComplete(function() { });
    }
    
    function updateState(rfb, state, oldstate) {
    }
    
    function disconnected(rfb, reason) {
    }
    
    function notification(rfb, msg, level, options) {
    }
    
    window.onscriptsload = function () {
	WebUtil.init_logging(WebUtil.getConfigVar('logging', 'warn'));
    
	try {
            Boa.rfb = new RFB({'target':       document.getElementById('noVNC_canvas'),
			       'encrypt':      false,
			       'true_color':   true,   // nedded for the background gradient
			       'local_cursor': true,
			       'shared':       WebUtil.getConfigVar('shared', true),
			       'view_only':    false,
			       'mouse_only':   true,
			       'onNotification':  notification,
			       'onUpdateState':  updateState,
			       'onDisconnected': disconnected,
			       'onFBUComplete': FBUComplete});
	} catch (exc) {
            status('Unable to create RFB client -- ' + exc, 'error');
            return; // don't continue trying to connect
	}
	
	Boa.rfb.connect(window.location.hostname, 6080, null, null);
    };
}

function init() {
    vnc_init();
    codemirror_init();
    target_init();
}
    
window.addEventListener('load', init);
