-- v52_token_blacklist.sql
-- v4.9 Phase 2-A4 — JWT jti 블랙리스트 (D1 결재: 잠정 DB 저장소)
--
-- 차장님 결재 (PRD v4.9 권고 적용):
-- "jti 블랙리스트 저장소는 잠정 DB. IBlacklistStore 추상화로 v5.0 Redis 전환 가능"
--
-- 용도:
-- - logout / lock / password-change 시 발행된 jti를 블랙리스트에 등록
-- - get_current_account_user 의존성에서 jti 조회 → 블랙된 토큰 거부
-- - exp 경과 row는 APScheduler가 1시간마다 정리 (Phase 5에서 등록)
--
-- 성능:
-- - jti UNIQUE 인덱스 + partial index (expires_at > now())
-- - in-memory TTL 캐시(60s, cachetools)는 라우터 측 적용

BEGIN;

CREATE TABLE IF NOT EXISTS token_blacklist (
    id          BIGSERIAL PRIMARY KEY,
    jti         VARCHAR(64)  NOT NULL UNIQUE,
    user_id     INTEGER      NULL REFERENCES account_users(id) ON DELETE SET NULL,
    token_type  VARCHAR(20)  NOT NULL DEFAULT 'access',  -- 'access' or 'refresh'
    reason      VARCHAR(50)  NOT NULL,  -- LOGOUT / LOCK / PASSWORD_CHANGE / FORCED / REVOKED
    expires_at  TIMESTAMP    NOT NULL,  -- 토큰 원래 exp (이후 row 정리 가능)
    revoked_at  TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_token_blacklist_jti ON token_blacklist (jti);
CREATE INDEX IF NOT EXISTS ix_token_blacklist_expires_at ON token_blacklist (expires_at);
CREATE INDEX IF NOT EXISTS ix_token_blacklist_user_id ON token_blacklist (user_id);

-- 검증
SELECT 'token_blacklist 생성 완료' AS status,
       COUNT(*) AS initial_rows
FROM token_blacklist;

COMMIT;
