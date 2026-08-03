# NVR — 이벤트 억제(정비 창) 연동 안내

- **작성일**: 2026-07-31 · **우선순위**: 중
- **상위 문서**: [README.md](README.md)
- **NVR 역할**: 카메라 녹화 관리(이벤트 트리거 녹화 포함).

---

## 바꿔야 할 것

| # | 변경 | Phase | 필수도 |
|---|---|---|---|
| N-1 | (라이브 차단 요구 시) 억제 창에 든 카메라의 **이벤트 트리거 녹화 억제** | Phase 2 | 정책(D1) |

> NVR은 서버로 장비 이벤트를 POST하지 않으므로 **Phase 1 필수 변경 없음**.

**N-1**: 정비 중 카메라 앞 작업이나 억제된 센서 탐지에 연동된 자동 녹화가 불필요하게 발생한다. 완전
차단이 필요하면 [VMS.md](VMS.md) §1과 동일 원리로:
- `GET /api/event-suppression-schedules/active` 폴링(30~60초) + 캐시.
- **감시쪽 관련 창만**(`target_side ∈ {surveillance, both}`) 반영, 대상 카메라(device/group/all) 산출.
- 억제 대상 카메라의 **이벤트 트리거 녹화 시작만** 스킵(상시/스케줄 녹화는 유지 권장 — 증적 보존).
- `event_scope` 반영(예: detection 창은 탐지 연동 녹화만). 창 종료 즉시 복귀.

**정책 주의**: 정비 중이라도 상시 녹화는 유지하는 편이 증적/안전상 유리. "이벤트 트리거 추가 녹화"만
억제할지, 전부 억제할지 NVR/운영팀이 확정.

---

## [N-2] ★ NATS 알림 `SYNC_EVENT_SUPPRESSION` — 신규 (v6.3.2)

정비 창 변경·**창 시작/종료**를 서버가 NATS 로 알린다. 폴링을 기다리지 않고 즉시 반영 가능.

```
Subject : sensorway.{부대ID}.all.sync.event-suppression
body    : { "action": "CREATED|UPDATED|DELETED", "resource_id": 12, "status": "active" }
```

- **구독 추가 불필요** — NVRManager 는 이미 `sensorway.unit001.all.sync.*` 구독.
- **필수**: `EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가 + **미지 cmd graceful skip** 방어
  (빠뜨리면 SYNC 수신 루프가 죽어 카메라/프리셋 동기화까지 멈춤).
- **처리**: action 분기 없이 **무조건 `GET /active` 재조회** → 대상 카메라 집합 재산출.
- **취소(`DELETE /{id}`)는 soft-cancel 이라 `action=UPDATED` + `status=cancelled`**. `DELETED` 는 하드삭제뿐.

### ★ 억제 해제는 신호에 의존 금지 — 증적 소실 위험

NATS 는 at-most-once. **창 종료 신호 유실 = 이벤트 트리거 녹화가 영원히 안 돌아옴 = 증적 소실**(금지).
상시 녹화를 유지하는 정책이라면 피해가 줄지만, 이벤트 녹화만 조용히 빠지는 상태는 알아채기 어렵다.

1. **`expired` 로 해제하지 말고** 캐시한 `window_end` **로컬 타이머**로 스스로 푼다 ← 1차 권위
2. `GET /active` **폴링 유지**(권위), SYNC 는 가속 신호(비권위)
3. 캐시 TTL(주기×3) 초과 시 "억제 없음" 자동 수렴(fail-open)

**통지 지연**: 정상 ≤5초 / 백스톱 ≤5분. 상세: 브로커 명세 v1.6 **§9.12**.

---

- [ ] (N-1, D1=Yes) 활성 창 폴링 + 감시쪽 창 카메라 이벤트 트리거 녹화 억제(상시녹화 유지 정책 확정)
- [ ] **(N-2) `EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가** (구독 추가 불필요)
- [ ] **(N-2) 미지 cmd graceful skip 방어 + 회귀 테스트**
- [ ] (N-2) 수신 시 `GET /active` 재조회 → 대상 카메라 집합 재산출
- [ ] **(N-2) `expired` 신호로 해제 금지** — 로컬 `window_end` 타이머 권위 + 폴링 유지 + 캐시 TTL
