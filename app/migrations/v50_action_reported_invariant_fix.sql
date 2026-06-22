-- v50_action_reported_invariant_fix.sql
-- v4.6 — action_reported 1:N invariant 회복 (차장 결재 필요, 2026-06-22)
--
-- 배경:
--   PRD_Event_ActionEvent_Refactoring.md v2.1 에 따라
--   detection_events.action_reported / malfunction_events.action_reported 는
--   "그 이벤트에 대한 ActionEvent 가 1건 이상 존재" 의 캐시 플래그(String "True"/"False").
--
--   진단 결과 (시드 환경, 2026-06-22):
--     detection_events    : action_reported='True' 총 2,634 건 중 743 건이 actions_count=0
--     malfunction_events  : action_reported='True' 총 4,365 건 중 1,256 건이 actions_count=0
--     합계 1,999 건 invariant 위배 — action_events 에 대응 row 가 없는데 'True' 로 표기됨.
--
--   원인 추정: 과거 ActionEvent 삭제 시 캐시 플래그를 되돌리지 않음 + 시드 데이터 생성 시 순서 어긋남.
--
-- 본 마이그레이션:
--   detection_events / malfunction_events 각각에 대해
--     action_reported = 'True'   IF EXISTS action_events WHERE from_event_id = id (NOT NULL)
--     action_reported = 'False'  ELSE
--
-- 안전성:
--   - 단일 BEGIN/COMMIT 트랜잭션
--   - 실행 전 위배 카운트 SELECT (기대: detection 743, malfunction 1,256, 합 1,999)
--   - TEMP 백업 테이블에 변경 대상 (id, old_value) 보존 (세션 종료 시 자동 폐기, 영구 보존 필요 시 일반 테이블로 변경)
--   - 변경은 'False' → 'True' / 'True' → 'False' 양방향이지만,
--     진단에 따르면 이번 환경에서는 'True' → 'False' 1,999 건만 발생할 것으로 예상
--   - 실행 후 잔여 위배 0 검증 SELECT, 0 아니면 ROLLBACK
--   - action_events.from_event_id IS NULL (orphaned) 는 EXISTS 조건이 자동 제외 → 손대지 않음

BEGIN;

-- =====================================================================
-- 0) 진단 helper view (트랜잭션 내 로컬)
--    invariant 위배 = action_reported 값과 EXISTS(action_events) 결과 불일치
-- =====================================================================
CREATE TEMP VIEW v_detection_invariant_violations AS
SELECT d.id,
       d.action_reported AS old_value,
       CASE WHEN EXISTS (
                 SELECT 1 FROM action_events a
                  WHERE a.from_event_id = d.id
             ) THEN 'True' ELSE 'False' END AS expected_value
  FROM detection_events d
 WHERE d.action_reported <> CASE WHEN EXISTS (
                                       SELECT 1 FROM action_events a
                                        WHERE a.from_event_id = d.id
                                   ) THEN 'True' ELSE 'False' END;

CREATE TEMP VIEW v_malfunction_invariant_violations AS
SELECT m.id,
       m.action_reported AS old_value,
       CASE WHEN EXISTS (
                 SELECT 1 FROM action_events a
                  WHERE a.from_event_id = m.id
             ) THEN 'True' ELSE 'False' END AS expected_value
  FROM malfunction_events m
 WHERE m.action_reported <> CASE WHEN EXISTS (
                                       SELECT 1 FROM action_events a
                                        WHERE a.from_event_id = m.id
                                   ) THEN 'True' ELSE 'False' END;

-- =====================================================================
-- 1) 실행 전 카운트 — 진단치(detection 743, malfunction 1,256)와 대조
-- =====================================================================
SELECT 'BEFORE_DETECTION'   AS phase,
       old_value, expected_value, COUNT(*) AS cnt
  FROM v_detection_invariant_violations
 GROUP BY old_value, expected_value
 ORDER BY old_value, expected_value;
-- 기대: ('True','False', 743). 'False'→'True' row 가 있으면 추가 조사 필요(예상 외).

SELECT 'BEFORE_MALFUNCTION' AS phase,
       old_value, expected_value, COUNT(*) AS cnt
  FROM v_malfunction_invariant_violations
 GROUP BY old_value, expected_value
 ORDER BY old_value, expected_value;
