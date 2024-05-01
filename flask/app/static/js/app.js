const socket = io();

const myFace = document.getElementById("myFace");

//음소거, 카메라 토글, 카메라 선택 버튼
const muteBtn = document.getElementById("mute");
const cameraBtn = document.getElementById("camera");
const camerasSelect = document.getElementById("cameras");

//접속 직후 보이는 div
const welcome = document.getElementById("welcome");
//방 입장 후 보이는 div
const call = document.getElementById("call");

//캡쳐 버튼
const captureButton = document.getElementById("capture");

// 캡처한 이미지를 그릴 캔버스 요소 가져오기
const capturedCanvas = document.getElementById("capturedCanvas");
const ctx = capturedCanvas.getContext("2d");

call.hidden = true;

let myStream;
let peersStream;
let muted = false;
let cameraOn = true;
let currentRoomName;
/** @type {RTCPeerConnection} */
let myPeerConnection;

/** @type {RTCDataChannel} */
let myDataChannel;

// async function getCameras() {
//   try {
//     const devices = await navigator.mediaDevices.enumerateDevices();
//     const cameras = devices.filter((device) => device.kind === "videoinput");
//     cameras.forEach((camera) => {
//       const option = document.createElement("option");
//       option.value = camera.deviceId;
//       option.innerText = camera.label;
//       camerasSelect.appendChild(option);
//     });

//     const option = document.createElement("option");
//     option.value = "screen";
//     option.innerText = "화면 공유";
//     camerasSelect.appendChild(option);
//   } catch (error) {
//     console.log(error);
//   }
// }

async function getCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter((device) => device.kind === "videoinput");
    const currentCamera = myStream.getVideoTracks()[0];
    cameras.forEach((camera) => {
      const option = document.createElement("option");
      option.value = camera.deviceId;
      option.innerText = camera.label;
      if (currentCamera.label === camera.label) {
        option.selected = true;
      }
      camerasSelect.appendChild(option);
    });
  } catch (e) {
    console.log(e);
  }
}

async function getMedia(deviceId) {
  const initialConstrains = {
    audio: true,
    video: { facingMode: "user" },
  };
  const cameraConstraints = {
    audio: true,
    video: { deviceId: { exact: deviceId } },
  };
  try {
    myStream = await navigator.mediaDevices.getUserMedia(
      deviceId ? cameraConstraints : initialConstrains
    );
    myFace.srcObject = myStream;
    if (!deviceId) {
      await getCameras();
    }
  } catch (e) {
    console.log(e);
  }
}

//getMedia();

function handleMuteClick() {
  myStream
    .getAudioTracks()
    .forEach((track) => (track.enabled = !track.enabled));
  muted = !muted;
  if (muted) {
    muteBtn.innerText = "Unmute";
  } else muteBtn.innerText = "Mute";
}

function handleCameraClick() {
  myStream
    .getVideoTracks()
    .forEach((track) => (track.enabled = !track.enabled));
  cameraOn = !cameraOn;
  if (cameraOn) cameraBtn.innerText = "Turn Camera Off";
  else cameraBtn.innerText = "Turn Camera On";
}

muteBtn.addEventListener("click", handleMuteClick);
cameraBtn.addEventListener("click", handleCameraClick);
camerasSelect.addEventListener("input", handleCameraChange);

// async function handleCameraChange() {
//   if (camerasSelect.value == "screen") {
//     console.log("화면 공유");
//     startScreenSharing();
//     return;
//   }
//   await getMedia(camerasSelect.value);
//   if (myPeerConnection) {
//     console.log("카메라 교체");
//     const videoTrack = myStream.getVideoTracks()[0];
//     const videoSender = myPeerConnection
//       .getSenders()
//       .find((sender) => sender.track.kind === "video");
//     videoSender.replaceTrack(videoTrack);
//   }
// }

async function handleCameraChange() {
  if (camerasSelect.value == "screen") {
    console.log("화면 공유");
    startScreenSharing();
    return;
  }

  await getMedia(camerasSelect.value);
  if (myPeerConnection) {
    const videoTrack = myStream.getVideoTracks()[0];
    const videoSender = myPeerConnection
      .getSenders()
      .find((sender) => sender.track.kind === "video");
    videoSender.replaceTrack(videoTrack);
  }
}

// async function handleCameraChange() {
//   if (camerasSelect.value == "screen") {
//     console.log("화면 공유");
//     startScreenSharing();
//     return;
//   }

