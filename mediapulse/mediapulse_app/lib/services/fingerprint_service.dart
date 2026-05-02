import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:fftea/fftea.dart';

class FingerprintService {
  static const int sampleRate = 16000;
  static const int nFft = 2048;
  static const int hopLength = 512;
  static const double minAmplitudeDb = -45.0;
  static const int neighborhoodFreq = 20;
  static const int neighborhoodTime = 20;
  static const double targetZoneSeconds = 3.0;
  static const int targetZoneFreqBins = 60;
  static const int fanout = 6;
  static const int maxPeaks = 200;
  static const int freqBin = 2;
  static const double timeBin = 0.1;

  Future<List<List<dynamic>>> extractHashes(String pcmFilePath) async {
    final file = File(pcmFilePath);
    if (!await file.exists()) return [];

    final bytes = await file.readAsBytes();
    if (bytes.isEmpty) return [];

    // Parse 16-bit PCM to double
    final audio = <double>[];
    final byteData = ByteData.view(bytes.buffer);
    for (int i = 0; i < bytes.length; i += 2) {
      if (i + 1 < bytes.length) {
        final sample = byteData.getInt16(i, Endian.little);
        audio.add(sample / 32768.0); // Normalize to [-1.0, 1.0]
      }
    }

    if (audio.isEmpty) return [];

    // 1. Calculate STFT
    final stft = STFT(nFft, Window.hanning(nFft));
    final specDb = <List<double>>[];
    
    // Process audio in chunks of hopLength
    // Librosa STFT does center padding by default. To approximate, we pad:
    final paddedAudio = List<double>.filled(nFft ~/ 2, 0.0) + audio + List<double>.filled(nFft ~/ 2, 0.0);
    
    double maxGlobal = 0.0;
    
    for (int i = 0; i <= paddedAudio.length - nFft; i += hopLength) {
      final chunk = paddedAudio.sublist(i, i + nFft);
      // fftea STFT run method:
      List<double> magnitudes = [];
      stft.run(chunk, (Float64x2List f) {
        final m = f.discardConjugates().magnitudes();
        magnitudes = m.toList();
      });
      
      for (final mag in magnitudes) {
        if (mag > maxGlobal) maxGlobal = mag;
      }
      specDb.add(magnitudes);
    }

    if (maxGlobal == 0.0) maxGlobal = 1e-10;

    // Convert to dB relative to max
    for (int i = 0; i < specDb.length; i++) {
      for (int j = 0; j < specDb[i].length; j++) {
        double val = specDb[i][j];
        if (val < 1e-10) val = 1e-10;
        specDb[i][j] = 20 * (log(val / maxGlobal) / ln10);
      }
    }

    // 2. 2D Maximum Filter (Peaks extraction)
    final numFrames = specDb.length;
    final numBins = specDb.isNotEmpty ? specDb[0].length : 0;
    
    List<Peak> peaks = [];

    for (int t = 0; t < numFrames; t++) {
      for (int f = 0; f < numBins; f++) {
        final val = specDb[t][f];
        if (val < minAmplitudeDb) continue;

        bool isMax = true;
        
        // Check neighborhood
        int tStart = max(0, t - neighborhoodTime ~/ 2);
        int tEnd = min(numFrames - 1, t + neighborhoodTime ~/ 2);
        int fStart = max(0, f - neighborhoodFreq ~/ 2);
        int fEnd = min(numBins - 1, f + neighborhoodFreq ~/ 2);

        for (int nt = tStart; nt <= tEnd; nt++) {
          for (int nf = fStart; nf <= fEnd; nf++) {
            if (nt == t && nf == f) continue;
            if (specDb[nt][nf] >= val) {
              isMax = false;
              break;
            }
          }
          if (!isMax) break;
        }

        if (isMax) {
          peaks.add(Peak(f, t, val));
        }
      }
    }

    // 3. Keep top N peaks
    if (peaks.length > maxPeaks) {
      peaks.sort((a, b) => b.amplitude.compareTo(a.amplitude));
      peaks = peaks.sublist(0, maxPeaks);
    }
    
    // Sort peaks by time
    peaks.sort((a, b) => a.timeIndex.compareTo(b.timeIndex));

    // 4. Combinatorial Hashing
    List<List<dynamic>> hashes = [];
    final timeScale = hopLength / sampleRate;
    
    for (int i = 0; i < peaks.length; i++) {
      final p1 = peaks[i];
      final t1 = p1.timeIndex * timeScale;
      int pairs = 0;

      for (int j = i + 1; j < peaks.length; j++) {
        final p2 = peaks[j];
        final t2 = p2.timeIndex * timeScale;
        final dt = t2 - t1;

        if (dt <= 0) continue;
        if (dt > targetZoneSeconds) break;
        if ((p2.freqIndex - p1.freqIndex).abs() > targetZoneFreqBins) continue;

        final f1Bin = p1.freqIndex ~/ freqBin;
        final f2Bin = p2.freqIndex ~/ freqBin;
        final dtBin = (dt / timeBin).round();

        final hashValue = "$f1Bin|$f2Bin|$dtBin";
        hashes.add([hashValue, t1]);

        pairs++;
        if (pairs >= fanout) break;
      }
    }

    return hashes;
  }
}

class Peak {
  final int freqIndex;
  final int timeIndex;
  final double amplitude;

  Peak(this.freqIndex, this.timeIndex, this.amplitude);
}
