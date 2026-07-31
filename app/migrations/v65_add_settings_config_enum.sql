-- v65: config_change_logs.resource_type enum 에 SETTINGS 값 보강 (clone/업그레이드 DB 자가치유).
--
-- 배경: EnumConfigResourceType.SETTINGS 는 세션설정 기능 때 뒤늦게 추가된 값이나,
--   Postgres 네이티브 enum(enumconfigresourcetype)은 create_all() 로 값이 추가되지 않는다.
--   → SETTINGS 이전에 enum 이 생성된 DB(git clone 시 옛 named volume 잔존 등)엔 값이 없어
--     세션설정 변경(PUT /api/settings/session)의 감사 INSERT(resource_type='SETTINGS')가
--     "invalid input value for enum enumconfigresourcetype: SETTINGS" 로 500.
-- 조치: 값이 없으면 추가. (IF NOT EXISTS 로 멱등 — 이미 있으면 no-op)
-- 검증: PG16 에서 트랜잭션 내 ALTER TYPE ADD VALUE 정상(마이그레이션 러너 tx 호환, 커밋 후 사용 가능).

ALTER TYPE enumconfigresourcetype ADD VALUE IF NOT EXISTS 'SETTINGS';
