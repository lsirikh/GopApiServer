-- v55_app_settings.sql
-- v5.2 (2026-06-30) — 런타임 세션/인증 정책 저장소(app_settings) 신설
--
-- 실행: docker exec api-test-postgres psql -U gop_user -d gop -f /app/migrations/v55_app_settings.sql
--
-- NOTE:
-- - 앱 startup 의 Base.metadata.create_all 이 ORM 모델(app/models/app_settings.py)로
--   이 테이블을 자동 생성한다. 본 SQL 은 명시 문서화 + psql 직접 적용 대비용이며 IF NOT EXISTS 로 멱등.
-- - PRD: docs/prds/PRD_GOP_Server_Session_Settings.md (FR-SVS-01).
-- - 편집 가능한 안전 부분집합만 저장: session_timeout_hours / refresh_expiration_days /
--   lockout_threshold / session_enabled. AUTH_MODE / JWT_SECRET 등 배포전용은 저장하지 않는다.
-- - 시드 후 DB(app_settings)가 권위, .env 는 최초 1회 기본값(settings_service.seed_if_empty).
-- - updated_at = TIMESTAMP(naive KST 컨벤션, 타 테이블 동일).

BEGIN;

CREATE TABLE IF NOT EXISTS app_settings (
    setting_key    VARCHAR(100) PRIMARY KEY,                  -- 예: session_timeout_hours
    setting_value  TEXT         NOT NULL,                     -- 직렬화 문자열
    value_type     VARCHAR(10)  NOT NULL,                     -- 'int' | 'bool' | 'str'
    updated_at     TIMESTAMP    NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Seoul'),
    updated_by     INTEGER      REFERENCES account_users(id) ON DELETE SET NULL
);

COMMIT;
