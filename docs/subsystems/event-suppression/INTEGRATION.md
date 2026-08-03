# 이벤트 억제(정비 창) — 서브시스템 통합 연동 가이드

> **이 문서 하나면 됩니다.** 여러 서브시스템을 겸하는 개발자를 위해 팀별 문서를 통합했습니다.
> 서브시스템별 개별 문서(`GIS.md`, `Proxy.md` 등)는 **이 문서를 가리키는 포인터**이며,
> **내용이 다르면 이 문서가 우선**입니다.

- **문서 버전**: v1.0 · **작성일**: 2026-08-03
- **대상 API 버전**: **6.3.2** (`release/v6.3`) · **브로커 명세**: **v1.6 §9.12**
- **서버 마스터 명세**: `GOP_Restful_Api_연동설계.md` **§6.8** (REST) / `Gop_Message_Broker_연동설계_v1.6.md` **§9.12** (NATS)
- **대상**: GIS(관제/Central UI) · PidsProxy · AiAnalysis · VMS · NVRManager · BroadcastingManager · Central · db_monitor

---

## 0. 두괄식 — 지금 당장 할 일

공사·설치·장애수리·AS 기간에 **대상(장비/그룹/전체) × 이벤트유형(연결/탐지/장애/전체) × 시간창**을
지정해 이벤트를 억제하는 "정비 창" 기능입니다. 서버는 **저장**을 막고, 각 서브시스템은 **자신의
라이브 반응**(발행·녹화·알람)을 막아야 완전한 억제가 완성됩니다.

### 0.1 팀별 할 일 한눈에

