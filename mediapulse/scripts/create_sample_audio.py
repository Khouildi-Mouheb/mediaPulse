import os

import numpy as np
import soundfile as sf

from config import AppConfig
from services.audio_utils import ensure_directories


def main():
    ensure_directories()
    sample_rate = AppConfig.SAMPLE_RATE
    duration = 5
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = 0.2 * np.sin(2 * np.pi * 440 * t)
    output_path = os.path.join(AppConfig.AUDIO_UPLOAD_DIR, "sample.wav")
    sf.write(output_path, tone, sample_rate)
    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
