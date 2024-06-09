const canvas = document.getElementById('canvas');

let currentColor = 'black';

function changeColor(color) {
    currentColor = color;
}

window.addEventListener('load', () => {
    const ctx = canvas.getContext('2d');

    // Resize canvas to full window size
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear canvas when resizing
    }
    resizeCanvas();

    let painting = false;

    function startPosition(e) {
        painting = true;
        draw(e);
    }

    function endPosition() {
        painting = false;
        ctx.beginPath();
    }

    function draw(e) {
        if (!painting) return;

        // Adjust mouse coordinates to canvas coordinates
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);

        ctx.lineWidth = 5;
        ctx.lineCap = 'round';
        ctx.strokeStyle = currentColor;

        ctx.lineTo(x, y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x, y);
    }

    // Event Listeners
    canvas.addEventListener('mousedown', startPosition);
    canvas.addEventListener('mouseup', endPosition);
    canvas.addEventListener('mousemove', draw);

    // Resize listener to adjust canvas size
    window.addEventListener('resize', resizeCanvas);
});

function captureScreen() {
    const videoElement = document.getElementById('remotevideo1-1');
    const context = canvas.getContext('2d');
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    console.log(videoElement);
}

async function submitCanvas() {
    const submitUrl = "https://rtctest.p-e.kr/api/whiteboard"
    const dataUrl = canvas.toDataURL('image/jpeg', 0.5);
    const fileName = document.getElementById('remote1').innerText;
    console.log(fileName)

    // Base64 URL을 Blob으로 변환
    const byteString = atob(dataUrl.split(',')[1]);
    const mimeString = dataUrl.split(',')[0].split(':')[1].split(';')[0];

    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);

    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }

    const blob = new Blob([ab], { type: mimeString });

    // FormData에 Blob 추가
    const formData = new FormData();
    formData.append('file', blob, fileName);

    // 파일 전송
    const response = await fetch(submitUrl, {
        method: 'POST',
        body: formData
    });
    
    if (response.ok) {
        alert('전송 성공');
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // canvas.innerHTML = <canvas class= "hide" id="canvas"></canvas>
    } else {
        alert('전송 실패');
        // const ctx = canvas.getContext('2d');
        // ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
}