"""Audio splitting and transcription via Whisper-compatible API.

Splits audio files at speech pauses, transcribes each chunk, and reassembles the text.
Adapted from ancroo-stack service-tools module.
"""

import logging
import os
import tempfile

import requests
import urllib3
from pydub import AudioSegment
from pydub.silence import split_on_silence

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "server": {
        "url": "http://speaches:8000/v1/audio/transcriptions",
        "token": "",
        "disable_ssl_verify": False,
    },
    "whisper": {
        "language": "de",
        "model": "",
        "response_format": "text",
    },
    "splitting": {
        "min_silence_duration_ms": 700,
        "silence_threshold_dbfs": -40,
        "min_chunk_duration_s": 20,
        "max_chunk_duration_s": 120,
        "overlap_ms": 200,
    },
}


def split_audio(audio: AudioSegment, config: dict) -> list[AudioSegment]:
    """Split audio on silence, merge small chunks, enforce max duration."""
    split_cfg = config["splitting"]

    chunks = split_on_silence(
        audio,
        min_silence_len=split_cfg["min_silence_duration_ms"],
        silence_thresh=split_cfg["silence_threshold_dbfs"],
        keep_silence=300,
    )

    if not chunks:
        chunks = [audio]

    # Merge small chunks until they reach min_chunk_duration
    min_ms = split_cfg["min_chunk_duration_s"] * 1000
    max_ms = split_cfg["max_chunk_duration_s"] * 1000
    merged = []
    current = chunks[0]
    for chunk in chunks[1:]:
        combined = current + chunk
        if len(current) < min_ms and len(combined) <= max_ms:
            current = combined
        else:
            merged.append(current)
            current = chunk
    merged.append(current)

    # Force-split any chunks that exceed max duration
    final_chunks = []
    for chunk in merged:
        if len(chunk) > max_ms:
            for i in range(0, len(chunk), max_ms):
                final_chunks.append(chunk[i : i + max_ms])
        else:
            final_chunks.append(chunk)

    # Apply overlap
    overlap_ms = split_cfg["overlap_ms"]
    if overlap_ms > 0 and len(final_chunks) > 1:
        overlapped = [final_chunks[0]]
        for i in range(1, len(final_chunks)):
            prev_tail = final_chunks[i - 1][-overlap_ms:]
            overlapped.append(prev_tail + final_chunks[i])
        final_chunks = overlapped

    return final_chunks


def transcribe_chunk(
    chunk: AudioSegment, chunk_index: int, total: int, config: dict, tmpdir: str
) -> str:
    """Export chunk to file and send to Whisper API. Returns transcribed text."""
    server_cfg = config["server"]
    whisper_cfg = config["whisper"]

    chunk_path = os.path.join(tmpdir, f"chunk_{chunk_index:04d}.wav")
    chunk.export(chunk_path, format="wav")

    headers = {}
    if server_cfg["token"]:
        headers["Authorization"] = f"Bearer {server_cfg['token']}"

    data = {}
    if whisper_cfg["language"]:
        data["language"] = whisper_cfg["language"]
    if whisper_cfg["model"]:
        data["model"] = whisper_cfg["model"]
    if whisper_cfg["response_format"]:
        data["response_format"] = whisper_cfg["response_format"]

    verify_ssl = not server_cfg["disable_ssl_verify"]

    with open(chunk_path, "rb") as audio_file:
        files = {"file": (f"chunk_{chunk_index:04d}.wav", audio_file, "audio/wav")}

        try:
            response = requests.post(
                server_cfg["url"],
                headers=headers,
                data=data,
                files=files,
                verify=verify_ssl,
                timeout=300,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Chunk %d/%d transcription failed: %s", chunk_index + 1, total, e)
            return ""

    if whisper_cfg["response_format"] == "text":
        return response.text.strip()

    try:
        result = response.json()
        return result.get("text", "").strip()
    except (ValueError, KeyError):
        return response.text.strip()
