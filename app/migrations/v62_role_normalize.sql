-- v62 (2026-07-07): account_users.role 정규화 (idempotent, startup 자동 적용)
-- 목적: v5.3 Phase 2 에서 role 을 2종(ADMIN/USER)으로 축소했으나,
--   그 이전에 시드/생성된 옛 값(MAINTAINER/OPERATOR/VIEWER/GUEST)이 DB 에 잔존.
--   v57 마이그레이션이 수동 실행이라 신규 배포/기존 볼륨 DB 에 미적용된 케이스가 있음.
--   → startup 마다 idempotent 하게 role 을 정규화한다 (ADMIN 은 유지, 그 외 폐지값 → USER).
-- 세부 권한은 group_id 매트릭스로 산출되므로 role 통일이 정책에 부합.
-- PRD: PRD_Role_Simplification.md
--
-- ⚠️ 이 파일은 apply_idempotent_migrations 화이트리스트에 등록되어 매 startup 실행됨.
--    role 값 UPDATE 만 수행 — 파괴적 DDL(그룹 삭제 등) 없음. 재실행 완전 안전.

BEGIN;

UPDATE account_users
   SET role = 'USER',
       updated_at = NOW()
 WHERE role NOT IN ('ADMIN', 'USER');

COMMIT;
