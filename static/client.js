function removebtn(){
	const btnElement = document.getElementById('btn_x');
	const remove_layer = document.getElementsByClassName("work_out_selection")
	btnElement.remove();
	remove_layer.remove();
}

function addList(){
	const div = document.createElement("div");
	const ul = document.createElement("ul");
	const ul2 = document.createElement("ul");
	const btn1 = document.createElement("select");
	const btn2 = document.createElement("input");
	const btn3 = document.createElement("input");
	const btn4 = document.createElement("input") 

	div.setAttribute('class', 'workouts')
	btn2.setAttribute('value', 0)
	btn2.setAttribute('type', "text")
	btn2.setAttribute('size', "2")
	btn2.setAttribute('class', 'cnt')

	btn3.setAttribute('value', 1)
	btn3.setAttribute('type', "text")
	btn3.setAttribute('size', "2")
	btn3.setAttribute('class', 'set')

	btn4.setAttribute('value', "x")
	btn4.setAttribute('type', "button")
	btn4.setAttribute('size', "2")
	btn4.setAttribute('class', "btn_x")
	btn4.setAttribute('onclick', "removeList(this)")

	parent = document.getElementById('work_out_selection');
	parent.appendChild(div);

	if (parent.childElementCount != 1){
	ul2.setAttribute('class', 'breaktime')
	parent.lastChild.appendChild(ul2);
	const break_time = document.createElement("li");
	const time = document.createElement("input")
	const default_time = document.createTextNode("break time")
	break_time.appendChild(default_time)
	time.setAttribute('id', 'time')
	time.setAttribute('class', 'time')
	time.setAttribute('type', "text")
	time.setAttribute('size', "2")
	time.setAttribute('value', '60')
	parent.lastChild.lastChild.appendChild(break_time);
	parent.lastChild.lastChild.appendChild(time);
	}

	// TODO 운동선택 없이 선택시 오류 발생 , 우선 운동선택 제외함
	exercises = ['pushup', 'plank', 'squat', 'legraise', 'lunge'];
	btn1.setAttribute('class', 'exercise')
	for(var i=0; i<exercises.length; i++){
		const option = document.createElement("option");
		const text = document.createTextNode(exercises[i]);
		option.setAttribute('value',exercises[i])
		option.appendChild(text);
		btn1.appendChild(option);
	}
	ul.setAttribute('class', 'list')
	parent.lastChild.appendChild(ul);
	
	parent.lastChild.lastChild.appendChild(btn1);
	parent.lastChild.lastChild.appendChild(btn2);
	parent.lastChild.lastChild.appendChild(btn3);
	parent.lastChild.lastChild.appendChild(btn4);

}

function removeList(ths){

	var ths = $(ths).parent();
	ths.parent().remove();
}


// peer connection
var pc = null;

// data channel
var dc = null, dcInterval = null;
// var audio = new Audio('../Wow.mp3');
// var audio = new Audio('C:/Users/o_nag/workspace/Real_Time_Virtual_Home_Trainer/Wow.mp3');
// audio.play();
var count=''

function createPeerConnection() {
		// get DOM elements
	var dataChannelLog = document.getElementById('data-channel'),
	iceConnectionLog = document.getElementById('ice-connection-state'),
	iceGatheringLog = document.getElementById('ice-gathering-state'),
	signalingLog = document.getElementById('signaling-state');
	var config = {
			sdpSemantics: 'unified-plan'
	};

	pc = new RTCPeerConnection(config);
	
	var channel = pc.createDataChannel("chat");
	channel.onopen = function(event) {
	channel.send('Hi you!');
	}
	
	channel.onmessage = function(event) {
		count=event.data
		localStorage.setItem("count",count)
		console.log(count)
		if(event.data.includes("exit")){
			stop();
		}
		
	}
	// register some listeners to help debugging
	pc.addEventListener('icegatheringstatechange', function() {
			iceGatheringLog.textContent += ' -> ' + pc.iceGatheringState;
	}, false);
	iceGatheringLog.textContent = pc.iceGatheringState;

	pc.addEventListener('iceconnectionstatechange', function() {
			iceConnectionLog.textContent += ' -> ' + pc.iceConnectionState;
	}, false);
	iceConnectionLog.textContent = pc.iceConnectionState;

	pc.addEventListener('signalingstatechange', function() {
			signalingLog.textContent += ' -> ' + pc.signalingState;
	}, false);
	signalingLog.textContent = pc.signalingState;

	// connect audio / video
	pc.addEventListener('track', function(evt) {
		if (evt.track.kind == 'video')
				document.getElementById('video').srcObject = evt.streams[0];
		else
				document.getElementById('audio').srcObject = evt.streams[0];
	});

	return pc;
}

function negotiate() {
	return pc.createOffer().then(function(offer) {
			return pc.setLocalDescription(offer);
	}).then(function() {
			// wait for ICE gathering to complete
			return new Promise(function(resolve) {
					if (pc.iceGatheringState === 'complete') {
							resolve();
					} else {
							function checkState() {
									if (pc.iceGatheringState === 'complete') {
											pc.removeEventListener('icegatheringstatechange', checkState);
											resolve();
									}
							}
							pc.addEventListener('icegatheringstatechange', checkState);
					}
			});
	}).then(function() {
			// console.log("offer")
			var offer = pc.localDescription;
			return fetch('/offer', {
				body: JSON.stringify({

						sdp: offer.sdp,
						type: offer.type,
						exercise: localStorage.getItem("exercise"),
						cnt: localStorage.getItem("cnt"),
						set: localStorage.getItem("set"),
						breaktime: localStorage.getItem("breaktime")
				}),
				headers: {
						'Content-Type': 'application/json'
				},
				method: 'POST'
			});
	}).then(function(response) {
		return response.json();
	}).then(function(answer) {
		document.getElementById('answer-sdp').textContent = answer.sdp;
		return pc.setRemoteDescription(answer);
	}).catch(function(e) {
		alert(e);
	});
}



