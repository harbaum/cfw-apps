// Brickly specifc javascript code

var Code = {};
var USER_FILES = "user/"
Code.workspace = null;
Code.Msg = {};
Code.speed = 90;                                     // 90% default speed
Code.skill = 1;                                      // GUI level: 1 = beginner ... expert
Code.program_name = [ "brickly-0.xml", "Brickly" ];  // default file name and program name
Code.connected = false;
Code.spinner = null;
Code.files = [ ]

/* When the user clicks on the button, */
/* toggle between hiding and showing the dropdown content */
function menu_show() {
    document.getElementById("dropdown_content").classList.toggle("show");
}

function menu_close() {
    document.getElementById("dropdown_content").classList.remove("show");
}

function menu_disable(disabled) {
    if(disabled) {
	document.getElementById("dropdown_button").classList.add("not-active");
	menu_close();
    } else
	document.getElementById("dropdown_button").classList.remove("not-active");
}

// check if a program with that filename exists
function file_exists(a) {
    for(var i = 0; i < Code.files.length; i++) 
	if(Code.files[i][0] == a) return true;

    return false;
}

// check if a program with that name exists
function name_exists(a) {
    for(var i = 0; i < Code.files.length; i++) 
	if(Code.files[i][1] == a) return true;

    return false;
}

// make sure the user doesn't use html tags in the program name
function htmlEscape(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function htmlDecode(str){
    return str
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&');
}

/* construct the main menu */
function menu_update() {
    document.getElementById("dropdown_new").innerHTML = MSG['dropdown_new'];
    menu_disable(false);
    menu_append_files(Code.files);
    menu_text_edit();                    // enable/disable "new" button as required
}

function menu_text_edit() {
    // check for current text and disable new button if such a name
    // already exists
    var name = htmlEscape(document.getElementById("dropdown_text").value);

    document.getElementById("dropdown_new").disabled = 
	(name_exists(name) || name == "");
}

function workspace_start() {
    // create a new program
    Blockly.Events.disable();
    Code.workspace.clear();
    Blockly.Events.enable();

    document.title = "Brickly: " + htmlDecode(Code.program_name[1]); 

    // an empty workspace with only the start bloick
    xml_text = '<xml xmlns="http://www.w3.org/1999/xhtml"><block type="start" id="' + 
	Blockly.utils.genUid()+'" x="10" y="20"></block></xml>'

    // alternally use this to add the start block:
    // Code.workspace.addTopBlock()

    // add the "start" block
    xml = Blockly.Xml.textToDom(xml_text);
    Blockly.Xml.domToWorkspace(xml, Code.workspace);

    // center if scrolling is enabled
    Code.workspace.scrollCenter();
}

function menu_file_new() {
    // now find an unused file name in the list
    var fname = null;
    for(var i = 0; i < 64; i++) {
	var tmp = "brickly-" + i + ".xml";
	if(!file_exists(tmp)) {
	    fname = tmp;
	    break;
	}
    }

    // TODO: prevent this from happening by disabling the new button
    // after 64 files
    if(!fname) {
	alert("Too many files!");
	return;
    }

    // fname is now a valid and unused filename
 
    Code.program_name = [ fname, htmlEscape(document.getElementById("dropdown_text").value) ];

    // create a new program
    workspace_start();

    menu_update();
}

function menu_file_load(fname, name) {
    Code.program_name = [ fname, htmlEscape(name) ]; // set the new file name
    document.title = "Brickly: " + htmlDecode(Code.program_name[1]);
    menu_update();                           // redo menu to highlight the newly loaded file
    program_load(USER_FILES + fname);        // and finally load the file

    // save on TXT that this is now the program
    Code.ws.send(JSON.stringify( { program_name: Code.program_name } ));
    Code.ws.send(JSON.stringify( { command: "save_settings" } ));

    // request new list as the previously active program may have been deleted
    Code.ws.send(JSON.stringify( { command: "list_program_files" } ));
}

function menu_create_entry(a) {
    var cl = ""
    var ar = ""

    if(a[0] == Code.program_name[0]) 
	// if this entry is for the current program then make it inactive and hightlight it
	cl = 'class="dropdown_selected dropdown_not_active" '
    else
	// othewise make it trigger an event
	ar = 'onclick="menu_file_load(\'' + a[0] + '\',\'' + a[1] + '\')"'

    // make sure name doesn't wrap
    var name = a[1].replace(/ /g, '&nbsp;');
    return '<td align="center"><a ' +  cl + ar + '>' + name + "</a></td>";
}

/* add files to the menu */
function menu_append_files(f) {
    var loc_f = f;

    content_files = document.getElementById("dropdown_content_files");

    // check if current file exists in list and
    // append it if not. Thus programs not yet saved in TXT side
    // will show up in the menu
    if(!file_exists(Code.program_name[0]))
	loc_f.push(Code.program_name)
    
    // determine number of columns for a square setup
    cols = Math.floor(1+Math.sqrt(loc_f.length-1));
    // limit number of columns
    // if(cols > 3) cols = 3;

    // remove all existing files
    rows = Math.floor(((loc_f.length-1)/cols)+1)

    var i;
    var new_content_files = "";

    // the files come as an array of arrays
    for(i = 0; i < loc_f.length; i++) {
	// first column?
	if((i % cols) == 0) new_content_files += "<tr>";
	    
	new_content_files += menu_create_entry(loc_f[i]);

	if((i % cols) == (cols-1)) new_content_files += "</tr>";
    }

    // fill up last row
    for( ; i < cols*rows; i++) {
	if((i % cols) == 0) new_content_files += "<tr>";
	new_content_files += "<td></td>";
	if((i % cols) == (cols-1)) new_content_files += "</tr>";
    }

    content_files.innerHTML = new_content_files;
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
    if(!event.target.classList.contains('dropdown-keep-open')) 
	menu_close();
}

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

    Blockly.BlockSvg.START_HAT = true;
    
    // enable/disable the speed control
    if(Code.skill > 1)	document.getElementById("speed_range").value = Code.speed;
    else                document.getElementById("speed").style.display = "none";

    // below skill level 3 hide the menu
    if(Code.skill <= 2) document.getElementById("dropdown").style.display = "none";    

    // initially disable the dropdown menu
    menu_disable(true);

    custom_blocks_init();

    // load the toolbox xml
    loadToolbox(Code.skill);
}

