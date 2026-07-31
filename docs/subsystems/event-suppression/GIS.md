# GIS(관제 / Central UI) — 이벤트 억제(정비 창) 연동 안내

- **작성일**: 2026-07-31 · **우선순위**: ★최상
- **상위 문서**: [README.md](README.md) (공통 계약·범위 경계)
- **GIS 역할**: `all.event.>` 구독 → 상황도(GMaps) 알람 표시. 운영자 조작 창구. **정비 창 관리 UI의
  1차 후보**(관리자가 억제 스케줄을 만들고 관리).

---

## 0. 두괄식 — GIS가 바꿔야 할 것

| # | 변경 | Phase | 필수도 |
|---|---|---|---|
| G-1 | **정비 창 관리 UI**(생성/목록/수정/삭제) — 6개 엔드포인트 연동 | **Phase 1 (즉시)** | ★필수 |
| G-2 | **활성 억제 배너** — 정비 중임을 상시 표시(`GET /active`) | Phase 1 | ★권장 |
| G-3 | (라이브 차단 요구 시) 억제 대상 장비의 **알람 팝업 필터/딤 처리** | Phase 2 | 정책(D1) |

---

## 1. [G-1] 정비 창 관리 UI — Phase 1 (필수)

관리자가 정비/공사/AS 전에 억제 창을 등록·관리하는 화면. 억제 판정 권위는 서버이므로 GIS는 순수
CRUD 클라이언트다.

**입력 폼 필드**:
| 필드 | UI | 값 |
|---|---|---|
| name | 텍스트(필수) | 작업명/사유 (예: "GOP 3구역 펜스 보수") |
| target_type | 라디오/셀렉트 | 장비(device) / 그룹(group) / 전체(all) |
| target_device_id | 장비 선택(device 시) | devices.id |
| target_group_id | 그룹 선택(group 시) | device_groups.id |
| target_side | 셀렉트(group·all 시) | 감지(detection) / 감시(surveillance) / 전체(both, 기본) |
| event_scope | 셀렉트(필수) | 연결(connection) / 탐지(detection) / 장애(malfunction) / 전체(all) |
| window_start, window_end | 날짜·시간(필수) | KST(+09:00). end > start, end 필수 |

**API 매핑**:
```
생성  POST   /api/event-suppression-schedules          (events:edit)
목록  GET    /api/event-suppression-schedules?page=&limit=&status=&target_type=&device_id=&group_id=  (events:view)
단건  GET    /api/event-suppression-schedules/{id}      (events:view)
수정  PATCH  /api/event-suppression-schedules/{id}      (events:edit)
삭제  DELETE /api/event-suppression-schedules/{id}      (events:delete, soft-cancel)
```

- 목록 status 필터: `pending`(예정) / `active`(진행중) / `expired`(종료) / `cancelled`(취소).
- 삭제는 soft-cancel(`revoked_at` 세팅) — 이력 보존, 물리삭제 아님.
- **RBAC**: 화면 노출/버튼 활성은 사용자 권한(events:view/edit/delete)에 맞춰 제어. `role=ADMIN`은 전권.
  권한 없는 사용자는 서버가 403.
- 응답 파생 `status` 필드로 상태 배지 표시(진행중/예정/종료/취소).

---

## 2. [G-2] 활성 억제 배너 — Phase 1 (권장, 안전)

정비 중에는 **일부 이벤트가 억제 중임을 운영자가 항상 인지**해야 한다(억제 사실이 숨겨지면 실제
장애를 놓칠 위험). 상황도 상단에 상시 배너를 둔다.

- `GET /api/event-suppression-schedules/active` 를 **30~60초 폴링**.
- 활성 창이 1건 이상이면 배너: "⚠ 이벤트 억제 중: {name} — {대상 요약} / {event_scope} / ~{window_end}".
- 배너 클릭 → 관리 UI(G-1) 해당 창으로 이동.
- 대상 요약: target_type=device→장비명, group→그룹명, all→"전체({target_side})".

---

## 3. [G-3] 억제 대상 알람 필터 — Phase 2 (정책 D1 결정 후)

**배경**: 서버 억제(Phase 1)는 저장만 막고, Proxy/AiAnalysis의 **라이브 방송은 그대로** GIS에 도달한다.
Phase 2에서 발행 주체가 억제되기 전까지는, 정비 중 장비의 이벤트가 상황도에 **알람으로 뜬다**. 이를
GIS가 클라이언트-측에서 필터/딤 처리해 오탐을 줄일 수 있다.

**권장**:
1. `GET /active` 캐시(G-2와 공유).
2. `all.event.*` 수신 시 [README §2.3 규칙]으로 이벤트가 활성 창에 걸리는지 판정. 그룹 멤버십은 이벤트
   body의 `device.device_groups[]`로 로컬 판정.
3. 매치 시: 알람 팝업/사운드 억제 + 상황도 아이콘 **딤/정비 아이콘** 표시(완전 숨김보다 "정비 중" 시각화
   권장 — 은폐 방지).
4. **감지/감시 side** 반영: 이벤트 장비의 side(sensor/controller=detection, camera=surveillance)와
   창의 target_side 매치(README §2.3 side_match).

**주의**: 탐지 이벤트 필터는 실제 침입을 가릴 수 있으므로, "숨김"이 아니라 "정비 중 표식 + 알람 톤 완화"
를 권장하고, 억제된 이벤트 수를 별도 카운트/로그로 남긴다.

---

## 4. 체크리스트 (GIS 팀)

- [ ] (G-1) 정비 창 CRUD 화면 6엔드포인트 연동 + 권한별 UI 제어
- [ ] (G-1) 입력 검증: end>start, target_type별 필수 필드, event_scope 명시 선택
- [ ] (G-2) 활성 배너 폴링 + 대상 요약 표시
- [ ] (G-3, D1=Yes) 라이브 이벤트 억제 필터/딤 + side 매치 + 억제 카운트
- [ ] 억제 사실 은폐 방지(딤/표식 우선, 완전 숨김 지양)
