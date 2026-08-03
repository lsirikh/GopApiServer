# GIS(관제 / Central UI) — 이벤트 억제(정비 창) 연동 안내

- **문서 버전**: v2.0 · **갱신일**: 2026-08-03 · **우선순위**: ★최상
- **대상 API 버전**: **6.3.2** (`release/v6.3`)
- **상위 문서**: [README.md](README.md) (공통 계약·범위 경계)
- **서버 마스터 명세**: `GOP_Restful_Api_연동설계.md` §6.8
- **GIS 역할**: `all.event.>` 구독 → 상황도(GMaps) 알람 표시. 운영자 조작 창구. **정비 창 관리 UI의 주체**

---

## 0. v1.0 → v2.0 변경 요약 (GIS 필독)

| # | 변경 | 영향 |
|---|---|---|
| **C-1** | 대상 필드가 **단수 → 배열**: `target_device_id` → **`target_device_ids: int[]`**, `target_group_id` → **`target_group_ids: int[]`** | **파괴적**. 구 필드로 보내면 **422**(`extra=forbid`) |
| **C-2** | 한 정비 창에 **장비 N개 / 그룹 N개** 지정 가능 (모드는 여전히 배타) | UI 다중선택 필요 |
| **C-3** | **일괄 하드삭제 신규**: `POST /api/event-suppression-schedules/bulk-delete` | 목록 정리 버튼 구현 가능 |
| **C-4** | 엔드포인트 6개 → **7개** | — |

> ⚠ **배포 상태 주의 (2026-08-03 기준)**
> `bulk-delete`(C-3)는 **로컬 개발 서버(6.3.2)에만 반영**되어 있고,
> **테스트 서버 `https://123.141.236.253:8136` 는 아직 6.3.1** 이라 호출 시 **405** 가 난다.
> 해당 서버 재배포 후 사용할 것. 버전은 `GET /openapi.json` → `info.version` 으로 확인.

---

## 1. 엔드포인트 전체 (7개)

Base: `/api/event-suppression-schedules`

| # | Method | Path | 인가 | 용도 |
|---|---|---|---|---|
| 1 | POST | `` | events:edit | 억제 창 생성 |
| 2 | GET | `` | events:view | 목록(상태·대상 필터, 페이지) |
| 3 | GET | `/active` | events:view | **현재 활성 창**(배너·폴링) |
| 4 | GET | `/{id}` | events:view | 단건 조회 |
| 5 | PATCH | `/{id}` | events:edit | 부분 변경 ⚠ §5-A 주의 |
| 6 | DELETE | `/{id}` | events:delete | **취소**(soft-cancel, 이력 보존) |
| 7 | POST | `/bulk-delete` | events:delete | **일괄 하드삭제**(목록 정리) |

`role=ADMIN` 은 전권 bypass. 권한 없으면 서버가 **403**, 미인증은 **401**.
화면 노출·버튼 활성은 `events:view/edit/delete` 에 맞춰 제어할 것.

---

## 2. 필드 사전

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `name` | string(1~200) | ✔ | 작업명/사유 (예: "GOP 3구역 펜스 보수") |
| `description` | string(0~500) | | 상세 설명 |
| `target_type` | enum | ✔ | `device` \| `group` \| `all` — **배타 모드** |
| **`target_device_ids`** | **int[]** | `device`일 때 ≥1 | **`devices.id`** 배열 (§6 주의) |
| **`target_group_ids`** | **int[]** | `group`일 때 ≥1 | `device_groups.id` 배열 |
| `target_side` | enum | | `detection` \| `surveillance` \| `both`(기본). **`group`·`all` 에만 적용** |
| `event_scope` | enum | ✔ | `connection` \| `detection` \| `malfunction` \| `all` |
| `window_start` | datetime | ✔ | 억제 시작 — **반드시 offset 포함**(§4) |
| `window_end` | datetime | ✔ | 억제 종료 — 필수(무기한 침묵 금지), `> window_start` |
| `recurrence_rule` | string | | **현재 미해석(단발 전용)**. 값을 넣어도 반복되지 않음 — UI 미노출 권장 |

**응답 전용 필드**

| 필드 | 설명 |
|---|---|
| `id` | 스케줄 id |
| `status` | **파생 상태** — `pending` \| `active` \| `expired` \| `cancelled` (배지 표시는 이 값 사용) |
| `is_active` | ⚠ **UI 표시 금지**. 내부 sweep 플래그로, **예정(pending) 창도 `true`** 이고 만료 후 최대 5분 지연으로 꺼진다. "억제 중" 판단은 반드시 `status` 로 |
| `revoked_at` | 취소 시각(취소 아니면 null) |
| `created_by`, `created_at`, `updated_at` | 감사용 |