function loadToolbox(skill_level) {
    var toolbox_name = "toolbox";
    if(skill_level) toolbox_name += "-" + skill_level.toString();

    var http = new XMLHttpRequest();
    http.open("GET", toolbox_name+".xml?random="+new Date().getTime());
    http.setRequestHeader("Content-type", "application/xml");
    http.onreadystatechange = function() {
        if (http.readyState == XMLHttpRequest.DONE) {
            if (http.status == 200)
		toolbox_install(http.responseText);
	    else if(skill_level)
		loadToolbox();
	}
    }
    http.send();
}

function onWorkspaceCleared(event) {
    // a program is deleted by deleting the stack with the start block
    // on top. This only works if the TXT is connected
    if((event.type == Blockly.Events.DELETE) &&
       (event.oldXml.getAttribute("type") == "start")) {

	if(!Code.connected || (!confirm(MSG['confirm_delete'].replace("%1", 
                  htmlDecode(Code.program_name[1]))))) {

	    // undo delete
	    Code.workspace.undo(false);

	    // the workspace jumps around when doing this. so recenter ...
	    Code.workspace.scrollCenter();

	    if(!Code.connected)
		alert(MSG['delete_not_connected'])

	    return;
	}
	
	// make sure the current program is set on TXT side ...
	Code.ws.send(JSON.stringify( { program_name: Code.program_name } ));
	
	// ... then delete it ...
	Code.ws.send(JSON.stringify( { command: "delete" } ));
	
	// ... and finally update file list
	Code.ws.send(JSON.stringify( { command: "list_program_files" } ));
	
	// disable the run button
	button_run_enable(false);

	workspace_start();
    }
    
    // enable the run button once the first block has been added
    if((event.type == Blockly.Events.CREATE) &&
       (Code.workspace.getAllBlocks().length >= 1))
	button_run_enable(true);
}
    
