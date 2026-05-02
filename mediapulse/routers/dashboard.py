from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from services.dashboard_service import get_live_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/live")
async def live_dashboard(request: Request, db: Session = Depends(get_db)):
    return await get_live_dashboard(db, request.app.state.redis_store)
