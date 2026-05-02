import asyncio

import redis.asyncio as redis

from config import AppConfig


async def main():
    client = redis.from_url(AppConfig.REDIS_URL, decode_responses=True)
    try:
        pong = await client.ping()
        if not pong:
            raise RuntimeError("Redis ping failed")
        await client.setex("mediapulse:test", 10, "ok")
        value = await client.get("mediapulse:test")
        if value != "ok":
            raise RuntimeError("Redis set/get failed")
        print("Redis connection OK")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
