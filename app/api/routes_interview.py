import os
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Interview, InterviewStatus, ScorecardRecord
from app.schemas.scorecard import (
    InterviewCreateRequest,
    InterviewCreateResponse,
    InterviewResponse,
    InterviewListResponse,
    Scorecard,
    PresignedUploadRequest,
    PresignedUploadResponse,
    compute_overall_score,
    compute_recommendation,
    compute_radar_scores,
)
from app.services.storage import storage_service
from app.tasks.worker import process_interview_task, execute_interview_assessment

logger = logging.getLogger(__name__)

router = APIRouter()


def _format_interview_response(interview: Interview) -> InterviewResponse:
    scorecard_data = None
    if interview.scorecard:
        sc = interview.scorecard
        overall = compute_overall_score(sc.coding_score, sc.communication_rating)
        rec = compute_recommendation(overall)
        radar = compute_radar_scores(sc.coding_score, sc.communication_rating)
        scorecard_data = Scorecard(
            coding_score=sc.coding_score,
            communication_rating=sc.communication_rating,
            technical_gaps_identified=sc.technical_gaps or [],
            follow_up_questions_to_ask=sc.follow_up_questions or [],
            summary=sc.summary,
            technical_notes=sc.technical_notes,
            communication_notes=sc.communication_notes,
            overall_score=overall,
            recommendation=rec,
            radar_scores=radar,
        )

    media_url = None
    if interview.media_storage_key:
        try:
            media_url = storage_service.generate_presigned_download_url(interview.media_storage_key)
        except Exception:
            media_url = None

    return InterviewResponse(
        task_id=interview.id,
        candidate_name=interview.candidate_name,
        candidate_email=interview.candidate_email,
        role_title=interview.role_title,
        status=interview.status.value,
        scorecard=scorecard_data,
        error_message=interview.error_message,
        media_storage_key=interview.media_storage_key,
        media_url=media_url,
        created_at=interview.created_at,
        updated_at=interview.updated_at,
    )


@router.post(
    "/",
    response_model=InterviewCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit interview assessment",
)
async def create_interview(
    payload: InterviewCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    interview = Interview(
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        role_title=payload.role_title,
        transcript=payload.transcript,
        media_storage_key=payload.media_storage_key,
        status=InterviewStatus.PENDING,
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)
    interview_id = interview.id

    # Dispatch assessment: Try Celery if enabled, otherwise use FastAPI background task
    if settings.use_celery:
        try:
            process_interview_task.delay(interview_id)
            logger.info("Dispatched assessment via Celery for %s", interview_id)
        except Exception as e:
            logger.warning("Celery dispatch failed (%s), running in-process background task", e)
            background_tasks.add_task(execute_interview_assessment, interview_id)
    else:
        background_tasks.add_task(execute_interview_assessment, interview_id)

    return InterviewCreateResponse(
        task_id=interview_id,
        status=interview.status.value,
    )


@router.get(
    "/audit-log",
    summary="Get real-time assessment audit log",
)
async def get_audit_log(
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Interview)
        .options(selectinload(Interview.scorecard))
        .order_by(Interview.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    interviews = result.scalars().all()
    events = []
    for it in interviews:
        events.append({
            "timestamp": it.created_at.isoformat() if it.created_at else None,
            "event": "Assessment Ingested",
            "actor": "Recruiter (Web Console)",
            "candidate": it.candidate_name,
            "role": it.role_title,
            "task_id": it.id,
            "status": "INGESTED",
        })
        if it.media_storage_key:
            events.append({
                "timestamp": it.created_at.isoformat() if it.created_at else None,
                "event": "S3 Media Artifact Vaulted",
                "actor": "AWS S3 Storage Vault",
                "candidate": it.candidate_name,
                "role": it.role_title,
                "task_id": it.id,
                "status": "VAULTED",
            })
        if it.status == InterviewStatus.COMPLETED:
            events.append({
                "timestamp": it.updated_at.isoformat() if it.updated_at else (it.created_at.isoformat() if it.created_at else None),
                "event": "Scorecard Synthesized",
                "actor": "Multi-Agent Synthesizer",
                "candidate": it.candidate_name,
                "role": it.role_title,
                "task_id": it.id,
                "status": "COMPLETED",
            })
        elif it.status == InterviewStatus.FAILED:
            events.append({
                "timestamp": it.updated_at.isoformat() if it.updated_at else (it.created_at.isoformat() if it.created_at else None),
                "event": "Assessment Failed",
                "actor": "Worker Engine",
                "candidate": it.candidate_name,
                "role": it.role_title,
                "task_id": it.id,
                "status": "FAILED",
            })
    return {"events": events, "total": len(events)}


@router.get(
    "/{interview_id}",
    response_model=InterviewResponse,
    summary="Get interview assessment and scorecard",
)
async def get_interview(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Interview)
        .options(selectinload(Interview.scorecard))
        .where(Interview.id == interview_id)
    )
    result = await db.execute(stmt)
    interview = result.scalars().first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    return _format_interview_response(interview)


@router.get(
    "/",
    response_model=InterviewListResponse,
    summary="List interview assessments",
)
async def list_interviews(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * size

    count_stmt = select(func.count(Interview.id))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = (
        select(Interview)
        .options(selectinload(Interview.scorecard))
        .order_by(Interview.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    interviews = result.scalars().all()

    items = [_format_interview_response(it) for it in interviews]

    return InterviewListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "/presigned-upload",
    response_model=PresignedUploadResponse,
    summary="Generate presigned S3 upload URL",
)
async def get_presigned_upload_url(payload: PresignedUploadRequest):
    storage_key = f"uploads/{uuid.uuid4()}-{payload.filename}"
    upload_url = storage_service.generate_presigned_upload_url(
        key=storage_key, expires_in=3600
    )
    return PresignedUploadResponse(
        upload_url=upload_url,
        storage_key=storage_key,
    )


@router.post(
    "/upload-file",
    summary="Directly upload interview media or transcript to storage",
)
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    key = f"transcripts/{uuid.uuid4()}-{file.filename}"
    storage_uri = storage_service.upload_bytes(
        data=content,
        key=key,
        content_type=file.content_type or "application/octet-stream",
    )
    return {
        "filename": file.filename,
        "storage_key": key,
        "storage_uri": storage_uri,
        "bytes": len(content),
    }


@router.delete(
    "/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete interview assessment",
)
async def delete_interview(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Interview).where(Interview.id == interview_id)
    result = await db.execute(stmt)
    interview = result.scalars().first()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview {interview_id} not found",
        )

    if interview.media_storage_key:
        storage_service.delete(interview.media_storage_key)

    await db.delete(interview)


@router.get(
    "/media/{key:path}",
    summary="Download or stream stored interview media artifact",
)
async def get_media_file(key: str):
    clean_key = os.path.normpath(key).lstrip("/")
    if ".." in clean_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path")

    if storage_service.is_s3:
        url = storage_service.generate_presigned_download_url(clean_key)
        return RedirectResponse(url)

    file_path = storage_service.local_dir / clean_key
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media artifact not found in storage",
        )

    try:
        file_path.resolve().relative_to(storage_service.local_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to media path is restricted",
        )

    return FileResponse(path=str(file_path))
