# Plan d'Intégration Speech-to-Text (STT) et Text Matching pour MediaPulse

Ce document détaille la feuille de route pour faire évoluer MediaPulse d'un système de reconnaissance par empreinte audio (Audio Fingerprinting type Shazam) vers un système d'analyse sémantique et de détection de mots-clés exacts.

---

## Phase 1 : Choix Technologiques et Architecture

Actuellement, l'application utilise l'analyse des fréquences (FFT via `fftea`). Pour détecter du texte, nous devons introduire un moteur de reconnaissance vocale (ASR).

1. **Choix du modèle ASR Backend :**
   - **Recommandation :** `faster-whisper` (implémentation optimisée du modèle Whisper d'OpenAI).
   - **Avantages :** Très précis, gère de multiples langues, open-source, et plus rapide que le modèle standard.
2. **Choix de l'architecture :**
   - L'extraction de texte (transcription) se fera côté **Backend** pour des raisons de performance.
   - L'application mobile (Flutter) n'enverra plus des hash calculés localement, mais directement des fragments audio (chunks `.wav`) au backend.

---

## Phase 2 : Mise à jour de la Base de Données (SQLAlchemy)

Il faut définir ce que le système doit chercher (les mots-clés).

1. **Créer un modèle `KeywordCampaign` ou `TargetKeyword` :**
   - Colonnes : `id`, `mot_cle` (ex: "Coca-Cola", "Promotion spéciale"), `points_recompense`, `actif`.
2. **Mettre à jour le modèle `Channel` :**
   - Ajouter un flag `monitoring_type` (ex: `audio_hash` vs `text_keyword`) pour savoir comment le flux doit être analysé par le `StreamManager`.
3. **Créer un modèle `TextMatchEvent` :**
   - Pour enregistrer quand un utilisateur ou un flux en direct (OOH/Radio) a matché un mot-clé précis (pour l'analytique et l'attribution des points).

---

## Phase 3 : Développement du Pipeline Backend (Python / FastAPI)

C'est le cœur de la transformation.

1. **Création du `TranscriptionService` :**
   - Créer `services/transcription_service.py`.
   - Instancier le modèle Whisper (`WhisperModel("base")` ou `"small"`).
   - Écrire une fonction `transcribe_audio(file_path)` qui retourne le texte brut.
2. **Création du `KeywordMatchingService` :**
   - Écrire un service qui prend le texte transcrit et vérifie s'il contient les mots-clés de la base de données (utilisation d'expressions régulières `re` ou recherche textuelle simple).
3. **Nouveaux Endpoints dans `routers/media.py` :**
   - Créer un endpoint `/detect-text-media` qui accepte un fichier `UploadFile`.
   - **Workflow de l'endpoint :** 
     1. Sauvegarder le `.wav` temporairement.
     2. Appeler `TranscriptionService.transcribe_audio`.
     3. Passer le texte à `KeywordMatchingService`.
     4. Si match -> attribuer les points (`points_service.py`) et retourner le résultat au mobile.

---

## Phase 4 : Adaptation de l'Application Mobile (Flutter)

L'application Flutter doit changer sa façon de traiter le son.

1. **Modification de `recording_screen.dart` :**
   - **Supprimer** ou ignorer l'étape `_fingerprintService.extractHashes(filePath)`.
   - **Modifier** `_processChunk(String filePath)` pour qu'il envoie le fichier `.wav` brut généré par le microphone (les chunks de 10 secondes) via une requête HTTP Multipart au nouvel endpoint `/detect-text-media`.
2. **Mise à jour de `api_service.dart` :**
   - Ajouter une méthode `detectTextFromAudio(File audioFile, int userId)` qui gère l'upload de fichier vers le backend.
3. **Optimisation réseau :**
   - Compresser légèrement le fichier `.wav` (ex: format `.m4a` ou baisse du bitrate) pour ne pas saturer la connexion de l'utilisateur, tout en gardant une qualité suffisante pour Whisper (16kHz est parfait).

---

## Phase 5 : Gestion des Flux en Direct (`StreamManager`)

Si vous écoutez des flux radio ou YouTube (via `channels.py`), il faut les transcrire en temps réel.

1. **Mise à jour du worker de flux :**
   - Actuellement, le système utilise `ffmpeg` pour extraire 10 secondes et calcule les hashs.
   - **Nouveau flux :** `ffmpeg` extrait 10 secondes -> le `.wav` est envoyé au `TranscriptionService` -> Recherche de mots-clés -> Sauvegarde dans `TextMatchEvent` si un mot-clé est détecté.
2. **Gérer les mots coupés (Chevauchement / Overlapping) :**
   - **Problème :** Si un mot-clé est "Bonjour", et que le chunk 1 finit par "Bon" et le chunk 2 commence par "jour", Whisper ne le verra pas.
   - **Solution :** Implémenter un chevauchement (Overlap). Par exemple, analyser les secondes 0 à 10, puis 8 à 18, puis 16 à 26.

---

## Phase 6 : Optimisation et Déploiement

Le passage au Speech-to-Text est beaucoup plus gourmand en ressources matérielles que le hachage d'empreintes.

1. **Gestion de la latence :**
   - Transcrire 10 secondes d'audio peut prendre 1 à 3 secondes selon le CPU. Il faut s'assurer que les requêtes Flutter ont un Timeout assez long.
   - Envisager d'utiliser des tâches en arrière-plan (ex: Celery) si la charge est trop élevée.
2. **Besoins d'Hébergement / Déploiement :**
   - Un modèle Whisper (même "base") consomme beaucoup de RAM. 
   - Si possible, déployer le backend sur une machine avec un petit GPU (Nvidia) ou un CPU très performant avec suffisamment de RAM (min 8 Go).
3. **Tests de précision :**
   - Vérifier si Whisper comprend bien l'accent local (ex: Arabe tunisien, Français) selon la région de vos utilisateurs.

---

## Résumé des Livrables Attendus

- [ ] `models/keyword.py` (Nouveau)
- [ ] `services/transcription_service.py` (Nouveau)
- [ ] `routers/media.py` (Mise à jour avec `/detect-text-media`)
- [ ] Flutter `recording_screen.dart` (Envoi du fichier au lieu du hash)
- [ ] `stream_manager.py` (Transcription des canaux Live)