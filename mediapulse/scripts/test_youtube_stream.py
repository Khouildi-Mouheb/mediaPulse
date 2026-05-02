import os
import subprocess

from config import AppConfig
from services.audio_utils import ensure_directories


def resolve_audio_url(url: str) -> str:
    result = subprocess.run(
        ["yt-dlp", "-f", "bestaudio", "-g", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()[0]


def capture_chunk(direct_url: str, output_path: str) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        direct_url,
        "-t",
        "10",
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(AppConfig.SAMPLE_RATE),
        output_path,
    ]
    subprocess.run(command, check=True)


def main():
    ensure_directories()
    direct_url = resolve_audio_url(AppConfig.DEFAULT_DIWAN_FM_URL)
    output_path = os.path.join(AppConfig.LIVE_CHUNKS_DIR, "test_diwan.wav")
    capture_chunk(direct_url, output_path)
    size = os.path.getsize(output_path)
    print(f"Saved {output_path} ({size} bytes)")


if __name__ == "__main__":
    main()
