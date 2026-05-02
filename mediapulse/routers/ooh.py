from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Billboard
from schemas import OOHEventCreate, OOHEventResponse
from services.ooh_service import create_ooh_event

router = APIRouter(tags=["ooh"])


@router.post("/ooh-event", response_model=OOHEventResponse)
def post_ooh_event(payload: OOHEventCreate, db: Session = Depends(get_db)):
    return create_ooh_event(
        payload.user_id,
        payload.panel_id,
        payload.timestamp,
        payload.distance_meters,
        db,
    )


@router.get("/billboards")
def list_billboards(db: Session = Depends(get_db)):
    return db.query(Billboard).all()
