-- v53_permissions_normalization.sql
-- v4.9 Phase 3 (A-2.4) — UserGroup.permissions 정규화 (flat string → nested dict)
--
-- 차장님 결재 D3 (PRD v4.9 권고 적용):
-- "운영팀 사전 승인 가정 — dry-run + alembic downgrade 검증"
--
-- 변환 규칙:
--   "rw" → {view:true, edit:true, delete:false, control:false}
--   "r"  → {view:true, edit:false, delete:false, control:false}
--   nested dict 이미 정규화된 row는 손대지 않음 (idempotent)
--
-- 시드 (관리팀/관제팀/유지보수팀) flat 'rw'/'r' 정규화

BEGIN;

-- 변경 전 상태
SELECT 'BEFORE' AS phase, id, name, permissions FROM user_groups ORDER BY id;

-- 정규화 함수 (단발성, COMMIT 후 자동 폐기)
CREATE OR REPLACE FUNCTION pg_temp.fn_normalize_permission_value(v jsonb) RETURNS jsonb AS $$
BEGIN
    -- nested object면 이미 정규화됨 (예: {"view":true, "edit":true})
    IF jsonb_typeof(v) = 'object' THEN
        RETURN v;
    END IF;

    -- string flat → nested dict 변환
    IF v::text = '"rw"' THEN
        RETURN '{"view": true, "edit": true, "delete": false, "control": false}'::jsonb;
    ELSIF v::text = '"r"' THEN
        RETURN '{"view": true, "edit": false, "delete": false, "control": false}'::jsonb;
    ELSE
        -- 미지정 값 → 모두 false (Audit REJECTED 큐에 별도 보고 권고)
        RETURN '{"view": false, "edit": false, "delete": false, "control": false}'::jsonb;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- modules.* 각 키별 변환
UPDATE user_groups
SET permissions = jsonb_set(
    COALESCE(permissions, '{}'::jsonb),
    '{modules}',
    (
        SELECT jsonb_object_agg(k, pg_temp.fn_normalize_permission_value(v))
        FROM jsonb_each(COALESCE(permissions->'modules', permissions, '{}'::jsonb)) AS m(k, v)
        WHERE k IN ('devices', 'events', 'reports', 'cameras', 'users', 'user_groups', 'audit_logs', 'servers')
    )
)
WHERE permissions IS NOT NULL;

-- modules 키가 없는 row의 기존 평탄 구조를 modules로 감싸기 (시드는 {"devices":"rw"} 평탄)
UPDATE user_groups
SET permissions = jsonb_build_object('modules', permissions->'modules', 'device_groups', permissions->'device_groups')
WHERE permissions ? 'modules' AND NOT (permissions ? 'device_groups')
  AND jsonb_typeof(permissions->'device_groups') IS NULL;

-- 변경 후 검증
SELECT 'AFTER' AS phase, id, name, permissions FROM user_groups ORDER BY id;

COMMIT;
