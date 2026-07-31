-- v66_datetime_to_utc.sql
-- datetime-timezone-unification (Option B): 전 naive datetime 컬럼을 timestamptz(UTC 저장)로 전환.
--
-- 규약: 저장 UTC(timestamptz) / 출력 DISPLAY_TZ / 입력 aware 권장. 다국가 이식 가능.
--
-- ★ 조건부 멱등: 대상 = `timestamp without time zone` 컬럼만. 재실행 시 이미 timestamptz면
--   information_schema 에서 미선택 → 자동 skip(이중변환 방지). fresh DB(모델=UtcDateTime로 create_all)
--   에서도 naive 컬럼이 없으므로 no-op. → fresh/기존/옛버전 사이트 모두 안전.
--
-- ★ 컬럼별 방향(USING ... AT TIME ZONE):
--     - 대부분(과거 KST 벽시계 저장) = 'Asia/Seoul'  → 정확한 UTC instant 로 재해석(무손실, 리허설 V-02 확인).
--     - token_blacklist(UTC 기록: default=datetime.utcnow) = 'UTC'  (리허설 V-06 확인).
--       (주: expires_at 은 세션복사(KST)/utcnow(UTC) 혼합 이력 가능하나, 블랙리스트는 존재확인 기반 +
--        TTL 로 단명 → 값 오차는 보안 무영향. 향후 writer 는 utc_now() 단일.)
--
-- ★ 제외:
--     - api_logs 파티션 계열(api_logs, api_logs_YYYY_MM, api_logs_before_partition):
--       `timestamp` 가 파티션 키라 직접 ALTER 불가(리허설 확인) → 별도 재생성 마이그(v67, Phase 4).
--     - schema_migrations: 마이그 추적 내부 테이블.
--
-- ★ report_generations.start_date/end_date/completed_at 은 이미 timestamptz(정확한 UTC) → 대상 아님(skip).

DO $$
DECLARE
    r RECORD;
    origin_tz TEXT;
BEGIN
    FOR r IN
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND data_type = 'timestamp without time zone'
          AND table_name NOT LIKE 'api_logs%'
          AND table_name <> 'schema_migrations'
        ORDER BY table_name, column_name
    LOOP
        IF r.table_name = 'token_blacklist' THEN
            origin_tz := 'UTC';
        ELSE
            origin_tz := 'Asia/Seoul';
        END IF;

        EXECUTE format(
            'ALTER TABLE public.%I ALTER COLUMN %I TYPE timestamptz USING %I AT TIME ZONE %L',
            r.table_name, r.column_name, r.column_name, origin_tz
        );
        RAISE NOTICE 'v66: converted %.% (origin %)', r.table_name, r.column_name, origin_tz;
    END LOOP;
END $$;
