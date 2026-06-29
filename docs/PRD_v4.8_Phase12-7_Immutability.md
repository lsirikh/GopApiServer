# PRD — v4.8 Phase 12-7 불변성 강화 6 sub-phase 통합

**작성일**: 2026-06-22 · **차수**: v4.8 Phase 12-7 · **안전점**: `pre-immutability-phase12-7` @ a9d4655

---

## §1. 배경 + 차수 의도

### 1.1 배경
- **선행 상태**: v4.8 Phase 1~12 완료 (시드 재설계 + pagination 안정성 검증 @ 536c0b8까지).
- **차장님 추가 요청**: 마감 직전 "근간을 흔드는 변경이 더 남아있지 않은지 한 번 더 훑어라" — 명세 §6 불변성 원칙 6대를 기준으로 전수 재점검 지시.
- **분석 수단**: Workflow 6-agent 병렬 조사 (스키마/제약/시드/감사/배치/타입) → 위반 후보 7건 도출.

### 1.2 식별 결과 (7건 → 6건 본 차수 / 1건 v5.0 분리)
| # | 카테고리 | 항목 | 등급 | 처리 차수 |
|---|---------|------|------|----------|
| 1 | 스키마 | 명세 §6.3.4 `device_type` 컬럼 정의 오류 → 코드 차단 | **P0** | **Phase 12-7 (본 차수)** |
| 2 | 제약 | `ActionEvent.created_at` 변경 가능 → 변경 차단 | P1 | Phase 12-7 |
| 3 | 감사 | `audit_logs` DB-level TRIGGER 미적용 | P1 | Phase 12-7 |
| 4 | 시드 | Static 시드 ID/이름 후행 변경 가능 | P1 | Phase 12-7 |
| 5 | 제약 | Soft-delete 후 `is_deleted` 재진입 가능 | P1 | Phase 12-7 |
| 6 | 제약 | 1:N 관계 cascade 누락 (orphan 발생 경로) | P1 | Phase 12-7 |
| 7 | 타입 | `type_device` enum → 테이블 분리 (영향도 大) | P1 | **v5.0 분리** |
| - | 배치 | Bulk atomicity (Phase 12-7 범위 외) | - | **v4.9 분리** |

→ 본 차수 = **P0 1건 + P1 5건 = 6 sub-phase 통합**.

### 1.3 차수 의도 (Why one version, not six)
- 6건 모두 "불변성 원칙 6대"라는 **단일 설계 축**에서 파생됨 → 묶어야 일관성 검증 가능.
- 동일 마이그레이션 윈도우(스키마 + TRIGGER + 시드 잠금)를 1회로 합쳐 다운타임 최소화.
- 메모리 규칙 `feedback_one_day_one_version`: 같은 날 작업 별도 차수 분리 금지 → 동일 차수 Phase 12-7로만 추가.

### 1.4 결재 사항 (4건, 이미 결재 완료)
| # | 결재 항목 | 결정 | 반영 섹션 |
|---|----------|------|-----------|
| 1 | 명세 §6.3.4 `device_type` 정정 방향 | **코드 차단 (스키마 정정으로 명세-코드 일치 확보)** | §3 |
| 2 | `ActionEvent.created_at` 처리 | **변경 차단** (admin batch-import는 v5.0 별도 경로) | §4 |
| 3 | `audit_logs` 감사 레이어 | **DB-level TRIGGER 적용** (애플리케이션 누락 방지) | §5 |
| 4 | Bulk operation atomicity | **v4.9 분리** (본 차수 범위 외) | 본 차수에서 제외 |

### 1.5 적용 원칙 — 불변성 6대 (보고서 §3)
1. **스키마 정합성**: 명세-코드-DB 3자 일치.
2. **시간 불변성**: `created_at`은 INSERT 후 변경 불가.
3. **감사 완전성**: 모든 mutating 작업은 DB-level에서 자동 기록.
4. **시드 잠금**: Static 시드(Category/Enum/Type)는 ID/이름 변경 불가.
5. **상태 단방향성**: Soft-delete 후 동일 PK 재진입 차단.
6. **관계 일관성**: 1:N orphan 미발생 (cascade 또는 RESTRICT 명시).

