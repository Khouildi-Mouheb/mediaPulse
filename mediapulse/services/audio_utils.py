import logging
import os
import subprocess
import time

from elBolbol.mediapulse.config import AppConfig

_logger = logging.getLogger("mediapulse.audio")


def ensure_directories() -> None:
    os.makedirs(AppConfig.AUDIO_UPLOAD_DIR, exist_ok=True)
    os.makedirs(AppConfig.LIVE_CHUNKS_DIR, exist_ok=True)


def convert_to_wav_16k_mono(input_path: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(AppConfig.SAMPLE_RATE),
        output_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        _logger.error("ffmpeg convert error: %s", result.stderr)
        result.check_returncode()


def capture_stream_chunk(direct_audio_url: str, output_path: str, seconds: int) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        direct_audio_url,
        "-t",
        str(seconds),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(AppConfig.SAMPLE_RATE),
        output_path,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        _logger.error("ffmpeg capture error (URL: %s): %s", direct_audio_url, result.stderr)
        result.check_returncode()


def cleanup_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as exc:
        _logger.warning("Failed to delete file %s: %s", path, exc)


def cleanup_old_files(directory: str, max_age_seconds: int) -> None:
    now = time.time()
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if not os.path.isfile(file_path):
                continue
            if now - os.path.getmtime(file_path) > max_age_seconds:
                cleanup_file(file_path)
    except FileNotFoundError:
        return
