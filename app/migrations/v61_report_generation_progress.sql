-- v61 (2026-07-05): report_generations 진행률 컬럼 추가
-- 목적: wall-clock timeout(180s) 대신 진행률 stall 감지로 hang 판정.
--       클라 폴링이 progress_pct/progress_stage를 읽어 UX 표시.
-- PRD: PRD_GOP_Server_Reports_Generation_Lifecycle 후속

BEGIN;

ALTER TABLE report_generations
    ADD COLUMN IF NOT EXISTS progress_pct INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS progress_stage VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS progress_updated_at TIMESTAMP NULL;

-- 종료 상태(COMPLETED/FAILED/CANCELLED)는 100%로 백필
UPDATE report_generations
   SET progress_pct = 100,
       progress_stage = 'done',
       progress_updated_at = COALESCE(completed_at::timestamp, created_at)
 WHERE status IN ('COMPLETED', 'FAILED', 'CANCELLED')
   AND progress_pct = 0;

-- stall 감지용 인덱스 (워치도그가 status IN ('PENDING','GENERATING') + progress_updated_at 조회)
CREATE INDEX IF NOT EXISTS ix_report_generations_stall
    ON report_generations (status, progress_updated_at)
 WHERE status IN ('PENDING', 'GENERATING');

COMMIT;