각 sub-phase(§3~§8)는 위 원칙 중 하나 이상에 매핑된다.

### 1.6 안전점 (단일 롤백 포인트)
- **태그**: `pre-immutability-phase12-7` @ commit `a9d4655` (현 HEAD 직전).
- **롤백 정책**: 본 차수 전체 실패 시 위 태그로 일괄 reset. sub-phase 부분 롤백은 §3~§8 각 절 rollback 참조.

### 1.7 본 PRD 구성
- §2: 영향 범위 + 의존성 (sub-phase 간 순서/락 충돌)
- §3: Sub-phase 1 (P0) — 명세 §6.3.4 스키마 정정
- §4~§8: Sub-phase 2~6 (P1) — 시간/감사/시드/상태/관계 불변성
- §9: 통합 회귀 + 마이그레이션 절차
- §10: DoD + 차수 종결 체크리스트

---

## 결론 (두괄식)

UserGroupUpdate에서 `permissions` 필드를 제거하고 `extra="forbid"`를 적용해 P0 권한 상승 공격 경로를 차단했다. 실측 결과 `PUT /api/user-groups/{id}` body에 `permissions` 포함 시 **HTTP 422 + extra_forbidden** 응답이 확정된다. 권한 변경 전용 admin 엔드포인트는 본 차수에서 신설하지 않으며, **v5.0 차수에 POST /user-groups/{id}/permissions로 분리 권고**(P1 잔존)한다.

## 변경 요약

| 항목 | Before | After |
|------|--------|-------|
| `UserGroupUpdate.permissions` | `Optional[Dict[str, Any]] = None` | 필드 제거 |
| `UserGroupUpdate.model_config` | (없음, 기본 `extra="ignore"`) | `ConfigDict(extra="forbid")` |
| 라우터 PUT 처리 | `group_data.permissions` 분기 존재 | 분기 삭제 |
| 감사 로그 before/after_state | `permissions` 키 추적 | 키 제거 (변경 불가) |
| 라우터 docstring | "permissions: 권한 설정 (선택)" | "P0 차단, 전용 admin 엔드포인트 권고 (v5.0)" + 422 응답 명시 |

## 실측 검증 (empirical evidence)

### 1) 스키마 단위 — `extra_forbidden` 발화
```text
PASS: Valid payload accepted: {'name': 'New Name', 'description': 'desc', 'is_active': True}
PASS: permissions rejected, error count = 1
  type= extra_forbidden  loc= ('permissions',)  msg= Extra inputs are not permitted
PASS: unknown field rejected, error count = 1
```

### 2) FastAPI HTTP 422 — TestClient 직격
```text
Valid body status = 200 / body = {'ok': True, 'data': {'name': 'X', 'description': 'd', 'is_active': True}}
permissions status = 422
detail = {'detail': [{'type': 'extra_forbidden', 'loc': ['body', 'permissions'],
                      'msg': 'Extra inputs are not permitted',
                      'input': {'modules': ['admin']}}]}
```

> 기대 동작(422 거부)이 실측으로 확인됨. PRD §2 Phase 12-7a 차단 요건 충족.

## 보안 영향 (P0 → 해소)

- **공격 시나리오**: 일반 ADMIN/MAINTAINER 권한 사용자가 `PUT /api/user-groups/{group_id}` body에 `{"permissions": {"modules": [...]}, ...}`를 첨부해 자신 또는 타 그룹의 RBAC 정책을 임의로 변조 → 권한 상승.
- **차단 메커니즘**: Pydantic v2의 `extra="forbid"`는 모델 인스턴스화 시점에 알 수 없는 필드를 차단한다. FastAPI 본문 디코딩 파이프라인은 Pydantic 검증 단계에서 즉시 `RequestValidationError`를 발생시키고 422를 반환하므로, 라우터 함수 본문은 단 1줄도 실행되지 않는다.
- **부수 효과**: `permissions` 외 임의의 알 수 없는 필드(예: `is_admin: true`, `role: "SUPERADMIN"`)도 동일 경로로 차단된다(테스트 3에서 확인). 향후 스키마 진화 시 오타·실수 필드의 조용한 무시(silent drop)도 함께 막힌다.

