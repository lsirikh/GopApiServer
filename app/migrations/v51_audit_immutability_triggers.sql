-- v51_audit_immutability_triggers.sql
-- v4.6 — Phase 12-7f (audit immutability) — 2026-06-22
--
-- 배경:
--   PRD §7 (Phase 12-7f). audit_logs / config_change_logs / user_login_logs 3 테이블은
--   "append-only(추가 전용)" 이어야 한다. INSERT 만 허용, UPDATE / DELETE 는
--   응용 계층(SQLAlchemy)뿐 아니라 DB 레벨에서도 차단되어야 감사 무결성이 보장된다.
--
--   현재(v50 까지)는 코드 상으로 UPDATE/DELETE 경로가 노출되어 있지 않을 뿐,
--   psql 직접 접속·관리자 실수·향후 신규 기능 추가 시 변조 가능성이 남아 있음.
--
-- 본 마이그레이션:
--   1) fn_block_audit_modification() — UPDATE/DELETE 시 RAISE EXCEPTION 던지는 트리거 함수
--   2) audit_logs / config_change_logs / user_login_logs 3 테이블에
--      BEFORE UPDATE OR DELETE … FOR EACH ROW EXECUTE FUNCTION 트리거 부착
--
-- 안전성:
--   - 단일 BEGIN/COMMIT 트랜잭션
--   - 기존 동명 트리거가 있을 수 있으므로 DROP TRIGGER IF EXISTS 선행
--   - CREATE OR REPLACE FUNCTION 으로 재실행 가능 (idempotent)
--   - INSERT 경로는 트리거 대상이 아니므로 정상 허용 (append-only 의미 유지)
--   - TRUNCATE 는 BEFORE UPDATE/DELETE FOR EACH ROW 트리거로는 차단되지 않음 —
--     실제 환경에서는 DB role 권한(REVOKE TRUNCATE / DELETE / UPDATE)으로 보완하는 것이
--     정석이지만 본 마이그레이션 범위는 명세에 따라 row-level 트리거에 한정한다.
--
-- 검증 (스모크):
--   - INSERT INTO audit_logs(...) VALUES (...) → 성공
--   - UPDATE audit_logs SET description='x' WHERE id=... → ERROR
--       (RAISE EXCEPTION 'audit table (audit_logs) is append-only — UPDATE/DELETE blocked')
--   - DELETE FROM audit_logs WHERE id=...                → 동일 ERROR
--   - 위 두 경로가 동일하게 config_change_logs / user_login_logs 에서도 차단

BEGIN;

-- =====================================================================
-- 1) Trigger function — UPDATE/DELETE 시 즉시 예외 발생
--    TG_TABLE_NAME 으로 어느 audit 테이블이 차단됐는지 메시지에 포함.
-- =====================================================================
CREATE OR REPLACE FUNCTION fn_block_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit table (%) is append-only — UPDATE/DELETE blocked', TG_TABLE_NAME
        USING ERRCODE = 'P0001';
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 2) audit_logs
-- =====================================================================
DROP TRIGGER IF EXISTS trg_audit_logs_immutable ON audit_logs;
CREATE TRIGGER trg_audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION fn_block_audit_modification();

-- =====================================================================
-- 3) config_change_logs
-- =====================================================================
DROP TRIGGER IF EXISTS trg_config_change_logs_immutable ON config_change_logs;
CREATE TRIGGER trg_config_change_logs_immutable
    BEFORE UPDATE OR DELETE ON config_change_logs
    FOR EACH ROW
    EXECUTE FUNCTION fn_block_audit_modification();

-- =====================================================================
-- 4) user_login_logs
-- =====================================================================
DROP TRIGGER IF EXISTS trg_user_login_logs_immutable ON user_login_logs;
CREATE TRIGGER trg_user_login_logs_immutable
    BEFORE UPDATE OR DELETE ON user_login_logs
    FOR EACH ROW
    EXECUTE FUNCTION fn_block_audit_modification();

-- =====================================================================
-- 5) 등록 결과 점검 (운영자 확인용)
-- =====================================================================
SELECT event_object_table AS table_name,
       trigger_name,
       action_timing,
       string_agg(event_manipulation, ',' ORDER BY event_manipulation) AS events
  FROM information_schema.triggers
 WHERE event_object_table IN ('audit_logs', 'config_change_logs', 'user_login_logs')
   AND trigger_name LIKE 'trg_%_immutable'
 GROUP BY event_object_table, trigger_name, action_timing
 ORDER BY event_object_table;
-- 기대:
--   audit_logs            | trg_audit_logs_immutable            | BEFORE | DELETE,UPDATE
--   config_change_logs    | trg_config_change_logs_immutable    | BEFORE | DELETE,UPDATE
--   user_login_logs       | trg_user_login_logs_immutable       | BEFORE | DELETE,UPDATE

COMMIT;
-- ROLLBACK; -- 검증 실패 시 위 COMMIT 대신 사용

-- ----------------------------------------------------------------
-- ROLLBACK (트리거 제거 절차) — 운영 사고 시 응급 복구용
--
--   BEGIN;
--     DROP TRIGGER IF EXISTS trg_audit_logs_immutable         ON audit_logs;
--     DROP TRIGGER IF EXISTS trg_config_change_logs_immutable ON config_change_logs;
--     DROP TRIGGER IF EXISTS trg_user_login_logs_immutable    ON user_login_logs;
--     DROP FUNCTION IF EXISTS fn_block_audit_modification();
--   COMMIT;
-- ----------------------------------------------------------------
