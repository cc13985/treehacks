"""
HeyGen text → video. Prompt on homescreen → Perplexity generates ~30s script → avatar speaks it → video.

Quick Start Option C: https://docs.heygen.com/docs/quick-start
Auth: X-API-KEY from HeyGen Settings → API. Set HEYGEN_API_KEY in .env.
Perplexity: PERPLEXITY_API_KEY in .env.
/api/video/generate: prompt → Perplexity script → HeyGen video
"""

import os
from typing import Optional

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__, static_folder="heygen_static")
CORS(app)  # allow cross-origin requests from frontend (port 8080)

HEYGEN_API = "https://api.heygen.com"
API_KEY = (os.environ.get("HEYGEN_API_KEY") or os.environ.get("LIVEAVATAR_API_KEY") or "").strip()

AVATAR_ID = os.environ.get("HEYGEN_AVATAR_ID", "160e3fd51deb4be180f90a491c4b6c9b")
# "talking_photo" = Photo Avatar / avatar look (look_id). "avatar" = Digital Twin / public avatar.
AVATAR_TYPE = os.environ.get("HEYGEN_AVATAR_TYPE", "talking_photo").strip().lower()
if AVATAR_TYPE not in ("avatar", "talking_photo"):
    AVATAR_TYPE = "talking_photo"

DEFAULT_VOICE_ID = os.environ.get("HEYGEN_VOICE_ID", "d572b8091a0843c79028a8c0c06d6dc9")

# Perplexity API key (keep in .env)
PERPLEXITY_API_KEY = (os.environ.get("PERPLEXITY_API_KEY") or "").strip()
PERPLEXITY_MODEL = os.environ.get("PERPLEXITY_MODEL", "sonar")


def _headers():
    return {"X-API-KEY": API_KEY, "Content-Type": "application/json"}


def generate_script_with_perplexity(prompt: str) -> str:
    """
    Uses Perplexity to create a ~30-second spoken monologue script.
    Returns plain text only.
    """
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not set in .env")

    system = (
        "You are a fictional script writer. Your ONLY job is to output the spoken script text. "
        "Do NOT include any commentary, preamble, explanation, notes, citations, "
        "quotation marks, labels like 'Script:', or anything other than the words "
        "the speaker will say out loud. "
        "Write a natural spoken monologue lasting about 30 seconds (70–85 words). "
        "No emojis, no stage directions, no bullet points, no lists. "
        "Output ONLY the raw script text — nothing else."
    )

    body = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 220,
    }

    r = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=30,
    )

    if r.status_code != 200:
        try:
            err = r.json().get("error", {}).get("message", r.text[:300])
        except Exception:
            err = r.text[:300]
        raise RuntimeError(f"Perplexity error: {err}")

    data = r.json()

    try:
        text = data["choices"][0]["message"]["content"].strip()
    except Exception:
        raise RuntimeError("Perplexity returned unexpected format")

    if not text:
        raise RuntimeError("Perplexity returned empty script")

    return text


