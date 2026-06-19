-- v4.6 — Camera Preset 감시금지구역 옵션 추가 (Option C, 차장 결재 2026-06-19)
--
-- 적용 사항:
--   1. camera_presets.is_restricted_zone (Boolean NOT NULL DEFAULT false) 추가
--   2. camera_presets.restricted_actions (JSONB NOT NULL DEFAULT '[]') 추가
--   3. 기존 row 모두 default 값으로 backfill (데이터 손실 0)
--
-- Enum 값 (애플리케이션 측 EnumRestrictedAction):
--   - BLOCK_RTSP         : RTSP 스트림 응답 차단 (서버/VMS 측)
--   - BLOCK_RECORDING    : 녹화 중지 (NVR 측)
--   - BLOCK_EVENT_NOTIFY : 탐지 이벤트 발행 차단 (db_monitor 측)
--   - MASK_DISPLAY       : 화면 마스킹 (Central UI 측)
--
-- 사고 시 롤백:
--   ALTER TABLE camera_presets DROP COLUMN IF EXISTS is_restricted_zone;
--   ALTER TABLE camera_presets DROP COLUMN IF EXISTS restricted_actions;

BEGIN;

-- 1. is_restricted_zone 컬럼 추가 (NOT NULL DEFAULT false → 기존 row 자동 false)
ALTER TABLE camera_presets
    ADD COLUMN IF NOT EXISTS is_restricted_zone BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN camera_presets.is_restricted_zone IS '감시금지구역 표시 (v4.6 신규)';

-- 2. restricted_actions JSONB 컬럼 추가 (NOT NULL DEFAULT '[]')
ALTER TABLE camera_presets
    ADD COLUMN IF NOT EXISTS restricted_actions JSONB NOT NULL DEFAULT '[]'::jsonb;

COMMENT ON COLUMN camera_presets.restricted_actions IS '차단 동작 목록 — BLOCK_RTSP / BLOCK_RECORDING / BLOCK_EVENT_NOTIFY / MASK_DISPLAY (v4.6 신규)';

COMMIT;

-- 검증
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default,
    col_description('camera_presets'::regclass, ordinal_position) AS comment
FROM information_schema.columns
WHERE table_name = 'camera_presets'
  AND column_name IN ('is_restricted_zone', 'restricted_actions')
ORDER BY column_name;

SELECT 'Backfill 검증:' AS check;
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE is_restricted_zone = false) AS default_false,
    COUNT(*) FILTER (WHERE restricted_actions = '[]'::jsonb) AS default_empty_array
FROM camera_presets;
