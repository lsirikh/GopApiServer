-- v71: 억제 스케줄 발행상태 전용 컬럼 — event-suppression-sync-message
--
-- 배경: 억제 창의 **시간창 자연 전이**(pending→active)는 DB 쓰기가 전혀 없어서
--   CRUD 트리거로는 원리적으로 포착되지 않는다(창 시작은 시간이 지날 뿐).
--   반면 active→expired 는 sweep 의 `is_active=false` 쓰기가 실재해 트리거가 잡는다.
--
-- 해법: 발행상태 전용 컬럼 `notified_status` 를 두고, date-job(suppression_scheduler)이
--   창 경계에서 이 컬럼만 UPDATE 한다. 그 UPDATE 를 기존 트리거가 잡아 NATS 로 발행한다.
--   → 발행자는 db_monitor 하나로 유지되고(봉투 생성 지점 단일화),
--     계산 상태 == notified_status 면 UPDATE 0행 → 발행 0건(멱등·멀티인스턴스 안전).
--
-- ★ is_active 는 절대 건드리지 않는다.
--   `ix_suppression_sync(is_active, window_end)` 인덱스와 sweep 쿼리가 현 의미에 의존한다.
--   notified_status 는 "마지막으로 통지한 파생 상태"일 뿐 억제 판정과 무관하다
--   (억제 판정 권위 = 요청시점 계산 window_start <= now < window_end).
--
-- 멱등: ADD COLUMN IF NOT EXISTS → 재실행 안전. fresh DB 는 create_all 이 이미 만들어 no-op.

ALTER TABLE event_suppression_schedules
    ADD COLUMN IF NOT EXISTS notified_status VARCHAR(16) NULL;

COMMENT ON COLUMN event_suppression_schedules.notified_status IS
    'NATS 발행상태 전용(마지막 통지 파생상태: pending/active/expired/cancelled). 억제 판정 무관 — is_active 와 별개';
