import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import redis.asyncio as redis

from config import AppConfig


class RedisFingerprintStore:
    def __init__(self, client: redis.Redis):
        self._client = client

    def _peak_hash_key(self, hash_value: str) -> str:
        return f"mediapulse:peak_hash:{hash_value}"

    async def store_hashes(
        self,
        channel_id: int,
        channel_name: str,
        media_type: str,
        timestamp: datetime,
        hashes: List[Tuple[str, float]],
    ) -> None:
        timestamp = timestamp.astimezone(timezone.utc)
        timestamp_iso = timestamp.isoformat().replace("+00:00", "Z")
        if not hashes:
            return

        pipe = self._client.pipeline()
        for hash_value, anchor_time in hashes:
            key = self._peak_hash_key(hash_value)
            value = {
                "channel_id": channel_id,
                "channel_name": channel_name,
                "media_type": media_type,
                "timestamp": timestamp_iso,
                "anchor_time": anchor_time,
            }
            pipe.lpush(key, json.dumps(value))
            pipe.ltrim(key, 0, AppConfig.PEAK_HASH_MAX_PER_KEY - 1)
            pipe.expire(key, AppConfig.LIVE_FINGERPRINT_TTL_SECONDS)
        await pipe.execute()

    async def get_hash_entries(self, hash_values: List[str]) -> Dict[str, List[Dict]]:
        if not hash_values:
            return {}

        pipe = self._client.pipeline()
        for hash_value in hash_values:
            pipe.lrange(self._peak_hash_key(hash_value), 0, -1)
        raw_lists = await pipe.execute()

        results: Dict[str, List[Dict]] = {}
        for hash_value, raw_items in zip(hash_values, raw_lists):
            entries: List[Dict] = []
            for item in raw_items:
                try:
                    entries.append(json.loads(item))
                except json.JSONDecodeError:
                    continue
            results[hash_value] = entries
        return results

    async def store_text(
        self,
        channel_id: int,
        channel_name: str,
        media_type: str,
        timestamp: datetime,
        text: str,
    ) -> None:
        if not text:
            return
        key = f"mediapulse:live_text:{channel_id}"
        value = {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "media_type": media_type,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "text": text,
        }
        pipe = self._client.pipeline()
        pipe.lpush(key, json.dumps(value))
        pipe.ltrim(key, 0, AppConfig.LIVE_TEXT_MAX_ENTRIES - 1)
        pipe.expire(key, AppConfig.LIVE_FINGERPRINT_TTL_SECONDS)
        await pipe.execute()

    async def get_recent_texts(self, channel_id: int, limit: int = 20) -> List[Dict]:
        key = f"mediapulse:live_text:{channel_id}"
        raw_items = await self._client.lrange(key, 0, limit - 1)
        return [json.loads(item) for item in raw_items if item]

    async def set_live_status(self, channel_id: int, status_dict: Dict) -> None:
        key = f"mediapulse:live_status:{channel_id}"
        await self._client.set(key, json.dumps(status_dict))

    async def get_live_status(self, channel_id: int) -> Optional[Dict]:
        key = f"mediapulse:live_status:{channel_id}"
        value = await self._client.get(key)
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    async def get_all_live_statuses(self, channel_ids: List[int]) -> List[Dict]:
        results: List[Dict] = []
        for channel_id in channel_ids:
            status = await self.get_live_status(channel_id)
            if status:
                results.append(status)
        return results

    async def set_last_error(self, channel_id: int, error_message: str) -> None:
        status = await self.get_live_status(channel_id) or {}
        status["last_error"] = error_message
        await self.set_live_status(channel_id, status)
