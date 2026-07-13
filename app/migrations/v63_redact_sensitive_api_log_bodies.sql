-- v63: SEC-01 — 기존 api_logs.body 에 평문 저장된 민감 데이터(로그인 비밀번호/토큰 등) 정리.
--
-- 배경: logging.py 가 POST/PUT/PATCH 요청 body 를 마스킹 없이 저장해,
--       /api/auth/login·/api/auth/refresh·비밀번호 변경/초기화 요청의 비밀번호·토큰이
--       api_logs.body 에 평문으로 남아 있었다(무인증 /api/logs 로 조회 가능했음).
-- 조치: 신규 로그는 코드(redact_request_body)에서 마스킹한다. 이 마이그레이션은
--       과거 rows 를 정리한다 — auth/비밀번호 관련 리소스 또는 민감 키를 포함하는 body 를 NULL 로.
--
-- 멱등성: body IS NOT NULL 조건으로 이미 정리된(=NULL) rows 는 재대상 아님 → 반복 실행 안전.

BEGIN;

UPDATE api_logs
SET body = NULL
WHERE body IS NOT NULL
  AND (
        resource ILIKE 'auth/login%'
     OR resource ILIKE 'auth/refresh%'
     OR resource ILIKE '%password%'
     OR body ILIKE '%"password"%'
     OR body ILIKE '%"current_password"%'
     OR body ILIKE '%"new_password"%'
     OR body ILIKE '%"user_password"%'
     OR body ILIKE '%"access_token"%'
     OR body ILIKE '%"refresh_token"%'
     OR body ILIKE '%"token"%'
     OR body ILIKE '%"secret"%'
     OR body ILIKE '%"authorization"%'
  );

COMMIT;
