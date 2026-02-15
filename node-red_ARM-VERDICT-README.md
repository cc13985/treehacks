# Arm verdict + lock (release when user returns to home)

## Node-RED quick checklist (to support Brain Crush + Continue to result)

1. **Import BCI wave flow**  
   Import **`node-red_bci-wave-flow.json`**. You get: Format beta high for wave, Send to wave simulator, Wave clients connect here, **Robot done (port 5006)**, **Robot done → frontend**, Test inject (disable it if using real sensor).

2. **Import arm verdict flow**  
   Import **`node-red_arm-verdict-lock-flow.json`**. You get: **Verdict (no lock)** (or Verdict and lock, depending on file).

3. **Wire BCI → wave**  
   Connect your **sensor / high-beta output** to **Format beta high for wave** (already wired to **Send to wave simulator**). That gives the live wave and μV² in Brain Crush.

4. **Wire decision → arm and frontend**  
   Connect **function 1** (APPROACH/REFUSE) → **Verdict (no lock)** (or Verdict and lock).  
   - **First output** of Verdict → your **UDP out** node set to **127.0.0.1:5005** (arm).  
   - **Second output** of Verdict → **Send to wave simulator** (so the app gets the verdict and shows “Robot moving…”).

5. **Robot done (Continue to result)**  
   The BCI wave flow already has **Robot done (port 5006)** and **Robot done → frontend** wired to **Send to wave simulator**. When the Python arm sends ROBOT_DONE to port 5006, Node-RED sends `{ robotDone: true }` to the app and the Continue button enables. No extra wiring.

6. **Release (if you use the lock flow)**  
   If your verdict flow has **Release lock** and **UDP RELEASE to arm**: connect **Wave clients connect here** → **Release lock (from frontend)** → **UDP RELEASE to arm** (127.0.0.1:5005).

7. **Deploy**  
   Click **Deploy**.

## Behaviour

1. When your flow decides **APPROACH** or **REFUSE**, that decision runs **once** and is sent to the arm and frontend.
2. The arm and Node-RED are **locked**: no new decision is sent to the arm until the user **returns to the home screen** in Brain Crush.
3. When the user clicks **"Keep analyzing my brain"** (Reset) and goes back to the home screen, the frontend sends **release**; Node-RED clears its lock and sends **RELEASE** to the Python arm so it can accept the next decision.

## Node-RED setup

### Step 1: Import the lock nodes

1. In Node-RED: **Menu (≡) → Import → select file** (or paste from clipboard).
2. Choose **`node-red_arm-verdict-lock-flow.json`** and import.
3. You should see three nodes: **"Verdict and lock"**, **"Release lock (from frontend)"**, and **"UDP RELEASE to arm"**.

### Step 2: Wire Verdict and lock between function 1 and UDP

1. **Remove** any existing wire from **function 1** to **udp 127.0.0.1:5005**.

2. **Connect function 1 → Verdict and lock**
   - Drag from the **output** of **function 1** to the **input** of **"Verdict and lock"**.

3. **Connect Verdict and lock → UDP**
   - **"Verdict and lock"** has **two outputs**. Drag from the **first (top) output** to the **input** of **udp 127.0.0.1:5005**.

4. **Connect Verdict and lock → frontend**
   - Drag from the **second (bottom) output** to the **input** of **"Send to wave simulator"** so the app shows the decision.

### Step 3: Wire release (when user goes home)

When the user returns to the home screen, the frontend sends `{ release: true }` on the WebSocket. Node-RED must handle it:

1. Find **"Wave clients connect here"** (WebSocket In on `/bci`).
2. **Connect** its **output** to the **input** of **"Release lock (from frontend)"**.
3. **Connect** the **output** of **"Release lock (from frontend)"** to the **input** of **"UDP RELEASE to arm"**.
4. Double‑click **"UDP RELEASE to arm"** and set destination **127.0.0.1** and port **5005** if needed.

### Step 4: Deploy

Click **Deploy** (top right).

## Frontend

- When a message with `verdict: "approach"` or `verdict: "reject"` is received, the app shows the verdict. The **Continue** button is disabled and shows **"Robot moving…"** until the app receives `robotDone: true` from Node-RED (or after 15 seconds). Then the user can click **Continue** to go to the result screen.
- **Unlock:** When the user clicks **"Keep analyzing my brain"** (Reset) and goes back to the home screen, the app sends `{ release: true }` to Node-RED so the arm can accept the next decision.

## Robot done → enable Continue

- The Python arm sends **ROBOT_DONE** over UDP to **127.0.0.1:5006** when a behavior (hand over or refuse) finishes.
- The **BCI → Wave Simulator** flow (`node-red_bci-wave-flow.json`) includes **"Robot done (port 5006)"** (UDP in) and **"Robot done → frontend"** (function). When it receives ROBOT_DONE, it sends `{ robotDone: true }` to the WebSocket so Brain Crush enables the Continue button. Re-import `node-red_bci-wave-flow.json` if you don’t see these nodes.

## Python arm

- `keyboard_drive_v2.py`: after one **APPROACH** or **REFUSE** it sets `arm_locked = True` and ignores further commands until it receives **RELEASE** on UDP (127.0.0.1:5005). Release is sent by Node-RED when the user returns to the home screen in Brain Crush.

## Quick wiring summary

```
[ function 1 ]  ──────────────────►  [ Verdict and lock ]  ── output 0 ──►  [ udp 127.0.0.1:5005 ]
     (APPROACH/REFUSE)                        │
                                               └── output 1 ──►  [ Send to wave simulator ]

[ Wave clients connect here ]  ──►  [ Release lock (from frontend) ]  ──►  [ UDP RELEASE to arm ]
     (WebSocket In /bci)              (when user returns to home)           (127.0.0.1:5005)
```

## Robot not moving?

- **First input never moves the arm:** (1) **Verdict and lock output 0** must be wired to your **UDP out** node (127.0.0.1:5005). (2) Run `python lerobot/keyboard_drive_v2.py`; you should see `Current Brain State: APPROACH (locked=False)` when a message is received. (3) Run `python lerobot/udp_listener_test.py` and inject APPROACH to confirm Node-RED is sending.
- If the arm already ran once and won’t move again: have the user click **"Keep analyzing my brain"** (Reset) to go back to home; that sends release. Or restart `keyboard_drive_v2.py` to clear the lock.
- Run **`python lerobot/udp_listener_test.py`** and inject **APPROACH** into the UDP out node to confirm Node-RED is sending.

## Summary

| Step | Who | Action |
|------|-----|--------|
| 1 | Node-RED | Decision → if not locked: set lock, send APPROACH/REFUSE to UDP and verdict to frontend |
| 2 | Arm | Executes once, then ignores until RELEASE |
| 3 | User | Goes through app, then clicks **"Keep analyzing my brain"** (back to home) |
| 4 | Frontend | Sends `{ release: true }` to Node-RED |
| 5 | Node-RED | Clears lock, sends RELEASE to UDP (arm) |
| 6 | Arm | Receives RELEASE, unlocks; next decision will run again |