## 향후 권고 (P1 잔존 — v5.0)

본 차수는 권한 변경 자체를 차단할 뿐, 합법적 권한 변경 경로를 신설하지 않았다. v5.0에서 다음을 분리 신설할 것을 권고한다.

| 엔드포인트 | 메서드 | 인가 | Body 스키마 |
|----|----|----|----|
| `/api/user-groups/{id}/permissions` | `POST` (또는 `PUT`) | ADMIN only + 감사 로그 강제 | 전용 `UserGroupPermissionsUpdate` (permissions 단일 필드, `extra="forbid"`) |

- 감사 로그 `action_type`: `GROUP_PERMISSIONS_UPDATED` 별도 발화.
- 정책 diff(before/after)를 `changes`에 구조화 기록.
- IP/세션/X-Forwarded-For 헤더 트레이싱 의무.

## 회귀 영향 분석

- `UserGroupCreate.permissions`: **변경 없음**. 생성 시점에는 초기 정책 부여가 정당하므로 유지. `test_create_user_group_with_permissions` 테스트 비영향.
- `UserGroupResponse.permissions`: **변경 없음**. 조회 시 권한 표출은 차단 대상 아님.
- 라우터 GET/POST/DELETE 경로: **변경 없음**.
- 감사 로그 `GROUP_UPDATED` 이벤트: `changes`에서 `permissions` 키가 더 이상 등장하지 않음 (스키마 차단의 의도된 결과). 기존 로그 소비자(대시보드/SIEM)가 `permissions` 변경을 강제 키로 기대하지 않는지 확인 필요 — 본 코드베이스 검색 결과 그러한 의존성 없음.

## 미해결 / 후속 트랙

1. **사전 존재 sqlite migration 이슈**: `tests/test_user_group_api.py` 픽스처가 `camera_presets.is_restricted_zone` 컬럼 부재로 set-up 단계에서 OperationalError. 본 PRD 변경과 무관하며 별도 차수(스키마 마이그레이션)로 처리. 본 차수에서는 schema-level / FastAPI-level 실측으로 422 거부 확정.
2. **전용 admin 엔드포인트 신설**: 위 §향후 권고 표 참조.

---

## Phase 12-7b — Event 3종 PUT device_id / device_description 원천 차단

### 결정 사항 (두괄식)
- **Event 3종 PUT 핸들러는 device 바인딩을 더 이상 받지 않는다.** `DetectionEventReplace` / `MalfunctionEventReplace` / `ConnectionEventReplace` 3종 신규 스키마를 신설하고, `device_id` 필드를 아예 노출하지 않으며 `device_description`도 제거해 **스냅샷을 보존**한다.
- **`model_config = ConfigDict(extra="forbid")`** 로 두 필드 중 어느 것이라도 전송되면 **422**로 즉시 거부된다. 이는 v4.8 Phase 12에서 `ActionEventReplace`/`ActionEventUpdate`에 적용했던 `from_event_id` 차단 패턴을 device 축으로 확장한 것이다.
- **명세서 §6.3.4 line 8797 노트도 정정**한다. 기존 "PATCH로 수정 불가, PUT 전체 교체만 가능"은 오기이며, **PATCH/PUT 모두 수정 불가**가 정확한 정책.

### 변경 요약 표

| 파일 | 변경 종류 | 내용 |
|---|---|---|
| `app/schemas/event.py` | 추가 | `DetectionEventReplace`(type_event/result/detail), `MalfunctionEventReplace`(type_event/reason/detail), `ConnectionEventReplace`(type_event) — 모두 `extra="forbid"` |
| `app/routers/detections.py` | 수정 | import + PUT 시그니처 `DetectionEventCreate`→`DetectionEventReplace`, Device 조회/device_description 재생성/대입 라인 제거, Response의 `device`는 `event.device` 사용 |
| `app/routers/malfunctions.py` | 수정 | 동일 패턴, `reason`/`detail`은 교체 대상으로 유지 |
| `app/routers/connections.py` | 수정 | 동일 패턴, `type_event`만 교체 대상 |
| `GOP_Restful_Api_연동설계.md` | 정정 | §6.3.4 line 8797 노트 문구 갱신 |

