"""Audio transcription plugin — accepts base64 audio, splits on silence, transcribes via Whisper."""

import base64
import os
import tempfile

from audio_transcribe import DEFAULT_CONFIG, split_audio, transcribe_chunk

from pydub import AudioSegment


def run(input: dict) -> dict:
    audio_b64 = input.get("audio_base64", "")
    if not audio_b64:
        raise ValueError("Missing required field: audio_base64")

    # Build config from defaults + input overrides
    config = {section: dict(values) for section, values in DEFAULT_CONFIG.items()}

    # Allow overriding server URL via environment variable
    whisper_url = os.environ.get("WHISPER_BASE_URL")
    if whisper_url:
        config["server"]["url"] = whisper_url

    # Apply input overrides
    if input.get("language"):
        config["whisper"]["language"] = input["language"]
    if input.get("model"):
        config["whisper"]["model"] = input["model"]
    if input.get("response_format"):
        config["whisper"]["response_format"] = input["response_format"]

    # Decode audio and transcribe
    audio_bytes = base64.b64decode(audio_b64)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write audio to temp file for pydub to load
        input_path = os.path.join(tmpdir, "input_audio")
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        audio = AudioSegment.from_file(input_path)
        duration_s = len(audio) / 1000

        chunks = split_audio(audio, config)

        texts = []
        for i, chunk in enumerate(chunks):
            text = transcribe_chunk(chunk, i, len(chunks), config, tmpdir)
            if text:
                texts.append(text)

    return {
        "result": " ".join(texts),
        "duration_s": round(duration_s, 1),
        "chunks_count": len(chunks),
    }
