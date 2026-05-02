import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from sqlalchemy.orm import Session

from config import AppConfig
from database import get_db
from schemas import MediaDetectionResponse, DetectHashesRequest
from services.media_matching_service import MediaMatchingService

router = APIRouter(tags=["media"])


@router.post("/detect-media", response_model=MediaDetectionResponse)
async def detect_media(
    request: Request,
    audio: UploadFile = File(...),
    user_id: int = Form(...),
    timestamp: str = Form(...),
    db: Session = Depends(get_db),
):
    if not audio:
        raise HTTPException(status_code=400, detail="Audio file required")

    os.makedirs(AppConfig.AUDIO_UPLOAD_DIR, exist_ok=True)
    file_ext = os.path.splitext(audio.filename or "audio.wav")[1]
    temp_path = os.path.join(AppConfig.AUDIO_UPLOAD_DIR, f"upload_{uuid.uuid4()}{file_ext}")

    with open(temp_path, "wb") as handle:
        handle.write(await audio.read())

    media_service = MediaMatchingService(request.app.state.redis_store)
    try:
        return await media_service.match_uploaded_audio(temp_path, int(user_id), db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/detect-hashes", response_model=MediaDetectionResponse)
async def detect_hashes(
    request: Request,
    payload: DetectHashesRequest,
    db: Session = Depends(get_db),
):
    media_service = MediaMatchingService(request.app.state.redis_store)
    
    # Convert list of lists to list of tuples as expected by matching service
    tuples_hashes = [(str(h[0]), float(h[1])) for h in payload.hashes]
    
    try:
        return await media_service.match_precomputed_hashes(tuples_hashes, payload.user_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
