-- v5.4 (2026-07-02) Role 축소 마이그레이션
-- PRD: docs/prds/PRD_Role_Simplification.md
-- 배경: EnumUserRole 5종 → 2종 (ADMIN/USER) + 등급 그룹 rename → Preset

BEGIN;

-- 1. role 값 이주 (admin 외 → USER)
UPDATE account_users
SET role = 'USER'
WHERE role IN ('MAINTAINER', 'OPERATOR', 'VIEWER', 'GUEST');

-- 검증 1: role 값 = ADMIN/USER만
DO $$
DECLARE invalid_cnt INTEGER;
BEGIN
  SELECT count(*) INTO invalid_cnt FROM account_users WHERE role NOT IN ('ADMIN', 'USER');
  IF invalid_cnt > 0 THEN
    RAISE EXCEPTION 'role 값에 ADMIN/USER 이외 % 건 존재', invalid_cnt;
  END IF;
END $$;

-- 2. 등급 그룹 rename (id 유지, 편집 매트릭스 유지)
UPDATE user_groups SET name = 'Preset - 유지보수자',
                       description = '표준 프리셋 — 유지보수자 권한 매트릭스 (참고 배정용)'
WHERE id = 11 AND name = 'MAINTAINER';
UPDATE user_groups SET name = 'Preset - 운영자',
                       description = '표준 프리셋 — 운영자 권한 매트릭스 (참고 배정용)'
WHERE id = 12 AND name = 'OPERATOR';
UPDATE user_groups SET name = 'Preset - 조회자',
                       description = '표준 프리셋 — 조회자 권한 매트릭스 (참고 배정용)'
WHERE id = 13 AND name = 'VIEWER';

-- 3. admin 사용자 group_id = NULL (ADMIN bypass, 그룹 매트릭스 무관)
UPDATE account_users SET group_id = NULL WHERE role = 'ADMIN';

-- 4. ADMIN 등급 그룹 (id=10) 삭제
DELETE FROM user_groups WHERE id = 10 AND name = 'ADMIN';

-- 5. GUEST 등급 그룹 (id=14) 삭제 (사용자 0명 검증 후)
DO $$
DECLARE guest_users INTEGER;
BEGIN
  SELECT count(*) INTO guest_users FROM account_users WHERE group_id = 14;
  IF guest_users > 0 THEN
    RAISE EXCEPTION 'GUEST 그룹(id=14) 배정 사용자 % 명 — 삭제 불가', guest_users;
  END IF;
END $$;
DELETE FROM user_groups WHERE id = 14 AND name = 'GUEST';

-- 검증 2: user_groups 6건 (팀 3 + Preset 3)
DO $$
DECLARE grp_cnt INTEGER;
BEGIN
  SELECT count(*) INTO grp_cnt FROM user_groups;
  IF grp_cnt < 6 THEN
    RAISE EXCEPTION 'user_groups 6건 이상 기대 vs 실제 %', grp_cnt;
  END IF;
END $$;

COMMIT;
