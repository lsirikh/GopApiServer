-- v5.4 롤백용 — Enum 5종 + 등급 그룹 5건 재생성
-- ⚠ 주의: admin 외 사용자 role은 USER로 통일됨 → 일괄 VIEWER로 재설정 (원 값 복원 불가)

BEGIN;

-- 1. 등급 그룹 재생성 (ADMIN + GUEST 복원)
INSERT INTO user_groups (id, name, description, permissions, is_active, created_at, updated_at)
VALUES
  (10, 'ADMIN', '권한 등급 — 관리자(전체)', '{}'::jsonb, true, NOW(), NOW()),
  (14, 'GUEST', '권한 등급 — 게스트', '{}'::jsonb, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 2. Preset 그룹을 원 이름으로 복원
UPDATE user_groups SET name = 'MAINTAINER', description = '권한 등급 — 유지보수자'
WHERE id = 11 AND name LIKE 'Preset%';
UPDATE user_groups SET name = 'OPERATOR', description = '권한 등급 — 운영자'
WHERE id = 12 AND name LIKE 'Preset%';
UPDATE user_groups SET name = 'VIEWER', description = '권한 등급 — 조회자'
WHERE id = 13 AND name LIKE 'Preset%';

-- 3. role 값 복원 (USER → VIEWER, admin 유지)
UPDATE account_users SET role = 'VIEWER' WHERE role = 'USER';

-- 4. admin 사용자 group_id 복원
UPDATE account_users SET group_id = 10 WHERE role = 'ADMIN' AND group_id IS NULL;

COMMIT;
