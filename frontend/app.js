// ═══════════════════════════════════════════════════════
//  BCI Wave Monitor — Frontend
// ═══════════════════════════════════════════════════════
//
//  USAGE (from your start button, Node-RED, or any JS):
//
//    // Start with simulated data (demo mode):
//    BCI.start();
//
//    // Start with external data (you push samples manually):
//    BCI.start({ mode: 'external', timeLimit: 30 });
//    BCI.pushSample(0.42);   // call this each time new data arrives
//
//    // Start with WebSocket (auto-connects and reads data):
//    BCI.start({ mode: 'websocket', url: 'ws://localhost:1880/bci' });
//
//    // Stop manually:
//    BCI.stop();
//
//    // Listen for stop events (time limit or trajectory hit):
//    BCI.onStop = (reason) => console.log('Stopped:', reason);
//
// ═══════════════════════════════════════════════════════

(() => {
  // ── DOM Elements ──────────────────────────────────
  const stopBtn = document.getElementById('stopBtn');
  const wavePanel = document.getElementById('wavePanel');
  const statusBadge = document.getElementById('statusBadge');
  const canvas = document.getElementById('waveCanvas');
  const ctx = canvas.getContext('2d');
  const amplitudeDisplay = document.getElementById('amplitudeValue');
  const frequencyDisplay = document.getElementById('frequencyValue');
  const elapsedDisplay = document.getElementById('elapsedValue');

  // ── Config (defaults, overridden by BCI.start(options)) ──
  const config = {
    mode: 'simulated',          // 'simulated' | 'external' | 'websocket'
    url: 'ws://localhost:1880/bci',  // WebSocket URL (only used in 'websocket' mode)
    timeLimit: 0,               // seconds, 0 = no limit
    trajectoryThreshold: 0,     // amplitude threshold, 0 = disabled
    speed: 1.8,                 // sweep speed (pixels per frame)
    eraseWidth: 40,             // gap ahead of sweep
  };

  // ── Internal State ────────────────────────────────
  let running = false;
  let animId = null;
  let elapsedTime = 0;
  let sweepX = 0;
  let waveBuffer = [];
  let W = 0;
  let H = 0;
  const DPR = window.devicePixelRatio || 1;
  const LINE_WIDTH = 2.5;
  const TICKER_RADIUS = 7;
  const CYAN = '#00D2FF';

  // Data queue — external sources push here, renderer consumes
  let dataQueue = [];
  let lastSample = 0;

  // WebSocket reference
  let ws = null;

  // Simulated signal state
  let signalPhase = 0;
  let ampTarget = 0.6;
  let ampCurrent = 0.6;
  let driftTimer = 0;
  const FIXED_FREQ = 0.7;

  // ── Simulated Signal Generator ────────────────────
  function generateSimulatedSample(dt) {
    signalPhase += dt;
    driftTimer -= dt;
    if (driftTimer <= 0) {
      ampTarget = 0.3 + Math.random() * 0.7;
      driftTimer = 2.0 + Math.random() * 4.0;
    }
    ampCurrent += (ampTarget - ampCurrent) * 0.008;
    const primary = Math.sin(signalPhase * FIXED_FREQ * 2 * Math.PI) * ampCurrent;
    const harmonic = Math.sin(signalPhase * FIXED_FREQ * 4 * Math.PI) * ampCurrent * 0.12;
    return primary + harmonic;
  }

  // ── Get Next Sample ───────────────────────────────
  // Returns a normalized value roughly in [-1, 1]
  function getNextSample(dt) {
    if (config.mode === 'simulated') {
      return generateSimulatedSample(dt);
    }
    // For external / websocket: consume from queue, or hold last value
    if (dataQueue.length > 0) {
      lastSample = dataQueue.shift();
    }
    return lastSample;
  }

  // ── WebSocket ─────────────────────────────────────
  function connectWebSocket() {
    if (ws) ws.close();
    ws = new WebSocket(config.url);

    ws.onopen = () => console.log('[BCI] WebSocket connected:', config.url);
    ws.onclose = () => console.log('[BCI] WebSocket closed');
    ws.onerror = (e) => console.error('[BCI] WebSocket error:', e);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Accept { amplitude: number } or just a raw number
        const value = typeof data === 'number' ? data : (data.amplitude ?? data.value ?? 0);
        dataQueue.push(value);
      } catch {
        // Try as plain number
        const num = parseFloat(event.data);
        if (!isNaN(num)) dataQueue.push(num);
      }
    };
  }

  function disconnectWebSocket() {
    if (ws) { ws.close(); ws = null; }
  }

  // ── Resize ────────────────────────────────────────
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    W = rect.width;
    H = rect.height;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    waveBuffer = new Array(Math.ceil(W)).fill(null);
    sweepX = 0;
  }
  window.addEventListener('resize', resize);

  // ── Drawing: Grid ─────────────────────────────────
  function drawGrid() {
    ctx.save();
    ctx.strokeStyle = 'rgba(37, 38, 54, 0.8)';
    ctx.lineWidth = 1;

    const hCount = 8;
    for (let i = 1; i < hCount; i++) {
      const y = (H / hCount) * i;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    const vSpacing = 80;
    for (let x = vSpacing; x < W; x += vSpacing) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }

    // Center baseline
    ctx.strokeStyle = 'rgba(37, 38, 54, 1)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, H / 2); ctx.lineTo(W, H / 2); ctx.stroke();
    ctx.restore();
  }

  // ── Drawing: Wave + Ticker ────────────────────────
  function drawWave(tickerPosX, tickerPosY) {
    const midY = H / 2;
    ctx.save();
    ctx.lineWidth = LINE_WIDTH;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const eraseStart = sweepX;
    const eraseEnd = (sweepX + config.eraseWidth) % W;

    // Trail
    ctx.beginPath();
    let drawing = false;
    for (let x = 0; x < W; x++) {
      const inErase = eraseEnd > eraseStart
        ? (x >= eraseStart && x <= eraseEnd)
        : (x >= eraseStart || x <= eraseEnd);

      if (inErase || waveBuffer[x] === null) {
        if (drawing) { ctx.stroke(); drawing = false; }
        continue;
      }
      if (!drawing) {
        ctx.beginPath();
        let dist = x < sweepX ? sweepX - x : sweepX + (W - x);
        const opacity = Math.max(0.1, 1 - dist / W);
        ctx.strokeStyle = `rgba(0, 210, 255, ${opacity})`;
        ctx.shadowColor = `rgba(0, 210, 255, ${opacity * 0.4})`;
        ctx.shadowBlur = 6;
        ctx.moveTo(x, waveBuffer[x]);
        drawing = true;
      } else {
        ctx.lineTo(x, waveBuffer[x]);
      }
    }
    if (drawing) ctx.stroke();

    // Bright head section
    const brightLen = 60;
    const brightStart = Math.floor(sweepX) - brightLen;
    if (brightStart >= 0) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(0, 210, 255, 1)';
      ctx.shadowColor = 'rgba(0, 210, 255, 0.6)';
      ctx.shadowBlur = 12;
      ctx.lineWidth = LINE_WIDTH + 0.5;
      drawing = false;
      for (let x = brightStart; x < Math.floor(sweepX); x++) {
        if (waveBuffer[x] === null) {
          if (drawing) { ctx.stroke(); ctx.beginPath(); drawing = false; }
          continue;
        }
        if (!drawing) { ctx.moveTo(x, waveBuffer[x]); drawing = true; }
        else { ctx.lineTo(x, waveBuffer[x]); }
      }
      if (drawing) ctx.stroke();
    }
    ctx.restore();

    // Ticker (three-layer)
    const tickerX = tickerPosX;
    const tickerY = tickerPosY;
    if (tickerX <= 0 || tickerX >= W) return;

    // Outer glow
    const glowGrad = ctx.createRadialGradient(tickerX, tickerY, 0, tickerX, tickerY, TICKER_RADIUS * 3);
    glowGrad.addColorStop(0, 'rgba(0, 210, 255, 0.4)');
    glowGrad.addColorStop(1, 'rgba(0, 210, 255, 0)');
    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(tickerX, tickerY, TICKER_RADIUS * 3, 0, Math.PI * 2);
    ctx.fill();

    // Circle border
    ctx.beginPath();
    ctx.arc(tickerX, tickerY, TICKER_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = '#0a0b10';
    ctx.fill();
    ctx.strokeStyle = CYAN;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(0, 210, 255, 0.8)';
    ctx.shadowBlur = 14;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Inner dot
    ctx.beginPath();
    ctx.arc(tickerX, tickerY, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.fill();
  }

  // ── Animation Loop ────────────────────────────────
  let lastFrameTime = 0;

  function frame(ts) {
    if (!running) return;

    const dt = lastFrameTime ? (ts - lastFrameTime) / 1000 : 1 / 60;
    lastFrameTime = ts;
    elapsedTime += dt;

    // ── Check stop conditions ──
    if (config.timeLimit > 0 && elapsedTime >= config.timeLimit) {
      doStop('time_limit');
      return;
    }

    // Get next amplitude sample
    const sample = getNextSample(dt);

    // Check trajectory threshold
    if (config.trajectoryThreshold > 0 && Math.abs(sample) >= config.trajectoryThreshold) {
      doStop('trajectory');
      return;
    }

    // Map sample to canvas Y
    const midY = H / 2;
    const amplitude = H * 0.35;
    const y = midY - sample * amplitude;

    // Write to buffer
    const steps = Math.ceil(config.speed);
    let lastWrittenX = Math.floor(sweepX);
    for (let i = 0; i < steps; i++) {
      const bx = Math.floor(sweepX + i) % W;
      waveBuffer[bx] = y;
      lastWrittenX = bx;
      const eraseX = (bx + Math.floor(config.eraseWidth)) % W;
      waveBuffer[eraseX] = null;
    }
    sweepX = (sweepX + config.speed) % W;

    // Update UI metrics
    amplitudeDisplay.textContent = Math.abs(sample * 100).toFixed(1);
    if (frequencyDisplay) frequencyDisplay.textContent = FIXED_FREQ.toFixed(1);
    if (elapsedDisplay) elapsedDisplay.textContent = elapsedTime.toFixed(1) + 's';

    // Render
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
    drawGrid();
    drawWave(lastWrittenX, y);

    animId = requestAnimationFrame(frame);
  }

  // ── Start / Stop ──────────────────────────────────
  function doStart(options = {}) {
    if (running) doStop('restart');

    // Merge user options into config
    Object.assign(config, options);

    // Reset state
    running = true;
    lastFrameTime = 0;
    elapsedTime = 0;
    sweepX = 0;
    dataQueue = [];
    lastSample = 0;
    signalPhase = 0;
    driftTimer = 0;
    ampCurrent = 0.6;

    // Connect WebSocket if needed
    if (config.mode === 'websocket') {
      connectWebSocket();
    }

    // Update UI
    statusBadge.classList.add('active');
    statusBadge.querySelector('.status-text').textContent = 'Monitoring';

    resize();
    animId = requestAnimationFrame(frame);

    console.log('[BCI] Started — mode:', config.mode,
      config.timeLimit ? `| time limit: ${config.timeLimit}s` : '',
      config.trajectoryThreshold ? `| trajectory threshold: ${config.trajectoryThreshold}` : ''
    );
  }

  function doStop(reason = 'manual') {
    running = false;
    if (animId) cancelAnimationFrame(animId);
    disconnectWebSocket();

    statusBadge.classList.remove('active');
    statusBadge.querySelector('.status-text').textContent = 'Stopped';

    console.log('[BCI] Stopped — reason:', reason, '| elapsed:', elapsedTime.toFixed(1) + 's');

    // Fire callback if set
    if (typeof window.BCI.onStop === 'function') {
      window.BCI.onStop(reason, { elapsed: elapsedTime });
    }
  }

  // ── Push Sample (for external mode) ───────────────
  function pushSample(value) {
    dataQueue.push(value);
  }

  // ── Stop button ───────────────────────────────────
  if (stopBtn) stopBtn.addEventListener('click', () => doStop('manual'));

  // ── Expose Global API ─────────────────────────────
  window.BCI = {
    start: doStart,
    stop: doStop,
    pushSample: pushSample,
    onStop: null,               // set this to a callback: (reason, data) => {}

    // Helpers
    isRunning: () => running,
    getElapsed: () => elapsedTime,
    getConfig: () => ({ ...config }),
  };

  // ── Init canvas on load ───────────────────────────
  window.addEventListener('load', () => {
    resize();
    // Auto-start in simulated mode for demo
    // Remove this line once the start button is wired up
    doStart({ mode: 'simulated' });
  });

})();
