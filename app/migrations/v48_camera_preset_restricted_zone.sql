-- v4.6 — Camera Preset 감시금지구역 옵션 추가 (차장 결재 2026-06-19, 단순화 확정)
--
-- 적용 사항:
--   1. camera_presets.is_restricted_zone (Boolean NOT NULL DEFAULT false) 추가
--   2. 기존 row 모두 default false로 backfill (데이터 손실 0)
--
-- 매니저 측 처리 (통일):
--   is_restricted_zone=true 시 RTSP/녹화/이벤트/화면 모두 차단
--   (VMS / NVR / db_monitor / Central UI 4 매니저가 통일 정책 적용)
--
-- 사고 시 롤백:
--   ALTER TABLE camera_presets DROP COLUMN IF EXISTS is_restricted_zone;

BEGIN;

-- is_restricted_zone 컬럼 추가 (NOT NULL DEFAULT false → 기존 row 자동 false)
ALTER TABLE camera_presets
    ADD COLUMN IF NOT EXISTS is_restricted_zone BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN camera_presets.is_restricted_zone IS '감시금지구역 표시 (v4.6 신규) — true 시 매니저 측에서 RTSP/녹화/이벤트/화면 모두 차단';

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
  AND column_name = 'is_restricted_zone';

SELECT 'Backfill 검증:' AS check;
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE is_restricted_zone = false) AS default_false
FROM camera_presets;
