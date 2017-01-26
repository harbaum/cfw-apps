// Brickly specifc javascript code

var Audio = { };
Audio.audioContext = null;
Audio.mediaStreamSource = null;
Audio.meter = null;
Audio.ctx = null;
Audio.canvas = null;
Audio.samples = 0;

function audio_rec() {
    // if audio is recoding stop it
    if(Audio.meter) {
	audio_rec_stop()
	return;
    }

    // -- setup audio --

    // media stream source already exists?
    if(!Audio.mediaStreamSource) {

	// grab canvas and place it over the audio icon
	Audio.canvas = document.getElementById("meter")
	icon = document.getElementById("audio_icon")
	Audio.canvas.style.border   = "2px solid red";
	Audio.canvas.style.left = icon.offsetLeft + 'px';
	Audio.canvas.style.top = icon.offsetTop + 'px';
	Audio.canvas.style.width = icon.offsetWidth -4 + 'px';
	Audio.canvas.style.height = icon.offsetHeight - 4 + 'px';
	Audio.ctx = Audio.canvas.getContext("2d");
	
	// monkeypatch Web Audio
	window.AudioContext = window.AudioContext || window.webkitAudioContext;
	
	// grab an audio context
	Audio.audioContext = new AudioContext();
	
	// Attempt to get audio input
	try {
            // monkeypatch getUserMedia
            navigator.getUserMedia = navigator.getUserMedia ||
		navigator.webkitGetUserMedia ||	navigator.mozGetUserMedia;
	    
            // ask for an audio input
            navigator.getUserMedia( {
		"audio": {
		    "mandatory": {
			"googEchoCancellation": "false",
			"googAutoGainControl": "false",
			"googNoiseSuppression": "false",
			"googHighpassFilter": "false"
		    },
		    "optional": []
		},
	    }, gotStream, didntGetStream);
	} catch (e) {
            alert('getUserMedia threw exception :' + e);
	}

	console.log("Audio init done");
    } else {
	console.log("Audio reconnect");

	Audio.canvas.style.display="block";

	// Create a new volume meter and connect it.
	Audio.meter = createAudioMeter(Audio.audioContext);
	Audio.mediaStreamSource.connect(Audio.meter);

	// kick off the visual updating
	audio_draw_meter();
    }
}

function audio_rec_stop() {
    console.log('Audio stop record.');
    Audio.canvas.style.display="none";
    Audio.mediaStreamSource.disconnect(Audio.meter);
    Audio.meter.shutdown();
    Audio.meter = null;

    alert("Received " + (Audio.samples/Audio.audioContext.sampleRate).toFixed(2) + " sec audio data")

    console.log("Samples: " + Audio.samples + " (" +  Audio.audioContext.sampleRate + ") -> " + 
		Audio.samples/Audio.audioContext.sampleRate + "sec");

    Audio.samples = 0;
}

function didntGetStream() {
    console.log('Stream generation failed.');
}

function gotStream(stream) {
    console.log('Got stream.');

    // Create an AudioNode from the stream.
    Audio.mediaStreamSource = Audio.audioContext.createMediaStreamSource(stream);
    
    // Create a new volume meter and connect it.
    Audio.meter = createAudioMeter(Audio.audioContext);
    Audio.mediaStreamSource.connect(Audio.meter);

    // kick off the visual updating
    audio_draw_meter();
}

function createAudioMeter(audioContext,clipLevel,averaging,clipLag) {
    var processor = audioContext.createScriptProcessor(512);
    processor.onaudioprocess = volumeAudioProcess;
    processor.clipping = false;
    processor.lastClip = 0;
    processor.volume = 0;
    processor.clipLevel = clipLevel || 0.98;
    processor.averaging = averaging || 0.95;
    processor.clipLag = clipLag || 750;
    
    // this will have no effect, since we don't copy the input to the output,
    // but works around a current Chrome bug.
    processor.connect(audioContext.destination);
    
    processor.checkClipping =
	function(){
	    if (!this.clipping)
		return false;
	    if ((this.lastClip + this.clipLag) < window.performance.now())
		this.clipping = false;
	    return this.clipping;
	};
    
    processor.shutdown =
	function(){
	    this.disconnect();
	    this.onaudioprocess = null;
	};
    
    return processor;
}

function volumeAudioProcess( event ) {
    var buf = event.inputBuffer.getChannelData(0);  // read first (left?) channel
    var bufLength = buf.length;
    var sum = 0;
    var x;

    console.log("process ...")

    Audio.samples += buf.length;
    
    for (var i=0; i<bufLength; i++) {
    	x = buf[i];
    	if (Math.abs(x)>=this.clipLevel) {
    	    this.clipping = true;
    	    this.lastClip = window.performance.now();
    	}
    	sum += x * x;
    }
    
    // ... then take the square root of the sum.
    var rms =  Math.sqrt(sum / bufLength);

    // Now smooth this out with the averaging factor applied
    // to the previous sample - take the max here because we
    // want "fast attack, slow release."
    this.volume = Math.max(rms, this.volume*this.averaging);
}

function audio_draw_meter() {
    if(Audio.meter) {
	var w = Audio.ctx.canvas.offsetWidth;
	var h = Audio.ctx.canvas.offsetHeight;

	// clear the background
	Audio.ctx.clearRect(0,0,w,h);

	// check if we're currently clipping
	if (Audio.meter.checkClipping())  Audio.ctx.fillStyle = "red";
	else                              Audio.ctx.fillStyle = "#fcce04";

	// draw a bar based on the current volume
	Audio.ctx.fillRect(0, h-Audio.meter.volume*h*2, w, Audio.meter.volume*h*2);

	// set up the next visual callback
	window.requestAnimationFrame( audio_draw_meter );
    }
}
