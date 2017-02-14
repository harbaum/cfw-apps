// custom block definitions for brickly incl. python code generation
// https://blockly-demo.appspot.com/static/demos/blockfactory/index.html

CustomBlocksHUE = 180
InputBlocksHUE = 200
OutputBlocksHUE = 220
MobileBlocksHUE = 250
TextBlocksHUE = 350

// --------------------------------------------------------

var block_wait = {
    "type": "wait",
    "message0": MSG['blockWaitMessage'],
    "args0": [ { "type": "input_value", "name": "seconds", "check": "Number" } ],
    "inputsInline": true,
    "previousStatement": null,
    "nextStatement": null,
    "colour": CustomBlocksHUE,
    "tooltip": MSG['blockWaitToolTip']
};

var block_repeat = {
    "type": "repeat",
    "message0": MSG['blockRepeatMessage'],
    "args0": [ {
	"type": "input_dummy"
    },{
	"type": "input_statement",
	"name": "STATEMENTS"
    } ],
    "previousStatement": null,
    "colour": Blockly.Blocks.loops.HUE,
    "tooltip": MSG['blockRepeatToolTip']
};

// --------------------------------------------------------
// --------------------- Joystick -------------------------
// --------------------------------------------------------

var block_js_present = {
  "type": "js_present",
  "message0": MSG['blockJsPresentMessage'],
  "output": "Boolean",
  "colour": InputBlocksHUE,
  "tooltip": MSG['blockJsPresetToolTip']
};

Blockly.Python['js_present'] = function(block) {
    code = 'jsIsPresent()';
    return [code, Blockly.Python.ORDER_NONE];
}

var block_js_axis = {
  "type": "js_axis",
  "message0": MSG['blockJsAxisMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "axis",
      "options": [ [ MSG["blockAxisX"],  "x" ],  [ MSG["blockAxisY"],  "y" ],  [ MSG["blockAxisZ"],  "z" ],
		   [ MSG["blockAxisRx"], "rx" ], [ MSG["blockAxisRy"], "ry" ], [ MSG["blockAxisRz"], "rz" ],
		   [ MSG["blockAxisHx"], "hat0x" ], [ MSG["blockAxisHy"], "hat0y" ] 
		 ]
    } ],
  "output": "Number",
  "colour": InputBlocksHUE,
  "tooltip": MSG['blockJsAxisToolTip']
};

Blockly.Python['js_axis'] = function(block) {
    var axis = block.getFieldValue('axis');
    code = 'jsGetAxis("%1")'.replace('%1', axis);
    return [code, Blockly.Python.ORDER_NONE];
}

var block_js_button = {
  "type": "js_button",
  "message0": MSG['blockJsButtonMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "button",
      "options": [ [ MSG["blockButtonTrigger"], "trigger" ], [ MSG["blockButtonThumb"],      "thumb" ], 
		   [ MSG["blockButtonThumb2"],   "thumb2" ], [ MSG["blockButtonTop"],          "top" ], 
		   [ MSG["blockButtonTop2"],       "top2" ], [ MSG["blockButtonPinkieBtn"], "pinkie" ],
		   [ MSG["blockButtonBaseBtn"],    "base" ], [ MSG["blockButtonBaseBtn2"],   "base2" ],
		   [ MSG["blockButtonBaseBtn3"],  "base3" ], [ MSG["blockButtonBaseBtn4"],   "base4" ],
		   [ MSG["blockButtonBaseBtn5"],  "base5" ], [ MSG["blockButtonBaseBtn6"],   "base6" ] ]
    } ],
  "output": "Boolean",
  "colour": InputBlocksHUE,
  "tooltip": MSG['blockJsButtonToolTip']
};

Blockly.Python['js_button'] = function(block) {
    var button = block.getFieldValue('button');
    code = 'jsGetButton("%1")'.replace('%1', button);
    return [code, Blockly.Python.ORDER_NONE];
}

// --------------------------------------------------------

var block_pwm_value = {
  "type": "pwm_value",
  "message0": MSG['blockPwmValueMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "state",
      "options": [ [ "100% ("+MSG['blockOn']+")",  "100" ],
		   [ "90%",  "90"  ],
		   [ "80%",  "80"  ],
		   [ "70%",  "70"  ],
		   [ "60%",  "60"  ],
		   [ "50%",  "50"  ],
		   [ "40%",  "40"  ],
		   [ "30%",  "30"  ],
		   [ "20%",  "20"  ],
		   [ "10%",  "10"  ],
		   [ "0% ("+MSG['blockOff']+")", "0" ] ]
    } ],
  "output": "Number",
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockPwmValueToolTip']
};

