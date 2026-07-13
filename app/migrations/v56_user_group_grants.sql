-- v56_user_group_grants.sql
-- v5.2 추가 Phase (2026-06-30) — 권한그룹 시간기반 스케쥴링: 부여(grant) 테이블 신설
--
-- 실행: docker exec api-test-postgres psql -U gop_user -d gop -f /app/migrations/v56_user_group_grants.sql
--
-- NOTE:
-- - 앱 startup 의 Base.metadata.create_all 이 ORM 모델(app/models/user.py:UserGroupGrant)로
--   이 테이블을 자동 생성한다. 본 SQL 은 명시 문서화 + psql 직접 적용 대비용이며 IF NOT EXISTS 로 멱등.
-- - PRD: docs/prds/PRD_Permission_Group_Scheduling.md (FR-01, §3.3).
-- - 설계: 스케쥴은 "그룹 정의"가 아니라 "부여"에 건다. 인가 권위는 요청시점 valid_until>now 계산.
--   is_active 는 sweep 비정규화(표시/통지용). valid_until NULL = 상시. revoked_at = soft 회수.
-- - 시각은 naive KST 컨벤션(타 테이블 동일, now() AT TIME ZONE 'Asia/Seoul').

BEGIN;

CREATE TABLE IF NOT EXISTS user_group_grants (
    id           SERIAL       PRIMARY KEY,
    user_id      INTEGER      NOT NULL REFERENCES account_users(id) ON DELETE CASCADE,
    group_id     INTEGER      NOT NULL REFERENCES user_groups(id)   ON DELETE CASCADE,
    valid_from   TIMESTAMP    NOT NULL,
    valid_until  TIMESTAMP    NULL,                                  -- NULL = 상시(무기한)
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,                 -- sweep 비정규화(표시/통지용)
    granted_by   INTEGER      NULL,                                  -- 부여한 ADMIN(감사)
    revoked_at   TIMESTAMP    NULL,                                  -- soft 회수
    created_at   TIMESTAMP    NOT NULL DEFAULT (now() AT TIME ZONE 'Asia/Seoul')
);

-- 사용자별 활성 부여 조회용
CREATE INDEX IF NOT EXISTS ix_grants_user_active ON user_group_grants(user_id, is_active);
-- 만료 sweep 대상 스캔용(상시 NULL 제외)
CREATE INDEX IF NOT EXISTS ix_grants_expiry      ON user_group_grants(valid_until) WHERE valid_until IS NOT NULL;

COMMIT;
