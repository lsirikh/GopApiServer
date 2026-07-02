"""
Tracking History API endpoints (read-only)
PRD: PRD_Tracking_History_API.md v1.0

GET /api/tracking/points    — 구간 추적점 조회(keyset cursor 청크) — Playback 핵심
GET /api/tracking/sessions  — 세션 목록(타임라인) — track_id 단위 파생 집계
GET /api/tracking/health    — 가용성 게이팅(무인증)

저장(인제스트)은 독립 워커 `gis-ingest`가 수행. 클라는 POST 하지 않는다.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from datetime import datetime
import base64

from app.dependencies import get_db
from app.routers.auth import get_current_account_user_optional
from app.models.tracking import TrackPoint
from app.schemas.tracking import (
    TrackPointResponse, TrackPointListResponse, CursorMeta, TrackSessionResponse,
)
from app.schemas.common import ApiResponse, KST

router = APIRouter(tags=["Tracking"])

DEFAULT_LIMIT = 1000
MAX_LIMIT = 5000


# ============================================================
# Helpers — keyset cursor / tz 정규화
# ============================================================

def _encode_cursor(observed_at: datetime, row_id: int) -> str:
    """(observed_at, id) → opaque base64 커서"""
    raw = f"{observed_at.isoformat()}|{row_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str):
    """opaque 커서 → (observed_at, id). 형식 오류 시 ValueError."""
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    ts_str, id_str = raw.rsplit("|", 1)
    return datetime.fromisoformat(ts_str), int(id_str)


def _to_naive_kst(dt: Optional[datetime]) -> Optional[datetime]:
    """저장값(naive KST) 비교용 정규화. aware → KST 변환 후 tz strip."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(KST).replace(tzinfo=None)
    return dt


def _as_dt(v):
    """SQLite 집계(func.min/max)가 문자열을 돌려줄 때 datetime 보정."""
    if isinstance(v, str):
        return datetime.fromisoformat(v)
    return v


# ============================================================
# GET /api/tracking/points
# ============================================================

@router.get(
    "/points",
    response_model=TrackPointListResponse,
    summary="추적점 구간 조회 (keyset cursor)",
)
async def get_track_points(
    from_: Optional[datetime] = Query(None, alias="from", description="구간 시작(observed_at ≥, ISO8601)"),
    to: Optional[datetime] = Query(None, description="구간 종료(observed_at ≤, ISO8601)"),
    camera_id: Optional[int] = Query(None, description="카메라 필터"),
    track_id: Optional[str] = Query(None, description="단일 트랙 필터"),
    cursor: Optional[str] = Query(None, description="직전 응답의 next_cursor"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="페이지 크기(기본 1000, 최대 5000)"),
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """
    Playback 구간 추적점 조회. 정렬 `observed_at ASC, id ASC`, keyset 커서 페이지네이션.

    클라는 `cursor`가 null이 될 때까지 반복 조회해 구간 전체를 청크로 적재한다.
    """
    query = db.query(TrackPoint)

    if camera_id is not None:
        query = query.filter(TrackPoint.camera_id == camera_id)
    if track_id:
        query = query.filter(TrackPoint.track_id == track_id)

    f = _to_naive_kst(from_)
    t = _to_naive_kst(to)
    if f is not None:
        query = query.filter(TrackPoint.observed_at >= f)
    if t is not None:
        query = query.filter(TrackPoint.observed_at <= t)

    if cursor:
        try:
            c_ts, c_id = _decode_cursor(cursor)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor",
            )
        # keyset: (observed_at, id) > (c_ts, c_id) — SQLite/PG 호환 전개형
        query = query.filter(
            or_(
                TrackPoint.observed_at > c_ts,
                and_(TrackPoint.observed_at == c_ts, TrackPoint.id > c_id),
            )
        )

    query = query.order_by(TrackPoint.observed_at.asc(), TrackPoint.id.asc())

    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = (
        _encode_cursor(rows[-1].observed_at, rows[-1].id) if (has_more and rows) else None
    )

    return TrackPointListResponse(
        success=True,
        message="Track points retrieved",
        data=[TrackPointResponse.model_validate(r) for r in rows],
        cursor=CursorMeta(next_cursor=next_cursor, limit=limit, has_more=has_more),
    )


# ============================================================
# GET /api/tracking/sessions
# ============================================================

@router.get(
    "/sessions",
    response_model=ApiResponse[List[TrackSessionResponse]],
    summary="추적 세션 목록 (타임라인)",
)
async def get_track_sessions(
    from_: Optional[datetime] = Query(None, alias="from", description="구간 시작(ISO8601)"),
    to: Optional[datetime] = Query(None, description="구간 종료(ISO8601)"),
    camera_id: Optional[int] = Query(None, description="카메라 필터"),
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """
    track_id(+camera_id) 단위로 `MIN/MAX(observed_at)`·`COUNT(*)`를 집계한 세션 목록.
    별도 세션 테이블 없이 추적점에서 파생한다. from/to는 구간 내 추적점만 집계한다.
    """
    query = db.query(
        TrackPoint.track_id.label("track_id"),
        TrackPoint.camera_id.label("camera_id"),
        func.max(TrackPoint.label).label("label"),
        func.min(TrackPoint.observed_at).label("start_at"),
        func.max(TrackPoint.observed_at).label("end_at"),
        func.count(TrackPoint.id).label("point_count"),
        func.max(TrackPoint.session_seq).label("session_seq"),
    )

    f = _to_naive_kst(from_)
    t = _to_naive_kst(to)
    if f is not None:
        query = query.filter(TrackPoint.observed_at >= f)
    if t is not None:
        query = query.filter(TrackPoint.observed_at <= t)
    if camera_id is not None:
        query = query.filter(TrackPoint.camera_id == camera_id)

    query = query.group_by(TrackPoint.track_id, TrackPoint.camera_id).order_by(
        func.min(TrackPoint.observed_at).asc()
    )

    rows = query.all()
    data = [
        TrackSessionResponse(
            track_id=r.track_id,
            camera_id=r.camera_id,
            label=r.label,
            start_at=_as_dt(r.start_at),
            end_at=_as_dt(r.end_at),
            point_count=r.point_count,
            session_seq=r.session_seq,
        )
        for r in rows
    ]

    return ApiResponse(
        success=True,
        message="Track sessions retrieved",
        data=data,
    )


# ============================================================
# GET /api/tracking/health
# ============================================================

@router.get(
    "/health",
    summary="추적 이력 가용성 게이팅",
)
async def tracking_health(db: Session = Depends(get_db)):
    """Playback 진입 게이팅용. 테이블 접근 가능하면 200, 아니면 503. 무인증."""
    try:
        count = db.query(func.count(TrackPoint.id)).scalar()
        return {"status": "ok", "tracking_count": int(count or 0)}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "tracking_count": 0},
        )
