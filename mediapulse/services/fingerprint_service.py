from typing import List, Tuple

import librosa
import numpy as np
from scipy.ndimage import maximum_filter

from config import AppConfig


class FingerprintService:
    def extract_peak_hashes(self, file_path: str) -> List[Tuple[str, float]]:
        y, sr = librosa.load(file_path, sr=AppConfig.SAMPLE_RATE, mono=True)
        if y.size == 0:
            return []

        spec = np.abs(
            librosa.stft(
                y,
                n_fft=AppConfig.PEAK_HASH_N_FFT,
                hop_length=AppConfig.PEAK_HASH_HOP_LENGTH,
            )
        )
        spec_db = librosa.amplitude_to_db(spec, ref=np.max)

        local_max = maximum_filter(
            spec_db,
            size=(
                AppConfig.PEAK_HASH_NEIGHBORHOOD_FREQ,
                AppConfig.PEAK_HASH_NEIGHBORHOOD_TIME,
            ),
        )
        peak_mask = (spec_db == local_max) & (
            spec_db >= AppConfig.PEAK_HASH_MIN_AMPLITUDE_DB
        )
        peak_coords = np.argwhere(peak_mask)
        if peak_coords.size == 0:
            return []

        peak_values = spec_db[peak_coords[:, 0], peak_coords[:, 1]]
        if peak_coords.shape[0] > AppConfig.PEAK_HASH_MAX_PEAKS:
            strongest = np.argsort(peak_values)[-AppConfig.PEAK_HASH_MAX_PEAKS :]
            peak_coords = peak_coords[strongest]

        peak_coords = peak_coords[np.argsort(peak_coords[:, 1])]
        time_scale = AppConfig.PEAK_HASH_HOP_LENGTH / float(sr)
        peak_times = peak_coords[:, 1] * time_scale

        hashes: List[Tuple[str, float]] = []
        target_time = AppConfig.PEAK_HASH_TARGET_ZONE_SECONDS
        target_freq = AppConfig.PEAK_HASH_TARGET_ZONE_FREQ_BINS
        fanout = AppConfig.PEAK_HASH_FANOUT
        freq_bin = max(1, AppConfig.PEAK_HASH_FREQ_BIN)
        time_bin = max(0.001, AppConfig.PEAK_HASH_TIME_BIN)

        for idx, (f1, _t1_index) in enumerate(peak_coords):
            t1 = peak_times[idx]
            pairs = 0
            for j in range(idx + 1, peak_coords.shape[0]):
                f2, _t2_index = peak_coords[j]
                dt = peak_times[j] - t1
                if dt <= 0:
                    continue
                if dt > target_time:
                    break
                if abs(int(f2) - int(f1)) > target_freq:
                    continue

                f1_bin = int(f1 // freq_bin)
                f2_bin = int(f2 // freq_bin)
                dt_bin = int(round(dt / time_bin))
                hash_value = f"{f1_bin}|{f2_bin}|{dt_bin}"
                hashes.append((hash_value, float(t1)))

                pairs += 1
                if pairs >= fanout:
                    break

        return hashes
