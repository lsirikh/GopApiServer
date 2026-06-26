"""
Tracking History Pydantic schemas
PRD: PRD_Tracking_History_API.md v1.0
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from app.schemas.common import KSTDatetime, ResponseMeta


# ============================================================
# Cursor (keyset) pagination meta — repo 전무, 신규 패턴
# ============================================================

class CursorMeta(BaseModel):
    """keyset 커서 페이지네이션 메타"""
    next_cursor: Optional[str] = Field(
        None,
        description="다음 페이지 커서(opaque). null이면 마지막 페이지",
        json_schema_extra={"example": "MjAyNi0wMi0wNVQxOTozNDoxMXwxMDAxMjM="}
    )
    limit: int = Field(..., description="요청 페이지 크기", json_schema_extra={"example": 1000})
    has_more: bool = Field(False, description="다음 페이지 존재 여부")


# ============================================================
# Response Schemas
# ============================================================

class TrackPointResponse(BaseModel):
    """추적점 응답(1행)"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., json_schema_extra={"example": 100123})
    camera_id: int = Field(..., json_schema_extra={"example": 201})
    track_id: str = Field(..., json_schema_extra={"example": "cam201-1738750245-007"})
    label: Optional[str] = Field(None, json_schema_extra={"example": "person"})
    threat_level: Optional[str] = Field(None, json_schema_extra={"example": "THREAT"})
    latitude: float = Field(..., json_schema_extra={"example": 38.1235})
    longitude: float = Field(..., json_schema_extra={"example": 127.5680})
    distance_m: Optional[float] = Field(None, json_schema_extra={"example": 120.5})
    confidence: Optional[float] = Field(None, json_schema_extra={"example": 0.92})
    observed_at: KSTDatetime = Field(..., json_schema_extra={"example": "2026-02-05T19:30:00+09:00"})
    tracking_state: Optional[str] = Field(None, json_schema_extra={"example": "active"})
    speed_mps: Optional[float] = Field(None, json_schema_extra={"example": 1.4})
    session_seq: Optional[int] = Field(None, json_schema_extra={"example": None})


class TrackPointListResponse(BaseModel):
    """추적점 목록 응답 — `data`=list + keyset `cursor`(표준 envelope에 cursor 슬롯이 없어 전용 래퍼)"""
    success: bool = True
    message: str
    data: List[TrackPointResponse]
    cursor: CursorMeta
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class TrackSessionResponse(BaseModel):
    """추적 세션(타임라인) — track_id 단위 파생 집계(별도 테이블 없음)"""
    track_id: str = Field(..., json_schema_extra={"example": "cam201-1738750245-007"})
    camera_id: int = Field(..., json_schema_extra={"example": 201})
    label: Optional[str] = Field(None, json_schema_extra={"example": "person"})
    start_at: KSTDatetime = Field(..., json_schema_extra={"example": "2026-02-05T19:30:00+09:00"})
    end_at: KSTDatetime = Field(..., json_schema_extra={"example": "2026-02-05T19:34:11+09:00"})
    point_count: int = Field(..., json_schema_extra={"example": 251})
    session_seq: Optional[int] = Field(None, json_schema_extra={"example": None})
