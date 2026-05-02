import os

class AppConfig:
    # Paths
    AUDIO_UPLOAD_DIR = os.getenv("AUDIO_UPLOAD_DIR", "uploads")
    LIVE_CHUNKS_DIR = os.getenv("LIVE_CHUNKS_DIR", "data/live_chunks")
    
    # Default Stream (Sera utilisé par seed.py lors de la création de la base)
    DEFAULT_DIWAN_FM_URL = "https://www.youtube.com/watch?v=NG7ZX42nZKc"
    
    # Audio & Chunking
    CHUNK_SECONDS = 12  # Augmenté de 5s à 12s pour donner plus de contexte
    SAMPLE_RATE = 16000
    
    # Matching Settings
    TEXT_SIMILARITY_THRESHOLD = 0.25
    
    # Redis settings
    LIVE_FINGERPRINT_TTL_SECONDS = 3600
    LIVE_TEXT_MAX_ENTRIES = 720
    
    # Language Detection
    LANGDETECT_MIN_CONFIDENCE = 0.85
    ACCEPTED_LANGUAGES = ["fr", "fr-ca", "fr-fr"]
    
    # Whisper Fallback Model
    WHISPER_MODEL = "small"