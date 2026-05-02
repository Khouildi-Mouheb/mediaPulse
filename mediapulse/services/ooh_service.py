from datetime import timedelta

from sqlalchemy.orm import Session

from config import AppConfig
from models import Billboard, OOHEvent, User
from services.points_service import award_points


def create_ooh_event(user_id: int, panel_id: str, timestamp, distance_meters: float, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"saved": False, "message": "User not found", "points_earned": 0}

    billboard = db.query(Billboard).filter(Billboard.panel_id == panel_id).first()
    if not billboard:
        return {"saved": False, "message": "Billboard not found", "points_earned": 0}

    window_start = timestamp - timedelta(minutes=AppConfig.DUPLICATE_OOH_MINUTES)
    duplicate = (
        db.query(OOHEvent)
        .filter(
            OOHEvent.user_id == user_id,
            OOHEvent.billboard_id == billboard.id,
            OOHEvent.timestamp >= window_start,
        )
        .first()
    )
    if duplicate:
        return {"saved": False, "message": "Duplicate exposure", "points_earned": 0}

    event = OOHEvent(
        user_id=user_id,
        billboard_id=billboard.id,
        timestamp=timestamp,
        distance_meters=distance_meters,
    )
    db.add(event)
    db.commit()

    points_earned = award_points(
        user_id, 5, "ooh_exposure", "OOH exposure event", db
    )
    return {"saved": True, "message": "Exposure saved", "points_earned": points_earned}