**`target_side` 파생 규칙** (서버가 장비 종류로 자동 판정)

| 장비 종류 | side |
|---|---|
| sensor, controller | `detection` |
| camera | `surveillance` |
| speaker, lamp, enclosure | 보조 — **`target_side=both` 일 때만** 매치 |

---

## 3. 요청/응답 예시

### 3.1 생성 — 장비 3개

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

### 3.2 생성 — 그룹 2개 + 감지쪽만

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

### 3.3 응답 (201 / 200 공통)

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

**에러**: `400` 대상 id 미존재(`Device id(s) not found: [...]`) · `422` `end<=start`/모드별 배열 ≥1 위반/enum 불량 · `401`/`403` 인가.

### 3.4 목록 조회

```
GET /api/event-suppression-schedules?page=1&limit=20&status=active&target_type=device&device_id=1352
```

| 파라미터 | 설명 |
|---|---|
| `page`, `limit` | 페이지네이션 (limit 1~100) |
| `status` | `pending`/`active`/`expired`/`cancelled` |
| `target_type` | `device`/`group`/`all` |
| `device_id`, `group_id` | 대상 배열 포함 매치 ⚠ §5-C 한계 |

응답에 `pagination: {page, limit, total, total_pages}` 동반.

---

## 4. ★ 시간대 규약 (가장 흔한 사고)

> **반드시 offset 을 붙여 보낼 것** — `"2026-08-03T09:00:00+09:00"`

`.NET` 의 `DateTime` 을 offset 없이 직렬화(`"2026-08-03T09:00:00"`)해 보내면:

| | `window_start` | `status` |
|---|---|---|
| 보낸 값 | `09:00:00` | (즉시 억제 의도) |
| **생성 응답** | **`18:00:00+09:00`** ❌ | **`pending`** ❌ |
| 목록 재조회 | `09:00:00+09:00` ✅ | `active` ✅ |
| 실제 억제 동작 | — | **정상 억제됨** ✅ |

**즉, 서버는 올바르게 억제하지만 생성 직후 응답만 9시간 어긋나 "억제가 안 걸렸다"고 오인**하게 된다
(서버측 알려진 결함, 수정 예정). 회피법 2가지:

1. **offset 포함 전송**(권장) — `DateTimeOffset` 사용, `"yyyy-MM-ddTHH:mm:sszzz"` 포맷
2. 생성 직후 **목록/단건을 재조회**해 화면 갱신

---

## 5. ⚠ 현재 서버의 알려진 제약 (회피 필요)

수정 PRD(`docs/prds/event-suppression-hardening-prd.md`)는 작성됐으나 **아직 반영 전**이다.
GIS는 아래를 회피해서 구현할 것.

### 5-A. `PATCH` 는 device/group 대상 창에서 **500** (★최중요)

`target_type` 이 `device` 또는 `group` 인 스케줄은 **어떤 PATCH 도 500**이 난다
(이름만 변경·창 시간만 연장 포함). `target_type=all` 만 정상.

| PATCH 내용 | 결과 |
|---|---|
| 이름만 변경 (device 창) | **500** |
| 창 시간 연장 (device 창) | **500** |
| 대상 추가 `[A] → [A,B]` | **500** |
| 대상 완전 교체 `[A] → [B]`(겹침 0) | 200 |
| `all` 창의 임의 변경 | 200 |

**GIS 회피**: 수정 UI는 당분간 **"취소 후 새로 생성"** 흐름으로 구현하거나, 편집 버튼을
`target_type=all` 창에만 노출한다. (서버 수정 후 안내 예정)

### 5-B. 겹치는 창을 만들면 하나만 취소해도 억제가 계속된다

동일 장비·동일 시간대에 **중복 창을 무제한 생성**할 수 있고, 서버는 억제 시
**매치된 창 중 1건만** `schedule_id` 로 알려준다.

**GIS 회피**: 취소 후 **반드시 `GET /active` 를 재조회**해 그 장비를 덮는 창이 남아 있는지 확인하고,
남아 있으면 배너를 유지한다. 생성 폼에서는 "같은 대상에 진행 중인 창이 이미 있습니다" 사전 경고 권장.

### 5-C. `?device_id=` 필터로는 `group`/`all` 창이 안 잡힌다

`GET ?device_id=1352` 는 **`target_device_ids` 배열 직접 매치만** 한다.
그 장비를 실제로 억제 중인 **그룹 창·전체 창은 결과에 포함되지 않는다**.