-- 기대: ('True','False', 1256).

-- =====================================================================
-- 2) 변경 대상 백업 (TEMP — 세션 종료 시 폐기; 영구 보존 필요 시 일반 테이블로)
-- =====================================================================
CREATE TEMP TABLE tmp_action_reported_backup_detection AS
SELECT id, old_value, expected_value
  FROM v_detection_invariant_violations;

CREATE TEMP TABLE tmp_action_reported_backup_malfunction AS
SELECT id, old_value, expected_value
  FROM v_malfunction_invariant_violations;

-- =====================================================================
-- 3) detection_events UPDATE
--    invariant 회복: actions 존재 시 'True', 없으면 'False'
--    WHERE 절로 실제 바뀔 row 만 터치 (불필요한 updated_at 갱신 방지)
-- =====================================================================
UPDATE detection_events d
   SET action_reported = b.expected_value
  FROM tmp_action_reported_backup_detection b
 WHERE d.id = b.id;
-- 기대 영향 행 수: 743

-- =====================================================================
-- 4) malfunction_events UPDATE
-- =====================================================================
UPDATE malfunction_events m
   SET action_reported = b.expected_value
  FROM tmp_action_reported_backup_malfunction b
 WHERE m.id = b.id;
-- 기대 영향 행 수: 1,256

-- =====================================================================
-- 5) 실행 후 잔여 위배 검증 — COMMIT 직전 필수 게이트
--    두 SELECT 모두 0 이어야 정상. 1 이상이면 ROLLBACK.
-- =====================================================================
SELECT 'AFTER_DETECTION' AS phase, COUNT(*) AS remaining_violations
  FROM detection_events d
 WHERE d.action_reported <> CASE WHEN EXISTS (
                                       SELECT 1 FROM action_events a
                                        WHERE a.from_event_id = d.id
                                   ) THEN 'True' ELSE 'False' END;
-- 기대: 0

SELECT 'AFTER_MALFUNCTION' AS phase, COUNT(*) AS remaining_violations
  FROM malfunction_events m
 WHERE m.action_reported <> CASE WHEN EXISTS (
                                       SELECT 1 FROM action_events a
                                        WHERE a.from_event_id = m.id
                                   ) THEN 'True' ELSE 'False' END;
-- 기대: 0

-- =====================================================================
-- 6) 결과 요약 (선택 — 로그용)
-- =====================================================================
SELECT 'SUMMARY_DETECTION'   AS phase,
       COUNT(*)                                                 AS updated_rows,
       SUM(CASE WHEN old_value='True'  THEN 1 ELSE 0 END)       AS true_to_false,
       SUM(CASE WHEN old_value='False' THEN 1 ELSE 0 END)       AS false_to_true
  FROM tmp_action_reported_backup_detection;

SELECT 'SUMMARY_MALFUNCTION' AS phase,
       COUNT(*)                                                 AS updated_rows,
       SUM(CASE WHEN old_value='True'  THEN 1 ELSE 0 END)       AS true_to_false,
       SUM(CASE WHEN old_value='False' THEN 1 ELSE 0 END)       AS false_to_true
  FROM tmp_action_reported_backup_malfunction;

-- =====================================================================
-- 7) 정상 시 커밋. 위 5) 잔여 위배가 0 이 아니면 아래 COMMIT 대신 ROLLBACK 으로 변경.
-- =====================================================================
COMMIT;
-- ROLLBACK;  -- 검증 실패 시 위 COMMIT 대신 사용

-- ----------------------------------------------------------------
-- ROLLBACK (커밋 후 사고 발견 시)
--   TEMP 백업은 세션 종료로 사라지므로, 사고 대비 영구 보존이 필요하면
--   2) 의 CREATE TEMP TABLE 을 CREATE TABLE backup_v50_... 로 변경 후 별도 보관 권장.
--   영구 백업이 남아 있다면 다음 패턴으로 원복 가능:
--
--   BEGIN;
--   UPDATE detection_events d
--      SET action_reported = b.old_value
--     FROM backup_v50_action_reported_detection b
--    WHERE d.id = b.id;
--   UPDATE malfunction_events m
--      SET action_reported = b.old_value
--     FROM backup_v50_action_reported_malfunction b
--    WHERE m.id = b.id;
--   COMMIT;
-- ----------------------------------------------------------------
