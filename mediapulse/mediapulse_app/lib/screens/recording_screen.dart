import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import 'package:flutter/animation.dart';

class RecordingScreen extends StatefulWidget {
  final User user;

  const RecordingScreen({super.key, required this.user});

  @override
  State<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends State<RecordingScreen> with TickerProviderStateMixin {
  final AudioRecorder _audioRecorder = AudioRecorder();
  final ApiService _apiService = ApiService();
  
  bool _isRecording = false;
  Timer? _chunkTimer;
  Timer? _demoTimer; // Pour le mode démo
  int _chunkDurationSeconds = 12;
  String? _lastResult;
  String? _detectedChannel;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  bool _isDemo = true; // Mode démo activé par défaut

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);
    
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _chunkTimer?.cancel();
    _demoTimer?.cancel();
    _audioRecorder.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    try {
      setState(() {
        _isRecording = true;
        _detectedChannel = null;
        _lastResult = "En train d'écouter...";
      });

      if (_isDemo) {
        // Mode démo - affiche les résultats après 5 secondes
        _demoTimer = Timer(const Duration(seconds: 5), () {
          if (mounted) {
            setState(() {
              _detectedChannel = "Diwan FM";
              _lastResult = "✅ Match trouvé: Diwan FM\n💰 Points gagnés: 30\nCorrespondance trouvée (87.3%)";
            });
          }
        });
      } else {
        // Mode réel - enregistre l'audio
        if (await _audioRecorder.hasPermission()) {
          await _recordChunk();
          
          // Start timer to record chunks repeatedly
          _chunkTimer = Timer.periodic(Duration(seconds: _chunkDurationSeconds), (timer) async {
            await _recordChunk();
          });
        } else {
          setState(() {
            _lastResult = "Permission microphone refusée";
          });
        }
      }
    } catch (e) {
      print('Error starting recording: $e');
      setState(() {
        _isRecording = false;
        _lastResult = "Erreur: $e";
      });
    }
  }

  Future<void> _recordChunk() async {
    // If already recording from a previous chunk, stop it to get the file
    if (await _audioRecorder.isRecording()) {
      final path = await _audioRecorder.stop();
      if (path != null) {
        _processChunk(path);
      }
    }

    // Start new chunk
    final directory = await getTemporaryDirectory();
    final String filePath = '${directory.path}/chunk_${DateTime.now().millisecondsSinceEpoch}.wav';
    
    await _audioRecorder.start(
      const RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000, numChannels: 1),
      path: filePath,
    );
  }

  Future<void> _processChunk(String filePath) async {
    print('Processing chunk: $filePath');
    
    // Envoyer le fichier audio brut au backend pour la transcription STT
    print('Sending audio file to backend for STT...');
    
    // Utilisation propre de l'ApiService existant au lieu d'une requête brute codée en dur
    final result = await _apiService.detectMedia(filePath, widget.user.id ?? 0);
    
    if (mounted) {
      setState(() {
        if (result != null) {
          // Mettre à jour la chaîne détectée si match trouvé
          if (result['detected'] == true && result['channel'] != null) {
            _detectedChannel = result['channel'];
            _lastResult = "✅ Match trouvé: ${result['channel']}\n💰 Points gagnés: ${result['points_earned']}";
          } else {
            // Si pas de match, afficher "Je ne sais pas"
            _detectedChannel = "Je ne sais pas";
            // Affiche le diagnostic venant du backend s'il existe
            final msg = result['message'];
            _lastResult = (msg != null && msg.toString().isNotEmpty) 
                ? "❌ Non détecté : $msg" 
                : "❌ Aucun match trouvé pour ce segment.";
          }
        } else {
          _detectedChannel = "Erreur de connexion";
          _lastResult = "⚠️ Impossible de contacter le serveur. (Délai d'attente dépassé ou erreur réseau)";
        }
      });
    }
    
    // Clean up file after sending
    try {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
      }
    } catch (e) {
      print('Error deleting temp file: $e');
    }
  }

  Future<void> _stopRecording() async {
    _chunkTimer?.cancel();
    _demoTimer?.cancel();
    if (await _audioRecorder.isRecording()) {
      final path = await _audioRecorder.stop();
      if (path != null) {
        _processChunk(path);
      }
    }
    setState(() {
      _isRecording = false;
      _detectedChannel = null;
      _lastResult = "Enregistrement arrêté.";
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const Text(
            'Reconnaissance Audio',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF111827)),
          ),
          const SizedBox(height: 16),
          const Text(
            "Appuyez pour commencer à écouter l'environnement et gagner des points.",
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16, color: Color(0xFF6B7280)),
          ),
          const SizedBox(height: 48),
          
          // En train d'écouter indicator with pulsing dot
          if (_isRecording)
            Column(
              children: [
                ScaleTransition(
                  scale: _pulseAnimation,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.redAccent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.redAccent, width: 2),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 10,
                          height: 10,
                          decoration: const BoxDecoration(
                            color: Colors.redAccent,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Flexible(
                          child: Text(
                            '🎙️ En train d\'écouter${_detectedChannel != null ? ': $_detectedChannel' : '...'}',
                            style: const TextStyle(
                              color: Colors.redAccent,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          
          // Microphone Button
          GestureDetector(
            onTap: _isRecording ? _stopRecording : _startRecording,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: 150,
              height: 150,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _isRecording ? Colors.redAccent : const Color(0xFF6B4EFF),
                boxShadow: [
                  BoxShadow(
                    color: (_isRecording ? Colors.redAccent : const Color(0xFF6B4EFF)).withOpacity(0.4),
                    blurRadius: _isRecording ? 30 : 15,
                    spreadRadius: _isRecording ? 10 : 2,
                  ),
                ],
              ),
              child: Icon(
                _isRecording ? Icons.stop : Icons.mic,
                color: Colors.white,
                size: 64,
              ),
            ),
          ),
          
          const SizedBox(height: 48),
          
          // Result Box
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFE5E7EB)),
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 10, offset: const Offset(0, 4))],
            ),
            child: Column(
              children: [
                const Text('Statut de la détection', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF111827))),
                const SizedBox(height: 12),
                Text(
                  _lastResult ?? "Prêt à enregistrer",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _lastResult != null && _lastResult!.contains("Match") ? const Color(0xFF4ade80) : const Color(0xFF6B7280),
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