### 왜 이 차단인가 (불변식 + 데이터 정합성)
- **v2.1 불변식**: Detection/Malfunction/ConnectionEvent는 생성 시점에 `device_id`가 확정되고 `device_description`은 그 시점의 device 스냅샷 문자열. PUT으로 device를 갈아치우면 *동일 이벤트 id가 다른 device 이력을 가리키는* 사실 왜곡이 생긴다.
- **1:N 가드 우회 위험**: ActionEvent는 from_event_id로 위 3종을 가리키며, source의 device가 PUT으로 바뀌면 1:N 카운팅 기반 `action_reported` 자동 관리(`update_source`/`reset_source`)와 DELETE 409 가드 의미가 깨진다. Phase 12에서 `from_event_id` 변경을 막은 것과 같은 결의 위협이 device 축에 남아 있었던 셈.
- **스냅샷 정책**: `device_description`은 운영자 사후 식별·감사 목적의 **불변 스냅샷**이다. PUT 핸들러가 `_generate_device_description(device)`로 갈아엎으면, 동일 이벤트가 시점에 따라 서로 다른 description을 가지게 되어 감사 추적이 망가진다. 본 차단으로 description은 생성 시점 값으로 고정된다.

### 거부 동작 (실증)
실제 `python -c` 실행 결과(요약):
- `DetectionEventReplace(type_event='Intrusion', result='PIR_SENSOR', device_id=1)` → ValidationError, 메시지에 `device_id` / `extra_forbidden` 포함 ✓
- `MalfunctionEventReplace(type_event='Fault', reason='FAULT_CONTROLLER', device_description='x')` → ValidationError, `device_description` 포함 ✓
- `ConnectionEventReplace(type_event='Connection')` → 정상 인스턴스화 ✓
- `ConnectionEventReplace(type_event='Connection', device_id=1)` → ValidationError ✓

### 운영 절차 변경 안내
- device 재지정이 필요한 경우는 **DELETE 후 POST**로 분리한다. PUT은 이제 type_event/result(또는 reason)/detail의 본문 교체에만 사용된다.
- PATCH (`*EventUpdate`)도 동일 정책(스냅샷 보존)이며 기존부터 device_id를 받지 않았다 — 따라서 클라이언트는 PATCH/PUT 어느 메서드로도 device를 바꿀 수 없다.

### 영향 범위 / 비영향
- **영향**: 외부 클라이언트가 PUT 본문에 `device_id`나 `device_description`을 포함해 보내던 경우 422가 되며, 호출자 측 수정이 필요. 현재 동봉 테스트(`tests/test_detection_event_api.py`, `tests/test_connection_event_api.py`)에는 PUT 케이스가 0건이라 회귀 우려는 낮다.
- **비영향**: POST(Create)는 device_id를 그대로 요구하며 변경 없음. ActionEvent / EventMapping / Event statistics 경로 무관.

### 후속 작업 권고
- Track B 수준에서 PUT 422 회귀 테스트 3종(`should_reject_when_put_includes_device_id`, `…_device_description`)을 Detection/Malfunction/Connection 각각 추가. 본 패치 자체는 schema-level 행위로 인스턴스화 단계에서 차단됨을 인라인 검증으로 확인했고, HTTP E2E 테스트는 별도 차수가 아닌 동일 v4.8 차수 Phase 12-7b 후속 step으로 묶어 진행.


---

## 12-7c AccountUserSelfUpdate sinseol /users/me gwonhan pildu chadan

### Gyolron

PUT /users/me ipryeok seukima reul gwallija yong AccountUserUpdate eseo singyu AccountUserSelfUpdate ro buni hago extra forbid jeokyong. Gwonhan pildu role group_id is_active neun self gyeong ro eseo 422 ro geobu. Gwallija gyeong ro PUT /users/{user_id} neun AccountUserUpdate yuji.

### Byeongyeong yoji

Table comparing before and after for users/me schema (9 fields to 6 fields), extra policy (none to forbid), photo_url reflection (missing to added), admin path PUT /users/{user_id} stays on AccountUserUpdate.

