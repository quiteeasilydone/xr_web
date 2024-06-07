window.addEventListener('load', () => {
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
  
    // Resize canvas to full window size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  
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
      
      ctx.lineWidth = 5;
      ctx.lineCap = 'round';
      ctx.strokeStyle = 'black';
  
      ctx.lineTo(e.clientX, e.clientY);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(e.clientX, e.clientY);
    }
  
    // Event Listeners
    canvas.addEventListener('mousedown', startPosition);
    canvas.addEventListener('mouseup', endPosition);
    canvas.addEventListener('mousemove', draw);
  
    // Resize listener to adjust canvas size
    window.addEventListener('resize', () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    });
  });
  