import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import AppConfig
from database import Base, SessionLocal, engine
from redis_client import close_redis, get_redis, ping_redis
from routers import analytics, channels, dashboard, health, media, ooh, rewards, users
from seed import seed_data
from services.audio_utils import ensure_directories
from services.live_stream_manager import LiveStreamManager
from services.redis_fingerprint_store import RedisFingerprintStore


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_data(db, AppConfig.DEFAULT_DIWAN_FM_URL)
    finally:
        db.close()

    if not await ping_redis():
        raise RuntimeError("Redis is required and not reachable at startup.")

    redis_client = await get_redis()
    redis_store = RedisFingerprintStore(redis_client)
    stream_manager = LiveStreamManager(redis_store)

    app.state.redis_store = redis_store
    app.state.stream_manager = stream_manager

    db = SessionLocal()
    try:
        try:
            await stream_manager.start_all(db)
        except Exception as e:
            logging.warning("Failed to start some streams: %s. Continuing without live streams.", e)
    finally:
        db.close()

    yield

    await stream_manager.stop_all()
    await close_redis()


app = FastAPI(title="MediaPulse Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(channels.router)
app.include_router(media.router)
app.include_router(ooh.router)
app.include_router(rewards.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
