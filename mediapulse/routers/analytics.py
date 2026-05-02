from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from services.analytics_service import get_panels_demographics, get_panels_ranking

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_filters(
    region: str | None,
    sex: str | None,
    age_group: str | None,
    occupation: str | None,
    panel_id: str | None,
    start_date: str | None,
    end_date: str | None,
):
    filters = {
        "region": region,
        "sex": sex,
        "age_group": age_group,
        "occupation": occupation,
        "panel_id": panel_id,
    }
    if start_date:
        filters["start_date"] = datetime.fromisoformat(start_date)
    if end_date:
        filters["end_date"] = datetime.fromisoformat(end_date)
    return filters


@router.get("/panels-demographics")
def panels_demographics(
    region: str | None = None,
    sex: str | None = None,
    age_group: str | None = None,
    occupation: str | None = None,
    panel_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    filters = _parse_filters(region, sex, age_group, occupation, panel_id, start_date, end_date)
    return get_panels_demographics(filters, db)


@router.get("/panels-ranking")
def panels_ranking(
    region: str | None = None,
    sex: str | None = None,
    age_group: str | None = None,
    occupation: str | None = None,
    panel_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    filters = _parse_filters(region, sex, age_group, occupation, panel_id, start_date, end_date)
    return get_panels_ranking(filters, db)
