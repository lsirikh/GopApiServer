# db_monitor — 이벤트 억제(정비 창) 연동 안내

- **작성일**: 2026-07-31 · **우선순위**: 낮음(참고)
- **상위 문서**: [README.md](README.md)
- **db_monitor 역할**: DBApi의 **NATS 발행 브리지**(Postgres LISTEN → NATS). `SYNC_*`(마스터데이터 알림),
  `SYSTEM_EVENT`(Full-DTO), `ENCLOSURE_METRICS`(주기 push)를 발행. **장비 탐지/장애 이벤트는 발행하지
  않는다**(그건 Proxy/AiAnalysis 소관).

---

## 바꿔야 할 것

| # | 변경 | Phase | 필수도 |
|---|---|---|---|
| D-1 | **필수 변경 없음** — 억제는 장비 이벤트(detection/malfunction/connection) 대상이고 db_monitor는 그걸 발행 안 함 | — | — |
| D-2 | (Phase 2-b, 선택) 억제 창 CRUD 변경을 `SYNC_SUPPRESSION` 마스터데이터 메시지로 **실시간 팬아웃** | Phase 2-b | 성능 최적화 |

**D-1**: 정비 창 억제는 이벤트 저장/수신을 대상으로 하며, db_monitor가 발행하는 SYNC/SYSTEM_EVENT/
ENCLOSURE_METRICS는 정보성이라 억제 대상이 아니다. **현재 db_monitor는 무변경**.

**D-2 (선택, Phase 2-b)**: 각 서브시스템이 `GET /active`를 폴링하는 대신, 억제 창 생성/수정/삭제 시
db_monitor가 `SYNC_SUPPRESSION`(신규 SYNC_* 메시지)을 발행해 GIS/VMS/NVR/Proxy가 **즉시** 반영하게
할 수 있다. 이는 브로커 스펙 v1.5 개정(§9 SYNC_* 계열 + 메시지 카운트 + 부록)이 필요하며, 폴링으로도
충분하면 도입하지 않는다.
- 구현 시: `event_suppression_schedules` INSERT/UPDATE/DELETE 트리거 → `gop_sync` 채널 → NATS
  `all.sync.suppression`(가칭). Grant/preset SYNC_* 패턴과 동일.

- [ ] (D-1) 무변경 확인
- [ ] (D-2, Phase 2-b 채택 시) SYNC_SUPPRESSION 발행 + 브로커 스펙 개정