function start() {
	var exercise_list = []
	var cnt_list = []
	var set_list = []
	var breaktime_list = []
	exercises = document.getElementsByClassName('exercise')
	cnts = document.getElementsByClassName('cnt')
	sets = document.getElementsByClassName('set')
	breaktimes = document.getElementsByClassName('time')

	for (var i=1; i < exercises.length; i++){
		exercise_list.push(exercises[i].value)
	}
	for (var i=1; i < cnts.length; i++){
		cnt_list.push(cnts[i].value)
	}
	for (var i=1; i < sets.length; i++){
		set_list.push(sets[i].value)
	}
	for (var i=1; i< breaktimes.length; i++){
		breaktime_list.push(breaktimes[i].value)
	}

	localStorage.setItem("exercise", exercise_list)
	localStorage.setItem("cnt", cnt_list)
	localStorage.setItem("set", set_list)
	localStorage.setItem("breaktime", breaktime_list)
	location.href = "start.html";

	fetch("/save_workout", {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			exercise: localStorage.getItem("exercise"),
			cnt: localStorage.getItem("cnt"),
			set: localStorage.getItem("set"),
			breaktime: localStorage.getItem("breaktime")
		})
	})
	.then(response => response.json())
	.then(data => console.log(data))

	
}

function start_camera(){
	pc = createPeerConnection();

	var constraints = {
			audio: false,
			video: false,
	};

	var resolution = "700x400";
	if (resolution) {
			resolution = resolution.split('x');
			constraints.video = {
					width: parseInt(window.innerHeight, 0),
					height: parseInt(window.innerWidth, 0),
					facingMode: "user",
			};
	} else {
			constraints.video = true;
	}

	if (constraints.video) {
		document.getElementById('media').style.display = 'block';
	}
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
			stream.getTracks().forEach(function(track) {
					pc.addTrack(track, stream);
			});
			return negotiate();
	}, function(err) {
			alert('Could not acquire media: ' + err);
	});

}



function negotiate_live() {
	return pc.createOffer().then(function(offer) {
			return pc.setLocalDescription(offer);
	}).then(function() {
			// wait for ICE gathering to complete
			return new Promise(function(resolve) {
					if (pc.iceGatheringState === 'complete') {
							resolve();
					} else {
							function checkState() {
									if (pc.iceGatheringState === 'complete') {
											pc.removeEventListener('icegatheringstatechange', checkState);
											resolve();
									}
							}
							pc.addEventListener('icegatheringstatechange', checkState);
					}
			});
	}).then(function() {
			var offer = pc.localDescription;
			return fetch('/offer2', {
				body: JSON.stringify({
						sdp: offer.sdp,
						type: offer.type,
				}),
				headers: {
						'Content-Type': 'application/json'
				},
				method: 'POST'
			});
	}).then(function(response) {
		return response.json();
	}).then(function(answer) {
		document.getElementById('answer-sdp').textContent = answer.sdp;
		return pc.setRemoteDescription(answer);
	}).catch(function(e) {
		alert(e);
	});
}




function live_camera(){
	pc = createPeerConnection();

	var constraints = {
			audio: false,
			video: false,
	};

	var resolution = "700x400";
	if (resolution) {
			resolution = resolution.split('x');
			constraints.video = {
					width: parseInt(window.innerHeight, 0),
					height: parseInt(window.innerWidth, 0),
					facingMode: "user",
			};
	} else {
			constraints.video = true;
	}

	if (constraints.video) {
		document.getElementById('media').style.display = 'block';
	}
	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
			stream.getTracks().forEach(function(track) {
					pc.addTrack(track, stream);
			});
			return negotiate_live();
	}, function(err) {
			alert('Could not acquire media: ' + err);
	});

}


function sdpFilterCodec(kind, codec, realSdp) {
    var allowed = []
    var rtxRegex = new RegExp('a=fmtp:(\\d+) apt=(\\d+)\r$');
    var codecRegex = new RegExp('a=rtpmap:([0-9]+) ' + escapeRegExp(codec))
    var videoRegex = new RegExp('(m=' + kind + ' .*?)( ([0-9]+))*\\s*$')
    
    var lines = realSdp.split('\n');

    var isKind = false;
    for (var i = 0; i < lines.length; i++) {
			if (lines[i].startsWith('m=' + kind + ' ')) {
					isKind = true;
			} else if (lines[i].startsWith('m=')) {
					isKind = false;
			}

			if (isKind) {
					var match = lines[i].match(codecRegex);
					if (match) {
							allowed.push(parseInt(match[1]));
					}

					match = lines[i].match(rtxRegex);
					if (match && allowed.includes(parseInt(match[2]))) {
							allowed.push(parseInt(match[1]));
					}
			}
    }

    var skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)';
    var sdp = '';

    isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var skipMatch = lines[i].match(skipRegex);
            if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
                continue;
            } else if (lines[i].match(videoRegex)) {
                sdp += lines[i].replace(videoRegex, '$1 ' + allowed.join(' ')) + '\n';
            } else {
                sdp += lines[i] + '\n';
            }
        } else {
            sdp += lines[i] + '\n';
        }
    }

    return sdp;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}
function schedule(){
	console.log(localStorage.getItem("count"))
}
function stop(){

	
	
	location.href = "record.html";
	alert(count)
}
