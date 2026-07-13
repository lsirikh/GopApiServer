-- v4.6 — device_group_mappings polymorphic cleanup (차장 결재 필요, 2026-06-22)
--
-- 배경:
--   device_group_mappings.device_id 는 polymorphic — cameras/sensors/controllers/
--   speakers/enclosures/lamps 6개 자식 테이블의 PK 를 (category_device 와 함께)
--   참조한다. 단일 DB FK 선언 불가. 따라서 ON DELETE CASCADE 를 6개 자식 테이블
--   각각에 트리거(또는 동등 메커니즘)로 보장한다.
--
-- 적용 사항:
--   1. UNIQUE 제약 (device_id, category_device, group_id) 재확인 — 이미 존재
--   2. 6개 자식 테이블에 AFTER DELETE 트리거 추가 — devices 베이스가 CASCADE 로
--      자식 row 를 삭제할 때마다 매핑 row 정리
--   3. devices 베이스 자체에는 트리거 불가 (category_device 알 수 없음 시점이 있음)
--      → 자식 테이블에 거는 것이 안전
--
-- 사고 시 롤백: 본 파일 하단 'ROLLBACK' 블록 참조

BEGIN;

-- ----------------------------------------------------------------
-- 1) 6개 자식 테이블 각각에 AFTER DELETE 트리거
-- ----------------------------------------------------------------

-- 공통 trigger function: 삭제된 자식 PK 와 카테고리로 mapping 정리
CREATE OR REPLACE FUNCTION fn_cleanup_device_group_mappings()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM device_group_mappings
     WHERE device_id = OLD.id
       AND category_device = TG_ARGV[0]::text::"enumdevicecategory";
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Camera
DROP TRIGGER IF EXISTS trg_cameras_cleanup_group_mappings ON cameras;
CREATE TRIGGER trg_cameras_cleanup_group_mappings
    AFTER DELETE ON cameras
    FOR EACH ROW
    EXECUTE FUNCTION fn_cleanup_device_group_mappings('CAMERA');

-- Sensor
DROP TRIGGER IF EXISTS trg_sensors_cleanup_group_mappings ON sensors;
CREATE TRIGGER trg_sensors_cleanup_group_mappings
    AFTER DELETE ON sensors
    FOR EACH ROW
    EXECUTE FUNCTION fn_cleanup_device_group_mappings('SENSOR');

-- Controller
DROP TRIGGER IF EXISTS trg_controllers_cleanup_group_mappings ON controllers;
CREATE TRIGGER trg_controllers_cleanup_group_mappings
    AFTER DELETE ON controllers
    FOR EACH ROW
    EXECUTE FUNCTION fn_cleanup_device_group_mappings('CONTROLLER');

-- Speaker
DROP TRIGGER IF EXISTS trg_speakers_cleanup_group_mappings ON speakers;
CREATE TRIGGER trg_speakers_cleanup_group_mappings
    AFTER DELETE ON speakers
    FOR EACH ROW
    EXECUTE FUNCTION fn_cleanup_device_group_mappings('SPEAKER');

-- Enclosure
DROP TRIGGER IF EXISTS trg_enclosures_cleanup_group_mappings ON enclosures;
CREATE TRIGGER trg_enclosures_cleanup_group_mappings
    AFTER DELETE ON enclosures
    FOR EACH ROW
    EXECUTE FUNCTION fn_cleanup_device_group_mappings('ENCLOSURE');

-- Lamp
DROP TRIGGER IF EXISTS trg_lamps_cleanup_group_mappings ON lamps;
CREATE TRIGGER trg_lamps_cleanup_group_mappings
    AFTER DELETE ON lamps
    FOR EACH ROW
    EXECUTE FUNCTION fn_cleanup_device_group_mappings('LAMP');

COMMENT ON FUNCTION fn_cleanup_device_group_mappings IS
    'v4.6 — polymorphic device_group_mappings cleanup. device_id 에 FK 선언 불가하므로 트리거로 보장.';

COMMIT;

-- ----------------------------------------------------------------
-- 검증
-- ----------------------------------------------------------------
-- SELECT tgname, tgrelid::regclass FROM pg_trigger
--  WHERE tgname LIKE 'trg_%_cleanup_group_mappings'
--  ORDER BY tgrelid::regclass::text;
-- 기대 결과: 6 rows (cameras, controllers, enclosures, lamps, sensors, speakers)

