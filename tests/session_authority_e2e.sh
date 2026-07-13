#!/usr/bin/env bash
# Session Authority E2E — 분석 §14 A01~A18 핵심 시나리오 라이브 검증.
# 사용법: bash session_authority_e2e.sh
set -u
B="https://localhost:8000/api"
PSQL() { docker exec pids-api-postgres psql -U gop_user -d gop -t -c "$1"; }
tok() { python -c "import json,sys;d=json.load(sys.stdin);print(d.get('data',{}).get('access_token',''))" 2>/dev/null; }
rtok() { python -c "import json,sys;d=json.load(sys.stdin);print(d.get('data',{}).get('refresh_token',''))" 2>/dev/null; }
code() { curl -sk -o /dev/null -w "%{http_code}" "$@"; }
pass=0; fail=0
chk() { # desc expected actual
  if [ "$2" = "$3" ]; then echo "  [PASS] $1 ($3)"; pass=$((pass+1)); else echo "  [FAIL] $1 exp=$2 got=$3"; fail=$((fail+1)); fi
}

AT=$(curl -sk -X POST $B/auth/login -H 'Content-Type: application/json' -d '{"login_id":"m_manager","password":"sensorway1"}' | tok)

# probe 계정 준비
PSQL "DELETE FROM account_users WHERE login_id='sa_probe';" >/dev/null 2>&1
curl -sk -o /dev/null -X POST $B/users -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"login_id":"sa_probe","password":"probe1234","name":"SA","role":"USER"}'
PID=$(PSQL "SELECT id FROM account_users WHERE login_id='sa_probe';" | tr -d ' \r\n')

login_probe() { curl -sk -X POST $B/auth/login -H 'Content-Type: application/json' -d '{"login_id":"sa_probe","password":"probe1234"}'; }

echo "=== A01: 잠긴 계정 기존 access → 401 ==="
R=$(login_probe); PT=$(echo "$R" | tok)
chk "active me" 200 "$(code -H "Authorization: Bearer $PT" $B/auth/me)"
PSQL "UPDATE account_users SET is_locked=true WHERE id=$PID;" >/dev/null 2>&1
chk "locked me" 401 "$(code -H "Authorization: Bearer $PT" $B/auth/me)"
PSQL "UPDATE account_users SET is_locked=false WHERE id=$PID;" >/dev/null 2>&1

echo "=== A02: 비활성 계정 기존 access → 401 ==="
R=$(login_probe); PT=$(echo "$R" | tok)
PSQL "UPDATE account_users SET is_active=false WHERE id=$PID;" >/dev/null 2>&1
chk "inactive me" 401 "$(code -H "Authorization: Bearer $PT" $B/auth/me)"
PSQL "UPDATE account_users SET is_active=true WHERE id=$PID;" >/dev/null 2>&1

echo "=== A03: 잠긴 계정 refresh → 401 ==="
R=$(login_probe); RT=$(echo "$R" | rtok)
PSQL "UPDATE account_users SET is_locked=true WHERE id=$PID;" >/dev/null 2>&1
chk "locked refresh" 401 "$(code -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT\"}")"
PSQL "UPDATE account_users SET is_locked=false WHERE id=$PID;" >/dev/null 2>&1

echo "=== A04: 세션 종료(is_active=false) 후 refresh → 401 ==="
R=$(login_probe); RT=$(echo "$R" | rtok)
PSQL "UPDATE user_sessions SET is_active=false WHERE user_id=$PID AND is_active=true;" >/dev/null 2>&1
chk "dead session refresh" 401 "$(code -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT\"}")"

echo "=== A05: 중복 로그인 후 이전 access/refresh 둘 다 401 ==="
R1=$(login_probe); PT1=$(echo "$R1" | tok); RT1=$(echo "$R1" | rtok)
sleep 1
R2=$(login_probe)  # 두 번째 로그인 → 이전 세션 폐기
chk "old access after dup" 401 "$(code -H "Authorization: Bearer $PT1" $B/auth/me)"
chk "old refresh after dup" 401 "$(code -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT1\"}")"

echo "=== A07: admin password reset 후 이전 토큰 401 ==="
R=$(login_probe); PT=$(echo "$R" | tok); RT=$(echo "$R" | rtok)
curl -sk -o /dev/null -X POST $B/users/$PID/reset-password -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"new_password":"newpass9999"}'
chk "old access after reset" 401 "$(code -H "Authorization: Bearer $PT" $B/auth/me)"
chk "old refresh after reset" 401 "$(code -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT\"}")"

echo "=== A16-lite: 정상 refresh 는 여전히 동작(무회귀) ==="
PSQL "UPDATE account_users SET is_locked=false, is_active=true WHERE id=$PID;" >/dev/null 2>&1
# reset로 비번 바뀌었으니 새 비번으로 로그인
R=$(curl -sk -X POST $B/auth/login -H 'Content-Type: application/json' -d '{"login_id":"sa_probe","password":"newpass9999"}'); RT=$(echo "$R" | rtok)
chk "valid refresh works" 200 "$(code -X POST $B/auth/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT\"}")"

# cleanup
PSQL "DELETE FROM account_users WHERE id=$PID;" >/dev/null 2>&1
echo ""
echo "=== RESULT: $pass passed, $fail failed ==="
