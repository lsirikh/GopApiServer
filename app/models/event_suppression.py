"""
EventSuppressionSchedule model — 스케줄 기반 이벤트 수신 억제(정비 창).

PRD: docs/prds/event-suppression-schedule-prd.md v1.1 §3.3

설계 원칙 (grant(UserGroupGrant) 시간창 패턴 이식):
- 억제 판정 권위는 요청 시점 계산(window_start <= now < window_end). is_active 는 sweep 비정규화(표시/통지용).
- window_end 필수(무기한 침묵 금지, NFR-04). revoked_at = soft-cancel(물리삭제 금지).
- 시간창 컬럼은 UtcDateTime(timestamptz, UTC 저장) — naive/aware 500 원천 차단(NFR-03).
- 대상: DEVICE(target_device_id) / GROUP(target_group_id → device_group_mappings 확장) / ALL(전역).
- target_side(감지/감시)는 GROUP·ALL 스코프에 적용(category_device 파생 필터).
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Index, Enum as SQLEnum,
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
    """이벤트 수신 억제 스케줄(정비 창).

    공사/설치/장애수리/AS 기간에 대상(장비/그룹/전체)의 이벤트 유형(연결/탐지/장애/전체)
    수신을 시간창으로 억제한다. 억제 시 이 서버는 해당 이벤트를 저장하지 않고 장비 상태
    플립도 건너뛴다(Phase 1: 저장·DB파생 억제).
    """
    __tablename__ = "event_suppression_schedules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 작업명/사유
    name = Column(String(200), nullable=False, comment="작업명/사유 (예: 'GOP 3구역 펜스 보수')")
    description = Column(String(500), nullable=True)

    # 대상 스코프
    target_type = Column(SQLEnum(EnumSuppressionTargetType), nullable=False, index=True)
    # ★ ON DELETE SET NULL (CASCADE 아님): 대상 장비/그룹이 삭제돼도 억제 스케줄 행은 보존한다.
    #   CASCADE 였다면 무관한 장비/그룹 삭제가 진행 중인 정비 창을 통째로 소멸시켜(soft-cancel·감사 없이)
    #   창 종료 전 조용히 억제가 풀리는 운영 리스크(H4). SET NULL 시 FK 만 비워져 해당 스코프는 무효화되고
    #   나머지(예: GROUP 창)는 유지된다.
    target_device_id = Column(
        Integer, ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="target_type=DEVICE 시 필수 — devices.id (전역 유일 PK)",
    )
    target_group_id = Column(
        Integer, ForeignKey("device_groups.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="target_type=GROUP 시 필수 — device_groups.id",
    )
    target_side = Column(
        SQLEnum(EnumSuppressionSide), nullable=False, default=EnumSuppressionSide.BOTH,
        comment="감지/감시 필터(GROUP·ALL 적용). 기본 BOTH",
    )

    # 억제 이벤트 유형
    event_scope = Column(SQLEnum(EnumSuppressionEventScope), nullable=False, index=True)

    # 유효 시간창 (UTC 저장). window_end 필수(자동 만료, 무기한 침묵 금지)
    window_start = Column(UtcDateTime, nullable=False)
    window_end = Column(UtcDateTime, nullable=False)

    # Phase 2 반복(RRULE). NULL = 단발
    recurrence_rule = Column(String(255), nullable=True)

    # sweep 비정규화 플래그(표시/통지용). 억제 권위는 window_start<=now<window_end 계산.
    is_active = Column(Boolean, default=True, nullable=False)

    # soft-cancel(grant.revoked_at 미러)
    revoked_at = Column(UtcDateTime, nullable=True)

    # 감사 — 생성 계정(append-only 익명화 정책상 nullable, SET NULL)
    created_by = Column(
        Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True,
    )

    created_at = Column(UtcDateTime, default=utc_now, nullable=False)
    updated_at = Column(UtcDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        # 억제 게이트 hot-path(모든 이벤트 POST 시 호출): window 범위 조건(is_suppressed) 최적화.
        # ★ 게이트 WHERE 에 is_active 는 없으므로 window 컬럼 선행 인덱스로 정합(M1).
        Index("ix_suppression_gate_window", "window_start", "window_end"),
        # sweep 백스톱(주기): 만료 창 정리(run_suppression_sweep 의 is_active + window_end 조건).
        Index("ix_suppression_sweep", "is_active", "window_end"),
    )

    # 대상 device/group 관계(참조 편의, 선택적 로드)
    target_device = relationship("Device", foreign_keys=[target_device_id])
    target_group = relationship("DeviceGroup", foreign_keys=[target_group_id])

    def __repr__(self):
        return (
            f"<EventSuppressionSchedule(id={self.id}, target={self.target_type}, "
            f"scope={self.event_scope}, window={self.window_start}~{self.window_end})>"
        )
