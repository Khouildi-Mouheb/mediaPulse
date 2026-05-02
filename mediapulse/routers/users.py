from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate, calculate_age, get_age_group
from services.points_service import award_points, get_or_create_user_points, get_points, get_transactions

router = APIRouter(prefix="/users", tags=["users"])


def _user_response(user: User, points: int) -> UserResponse:
    age = calculate_age(user.birth_date)
    return UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        birth_date=user.birth_date,
        age=age,
        age_group=get_age_group(age),
        occupation=user.occupation,
        sex=user.sex,
        region=user.region,
        phone_number=user.phone_number,
        email=user.email,
        points=points,
        consent_microphone=user.consent_microphone,
        consent_location=user.consent_location,
        consent_rewards=user.consent_rewards,
        consent_demographic_analytics=user.consent_demographic_analytics,
        created_at=user.created_at,
    )


@router.post("/signup", response_model=UserResponse)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(**payload.dict())
    db.add(user)
    db.commit()
    db.refresh(user)

    get_or_create_user_points(user.id, db)
    if user.consent_rewards:
        award_points(user.id, 100, "onboarding", "Completed onboarding", db)

    points = get_points(user.id, db)
    return _user_response(user, points)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    points = get_points(user.id, db)
    return _user_response(user, points)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    points = get_points(user.id, db)
    return _user_response(user, points)


@router.get("/{user_id}/points")
def user_points(user_id: int, db: Session = Depends(get_db)):
    return {"user_id": user_id, "points": get_points(user_id, db)}


@router.get("/{user_id}/transactions")
def user_transactions(user_id: int, db: Session = Depends(get_db)):
    transactions = get_transactions(user_id, db)
    return [
        {
            "id": txn.id,
            "type": txn.type,
            "description": txn.description,
            "points": txn.points,
            "timestamp": txn.timestamp,
        }
        for txn in transactions
    ]
