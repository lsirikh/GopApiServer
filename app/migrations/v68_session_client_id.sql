-- v68: 세션 동시성 정책 — client_id(RP 식별) + SSO 연동 예약 컬럼.
--
-- FR-MIG-01: allow 모드 self-replace 축이 되는 client_id.
-- FR-SSO-01: SSO 연동 예약 컬럼(auth_source/idp_subject/idp_session_id) — 현 차수 미사용,
--            향후 SSO Agent/서버가 채움. 표준 OIDC 필드라 IdP 제품 무관·저위험(전부 nullable/default).
--
-- 멱등성: ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS. 동작 변화 0(NULL/기본값 컬럼 추가만).

BEGIN;

ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS client_id VARCHAR(64);
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS auth_source VARCHAR(20) NOT NULL DEFAULT 'local';
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS idp_subject VARCHAR(255);       -- OIDC sub(계정 링킹)
ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS idp_session_id VARCHAR(255);    -- OIDC sid(Back-Channel Logout 조회키)

-- self-replace 조회: 같은 (user_id, client_id) 활성 세션
CREATE INDEX IF NOT EXISTS ix_user_sessions_active_client
    ON user_sessions (user_id, client_id) WHERE is_active AND client_id IS NOT NULL;
-- cap 카운트/evict_oldest created_at 정렬
CREATE INDEX IF NOT EXISTS ix_user_sessions_active_user
    ON user_sessions (user_id) WHERE is_active;

COMMIT;
