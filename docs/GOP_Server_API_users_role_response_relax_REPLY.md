# GOP 서버(API) 응답: `AccountUserResponse.role` 이슈 처리 결과 통지

- **작성일**: 2026-07-06
- **응답 대상**: 다른 PC 배포 팀 (사용자 이슈 리포트 세션)
- **응답 세션**: `pids-api-server` 서버 세션
- **커밋/태그**: `release/v6.0` 위 → `v6.0-users_role_response_relax`
- **브랜치**: `release/v6.0` (Swagger `info.version=6.0.0`)
- **관련 선행 대응**: `docs/GOP_Server_API_servers_port0_issue_REPLY.md` (동일 패턴 이슈, `servers.port=0`)

---

## 📌 두괄식 결론

| 항목 | 상태 |
|---|---|
| 이슈 원인 진단 | ✅ 서버측 응답 스키마 설계 실수 (Postel's Law 위배) — `servers.port=0` 과 동일 패턴 |
| 서버측 근본 픽스 | ✅ 완료 (2층 방어: L1 스키마 완화 + L2 목록 fault tolerance) |
| 실측 검증 | ✅ `UPDATE account_users SET role='OPERATOR' WHERE id=23` 인위 주입 후 GET `/api/users` **500 → 200**, 해당 행 그대로 노출 |
| 데이터 위생 조치 필요 | ⚠️ **원격 GOPDB `account_users.role` 옛 값 정리 필요** (아래 §3) |
| 원격 GOPDB 배포 | ⚠️ 서버 팀이 원격 GOPDB 이미지 재빌드/재기동 후 별도 통지 |

**요약**: 서버 응답 500은 근본 시정 완료. 다만 이미 DB에 박힌 옛 `role` 값(OPERATOR/MAINTAINER/VIEWER/GUEST)은 서버 픽스가 지우지 못하므로, GOP DB 관리자가 원격 DB에서 SQL `UPDATE` 로 정리 부탁드립니다.

---

## 1. 발단 — 사용자 리포트

다른 PC에서 `git clone` 후 `docker compose up` → `admin` 로그인 성공 → 그 토큰으로 `GET /api/users?page=1&limit=100` 호출:

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error: 1 validation error for AccountUserResponse\nrole\n  Input should be 'ADMIN' or 'USER' [type=enum, input_value='OPERATOR', input_type=str]",
    "details": null
  }
}
```

이전에 `servers.port=0` 이슈로 이미 확인된 **정확히 같은 패턴**입니다.

---

## 2. 원인 자인 (반복된 설계 실수)

`v5.3 Phase 2` (2026-07-02) 에서 `EnumUserRole` 을 5종 → 2종(`ADMIN`/`USER`)으로 축소했습니다. 그러나:

1. **응답 스키마에 Enum 그대로 유지** — `AccountUserResponse.role: EnumUserRole`
2. **DB 데이터 마이그레이션 부재/부분적** — 옛 role 값(`OPERATOR`, `MAINTAINER`, `VIEWER`, `GUEST`) 이 여전히 남은 사이트 존재
3. **`example="OPERATOR"`** 로 되어 있음 — v5.3 이후 무효 값을 예시로 유지 (더 웃긴 지뢰)

**결과**: 옛 role 값 행이 응답에 담길 때 pydantic 검증 실패 → 목록 API 전체 500.

**행 1개가 목록 전체를 죽인다** — 이전 `servers.port=0` 리포트에서 지적하신 것과 동일한 blast radius 문제.

**서버 팀 반성**: 이전 사이클(`v6.0-servers_port_response_relax`)에서 "유사 필드 감사 별도 사이클 진행 예정"이라고만 하고 즉시 스캔하지 못한 것이 이번 재발의 직접 원인입니다. 이번 사이클 후 실제로 감사 진행합니다 (§7).

---

## 3. 서버측 픽스 (2층 방어, `servers` 케이스와 동일 방법론)

### L1. 응답 스키마 Enum → str 완화

**파일**: `app/schemas/user.py`

| 스키마 | 필드 | 이전 | 이후 |
|---|---|---|---|
| `AccountUserCreate.role` | 요청 | `Optional[EnumUserRole]` | **유지** (새 데이터 위생) |
| `AccountUserUpdate.role` | 요청 | `Optional[EnumUserRole]` | **유지** |
| **`AccountUserResponse.role`** | 응답 | `EnumUserRole` | **`str`** — `"ADMIN/USER, 옛 데이터는 OPERATOR/MAINTAINER/VIEWER/GUEST 가능"` description |
| **`AccountUserNestedResponse.role`** | 응답 (중첩) | `EnumUserRole` | **`str`** |
| **`UserSessionResponse.role`** | 응답 (세션 join) | `Optional[EnumUserRole]` | **`Optional[str]`** |

`example` 도 `"OPERATOR"` → `"USER"` 로 갱신 (v5.3 이후 유효 값).

### L2. 목록 fault tolerance

**파일**: `app/routers/users.py` `get_users`

```python
# v6.0-users_role_response_relax L2 (2026-07-06)
data = []
for u in users:
    try:
        data.append(AccountUserResponse.model_validate(u))
    except Exception as exc:
        logger.warning(
            "[users.list] response 직렬화 실패 → 목록에서 skip: user_id=%s login_id=%r role=%r reason=%s",
            u.id, u.login_id, u.role, exc,
        )
