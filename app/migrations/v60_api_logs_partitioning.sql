-- v60_api_logs_partitioning.sql
-- v6.0 (2026-07-03) — api_logs 월별 파티셔닝 전환 (A-7 #6)
--
-- 실행: docker exec api-test-postgres psql -U gop_user -d gop -f /app/migrations/v60_api_logs_partitioning.sql
--
-- 배경:
--   문서 시점(GOPDB_통합_원인분석_및_조치_20260702.md, A-7 #6) api_logs 크기 10,606,885행 / 3.2GB.
--   v5.4 도입된 TTL sweep(30일 초과 DELETE)은 무한 성장은 막지만 삭제 비용/인덱스 팽창 문제 잔존.
--   본 마이그레이션은 PostgreSQL native RANGE 파티셔닝으로 전환하여 30일 초과 파티션을 DROP으로
--   O(1) 회수 가능하게 한다.
--
-- 전략:
--   - PARTITION BY RANGE ("timestamp"), 월별 파티션.
--   - 기존 api_logs → api_logs_v5 로 rename → 신규 파티션 부모 테이블(api_logs) 생성.
--   - 기존 데이터는 default 대체 파티션(api_logs_before_partition, 2026-07 이전 전체)에 이관.
--   - 당월(2026-07) + 향후 3개월(2026-08~10) 파티션을 미리 생성.
--   - PK 는 (id, "timestamp") 복합 — 파티션 키가 반드시 PK 에 포함되어야 함 (PostgreSQL 제약).
--   - 인덱스는 파티션 부모에 CREATE INDEX 하여 자동 상속.
--
-- 유의:
--   - 트랜잭션 단위로 실행되므로 도중 실패 시 자동 롤백.
--   - api_logs.body 는 nullable=True(VARCHAR 2000). 기존 스키마와 동일 유지.
--   - 향후 파티션 생성/DROP 는 docs/API_LOGS_PARTITION_MAINTENANCE.md 참조.
--   - v5.4 TTL sweep(api_logs_sweep_service.py) 은 파티션 DROP 자동화로 대체될 예정.
--     본 마이그레이션 이후에도 sweep 자체는 그대로 동작(DELETE)하지만, 대량 데이터는 파티션 DROP 이 훨씬 저렴.
--
-- ROLLBACK 절차(수동):
--   BEGIN;
--     ALTER TABLE api_logs RENAME TO api_logs_v6_partitioned;
--     ALTER TABLE api_logs_v5 RENAME TO api_logs;   -- v5 백업이 남아있어야 함
--   COMMIT;

BEGIN;

-- 1. 기존 테이블 백업 이름 변경
ALTER TABLE api_logs RENAME TO api_logs_v5;

-- 1-a. 기존 인덱스 이름도 v5 접미어로 rename → 8단계에서 새 인덱스와 충돌 방지.
--      (PostgreSQL 은 인덱스 이름을 스키마 전역 네임스페이스로 관리하므로,
--       테이블만 rename 하면 인덱스는 원래 이름 그대로 남는다.)
ALTER INDEX IF EXISTS api_logs_pkey           RENAME TO api_logs_v5_pkey;
ALTER INDEX IF EXISTS ix_api_logs_id          RENAME TO ix_api_logs_v5_id;
ALTER INDEX IF EXISTS ix_api_logs_timestamp   RENAME TO ix_api_logs_v5_timestamp;
ALTER INDEX IF EXISTS ix_api_logs_resource    RENAME TO ix_api_logs_v5_resource;
ALTER INDEX IF EXISTS ix_api_logs_method      RENAME TO ix_api_logs_v5_method;
ALTER INDEX IF EXISTS ix_api_logs_request_id  RENAME TO ix_api_logs_v5_request_id;
ALTER INDEX IF EXISTS ix_api_logs_client_uuid RENAME TO ix_api_logs_v5_client_uuid;

-- 2. 신규 파티션 부모 테이블 (동일 컬럼)
CREATE TABLE api_logs (
    id             SERIAL,
    "timestamp"    TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    resource       VARCHAR(100)  NOT NULL,
    method         VARCHAR(10)   NOT NULL,
    client_uuid    VARCHAR(100),
    request_id     VARCHAR(100),
    description    VARCHAR(500)  NOT NULL,
    status_code    INTEGER,
    user_id        INTEGER,
    body           VARCHAR(2000),
    param          VARCHAR(1000),
    error_message  VARCHAR(1000),
    PRIMARY KEY (id, "timestamp")
) PARTITION BY RANGE ("timestamp");

-- 3. 초기 파티션 (당월 + 3개월 미리 생성)
CREATE TABLE api_logs_2026_07 PARTITION OF api_logs
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE api_logs_2026_08 PARTITION OF api_logs
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE api_logs_2026_09 PARTITION OF api_logs
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE api_logs_2026_10 PARTITION OF api_logs
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

-- 4. 2026-07-01 이전 데이터 수용용 파티션 (기존 데이터 이관 대상)
CREATE TABLE api_logs_before_partition PARTITION OF api_logs
    FOR VALUES FROM (MINVALUE) TO ('2026-07-01');

-- 5. 기존 데이터 이관 (v5 → 파티션 부모 = 각 파티션으로 자동 라우팅)
INSERT INTO api_logs (id, "timestamp", resource, method, client_uuid, request_id,
                     description, status_code, user_id, body, param, error_message)
SELECT id, "timestamp", resource, method, client_uuid, request_id,
       description, status_code, user_id, body, param, error_message
FROM api_logs_v5;

-- 6. sequence 재정합 (id 자동 증가 연속성 보장)
SELECT setval(
    pg_get_serial_sequence('api_logs', 'id'),
    COALESCE((SELECT MAX(id) FROM api_logs), 1),
    true
);

-- 7. 인덱스 재생성 (파티션 부모에 생성 → 파티션 자동 상속)
CREATE INDEX ix_api_logs_id          ON api_logs (id);
CREATE INDEX ix_api_logs_timestamp   ON api_logs ("timestamp");
CREATE INDEX ix_api_logs_resource    ON api_logs (resource);
CREATE INDEX ix_api_logs_method      ON api_logs (method);
CREATE INDEX ix_api_logs_request_id  ON api_logs (request_id);
CREATE INDEX ix_api_logs_client_uuid ON api_logs (client_uuid);

-- 8. 이전 테이블 삭제
--    NOTE: 롤백 여지를 원할 경우 아래 DROP 라인을 주석 처리하여
--          api_logs_v5 를 배포 후 N일간 유지 후 별도 스크립트로 정리 가능.
DROP TABLE api_logs_v5;

COMMIT;
