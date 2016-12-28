// custom block definitions for brickly incl. python code generation
// https://blockly-demo.appspot.com/static/demos/blockfactory/index.html

CustomBlocksHUE = 180
InputBlocksHUE = 200
OutputBlocksHUE = 220

// json definition of custom blocks
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
    }
	     ],
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

// generate python code for custom blocks
Blockly.Python['wait'] = function(block) {
    var value_seconds = Blockly.Python.valueToCode(block, 'seconds', Blockly.Python.ORDER_ATOMIC);
   if(!value_seconds) value_seconds = 0;
    return 'time.sleep(%1)\n'.replace('%1', value_seconds);
};

Blockly.Python['pwm_value'] = function(block) {
    var state = block.getFieldValue('state');
    return [state, Blockly.Python.ORDER_NONE];
};

Blockly.Python['on_off'] = function(block) {
    var state = block.getFieldValue('state');
    return [state, Blockly.Python.ORDER_NONE];
};

Blockly.Python['output'] = function(block) {
    var port = block.getFieldValue('port');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    return 'setOutput(%1, %2)\n'.replace('%1', port).replace('%2', value);
}

Blockly.Python['motor'] = function(block) {
    var port = block.getFieldValue('port');
    var dir = block.getFieldValue('dir');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    return 'setMotor(%1, %2, %3)\n'.replace('%1', port).replace('%2', dir).replace('%3', value);
}

Blockly.Python['motor_steps'] = function(block) {
    var port = block.getFieldValue('port');
    var dir = block.getFieldValue('dir');
    var value = Blockly.Python.valueToCode(block, 'value', Blockly.Python.ORDER_ATOMIC);
    var steps = Blockly.Python.valueToCode(block, 'steps', Blockly.Python.ORDER_ATOMIC);
    return 'setMotor(%1, %2, %3, %4)\n'.replace('%1', port).replace('%2', dir).replace('%3', value).replace('%4', steps);
};

Blockly.Python['motor_has_stopped'] = function(block) {
    var port = block.getFieldValue('port');
    return ['motorHasStopped(%1)\n'.replace('%1', port), Blockly.Python.ORDER_NONE];
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

function custom_blocks_init() {
    // make custom blocks known to blockly
    Blockly.Blocks['wait'] = {
	init: function() { this.jsonInit(block_wait); } };
    Blockly.Blocks['output'] = {
	init: function() { this.jsonInit(block_output); } };
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
    Blockly.Blocks['play_snd'] = {
	init: function() { this.jsonInit(block_play_snd); } };
    Blockly.Blocks['sound'] = {
	init: function() { this.jsonInit(block_sound); } };
}

