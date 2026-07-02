-- v5.3 (2026-07-02): Legacy User 모델 삭제 마이그레이션
-- PRD: docs/prds/PRD_Legacy_User_Removal.md
-- 배경: GIS 팀 요청 대응 — User(레거시)와 AccountUser 혼용 → AccountUser로 통일

BEGIN;

-- 검증 1: 다른 테이블 FK가 users를 참조하지 않는지 확인
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE contype='f'
      AND pg_get_constraintdef(oid) LIKE '%REFERENCES users(%'
  ) THEN
    RAISE EXCEPTION 'users 테이블 FK 참조가 남아있음 — DROP 불가';
  END IF;
END $$;

-- DROP
DROP TABLE IF EXISTS users CASCADE;

-- 검증 2: DROP 완료 확인
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_tables
    WHERE tablename='users' AND schemaname='public'
  ) THEN
    RAISE EXCEPTION 'users 테이블 DROP 실패';
  END IF;
END $$;

COMMIT;
