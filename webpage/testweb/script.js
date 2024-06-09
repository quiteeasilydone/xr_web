let janus = null;
let sfutest = null;
let opaqueId = "videoroomtest-" + Janus.randomString(12);
let myRoom = 12345; // 생성할 방 번호
let dataChannel = null;

Janus.init({
    debug: "all",
    callback: function() {
        janus = new Janus({
            server: server,
            success: function() {
                janus.attach({
                    plugin: "janus.plugin.videoroom",
                    opaqueId: opaqueId,
                    success: function(pluginHandle) {
                        sfutest = pluginHandle;
                        console.log("Plugin attached! (" + sfutest.getPlugin() + ", id=" + sfutest.getId() + ")");
                        createRoom(myRoom);
                    },
                    error: function(error) {
                        console.error("Error attaching plugin...", error);
                        alert("Error attaching plugin... " + error);
                    },
                    consentDialog: function(on) {
                        Janus.debug("Consent dialog should be " + (on ? "on" : "off") + " now");
                    },
                    mediaState: function(medium, on) {
                        Janus.log("Janus " + (on ? "started" : "stopped") + " receiving our " + medium);
                    },
                    webrtcState: function(on) {
                        Janus.log("Janus says our WebRTC PeerConnection is " + (on ? "up" : "down") + " now");
                    },
                    onmessage: function(msg, jsep) {
                        Janus.debug(" ::: Got a message :::", msg);
                        let event = msg["videoroom"];
                        Janus.debug("Event: " + event);
                        if (event === "joined") {
                            myid = msg["id"];
                            mypvtid = msg["private_id"];
                            Janus.log("Successfully joined room " + msg["room"] + " with ID " + myid);
                            if (jsep) {
                                sfutest.createAnswer({
                                    jsep: jsep,
                                    media: { audioSend: false, videoSend: false, data: true }, // Enable DataChannel
                                    success: function(jsep) {
                                        Janus.debug("Got SDP!", jsep);
                                        const body = { request: "start", room: myRoom };
                                        sfutest.send({ message: body, jsep: jsep });
                                    },
                                    error: function(error) {
                                        Janus.error("WebRTC error:", error);
                                        alert("WebRTC error " + error.message);
                                    }
                                });
                            }
                        } else if (event === "event") {
                            // Handle other events
                        }
                    },
                    onlocalstream: function(stream) {
                        Janus.attachMediaStream($('#localvideo').get(0), stream);
                    },
                    onremotestream: function(stream) {
                        Janus.attachMediaStream($('#remotevideo').get(0), stream);
                    },
                    ondataopen: function(label, protocol) {
                        Janus.log("DataChannel opened!");
                        dataChannel = sfutest.dataChannel;
                        document.getElementById('sendImage').onclick = sendImage;
                    },
                    ondata: function(data, label) {
                        Janus.log("We got data from the DataChannel!", data);
                        receiveImage(data);
                    },
                    oncleanup: function() {
                        Janus.log(" ::: Got a cleanup notification :::");
                    }
                });
            },
            error: function(error) {
                console.error(error);
                alert(error);
            },
            destroyed: function() {
                window.location.reload();
            }
        });
    }
});

function createRoom(roomId) {
    let create = {
        request: "create",
        room: roomId,
        description: "My specific room",
        is_private: false,
        publishers: 6,
        bitrate: 128000,
        audiocodec: "opus",
        videocodec: "vp8"
    };
    sfutest.send({
        message: create,
        success: function(result) {
            console.log("Room created successfully", result);
            joinRoom(roomId);
        },
        error: function(error) {
            console.error("Error creating room", error);
        }
    });
}

function joinRoom(roomId) {
    let register = {
        request: "join",
        room: roomId,
        ptype: "publisher",
        display: "User"
    };
    sfutest.send({ message: register });
}

function sendImage() {
    console.log("sendImage function called");
    if (!dataChannel || dataChannel.readyState !== "open") {
        console.error("DataChannel is not open");
        return;
    }
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const arrayBuffer = event.target.result;
            console.log("Sending image data...");
            dataChannel.send(arrayBuffer);
        };
        reader.readAsArrayBuffer(file);
    } else {
        alert("Please select an image file first.");
    }
}

function receiveImage(data) {
    console.log("Receiving image data...");
    const arrayBuffer = data;
    const blob = new Blob([arrayBuffer], { type: 'image/jpeg' });
    const url = URL.createObjectURL(blob);
    const img = document.getElementById('receivedImage');
    img.src = url;
    img.style.display = 'block';
}