function toolbox_install(toolboxText) {
    // Interpolate translated messages into toolbox.
    toolboxText = toolboxText.replace(/{(\w+)}/g,
				      function(m, p1) {return MSG[p1]});

    set_skill_tooltips();

    var toolbox = Blockly.Xml.textToDom(toolboxText);
    Code.workspace = Blockly.inject('blocklyDiv',
				    { media: 'blockly/media/',
				      toolbox: toolbox,
				      // scrollbars: false,  // 
				      zoom: { // controls: true,
					  wheel: true,
					  // startScale: 1.0,
					  maxScale: 2,
					  minScale: 0.5,
					  scaleSpeed: 2
				      }
				    } );

    // disable and enable run button depending on workspace being used
    // and delete program if all blocks are deleted
    Code.workspace.addChangeListener(onWorkspaceCleared);

    // don't allow orphaned stacks
    Code.workspace.addChangeListener(Blockly.Events.disableOrphans);
    
    button_set_state(true, true);
    display_state(MSG['stateDisconnected']);

    // fixme: this must not happen before screen resizing is done
    setTimeout(function() { program_load( USER_FILES + Code.program_name[0] ) }, 100);
    
    window.addEventListener('resize', onresize, false);
    onresize();
	
    // try to connect web socket right away
    ws_start(true);
}

function set_skill_tooltips() {
    for (var i = 1; i <= 5; i++) { 
	var obj = document.getElementById("skill-"+i.toString());
	obj.title = MSG['skillToolTip'].replace('%1',MSG['skill'+i.toString()]);
	if(i==Code.skill) obj.setAttribute("data-selected", "true");
    }
}

function speed_change(value) {
    Code.speed = value;
    if (typeof Code.ws !== 'undefined') 
	Code.ws.send(JSON.stringify( { speed: Code.speed } ));
}

function get_parm(name, current) {
  var val = location.search.match(new RegExp('[?&]'+name+'=([^&]+)'));
  return val ? decodeURIComponent(val[1].replace(/\+/g, '%20')) : current;
}
    
function set_parm(name, newVal, curVal) {
    // don't do anything if the value hasn't changed
    if(newVal != curVal) {
	var search = window.location.search;

	if (search.length <= 1) {
	    search = '?'+name+'=' + newVal;
	} else if (search.match(new RegExp('[?&]'+name+'=[^&]*'))) {
	    search = search.replace(new RegExp('([?&]'+name+'=)[^&]*'), '$1'+newVal);
	} else {
	    search = search.replace(/\?/, '?'+name+'='+newVal+'&');
	}
    
	window.location = window.location.protocol + '//' +
	    window.location.host + window.location.pathname + search;
    }
}

function display_state(str) {
    document.getElementById("stateDiv").innerHTML = str;
}

// the run button may only be enabled if there's at least
// none block in the workspace
function button_run_enable(enable) {
    // if button is in "run" mode enable and disable
    // it immediately
    but = document.getElementById("button");
    but.run_enabled = enable;

    // if the button is currently in "run mode" (and not "stopp")
    // then disable and enable it immediately
    if(but.run_mode)
	but.disabled = !enable;
}

// switch between "Run..." and "Stop!" button
function button_set_state(enable, run) {
    but = document.getElementById("button");
    but.disabled = !enable;
    but.run_mode = run;
    if(run) {
        but.innerHTML = MSG['buttonRun'];
        but.onclick = program_run;

	// if run is not enabled (workspace is empty)
	// then keep button disabled
	if(enable && !but.run_enabled)
	    but.disabled = true;
    } else {
        but.innerHTML = MSG['buttonStop'];
        but.onclick = program_stop;
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
	// ignore empty messages
	if(evt.data.length) {
	    // console.log("MSG:" + evt.data)

            // the message is json encoded
            obj = JSON.parse(evt.data);

	    // handle the various json values

	    // commands from client
	    if(typeof obj.gui_cmd !== 'undefined') {
		if(obj.gui_cmd == "clear") display_text_clr();
		if(obj.gui_cmd == "run") {
		    display_state(MSG['stateRunning']);
		    button_set_state(true, false);
		}
	    }

	    if(typeof obj.program_files !== 'undefined') {
		Code.files = obj.program_files;
		menu_update();
	    }

	    if(typeof obj.running !== 'undefined') {
		if(obj.running) {
		    // client informs us after a connect that there's code being
		    // executed
		    display_state(MSG['stateRunning']);
		    button_set_state(true, false);		
		}
	    }

            if(typeof obj.stdout !== 'undefined') 
		display_text("<tt><b>"+html_escape(obj.stdout)+"</b></tt>");

            if(typeof obj.stderr !== 'undefined')
		display_text("<font color='red'><tt><b>"+
			     html_escape(obj.stderr)+"</b></tt></font>");

	    if(typeof obj.highlight !== 'undefined') {
		if(obj.highlight == "none") {
		    display_state(MSG['stateProgramEnded']);
		    Code.workspace.highlightBlock();

		    button_set_state(true, true);
		} else
		    Code.workspace.highlightBlock(obj.highlight);
	    }
	}
    };
    
    Code.ws.onopen = function(evt) {
	// update GUI to reflect the connected state
        Code.connected = true;
        button_set_state(true, true);          // initially display an enabled run button
	display_state(MSG['stateConnected']);
	
	// request list of program files stored on TXT
	Code.ws.send(JSON.stringify( { command: "list_program_files" } ));

	// Not the initial probe but a connection initialted by the user? Then run the code ...
	if(!initial)
	    send_and_run_code();
    };
    
    Code.ws.onerror = function(evt) {
    };
    
    Code.ws.onclose = function(evt) {
        // retry if we never were successfully connected
        if(!Code.connected) {
            //try to reconnect in 10ms
	    if(!initial) setTimeout(function(){ ws_start(false) }, 100);
	    // setTimeout(function(){ ws_start(false) }, 100);
        } else {
	    // connection lost
            display_state(MSG['stateDisconnected']);
            Code.connected = false;
            button_set_state(true, true);
	    Code.workspace.highlightBlock();
	    menu_disable(true);
	    delete Code.ws;
        }
    };
};

