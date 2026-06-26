-- v54_tracking_points.sql
-- v4.11 (2026-06-26) — 추적 이력(Tracking) 영속 테이블 신설
--
-- 실행: docker exec api-test-postgres psql -U gop_user -d gop -f /app/migrations/v54_tracking_points.sql
--
-- NOTE:
-- - 앱 startup 의 Base.metadata.create_all 이 ORM 모델(app/models/tracking.py)로
--   이 테이블을 자동 생성한다. 본 SQL 은 명시 문서화 + create_all 미사용(psql 직접) 대비용이며,
--   IF NOT EXISTS 로 멱등하다(이미 생성됐으면 skip).
-- - 컬럼 타입은 ORM(create_all) 산출과 정합: observed_at/created_at = TIMESTAMP(naive KST 컨벤션,
--   audit_logs 동일). KSTDatetime 응답 직렬화가 +09:00 라벨을 부여한다.
-- - 인제스트(gis-ingest 워커)는 raw asyncpg 로 INSERT ... ON CONFLICT (track_id, observed_at)
--   DO NOTHING 을 사용(멱등). 본 테이블은 audit append-only 트리거 대상이 아니다(자유 삭제 가능).

BEGIN;

CREATE TABLE IF NOT EXISTS track_points (
    id             BIGSERIAL PRIMARY KEY,
    camera_id      INTEGER          NOT NULL,                 -- body.camera_id (비-FK)
    track_id       VARCHAR(64)      NOT NULL,                 -- targets[].track_id
    label          VARCHAR(32),                               -- targets[].label
    threat_level   VARCHAR(16),                               -- targets[].threat_level (tolerant)
    latitude       DOUBLE PRECISION NOT NULL,                 -- targets[].location.latitude
    longitude      DOUBLE PRECISION NOT NULL,                 -- targets[].location.longitude
    distance_m     DOUBLE PRECISION,                          -- targets[].location.distance_m
    confidence     DOUBLE PRECISION,                          -- targets[].confidence
    observed_at    TIMESTAMP        NOT NULL,                 -- targets[].observed_at (keyset 정렬키)
    tracking_state VARCHAR(16),                               -- body.tracking
    speed_mps      DOUBLE PRECISION,                          -- (선택) 서버 계산
    session_seq    INTEGER,                                   -- (선택) 세션 시퀀스
    created_at     TIMESTAMP        NOT NULL DEFAULT now(),   -- 인제스트 시각
    CONSTRAINT uq_track_points_track_observed UNIQUE (track_id, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_track_points_observed_at
    ON track_points (observed_at);
CREATE INDEX IF NOT EXISTS idx_track_points_camera_observed
    ON track_points (camera_id, observed_at);

-- 보존정책(기본 7일) purge 함수 — 스케줄 호출은 운영 선택(또는 후속 cron)
CREATE OR REPLACE FUNCTION purge_track_points(retain_days INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted INTEGER;
BEGIN
    DELETE FROM track_points
    WHERE observed_at < (now() - (retain_days || ' days')::interval);
    GET DIAGNOSTICS deleted = ROW_COUNT;
    RETURN deleted;
END;
$$ LANGUAGE plpgsql;

-- 검증
SELECT 'track_points 생성 완료' AS status,
       COUNT(*) AS initial_rows
FROM track_points;

COMMIT;
