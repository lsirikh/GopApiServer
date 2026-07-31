"""
Tracking History model — GIS 추적점 영속
PRD: PRD_Tracking_History_API.md v1.0

NATS `sensorway.{부대ID}.gis.tracking-status`(TRACKING_STATUS, 신버전 targets[])로
수집된 추적 타겟의 위치 이력을 영속한다. 저장은 독립 워커 `gis-ingest`가 수행하고,
이 모델은 read-only 조회(`/api/tracking/points`·`/sessions`)에 사용된다.
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, DateTime, Index, UniqueConstraint
)
from datetime import datetime

from app.database import Base
from app.models.types import UtcDateTime
from app.config import settings


class TrackPoint(Base):
    """
    추적점(track point) — TRACKING_STATUS targets[]의 단일 타겟 관측 1건.

    멱등 인제스트: UNIQUE(track_id, observed_at) — 재전송/다중 인제스트 안전.
    keyset 페이지네이션: (observed_at, id) 단조 정렬.

    PRD: PRD_Tracking_History_API.md Section 4.1
    """
    __tablename__ = "track_points"

    # 고볼륨 시계열 → BIGSERIAL(PG) / INTEGER(SQLite)
    id = Column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    # 발행 메시지 매핑
    camera_id = Column(Integer, nullable=False, index=True)   # body.camera_id (비-FK: 이력은 자산 수명에 독립)
    track_id = Column(String(64), nullable=False, index=True)  # targets[].track_id
    label = Column(String(32))                                 # targets[].label (person/car/vehicle/animal)
    threat_level = Column(String(16))                          # targets[].threat_level (NORMAL/CAUTION/THREAT, tolerant)
    latitude = Column(Float, nullable=False)                   # targets[].location.latitude
    longitude = Column(Float, nullable=False)                  # targets[].location.longitude
    distance_m = Column(Float)                                 # targets[].location.distance_m
    confidence = Column(Float)                                 # targets[].confidence
    observed_at = Column(UtcDateTime, nullable=False, index=True)  # targets[].observed_at (keyset 정렬키, naive KST)
    tracking_state = Column(String(16))                        # body.tracking (active 고정; 세션경계 참고)
    speed_mps = Column(Float)                                  # (선택) 서버 계산/미저장 시 클라 재계산
    session_seq = Column(Integer)                             # (선택) 세션 시퀀스

    # 인제스트 시각 (감사용) — naive KST 컨벤션(audit_log 동일)
    created_at = Column(
        UtcDateTime,
        default=lambda: datetime.now(settings.tz).replace(tzinfo=None),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("track_id", "observed_at", name="uq_track_points_track_observed"),
        Index("idx_track_points_observed_at", "observed_at"),
        Index("idx_track_points_camera_observed", "camera_id", "observed_at"),
    )

    def __repr__(self):
        return f"<TrackPoint {self.id}: cam{self.camera_id}/{self.track_id} @ {self.observed_at}>"
