let janus = null;
let sfutest = null;
let myRoom = 12345; // 생성할 방 번호
let opaqueId = "videoroomtest-" + Janus.randomString(12);

// Janus 초기화
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
                        } else if (event === "event") {
                            // Handle other events
                        }
                        if (jsep !== undefined && jsep !== null) {
                            Janus.debug("Handling SDP as well...", jsep);
                            sfutest.handleRemoteJsep({ jsep: jsep });
                        }
                    },
                    onlocalstream: function(stream) {
                        Janus.attachMediaStream($('#localvideo').get(0), stream);
                    },
                    onremotestream: function(stream) {
                        Janus.attachMediaStream($('#remotevideo').get(0), stream);
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