function program_stop() {
    button_set_state(false, false);
    Code.ws.send(JSON.stringify( { command: "stop" } ));
}

function program_load(name) {
    var http = new XMLHttpRequest();
    http.open("GET",  name + "?random="+new Date().getTime());
    http.setRequestHeader("Content-type", "application/xml");
    http.onreadystatechange = function() {
        if (http.readyState == XMLHttpRequest.DONE) {
	    // clearing the workspace should not trigger any "really delete?"
	    // request 
	    Blockly.Events.disable();
	    Code.workspace.clear();
	    Blockly.Events.enable();

            if (http.status == 200) {
		var min_x = Number.POSITIVE_INFINITY;
		var min_y = Number.POSITIVE_INFINITY;

		var start_found = false;
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

		    // change the origin of the root blocks
		    // find the minimum x and y coordinates used
		    if (name == 'block') {
			// does this program already have a "start" block?
			if(xmlChild.getAttribute('type') == "start")
			    start_found = true;
			
			if(min_x > parseInt(xmlChild.getAttribute('x')))  
			    min_x = parseInt(xmlChild.getAttribute('x'));
			if(min_y > parseInt(xmlChild.getAttribute('y')))
			    min_y = parseInt(xmlChild.getAttribute('y'));
		    }
		}

		// make sure top/left corner is at (10,10)
		for (var i = 0; i < xml.childNodes.length; i++) {
		    var xmlChild = xml.childNodes[i];
		    var name = xmlChild.nodeName.toLowerCase();
		    if (name == 'block') {
			xmlChild.setAttribute('x', parseInt(xmlChild.getAttribute('x')) - min_x + 10);
			xmlChild.setAttribute('y', parseInt(xmlChild.getAttribute('y')) - min_y + 20);
		    }
		}

		// --- make sure there's a start element as introduced with version 1.19 ---
		if(!start_found) {
		    // once more walk over all root nodes
		    for (var i = 0; i < xml.childNodes.length; i++) {
			var xmlChild = xml.childNodes[i];
			var name = xmlChild.nodeName.toLowerCase();

			if (name == 'block') {
			    // get type. The types of procedures all begin with procedures_
			    type = xmlChild.getAttribute('type').split('_')[0];
			    if(type != "procedures") {
				// insert a start block
				var start_block = goog.dom.createDom('block');
				start_block.setAttribute('type', 'start');
				start_block.setAttribute('id', Blockly.utils.genUid());

				// use position of block we are going to "swallow"
				start_block.setAttribute('x', xmlChild.getAttribute('x'));
				start_block.setAttribute('y', xmlChild.getAttribute('y'));
				
				xml.appendChild(start_block);

				// remove old block from root
				xml.removeChild(xmlChild);
				// remove old blocks coordinates 
				xmlChild.removeAttribute('x');
				xmlChild.removeAttribute('y');
				
				// create a new next block
				var next = goog.dom.createDom('next');
				start_block.appendChild(next);

				// and append it to the next element of the new start block
				next.appendChild(xmlChild);

				break;
			    }
			}
		    }
		}
		
		Blockly.Xml.domToWorkspace(xml, Code.workspace);
            } else {
		// could not load program. Make sure the
		// default start block is there
		workspace_start();
	    }

	    // center if scrolling is enabled
	    Code.workspace.scrollCenter();
        }
    }
    http.send();
}

