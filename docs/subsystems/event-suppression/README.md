# 이벤트 수신 억제(정비 창) — 서브시스템 연동 안내 (Overview)

- **작성일**: 2026-07-31
- **서버 기능**: `event-suppression-schedule` (DBApi, release/v6.3, 태그 `v6.3-event_suppression`)
- **연관 PRD**: `docs/prds/event-suppression-schedule-prd.md` v1.1
- **대상 서브시스템**: **Proxy(PidsProxy)**, **GIS(관제/Central UI)**, **VMS**, AiAnalysis, NVR, db_monitor

---

## 0. 한 줄 요약

공사·설치·장애수리·AS 기간에 **대상(장비/그룹/전체) × 이벤트유형(연결/탐지/장애/전체) × 시간창**을
지정해 이벤트 수신을 억제하는 "정비 창" 기능이 DBApi 서버에 신설됐다. **각 서브시스템은 이 억제 창을
조회해 자기 역할에 맞게 이벤트 발행/알람/녹화를 억제해야 완전한 "수신 차단"이 완성된다.**

---

## 1. ★ 반드시 이해할 범위 경계 (Phase 1 vs Phase 2)

DBApi 서버는 브로커 토폴로지상 **발행 전용(publish-only)** 이라, 장비 이벤트는 서버로 NATS 구독으로
들어오지 않고 **HTTP POST로만** 유입된다. 따라서 서버 억제(Phase 1, 이미 배포)는:

| 서버가 막는 것 (Phase 1, 완료) | 서버가 못 막는 것 (Phase 2, 각 서브시스템 몫) |
|---|---|
| 이벤트 **DB 저장**(레코드 미생성) | PidsProxy/AiAnalysis가 쏘는 **실시간 NATS 방송** |
| 이벤트 로그·통계·보고서 등 DB 파생 | 관제/VMS/NVR의 **실시간 알람·녹화·PTZ 반응** |
| 장비 상태 자동전환(탐지→활성/장애→ERROR) | — |

→ **완전한 시스템 차원의 억제**를 위해 각 서브시스템은 활성 억제 창을 조회(`GET /active`)해
자신의 라이브 반응을 억제해야 한다. 이 문서 세트가 그 요구사항을 서브시스템별로 정의한다.

---

## 2. 공통 API 계약 (모든 서브시스템 공유)

### 2.1 활성 억제 창 조회 (핵심 훅)

```
GET /api/event-suppression-schedules/active
Authorization: Bearer <token>        # AUTH_MODE=token 시 events:view 필요
```

응답:
```json
{
  "success": true,
  "message": "활성 억제 창 조회 성공",
  "data": [
    {
      "id": 12,
      "name": "GOP 3구역 펜스 보수",
      "target_type": "group",           // device | group | all
      "target_device_ids": [],           // target_type=device 일 때 ≥1 (배열, v6.3 확장)
      "target_group_ids": [5, 6],        // target_type=group 일 때 ≥1 (배열, v6.3 확장)
      "target_side": "detection",        // detection | surveillance | both
      "event_scope": "all",              // connection | detection | malfunction | all
      "window_start": "2026-08-01T09:00:00+09:00",
      "window_end":   "2026-08-01T18:00:00+09:00",
      "status": "active",
      "is_active": true
    }
  ]
}
```

- 폴링 주기 권장: **30~60초 캐시**(창 경계 정밀도는 분 단위로 충분). 또는 서버가 향후 제공할 브로커
  신호 구독(Phase 2 확장 여지).
- 전체 목록/관리: `GET|POST|PATCH|DELETE /api/event-suppression-schedules` (§4 참조).

### 2.2 억제된 이벤트 POST 응답 (Proxy/AiAnalysis 필독)

장비 이벤트를 서버로 POST(`/api/events/detections|malfunctions|connections`)할 때, 해당 이벤트가
활성 억제 창에 걸리면 서버는 **201 대신 202**를 반환한다:

```json
HTTP/1.1 202 Accepted
{ "success": true, "suppressed": true,
  "message": "Event (detection) suppressed by active maintenance window",
  "schedule_id": 12 }
```

→ POST 클라이언트(Proxy/AiAnalysis)는 **202를 "성공(억제됨)"으로 처리**해야 한다(오류/재시도 금지).
저장은 되지 않으며 응답에 이벤트 id가 없다.

### 2.3 억제 판정 규칙 (서브시스템이 클라이언트-측 복제 시 동일 로직 사용)

한 장비 이벤트 `(device_id, category)` 가 활성 창 `W`에 억제되는 조건:

