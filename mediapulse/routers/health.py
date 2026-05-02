from fastapi import APIRouter

from redis_client import ping_redis

router = APIRouter()


@router.get("/")
async def root():
    return {
        "status": "ok",
        "service": "MediaPulse Backend",
        "redis_connected": await ping_redis(),
    }
