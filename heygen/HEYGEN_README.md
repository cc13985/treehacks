# HeyGen Text → Video

Simple app: **prompt on the homescreen** → your avatar speaks it → **video**. Uses the [HeyGen API Quick Start](https://docs.heygen.com/docs/quick-start) (Option C: Digital Twin / Photo Avatar).

## Setup

1. **Install**
   ```bash
   pip install -r heygen_requirements.txt
   ```

2. **API key**  
   Get it from [HeyGen → Settings → API](https://app.heygen.com/settings?nav=API). Put in `.env`:
   ```env
   HEYGEN_API_KEY=your_api_key
   ```
   (If you already have `LIVEAVATAR_API_KEY` in `.env`, the app will use that if `HEYGEN_API_KEY` is not set.)

3. **Run**
   ```bash
   python heygen_server.py
   ```

4. Open **http://127.0.0.1:5000**, enter what the avatar should talk about, click **Generate video**. The video appears when ready (usually 1–2 minutes).

## Config

- **Avatar** default: look ID `160e3fd51deb4be180f90a491c4b6c9b` as a **Photo Avatar look** (`talking_photo`). Override with `HEYGEN_AVATAR_ID` in `.env`. If your ID is a Digital Twin / public avatar, set `HEYGEN_AVATAR_TYPE=avatar` in `.env`.
- **Original voice**: The app uses the avatar/look’s **default voice** when HeyGen has one (from List Avatars V2 or from avatar groups’ `default_voice_id`). If none is set, it falls back to a default voice. To use the avatar’s voice, assign a default voice to the look in the HeyGen app if possible, or set `HEYGEN_VOICE_ID` in `.env` to that voice’s ID.
- **Voice**: override with `HEYGEN_VOICE_ID` in `.env` (from [List Voices V2](https://docs.heygen.com/reference/list-voices-v2)).

## API

- **POST /api/video/generate** — Body: `{ "prompt": "what to talk about" }` → returns `{ "video_id": "..." }`.
- **GET /api/video/status/<video_id>** — Returns `{ "status", "video_url", "error" }`. Poll until `status === "completed"`.
