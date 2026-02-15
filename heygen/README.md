# Prompt → Script → Avatar Video

Enter a topic or idea on the homescreen. **Perplexity** writes a ~30-second script, then **HeyGen** renders your avatar speaking it as a video.

```
You type a prompt  →  Perplexity (sonar) writes the script  →  HeyGen generates the video  →  watch it in the browser
```

## Quick start

### 1. Install dependencies

```bash
pip install -r heygen_requirements.txt
```

### 2. Set up `.env`

Create a `.env` file in the project root (or edit the existing one):

```env
HEYGEN_API_KEY=your_heygen_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

- **HeyGen key**: [HeyGen → Settings → API](https://app.heygen.com/settings?nav=API)
- **Perplexity key**: [Perplexity API settings](https://www.perplexity.ai/settings/api)

### 3. Run the server

```bash
python heygen_server.py
```

### 4. Open the app

Go to **http://127.0.0.1:5000** in your browser.

1. Type what the avatar should talk about (e.g. "Introduce our new AI fitness app").
2. Click **Generate video**.
3. Wait — Perplexity writes the script (shown on screen), then HeyGen renders the video (usually 1–2 minutes).
4. Watch the video right in the page.

## Configuration (optional)

All config is via environment variables in `.env`:

| Variable | Default | Description |
|---|---|---|
| `HEYGEN_API_KEY` | *(required)* | Your HeyGen API key |
| `PERPLEXITY_API_KEY` | *(required)* | Your Perplexity API key |
| `HEYGEN_AVATAR_ID` | `160e3fd51deb4be180f90a491c4b6c9b` | Avatar or look ID |
| `HEYGEN_AVATAR_TYPE` | `talking_photo` | `talking_photo` for Photo Avatar looks, `avatar` for Digital Twins / public avatars |
| `HEYGEN_VOICE_ID` | `d572b8091a0843c79028a8c0c06d6dc9` | Voice ID (from [List Voices V2](https://docs.heygen.com/reference/list-voices-v2)) |
| `PERPLEXITY_MODEL` | `sonar` | Perplexity model for script generation |

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/video/generate` | Body: `{ "prompt": "topic" }`. Returns `{ "video_id", "script" }` |
| `GET` | `/api/video/status/<video_id>` | Returns `{ "status", "video_url", "error" }`. Poll until `status === "completed"` |

## Project files

| File | Purpose |
|---|---|
| `heygen_server.py` | Flask backend (Perplexity + HeyGen) |
| `heygen_static/index.html` | Frontend UI |
| `heygen_requirements.txt` | Python dependencies |
| `.env` | API keys (git-ignored) |

## Links

- [HeyGen API Quick Start](https://docs.heygen.com/docs/quick-start)
- [HeyGen Create Video V2](https://docs.heygen.com/reference/create-an-avatar-video-v2)
- [Perplexity API](https://docs.perplexity.ai/)
