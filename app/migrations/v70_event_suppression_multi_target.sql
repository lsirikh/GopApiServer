-- v70: 이벤트 억제 복수 대상 — 단일 FK → junction 이관 후 컬럼 DROP.
--
-- 배경: event-suppression-multi-target. 한 정비 창에 복수 장비/그룹을 지정하기 위해
--   단일 FK(target_device_id/target_group_id)를 junction 2테이블로 전환한다.
--   junction 테이블(event_suppression_target_devices/event_suppression_target_groups)은
--   ORM 모델에서 Base.metadata.create_all() 로 생성된다(fresh·기존 DB 공통, apply 이전 단계).
--
-- 이 마이그레이션은:
--   1) 기존 단일-대상 행을 junction 으로 이관(각 1행).
--   2) 단일 FK 컬럼 제거(create_all 은 기존 테이블 컬럼을 삭제하지 않으므로 여기서 DROP).
--
-- 멱등: 컬럼 존재 여부로 가드 → 재실행 시 이미 DROP 됐으면 skip. fresh DB(컬럼 애초 없음) no-op.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'event_suppression_schedules' AND column_name = 'target_device_id') THEN
        INSERT INTO event_suppression_target_devices (schedule_id, device_id)
            SELECT id, target_device_id
            FROM event_suppression_schedules
            WHERE target_device_id IS NOT NULL
            ON CONFLICT (schedule_id, device_id) DO NOTHING;
        ALTER TABLE event_suppression_schedules DROP COLUMN target_device_id;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'event_suppression_schedules' AND column_name = 'target_group_id') THEN
        INSERT INTO event_suppression_target_groups (schedule_id, group_id)
            SELECT id, target_group_id
            FROM event_suppression_schedules
            WHERE target_group_id IS NOT NULL
            ON CONFLICT (schedule_id, group_id) DO NOTHING;
        ALTER TABLE event_suppression_schedules DROP COLUMN target_group_id;
    END IF;
END $$;
