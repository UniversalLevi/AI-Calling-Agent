import os
import uuid
import tempfile
from flask import Flask, request, jsonify, send_from_directory
import subprocess
from pathlib import Path
import openai
import whisper
from gtts import gTTS
from pydub import AudioSegment

app = Flask(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY environment variable")
openai.api_key = OPENAI_API_KEY

print("Loading Whisper model...")
whisper_model = whisper.load_model("small")
print("Whisper loaded.")

OUT_DIR = Path("tts_out")
OUT_DIR.mkdir(exist_ok=True)

def convert_to_wav(in_path: str, out_path: str):
    cmd = ["ffmpeg", "-y", "-i", in_path, "-ar", "16000", "-ac", "1", out_path]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@app.route("/process_audio", methods=["POST"])
def process_audio():
    if "audio" not in request.files:
        return jsonify({"error": "no audio file"}), 400

    f = request.files["audio"]
    tmp_dir = tempfile.mkdtemp(prefix="callbot_")
    in_path = os.path.join(tmp_dir, f.filename or "input_audio")
    f.save(in_path)

    wav_path = os.path.join(tmp_dir, "in.wav")
    convert_to_wav(in_path, wav_path)

    result = whisper_model.transcribe(wav_path)
    transcript = result.get("text", "").strip()

    system_prompt = "You are a polite AI calling agent. Keep responses short (1–2 sentences)."
    user_prompt = f"Customer said: '{transcript}'. How should the agent reply?"

    chat_resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=200,
        temperature=0.3,
    )
    reply_text = chat_resp["choices"][0]["message"]["content"].strip()

    tts_filename = f"{uuid.uuid4().hex}.mp3"
    tts_path = OUT_DIR / tts_filename
    tts = gTTS(text=reply_text, lang="en")
    tts.save(str(tts_path))

    wav_out = OUT_DIR / (tts_filename.replace(".mp3", ".wav"))
    AudioSegment.from_mp3(str(tts_path)).export(str(wav_out), format="wav")

    return jsonify({
        "transcript": transcript,
        "reply_text": reply_text,
        "tts_filename": tts_filename,
        "tts_wav": str(wav_out),
    })

@app.route("/tts/<path:filename>")
def serve_tts(filename):
    return send_from_directory(OUT_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
