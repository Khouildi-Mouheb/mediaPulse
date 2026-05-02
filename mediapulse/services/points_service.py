from datetime import datetime

from sqlalchemy.orm import Session

from models import PointsTransaction, UserPoints


def get_or_create_user_points(user_id: int, db: Session) -> UserPoints:
    points = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
    if points:
        return points
    points = UserPoints(user_id=user_id, total_points=0)
    db.add(points)
    db.commit()
    db.refresh(points)
    return points


def award_points(user_id: int, points: int, type: str, description: str, db: Session) -> int:
    user_points = get_or_create_user_points(user_id, db)
    user_points.total_points += points
    user_points.updated_at = datetime.utcnow()
    db.add(
        PointsTransaction(
            user_id=user_id,
            type=type,
            description=description,
            points=points,
        )
    )
    db.commit()
    return points


def get_points(user_id: int, db: Session) -> int:
    user_points = get_or_create_user_points(user_id, db)
    return user_points.total_points


def get_transactions(user_id: int, db: Session):
    return (
        db.query(PointsTransaction)
        .filter(PointsTransaction.user_id == user_id)
        .order_by(PointsTransaction.timestamp.desc())
        .all()
    )