### Self-only gadeu

PUT /me has no path parameter user_id, target is current_user. Equality current_user.id == target_id is satisfied at signature level.

### Silcheuk gidaegap

PUT /users/me {role admin} returns 422 with extra_forbidden detail at body.role location.

### Tidy First

Structural: schema separation, import update. Behavioral: extra forbid 422 enforcement plus photo_url assignment.

### Files

- c:/workspace_python/api-test-server/app/schemas/user.py line 130-171 after AccountUserUpdate add AccountUserSelfUpdate
- c:/workspace_python/api-test-server/app/routers/users.py line 12 import line 80-153 PUT /me handler
- c:/workspace_python/api-test-server/tests/test_users_self_update.py new test file

---

## Phase 12-7d: ActionEvent.created_at 변경 차단

### 배경
ActionEvent의 `created_at`은 "운영자가 조치를 수행한 실제 시각"으로, 감사·법적 증거 가치를 가진다. 현재 `ActionEventReplace`(PUT)와 `ActionEventUpdate`(PATCH) 모두 `created_at: Optional[KSTDatetime]` 을 허용하여 사후 시각 위조가 가능한 구조이다. Phase 12 "변경 경로 일원화" 정책에 따라 갱신 경로에서 봉쇄한다.

### 변경 결정
| 스키마 | created_at | 사유 |
|--------|-----------|------|
| `ActionEventCreate` (POST) | 유지 | 생성 시점 지정은 합리적 (batch-import, 동기화 등) |
| `ActionEventReplace` (PUT) | 제거 | 시각 위조 금지 |
| `ActionEventUpdate` (PATCH) | 제거 | 시각 위조 금지 |

- 기존 `extra="forbid"` 가 이미 적용되어 있어, 필드 제거만으로 클라이언트가 `created_at` 을 전송하면 422 가 자동으로 발생한다.
- 생성 시각 재지정이 반드시 필요한 운영 시나리오는 DELETE 후 POST 재생성으로 처리한다.

### 결재 사항
- **admin-only batch-import 엔드포인트**(예: `POST /events/action/batch?force_created_at=true`)는 v5.0 권고 사항으로 분리한다. v4.8 범위에서는 일반 PUT/PATCH 차단만 수행한다.

---

## Phase 12-7e: EnclosureUpdate.door_status 일반 PATCH 우회 봉쇄

### 배경
`door_status`(CLOSED/OPEN)는 외부 센서가 주기적으로 보고하는 **물리적 상태**이며, 변경 시 `ConfigChangeLog.STATUS_CHANGED` 로 별도 추적되어야 한다. 현재 두 개의 경로가 공존한다:

1. **전용 경로**: `PATCH /enclosures/{id}/status` — `EnclosureStatusUpdate` 사용, STATUS_CHANGED 로그 기록 (`app/routers/enclosures.py` L490~)
2. **우회 경로**: `PATCH /enclosures/{id}` — `EnclosureUpdate` 의 `door_status` 필드 (L821~824)로도 변경 가능, UPDATED 로그로 섞임

이는 동일 상태에 대한 변경 경로 이원화이며, 감사 로그의 일관성을 해친다.

### 변경 결정
| 엔드포인트 | door_status 변경 | ConfigChangeLog |
|-----------|------------------|-----------------|
| `PATCH /enclosures/{id}` | **불가** (필드 제거 + `extra='forbid'`) | UPDATED (door_status 외 필드만) |
| `PATCH /enclosures/{id}/status` | 허용 (전용 경로) | STATUS_CHANGED |

- `EnclosureBase`/`EnclosureResponse` 의 `door_status` 는 그대로 유지(생성·조회용).
- `EnclosureUpdate` 에 `model_config = ConfigDict(from_attributes=True, extra="forbid")` 를 명시해, 클라이언트가 `door_status` 를 전송하면 422 자동 거부.
- 라우터 `update_enclosure` docstring 에서 `door_status` 라인 삭제.

### audit log 강화 권고
`update_enclosure_status`(L490~)는 이미 `STATUS_CHANGED` 로그를 기록하지만, `user_agent`/`ip_address`/`actor` 메타데이터를 audit 컬럼에 함께 적재하도록 v4.8 후속 Phase(또는 v5.0)에서 보강하는 것을 권고한다.