**GIS 회피**: "이 장비가 지금 억제 중인가?"는 필터가 아니라 **`GET /active` 전체를 받아
클라이언트에서 판정**한다 (§7 판정 규칙).

### 5-D. 기타

- **취소한 창은 되살릴 수 없다.** 취소된 창에 PATCH 하면 200이 오지만 **아무 효과가 없다**(`status`는 `cancelled` 유지). 재사용이 필요하면 새로 생성할 것.
- **창 길이 상한이 없다.** 오타로 1년짜리 전체 억제도 생성된다 → **폼에서 최대 기간(예: 30일) 검증 권장**.
- 억제 중에는 장애/복구 이벤트가 버려지므로 **장비 상태가 창 종료 후에도 이전 값으로 남을 수 있다**.

---

## 6. ★ 장비 ID 주의 — `devices.id` 를 보낼 것

`target_device_ids` 는 **`devices.id`**(내부 PK)다. 화면에 보이는 **`number_device`(장비 번호)가 아니다.**

```
제어기1  →  id = 1351,  number_device = 1
제어기2  →  id = 1352,  number_device = 2
```

**실제 발생한 사고(2026-08-03)**: 운영자가 "제어기2"를 선택했는데 서버에는
`target_device_ids: [1351]`(= 제어기1)이 전달되어, 억제 창이 도는 동안 **제어기2 장애 이벤트가
계속 올라왔다**. 서버는 정상 동작했으나 운영자는 "억제가 안 먹는다"고 판단했다.

**GIS 확인 요청**:
1. 장비 선택 UI가 `devices.id` 를 전송하는지 (인덱스·`number_device` 혼동 여부)
2. 컨트롤러/센서 목록 API의 `id` 필드를 그대로 쓰는지

억제 창 생성 후 응답의 `target_device_ids` 를 **장비명으로 되풀이 표시**해 운영자가 대상을 육안
확인할 수 있게 하는 것을 강력 권장한다.

---

## 7. 활성 억제 배너 (필수 안전장치)

정비 중에는 **일부 이벤트가 억제 중임을 운영자가 항상 인지**해야 한다(억제 사실이 숨겨지면 실제 장애를 놓친다).

- `GET /api/event-suppression-schedules/active` 를 **30~60초 폴링**(서버 푸시 없음)
- 활성 창 ≥1건이면 배너:
  `⚠ 이벤트 억제 중: {name} — {대상 요약} / {event_scope} / ~{window_end}`
- 대상 요약: `device`→장비명 나열, `group`→그룹명 나열, `all`→"전체({target_side})"
- 배너 클릭 → 관리 UI 해당 창으로 이동
- **여러 창이 동시에 활성일 수 있다** — 건수를 함께 표시할 것

### 특정 장비가 억제 중인지 클라이언트 판정 규칙

`GET /active` 결과 각 창에 대해:

```
매치 =
  (target_type == "device" && 장비.id ∈ target_device_ids)
  || (target_type == "group" && (장비의 device_groups[] ∩ target_group_ids) != ∅ && side_match)
  || (target_type == "all"   && side_match)

side_match =
  target_side == "both"
  || (장비 side == target_side)          // sensor/controller=detection, camera=surveillance
                                          // speaker/lamp/enclosure 는 both 일 때만

그리고
  event_scope == "all" || event_scope == 이벤트 종류
```

---

## 8. 삭제 2종 — 반드시 구분할 것

| | `DELETE /{id}` | `POST /bulk-delete` |
|---|---|---|
| 성격 | **취소**(soft-cancel) | **하드삭제**(물리 제거) |
| 결과 | `status=cancelled`, 목록에 **남음** | 행 + 대상 매핑 완전 제거, **복구 불가** |
| 억제 중단 | ✅ 즉시 | (이미 terminal 인 것만 대상) |
| 대상 제한 | 없음 | **취소·종료(`cancelled`/`expired`)만** |
| 용도 | 정비 조기 종료 / 잘못 만든 창 중단 | **목록 정리** |
| 멱등 | 재호출 시 200 (이미 취소면 그대로) | 없는 id 는 `not_found_ids` 로 보고 |

### 8.1 취소 (진행 중인 억제 중단)

```
DELETE /api/event-suppression-schedules/12
→ 200, data.status = "cancelled", data.revoked_at 세팅
```

취소 직후 **`GET /active` 를 재조회**해 배너를 갱신할 것(§5-B).

### 8.2 일괄 하드삭제 (목록 정리)

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

