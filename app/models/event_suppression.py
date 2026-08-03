"""
EventSuppressionSchedule model — 스케줄 기반 이벤트 수신 억제(정비 창).

PRD: docs/prds/event-suppression-schedule-prd.md v1.1 (기반)
     docs/prds/event-suppression-multi-target-prd.md v1.0 (복수 대상 확장)

설계 원칙:
- 억제 판정 권위는 요청 시점 계산(window_start <= now < window_end). is_active 는 sweep 비정규화(표시/통지용).
- window_end 필수(무기한 침묵 금지). revoked_at = soft-cancel(물리삭제 금지).
- 시간창 컬럼은 UtcDateTime(timestamptz, UTC 저장) — naive/aware 500 원천 차단.
- **복수 대상**: target_type(device/group/all 배타)은 유지, 대상은 junction 2테이블로 N개.
  DEVICE → event_suppression_target_devices, GROUP → event_suppression_target_groups.
- junction FK 는 CASCADE: 스케줄/장비/그룹 삭제 시 해당 junction 행만 정리(다중 대상 중 하나만 빠짐).
  단일-대상 스케줄이 0대상이 되면 inert(빈 대상=미매치).
- target_side(감지/감시)는 GROUP·ALL 스코프에 적용(category_device 파생 필터).
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Index, UniqueConstraint, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import UtcDateTime
from app.utils.datetime import utc_now
from app.utils.enums import (
    EnumSuppressionTargetType,
    EnumSuppressionSide,
    EnumSuppressionEventScope,
)


class EventSuppressionSchedule(Base):
    """이벤트 수신 억제 스케줄(정비 창) — 복수 대상 지원."""
    __tablename__ = "event_suppression_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String(200), nullable=False, comment="작업명/사유 (예: 'GOP 3구역 펜스 보수')")
    description = Column(String(500), nullable=True)

    # 대상 모드(배타). 실제 대상 id 는 junction 테이블(target_devices/target_groups)에 N개.
    target_type = Column(SQLEnum(EnumSuppressionTargetType), nullable=False, index=True)
    target_side = Column(
        SQLEnum(EnumSuppressionSide), nullable=False, default=EnumSuppressionSide.BOTH,
        comment="감지/감시 필터(GROUP·ALL 적용). 기본 BOTH",
    )

    event_scope = Column(SQLEnum(EnumSuppressionEventScope), nullable=False, index=True)

    window_start = Column(UtcDateTime, nullable=False)
    window_end = Column(UtcDateTime, nullable=False)

    recurrence_rule = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    # NATS 발행상태 전용(event-suppression-sync). 마지막으로 통지한 파생 상태를 기록해
    # date-job 이 창 경계에서 이 컬럼만 UPDATE → 트리거가 SYNC_EVENT_SUPPRESSION 발행.
    # ★ 억제 판정과 무관하며 is_active 와도 별개(is_active 는 sweep 비정규화 플래그).
    notified_status = Column(String(16), nullable=True)
    revoked_at = Column(UtcDateTime, nullable=True)
    created_by = Column(
        Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at = Column(UtcDateTime, default=utc_now, nullable=False)
    updated_at = Column(UtcDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_suppression_gate_window", "window_start", "window_end"),
        Index("ix_suppression_sweep", "is_active", "window_end"),
    )

    # 복수 대상 junction (async 안전 위해 lazy="selectin" — 조회 시 자동 eager 로드).
    # passive_deletes=True: 부모 삭제 시 자식 DELETE 를 ORM 이 선행 실행하지 않고 **DB FK CASCADE 에 위임**.
    #   → 하드삭제 순서가 "부모 DELETE → cascade" 가 되어, junction statement 트리거의 부모 JOIN 이
    #     이미 삭제된 부모를 못 찾아 중복 SYNC(UPDATED+DELETED)가 원천 차단된다.
    #   delete-orphan(컬렉션에서 제거된 개별 항목 삭제)은 그대로 유지된다(대상 배열 편집 경로).
    target_devices = relationship(
        "EventSuppressionTargetDevice", back_populates="schedule",
        cascade="all, delete-orphan", lazy="selectin", passive_deletes=True,
    )
    target_groups = relationship(
        "EventSuppressionTargetGroup", back_populates="schedule",
        cascade="all, delete-orphan", lazy="selectin", passive_deletes=True,
    )

    @property
    def device_ids(self) -> list[int]:
        return [t.device_id for t in self.target_devices]

    @property
    def group_ids(self) -> list[int]:
        return [t.group_id for t in self.target_groups]

    def __repr__(self):
        return (
            f"<EventSuppressionSchedule(id={self.id}, target={self.target_type}, "
            f"scope={self.event_scope}, window={self.window_start}~{self.window_end})>"
        )


class EventSuppressionTargetDevice(Base):
    """억제 스케줄 ↔ 대상 장비 junction (target_type=device 시 N개)."""
    __tablename__ = "event_suppression_target_devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    schedule_id = Column(
        Integer, ForeignKey("event_suppression_schedules.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    device_id = Column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    __table_args__ = (
        UniqueConstraint("schedule_id", "device_id", name="uq_suppression_target_device"),
    )

    schedule = relationship("EventSuppressionSchedule", back_populates="target_devices")


class EventSuppressionTargetGroup(Base):
    """억제 스케줄 ↔ 대상 그룹 junction (target_type=group 시 N개)."""
    __tablename__ = "event_suppression_target_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    schedule_id = Column(
        Integer, ForeignKey("event_suppression_schedules.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    group_id = Column(
        Integer, ForeignKey("device_groups.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    __table_args__ = (
        UniqueConstraint("schedule_id", "group_id", name="uq_suppression_target_group"),
    )

    schedule = relationship("EventSuppressionSchedule", back_populates="target_groups")