---

## 통합 영향도

- **호환성**: 두 변경 모두 "현행 정상 사용자에게는 영향 없음, 잘못된 사용자에게는 422" 의 형태이다. 도어 상태를 일반 PATCH 로 변경하던 클라이언트는 전용 status 엔드포인트로 전환해야 한다.
- **DB**: 마이그레이션 불필요. 모델 컬럼은 모두 유지.
- **테스트**: 두 sub-phase 모두 회귀 테스트 신규 케이스 추가 후 green 확인.
- **문서**: OpenAPI 스키마 재생성, `endpoints_spec.txt` 갱신, README 변경 이력 기록.

---

## §12-7f — 감사 테이블 DB-level immutability 트리거

### 결론 (두괄식)
audit_logs / config_change_logs / user_login_logs 3개 테이블에 BEFORE UPDATE OR DELETE 트리거를 부착하여 DB 레벨에서 append-only를 강제했다. INSERT는 정상 허용, UPDATE/DELETE는 RAISE EXCEPTION으로 즉시 차단. 6개 시나리오(테이블 3 × 행위 2) 실측 검증 완료.

### 변경 파일
| 파일 | 변경 |
|---|---|
| `app/migrations/v51_audit_immutability_triggers.sql` | 신설. 트리거 함수 1개 + 트리거 3개 + 등록 결과 점검 SELECT |

### 트리거 함수 (TG_TABLE_NAME 동적 치환)
```sql
CREATE OR REPLACE FUNCTION fn_block_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit table (%) is append-only — UPDATE/DELETE blocked', TG_TABLE_NAME
        USING ERRCODE = 'P0001';
END;
$$ LANGUAGE plpgsql;
```

### 실측 검증 결과

| 테이블 | UPDATE | DELETE | INSERT |
|---|---|---|---|
| `audit_logs` | ERROR (차단) | ERROR (차단) | id=21 정상 |
| `config_change_logs` | ERROR (차단) | ERROR (차단) | id=1633 정상 |
| `user_login_logs` | ERROR (차단) | ERROR (차단) | id=87 정상 |

에러 메시지 예시 (psql 실측):
```
ERROR:  audit table (audit_logs) is append-only — UPDATE/DELETE blocked
CONTEXT:  PL/pgSQL function fn_block_audit_modification() line 3 at RAISE
```

### 설계 선택
1. **단일 함수 + 3 트리거** — `TG_TABLE_NAME`으로 어느 테이블이 차단됐는지 메시지에 동적 포함. 코드 중복 제거.
2. **DROP TRIGGER IF EXISTS 선행** — 재실행 가능(idempotent). NOTICE 출력은 최초 실행 시에만 발생.
3. **ERRCODE = 'P0001'** — `psycopg2.errors.RaiseException` 으로 응용 계층에서 분기 가능.
4. **INSERT 미차단** — append-only 의미 유지. BEFORE UPDATE OR DELETE 만 지정.

### 알려진 제약 (스코프 명시)
- **TRUNCATE는 row-level 트리거로 차단되지 않음** — 명세(`BEFORE UPDATE OR DELETE`)에 따라 행-단위 트리거에 한정. 운영 환경에서는 DB role 권한 `REVOKE TRUNCATE/DELETE/UPDATE`로 보완하는 것이 정석이며, 이는 Phase 12-7f 범위 밖.
- **SUPERUSER는 우회 가능** — `ALTER TABLE ... DISABLE TRIGGER` 권한 보유자는 트리거를 비활성화할 수 있음. 실제 위협 모델 상 SUPERUSER는 신뢰 경계 내부.

### 관련 파일 (참고)
- `app/models/audit_log.py` — `audit_logs` 테이블 정의
- `app/models/config_change_log.py` — `config_change_logs` 테이블 정의
- `app/models/user.py:141` — `UserLoginLog` 클래스 (`user_login_logs`)
- `app/migrations/v50_action_reported_invariant_fix.sql` — 직전 마이그레이션 (스타일 참고)

---