| 필드 | UI 처리 |
|---|---|
| `deleted_ids` | 목록에서 제거 |
| `skipped_ids` | **"진행 중/예정이라 삭제할 수 없습니다. 먼저 취소하세요."** 안내 |
| `not_found_ids` | 이미 지워진 항목 — 조용히 목록 갱신 |

- `ids` 는 **1~500건**, 중복은 서버가 제거. 빈 배열은 **422**.
- 활성·예정 창은 **절대 삭제되지 않는다**(오삭제 방지). 지우려면 `DELETE /{id}` 로 먼저 취소.
- **권장 UI**: 목록에서 `status ∈ {cancelled, expired}` 인 행에만 체크박스 노출 + "선택 삭제" /
  "종료·취소 항목 모두 정리" 버튼. 하드삭제는 복구 불가이므로 **확인 다이얼로그 필수**.

---

## 9. 억제된 이벤트의 서버 응답 (참고)

이벤트 POST 주체(PidsProxy/AiAnalysis)가 받는 응답. GIS가 직접 받지는 않지만 동작 이해용.

```json
HTTP/1.1 202 Accepted
{ "success": true, "suppressed": true,
  "message": "Event (detection) suppressed by active maintenance window",
  "schedule_id": 12 }
```

**서버 억제 = DB 저장 차단**이다. 억제된 이벤트는 저장·통계·보고서·장비 상태 전환에서 제외된다.
단 **PidsProxy/AiAnalysis 가 직접 쏘는 실시간 NATS 방송은 막지 않는다**(§10).

---

## 10. [Phase 2] 라이브 알람 필터 — 정책 결정 후

서버 억제(Phase 1)는 저장만 막고, Proxy/AiAnalysis의 **라이브 방송은 그대로 GIS에 도달**한다.
따라서 정비 중 장비의 이벤트가 상황도에 **알람으로 뜬다**. GIS가 클라이언트-측에서 완화할 수 있다.

1. `GET /active` 캐시(§7과 공유)
2. `all.event.*` 수신 시 §7 판정 규칙으로 매치 확인. 그룹 멤버십은 이벤트 body 의
   `device.device_groups[]` 로 로컬 판정
3. 매치 시: 알람 팝업/사운드 억제 + 상황도 아이콘 **딤 / 정비 아이콘** 표시
4. **완전 숨김보다 "정비 중" 시각화 권장** — 은폐 방지

> **주의**: 탐지 이벤트 필터는 실제 침입을 가릴 수 있다. "숨김"이 아니라 **"정비 중 표식 + 알람 톤
> 완화"** 로 구현하고, 억제된 이벤트 수를 별도 카운트/로그로 남길 것.

---

## 11. 체크리스트 (GIS 팀)

**계약 갱신 (C-1~C-4)**
- [ ] `target_device_id` → **`target_device_ids: int[]`**, `target_group_id` → **`target_group_ids: int[]`** 전환
- [ ] 장비/그룹 **다중 선택** UI
- [ ] `bulk-delete` 연동 (서버 재배포 후)

**정확성**
- [ ] 시간은 **offset 포함**(`+09:00`) 전송 — 또는 생성 후 재조회 (§4)
- [ ] 장비 선택이 **`devices.id`** 를 보내는지 확인 (§6) ← **최우선 확인**
- [ ] 상태 배지는 **`status`** 사용, `is_active` **미사용** (§2)
- [ ] 생성 후 응답의 `target_device_ids` 를 장비명으로 되풀이 표시

**회피 (서버 수정 전)**
- [ ] device/group 창은 **PATCH 대신 취소+재생성** (§5-A)
- [ ] 취소 후 **`GET /active` 재확인** — 겹친 창 잔존 여부 (§5-B)
- [ ] "이 장비 억제 중?" 판정은 `?device_id=` 필터 아닌 **`/active` + 로컬 판정** (§5-C)
- [ ] 창 최대 기간(예: 30일) 폼 검증 (§5-D)

**안전**
- [ ] 활성 억제 배너 상시 표시 + 다중 창 건수 (§7)
- [ ] 하드삭제 확인 다이얼로그 + `skipped_ids` 안내 (§8.2)
- [ ] 권한별 버튼 제어 (events:view/edit/delete)
- [ ] (Phase 2, 정책 확정 시) 라이브 알람 딤 + 억제 카운트 (§10)

---

## 12. 문의

- 서버 마스터 명세: `GOP_Restful_Api_연동설계.md` §6.8 (v6.3.2)
- 공통 계약·범위 경계: [README.md](README.md)
- 서버 결함 수정 계획: `docs/prds/event-suppression-hardening-prd.md`
- 담당: 이기호 차장
