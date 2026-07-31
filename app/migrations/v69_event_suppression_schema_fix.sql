-- v69: event_suppression_schedules 스키마 정합 self-heal (code-review H4b/M1)
--
-- 배경: 이 테이블이 "중간 버전" 모델(target FK ON DELETE CASCADE + 구 인덱스
--   ix_suppression_active_window)로 먼저 create_all 된 DB가 존재할 수 있다(개발기 등).
--   create_all()은 기존 테이블의 제약/인덱스를 변경하지 않으므로, 모델을 SET NULL + 신규 인덱스로
--   고쳐도 이미 생성된 테이블엔 반영되지 않는다(clone-deploy 원칙과 동일).
--
-- 문제(H4b): target FK 가 CASCADE 면 무관한 장비/그룹 삭제가 진행 중 정비 창을 통째로 소멸시켜
--   soft-cancel·감사 없이 억제가 조용히 풀린다 → SET NULL 로 교정.
-- 문제(M1): 억제 게이트 hot-path WHERE 에 is_active 가 없어 구 인덱스가 미활용 → window 선행 인덱스로 교체.
--
-- 멱등: fresh DB 는 create_all 이 이미 SET NULL + 신규 인덱스로 생성 → 아래 전부 no-op.
--   중간 버전 DB 는 이 마이그레이션으로 자가치유. 재실행 안전.

DO $$
BEGIN
    -- target_device_id FK: CASCADE(c) → SET NULL
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'event_suppression_schedules_target_device_id_fkey' AND confdeltype = 'c'
    ) THEN
        ALTER TABLE event_suppression_schedules
            DROP CONSTRAINT event_suppression_schedules_target_device_id_fkey;
        ALTER TABLE event_suppression_schedules
            ADD CONSTRAINT event_suppression_schedules_target_device_id_fkey
            FOREIGN KEY (target_device_id) REFERENCES devices(id) ON DELETE SET NULL;
    END IF;

    -- target_group_id FK: CASCADE(c) → SET NULL
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'event_suppression_schedules_target_group_id_fkey' AND confdeltype = 'c'
    ) THEN
        ALTER TABLE event_suppression_schedules
            DROP CONSTRAINT event_suppression_schedules_target_group_id_fkey;
        ALTER TABLE event_suppression_schedules
            ADD CONSTRAINT event_suppression_schedules_target_group_id_fkey
            FOREIGN KEY (target_group_id) REFERENCES device_groups(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 인덱스 정합(M1): 구 인덱스 제거 + 신규 hot-path/sweep 인덱스 생성(멱등)
DROP INDEX IF EXISTS ix_suppression_active_window;
CREATE INDEX IF NOT EXISTS ix_suppression_gate_window ON event_suppression_schedules (window_start, window_end);
CREATE INDEX IF NOT EXISTS ix_suppression_sweep ON event_suppression_schedules (is_active, window_end);
