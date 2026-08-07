"""
이벤트 억제(정비 창) 도메인 서비스 — event-suppression-schedule PRD v1.1

- is_suppressed        : 수신 게이트(요청시점 lazy 평가 = 억제 권위). fail-open(오류 시 억제 안 함).
- suppression_status   : 파생 상태(PENDING/ACTIVE/EXPIRED/CANCELLED) 계산 (순수함수).
- get_active_schedules : 현재 활성 창 조회 (/active, UI 배너·외부 조회 훅).
- run_suppression_sweep: 만료 창 is_active=false 정리 (비권위 백스톱, grant sweep 이식).
- record_suppression   : 억제된 이벤트 관측성(로그 + 프로세스 카운터) — NFR-05.

★ 억제 판정 권위 = 요청시점 계산(window_start <= now < window_end). is_active 는 sweep 비정규화(표시용).
★ 감지/감시 side 파생(D5): sensor/controller=detection, camera=surveillance, 그 외=보조(BOTH 일 때만 매치).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.utils.datetime import utc_now
from app.utils.enums import (
    EnumSuppressionTargetType,
    EnumSuppressionEventScope,
    EnumSuppressionStatus,
)

logger = logging.getLogger(__name__)

# 억제 대상 이벤트 카테고리(조치보고 action 은 제외 — 운영자 발행)
_SUPPRESSIBLE_CATEGORIES = ("detection", "malfunction", "connection")

# 관측성(NFR-05): 프로세스-로컬 억제 카운터(best-effort, 표시/테스트용). 권위 지표 아님.
_suppressed_counter: dict[str, int] = {}


def _enum_value(v) -> str:
    """enum 인스턴스/문자열 모두에서 값 문자열 추출."""
    return v.value if hasattr(v, "value") else str(v)


def _derive_side(device_category) -> str:
    """category_device → 감지/감시 side 파생(D5). 반환: 'detection'|'surveillance'|'auxiliary'."""
    cat = _enum_value(device_category)
    if cat in ("sensor", "controller"):
        return "detection"
    if cat == "camera":
        return "surveillance"
    return "auxiliary"  # speaker/lamp/enclosure — 보조(감지·감시 어느 쪽도 아님)


def _side_matches(device_side: str, target_side) -> bool:
    """스케줄 target_side 가 이 장비의 파생 side 를 포함하는가.

    - target_side=both  → 항상 매치(보조 장비 포함)
    - target_side=detection/surveillance → 파생 side 동일할 때만(보조 장비는 미매치)
    """
    ts = _enum_value(target_side)
    if ts == "both":
        return True
    return device_side == ts


def _naive_utc(dt: datetime | None) -> datetime | None:
    """저장/조회 datetime 을 naive-UTC 로 정규화(교차환경 비교 안전).

    aware → UTC 로 변환 후 tz strip. naive → 이미 UTC(저장 규약) 로 간주하고 그대로.
    ★ to_utc()(경계 입력용, naive=DISPLAY_TZ 가정)와 다름 — 여기는 저장 후 값(UTC)이라 shift 금지.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def suppression_status(schedule, now: datetime | None = None) -> str:
    """억제 스케줄 파생 상태. 우선순위: CANCELLED > PENDING > EXPIRED > ACTIVE."""
    n = _naive_utc(now or utc_now())
    if getattr(schedule, "revoked_at", None) is not None:
        return EnumSuppressionStatus.CANCELLED.value
    ws = _naive_utc(schedule.window_start)
    we = _naive_utc(schedule.window_end)
    if ws is not None and ws > n:
        return EnumSuppressionStatus.PENDING.value
    if we is not None and we <= n:
        return EnumSuppressionStatus.EXPIRED.value
    return EnumSuppressionStatus.ACTIVE.value


async def is_suppressed(db, device_id: int, device_category, category: str, now: datetime | None = None):
    """이벤트 수신 억제 게이트. 반환: (suppressed: bool, matched_schedule_id: int|None).

    3개 수신 핸들러(detections/malfunctions/connections)가 device 조회 직후·상태 플립 전에 호출한다.
    ★ fail-open: 게이트 조회 오류가 이벤트 저장을 막지 않는다(탐지 서버에서 조용한 유실 방지).
    """
    try:
        if category not in _SUPPRESSIBLE_CATEGORIES:
            return False, None
        try:
            scope_for_category = EnumSuppressionEventScope(category)
        except ValueError:
            return False, None

        from app.models.event_suppression import EventSuppressionSchedule
        from app.models.device_group import DeviceGroupMapping

        n = now or utc_now()
        stmt = select(EventSuppressionSchedule).where(
            EventSuppressionSchedule.revoked_at.is_(None),
            EventSuppressionSchedule.window_start <= n,
            EventSuppressionSchedule.window_end > n,
            EventSuppressionSchedule.event_scope.in_(
                [EnumSuppressionEventScope.ALL, scope_for_category]
            ),
        ).order_by(EventSuppressionSchedule.id)  # 다중 매치 시 결정적 first-match(L1, 감사 추적 안정)
        candidates = (await db.execute(stmt)).scalars().all()
        if not candidates:
            return False, None

        device_side = _derive_side(device_category)

        # GROUP 후보들의 대상 그룹 **합집합**으로 멤버십 1회 배치 조회(N+1 회피 유지).
        # target_groups 는 relationship lazy="selectin" 으로 후보 로드 시 자동 eager 로드됨.
        group_ids = {
            g.group_id for c in candidates
            if c.target_type == EnumSuppressionTargetType.GROUP
            for g in c.target_groups
        }
        member_groups: set[int] = set()
        if group_ids:
            rows = (await db.execute(
                select(DeviceGroupMapping.group_id).where(
                    DeviceGroupMapping.device_id == device_id,
                    DeviceGroupMapping.group_id.in_(group_ids),
                )
            )).scalars().all()
            member_groups = set(rows)

        for c in candidates:
            tt = c.target_type
            if tt == EnumSuppressionTargetType.DEVICE:
                # device_id ∈ 대상 장비 집합
                if device_id in {t.device_id for t in c.target_devices}:
                    return True, c.id
            elif tt == EnumSuppressionTargetType.ALL:
                if _side_matches(device_side, c.target_side):
                    return True, c.id
            elif tt == EnumSuppressionTargetType.GROUP:
                # 대상 그룹 집합 ∩ 장비 소속 그룹 ≠ ∅
                if ({t.group_id for t in c.target_groups} & member_groups) and _side_matches(device_side, c.target_side):
                    return True, c.id
        return False, None
    except Exception as e:  # fail-open — 억제 게이트 오류가 이벤트 저장을 막지 않음
        # ★ H2: 조회 예외로 세션이 무효(inactive) 상태일 수 있음. rollback 으로 복구하지 않으면
        #   호출부의 db.add(new_event)/commit 이 PendingRollbackError 로 500 → 이벤트 유실(진짜 fail-open 붕괴).
        #   best-effort rollback 후 (False,None) 반환해 핸들러가 정상 저장 경로로 진행하도록 보장.
        try:
            await db.rollback()
        except Exception:
            pass
        logger.warning(
            "is_suppressed failed (device_id=%s category=%s): %s — fail-open(억제 안 함, 세션 복구)",
            device_id, category, e,
        )
        return False, None


