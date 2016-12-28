var Code = {};
Code.workspace = null;
Code.Msg = {};
Code.speed = 90;        // 90% default speed
Code.Level = 2;         // GUI level: 1 = beginner, 10 = expert

function init() {
    // do various global initialization
    Blockly.Blocks.logic.HUE = 43;      // TXT orange
    Blockly.Blocks.texts.HUE = 350;       // red
    //Blockly.Blocks.colour.HUE = 20;
    //Blockly.Blocks.lists.HUE = 260;
    //Blockly.Blocks.logic.HUE = 210;
    //Blockly.Blocks.loops.HUE = 120;
    Blockly.Blocks.math.HUE = 240;
    //Blockly.Blocks.procedures.HUE = 290;
    //Blockly.Blocks.variables.HUE = 330;

    Blockly.HSV_SATURATION = 0.7;   // global saturation
    Blockly.HSV_VALUE = 0.6;        // global brightness

    // enable/disable the speed control
    if(Code.Level > 1) {
	document.getElementById("speed_range").value = Code.speed;
    } else {
	document.getElementById("speed").style.display = "none";
    }

    // Interpolate translated messages into toolbox.
    var toolboxText = document.getElementById('toolbox').outerHTML;
    toolboxText = toolboxText.replace(/{(\w+)}/g,
				      function(m, p1) {return MSG[p1]});

    // enable/disable parts of toolbox with respect to current
    // level
    // ToDo

    var toolboxXml = Blockly.Xml.textToDom(toolboxText);
    Code.workspace = Blockly.inject('blocklyDiv',
				    { media: 'media/', 
				      toolbox: toolboxXml } );
    
    custom_blocks_init();
    button_set_state(true, true);
    display_state(MSG['stateDisconnected']);
    loadCode("./brickly.xml");

    window.addEventListener('resize', onresize, false);
    onresize();
}

function speed_change(value) {
    Code.speed = value;
    if (typeof Code.ws !== 'undefined') 
	Code.ws.send(JSON.stringify( { speed: Code.speed } ));
}

function get_lang(current) {
  var val = location.search.match(new RegExp('[?&]lang=([^&]+)'));
  return val ? decodeURIComponent(val[1].replace(/\+/g, '%20')) : current;
};

function set_lang(newLang) {
    var search = window.location.search;
    if (search.length <= 1) {
	search = '?lang=' + newLang;
    } else if (search.match(/[?&]lang=[^&]*/)) {
	search = search.replace(/([?&]lang=)[^&]*/, '$1' + newLang);
    } else {
	search = search.replace(/\?/, '?lang=' + newLang + '&');
    }
    
    window.location = window.location.protocol + '//' +
	window.location.host + window.location.pathname + search;
}

function display_state(str) {
    document.getElementById("stateDiv").innerHTML = str;
}

// switch between "Run..." and "Stop!" button
function button_set_state(enable, run) {
    but = document.getElementById("button");
    but.disabled = !enable;
    if(enable) {
        if(run) {
            but.innerHTML = MSG['buttonRun'];
            but.onclick = runCode;
        } else {
            but.innerHTML = MSG['buttonStop'];
            but.onclick = stopCode;
        }
    }
}

