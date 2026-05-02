from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from elBolbol.mediapulse.database import get_db
from elBolbol.mediapulse.models import Channel
from elBolbol.mediapulse.redis_client import ping_redis
from elBolbol.mediapulse.schemas import ChannelCreate, ChannelResponse, ChannelUpdate

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelResponse])
def list_channels(db: Session = Depends(get_db)):
    return db.query(Channel).all()


@router.post("", response_model=ChannelResponse)
async def create_channel(
    payload: ChannelCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    channel = Channel(**payload.dict())
    db.add(channel)
    db.commit()
    db.refresh(channel)

    if channel.active:
        await request.app.state.stream_manager.start_channel(channel)
    return channel


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    payload: ChannelUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    before = {
        "active": channel.active,
        "source_type": channel.source_type,
        "source_url": channel.source_url,
    }

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(channel, key, value)

    db.commit()
    db.refresh(channel)

    changed_source = (
        before["source_type"] != channel.source_type
        or before["source_url"] != channel.source_url
    )

    if channel.active and (changed_source or not before["active"]):
        await request.app.state.stream_manager.restart_channel(channel)
    elif not channel.active and before["active"]:
        await request.app.state.stream_manager.stop_channel(channel.id)

    return channel


@router.post("/{channel_id}/start")
async def start_channel(
    channel_id: int, request: Request, db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel.active = True
    db.commit()
    await request.app.state.stream_manager.start_channel(channel)
    return {"started": True}


@router.post("/{channel_id}/stop")
async def stop_channel(
    channel_id: int, request: Request, db: Session = Depends(get_db)
):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    channel.active = False
    db.commit()
    await request.app.state.stream_manager.stop_channel(channel_id)
    return {"stopped": True}


@router.get("/live-status")
async def live_status(request: Request, db: Session = Depends(get_db)):
    statuses = await request.app.state.stream_manager.get_status(db)
    return {"redis_connected": await ping_redis(), "channels": statuses}