//   try {
//     const stream = await getMedia(camerasSelect.value);
//     if (myPeerConnection) {
//       console.log("카메라 교체");
//       const videoTrack = stream.getVideoTracks()[0];
//       const videoSender = myPeerConnection
//         .getSenders()
//         .find((sender) => sender.track.kind === "video");
//       if (videoSender) {
//         await videoSender.replaceTrack(videoTrack);
//         console.log("카메라 교체 완료");
//       } else {
//         console.error("비디오 트랙을 찾을 수 없습니다.");
//       }
//     } else {
//       console.error("Peer 연결이 없습니다.");
//     }
//   } catch (error) {
//     console.error("카메라 변경 중 오류 발생:", error);
//   }
// }

const welcomeForm = welcome.querySelector("form");

async function initCall() {
  welcome.hidden = true;
  call.hidden = false;
  await getMedia();
  makeConnection();
}

async function handleWelcomeSubmit(event) {
  event.preventDefault();
  const input = welcomeForm.querySelector("input");
  await initCall();
  socket.emit("join_room", input.value);
  currentRoomName = input.value;
  input.value = "";
}
welcomeForm.addEventListener("submit", handleWelcomeSubmit);

// Socket code

socket.on("welcome", async () => {
  //DataChannel 생성
  myDataChannel = myPeerConnection.createDataChannel("chat");
  myDataChannel.addEventListener("message", handleDataMessage);
  console.log("made data channel");

  const offer = await myPeerConnection.createOffer();
  myPeerConnection.setLocalDescription(offer);
  console.log("sent the offer");
  socket.emit("offer", offer, currentRoomName);
});

socket.on("offer", async (offer) => {
  console.log("received the offer");

  //Data channel 세팅
  myPeerConnection.addEventListener("datachannel", (event) => {
    myDataChannel = event.channel;
    myDataChannel.addEventListener("message", handleDataMessage);
  });

  myPeerConnection.setRemoteDescription(offer);
  const answer = await myPeerConnection.createAnswer();
  myPeerConnection.setLocalDescription(answer);
  socket.emit("answer", answer, currentRoomName);
  console.log("sent the answer");
});

socket.on("answer", (answer) => {
  myPeerConnection.setRemoteDescription(answer);
  console.log("received the offer");
});

socket.on("ice", (ice) => {
  console.log("received candidate");
  myPeerConnection.addIceCandidate(ice);
});

// RTC code

function makeConnection() {
  myPeerConnection = new RTCPeerConnection();
  // myPeerConnection = new RTCPeerConnection({
  //   iceServers: [
  //     {
  //       urls: [
  //         "stun:stun.l.google.com:19302",
  //         "stun:stun1.l.google.com:19302",
  //         "stun:stun2.l.google.com:19302",
  //         "stun:stun3.l.google.com:19302",
  //         "stun:stun4.l.google.com:19302",
  //       ],
  //     },
  //   ],
  // });
  myPeerConnection.addEventListener("icecandidate", handleIce);
  myPeerConnection.addEventListener("addstream", handleAddStream);
  myStream
    .getTracks()
    .forEach((track) => myPeerConnection.addTrack(track, myStream));
}

function handleIce(data) {
  socket.emit("ice", data.candidate, currentRoomName);
  console.log("sent candidate");
}

function handleAddStream(data) {
  const peerFace = document.getElementById("peerFace");
  console.log("got an event from my peer");
  peerFace.srcObject = data.stream;
}

captureButton.addEventListener("click", captureAndDraw);

// peerFace 요소에서 화면 캡처 및 이미지를 그림
function captureAndDraw() {
  // peerFace 비디오 요소 가져오기

  const canvasWidth = 400; // 원하는 캔버스 폭
  const canvasHeight = 400;

  const peerVideo = document.getElementById("peerFace");

  // 캔버스 배경을 검정색으로 처리
  // ctx.fillStyle = "black";
  // ctx.fillRect(0, 0, 400, 400);

  // capturedCanvas.width = peerVideo.videoWidth;
  // capturedCanvas.height = peerVideo.videoHeight;

  // // 캔버스에 그릴 이미지 데이터 생성
  // ctx.drawImage(peerVideo, 0, 0, capturedCanvas.width, capturedCanvas.height);

  // 비율에 맞게 이미지를 그림
  const aspectRatio = peerVideo.videoWidth / peerVideo.videoHeight;
  const imageWidth = canvasWidth;
  const imageHeight = canvasWidth / aspectRatio;
  const xOffset = 0;
  const yOffset = (canvasHeight - imageHeight) / 2; // 이미지를 수직으로 가운데 정렬
  ctx.drawImage(peerVideo, xOffset, yOffset, imageWidth, imageHeight);

  //ctx.fillStyle = "black";
  //ctx.font = "20px Arial";
  //ctx.fillText("캡처된 이미지", 50, 50);

  capturedCanvas.addEventListener("mousedown", startDrawing);
  capturedCanvas.addEventListener("mousemove", draw);
  capturedCanvas.addEventListener("mouseup", stopDrawing);
  capturedCanvas.addEventListener("mouseout", stopDrawing);
}

