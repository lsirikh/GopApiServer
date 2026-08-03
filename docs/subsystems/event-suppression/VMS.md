# VMS — 이벤트 억제(정비 창) 연동 안내

- **작성일**: 2026-07-31 · **우선순위**: 상
- **상위 문서**: [README.md](README.md) (공통 계약·범위 경계)
- **VMS 역할**: 영상/RTSP 스트리밍, **이벤트 트리거 반응**(자동 녹화 시작, 연동 카메라 PTZ 프리셋 이동,
  팝업/타일 강조). 감시쪽(camera) 중심.

---

## 0. 두괄식 — VMS가 바꿔야 할 것

| # | 변경 | Phase | 필수도 |
|---|---|---|---|
| V-1 | (라이브 차단 요구 시) 억제 창에 든 **카메라의 이벤트 트리거 녹화/PTZ/팝업 억제** | Phase 2 | 정책(D1) |
| V-2 | 기존 `is_restricted_zone`(감시금지구역) 억제 로직의 **시간창 버전** 확장 재사용 | Phase 2 | 설계 참조 |

> VMS는 서버로 장비 이벤트를 POST하는 주체가 아니므로 **Phase 1 필수 변경은 없다**(202 처리 불필요).
> 완전한 정비-중 무반응을 원할 때 Phase 2에서 라이브 억제를 적용한다.

---

## 1. [V-1] 이벤트 트리거 반응 억제 — Phase 2 (정책 D1 결정 후)

**배경**: 정비 중 카메라 앞 작업(사다리·인원 이동 등)이나, 억제된 센서 탐지에 연동된 카메라 자동
반응(녹화 시작·PTZ 회전·타일 팝업)이 **불필요하게 발동**한다. 서버 억제(Phase 1)는 이 라이브 반응을
막지 못한다.

**권장 설계**:
1. `GET /api/event-suppression-schedules/active` 를 **30~60초 폴링** + 캐시.
2. **감시쪽 관련 창만** 반영: `target_side ∈ {surveillance, both}` 인 창.
   - target_type=device 이고 그 device가 카메라이면 해당 카메라.
   - target_type=group 이면 그룹의 카메라 멤버.
   - target_type=all 이고 side가 surveillance/both 이면 전체 카메라.
3. 억제 대상 카메라에 대해, 이벤트 트리거로 발동하는 다음 동작을 **일시 중지**:
   - 이벤트 기반 **자동 녹화 시작** 스킵(수동/상시 녹화는 유지 — 정책 선택).
   - 연동 **PTZ 프리셋 이동** 스킵.
   - **팝업/타일 강조** 스킵(또는 "정비 중" 오버레이).
4. `event_scope` 도 고려: 예) `event_scope=detection` 창은 탐지 연동 반응만 억제. `all`은 전부.
5. 창 종료 즉시 정상 반응 복귀.

---

## 2. [V-2] 감시금지구역(is_restricted_zone) 패턴 재사용 — 설계 참조

기존에 CameraPreset `is_restricted_zone`(감시금지구역)이 **공간 기반**으로 VMS=RTSP/녹화 차단,
db_monitor=이벤트 발행 차단, AiAnalysis=분석 억제를 팬아웃한다(브로커 v1.5 PTZ_STATUS). 본 정비 창은
그 **시간 기반 버전**이다.

→ VMS가 이미 가진 `is_restricted_zone` 억제 파이프라인에 **"활성 정비 창에 걸린 카메라" 조건을 OR로
추가**하면 최소 변경으로 구현 가능. 판정 소스만 (공간=PTZ 위치) → (시간=활성 창)으로 확장.

---

## 3. [V-3] ★ NATS 알림 `SYNC_EVENT_SUPPRESSION` — 신규 (v6.3.2)

정비 창 변경·**창 시작/종료**를 서버가 NATS 로 알린다. 30~60초 폴링을 기다리지 않고 즉시 반영 가능.

```
Subject : sensorway.{부대ID}.all.sync.event-suppression
body    : { "action": "CREATED|UPDATED|DELETED", "resource_id": 12, "status": "active" }
```

- **구독 추가 불필요** — VMS 는 이미 `sensorway.unit001.all.sync.*` 구독.
- **필수**: `EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가 + **미지 cmd graceful skip** 방어
  (빠뜨리면 SYNC 수신 루프가 죽어 장비/프리셋 동기화까지 멈춤).
- **처리**: action 분기 없이 **무조건 `GET /active` 재조회** → §1 의 감시쪽 카메라 집합 재산출.
- **취소(`DELETE /{id}`)는 soft-cancel 이라 `action=UPDATED` + `status=cancelled`**. `DELETED` 는 하드삭제뿐.
- V-2(`is_restricted_zone` 파이프라인 재사용)를 채택했다면, 이 알림이 **그 파이프라인의 갱신 트리거**가 된다
  (공간 신호=PTZ_STATUS ↔ 시간 신호=SYNC_EVENT_SUPPRESSION, 같은 자리에 OR 로 붙는다).

### ★ 억제 해제는 신호에 의존 금지

NATS 는 at-most-once. **창 종료 신호 유실 = 이벤트 트리거 녹화/팝업이 영원히 안 돌아옴**(금지).

1. **`expired` 로 해제하지 말고** 캐시한 `window_end` **로컬 타이머**로 스스로 푼다 ← 1차 권위
2. `GET /active` **폴링 유지**(권위), SYNC 는 가속 신호(비권위)
3. 캐시 TTL(주기×3) 초과 시 "억제 없음" 자동 수렴(fail-open) — 녹화가 조용히 멈춰 있는 상태 방지

**통지 지연**: 정상 ≤5초 / 백스톱 ≤5분. 상세: 브로커 명세 v1.6 **§9.12**.

---

## 4. 체크리스트 (VMS 팀)

- [ ] (V-1, D1=Yes) 활성 창 폴링 + 감시쪽(surveillance/both) 창 카메라 산출
- [ ] 억제 대상 카메라의 이벤트 트리거 녹화/PTZ/팝업 억제(상시 녹화 유지 여부 정책 확정)
- [ ] (V-2) is_restricted_zone 억제 파이프라인에 시간창 조건 OR 추가(재사용)
- [ ] **(V-3) `EnumGopCommand` 에 `SYNC_EVENT_SUPPRESSION` 추가** (구독 추가 불필요)
- [ ] **(V-3) 미지 cmd graceful skip 방어 + 회귀 테스트**
- [ ] (V-3) 수신 시 `GET /active` 재조회 → 감시쪽 카메라 집합 재산출
- [ ] **(V-3) `expired` 신호로 해제 금지** — 로컬 `window_end` 타이머 권위 + 폴링 유지 + 캐시 TTL
- [ ] event_scope·창 종료 복귀 검증
