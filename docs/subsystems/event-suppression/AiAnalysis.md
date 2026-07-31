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

- [ ] (A-1) POST 202 분기 추가(서버 POST 시)
- [ ] (A-2, D1=Yes) 활성 창 폴링 + AI 탐지 발행 skip/mark(감시쪽 창)
