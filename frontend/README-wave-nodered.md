# BCI Wave Simulator + Node-RED (High Beta)

## Troubleshooting

- **Wave stays flat or “not working”**
  1. Open the wave page with **http://localhost:8080?mode=websocket** (not just http://localhost:8080).
  2. Open DevTools (F12) → **Console**. You should see `[BCI] WebSocket connected: ws://localhost:1880/bci`. If you see `WebSocket error` or `closed`, Node-RED may not be running or the path `/bci` may be wrong.
  3. When data is flowing you should see a few `[BCI] received: 0.xx` lines. If you never see those, Node-RED is not sending to the browser — check that **Format beta high for wave** is wired to **Send to wave simulator** (WebSocket out).
  4. In Node-RED, add a **Debug** node and connect it to the output of **Format beta high for wave**. Deploy and check the Debug sidebar to confirm messages with `{ amplitude: 0.xx }` are being sent.
  5. If your high beta range is very different from 0–2000, edit the **Format beta high for wave** function and change `maxBeta` (e.g. to 500 or 5000).

## 1. Node-RED: send high beta to the wave simulator

- **Import the flow:** In Node-RED, Menu → Import → paste/clipboard, then choose `node-red_bci-wave-flow.json` from the repo root (or copy its contents).
- **Connect your BCI high-beta output** to the **"Format beta high for wave"** function node (the node that says "Format beta high for wave").  
  So: `[Your BCI / beta high node]` → **Format beta high for wave** → (already wired to) **Send to wave simulator**.
- The flow also has a **"Test (fake beta high)"** inject that sends a number every 0.5 s so you can test without the BCI.
- **Scaling:** The function normalizes with `maxBeta = 2000`. If your high beta range is different, edit that line in the "Format beta high for wave" function (e.g. change `maxBeta`).

The wave simulator expects WebSocket URL: **`ws://localhost:1880/bci`** (Node-RED’s default port).

## 2. Run the wave simulator with live high beta

1. Serve the frontend (from repo root):
   ```bash
   cd frontend && python3 -m http.server 8080
   ```
2. Open: **http://localhost:8080?mode=websocket**  
   The page will auto-connect to Node-RED at `ws://localhost:1880/bci` and display high beta as the wave.  
   For a different WebSocket URL: **http://localhost:8080?mode=websocket&url=ws://yourhost:port/path**
3. Optional: from the normal page (http://localhost:8080), you can switch to Node-RED in the console:
   ```js
   BCI.stop();
   BCI.start({ mode: 'websocket', url: 'ws://localhost:1880/bci' });
   ```