```
category ∈ {detection, malfunction, connection}                # action(조치보고)은 억제 대상 아님
AND (W.event_scope == 'all' OR W.event_scope == category)
AND scope_match:
      W.target_type == 'device' : device_id ∈ W.target_device_ids                      # 배열(v6.3 복수 대상)
      W.target_type == 'all'    : side_match(device_side, W.target_side)
      W.target_type == 'group'  : (groups(device_id) ∩ W.target_group_ids) ≠ ∅ AND side_match(...)

device_side = sensor|controller → 'detection'
              camera            → 'surveillance'
              speaker|lamp|enclosure → 'auxiliary'
side_match(ds, ts) = (ts == 'both') OR (ds == ts)              # 보조 장비는 'both' 일 때만 매치
```

- 그룹 멤버십은 라이브 이벤트 body의 `device.device_groups[]`(브로커 v1.5 §6.1)로 로컬 판정 가능.
- 창 유효: `window_start <= now < window_end` AND `revoked_at == null`(=`status=='active'`). GET /active는
  이미 활성만 반환하므로 서브시스템은 status 재계산 없이 그대로 사용해도 된다.

---

## 3. 서브시스템별 영향 매트릭스

| 서브시스템 | 역할 | 억제 시 해야 할 일 | 문서 | 우선순위 |
|---|---|---|---|---|
| **Proxy(PidsProxy)** | 필드 센서 이벤트 발행자 + 서버 POST 주체 | ①202 응답 처리 ②(Phase2)활성 창 device+category 매치 시 NATS 발행 skip/mark | [Proxy.md](Proxy.md) | ★최상 |
| **GIS(관제)** | all.event.> 구독·상황도 알람 + 정비창 관리 UI | ①정비창 CRUD 화면 ②활성 배너 ③(Phase2)억제 장비 알람 필터 | [GIS.md](GIS.md) | ★최상 |
| **VMS** | 영상/RTSP·이벤트 트리거 녹화·PTZ | (Phase2)감시쪽 대상 창에 든 카메라의 이벤트 트리거 녹화/PTZ/팝업 억제 | [VMS.md](VMS.md) | 상 |
| AiAnalysis | AI 영상 탐지 발행자(all.event_ai.detect) | ①202 처리 ②(Phase2)활성 창 매치 시 AI 탐지 발행 skip | [AiAnalysis.md](AiAnalysis.md) | 상 |
| NVR | 녹화 관리 | (Phase2)감시쪽 대상 창 카메라의 이벤트 녹화 억제 | [NVR.md](NVR.md) | 중 |
| db_monitor | DBApi NATS 발행 브리지 | 참고(SYSTEM_EVENT 발행은 억제 무관, 정보성) | [db_monitor.md](db_monitor.md) | 낮 |

---

## 4. 관리 API 전체 (관리 UI = 주로 GIS)

| Method | Path | 인가 | 설명 |
|---|---|---|---|
| POST | `/api/event-suppression-schedules` | events:edit | 정비 창 생성 |
| GET | `/api/event-suppression-schedules` | events:view | 목록(page/limit + status/target_type/device_id/group_id 필터) |
| GET | `/api/event-suppression-schedules/{id}` | events:view | 단건 |
| PATCH | `/api/event-suppression-schedules/{id}` | events:edit | 변경 |
| DELETE | `/api/event-suppression-schedules/{id}` | events:delete | 삭제(soft-cancel) |
| POST | `/api/event-suppression-schedules/bulk-delete` | events:delete | **취소·종료 스케줄 일괄 하드삭제**(목록 정리, v6.3.2) |
| GET | `/api/event-suppression-schedules/active` | events:view | 활성 창(배너·서브시스템 조회 훅) |

생성 요청 예:
```json
POST /api/event-suppression-schedules
{
  "name": "GOP 3구역 펜스 보수",
  "target_type": "group",           // device: target_device_ids≥1 / group: target_group_ids≥1 / all
  "target_group_ids": [5, 6],
  "target_side": "detection",        // 기본 both (group·all 에만 적용)
  "event_scope": "all",              // connection | detection | malfunction | all
  "window_start": "2026-08-01T09:00:00+09:00",
  "window_end":   "2026-08-01T18:00:00+09:00"
}
```

- RBAC: 쓰기 events:edit/delete, 조회 events:view, `role=ADMIN`만 무조건 bypass(AUTH_MODE=token 시 강제).
- `window_end` 필수(자동 만료 — 무기한 침묵 금지). `revoked_at` 로 soft-cancel(물리삭제 없음).

---

## 5. 결정 필요 (PM/서브시스템 팀 합의)

- **D1(범위 확정)**: 라이브 경로 억제(Phase 2)를 각 서브시스템에 요구할지. Yes면 아래 문서의 Phase 2
  항목을 각 팀 백로그로. No(서버 저장 억제만)면 GIS 관리 UI + 배너까지만.
- **폴링 vs 신호**: 현재 `GET /active` 폴링. 다수 서브시스템이 실시간성을 요구하면 서버가 브로커
  `SYNC_SUPPRESSION`(마스터데이터 알림) 또는 runtime 신호를 추가 발행하는 Phase 2-b 검토.