def record_suppression(device_id: int, category: str, schedule_id: int | None) -> None:
    """억제된 이벤트 관측성(NFR-05): 구조화 로그 + 프로세스 카운터. best-effort."""
    try:
        _suppressed_counter[category] = _suppressed_counter.get(category, 0) + 1
        logger.info(
            "event suppressed: category=%s device_id=%s schedule_id=%s (maintenance window)",
            category, device_id, schedule_id,
        )
    except Exception:  # 관측성 실패가 응답을 막지 않음
        pass


def get_suppressed_counts() -> dict[str, int]:
    """프로세스 억제 카운터 스냅샷(표시/테스트용)."""
    return dict(_suppressed_counter)


def suppressed_response(category: str, schedule_id: int | None):
    """억제된 POST 응답(D2): 202 + {suppressed:true}, 무저장. Response 직접 반환이라 response_model 우회."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "suppressed": True,
            "message": f"Event ({category}) suppressed by active maintenance window",
            "schedule_id": schedule_id,
        },
    )


async def get_active_schedules(db, now: datetime | None = None):
    """현재 활성(진행 중) 억제 창 목록 — /active. revoked 제외, window_start<=now<window_end."""
    from app.models.event_suppression import EventSuppressionSchedule

    n = now or utc_now()
    stmt = select(EventSuppressionSchedule).where(
        EventSuppressionSchedule.revoked_at.is_(None),
        EventSuppressionSchedule.window_start <= n,
        EventSuppressionSchedule.window_end > n,
    ).order_by(EventSuppressionSchedule.window_end)
    return (await db.execute(stmt)).scalars().all()


async def run_suppression_sweep() -> int:
    """스케줄러 진입점(FR-06) — 만료 창 is_active=false 정리 + **notified_status 양방향 재조정**.

    자체 AsyncSessionLocal 세션 사용(스케줄러 컨텍스트). 억제 판정 비의존(요청시점 계산이 권위).
    반환 = 갱신된 행 수. 예외는 호출 측 래퍼가 잡아 기동/주기를 막지 않는다.

    ★ event-suppression-sync 백스톱(FR-06):
      창 경계 통지는 date-job(suppression_scheduler)이 담당하지만, 잡 유실·프로세스 재기동·
      지평 밖 등록 실패 시 전이가 통지되지 않을 수 있다. 여기서 **파생상태 != notified_status**
      인 행을 찾아 맞춰줌으로써 최대 SUPPRESSION_SWEEP_INTERVAL_MINUTES 안에 자가 수렴시킨다.
      (UPDATE 가 곧 트리거 발화 → SYNC_EVENT_SUPPRESSION 발행. 이미 일치하면 UPDATE 0행 = 발행 0건.)
    """
    from app.database import AsyncSessionLocal
    from app.models.event_suppression import EventSuppressionSchedule

    async with AsyncSessionLocal() as db:
        now = utc_now()
        changed = 0

        # (1) 만료 창 is_active 정리 — 기존 동작 보존
        stmt = select(EventSuppressionSchedule).where(
            EventSuppressionSchedule.is_active == True,  # noqa: E712
            EventSuppressionSchedule.window_end <= now,
        )
        due = (await db.execute(stmt)).scalars().all()
        for s in due:
            s.is_active = False
            # 같은 UPDATE 에 통지 상태도 실어 (2)가 같은 행을 다시 건드리지 않게 한다(이중 통지 차단).
            s.notified_status = suppression_status(s, now)
            changed += 1

        # (2) 통지 상태 재조정 백스톱 — 파생상태와 어긋난 행만
        due_ids = {s.id for s in due}
        all_rows = (await db.execute(select(EventSuppressionSchedule))).scalars().all()
        for s in all_rows:
            if s.id in due_ids:
                continue
            st = suppression_status(s, now)
            if s.notified_status != st:
                s.notified_status = st
                changed += 1

        if not changed:
            return 0
        await db.commit()
        logger.info(
            "suppression sweep: %d expired deactivated, %d notify-state reconciled (total %d)",
            len(due), changed - len(due), changed,
        )
        return changed