var block_on_off = {
  "type": "on_off",
  "message0": MSG['blockOnOffMessage'],
  "args0": [ { 
      "type": "field_dropdown",
      "name": "state", 
      "options": [ [ MSG['blockOn'], "100" ], [ MSG['blockOff'], "0" ] ]
    } ],
  "output": "Number",
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockOnOffToolTip']
};

var block_output = {
  "type": "output",
  "message0": MSG['blockOutputMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "port",
      "options": [
        [ "O1", "0" ], [ "O2", "1" ], [ "O3", "2" ], [ "O4", "3" ],
        [ "O5", "4" ], [ "O6", "5" ], [ "O7", "6" ], [ "O8", "7" ]
      ] },
    {
      "type": "input_value",
      "name": "value",
      "check": "Number"
    }
  ],
  "previousStatement": null,
  "nextStatement": null,
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockOutputToolTip']
}

var block_io_sync = {
    "type": "io_sync",
    "message0": MSG['blockIOSyncMessage'],
    "args0": [ {
	"type": "input_dummy"
    },{
	"type": "input_statement",
	"name": "STATEMENTS"
    } ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": OutputBlocksHUE,
    "tooltip": MSG['blockIOSyncToolTip']
};

var block_mobile_config = {
    "type": "mobile_config",
    "message0": MSG['blockMobileConfigMessage'],
    "args0": [ 
	{ "type": "input_dummy" },
	{ "type": "field_dropdown",
	  "name": "motor_left",
	  "options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ] },
	{ "type": "field_dropdown",
	  "name": "motor_right",
	  "options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ] },
	{ "type": "input_value",
	  "name": "motor_type",
	  "check": "Number" },
	{ "type": "field_number",
	  "name": "gear_ratio_1",
	  "value": 10,
	  "min": 1 },
	{ "type": "field_number",
	  "name": "gear_ratio_2",
	  "value": 20,
	  "min": 1 },
	{ "type": "input_dummy"	},
	{ "type": "field_number",
	  "name": "wheel_diam",
	  "value": 5.8,
	  "min": 1 },
	{ "type": "input_dummy" },
	{ "type": "field_number",
	  "name": "wheel_dist",
	  "value": 15.4,
	  "min": 1
	}
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": MobileBlocksHUE,
    "tooltip": MSG['blockMobileConfigToolTip']
}

var block_mobile_drive = {
    "type": "mobile_drive",
    "message0": MSG['blockMobileDriveMessage'],
    "args0": [ {
	"type": "field_dropdown",
	"name": "dir",
	"options": [ [ MSG['blockForward'], "1" ],
		     [ MSG['blockBackward'], "-1" ] ] 
    }, {
	"type": "input_value",
	"name": "dist",
	"check": "Number"
    } ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": MobileBlocksHUE,
    "tooltip": MSG['blockMobileDriveToolTip']
}

var block_mobile_drive_while = {
    "type": "mobile_drive_while",
    "message0": MSG['blockMobileDriveWhileMessage'],
    "args0": [
	{ "type": "field_dropdown",
	  "name": "dir",
	  "options": [ [ MSG['blockForward'], "1" ],
		       [ MSG['blockBackward'], "-1" ] ] },
	{ "type": "field_dropdown",
	  "name": "while",
	  "options": [ [ MSG['blockWhile'], "True" ],
		       [ MSG['blockUntil'], "False" ] ] },
	{ "type": "input_value",
	  "name": "value",
	  "check": "Boolean"
	}
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": MobileBlocksHUE,
    "tooltip": MSG['blockMobileDriveWhileToolTip']
}

var block_mobile_turn = {
    "type": "mobile_turn",
    "message0": MSG['blockMobileTurnMessage'],
    "args0": [ {
	"type": "field_dropdown",
	"name": "dir",
	"options": [ [ MSG['blockRight'], "1" ],
		     [ MSG['blockLeft'], "-1" ] ] 
    }, {
	"type": "input_value",
	"name": "angle",
	"check": "Number"
    } ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": MobileBlocksHUE,
    "tooltip": MSG['blockMobileTurnToolTip']
}

var block_simple_angle = {
  "type": "simple_angle",
  "message0": MSG['blockAngleMessage'],
  "args0": [ { 
      "type": "field_dropdown",
      "name": "angle", 
      "options": [ [ MSG['blockRot45'],  "45" ],
		   [ MSG['blockRot90'],  "90" ],
		   [ MSG['blockRot135'], "135" ],
		   [ MSG['blockRot180'], "180" ] ]
    } ],
  "output": "Number",
  "colour": MobileBlocksHUE,
  "tooltip": MSG['blockAngleToolTip']
};

var block_angle = {
  "type": "angle",
  "message0": MSG['blockAngleMessage']+"°",
  "args0": [ { 
      "type": "field_angle",
      "name": "angle",
      "angle": 90
    } ],
  "output": "Number",
  "colour": MobileBlocksHUE,
  "tooltip": MSG['blockAngleToolTip']
};

// old motor block
var block_motor = {
  "type": "motor",
  "message0": MSG['blockMotorMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "port",
      "options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ]
  }, {
      "type": "field_dropdown",
      "name": "dir",
      "options": [
          [ MSG['blockLeft'] + ' \u21BA', "-1" ],
	  [ MSG['blockRight'] + ' \u21BB', "1" ]
      ]
  }, {
      "type": "input_value",
      "name": "value",
      "check": "Number"
  }
  ],
  "previousStatement": null,
  "nextStatement": null,
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockMotorToolTip']
}

// old motor block with distance
var block_motor_steps = {
    "type": "motor_steps",
    "message0": MSG['blockMotorStepsMessage'],
    "args0": [ {
	"type": "field_dropdown",
	"name": "port",
	"options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ]
    }, {
  	"type": "field_dropdown",
	"name": "dir",
	"options": [
	    [ MSG['blockLeft'] + ' \u21BA', "-1" ],
	    [ MSG['blockRight'] + ' \u21BB', "1" ] ]
    }, {
	"type": "input_value",
	"name": "value",
	"check": "Number"
    }, {
	"type": "input_value",
	"name": "steps",
	"check": "Number"
    }
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": OutputBlocksHUE,
    "tooltip": MSG['blockMotorStepsToolTip']
}

var block_motor_set = {
  "type": "motor_set",
  "message0": MSG['blockMotorSetMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "port",
      "options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ]
    }, {
  	"type": "field_dropdown",
	"name": "name",
	"options": [
	    [ MSG['blockMotorSetSpeed'], "speed" ],
	    [ MSG['blockMotorSetDir'],   "dir"   ],
	    [ MSG['blockMotorSetDist'],  "dist"  ],
	    [ MSG['blockMotorSetGear'],  "gear"  ]
	]
  }, {
      "type": "input_value",
      "name": "value",
      "check": "Number"
  }
  ],
  "previousStatement": null,
  "nextStatement": null,
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockMotorSetToolTip']
}

var block_motor_sync = {
  "type": "motor_sync",
  "message0": MSG['blockMotorSyncMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "port_a",
      "options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ]
    }, {
      "type": "field_dropdown",
      "name": "port_b",
      "options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ]
    },
  ],
  "previousStatement": null,
  "nextStatement": null,
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockMotorSyncToolTip']
}

var block_left_right = {
  "type": "left_right",
  "message0": MSG['blockLeftRightMessage'],
  "args0": [ { 
      "type": "field_dropdown",
      "name": "dir", 
      "options": [ [ MSG['blockLeft']  + ' \u21BA', "-1" ],
		   [ MSG['blockRight'] + ' \u21BB',  "1" ] ]
    } ],
  "output": "Number",
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockLeftRightToolTip']
};

var block_gear_ratio = {
  "type": "gear_ratio",
  "message0": MSG['blockGearMessage'],
  "args0": [ { 
      "type": "field_dropdown",
      "name": "gear_ratio", 
      "options": [ [ MSG['blockGearTXT'], "63" ],
		   [ MSG['blockGearTX'],  "75" ] ]
    } ],
  "output": "Number",
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockGearToolTip']
};

var block_motor_has_stopped = {
    "type": "motor_has_stopped",
    "message0": MSG['blockMotorHasStoppedMessage'] ,
    "args0": [ {
	"type": "field_dropdown",
	"name": "port",
	"options": [ [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ] ]
    }
  ],
  "output": "Boolean",
  "colour": OutputBlocksHUE,
  "tooltip": MSG['blockMotorHasStoppedToolTip']
}

var block_motor_off = {
    "type": "motor_off",
    "message0": MSG['blockMotorOffMessage'],
    "args0": [ {
	"type": "field_dropdown",
	"name": "port",
	"options": [
            [ "M1", "0" ], [ "M2", "1" ], [ "M3", "2" ], [ "M4", "3" ]
	]
    }, {
	"type": "input_value",
	"name": "value",
	"check": "Number"
    } ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": OutputBlocksHUE,
    "tooltip": MSG['blockMotorOffToolTip']
}

var block_simple_input = {
  "type": "simple_input",
  "message0": MSG['blockSimpleInputMessage'],
  "args0": [
    {
      "type": "field_dropdown",
      "name": "input_port",
      "options": [
        [ "I1", "0" ], [ "I2", "1" ], [ "I3", "2" ], [ "I4", "3" ],
        [ "I5", "4" ], [ "I6", "5" ], [ "I7", "6" ], [ "I8", "7" ]
      ]
    }
  ],
  "output": "Boolean",
  "colour": InputBlocksHUE,
  "tooltip": MSG['blockSimpleInputToolTip']
}

var block_input = {
  "type": "input",
  "message0": MSG['blockInputMessage'],
  "args0": [
    {
      "type": "field_dropdown",
      "name": "type",
      "options": [
          [ MSG['blockInputModeVoltage'],    '"voltage"' ],
          [ MSG['blockInputModeSwitch'],     '"switch"'  ],
          [ MSG['blockInputModeResistor'],   '"resistor"' ],
          // [ MSG['blockInputModeResistor2'],  '"resistor2"' ],
          [ MSG['blockInputModeUltrasonic'], '"ultrasonic"' ]
      ]
    },
    {
      "type": "field_dropdown",
      "name": "input_port",
      "options": [
        [ "I1", "0" ], [ "I2", "1" ], [ "I3", "2" ], [ "I4", "3" ],
        [ "I5", "4" ], [ "I6", "5" ], [ "I7", "6" ], [ "I8", "7" ]
      ]
    }
  ],
  "output": "Number",
  "colour": InputBlocksHUE,
  "tooltip": MSG['blockInputToolTip']
}

var block_input_converter_r2t = {
    "type": "input_converter_r2t",
    "message0": MSG['blockInputConvTempMessage'],
    "args0": [ {
	"type": "field_dropdown",
	"name": "system",
	"options": [
            [ "°C", '"degCelsius"' ],
            [ "°F", '"degFahrenheit"' ],
            [ "K",  '"kelvin"' ]
	]
    }, {
	"type": "input_value",
	"name": "value",
	"check": "Number"
    } ],
    "output": "Number",
    "colour": InputBlocksHUE,
    "tooltip": MSG['blockInputConvTempToolTip']
}

var block_play_snd = {
    "type": "play_snd",
    "message0": MSG['blockPlaySndMessage'],
    "args0": [
	{
	    "type": "input_value",
	    "name": "sound_index"
	}
    ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": CustomBlocksHUE,
    "tooltip": MSG['blockPlaySndToolTip']
}
    
var block_sound = {
  "type": "sound",
  "message0": MSG['blockSoundMessage'],
  "args0": [ {
      "type": "field_dropdown",
      "name": "index",
      "options": [
	  [ MSG['blockSoundAirplane'], "1" ],
	  [ MSG['blockSoundAlarm'], "2" ],
	  [ MSG['blockSoundBell'], "3" ],
	  [ MSG['blockSoundBraking'], "4" ],
	  [ MSG['blockSoundCar_horn_long'], "5" ],
	  [ MSG['blockSoundCar_horn_short'], "6" ],
	  [ MSG['blockSoundCrackling_wood'], "7" ],
	  [ MSG['blockSoundExcavator'], "8" ],
	  [ MSG['blockSoundFantasy_1'], "9" ],
	  [ MSG['blockSoundFantasy_2'], "10" ],
	  [ MSG['blockSoundFantasy_3'], "11" ],
	  [ MSG['blockSoundFantasy_4'], "12" ],
	  [ MSG['blockSoundFarm'], "13" ],
	  [ MSG['blockSoundFire_department'], "14" ],
	  [ MSG['blockSoundFire_noises'], "15" ],
	  [ MSG['blockSoundFormula1'], "16" ],
	  [ MSG['blockSoundHelicopter'], "17" ],
	  [ MSG['blockSoundHydraulic'], "18" ],
	  [ MSG['blockSoundMotor_sound'], "19" ],
	  [ MSG['blockSoundMotor_starting'], "20" ],
	  [ MSG['blockSoundPropeller_airplane'], "21" ],
	  [ MSG['blockSoundRoller_coaster'], "22" ],
	  [ MSG['blockSoundShips_horn'], "23" ],
	  [ MSG['blockSoundTractor'], "24" ],
	  [ MSG['blockSoundTruck'], "25" ],
	  [ MSG['blockSoundRobby_1'], "26" ],
	  [ MSG['blockSoundRobby_2'], "27" ],
	  [ MSG['blockSoundRobby_3'], "28" ],
	  [ MSG['blockSoundRobby_4'], "29" ]
      ]
    } ],
  "output": "Number",
  "colour": CustomBlocksHUE,
  "tooltip": MSG['blockSoundToolTip']
};

// custom text related blocks
var block_text_print_color = {
    "type": "text_set_color",
    "message0": MSG['blockTextPrintColorMessage'],
    "args0": [ { "type": "field_colour", "name": "color",
		 "colour": "#ffff00" }, 
	       {
		   "type": "input_value",
		   "name": "str" } ],
    "previousStatement": null,
    "nextStatement": null,
    "colour": TextBlocksHUE,
    "tooltip": MSG['blockTextPrintColorToolTip']
}

var block_text_clear = {
    "type": "text_clear",
    "message0": MSG['blockTextEraseMessage'],
    "previousStatement": null,
    "nextStatement": null,
    "colour": TextBlocksHUE,
    "tooltip": MSG['blockTextEraseToolTip']
}

// generate python code for custom blocks
Blockly.Python['start'] = function(block) {
  var code = '# program start\n';
  return code;
};

Blockly.Python['wait'] = function(block) {
    var value_seconds = Blockly.Python.valueToCode(block, 'seconds', Blockly.Python.ORDER_ATOMIC);
    if(!value_seconds) value_seconds = 0;
    return 'wait(%1)\n'.replace('%1', value_seconds);
};

Blockly.Python['repeat'] = function(block) {
    var statements = Blockly.Python.statementToCode(block, 'STATEMENTS');
    var code = 'while True:\n' + statements;
    return code;
}

Blockly.Python['io_sync'] = function(block) {
    var statements = Blockly.Python.statementToCode(block, 'STATEMENTS');
    var code = 'sync(True)\nif True:\n' + statements + "sync(False)\n";
    return code;
}

Blockly.Python['mobile_config'] = function(block) {
    var motors = [ block.getFieldValue('motor_left'), block.getFieldValue('motor_right') ];
    var motor_type = Blockly.Python.valueToCode(block, 'motor_type', Blockly.Python.ORDER_ATOMIC);
    var gear = block.getFieldValue('gear_ratio_1') / block.getFieldValue('gear_ratio_2');
    var wheels = [ block.getFieldValue('wheel_diam'), block.getFieldValue('wheel_dist') ];
    return 'mobileConfig([%1], %2, %3, [%4])\n'.replace('%1', motors).replace('%2', motor_type)
	.replace('%3', gear).replace('%4', wheels);
}

Blockly.Python['mobile_drive'] = function(block) {
    var dir = block.getFieldValue('dir');
    var dist = Blockly.Python.valueToCode(block, 'dist', Blockly.Python.ORDER_ATOMIC);
    return 'mobileDrive(%1, %2)\n'.replace('%1', dir).replace('%2', dist);
}

Blockly.Python['mobile_drive_while'] = function(block) {
    var dir = block.getFieldValue('dir');
    var w = block.getFieldValue('while');
    var value = Blockly.Python.valueToCode(block, 'value',
	       Blockly.Python.ORDER_ATOMIC) || 'False';
    
    // todo: value is only evaluated once!!
    return 'mobileDriveWhile(%1, %2, \'%3\')\n'.replace('%1', dir).replace('%2', w).replace('%3', value);
}

Blockly.Python['mobile_turn'] = function(block) {
    var dir = block.getFieldValue('dir');
    var angle = Blockly.Python.valueToCode(block, 'angle', Blockly.Python.ORDER_ATOMIC);
    return 'mobileTurn(%1, %2)\n'.replace('%1', dir).replace('%2', angle);
}

Blockly.Python['simple_angle'] = function(block) {
    var angle = block.getFieldValue('angle');
    return [angle, Blockly.Python.ORDER_NONE];
};

Blockly.Python['angle'] = function(block) {
    var angle = block.getFieldValue('angle');
    return [angle, Blockly.Python.ORDER_NONE];
};

Blockly.Python['pwm_value'] = function(block) {
    var state = block.getFieldValue('state');
    return [state, Blockly.Python.ORDER_NONE];
};

Blockly.Python['on_off'] = function(block) {
    var state = block.getFieldValue('state');
    return [state, Blockly.Python.ORDER_NONE];
};

Blockly.Python['left_right'] = function(block) {
    var dir = block.getFieldValue('dir');
    return [dir, Blockly.Python.ORDER_NONE];
};

Blockly.Python['gear_ratio'] = function(block) {
    var impulses = block.getFieldValue('gear_ratio');
    return [impulses, Blockly.Python.ORDER_NONE];
};

Blockly.Python['output'] = function(block) {
    var port = block.getFieldValue('port');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    return 'setOutput(%1, %2)\n'.replace('%1', port).replace('%2', value);
}

Blockly.Python['motor_set'] = function(block) {
    var port = block.getFieldValue('port');
    var name = block.getFieldValue('name');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    return 'setMotor(%1, \'%2\', %3)\n'.replace('%1', port).replace('%2', name).replace('%3', value);
}

Blockly.Python['motor_sync'] = function(block) {
    var port_a = block.getFieldValue('port_a');
    var port_b = block.getFieldValue('port_b');
    return 'setMotorSync(%1, %2)\n'.replace('%1', port_a).replace('%2', port_b);
}

Blockly.Python['motor'] = function(block) {
    var port = block.getFieldValue('port');
    var dir = block.getFieldValue('dir');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    return 'setMotorOld(%1, %2, %3)\n'.replace('%1', port).replace('%2', dir).replace('%3', value);
}

Blockly.Python['motor_steps'] = function(block) {
    var port = block.getFieldValue('port');
    var dir = block.getFieldValue('dir');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    var steps = Blockly.Python.valueToCode(block, 'steps', Blockly.Python.ORDER_ATOMIC);
    return 'setMotorOld(%1, %2, %3, %4)\n'.replace('%1', port).replace('%2', dir).replace('%3', value).replace('%4', steps);
};

Blockly.Python['motor_has_stopped'] = function(block) {
    var port = block.getFieldValue('port');
    return ['motorHasStopped(%1)'.replace('%1', port), Blockly.Python.ORDER_NONE];
};

Blockly.Python['motor_off'] = function(block) {
    var port = block.getFieldValue('port');
    return 'setMotorOff(%1)\n'.replace('%1', port);
}

Blockly.Python['simple_input'] = function(block) {
    var port = block.getFieldValue('input_port');
    code = 'getInput("switch", %1)'.replace('%1', port);
    return [code, Blockly.Python.ORDER_NONE];
}

Blockly.Python['input'] = function(block) {
    var type = block.getFieldValue('type');
    var port = block.getFieldValue('input_port');
    code = 'getInput(%1, %2)'.replace("%1", type).replace('%2', port);
    return [code, Blockly.Python.ORDER_NONE];
};

Blockly.Python['input_converter_r2t'] = function(block) {
    var system = block.getFieldValue('system');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    var code = "inputConvR2T(%1, %2)".replace("%1", system).replace("%2", value);
    return [code, Blockly.Python.ORDER_NONE];
};

Blockly.Python['play_snd'] = function(block) {
    var value = Blockly.Python.valueToCode(block, 'sound_index', Blockly.Python.ORDER_ATOMIC);
    return 'playSound(%1)\n'.replace('%1', value);
}

Blockly.Python['sound'] = function(block) {
    var index = block.getFieldValue('index');
    return [index, Blockly.Python.ORDER_NONE];
}

Blockly.Python['text_clear'] = function(block) {
    return 'textClear()\n';
}

Blockly.Python['text_print_color'] = function(block) {
    var col = block.getFieldValue('color');
    var str = Blockly.Python.valueToCode(block, 'str', Blockly.Python.ORDER_ATOMIC);
    return 'textPrintColor(\'%1\',%2)\n'.replace('%1', col).replace('%2', str);
}

function custom_blocks_init() {
    // make custom blocks known to blockly

    // the start block has some additional brickly specific magic and
    // is thus created programmatically
    Blockly.Blocks['start'] = {
	init: function() {
	    // add icon and program name to block
	    this.appendDummyInput()
		.appendField(new Blockly.FieldImage("icon_start.svg", 16, 16, "|>"))
		.appendField(new Blockly.FieldLabel(htmlDecode(Code.program_name[1]), 'program_name'))
	    
	    this.setNextStatement(true, null);
	    this.setColour(225);
	    this.setTooltip(MSG['blockStartToolTip']);
	} 
    };
    
    Blockly.Blocks['wait'] = {
	init: function() { this.jsonInit(block_wait); } };
    Blockly.Blocks['repeat'] = {
	init: function() { this.jsonInit(block_repeat); } };
    Blockly.Blocks['js_present'] = {
	init: function() { this.jsonInit(block_js_present); } };
    Blockly.Blocks['js_axis'] = {
	init: function() { this.jsonInit(block_js_axis); } };
    Blockly.Blocks['js_button'] = {
	init: function() { this.jsonInit(block_js_button); } };
    Blockly.Blocks['output'] = {
	init: function() { this.jsonInit(block_output); } };
    Blockly.Blocks['io_sync'] = {
	init: function() { this.jsonInit(block_io_sync); } };
    Blockly.Blocks['mobile_config'] = {
	init: function() { this.jsonInit(block_mobile_config); } };
    Blockly.Blocks['mobile_drive'] = {
	init: function() { this.jsonInit(block_mobile_drive); } };
    Blockly.Blocks['mobile_drive_while'] = {
	init: function() { this.jsonInit(block_mobile_drive_while); } };
    Blockly.Blocks['mobile_turn'] = {
	init: function() { this.jsonInit(block_mobile_turn); } };
    Blockly.Blocks['simple_angle'] = {
	init: function() { this.jsonInit(block_simple_angle); } };
    Blockly.Blocks['angle'] = {
	init: function() { this.jsonInit(block_angle); } };
    Blockly.Blocks['motor_set'] = {
	init: function() { this.jsonInit(block_motor_set); } };
    Blockly.Blocks['motor_sync'] = {
	init: function() { this.jsonInit(block_motor_sync); } };
    Blockly.Blocks['motor'] = {
	init: function() { this.jsonInit(block_motor); } };
    Blockly.Blocks['motor_steps'] = {
	init: function() { this.jsonInit(block_motor_steps); } };
    Blockly.Blocks['motor_has_stopped'] = {
	init: function() { this.jsonInit(block_motor_has_stopped); } };
    Blockly.Blocks['motor_off'] = {
	init: function() { this.jsonInit(block_motor_off); } };
    Blockly.Blocks['simple_input'] = {
	init: function() { this.jsonInit(block_simple_input); } };
    Blockly.Blocks['input'] = {
	init: function() { this.jsonInit(block_input); } };
    Blockly.Blocks['input_converter_r2t'] = {
	init: function() { this.jsonInit(block_input_converter_r2t); } };
    Blockly.Blocks['pwm_value'] = {
	init: function() { this.jsonInit(block_pwm_value); } };
    Blockly.Blocks['on_off'] = {
	init: function() { this.jsonInit(block_on_off); } };
    Blockly.Blocks['left_right'] = {
	init: function() { this.jsonInit(block_left_right); } };
    Blockly.Blocks['gear_ratio'] = {
	init: function() { this.jsonInit(block_gear_ratio); } };
    Blockly.Blocks['play_snd'] = {
	init: function() { this.jsonInit(block_play_snd); } };
    Blockly.Blocks['sound'] = {
	init: function() { this.jsonInit(block_sound); } };
    Blockly.Blocks['text_clear'] = {
	init: function() { this.jsonInit(block_text_clear); } };
    Blockly.Blocks['text_print_color'] = {
	init: function() { this.jsonInit(block_text_print_color); } };
}