-- ----------------------------------------------------------------
-- ROLLBACK (사고 시)
-- ----------------------------------------------------------------
-- BEGIN;
--   DROP TRIGGER IF EXISTS trg_cameras_cleanup_group_mappings    ON cameras;
--   DROP TRIGGER IF EXISTS trg_sensors_cleanup_group_mappings    ON sensors;
--   DROP TRIGGER IF EXISTS trg_controllers_cleanup_group_mappings ON controllers;
--   DROP TRIGGER IF EXISTS trg_speakers_cleanup_group_mappings   ON speakers;
--   DROP TRIGGER IF EXISTS trg_enclosures_cleanup_group_mappings ON enclosures;
--   DROP TRIGGER IF EXISTS trg_lamps_cleanup_group_mappings      ON lamps;
--   DROP FUNCTION IF EXISTS fn_cleanup_device_group_mappings;
-- COMMIT;

-- ORPHANED CLEANUP
-- v4.6 — 기존 orphaned device_group_mappings 일괄 정리
--   진단 결과: 504 건 orphaned (SPEAKER 262 + SENSOR 242)
--   사유: Lamp/Speaker/Enclosure 라우터 DELETE 핸들러 누락 + 초기 Sensor 코드 누락 잔재
--
-- 안전성:
--   - 자식 테이블(cameras/sensors/controllers/speakers/enclosures/lamps)에 실제 row 가
--     존재하는 mapping 은 보존
--   - device_id + category_device 조합이 어느 자식 테이블에도 존재하지 않는 row 만 삭제
--   - 트랜잭션 + 실행 전 카운트/실행 후 카운트로 검증

BEGIN;

-- 1) 실행 전 백업 (롤백용)
CREATE TEMP TABLE tmp_orphaned_mappings_backup AS
SELECT m.*
  FROM device_group_mappings m
 WHERE (m.category_device = 'CAMERA'     AND NOT EXISTS (SELECT 1 FROM cameras     c WHERE c.id = m.device_id))
    OR (m.category_device = 'SENSOR'     AND NOT EXISTS (SELECT 1 FROM sensors     s WHERE s.id = m.device_id))
    OR (m.category_device = 'CONTROLLER' AND NOT EXISTS (SELECT 1 FROM controllers c WHERE c.id = m.device_id))
    OR (m.category_device = 'SPEAKER'    AND NOT EXISTS (SELECT 1 FROM speakers    s WHERE s.id = m.device_id))
    OR (m.category_device = 'ENCLOSURE'  AND NOT EXISTS (SELECT 1 FROM enclosures  e WHERE e.id = m.device_id))
    OR (m.category_device = 'LAMP'       AND NOT EXISTS (SELECT 1 FROM lamps       l WHERE l.id = m.device_id));

-- 2) 실행 전 카운트 — 진단 504 와 일치하는지 확인
SELECT 'BEFORE' AS phase,
       category_device,
       COUNT(*) AS orphan_count
  FROM tmp_orphaned_mappings_backup
 GROUP BY category_device
 ORDER BY category_device;
-- 기대: SPEAKER 262, SENSOR 242 (합 504). 불일치 시 ROLLBACK 후 재조사.

-- 3) 실제 삭제
DELETE FROM device_group_mappings m
 USING tmp_orphaned_mappings_backup b
 WHERE m.id = b.id;

-- 4) 실행 후 검증 — 남은 orphan 0 이어야 정상
SELECT 'AFTER' AS phase, COUNT(*) AS remaining_orphans
  FROM device_group_mappings m
 WHERE (m.category_device = 'CAMERA'     AND NOT EXISTS (SELECT 1 FROM cameras     c WHERE c.id = m.device_id))
    OR (m.category_device = 'SENSOR'     AND NOT EXISTS (SELECT 1 FROM sensors     s WHERE s.id = m.device_id))
    OR (m.category_device = 'CONTROLLER' AND NOT EXISTS (SELECT 1 FROM controllers c WHERE c.id = m.device_id))
    OR (m.category_device = 'SPEAKER'    AND NOT EXISTS (SELECT 1 FROM speakers    s WHERE s.id = m.device_id))
    OR (m.category_device = 'ENCLOSURE'  AND NOT EXISTS (SELECT 1 FROM enclosures  e WHERE e.id = m.device_id))
    OR (m.category_device = 'LAMP'       AND NOT EXISTS (SELECT 1 FROM lamps       l WHERE l.id = m.device_id));
-- 기대: 0. 1 이상이면 ROLLBACK.

-- 5) 정상 시 커밋, 이상 시 ROLLBACK
COMMIT;
-- ROLLBACK;  -- 검증 실패 시 위 COMMIT 대신 사용

-- ----------------------------------------------------------------
-- 비상 복구 (커밋 후 실수 발견 시 — tmp 테이블은 세션 종료로 사라지므로
-- 별도 보존이 필요하면 일반 테이블로 변경: CREATE TABLE backup_... AS ...)
-- ----------------------------------------------------------------