// htmlize text received from the code before it's being
// put into a text output
function html_escape(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;') 
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// display some text output by the code
function display_text(str) {
    var objDiv = document.getElementById("textDiv");
    objDiv.innerHTML += str.replace(/\n/g,'<br />');
    objDiv.scrollTop = objDiv.scrollHeight;
}

// clear the text area
function display_text_clr() {
    document.getElementById("textDiv").innerHTML = "";
}

// start the websocket server
function ws_start(initial) {
    url = "ws://"+document.location.hostname+":9002/";
    
    Code.ws = new WebSocket(url);
    Code.connected = false;
    
    Code.ws.onmessage = function(evt) {
	// ignore empty messages (which we use to force waiting for client)
	if(evt.data.length) {
            // the message is json encoded
            obj = JSON.parse(evt.data);
            if(obj.stdout) display_text("<tt><b>"+html_escape(obj.stdout)+"</b></tt>");
            if(obj.stderr) display_text("<font color='red'><tt><b>"+
					    html_escape(obj.stderr)+"</b></tt></font>");
	    if(obj.highlight) {
		if(obj.highlight == "none") {
		    display_state(MSG['stateProgramEnded']);
		    Code.workspace.highlightBlock();
		} else
		    Code.workspace.highlightBlock(obj.highlight);
	    }
	}
    };
    
    Code.ws.onopen = function(evt) {
	Code.spinner.stop();
        Code.connected = true;
        display_state(MSG['stateConnected']);
        button_set_state(true, false);

	// send initial speed
	Code.ws.send(JSON.stringify( { speed: Code.speed } ));
    };
    
    Code.ws.onerror = function(evt) {
    };
    
    Code.ws.onclose = function(evt) {
        // retry if we never were successfully connected
        if(!Code.connected) {
            //try to reconnect in 10ms
           setTimeout(function(){ws_start(false)}, 10);
        } else {
            display_state(MSG['stateDisconnected']);
            Code.connected = false;
            button_set_state(true, true);
	    Code.workspace.highlightBlock();
	    delete Code.ws;
        }
    };
};

function stopCode() {
    var objDiv = document.getElementById("textArea");
    Code.spinner = new Spinner({top:"0%", position:"relative", color: '#fff'}).spin(objDiv)
    button_set_state(false, false);

    var http = new XMLHttpRequest();
    http.open("GET", "./brickly_stop.py?pid="+pid);
    http.setRequestHeader("Content-type", "text/html");
    http.onreadystatechange = function() {
        if (http.readyState == XMLHttpRequest.DONE) {
	    Code.spinner.stop();
	    
            if (http.status != 200) {
		alert("Error " + http.status + "\n" + http.statusText);
            } else {

            }
        }
    }
    http.send();
}

function loadCode(name) {
    var http = new XMLHttpRequest();
    http.open("GET", name + "?random="+new Date().getTime());
    http.setRequestHeader("Content-type", "application/xml");
    http.onreadystatechange = function() {
        if (http.readyState == XMLHttpRequest.DONE) {
            if (http.status != 200) {
		if (name != "default.xml") {
		    loadCode("./default.xml");
		}
            } else {
		var xml = Blockly.Xml.textToDom(http.responseText);

		// try to find settings in dom
		for (var i = 0; i < xml.childNodes.length; i++) {
		    var xmlChild = xml.childNodes[i];
		    var name = xmlChild.nodeName.toLowerCase();
		    if (name == 'settings') {
			var speed = parseInt(xmlChild.getAttribute('speed'), NaN);
			if((speed >= 0) && (speed <= 100)) {
			    Code.speed = speed
			    document.getElementById("speed_range").value = Code.speed;
			}
		    }
		}
		Blockly.Xml.domToWorkspace(xml, Code.workspace);
            }
        }
    }
    http.send();
}

function runCode() {
    // add highlight information to the code. Make it commented so the code
    // will run on any python setup. If highlighting is wanted these lines
    // need to be uncommented on server side
    Blockly.Python.STATEMENT_PREFIX = '# highlightBlock(%1)\n';
    Blockly.Python.addReservedWords('wrapper');

    // Generate Python code and POST it
    var code = Blockly.Python.workspaceToCode(Code.workspace);

    // there may be no code at all, this is still valid. Mabe we can do something more
    // useful in this case
    if(code == "") {
	// simply do nothing by now. In the future perhaps ask to reload
	// the default code
    } else {
	// preprend current speed settings
	code = "# speed = " + Code.speed.toString() + "\n" + code;

	var objDiv = document.getElementById("textArea");
	Code.spinner = new Spinner({top:"0%", position:"relative", color: '#fff'}).spin(objDiv)

	// prepare gui for running program
	display_text_clr();
	button_set_state(false, true);
        display_state(MSG['stateConnecting']);

	// generate xml and post it with the python code
	var xml = Blockly.Xml.workspaceToDom(Code.workspace);

	// insert settings (speed) into xml
	var settings = goog.dom.createDom('settings');
	settings.setAttribute('speed', Code.speed);
	xml.appendChild(settings)
	
	var text = Blockly.Xml.domToText(xml);

	var http = new XMLHttpRequest();
	http.open("POST", "./brickly_run.py");
	http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	http.onreadystatechange = function() {
            if (http.readyState == XMLHttpRequest.DONE) {
		if (http.status != 200) {
		    alert("Error " + http.status + "\n" + http.statusText);
		} else {
		    // try to find PID ...
		    pid = JSON.parse(http.responseText).pid;
		    
		    // finally connect to the server
		    setTimeout(function(){ws_start(true)}, 500);
		}
            }
	}
	
	// POST python as well as xml
	http.send('code='+encodeURIComponent(code)+
		  '&text='+encodeURIComponent(text)+
		  '&lang='+lang);
	}
}

function resizeTo(element_name, target_name) {
    var element = document.getElementById(element_name);
    var target = document.getElementById(target_name);

    // Compute the absolute coordinates and dimensions of source
    var r_element = element;
    var x = 0;
    var y = 0;
    do {
        x += element.offsetLeft;
        y += element.offsetTop;
        element = element.offsetParent;
    } while (element);

    // Position blocklyDiv over blocklyArea.
    target.style.left = x + 'px';
    target.style.top = y + 'px';
    target.style.width = r_element.offsetWidth + 'px';
    target.style.height = r_element.offsetHeight + 'px';
}

// Returns a function, that, as long as it continues to be invoked, will not
// be triggered. The function will be called after it stops being called for
// N milliseconds. If `immediate` is passed, trigger the function on the
// leading edge, instead of the trailing.
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
	var context = this, args = arguments;
	var later = function() {
	    timeout = null;
	    if (!immediate) func.apply(context, args);
	};
	var callNow = immediate && !timeout;
	clearTimeout(timeout);
	timeout = setTimeout(later, wait);
	if (callNow) func.apply(context, args);
    };
};

var onresize = debounce(function() {
    resizeTo('blocklyArea', 'blocklyDiv');
    resizeTo('textArea', 'textDiv');
    Blockly.svgResize(Code.workspace);
}, 100);

// language may not be set by now. Use english as default then
if (typeof lang === 'undefined') { lang = 'en'; }
// try to override from url
lang = get_lang(lang);

document.head.parentElement.setAttribute('lang', lang);
document.write('<script src="blockly/' + lang + '.js"></script>\n');
document.write('<script src="' + lang + '.js"></script>\n');
window.addEventListener('load', init);
