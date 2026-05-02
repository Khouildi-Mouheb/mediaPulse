import logging
import asyncio
import speech_recognition as sr
from langdetect import detect_langs
from faster_whisper import WhisperModel
from sklearn.feature_extraction.text import TfidfVectorizer
from elBolbol.mediapulse.config import AppConfig

logger = logging.getLogger(__name__)

class TextMatchingService:
    def __init__(self):
        # 1. Configuration Google Speech Recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 2000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # 2. Initialisation de Whisper (Fallback)
        # Le modèle "small" est un bon compromis entre précision (fr) et vitesse CPU
        self.whisper_model = WhisperModel(AppConfig.WHISPER_MODEL, device="cpu", compute_type="int8")
        

    async def extract_text_with_retry(self, audio_path: str, max_retries: int = 3) -> str:
        """Extrait le texte avec Retry Exponential Backoff et Fallback Whisper."""
        
        # Lecture audio dans un thread séparé pour ne pas bloquer l'Event Loop
        def read_audio():
            with sr.AudioFile(audio_path) as source:
                return self.recognizer.record(source)
                
        audio_data = await asyncio.to_thread(read_audio)
        
        # Essai avec Google STT (avec gestion du rate-limit)
        for attempt in range(max_retries):
            try:
                # Appel réseau bloquant isolé dans un thread
                text = await asyncio.to_thread(
                    self.recognizer.recognize_google, audio_data, language="fr-FR"
                )
                if text:
                    return text
            except sr.UnknownValueError:
                logger.warning("Google STT : Audio incompréhensible. Passage au fallback Whisper.")
                break  # L'audio est mauvais, inutile de retry Google
            except sr.RequestError as e:
                logger.error(f"Erreur API Google (Rate Limit potentiel): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponentiel (1s, 2s, 4s...)
                    continue
        
        # Fallback sur Whisper local si Google échoue
        logger.info("Déclenchement du fallback Whisper...")
        
        def transcribe_whisper():
            return self.whisper_model.transcribe(audio_path, language="fr", beam_size=5)
            
        segments, _ = await asyncio.to_thread(transcribe_whisper)
        text = " ".join([segment.text for segment in segments])
        return text.strip()

    def validate_language(self, text: str) -> bool:
        """Accepte toutes les langues - pas de validation."""
        if not text or len(text.strip()) == 0:
            return False
        return True
        
    def compute_similarity(self, target_text: str, corpus: list[str]) -> float:
        """Calcule la similarité Cosine. Instancie le vectorizer localement pour être thread-safe."""
        if not corpus or not target_text:
            return 0.0
            
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=1000,
            lowercase=True,
            min_df=1
        )
            
        all_texts = [target_text] + corpus
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        cosine_similarities = (tfidf_matrix[0:1] * tfidf_matrix[1:].T).toarray()[0]
        
        return float(cosine_similarities.max()) if len(cosine_similarities) > 0 else 0.0

# Instance globale pour partager le modèle en mémoire (évite de recharger Whisper à chaque appel)
text_matcher = TextMatchingService()