| 서브시스템 | 우선순위 | Phase 1 (지금, 필수) | Phase 2 (D1 결정 후) | 상세 |
|---|---|---|---|---|
| **GIS** | ★최상 | ★**대상 필드 단수→배열**(파괴적) · 다중선택 UI · `bulk-delete` 연동 · 활성 배너 · **offset 포함 전송** · **`devices.id` 확인** · **NATS 3원칙** | 알람 딤/정비 표식 | [§3.1](#31-gis-관제--central-ui) |
| **PidsProxy** | ★최상 | **202 억제 응답 처리** · connection POST 토큰 · **NATS 3원칙** | 탐지/장애 라이브 발행 skip | [§3.2](#32-pidsproxy) |
| **AiAnalysis** | 상 | **202 처리**(서버 POST 시) · **NATS 3원칙** | AI 탐지 발행 skip | [§3.3](#33-aianalysis) |
| **VMS** | 상 | **NATS 3원칙** | 이벤트 트리거 녹화/PTZ/팝업 억제 · `is_restricted_zone` 파이프라인 재사용 | [§3.4](#34-vms) |
| **NVRManager** | 중 | **NATS 3원칙** | 이벤트 트리거 녹화 억제 | [§3.5](#35-nvrmanager) |
| **BroadcastingManager** | 중 | **NATS 3원칙**(최소) | 이벤트 연동 자동 방송 억제 | [§3.6](#36-broadcastingmanager) |
| **Central** | 중 | **NATS 미수신** → `GET /active` HTTP 폴링으로만 배너 | — | [§3.7](#37-central) |
| **db_monitor** | 낮(참고) | ✅ 서버측 완료(단, **배포 순서** 준수) | — | [§3.8](#38-db_monitor-참고) |

### 0.2 ★ NATS 수신 팀 공통 3원칙 (이번 차수 필수 — Central 제외)

1. **`EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가** — **구독 추가는 불필요**(이미 `all.sync.*` 구독 중)
2. **미지 cmd graceful skip 방어** — 빠뜨리면 SYNC 수신 루프 전체가 죽어 **장비 동기화(SYNC_DEVICE)까지 멈춥니다**
3. **`expired` 신호로 억제를 해제하지 말 것** — 캐시한 `window_end` **로컬 타이머가 1차 권위**,
   `GET /active` 폴링 **존치** ([§2.8 fail-safe](#28--fail-safe-규범-must))

### 0.3 ⚠ 배포 상태 (2026-08-03 기준)

| | 개발 서버 | 테스트 서버 `123.141.236.253:8136` |
|---|---|---|
| `info.version` | 6.3.2 | 6.3.2 |
| `bulk-delete` | ✅ | ✅ |
| **`SYNC_EVENT_SUPPRESSION`** | ✅ | ❌ **미발행** |
| **PATCH 500 수정** | ✅ | ❌ 여전히 **500** |

테스트 서버는 **6.3.2 초기 커밋(`36128f7`)** 상태입니다. `SYNC_EVENT_SUPPRESSION` 과 PATCH 500 수정은
**후속 커밋(`b92082f`)** 에 있으므로 **재배포가 필요**합니다.
**`info.version` 이 양쪽 6.3.2 로 같아 버전으로는 구분되지 않습니다** — device 대상 창에
**이름만 바꾸는 PATCH**(단일 필드)를 던져 **200 이면 최신 / 500 이면 재배포 전**입니다.
**재배포 후 반드시 연동 시험하세요.**

---

## 1. ★ 반드시 이해할 범위 경계 (Phase 1 vs Phase 2)

DBApi 서버는 브로커 토폴로지상 **발행 전용(publish-only)** 이라, 장비 이벤트가 서버로 NATS 구독으로
들어오지 않고 **HTTP POST 로만** 유입됩니다. 따라서 서버 억제(Phase 1, 배포 완료)의 범위는:

| 서버가 막는 것 (Phase 1 — 완료) | 서버가 **못** 막는 것 (Phase 2 — 각 팀 몫) |
|---|---|
| 이벤트 **DB 저장**(레코드 미생성) | PidsProxy/AiAnalysis 가 쏘는 **실시간 NATS 방송** |
| 이벤트 로그·통계·보고서 등 DB 파생 | 관제/VMS/NVR 의 **실시간 알람·녹화·PTZ 반응** |
| **장비 상태 자동전환**(탐지→ACTIVATED / 장애→ERROR) | — |

> 즉 **정비 중에도 상황도에는 알람이 뜹니다.** 서버가 저장만 막기 때문입니다.
> 완전한 무반응을 원하면 Phase 2 에서 각 서브시스템이 라이브 반응을 억제해야 합니다(D1 결정 사항).

---

## 2. 공통 계약 (전 팀 필독)

### 2.1 REST 엔드포인트 (7개)

Base: `/api/event-suppression-schedules`

| # | Method | Path | 인가 | 용도 |
|---|---|---|---|---|
| 1 | POST | `` | events:edit | 정비 창 생성 |
| 2 | GET | `` | events:view | 목록(page/limit + status/target_type/device_id/group_id 필터) |
| 3 | **GET** | **`/active`** | events:view | **현재 활성 창 — 전 팀의 핵심 훅** |
| 4 | GET | `/{id}` | events:view | 단건 조회 |
| 5 | PATCH | `/{id}` | events:edit | 부분 변경 |
| 6 | DELETE | `/{id}` | events:delete | **취소**(soft-cancel, 이력 보존) |
| 7 | POST | `/bulk-delete` | events:delete | **일괄 하드삭제**(목록 정리, v6.3.2) |

인가는 **`AUTH_MODE=token`(운영 배포)** 에서 강제됩니다 — `Authorization: Bearer <token>` 필수,
무권한 **403** / 미인증 **401**. `role=ADMIN` 은 전권 bypass.
`AUTH_MODE` 가 token 이 아닌 개발 환경에서는 인가가 집행되지 않으므로 **권한 시나리오 검증은 반드시
token 모드에서** 하세요. `window_end` 필수(자동 만료 — 무기한 침묵 금지). `revoked_at` 으로 soft-cancel.

**`GET ` (목록) 쿼리 파라미터**

| 파라미터 | 값 |
|---|---|
| `page` | ≥1 (기본 1) |
| `limit` | **1~100** (기본 20) — 초과 시 **422** |
| `status` | `pending` / `active` / `expired` / `cancelled` |
| `target_type` | `device` / `group` / `all` |
| `device_id`, `group_id` | 대상 배열 포함 매치 — ⚠ 한계는 [§4-C](#4-c-device_id-필터로는-groupall-창이-안-잡힌다) |

목록 응답에는 `pagination: {page, limit, total, total_pages}` 가 동반됩니다.
**`/active` 에는 pagination 이 없습니다.**

**`PATCH /{id}` 규칙** — 보낸 필드만 반영됩니다.

- `target_device_ids` / `target_group_ids` — **생략하면 기존 대상 유지**, 보내면 **그 배열로 전체 교체**.
- `target_type` 을 바꿀 때는 **새 모드의 대상 배열을 반드시 함께** 보낼 것 — 없으면 **422**.
- 반대 모드의 대상 매핑은 **서버가 자동 정리**합니다(`all` 로 바꾸면 양쪽 다 비움).
- 취소된(`cancelled`) 창에 PATCH 하면 200 이지만 효과가 없습니다([§4-D](#4-g-기타)).

**생성 요청 예 — 장비 3개**

```json
POST /api/event-suppression-schedules
{
  "name": "GOP 3구역 펜스 보수",
  "description": "AS 업체 방문",
  "target_type": "device",
  "target_device_ids": [1351, 1352, 1801],
  "event_scope": "all",
  "window_start": "2026-08-03T09:00:00+09:00",
  "window_end":   "2026-08-03T18:00:00+09:00"
}
```

**생성 요청 예 — 그룹 2개 + 감지쪽만**

```json
{
  "name": "1대대 정기점검",
  "target_type": "group",
  "target_group_ids": [5, 6],
  "target_side": "detection",
  "event_scope": "detection",
  "window_start": "2026-08-03T09:00:00+09:00",
  "window_end":   "2026-08-03T12:00:00+09:00"
}
```

**생성 응답 (201) — 전 필드 실물**

```json
{
  "success": true,
  "message": "억제 스케줄 생성 성공",
  "data": {
    "id": 12,
    "name": "GOP 3구역 펜스 보수",
    "description": "AS 업체 방문",
    "target_type": "device",
    "target_device_ids": [1351, 1352, 1801],
    "target_group_ids": [],
    "target_side": "both",
    "event_scope": "all",
    "window_start": "2026-08-03T09:00:00+09:00",
    "window_end":   "2026-08-03T18:00:00+09:00",
    "recurrence_rule": null,
    "is_active": true,
    "status": "active",
    "revoked_at": null,
    "created_by": 22,
    "created_at": "2026-08-03T08:55:12.340+09:00",
    "updated_at": "2026-08-03T08:55:12.340+09:00"
  }
}
```

> 비활성 모드의 대상 배열은 **빈 배열 `[]`** 로 옵니다(위 예: `target_group_ids`).

**`GET /active` 응답 예시** (배너·판정의 소스):

```json
{
  "success": true,
  "data": [
    {
      "id": 12,
      "name": "GOP 3구역 펜스 보수",
      "target_type": "group",            // device | group | all
      "target_device_ids": [],           // target_type=device 일 때 ≥1
      "target_group_ids": [5, 6],        // target_type=group 일 때 ≥1
      "target_side": "detection",        // detection | surveillance | both
      "event_scope": "all",              // connection | detection | malfunction | all
      "window_start": "2026-08-03T09:00:00+09:00",
      "window_end":   "2026-08-03T18:00:00+09:00",
      "status": "active",
      "is_active": true
    }
  ]
}
```

`/active` 는 **활성 창만** 반환하므로 서브시스템이 status 를 재계산할 필요가 없습니다.

### 2.2 필드 사전

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `name` | string(1~200) | ✔ | 작업명/사유 |
| `description` | string(0~500) | | 상세 설명 |
| `target_type` | enum | ✔ | `device` \| `group` \| `all` — **배타 모드** |
| **`target_device_ids`** | **int[]** | `device`일 때 ≥1 | **`devices.id`** 배열 ([§2.4](#24--장비-id-주의--devicesid-를-보낼-것)) |
| **`target_group_ids`** | **int[]** | `group`일 때 ≥1 | `device_groups.id` 배열 |
| `target_side` | enum | | `detection` \| `surveillance` \| `both`(기본). **`group`·`all` 에만 적용** |
| `event_scope` | enum | ✔ | `connection` \| `detection` \| `malfunction` \| `all` |
| `window_start` | datetime | ✔ | **반드시 offset 포함** ([§2.3](#23--시간대-규약--가장-흔한-사고)) |
| `window_end` | datetime | ✔ | 필수, `> window_start` |
| `recurrence_rule` | string(0~255) | | **현재 미해석(단발 전용)** — 값을 넣어도 반복 안 됨. UI 미노출 권장 |

**응답 전용**

| 필드 | 설명 |
|---|---|
| `status` | **파생 상태** `pending`/`active`/`expired`/`cancelled` — **배지는 이 값 사용** |
| `is_active` | ⚠ **UI 표시 금지**. 내부 sweep 플래그로 **예정(pending) 창도 `true`**, 만료 후 최대 5분 지연으로 꺼짐 |
| `revoked_at` | 취소 시각(아니면 null) |
| `created_by`, `created_at`, `updated_at` | 감사용 |

**`target_side` 파생 규칙** (서버가 장비 종류로 자동 판정)

| 장비 종류 | side |
|---|---|
| sensor, controller | `detection` |
| camera | `surveillance` |
| speaker, lamp, enclosure | 보조 — **`target_side=both` 일 때만** 매치 |

**에러**: `400` 대상 id 미존재(`Device id(s) not found: [...]` / `DeviceGroup id(s) not found: [...]`) ·
`422` `end<=start` / 모드별 배열 ≥1 위반 / enum 불량 / `limit` 범위 초과 · `401`·`403` 인가.

### 2.3 ★ 시간대 규약 — 가장 흔한 사고

> **반드시 offset 을 붙여 보낼 것** — `"2026-08-03T09:00:00+09:00"`

`.NET` `DateTime` 을 offset 없이 직렬화하면:

| | `window_start` | `status` |
|---|---|---|
| 보낸 값 | `09:00:00` | (즉시 억제 의도) |
| **생성 응답** | **`18:00:00+09:00`** ❌ | **`pending`** ❌ |
| 목록 재조회 | `09:00:00+09:00` ✅ | `active` ✅ |
| 실제 억제 동작 | — | **정상 억제됨** ✅ |

**서버는 올바르게 억제하는데 생성 응답만 9시간 어긋나 "억제가 안 걸렸다"고 오인**하게 됩니다.
(**서버측 알려진 결함 — 하드닝 PRD #3, 수정 예정**, [§4-F](#4-f-naive-datetime-을-수용해-생성-응답만-9h-로-어긋난다)).
회피: ① `DateTimeOffset` 사용(`"yyyy-MM-ddTHH:mm:sszzz"`) ② 생성 직후 재조회.

### 2.4 ★ 장비 ID 주의 — `devices.id` 를 보낼 것

`target_device_ids` 는 **`devices.id`**(내부 PK)입니다. 화면의 **`number_device`(장비 번호)가 아닙니다.**

```
제어기1  →  id = 1351,  number_device = 1
제어기2  →  id = 1352,  number_device = 2
```

**실제 사고(2026-08-03)**: 운영자가 "제어기2"를 선택했는데 서버에는 `target_device_ids: [1351]`
(= 제어기1)이 전달되어, 억제 창이 도는 동안 **제어기2 장애 이벤트가 계속 올라왔습니다.**
서버는 정상 동작했으나 운영자는 "억제가 안 먹는다"고 판단했습니다.

→ 확인 ① 장비 선택 UI 가 `devices.id` 를 전송하는지(인덱스·`number_device` 혼동 여부)
② **컨트롤러/센서 목록 API 의 `id` 필드를 그대로 쓰는지**. 그리고 생성 후 응답의 `target_device_ids` 를
**장비명으로 되풀이 표시**해 운영자가 육안 확인할 수 있게 하는 것을 강력 권장합니다.

### 2.5 억제 판정 규칙 (클라이언트-측 복제 시 동일 로직)

한 장비 이벤트 `(device_id, category)` 가 활성 창 `W` 에 억제되는 조건:

```
category ∈ {detection, malfunction, connection}      # action(조치보고)은 억제 대상 아님
AND (W.event_scope == 'all' OR W.event_scope == category)
AND scope_match:
      W.target_type == 'device' : device_id ∈ W.target_device_ids
      W.target_type == 'all'    : side_match(device_side, W.target_side)
      W.target_type == 'group'  : (groups(device_id) ∩ W.target_group_ids) ≠ ∅ AND side_match(...)

device_side = sensor|controller       → 'detection'
              camera                  → 'surveillance'
              speaker|lamp|enclosure  → 'auxiliary'
side_match(ds, ts) = (ts == 'both') OR (ds == ts)    # 보조 장비는 'both' 일 때만 매치
```

- 그룹 멤버십은 라이브 이벤트 body 의 `device.device_groups[]`(브로커 명세 §6.1)로 로컬 판정 가능.
- 창 유효: `window_start <= now < window_end` AND `revoked_at == null`.

### 2.6 억제된 이벤트 POST 응답 — 202 (Proxy/AiAnalysis 필독)

장비 이벤트를 `POST /api/events/detections|malfunctions|connections` 로 보낼 때 억제 창에 걸리면
서버는 **201 대신 202** 를 반환하고 **레코드를 만들지 않습니다**:

```json
HTTP/1.1 202 Accepted
{ "success": true, "suppressed": true,
  "message": "Event (detection) suppressed by active maintenance window",
  "schedule_id": 12 }
```

**조치**:
- 응답 분기에 **202 = "성공(억제됨)"** 추가. 201/202 모두 정상 종료.
- **재시도·에러 로깅 금지** (202 를 실패로 오인하면 무한 재시도/알람 발생).
- 로깅은 **정보성**(`suppressed schedule_id=…`)으로만 — **에러 레벨 금지**.
- 202 응답에는 이벤트 `id` 가 없음 → 이후 id 기반 후속 처리(PATCH 등) 대상에서 제외.

```csharp
var res = await httpClient.PostAsync(url, content);
if      (res.StatusCode == HttpStatusCode.Created)  { /* 저장됨: id 사용 */ }
else if (res.StatusCode == HttpStatusCode.Accepted) { /* 억제됨: 정상 종료, 재시도 금지 */ }
else                                                { /* 실제 오류 처리 */ }
```

### 2.7 ★ NATS 알림 `SYNC_EVENT_SUPPRESSION` (v6.3.2 신설)

정비 창이 바뀌거나 창이 **시작·종료**되면 서버가 NATS 로 알립니다. 폴링 주기를 기다리지 않고 즉시 반영 가능.

```
Subject : sensorway.{부대ID}.all.sync.event-suppression
cmd     : SYNC_EVENT_SUPPRESSION      from: DBApi      m_type: PUB
body    : { "action": "CREATED|UPDATED|DELETED", "resource_id": 12, "status": "active" }
```

- **구독 추가 불필요** — NATS 를 수신하는 6개 서브시스템(GIS · PidsProxy · BroadcastingManager ·
  NVRManager · VMS · AiAnalysis)은 이미 `all.sync.*` 를 구독하므로 자동 수신됩니다(브로커 명세 §3.4).
  **Central 은 NATS 미수신** → [§3.7](#37-central).
- **필수 2가지**: `EnumGopCommand` 에 cmd 추가 + **미지 cmd graceful skip** 방어(+회귀 테스트).
- **처리**: action 별로 분기하지 말고 **무조건 `GET /active` 재조회**로 억제 목록을 갱신하면 됩니다.

**action 매핑 — HTTP 메서드와 다릅니다**

| 발생 사건 | action | status |
|---|---|---|
| 정비 창 생성 | `CREATED` | 생성 시점 상태 |
| 창 시간·이름·**대상 배열** 변경 | `UPDATED` | 변경 후 상태 |
| **취소**(`DELETE /{id}` — soft-cancel) | **`UPDATED`** | **`cancelled`** |
| **창 시작 / 창 종료**(시간 도달) | `UPDATED` | `active` / `expired` |
| **하드삭제**(`bulk-delete`) | `DELETED` | (없음) |

> `DELETE /{id}` 는 물리삭제가 아니라 `revoked_at` 을 세팅하는 soft-cancel 이라 **`DELETED` 가 아니라
> `UPDATED`** 로 옵니다. `DELETED` 는 `bulk-delete` 로 목록에서 완전히 지운 경우뿐이고, 그 대상은
> 이미 terminal 이라 **억제 상태 변화가 아닙니다**(캐시 eviction 전용).

**통지 지연**: 정상 **≤5초**, 서버 재기동 등 예외 시 **≤5분**.
단 서버측 억제 판정 자체는 요청시점 계산이라 **지연 0** — 통지만 늦습니다.

### 2.8 ★ fail-safe 규범 (MUST)

NATS Core 는 **at-most-once** 라 **유실이 정상 경로**입니다. 안전 비대칭이 극단적입니다:

| 유실 대상 | 결과 | 판정 |
|---|---|---|
| 창 시작(`active`) 신호 | 억제가 늦게 걸림(정비 중 알람이 좀 시끄러움) | **허용** |
| **창 종료(`expired`) 신호** | **억제가 영원히 안 풀림 = 영구 침묵** | **금지** |

1. **`expired` 신호로 해제하지 말고**, 캐시한 `window_end` **로컬 타이머 만료로 스스로 푼다** ← **1차 권위**
2. **`GET /active` 30~60초 폴링 유지**(창 경계 정밀도는 분 단위로 충분하므로 이 주기면 됩니다) — SYNC 가 생겼다고 폴링을 제거하면 안 됨(**폴링이 권위, SYNC 는 가속**)
3. **캐시 TTL(폴링 주기 ×3)** 초과 시 자동으로 "억제 없음"으로 수렴(**fail-open**)

서버 게이트도 fail-open(게이트 오류 시 억제하지 않고 정상 저장)이라 전 구간이 일관됩니다.

---

## 3. 서브시스템별 상세

### 3.1 GIS (관제 / Central UI)

**역할**: `all.event.>` 구독 → 상황도 알람 표시. 운영자 조작 창구. **정비 창 관리 UI의 주체**.

#### G-1. 정비 창 관리 UI (Phase 1, 필수)

7개 엔드포인트([§2.1](#21-rest-엔드포인트-7개)) 연동. 입력 폼은 [§2.2 필드 사전](#22-필드-사전) 그대로.

> ★ **v6.3 파괴적 변경**: 대상 필드가 **단수 → 배열**입니다.
> `target_device_id` → **`target_device_ids: int[]`**, `target_group_id` → **`target_group_ids: int[]`**
> 구 필드로 보내면 **422**(`extra=forbid`). **장비/그룹 다중 선택 UI** 필요.

- 상태 배지는 **`status`** 사용, **`is_active` 미사용**([§2.2](#22-필드-사전)).
- 시간은 **offset 포함 전송**([§2.3](#23--시간대-규약--가장-흔한-사고)).
- 장비 선택이 **`devices.id`** 를 보내는지 확인([§2.4](#24--장비-id-주의--devicesid-를-보낼-것)).
- 권한별 버튼 제어(`events:view/edit/delete`).

#### G-2. 삭제 2종 — 반드시 구분

| | `DELETE /{id}` | `POST /bulk-delete` |
|---|---|---|
| 성격 | **취소**(soft-cancel) | **하드삭제**(물리 제거) |
| 결과 | `status=cancelled`, 목록에 **남음** | 행+대상 매핑 완전 제거, **복구 불가** |
| 억제 중단 | ✅ 즉시 | (이미 terminal 인 것만 대상) |
| 대상 제한 | 없음 | **취소·종료(`cancelled`/`expired`)만** |
| 용도 | 정비 조기 종료 / 잘못 만든 창 중단 | **목록 정리** |
| **멱등** | 재호출 시 200 (이미 취소면 `revoked_at` 유지) | 없는 id 는 `not_found_ids` 로 보고 |

```
DELETE /api/event-suppression-schedules/12
→ 200, data.status = "cancelled", data.revoked_at 세팅
```

취소 직후 **`GET /active` 를 재조회**해 배너를 갱신하세요([§4-B](#4-b-겹치는-창을-만들면-하나만-취소해도-억제가-계속된다)).

```json
POST /api/event-suppression-schedules/bulk-delete
{ "ids": [3, 5, 8, 14] }
```

```json
{
  "success": true,
  "message": "삭제 2건 · 스킵(활성/예정) 2건 · 없음 0건",
  "data": {
    "deleted_ids":   [3, 5],
    "skipped_ids":   [8, 14],
    "not_found_ids": []
  }
}
```

> ⚠ 세 배열은 **`data` 하위**입니다(공통 `ApiSingleResponse` 래퍼). `res.deleted_ids` 가 아니라
> `res.data.deleted_ids` 로 읽어야 합니다.

| 필드 | UI 처리 |
|---|---|
| `deleted_ids` | 목록에서 제거 |
| `skipped_ids` | **"진행 중/예정이라 삭제 불가. 먼저 취소하세요."** 안내 |
| `not_found_ids` | 이미 지워짐 — 조용히 목록 갱신 |

- `ids` **1~500건**, 중복은 서버가 제거. 빈 배열 **422**.
- **활성·예정 창은 절대 삭제되지 않습니다**(오삭제 방지). 지우려면 `DELETE /{id}` 로 먼저 취소.
- **권장 UI**: `status ∈ {cancelled, expired}` 행에만 체크박스 + "선택 삭제"/"종료·취소 모두 정리".
  복구 불가이므로 **확인 다이얼로그 필수**.

#### G-3. 활성 억제 배너 (Phase 1, 필수 안전장치)

정비 중에는 **일부 이벤트가 억제 중임을 운영자가 항상 인지**해야 합니다(억제 사실이 숨겨지면 실제
장애를 놓칩니다).

- `GET /active` **30~60초 폴링** + `SYNC_EVENT_SUPPRESSION` 수신 시 즉시 갱신([§2.7](#27--nats-알림-sync_event_suppression-v632-신설)).
- 활성 창 ≥1건이면 배너: `⚠ 이벤트 억제 중: {name} — {대상 요약} / {event_scope} / ~{window_end}`
- 대상 요약: `device`→장비명 나열, `group`→그룹명 나열, `all`→"전체({target_side})"
- **여러 창이 동시 활성일 수 있음** — 건수 함께 표시. 배너 클릭 → 관리 UI 해당 창으로 이동.
- 특정 장비가 억제 중인지는 [§2.5 판정 규칙](#25-억제-판정-규칙-클라이언트-측-복제-시-동일-로직)으로 로컬 판정.

#### G-4. (Phase 2, D1=Yes) 알람 필터/딤

`all.event.*` 수신 시 §2.5 로 매치 판정 → 알람 팝업/사운드 억제 + 상황도 아이콘 **딤/정비 아이콘**.

> **주의**: 탐지 이벤트 필터는 실제 침입을 가릴 수 있습니다. **"숨김"이 아니라 "정비 중 표식 +
> 알람 톤 완화"** 로 구현하고, 억제된 이벤트 수를 별도 카운트/로그로 남기세요(은폐 방지).

#### G-5. NATS 3원칙 (Phase 1, 필수)

[§2.7](#27--nats-알림-sync_event_suppression-v632-신설)·[§2.8](#28--fail-safe-규범-must) 적용.
GIS 는 이미 `sensorway.*.all.sync.*` 를 구독하므로 **구독 추가는 불필요**합니다.

1. `EnumGopCommand` 에 **`SYNC_EVENT_SUPPRESSION`** 추가
2. **미지 cmd graceful skip** 방어 + 회귀 테스트 ← 빠뜨리면 SYNC 수신 루프 전체가 죽어 **장비 동기화까지 멈춥니다**
3. **`expired` 신호로 배너를 내리지 말 것** — 캐시한 `window_end` 로컬 타이머가 1차 권위, `/active` 폴링 존치

수신 시 action 분기 없이 **무조건 `GET /active` 재조회** → 배너·필터 갱신.

---

### 3.2 PidsProxy

**역할**: 필드 센서(펜스/PIR/케이블)의 탐지·장애·연결 이벤트를 **발행**(`all.event.detect` 등)하고,
동시에 DBApi 로 **HTTP POST** 하는 주체.

#### P-1. 202 억제 응답 처리 (Phase 1, ★필수)

[§2.6](#26-억제된-이벤트-post-응답--202-proxyaianalysis-필독) 그대로. 201만 성공으로 보던 코드에 202 분기 추가, **재시도 금지**.

#### P-2. connection POST 인증 정합 (Phase 1, 필수)

`POST /api/events/connections` 에 라우트-레벨 인가(`events:edit`)가 명시적으로 추가됐습니다
(기존에도 중앙 매트릭스가 token 모드에서 커버했으나 데코레이터 정합으로 방어 심화).
→ token 모드 배포에서 connection POST 에 **Bearer 토큰이 첨부되는지 확인**. 무토큰이면 401.

#### P-3. (Phase 2, D1=Yes) 라이브 발행 억제

서버 억제는 **저장만** 막습니다. Proxy 가 이미 `all.event.detect` 로 **직접 방송**한 라이브 이벤트는
GIS/VMS/NVR 이 그대로 받습니다.

1. `GET /active` 폴링 + 캐시, `SYNC_EVENT_SUPPRESSION` 으로 즉시 갱신.
2. 이벤트 발행 직전 [§2.5](#25-억제-판정-규칙-클라이언트-측-복제-시-동일-로직) 로 `(device_id, category)` 판정.
   **그룹 멤버십은 Proxy 가 보유한 장비-그룹 정보**로 판정합니다(이벤트 body 의존 불필요).
3. 매치 시 선택:
   - **(권장) skip** — `all.event.*` 발행 생략(완전 억제). 서버 POST 는 **"생략" 또는 "유지(202 수신)"
     중 택1** — 유지하면 억제 건수가 서버 로그에 남아 관측성이 좋습니다.
   - **mark** — 발행하되 body 에 `suppressed:true` (+ **`suppression_schedule_id`**) 를 실어 소비자가 필터.
     브로커 스펙 필드 추가 **협의 필요**.
4. **감지/감시 side**: Proxy 소관은 감지쪽(sensor/controller). `target_side=surveillance` 창은 영향 없음,
   `detection`/`both` 만 반영.

> **★ 안전 주의**: 탐지(detection) 발행 skip 은 **실제 침입을 놓칠 수 있습니다.** 반드시 활성 창만
> 반영하고 **창 종료 즉시 정상 발행 복귀**. 억제 발행 건수는 로깅.

#### P-4. NATS 3원칙 — Proxy 가 가장 위험

[§2.7](#27--nats-알림-sync_event_suppression-v632-신설)·[§2.8](#28--fail-safe-규범-must) 적용. Proxy 는 **탐지 이벤트의 원천**이라 안전 비대칭이 가장 큽니다:

| 유실 | 결과 | |
|---|---|---|
| 창 시작 신호 | 억제가 늦게 걸림(정비 중 오탐이 좀 올라옴) | 허용 |
| **창 종료 신호** | **탐지 발행이 영원히 안 풀림 = 실제 침입을 못 잡음** | **절대 금지** |

---

### 3.3 AiAnalysis

**역할**: AI 영상 탐지 **발행자**(`all.event_ai.detect`, `vms.event_ai.detect`). 탐지 이벤트의 원천이며
DBApi 로 탐지 이벤트를 POST 할 수 있습니다.

- **A-1 (Phase 1)**: DBApi 로 detection 을 POST 한다면 **202 처리**([§2.6](#26-억제된-이벤트-post-응답--202-proxyaianalysis-필독)) — Proxy P-1 과 동일.
- **A-2 (Phase 2, D1=Yes)**: 활성 창 매치 AI 탐지 **발행 skip/mark**. AI 탐지는 대개 **감시쪽(카메라)**
  이므로 `target_side ∈ {surveillance, both}` 또는 카메라 device/그룹 창을 반영. 창 종료 즉시 복귀, 억제 건수 로깅.
- **A-3 (Phase 1)**: NATS 3원칙. **창 종료 신호 유실 = AI 탐지가 영원히 안 풀림 = 실제 침입 미탐지**(금지).

---

### 3.4 VMS

**역할**: 영상/RTSP 스트리밍, **이벤트 트리거 반응**(자동 녹화 시작, 연동 카메라 PTZ 프리셋 이동,
팝업/타일 강조). 감시쪽(camera) 중심.

> VMS 는 서버로 장비 이벤트를 POST 하는 주체가 아니라 **202 처리 불필요**. Phase 1 은 NATS 3원칙만.

- **V-1 (Phase 2, D1=Yes)**: 억제 창에 든 **카메라의 이벤트 트리거 반응 억제**
  1. `GET /active` 폴링 + `SYNC_EVENT_SUPPRESSION` 즉시 갱신.
  2. 대상 카메라 산출 — **`target_side` 는 `group`·`all` 창에만 적용**됩니다(서버 게이트도 동일:
     device 창은 side 를 보지 않음). 따라서
     **device 창 → 대상이 카메라면 side 무관하게 반영** / `group`·`all` 창 → `target_side ∈ {surveillance, both}` 일 때
     그룹의 카메라 멤버 또는 전체 카메라.
  3. 대상 카메라의 **이벤트 기반 자동 녹화 시작·연동 PTZ 프리셋 이동·팝업/타일 강조** 일시 중지
     (상시/수동 녹화는 유지 — 정책 선택).
  4. `event_scope` 고려(예: `detection` 창은 탐지 연동 반응만). **창 종료 즉시 복귀.**
- **V-2 (Phase 2, 설계 참조)**: 기존 CameraPreset `is_restricted_zone`(감시금지구역)은 **공간 기반**으로
  **VMS = RTSP/녹화 차단 · db_monitor = 이벤트 발행 차단 · AiAnalysis = 분석 억제** 를 팬아웃합니다
  (공간 신호 `PTZ_STATUS`). 정비 창은 그 **시간 기반 버전**이므로, **세 컴포넌트 모두** 기존 억제
  파이프라인에 **"활성 정비 창에 걸린 카메라" 조건을 OR 로 얹으면 최소 변경**으로 구현됩니다.
  이때 `SYNC_EVENT_SUPPRESSION` 이 **그 파이프라인의 갱신 트리거**가 됩니다
  (공간 `PTZ_STATUS` ↔ 시간 `SYNC_EVENT_SUPPRESSION`, 같은 자리에 OR 로).
- **V-3 (Phase 1)**: NATS 3원칙. 창 종료 신호 유실 = **이벤트 트리거 녹화/팝업이 영원히 안 돌아옴**.

---

### 3.5 NVRManager

**역할**: 카메라 녹화 관리(이벤트 트리거 녹화 포함). 서버로 장비 이벤트를 POST 하지 않으므로
Phase 1 은 NATS 3원칙만.

- **N-1 (Phase 2, D1=Yes)**: VMS V-1 과 동일 원리 —
  감시쪽 창(`target_side ∈ {surveillance, both}`) 대상 카메라의 **이벤트 트리거 녹화 시작만** 스킵.
  **상시/스케줄 녹화는 유지 권장**(증적 보존). `event_scope` 반영, 창 종료 즉시 복귀.
  > **정책 확정 필요**: "이벤트 트리거 추가 녹화"만 억제할지, 전부 억제할지 NVR/운영팀 합의.
- **N-2 (Phase 1)**: NATS 3원칙. 창 종료 신호 유실 = **이벤트 트리거 녹화가 영원히 안 돌아옴 = 증적 소실**.
  상시 녹화를 유지하면 피해가 줄지만, **이벤트 녹화만 조용히 빠진 상태는 알아채기 어렵습니다.**

---

### 3.6 BroadcastingManager

- **Phase 1**: NATS 3원칙(최소) — `EnumGopCommand` 추가 + graceful skip.
- **Phase 2 (D1=Yes, 해당 시)**: 억제 창 중 **이벤트 연동 자동 방송 억제**.
  정비 중 억제된 탐지에 연동된 자동 TTS/방송이 불필요하게 나가는 것을 막습니다.
  판정은 [§2.5](#25-억제-판정-규칙-클라이언트-측-복제-시-동일-로직) 동일.

---

### 3.7 Central

**Central 은 NATS 를 수신하지 않습니다**(브로커 명세 §3.4 — 발행 전용, 데이터는 DBApi HTTP 경유).

→ `SYNC_EVENT_SUPPRESSION` 이 **도달하지 않습니다.** 배너·정비 창 상태는 **`GET /active` HTTP 폴링**
(30~60초)으로만 구현합니다. 나머지 계약([§2.1](#21-rest-엔드포인트-7개)~[§2.6](#26-억제된-이벤트-post-응답--202-proxyaianalysis-필독)) 및
**[§2.8 fail-safe](#28--fail-safe-규범-must)**(로컬 `window_end` 타이머 1차 권위 · 캐시 TTL = 폴링 주기 ×3
fail-open)는 **동일하게 적용**됩니다. **[§2.7](#27--nats-알림-sync_event_suppression-v632-신설)(NATS)만 해당 없음.**

---

### 3.8 db_monitor 참고

> 우리(DBApi) 컴포넌트라 **서브시스템 팀의 할 일은 없습니다.** 발행 경로 이해용 참고 절입니다. (v6.3.2 완료)

**역할**: DBApi 의 **NATS 발행 브리지**(Postgres LISTEN → NATS). 장비 탐지/장애 이벤트는 발행하지
않습니다(그건 Proxy/AiAnalysis 소관).

**v6.3.2 변경분 (반영 완료)**:

```python
CMD_SUBJECT_MAP = {
    ...
    "SYNC_EVENT_SUPPRESSION": "all.sync.event-suppression",
}
```

- `cmd_to_subject()` 가 **미등재 cmd 를 만나면 경고 로그**를 남기도록 보강(종전에는 조용히 drop → 무성 유실).
- **★ 배포 순서 고정: db-monitor 먼저 → api-server.** 역순이면 새 cmd 가 NOTIFY 되는데 매핑이 없어 버려집니다.

**서버측 발행 경로 (참고)**:

| # | 트리거 | 담당 |
|---|---|---|
| 1 | `event_suppression_schedules` row-level | 생성/시간·이름 변경/취소(soft-cancel)/하드삭제 |
| 2 | junction 2테이블 statement-level | **대상 배열만 바꾸는 PATCH**(부모 행이 dirty 가 안 돼 UPDATE 문이 안 나감) |
| 3 | 창 경계 date-job → `notified_status` UPDATE | **창 시작**(DB 쓰기가 없어 트리거로 포착 불가) / 창 종료 |

---

## 4. ⚠ 알려진 서버 제약 (회피 필요)

`§4-A` 는 v6.3.2 에서 해소됐고, 나머지는 하드닝 PRD 대상으로 **아직 반영 전**입니다.

### 4-A. ~~PATCH 가 device/group 창에서 500~~ → **해소됨 (v6.3.2)**

> ✅ **후속 커밋 `b92082f` 이상에서 해소** — device/group 대상 창의 PATCH 가 정상 동작합니다
> (이름 변경 / 창 연장 / 대상 추가·축소 / 완전 교체 **전부 200**). 원인은 junction 재구성 시
> UNIQUE 위반이었고 delta 동기화로 전환했습니다.
>
> ⚠ **테스트 서버는 `36128f7` 이라 아직 500** 입니다 — [§0.3](#03--배포-상태-2026-08-03-기준) 의
> PATCH 200/500 프로브로 확인한 뒤 회피 로직(취소 후 재생성)을 제거하세요.

### 4-B. 겹치는 창을 만들면 하나만 취소해도 억제가 계속된다

동일 장비·동일 시간대에 **중복 창을 무제한 생성**할 수 있고, 서버는 억제 시 **매치된 창 중 1건만**
`schedule_id` 로 알려줍니다.

→ 취소 후 **반드시 `GET /active` 재조회**해 그 장비를 덮는 창이 남았는지 확인하고, 남아 있으면 배너 유지.
생성 폼에서 "같은 대상에 진행 중인 창이 이미 있습니다" 사전 경고 권장.

### 4-C. `?device_id=` 필터로는 `group`/`all` 창이 안 잡힌다

`GET ?device_id=1352` 는 **`target_device_ids` 배열 직접 매치만** 합니다. 그 장비를 실제로 억제 중인
**그룹 창·전체 창은 결과에 포함되지 않습니다.**

→ "이 장비가 지금 억제 중인가?"는 필터가 아니라 **`GET /active` 전체 + [§2.5](#25-억제-판정-규칙-클라이언트-측-복제-시-동일-로직) 로컬 판정**으로 하세요.

### 4-D. PATCH 에 명시적 `null` 을 보내면 422 가 아니라 **500**

`{"window_end": null}`, `{"name": null}` 처럼 NOT NULL 컬럼에 **명시적 null** 을 보내면 서버가 500 을 냅니다
(하드닝 PRD #5, 라이브 재현). `.NET` 기본 직렬화가 미설정 필드를 `null` 로 실어 보내면 그대로 걸립니다.

→ **PATCH body 에는 실제로 바꿀 필드만 담고, null 은 보내지 마세요.** `description` / `recurrence_rule`
같은 nullable 필드만 null 이 유효합니다.

### 4-E. 대상 장비/그룹을 삭제하면 창이 조용히 무력화된다

대상 매핑은 `devices.id` / `device_groups.id` 에 **FK CASCADE** 로 걸려 있습니다. 장비(또는 그룹)를
삭제하면 그 창의 대상 목록에서 **조용히 빠지고**, 단일 대상이었다면 **대상 0개 = 아무것도 억제하지
않는 빈 창**이 됩니다. 그런데도 `status` 는 `active` 로 남고 `/active` 에도 계속 나옵니다.

→ 배너 렌더 시 `target_device_ids`/`target_group_ids` 가 **빈 배열인 active 창**은 "대상 없음(무효)"로
경고 표시하고, 장비 삭제 화면에서 "이 장비를 대상으로 하는 정비 창 N건"을 사전 안내하세요.

### 4-F. naive datetime 을 수용해 생성 응답만 +9h 로 어긋난다

억제 **동작 자체는 정상**이고 응답 표시만 틀립니다(하드닝 PRD #3, 미수정). [§2.3](#23--시간대-규약--가장-흔한-사고) 의
offset 포함 전송으로 회피하고, **서버 수정 후에도 offset 전송은 유지**하는 것이 안전합니다.

### 4-G. 기타

- **취소한 창은 되살릴 수 없습니다.** 취소된 창에 PATCH 하면 200 이 오지만 **효과가 없습니다**
  (`status` 는 `cancelled` 유지). 재사용이 필요하면 새로 생성.
- **창 길이 상한이 없습니다.** 오타로 1년짜리 전체 억제도 생성됩니다 → **폼에서 최대 기간(예: 30일) 검증 권장**.
- 억제 중에는 장애/복구 이벤트가 버려지므로 **장비 상태가 창 종료 후에도 이전 값으로 남을 수 있습니다.**

---

## 5. 통합 체크리스트

### 5.1 공통 (Phase 1, 필수) — 1·2번은 **NATS 수신 팀만**(Central 제외)

- [ ] `EnumGopCommand` 에 **`SYNC_EVENT_SUPPRESSION`** 추가 (구독 추가는 **불필요**)
- [ ] **미지 cmd graceful skip** 방어 + 회귀 테스트 ← 빠뜨리면 SYNC 수신 루프 전체 중단
- [ ] 수신 시 **`GET /active` 재조회**로 억제 목록 갱신 (action 별 분기 불필요)
- [ ] **`expired` 신호로 해제 금지** — 로컬 `window_end` 타이머가 1차 권위
- [ ] **`/active` 폴링 유지**(SYNC 도입해도 제거 금지) + 캐시 TTL(주기×3) fail-open

### 5.2 GIS

- [ ] `target_device_id` → **`target_device_ids: int[]`**, `target_group_id` → **`target_group_ids: int[]`** 전환
- [ ] 장비/그룹 **다중 선택** UI
- [ ] 7개 엔드포인트 연동 + 권한별 버튼 제어
- [ ] `bulk-delete` 연동 + **확인 다이얼로그** + `skipped_ids` 안내
- [ ] 시간 **offset 포함**(`+09:00`) 전송 — 또는 생성 후 재조회
- [ ] 장비 선택이 **`devices.id`** 를 보내는지 확인 ← **최우선**
- [ ] 상태 배지는 **`status`**, `is_active` **미사용**
- [ ] 생성 후 응답 `target_device_ids` 를 장비명으로 되풀이 표시
- [ ] 활성 배너 상시 표시 + 다중 창 건수
- [ ] 취소 후 `GET /active` 재확인(겹친 창 잔존)
- [ ] "이 장비 억제 중?" 판정은 `?device_id=` 필터가 아니라 **`/active` 전체 + 로컬 판정**([§4-C](#4-c-device_id-필터로는-groupall-창이-안-잡힌다))
- [ ] 창 최대 기간(예: 30일) 폼 검증
- [ ] (Phase 2) 알람 딤/정비 표식 + 억제 카운트

### 5.3 PidsProxy

- [ ] **202 분기 추가**, 재시도/에러 오인 제거
- [ ] connection POST 토큰 첨부 확인(token 모드 401 회귀 방지)
- [ ] 억제 발행/POST 건수 로깅(관측성)
- [ ] 창 종료 후 정상 발행 자동 복귀 검증
- [ ] (Phase 2) 활성 창 폴링 + 발행 skip/mark (감지쪽 `detection`/`both` 창만)

### 5.4 AiAnalysis

- [ ] **202 분기 추가**(서버 POST 시)
- [ ] (Phase 2) 활성 창 매치 AI 탐지 발행 skip/mark (감시쪽 창)

### 5.5 VMS

- [ ] (Phase 2) 활성 창 폴링 + 감시쪽 창 카메라 산출
- [ ] (Phase 2) 이벤트 트리거 녹화/PTZ/팝업 억제 (상시 녹화 유지 여부 정책 확정)
- [ ] (Phase 2) `is_restricted_zone` 억제 파이프라인에 **시간창 조건 OR 추가**(재사용)
- [ ] `event_scope`·창 종료 복귀 검증

### 5.6 NVRManager

- [ ] (Phase 2) 감시쪽 창 카메라의 이벤트 트리거 녹화 억제
- [ ] (Phase 2) **상시 녹화 유지 여부 정책 확정**(증적 보존)

### 5.7 BroadcastingManager

- [ ] (Phase 2, 해당 시) 이벤트 연동 자동 방송 억제

### 5.8 Central

- [ ] `GET /active` HTTP 폴링으로 배너 구현 (**NATS 미수신**)
- [ ] 로컬 `window_end` 타이머로 자체 해제 + **캐시 TTL(폴링 주기 ×3) fail-open** ([§2.8](#28--fail-safe-규범-must))

### 5.9 db_monitor (우리 컴포넌트)

- [x] `CMD_SUBJECT_MAP` 에 `SYNC_EVENT_SUPPRESSION` 등재 + 미등재 cmd 경고 로그
- [x] `SYNC_EVENT_SUPPRESSION` 발행 + 브로커 스펙 v1.6 §9.12 개정
- [ ] **배포 시 db-monitor 를 먼저 재빌드·기동한 뒤 api-server** (역순이면 새 cmd 가 무성 유실)

---

## 6. 결정 필요 · 문의

### D1 — 라이브 경로 억제 요구 여부 (PM 결재 대기)

| 결정 | 각 팀 범위 |
|---|---|
| **D1 = No** (서버 저장 억제만) | 전 팀 **§5.1 공통 3원칙만** + GIS 관리 UI·배너까지 |
| **D1 = Yes** (라이브 차단) | 위 + 각 팀 **Phase 2** 항목 백로그 등록 |

### 문의

| 항목 | 위치 |
|---|---|
| REST 계약 원본 | `GOP_Restful_Api_연동설계.md` **§6.8** |
| NATS 메시지 계약 원본 | `Gop_Message_Broker_연동설계_v1.6.md` **§9.12** |
| 서버 결함 수정 계획 | `docs/prds/event-suppression-hardening-prd.md` |
| 기능 PRD | `docs/prds/event-suppression-schedule-prd.md` v1.1 · `event-suppression-sync-message-prd.md` |
| **이 문서를 참조하는 계약 원본** | 브로커 §9.12(→§2.5) · REST §6.8.10(→§2.6/§3.2) — **개정 시 양쪽 동시 갱신** |
| 담당 | 이기호 차장 |
