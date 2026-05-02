from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import RewardRedeemRequest, RewardResponse
from services.rewards_service import list_rewards, redeem_reward

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("", response_model=list[RewardResponse])
def get_rewards(db: Session = Depends(get_db)):
    return list_rewards(db)


@router.post("/redeem")
def redeem(payload: RewardRedeemRequest, db: Session = Depends(get_db)):
    result = redeem_reward(payload.user_id, payload.reward_id, db)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result
