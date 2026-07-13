-- v4.7 마이그레이션 — FR-14 (JSON → JSONB) + FR-13 (Backfill heading:null)
-- 실행: docker exec api-test-postgres psql -U gop_user -d gop -f /v47_migration.sql
-- 롤백 태그: pre-v47 (HEAD=6a2430a)
-- 작성일: 2026-06-23

BEGIN;

-- ============================================================
-- FR-14: 23개 컬럼 json → jsonb 일괄 전환
--   PRD 기획 의도 (JsonB) 복원 — 시스템 일관성 회복
-- ============================================================

ALTER TABLE audit_logs         ALTER COLUMN changes          TYPE jsonb USING changes::jsonb;
ALTER TABLE config_change_logs ALTER COLUMN before_state     TYPE jsonb USING before_state::jsonb;
ALTER TABLE config_change_logs ALTER COLUMN after_state      TYPE jsonb USING after_state::jsonb;

ALTER TABLE cameras            ALTER COLUMN geolocation      TYPE jsonb USING geolocation::jsonb;
ALTER TABLE cameras            ALTER COLUMN hardware_spec    TYPE jsonb USING hardware_spec::jsonb;
ALTER TABLE cameras            ALTER COLUMN urls             TYPE jsonb USING urls::jsonb;
ALTER TABLE controllers        ALTER COLUMN geolocation      TYPE jsonb USING geolocation::jsonb;
ALTER TABLE sensors            ALTER COLUMN geolocation      TYPE jsonb USING geolocation::jsonb;
ALTER TABLE speakers           ALTER COLUMN geolocation      TYPE jsonb USING geolocation::jsonb;
ALTER TABLE lamps              ALTER COLUMN geolocation      TYPE jsonb USING geolocation::jsonb;
ALTER TABLE enclosures         ALTER COLUMN geolocation      TYPE jsonb USING geolocation::jsonb;
ALTER TABLE enclosures         ALTER COLUMN threshold_config TYPE jsonb USING threshold_config::jsonb;

ALTER TABLE detection_events   ALTER COLUMN detail           TYPE jsonb USING detail::jsonb;
ALTER TABLE malfunction_events ALTER COLUMN detail           TYPE jsonb USING detail::jsonb;
ALTER TABLE system_events      ALTER COLUMN detail           TYPE jsonb USING detail::jsonb;
ALTER TABLE server_metrics     ALTER COLUMN detail           TYPE jsonb USING detail::jsonb;
ALTER TABLE enclosure_metrics  ALTER COLUMN detail           TYPE jsonb USING detail::jsonb;

ALTER TABLE servers            ALTER COLUMN threshold_config TYPE jsonb USING threshold_config::jsonb;

ALTER TABLE file_groups        ALTER COLUMN files            TYPE jsonb USING files::jsonb;

ALTER TABLE report_templates   ALTER COLUMN components       TYPE jsonb USING components::jsonb;
ALTER TABLE report_generations ALTER COLUMN severity_filter  TYPE jsonb USING severity_filter::jsonb;
ALTER TABLE report_generations ALTER COLUMN summary_data     TYPE jsonb USING summary_data::jsonb;

ALTER TABLE user_groups        ALTER COLUMN permissions      TYPE jsonb USING permissions::jsonb;

-- ============================================================
-- FR-13: Backfill heading:null — 6 디바이스 테이블 geolocation에 heading 키 추가
--   기존 row 응답 JSON 키 일관성 보장
-- ============================================================

UPDATE cameras
SET geolocation = jsonb_set(geolocation, '{heading}', 'null'::jsonb, true)
WHERE geolocation IS NOT NULL AND NOT (geolocation ? 'heading');

UPDATE speakers
SET geolocation = jsonb_set(geolocation, '{heading}', 'null'::jsonb, true)
WHERE geolocation IS NOT NULL AND NOT (geolocation ? 'heading');

UPDATE sensors
SET geolocation = jsonb_set(geolocation, '{heading}', 'null'::jsonb, true)
WHERE geolocation IS NOT NULL AND NOT (geolocation ? 'heading');

UPDATE controllers
SET geolocation = jsonb_set(geolocation, '{heading}', 'null'::jsonb, true)
WHERE geolocation IS NOT NULL AND NOT (geolocation ? 'heading');

UPDATE lamps
SET geolocation = jsonb_set(geolocation, '{heading}', 'null'::jsonb, true)
WHERE geolocation IS NOT NULL AND NOT (geolocation ? 'heading');

UPDATE enclosures
SET geolocation = jsonb_set(geolocation, '{heading}', 'null'::jsonb, true)
WHERE geolocation IS NOT NULL AND NOT (geolocation ? 'heading');

COMMIT;

-- ============================================================
-- 검증 쿼리 (마이그레이션 후 실행)
-- ============================================================
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE data_type IN ('json', 'jsonb')
-- ORDER BY data_type, table_name;
-- → json 0건, jsonb 23건 기대
--
-- SELECT id, name_device, geolocation
-- FROM cameras JOIN devices USING (id) LIMIT 3;
-- → geolocation 안에 "heading": null 포함 기대
