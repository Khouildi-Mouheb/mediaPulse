import logging
from typing import Dict

from models import Channel
from services.live_stream_worker import LiveStreamWorker
from services.redis_fingerprint_store import RedisFingerprintStore

_logger = logging.getLogger("mediapulse.stream_manager")


class LiveStreamManager:
    def __init__(self, redis_store: RedisFingerprintStore):
        self.redis_store = redis_store
        self._workers: Dict[int, LiveStreamWorker] = {}

    async def start_all(self, db) -> None:
        channels = db.query(Channel).filter(Channel.active.is_(True)).all()
        for channel in channels:
            await self.start_channel(channel)

    async def stop_all(self) -> None:
        for channel_id in list(self._workers.keys()):
            await self.stop_channel(channel_id)

    async def start_channel(self, channel: Channel) -> None:
        if channel.id in self._workers:
            return
        worker = LiveStreamWorker(
            channel_id=channel.id,
            name=channel.name,
            media_type=channel.media_type,
            source_type=channel.source_type,
            source_url=channel.source_url,
            redis_store=self.redis_store,
        )
        self._workers[channel.id] = worker
        await worker.start()
        _logger.info("Started live worker for channel %s", channel.id)

    async def stop_channel(self, channel_id: int) -> None:
        worker = self._workers.pop(channel_id, None)
        if worker:
            await worker.stop()
            _logger.info("Stopped live worker for channel %s", channel_id)

    async def restart_channel(self, channel: Channel) -> None:
        await self.stop_channel(channel.id)
        if channel.active:
            await self.start_channel(channel)

    async def get_status(self, db):
        channels = db.query(Channel).all()
        channel_ids = [channel.id for channel in channels]
        statuses = await self.redis_store.get_all_live_statuses(channel_ids)
        statuses_by_id = {item.get("channel_id"): item for item in statuses}

        response = []
        for channel in channels:
            status = statuses_by_id.get(channel.id)
            if not status:
                status = {
                    "channel_id": channel.id,
                    "name": channel.name,
                    "media_type": channel.media_type,
                    "source_type": channel.source_type,
                    "source_url": channel.source_url,
                    "active": channel.active,
                    "worker_running": channel.id in self._workers,
                    "recent_fingerprints": 0,
                    "last_chunk_time": None,
                    "last_error": None,
                }
            else:
                status["active"] = channel.active
            response.append(status)
        return response
