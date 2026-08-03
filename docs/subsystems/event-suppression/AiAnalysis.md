# AiAnalysis — 이벤트 억제(정비 창) 연동 안내

- **작성일**: 2026-07-31 · **우선순위**: 상
- **상위 문서**: [README.md](README.md)
- **AiAnalysis 역할**: AI 영상 탐지 **발행자**(`all.event_ai.detect`, `vms.event_ai.detect`). Proxy와 함께
  탐지 이벤트의 원천이며, DBApi로 탐지 이벤트를 POST할 수 있다.

---

## 바꿔야 할 것

| # | 변경 | Phase | 필수도 |
|---|---|---|---|
| A-1 | 이벤트 POST 시 **202 Accepted(suppressed) 처리** (서버로 탐지 POST하는 경우) | Phase 1 | ★필수(해당 시) |
| A-2 | (라이브 차단 요구 시) 활성 창 매치 AI 탐지 **발행 skip/mark** | Phase 2 | 정책(D1) |

**A-1**: DBApi로 detection 이벤트를 POST한다면, 억제 시 서버가 **202 + `{suppressed:true}`** 반환.
201만 성공으로 보던 코드에 202 성공(억제됨) 분기 추가, 재시도 금지(자세히는 [Proxy.md](Proxy.md) §1 동일).

**A-2**: 서버 저장 억제는 라이브 `event_ai.detect` 방송을 막지 않는다. 정비 중 AI 오탐(작업자/장비 오인)을
원천 차단하려면 AiAnalysis가 `GET /active` 폴링 후 [README §2.3 규칙]으로 매치되는 device+category의
AI 탐지 발행을 skip/mark. AI 탐지는 대개 **감시쪽(카메라)** 이므로 `target_side ∈ {surveillance, both}`
또는 카메라 device/그룹 창을 반영. 창 종료 즉시 복귀, 억제 건수 로깅.

---

## [A-3] ★ NATS 알림 `SYNC_EVENT_SUPPRESSION` — 신규 (v6.3.2)

정비 창 변경·**창 시작/종료**를 서버가 NATS 로 알린다. 폴링을 기다리지 않고 즉시 반영 가능.

```
Subject : sensorway.{부대ID}.all.sync.event-suppression
body    : { "action": "CREATED|UPDATED|DELETED", "resource_id": 12, "status": "active" }
```

- **구독 추가 불필요** — AiAnalysis 는 이미 `sensorway.unit001.all.sync.*` 구독.
- **필수**: `EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가 + **미지 cmd graceful skip** 방어
  (빠뜨리면 SYNC 수신 루프 전체가 죽어 장비 동기화까지 멈춤).
- **처리**: action 분기 없이 **무조건 `GET /active` 재조회**.
- **취소(`DELETE /{id}`)는 soft-cancel 이라 `action=UPDATED` + `status=cancelled`** 로 온다.
  `DELETED` 는 하드삭제(`bulk-delete`)뿐.

### ★ 억제 해제는 신호에 의존 금지 — AiAnalysis 도 탐지 원천이라 위험

NATS 는 at-most-once. **창 종료 신호 유실 = AI 탐지가 영원히 안 풀림 = 실제 침입 미탐지**(금지).
창 시작 신호 유실은 "오탐이 좀 올라옴"(허용)이라 비대칭이 크다.

1. **`expired` 로 해제하지 말고** 캐시한 `window_end` **로컬 타이머**로 스스로 푼다 ← 1차 권위
2. `GET /active` **30~60초 폴링 유지**(권위), SYNC 는 가속 신호(비권위)
3. 캐시 TTL(주기×3) 초과 시 자동으로 "억제 없음" 수렴(fail-open)

**통지 지연**: 정상 ≤5초 / 백스톱 ≤5분. 상세: 브로커 명세 v1.6 **§9.12**.

---

- [ ] (A-1) POST 202 분기 추가(서버 POST 시)
- [ ] (A-2, D1=Yes) 활성 창 폴링 + AI 탐지 발행 skip/mark(감시쪽 창)
- [ ] **(A-3) `EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가** (구독 추가 불필요)
- [ ] **(A-3) 미지 cmd graceful skip 방어 + 회귀 테스트**
- [ ] (A-3) 수신 시 `GET /active` 재조회
- [ ] **(A-3) `expired` 신호로 해제 금지** — 로컬 `window_end` 타이머 권위 + 폴링 유지 + 캐시 TTL
