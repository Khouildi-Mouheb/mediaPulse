import asyncio
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from elBolbol.mediapulse.config import AppConfig
from elBolbol.mediapulse.models import Channel, MediaDetection, User
from elBolbol.mediapulse.services.audio_utils import cleanup_file, convert_to_wav_16k_mono
from elBolbol.mediapulse.services.text_matching_service import text_matcher
from elBolbol.mediapulse.services.points_service import award_points
from elBolbol.mediapulse.services.redis_fingerprint_store import RedisFingerprintStore


class MediaMatchingService:
    def __init__(self, redis_store: RedisFingerprintStore):
        self.redis_store = redis_store

    async def match_uploaded_audio(
        self, uploaded_file_path: str, user_id: int, db: Session
    ) -> Dict:
        import logging
        import time
        logger = logging.getLogger("mediapulse.matching")
        start_time = time.time()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        converted_path = os.path.join(
            AppConfig.AUDIO_UPLOAD_DIR,
            f"converted_{user_id}_{int(datetime.utcnow().timestamp())}.wav",
        )

        points_earned = award_points(user_id, 10, "scan_attempt", "Scan attempt", db)

        try:
            # Conversion
            conv_start = time.time()
            await asyncio.to_thread(
                convert_to_wav_16k_mono, uploaded_file_path, converted_path
            )
            logger.info(f"⏱️ [User {user_id}] Conversion: {time.time() - conv_start:.2f}s")
            
            # 1. Extraction du texte (Speech-to-Text)
            stt_start = time.time()
            text = await text_matcher.extract_text_with_retry(converted_path)
            logger.info(f"⏱️ [User {user_id}] STT: {time.time() - stt_start:.2f}s - Texte: '{text[:60]}'")
            
            if not text:
                return self._create_failure_response(user_id, points_earned, db, "Audio incompréhensible ou vide.")
                
            if not text_matcher.validate_language(text):
                return self._create_failure_response(user_id, points_earned, db, f"Langue non reconnue/ignorée. Texte: '{text}'")

            # 2. Récupération du corpus Redis (Live streams)
            redis_start = time.time()
            channels = db.query(Channel).filter(Channel.active.is_(True)).all()
            logger.info(f"📻 [User {user_id}] Chaînes actives: {[ch.name for ch in channels]}")
            
            best_similarity = 0.0
            best_channel = None
            best_matched_time = None

            for channel in channels:
                recent_entries = await self.redis_store.get_recent_texts(channel.id, limit=20)
                logger.info(f"📚 [User {user_id}] [{channel.name}] {len(recent_entries)} textes dans Redis")
                
                if not recent_entries:
                    logger.warning(f"⚠️ [User {user_id}] [{channel.name}] Aucun texte dans Redis!")
                    continue
                
                corpus = [entry["text"] for entry in recent_entries]
                    
                similarity = text_matcher.compute_similarity(text, corpus)
                logger.info(f"🔍 [User {user_id}] [{channel.name}] Similarité: {similarity:.4f}")
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_channel = channel
                    best_matched_time = recent_entries[0]["timestamp"]

            logger.info(f"⏱️ [User {user_id}] Redis fetch: {time.time() - redis_start:.2f}s")

            # 3. Vérification de la similarité avec le seuil
            if best_similarity >= AppConfig.TEXT_SIMILARITY_THRESHOLD and best_channel:
                points_earned += award_points(user_id, 20, "scan_detected", "Valid detection", db)
                detection = MediaDetection(
                    user_id=user_id,
                    channel_id=best_channel.id,
                    media_type=best_channel.media_type,
                    confidence=best_similarity,
                    detected=True,
                    matched_time=datetime.fromisoformat(best_matched_time.replace("Z", "+00:00"))
                )
                db.add(detection)
                db.commit()
                total_time = time.time() - start_time
                logger.info(f"✅ [User {user_id}] MATCH: {best_channel.name} ({best_similarity*100:.1f}%) en {total_time:.2f}s")
                return {
                    "detected": True,
                    "media_type": best_channel.media_type,
                    "channel": best_channel.name,
                    "confidence": best_similarity,
                    "matched_time": best_matched_time,
                    "points_earned": points_earned,
                    "message": f"Correspondance trouvée ({best_similarity*100:.1f}%)"
                }

            total_time = time.time() - start_time
            logger.warning(f"❌ [User {user_id}] Pas de match ({best_similarity*100:.1f}% < {AppConfig.TEXT_SIMILARITY_THRESHOLD*100}%) en {total_time:.2f}s")
            return self._create_failure_response(user_id, points_earned, db, f"Similarité faible ({best_similarity*100:.1f}%). Texte: '{text}'")

        finally:
            cleanup_file(uploaded_file_path)
            cleanup_file(converted_path)

    def _create_failure_response(self, user_id: int, points: int, db: Session, message: str) -> Dict:
        detection = MediaDetection(
            user_id=user_id,
            channel_id=None,
            media_type=None,
            confidence=0.0,
            detected=False,
        )
        db.add(detection)
        db.commit()
        return {
            "detected": False,
            "media_type": None,
            "channel": None,
            "confidence": 0.0,
            "matched_time": None,
            "points_earned": points,
            "message": message
        }

    async def match_precomputed_hashes(
        self, hashes: list[Tuple[str, float]], user_id: int, db: Session
    ) -> Dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        hash_values = [hash_value for hash_value, _t1 in hashes]
        hash_entries = await self.redis_store.get_hash_entries(hash_values)

        best_votes = 0
        best_entry: Optional[Dict] = None
        vote_counts: Dict[Tuple[int, int], int] = {}
        for hash_value, query_time in hashes:
            entries = hash_entries.get(hash_value, [])
            for entry in entries:
                entry_time = datetime.fromisoformat(
                    entry["timestamp"].replace("Z", "+00:00")
                ).timestamp() + float(entry.get("anchor_time", 0.0))
                offset = entry_time - query_time
                offset_bin = int(round(offset / AppConfig.PEAK_HASH_TIME_BIN))
                key = (int(entry["channel_id"]), offset_bin)
                vote_counts[key] = vote_counts.get(key, 0) + 1
                if vote_counts[key] > best_votes:
                    best_votes = vote_counts[key]
                    best_entry = entry

        confidence = 0.0
        if hashes:
            confidence = best_votes / float(len(hashes))

        points_earned = 0
        points_earned += award_points(
            user_id, 10, "scan_attempt", "Scan attempt", db
        )

        if (
            best_entry
            and best_votes >= AppConfig.PEAK_HASH_MIN_VOTES
            and confidence >= AppConfig.PEAK_HASH_MATCH_RATIO
        ):
            channel = (
                db.query(Channel)
                .filter(Channel.id == best_entry.get("channel_id"))
                .first()
            )
            points_earned += award_points(
                user_id, 20, "scan_detected", "Valid detection", db
            )
            detection = MediaDetection(
                user_id=user_id,
                channel_id=best_entry.get("channel_id"),
                media_type=best_entry.get("media_type"),
                confidence=confidence,
                detected=True,
                matched_time=datetime.fromisoformat(
                    best_entry.get("timestamp").replace("Z", "+00:00")
                ),
            )
            db.add(detection)
            db.commit()
            return {
                "detected": True,
                "media_type": best_entry.get("media_type"),
                "channel": channel.name if channel else None,
                "confidence": confidence,
                "matched_time": best_entry.get("timestamp"),
                "points_earned": points_earned,
            }

        detection = MediaDetection(
            user_id=user_id,
            channel_id=None,
            media_type=None,
            confidence=0.0,
            detected=False,
        )
        db.add(detection)
        db.commit()
        return {
            "detected": False,
            "media_type": None,
            "channel": None,
            "confidence": 0.0,
            "matched_time": None,
            "points_earned": points_earned,
        }