//그림판 기능

let isDrawing = false;
let lastX = 0;
let lastY = 0;

function startDrawing(e) {
  isDrawing = true;
  [lastX, lastY] = [e.offsetX, e.offsetY];

  draw(e);
}

function draw(e) {
  if (!isDrawing) return;
  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(e.offsetX, e.offsetY);
  ctx.strokeStyle = "#000"; // 그림의 색상 설정
  ctx.lineWidth = 5; // 그림의 두께 설정
  ctx.lineCap = "round"; // 그림의 끝 모양 설정
  ctx.stroke();
  [lastX, lastY] = [e.offsetX, e.offsetY];
}

function stopDrawing() {
  isDrawing = false;
}

// fileInput 요소 가져오기
const fileInput = document.getElementById("fileInput");

// fileInput에 change 이벤트 리스너 추가
fileInput.addEventListener("change", handleFileSelect);

function handleFileSelect(event) {
  const file = event.target.files[0]; // 선택된 파일 가져오기

  // FileReader 객체 생성
  const reader = new FileReader();

  // 파일 읽기 완료 시 호출되는 콜백 함수
  reader.onload = function (event) {
    const imageData = event.target.result; // 이미지 데이터 가져오기

    // DataChannel을 통해 상대방에게 이미지 데이터 전송
    if (myDataChannel.readyState === "open") {
      myDataChannel.send(imageData);
      console.log("File sent!");
    } else {
      console.log("DataChannel is not ready!");
    }
  };

  // 파일을 읽기 시작
  reader.readAsDataURL(file);
}

const sendButton = document.getElementById("sendButton");

sendButton.addEventListener("click", () => {
  // 캔버스의 이미지 데이터를 Data URL로 가져오기
  const imageData = capturedCanvas.toDataURL();

  // DataChannel을 통해 이미지 데이터 전송
  if (myDataChannel.readyState === "open") {
    myDataChannel.send(imageData);
    console.log("Image sent!");
  } else {
    console.log("DataChannel is not ready!");
  }
});

//DataChannel message 처리

function handleDataMessage(event) {
  console.log(event.data);
  // 받은 데이터가 이미지 데이터인 경우
  if (typeof event.data === "string" && event.data.startsWith("data:image")) {
    const image = new Image();
    image.onload = function () {
      handleImageData(image);
    };
    image.src = event.data;
  }
}

//이미지 데이터 처리
function handleImageData(image) {
  // 캔버스의 크기를 고정
  const canvasWidth = capturedCanvas.width;
  const canvasHeight = capturedCanvas.height;

  // 이미지의 가로, 세로 비율 계산
  const imageRatio = image.width / image.height;
  const canvasRatio = canvasWidth / canvasHeight;

  // 캔버스에 그릴 이미지 크기 계산
  let drawWidth = canvasWidth;
  let drawHeight = canvasHeight;
  let offsetX = 0;
  let offsetY = 0;

  if (imageRatio > canvasRatio) {
    // 이미지의 가로가 캔버스보다 길 때
    drawWidth = canvasWidth;
    drawHeight = drawWidth / imageRatio;
    offsetY = (canvasHeight - drawHeight) / 2;
  } else {
    // 이미지의 세로가 캔버스보다 길 때
    drawHeight = canvasHeight;
    drawWidth = drawHeight * imageRatio;
    offsetX = (canvasWidth - drawWidth) / 2;
  }

  // 캔버스에 이미지 그리기
  ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight);
}

//화면 공유
async function startScreenSharing() {
  const stream = await captureScreen();
  if (stream) {
    // 캡처된 화면을 WebRTC를 사용하여 다른 피어와 공유하는 코드를 작성
  }
}

async function captureScreen() {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
    });
    return stream;
  } catch (error) {
    console.error("Error capturing screen:", error);
    return null;
  }
}