```

**즉 이제**:
- 한 사용자의 스키마 위반이 있어도 나머지 정상 사용자는 그대로 반환
- 서버 로그에 `[users.list] response 직렬화 실패 → 목록에서 skip: user_id=X login_id='...' role='...' reason=...` WARN 남김

---

## 4. 로컬 실측 검증

로컬(`pids-api-server`, PostgreSQL 16)에서 4단계 실측:

| # | 시나리오 | HTTP | 상세 |
|---|---|---|---|
| 1 | 회귀 (정상 상태) | 200 | 12 rows |
| 2 | **인위 주입** — `UPDATE account_users SET role='OPERATOR' WHERE id=23` | — | 저장 확인 |
| 3 | **핵심** — GET /api/users (OPERATOR 존재 상태) | **200** ✅ | **12 rows + id=23 role=OPERATOR 그대로 노출** |
| 4 | 원위치 — `UPDATE ... SET role='USER'` | — | 정상 복구 |

이전엔 500이었을 시나리오가 이제 200으로 정상 처리됨.

---

## 5. 원격 GOPDB 데이터 위생 조치 (요청)

⚠️ 서버 픽스는 응답 500을 막는 대증요법이고, 근본은 데이터 정리입니다.

### 진단

```sql
SELECT role, count(*)
  FROM account_users
 GROUP BY role
 ORDER BY 2 DESC;
```

기대 출력 (v5.3 이후):
```
 role  | count
-------+------
 ADMIN |   ?
 USER  |   ?
```

만약 `OPERATOR`, `MAINTAINER`, `VIEWER`, `GUEST` 가 보이면 아래 정리 필요.

### 정리 (권장 — v5.3 Phase 2 재매핑 규칙)

```sql
-- v5.3 Phase 2 정책 재적용:
--   OPERATOR / MAINTAINER / VIEWER / GUEST → USER (권한은 group_id 매트릭스로 부여)
--   ADMIN 은 그대로

BEGIN;
UPDATE account_users
   SET role = 'USER',
       updated_at = NOW()
 WHERE role IN ('OPERATOR', 'MAINTAINER', 'VIEWER', 'GUEST');
COMMIT;

-- 확인
SELECT role, count(*) FROM account_users GROUP BY role;
```

주의: 감사 로그 `audit_logs.actor_role` 은 append-only 라 **건드리지 않음**. 옛 감사 이력은 그대로 `OPERATOR` 등으로 남습니다 (이력 보존).

### 검증

```bash
GET /api/users   (Bearer 토큰)   →   200 (정상 유지)
```

---

## 6. 다른 PC 즉시 적용 방법

배포 대상 다른 PC 에서 이번 픽스가 적용된 이미지로 재기동:

```bash
# 1) 최신 코드 pull
git pull origin release/v6.0

# 2) 새 이미지 빌드
docker compose build api-server

# 3) 재기동
docker compose up -d --no-deps api-server

# 4) 로컬 DB 정리 (§5 SQL 실행)
docker exec pids-api-postgres psql -U gop_user -d gop -f - <<'EOF'
BEGIN;
UPDATE account_users
   SET role = 'USER', updated_at = NOW()
 WHERE role IN ('OPERATOR', 'MAINTAINER', 'VIEWER', 'GUEST');
COMMIT;
EOF

# 5) 재로그인 후 재시도
```

---

## 7. 서버측 후속 조치 — 유사 필드 스캔 (약속)

`servers.port=0` REPLY §7 에서 예고한 "유사 필드 감사" 를 이번 이슈로 촉발되어 즉시 착수 예정:

**감사 대상**: 모든 `*Response` 스키마의 Enum/제약 필드가 요청과 응답 사이에서 대칭인지, DB 옛 값이 응답을 죽일 위험이 있는지.

**후보 지점 (이번 사이클 후 별도 감사)**:
- `EnumServerStatus` — `servers.status`, `system_events.severity` 등
- `EnumDeviceStatus` — `devices.status`
- `EnumDeviceCategory`, `EnumDeviceType`
- `EnumEventType`, `EnumEventResult`
- `AuditLog.actor_role`, `AuditLog.action_type`, `AuditLog.action_status`
- `EnumReportPeriod`, `EnumReportStatus`
- `EnumLoginAction`, `EnumLoginResult`
- `EnumConfigResourceType`, `EnumConfigActionType`

별도 감사 사이클 태그 예정: `v6.0-response_schema_audit`.

---

## 8. 서버측 정책 재확인

`servers.port=0` REPLY §7 에서 표명한 원칙 재확인:

1. **응답 스키마에는 요청 제약을 그대로 복사하지 않는다** — Postel's Law 적용
2. **목록 API 는 행별 실패에 관대해야 한다** — 한 행이 전체를 죽이지 않도록 fault tolerance
3. **Enum 축소는 데이터 마이그레이션과 병행해야** — 뒤에 축소하면 옛 데이터가 지뢰
4. **응답 스키마도 pydantic 검증이 있다** — 요청만 신경 쓰면 안 됨

원칙은 알고 있었으나 실제 실행에서 반복 위반. 이번 감사로 마무리하겠습니다.

---

## 9. 참조

- **선행 REPLY**: `docs/GOP_Server_API_servers_port0_issue_REPLY.md` (동일 패턴)
- **서버 커밋**: 태그 `v6.0-users_role_response_relax` (release/v6.0 위)
- **CHANGELOG**: `CHANGELOG.md` → v6.0-users_role_response_relax 섹션
- **파일**: `app/schemas/user.py` (L1), `app/routers/users.py` (L2)
- **저장소**: origin=`github.com/lsirikh/GopApiServer`, gitea=`192.168.202.160:3000/Sensorway_SW/GOP-Api-Db-Server`

문의/피드백은 서버 세션으로 회신 부탁드립니다.
