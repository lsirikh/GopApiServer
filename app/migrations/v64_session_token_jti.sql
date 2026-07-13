-- v64: E1/P1-10 — 세션 토큰 원문 저장 제거 준비.
--
-- 배경: user_sessions.token/refresh_token 에 access/refresh JWT **원문**(크리덴셜)이 저장돼
--       DB/로그/백업 유출 시 즉시 토큰 탈취 가능(§4.2). 코드가 원문 대신 jti 를 저장하도록 전환됨.
-- 조치:
--   1) refresh_expires_at 컬럼 추가(블랙리스트 TTL 원천).
--   2) 기존 활성 세션 중 원문 토큰(JWT 는 'eyJ' 로 시작)을 저장한 rows 를 무효화 →
--      jti 기반 폐기 로직이 원문을 jti 로 오인하지 않도록. 해당 사용자는 재로그인(활성 세션 소수).
--
-- 멱등성: ADD COLUMN IF NOT EXISTS + UPDATE 는 이미 무효화된 rows 재대상 아님.

BEGIN;

ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS refresh_expires_at TIMESTAMP;

UPDATE user_sessions
SET is_active = false,
    logout_reason = 'TOKEN_STORE_MIGRATION',
    logged_out_at = now()
WHERE is_active = true
  AND (token LIKE 'eyJ%' OR token LIKE 'pending-%');

COMMIT;
