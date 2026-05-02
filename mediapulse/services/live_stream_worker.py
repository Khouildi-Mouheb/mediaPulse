import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional
import json

import yt_dlp

from elBolbol.mediapulse.config import AppConfig
from elBolbol.mediapulse.services.audio_utils import capture_stream_chunk, cleanup_old_files
from elBolbol.mediapulse.services.text_matching_service import text_matcher
from elBolbol.mediapulse.services.redis_fingerprint_store import RedisFingerprintStore

_logger = logging.getLogger("mediapulse.live_worker")


class LiveStreamWorker:
    def __init__(
        self,
        channel_id: int,
        name: str,
        media_type: str,
        source_type: str,
        source_url: str,
        redis_store: RedisFingerprintStore,
    ):
        self.channel_id = channel_id
        self.name = name
        self.media_type = media_type
        self.source_type = source_type
        self.source_url = source_url
        self.redis_store = redis_store
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._direct_audio_url: Optional[str] = None
        self._youtube_resolve_failures = 0
        self._youtube_resolve_cooldown = 0

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _resolve_audio_url(self) -> Optional[str]:
        if self.source_type != "youtube":
            return self.source_url

        def get_audio_url() -> str:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                # Utilisation du fichier statique exporté depuis le navigateur
                "cookiefile": "cookies.txt",
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.source_url, download=False)
                return info.get("url")

        try:
            return await asyncio.to_thread(get_audio_url)
        except Exception as exc:
            _logger.error("Failed to resolve YouTube audio URL: %s", exc)
            return None

    def _chunk_file_path(self, timestamp: datetime) -> str:
        safe_name = self.name.lower().replace(" ", "_")
        file_name = f"{safe_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
        return os.path.join(AppConfig.LIVE_CHUNKS_DIR, file_name)

    async def _run_loop(self) -> None:
        while self._running:
            try:
                if self.source_type == "youtube" and not self._direct_audio_url:
                    # Skip if in cooldown from repeated failures
                    if self._youtube_resolve_cooldown > 0:
                        self._youtube_resolve_cooldown -= 1
                        _logger.debug("YouTube resolve cooldown for channel %s: %d seconds remaining", 
                                     self.channel_id, self._youtube_resolve_cooldown)
                    else:
                        self._direct_audio_url = await self._resolve_audio_url()
                        if not self._direct_audio_url:
                            self._youtube_resolve_failures += 1
                            # Exponential backoff: 5s * 2^failures, max 300s
                            backoff = min(5 * (2 ** (self._youtube_resolve_failures - 1)), 300)
                            self._youtube_resolve_cooldown = backoff
                        else:
                            # Success, reset failure counter
                            self._youtube_resolve_failures = 0
                            self._youtube_resolve_cooldown = 0
                elif self.source_type in {"hls", "direct_audio"}:
                    self._direct_audio_url = self.source_url

                if not self._direct_audio_url:
                    raise RuntimeError("Unable to resolve stream URL")

                timestamp = datetime.now(timezone.utc)
                chunk_file = self._chunk_file_path(timestamp)

                await asyncio.to_thread(
                    capture_stream_chunk,
                    self._direct_audio_url,
                    chunk_file,
                    AppConfig.CHUNK_SECONDS,
                )

                _logger.info("▶️ [Live %s] Morceau audio téléchargé. Début de la transcription...", self.name)
                # Remplacement : Extraction STT au lieu des empreintes audio
                text = await text_matcher.extract_text_with_retry(chunk_file)
                
                recent_fingerprints_count = 0
                if text:
                    _logger.info("📝 [Live %s] Audio entendu : '%s'", self.name, text)
                    if text_matcher.validate_language(text):
                        _logger.info("✅ [Live %s] Sauvegardé dans Redis pour comparaison avec le mobile.", self.name)
                        await self.redis_store.store_text(
                            channel_id=self.channel_id,
                            channel_name=self.name,
                            media_type=self.media_type,
                            timestamp=timestamp,
                            text=text,
                        )
                        recent_fingerprints_count = 1
                    else:
                        _logger.warning("⚠️ [Live %s] Ignoré (Non français ou trop court).", self.name)
                        # Log diagnostics des textes ignorés (langue non supportée)
                        ignored_data = {
                            "timestamp": timestamp.isoformat(),
                            "channel_id": self.channel_id,
                            "text": text
                        }
                        os.makedirs("data/diagnostics", exist_ok=True)
                        with open("data/diagnostics/ignored_transcripts.jsonl", "a", encoding="utf-8") as f:
                            f.write(json.dumps(ignored_data) + "\n")

                status = {
                    "channel_id": self.channel_id,
                    "name": self.name,
                    "media_type": self.media_type,
                    "source_type": self.source_type,
                    "source_url": self.source_url,
                    "worker_running": True,
                    "recent_fingerprints": recent_fingerprints_count,
                    "last_chunk_time": timestamp.isoformat().replace("+00:00", "Z"),
                    "last_error": None,
                    "active": True,
                }
                await self.redis_store.set_live_status(self.channel_id, status)

                cleanup_old_files(AppConfig.LIVE_CHUNKS_DIR, 3600)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                _logger.error("Live worker error (channel %s): %s", self.channel_id, exc)
                if self.source_type == "youtube":
                    self._direct_audio_url = None
                await self.redis_store.set_last_error(self.channel_id, str(exc))
                await asyncio.sleep(5)

        await self.redis_store.set_live_status(
            self.channel_id,
            {
                "channel_id": self.channel_id,
                "name": self.name,
                "media_type": self.media_type,
                "source_type": self.source_type,
                "source_url": self.source_url,
                "worker_running": False,
                "recent_fingerprints": 0,
                "last_chunk_time": None,
                "last_error": None,
                "active": True,
            },
        )
