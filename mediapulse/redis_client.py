import logging
import os

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# URL de connexion locale à Redis (port 6379, configuré dans votre docker-compose)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client = None

async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

async def ping_redis() -> bool:
    try:
        client = await get_redis()
        return await client.ping()
    except Exception as e:
        logger.error("La connexion à Redis a échoué : %s", e)
        return False

async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None