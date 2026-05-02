import random
import string

from sqlalchemy.orm import Session

from models import Reward, RewardRedemption, User
from services.points_service import award_points, get_or_create_user_points


def list_rewards(db: Session):
    return db.query(Reward).filter(Reward.active.is_(True)).all()


def _generate_coupon_code() -> str:
    return "MP-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def redeem_reward(user_id: int, reward_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "message": "User not found"}

    reward = db.query(Reward).filter(Reward.id == reward_id, Reward.active.is_(True)).first()
    if not reward:
        return {"success": False, "message": "Reward not found"}

    points = get_or_create_user_points(user_id, db)
    if points.total_points < reward.points_cost:
        return {"success": False, "message": "Not enough points"}

    coupon = _generate_coupon_code()
    redemption = RewardRedemption(
        user_id=user_id,
        reward_id=reward_id,
        coupon_code=coupon,
        points_spent=reward.points_cost,
    )
    db.add(redemption)
    db.commit()

    award_points(
        user_id,
        -reward.points_cost,
        "reward_redeem",
        f"Redeemed reward {reward.title}",
        db,
    )

    return {
        "success": True,
        "message": "Reward redeemed",
        "coupon_code": coupon,
        "points_spent": reward.points_cost,
    }