def get_avatar_default_voice(avatar_id: str) -> Optional[str]:
    """Get the avatar/look's original default voice. Tries List Avatars V2 then avatar groups."""
    # 1) List Avatars V2 (avatars + talking_photos)
    try:
        r = requests.get(f"{HEYGEN_API}/v2/avatars", headers=_headers(), timeout=15)
        if r.status_code == 200:
            data = r.json()
            if not data.get("error"):
                out = data.get("data") or data
                for a in out.get("avatars") or []:
                    if (a.get("avatar_id") or a.get("id")) == avatar_id:
                        vid = a.get("default_voice_id")
                        if vid:
                            return vid
                for t in out.get("talking_photos") or []:
                    if (t.get("talking_photo_id") or t.get("id")) == avatar_id:
                        vid = t.get("default_voice_id")
                        if vid:
                            return vid
    except Exception:
        pass

    # 2) Avatar groups: list groups, then GET /v2/avatar_group/{group_id}/avatars (avatar_list has id + default_voice_id)
    try:
        r = requests.get(f"{HEYGEN_API}/v2/avatar_group.list", headers=_headers(), timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("error"):
            return None
        out = data.get("data") or data
        groups = out.get("avatar_groups") or out.get("groups") or []
        for g in groups:
            gid = g.get("id") or g.get("group_id")
            if not gid:
                continue
            r2 = requests.get(
                f"{HEYGEN_API}/v2/avatar_group/{gid}/avatars",
                headers=_headers(),
                timeout=15,
            )
            if r2.status_code != 200:
                continue
            d2 = r2.json()
            if d2.get("error"):
                continue
            lst = (d2.get("data") or d2).get("avatar_list") or []
            for look in lst:
                if look.get("id") == avatar_id:
                    vid = look.get("default_voice_id")
                    if vid:
                        return vid
    except Exception:
        pass
    return None


def create_video(script: str, avatar_id: str, voice_id: str, character_type: str = None) -> tuple:
    """POST /v2/video/generate — script + avatar/look → (video_id, error_message). One will be None."""
    if not (script and script.strip()):
        return None, "Script is empty"
    ctype = (character_type or AVATAR_TYPE).strip().lower()
    if ctype == "talking_photo":
        character = {"type": "talking_photo", "talking_photo_id": avatar_id}
    else:
        character = {"type": "avatar", "avatar_id": avatar_id}
    payload = {
        "video_inputs": [
            {
                "character": character,
                "voice": {
                    "type": "text",
                    "voice_id": voice_id,
                    "input_text": script.strip(),
                },
                "background": {"type": "color", "value": "#FFFFFF"},
            }
        ],
    }
    try:
        r = requests.post(
            f"{HEYGEN_API}/v2/video/generate",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        try:
            data = r.json()
        except Exception:
            data = {}
        err = data.get("error")
        if isinstance(err, dict):
            err = err.get("message") or err.get("detail") or str(err)
        if r.status_code != 200:
            return None, err or (r.text[:200] if r.text else f"HTTP {r.status_code}")
        if err:
            return None, err
        out = data.get("data") or data
        vid = out.get("video_id")
        return (vid, None) if vid else (None, "No video_id in response")
    except Exception as e:
        return None, str(e)


def video_status(video_id: str) -> dict:
    """GET video status → status, video_url when completed."""
    try:
        r = requests.get(
            f"{HEYGEN_API}/v1/video_status.get",
            params={"video_id": video_id},
            headers=_headers(),
            timeout=15,
        )
        if r.status_code != 200:
            return {"status": "error", "error": r.text or f"HTTP {r.status_code}"}
        data = r.json()
        out = data.get("data") or data
        return {
            "status": out.get("status", "unknown"),
            "video_url": out.get("video_url"),
            "thumbnail_url": out.get("thumbnail_url"),
            "error": out.get("error"),
            "duration": out.get("duration"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.route("/")
def index():
    return send_from_directory("heygen_static", "index.html")


@app.route("/api/video/generate", methods=["POST"])
def api_generate():
    """
    Prompt → Gemini script → HeyGen video.
    Body: { "prompt": "...", optional: avatar_id, voice_id, character_type }
    Returns: { video_id, script }
    """
    if not API_KEY:
        return jsonify({"error": "HEYGEN_API_KEY is not set in .env"}), 500

    body = request.get_json() or {}
    prompt = (body.get("prompt") or body.get("script") or "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # 1) Perplexity generates a ~30-second script
    try:
        script = generate_script_with_perplexity(prompt)
    except Exception as e:
        return jsonify({"error": f"Script generation failed: {str(e)}"}), 500

    # 2) HeyGen renders the video using the generated script
    avatar_id = (body.get("avatar_id") or AVATAR_ID).strip()
    character_type = body.get("character_type") or os.environ.get("HEYGEN_AVATAR_TYPE") or AVATAR_TYPE

    voice_id = body.get("voice_id")
    if voice_id:
        voice_id = voice_id.strip()
    else:
        avatar_voice = get_avatar_default_voice(avatar_id)
        voice_id = (avatar_voice or DEFAULT_VOICE_ID).strip()

    video_id, err = create_video(script, avatar_id, voice_id, character_type=character_type)
    if not video_id:
        msg = err or "HeyGen failed to start video. Check API key and avatar ID."
        return jsonify({"error": msg}), 400

    return jsonify({"video_id": video_id, "script": script})


@app.route("/api/video/status/<video_id>")
def api_status(video_id):
    """Poll status. Returns { status, video_url, error }."""
    if not API_KEY:
        return jsonify({"error": "API key not set"}), 500
    return jsonify(video_status(video_id))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
