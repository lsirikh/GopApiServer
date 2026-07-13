# [GIS 클라 전달] GOP API 서버 v6.3 변경 통합 통지

- **발신**: DBApi (API 서버) 팀
- **수신**: GIS 클라(.NET) 팀
- **일자**: 2026-07-13
- **서버 버전**: v6.3 (Swagger `6.3.0`, branch `release/v6.3`)
- **관련 태그**: `v6.3-nats_sync_completion` · `v6.3-lockout_policy` · `v6.3-audit_auto_lock`
- **근거 명세**: `GOP_Restful_Api_연동설계.md`(§9.2.2 로그인, §9.8 세션설정, v6.3 후속 체인지로그) · `docs/DBApi_API서버.md`(NATS)

---

## 0. 요약 (두괄식)

| 영역 | 변경 | 클라 조치 |
|---|---|---|
| **A. NATS 발행** | SYNC 식별자 2종 필드명 변경 + 신규 2종(SYSTEM_EVENT·ENCLOSURE_METRICS) | ⚠ **파싱 수정 + 신규 수신** |
| **B. 로그인 실패 응답** | 401에 잔여 횟수 안내 + `error.details` 구조화 | 선택 — UX 개선 반영 시 |
| **C. 세션/잠금 설정** | 신규 설정 `lockout_duration_minutes`(자동해제) + 잠금 정책 | 관리자 화면 있으면 반영 |

---

## A. NATS 발행 정합 (`v6.3-nats_sync_completion`) ⚠ 계약 변경

DBApi는 발행 전용. GIS는 SYNC 구독 + (신규) SYSTEM_EVENT·ENCLOSURE_METRICS 수신 대상.

### A-1. ⚠ 계약 변경 — 파싱 수정 필요
`resource_id`(설정 row PK)를 싣던 것이 **REST 조회에 필요한 부모 ID**로 정정됨 (`camera_settings.id≠camera_id`, `proxy_settings.id≠server_id` 였음 — 기존 값으론 REST 경로 구성 불가한 실버그).

| cmd | 이전 body | **변경 후** | 조회 경로 |
|-----|-----------|------------|----------|
| `SYNC_CAMERA_SETTING` | `{action, resource_id}` | **`{action, camera_id}`** | `GET /api/devices/cameras/{camera_id}/settings` |
| `SYNC_PROXY_SETTING` | `{action, resource_id}` | **`{action, server_id}`** | `GET /api/servers/{server_id}/proxy-settings` |

→ 수신 시 `body.resource_id` → **`body.camera_id` / `body.server_id`** 로 읽기.

### A-2. 추가 (하위호환)
| cmd | 변경 |
|-----|------|
| `SYNC_PRESET` | body에 **`camera_id` 추가**: `{action, resource_id(Preset), camera_id}`. 조회 경로 `.../cameras/{camera_id}/presets/{preset_id}`에 직접 사용 가능 |

### A-3. 신규 수신 2종
- **`SYSTEM_EVENT`** — Subject `sensorway.{부대ID}.all.event.system`, **Full-DTO**(body에 실데이터). 필드: `id, server_id, type_event, severity(INFO/WARNING/ERROR/CRITICAL), source, message, acknowledged, server_description, created_at`. system_events 발생 시.
- **`ENCLOSURE_METRICS`** — Subject `sensorway.{부대ID}.gis.enclosure-metrics`(GIS 대상), **주기 텔레메트리**(기본 10초). body: `enclosure_id, temperature, humidity, voltage, current, measured_at`. 함체별 최신값 단건 반복.

### A-4. 불변
SYNC 7종(`DEVICE`/`SERVER`/`CATEGORY`/`DEVICE_GROUP`/`EVENT_MAPPING`/`FILE_GROUP`) body·subject 불변. Envelope(`id`/`m_type=PUB`/`cmd`/`from=DBApi`/`body`/`created`) 불변. DBApi 발행 전용(구독 없음).

> 상세: `docs/DBApi_API서버.md`. 서버측 실측: 6종 NATS 수신 subject+body 명세 100% 일치 확인.

---

## B. 로그인 실패 응답 변경 (`v6.3-lockout_policy`) — `POST /api/auth/login`

기존엔 실패 시 몇 번 틀렸는지·잠금 여부 안내가 전혀 없었음. 이제 잔여 횟수를 안내한다.

