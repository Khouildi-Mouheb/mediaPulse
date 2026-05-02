from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Billboard, Channel, MediaDetection, OOHEvent, RewardRedemption, User


async def get_live_dashboard(db: Session, redis_store):
    today = date.today()

    users_count = db.query(User).count()
    media_detections_today = (
        db.query(MediaDetection)
        .filter(func.date(MediaDetection.detected_at) == today)
        .count()
    )
    ooh_exposures_today = (
        db.query(OOHEvent).filter(func.date(OOHEvent.timestamp) == today).count()
    )
    rewards_redeemed_today = (
        db.query(RewardRedemption)
        .filter(func.date(RewardRedemption.redeemed_at) == today)
        .count()
    )

    top_channels = (
        db.query(Channel.name, func.count(MediaDetection.id))
        .join(MediaDetection, MediaDetection.channel_id == Channel.id)
        .group_by(Channel.name)
        .order_by(func.count(MediaDetection.id).desc())
        .limit(5)
        .all()
    )
    top_billboards = (
        db.query(Billboard.panel_id, func.count(OOHEvent.id))
        .join(OOHEvent, OOHEvent.billboard_id == Billboard.id)
        .group_by(Billboard.panel_id)
        .order_by(func.count(OOHEvent.id).desc())
        .limit(5)
        .all()
    )

    live_reference_status = []
    if redis_store:
        channel_ids = [row[0] for row in db.query(Channel.id).all()]
        live_reference_status = await redis_store.get_all_live_statuses(channel_ids)

    return {
        "users_count": users_count,
        "media_detections_today": media_detections_today,
        "ooh_exposures_today": ooh_exposures_today,
        "top_channels": [
            {"name": name, "detections": count} for name, count in top_channels
        ],
        "top_billboards": [
            {"panel_id": panel_id, "exposures": count}
            for panel_id, count in top_billboards
        ],
        "rewards_redeemed_today": rewards_redeemed_today,
        "live_reference_status": live_reference_status,
    }