/* ------------------------- busy spinner of top of the text window --------------------------*/
/* the spinner is shown when the app is being launched as this takes some time */
function spinner_start() {
    if(!Code.spinner) {
	var objDiv = document.getElementById("textArea");
	Code.spinner = new Spinner({top:"0%", position:"relative", color: '#fff'}).spin(objDiv)
    }
}

function spinner_stop() {
    if(Code.spinner) {
	Code.spinner.stop();
	Code.spinner = null;
    }
}

function send_and_run_code() {
    // Generate Python code and POST it
    var python_code = Blockly.Python.workspaceToCode(Code.workspace);

    // preprend current speed settings
    python_code = "# speed = " + Code.speed.toString() + "\n" + python_code;

    // generate xml and post it with the python code
    var blockly_dom = Blockly.Xml.workspaceToDom(Code.workspace);

    // insert settings (speed) into xml
    var settings = goog.dom.createDom('settings');
    settings.setAttribute('speed', Code.speed);
    settings.setAttribute('name', Code.program_name[1]);
    blockly_dom.appendChild(settings)
	
    var blockly_code = Blockly.Xml.domToText(blockly_dom);

    // set current program name
    Code.ws.send(JSON.stringify( { program_name: Code.program_name } ));

    // send various parameters
    Code.ws.send(JSON.stringify( { speed: Code.speed } ));
    Code.ws.send(JSON.stringify( { skill: Code.skill } ));
    Code.ws.send(JSON.stringify( { lang: Code.lang } ));
    Code.ws.send(JSON.stringify( { command: "save_settings" } ));

    // send python and blockly version fo the current code
    Code.ws.send(JSON.stringify( { python_code: python_code } ));
    Code.ws.send(JSON.stringify( { blockly_code: blockly_code } ));

    // and finally request app to be started
    Code.ws.send(JSON.stringify( { command: "run" } ));

    // enable button and make it a "stop!" button
    button_set_state(true, false);
    spinner_stop();

    // request list of program files stored on TXT as it may have changed
    Code.ws.send(JSON.stringify( { command: "list_program_files" } ));
}
    
function program_run() {
    // add highlight information to the code. Make it commented so the code
    // will run on any python setup. If highlighting is wanted these lines
    // need to be uncommented on server side
    Blockly.Python.STATEMENT_PREFIX = '# highlightBlock(%1)\n';
    Blockly.Python.addReservedWords('wrapper');

    if(Code.connected) {
	send_and_run_code();
    } else {
	// if we aren't connected then we need to start the brickly app on the TXT
	// first. This is done by posting the code
	
	button_set_state(false, true);
        display_state(MSG['stateConnecting']);

	spinner_start();

	var http = new XMLHttpRequest();
	http.open("GET", "./brickly_launch.py");
	// http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	http.onreadystatechange = function() {
	    if (http.readyState == XMLHttpRequest.DONE) {
		if (http.status != 200) 
		    alert("Error " + http.status + "\n" + http.statusText);
		else
		    ws_start(false);
	    }
	}
	http.send();
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
}, 50);

// ----------------- verify settings read from settings.js -----------

// "lang" is set in settings.js
// language may not be set by now. Use english as default then
if (typeof lang === 'undefined') { lang = 'en'; }
// try to override from url
Code.lang = get_parm("lang", lang);

if (typeof skill === 'undefined') { skill = 1; }
// try to override from url
Code.skill = parseInt(get_parm("skill", skill));

// the settings may also contain info about the name of
// the last program used
if((typeof program_name !== 'undefined')&&
   (typeof program_file_name !== 'undefined'))
    Code.program_name = [ program_file_name, program_name ]

document.title = "Brickly: " + htmlDecode(Code.program_name[1]);
document.head.parentElement.setAttribute('lang', Code.lang);
document.head.parentElement.setAttribute('skill', Code.skill);
document.write('<script src="blockly/' + Code.lang + '.js"></script>\n');
document.write('<script src="' + Code.lang + '.js"></script>\n');
window.addEventListener('load', init);