### B-1. 비밀번호 불일치 (`401`)
`lockout_threshold>0` 이면 잔여 횟수 안내 + 구조화 `error.details`:
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "로그인 정보가 올바르지 않습니다. (5회 중 2회 실패, 3회 남음)",
    "details": { "failed_count": 2, "threshold": 5, "remaining": 3, "locked": false }
  }
}
```
- **이번 실패로 임계 도달 시**: `message`="실패 N회 초과로 계정이 잠겼습니다. 약 M분 후 자동 해제됩니다.", `details.locked=true`, `remaining=0`.
- **미존재 계정**: 카운트 미노출(계정 열거 방지) — `message="Incorrect login_id or password"`, `details=null`.
- **틀린 이유(id/pw)는 구분 노출 안 함**. `lockout_threshold=0`(잠금 비활성)이면 카운트 없이 일반 메시지.

### B-2. 잠긴 계정 재로그인 (`403`)
`lockout_duration_minutes>0` 이면 `message`="계정이 잠겼습니다. 약 M분 후 자동 해제됩니다."
- **자동 해제**: 잠금 후 `lockout_duration_minutes` 경과 후 로그인 시도 시 자동 해제(+실패카운트 리셋)되어 통과.
- 관리자 `POST /api/users/{id}/unlock` 은 즉시 해제(카운트 리셋 동반).

### B-3. 기타
- IP rate limit 초과 시 `429` + `Retry-After`(무차별 대입 방어, 300초/10회).
- **클라 권장**: `error.details.remaining`으로 "N회 남음" 표시, `locked=true`면 잠금 안내 화면. 파싱은 `error.details` 우선(메시지 문자열 파싱 지양).

---

## C. 세션 / 잠금 정책 설정 (`v6.3-lockout_policy`) — `GET·PUT /api/settings/session`

인가: `setup_system:view/edit` (ADMIN bypass). 세션/잠금 정책 런타임 관리.

### C-1. GET 응답 필드
```json
{
  "success": true,
  "data": {
    "session_timeout_hours": 12,
    "refresh_expiration_days": 7,
    "lockout_threshold": 5,
    "lockout_duration_minutes": 30,
    "session_enabled": true,
    "auth_mode": "token",
    "jwt_algorithm": "HS256"
  }
}
```

| 필드 | 편집 | 제약 | 의미 |
|------|------|------|------|
| `session_timeout_hours` | ✅ | 1~168 | access 토큰 만료(시간) |
| `refresh_expiration_days` | ✅ | 1~90 | refresh 토큰 만료(일) |
| `lockout_threshold` | ✅ | **0(비활성) 또는 3~20** | N회 실패 시 잠금 |
| **`lockout_duration_minutes`** | ✅ | **0(자동해제 없음=영구) 또는 1~1440** | 🆕 잠금 후 이 시간 경과 뒤 로그인 시 자동 해제(+카운트 리셋) |
| `session_enabled` | ✅ | bool | 세션 만료 마스터 스위치. **false면 토큰 사실상 영속(≈10년)** |
| `auth_mode` / `jwt_algorithm` | ❌ 읽기전용 | — | 배포(.env) 전용. `jwt_secret`은 절대 미노출 |

### C-2. PUT (부분 수정)
편집 가능 필드의 부분집합만 수용(미지정 필드 불변). 경계 위반 시 `422`(예: `lockout_threshold`=1,2 / `lockout_duration_minutes` 범위 밖). 변경분은 서버 `ConfigChangeLog` 감사 + 즉시 반영.
```json
PUT /api/settings/session  { "lockout_threshold": 5, "lockout_duration_minutes": 30 }
```

### C-3. 참고 — 자동 잠금/해제 감사 (`v6.3-audit_auto_lock`)
브루트포스 자동잠금·타이머 자동해제가 `audit_logs`에 `USER_LOCKED`/`USER_UNLOCKED`(행위자 `(system)`)로 기록됨. GIS가 감사 로그(`GET /api/audit-logs`)를 조회한다면 시스템 행위자 이벤트가 추가로 보인다(수동 관리자 lock/unlock과 액션타입 동일·행위자 상이).

---

## D. 추적성 / 검증

| 영역 | 태그 | 검증 |
|---|---|---|
| NATS | `v6.3-nats_sync_completion` | NATS 실수신 6종 subject+body 문서 100% 일치 |
| 로그인 실패·세션설정 | `v6.3-lockout_policy` | 실패 시퀀스 메시지/details·자동해제·unlock 리셋 실측, A01~A18 10/10 |
| 자동잠금 감사 | `v6.3-audit_auto_lock` | USER_LOCKED/UNLOCKED row 실측 |

> REST/Swagger는 `https://<서버>:8000/docs`(OpenAPI 6.3.0)에서 최신 계약 확인 가능. 문의는 DBApi 팀.
