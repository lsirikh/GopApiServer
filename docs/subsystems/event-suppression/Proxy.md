# Proxy(PidsProxy) — 이벤트 억제(정비 창) 연동 안내

- **작성일**: 2026-07-31 · **우선순위**: ★최상
- **상위 문서**: [README.md](README.md) (공통 계약·범위 경계)
- **Proxy 역할**: 필드 센서(펜스/PIR/케이블 등)의 탐지·장애·연결 이벤트를 **발행**(`all.event.detect`,
  `all.event.malfunction`, `all.event.connection`)하고, 동시에 DBApi 서버로 **HTTP POST** 하는 주체.

---

## 0. 두괄식 — Proxy가 바꿔야 할 것

| # | 변경 | Phase | 필수도 |
|---|---|---|---|
| P-1 | 이벤트 POST 응답에서 **202 Accepted(suppressed) 처리** 추가 (201만 성공으로 보던 코드) | **Phase 1 (즉시)** | ★필수 |
| P-2 | 연결(connection) 이벤트 POST 시 **인증 토큰 첨부** 확인(token 모드) | Phase 1 | ★필수(회귀 방지) |
| P-3 | (라이브 차단 요구 시) 활성 억제 창 조회 → 매치 device+category 이벤트 **NATS 발행 skip/mark** | Phase 2 | 정책(D1) |

---

## 1. [P-1] 202 억제 응답 처리 — Phase 1 (즉시, 필수)

Proxy가 `POST /api/events/detections|malfunctions|connections` 로 이벤트를 저장할 때, 그 이벤트가
활성 억제 창에 걸리면 서버는 **201 대신 202**를 반환하고 **레코드를 만들지 않는다**:

```json
HTTP/1.1 202 Accepted
{ "success": true, "suppressed": true,
  "message": "Event (detection) suppressed by active maintenance window",
  "schedule_id": 12 }
```

**Proxy 조치**:
- 응답 코드 처리 분기에 **202를 "성공(억제됨)"** 으로 추가. 201/202 모두 정상 종료로 간주.
- **재시도·에러 로깅 금지**(202를 실패로 오인하면 무한 재시도/알람 발생).
- 202 응답에는 이벤트 `id`가 없다 → 이후 `id` 기반 후속 처리(PATCH 등) 대상에서 제외.
- 로깅은 정보성(`suppressed schedule_id=…`)으로만.

```csharp
// 예시 (개념)
var res = await httpClient.PostAsync(url, content);
if (res.StatusCode == HttpStatusCode.Created)      { /* 저장됨: id 사용 */ }
else if (res.StatusCode == HttpStatusCode.Accepted){ /* 억제됨: 정상 종료, 재시도 금지 */ }
else                                                { /* 실제 오류 처리 */ }
```

---

## 2. [P-2] connection POST 인증 정합 — Phase 1 (필수)

이번 업데이트로 `POST /api/events/connections` 에 라우트-레벨 인가(`events:edit`)가 **명시적으로** 추가됐다
(기존에도 중앙 매트릭스가 token 모드에서 이미 커버했으나, 데코레이터 정합으로 방어 심화). 

**Proxy 조치**: token 모드(운영) 배포에서 connection 이벤트 POST 시 **Bearer 토큰이 첨부되는지 확인**한다.
detection/malfunction POST와 동일한 인증 경로를 사용하면 된다(이미 그렇다면 무변경). 무토큰이면 401.

---

## 3. [P-3] 라이브 발행 억제 — Phase 2 (정책 D1 결정 후)

**배경**: 서버 억제(Phase 1)는 **저장**만 막는다. Proxy가 이미 `all.event.detect` 등으로 **직접 방송**한
라이브 이벤트는 GIS/VMS/NVR가 그대로 받는다. 정비 중 상황도 오탐/자동반응을 원천 차단하려면 **발행
주체인 Proxy가 억제 창을 인지**해 발행을 건너뛰거나 억제 플래그를 붙여야 한다.

**권장 설계**:
1. Proxy가 `GET /api/event-suppression-schedules/active` 를 **30~60초 주기 폴링** + 로컬 캐시.
2. 각 센서 이벤트 발행 직전, [README §2.3 억제 판정 규칙]로 `(device_id, category)`가 활성 창에 걸리는지
   판정. 그룹 멤버십은 Proxy가 보유한 장비-그룹 정보로 판정.
3. 매치 시 선택:
   - **(권장) skip**: `all.event.*` 발행을 하지 않음(완전 억제). 단 서버 POST는 그대로 보내도 서버가
     202로 억제하므로, "발행 skip + POST 생략" 또는 "발행 skip + POST 유지(202 수신)" 중 택1.
   - **mark**: 발행하되 body에 `suppressed:true`(+`suppression_schedule_id`)를 실어 소비자가 필터.
     → 이 경우 브로커 스펙(v1.5)에 필드 추가 협의 필요.
4. **감지/감시 side**: Proxy 소관은 감지쪽(sensor/controller). `target_side` 가 `surveillance` 인 창은
   Proxy 발행에 영향 없음(카메라 대상). `detection`/`both`만 반영.

**주의(안전)**: 탐지(detection) 발행 skip은 **실제 침입을 놓칠 수 있음**. 반드시 활성 창(관리자가 명시
설정)만 반영하고, 창 종료 즉시 정상 발행 복귀. 억제 발행 건수는 로깅.

---

## 4. 체크리스트 (Proxy 팀)

- [ ] (P-1) 이벤트 POST 응답 202 분기 추가, 재시도/에러 오인 제거
- [ ] (P-2) connection POST 토큰 첨부 확인(token 모드 401 회귀 방지)
- [ ] (P-3, D1=Yes) 활성 창 폴링 + 발행 skip/mark 로직 (감지쪽 detection/both 창만)
- [ ] 억제 발행/POST 건수 로깅(관측성)
- [ ] 창 종료 후 정상 발행 자동 복귀 검증
