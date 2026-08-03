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
| D-2 | ~~(선택) 억제 창 CRUD 변경을 `SYNC_SUPPRESSION` 으로 실시간 팬아웃~~ → **✅ 구현 완료 (2026-08-03, v6.3.2)** | — | 완료 |

**D-1**: 정비 창 억제는 이벤트 저장/수신을 대상으로 하며, db_monitor가 발행하는 SYNC/SYSTEM_EVENT/
ENCLOSURE_METRICS는 정보성이라 억제 대상이 아니다. **현재 db_monitor는 무변경**.

**D-2 ✅ 구현 완료 (2026-08-03, `v6.3-event_suppression_sync`)**: 종전 제안(가칭 `all.sync.suppression`)이
**`SYNC_EVENT_SUPPRESSION` @ `all.sync.event-suppression`** 으로 확정·출하됐다. 이제 GIS/VMS/NVR/Proxy/
AiAnalysis 가 폴링을 기다리지 않고 **즉시** 반영할 수 있다(폴링은 fail-safe 로 계속 유지).

**db_monitor 변경분 (이미 반영됨)**:

```python
CMD_SUBJECT_MAP = {
    ...
    "SYNC_EVENT_SUPPRESSION": "all.sync.event-suppression",
}
```

- `cmd_to_subject()` 가 **미등재 cmd 를 만나면 경고 로그**를 남기도록 보강했다. 종전에는 조용히
  drop 해서, 트리거만 배포되고 db_monitor 가 구버전이면 **무성 유실**이 났다.
- **★ 배포 순서 고정: db-monitor 먼저 → api-server.** 역순이면 새 cmd 가 NOTIFY 되는데 매핑이 없어
  버려진다(위 경고 로그로 즉시 드러남).

**발행 경로 (api-server 측, 참고)** — db_monitor 는 기존 `gop_sync` LISTEN 그대로다:

| # | 트리거 | 담당 |
|---|---|---|
| 1 | `event_suppression_schedules` row-level | 생성/시간·이름 변경/취소(soft-cancel)/하드삭제 |
| 2 | junction 2테이블 statement-level | **대상 배열만 바꾸는 PATCH**(부모 행이 dirty 가 안 돼 UPDATE 문이 안 나감 — MSG-01 재발 구조) |
| 3 | 창 경계 date-job → `notified_status` UPDATE | **창 시작**(DB 쓰기가 없어 트리거로 포착 불가) / 창 종료 |

- payload 를 부모/junction 동일하게 맞춰 **동일 (채널,payload) NOTIFY 병합**으로 중복이 자동 제거된다
  (device_group_mappings 에서 쓰던 기법과 동일).
- 전용 함수 `fn_notify_suppression_sync()` 는 **EXCEPTION 가드**가 있다 —
  `fn_notify_gop_sync` 는 가드가 없어 확장하지 않았다(트리거 오류가 사용자 트랜잭션을 롤백 → API 500).

**라이브 검증**: NATS `sensorway.>` 구독 하에 **7전이 전부 정확히 1건**(생성/대상교체/이름변경/취소/
하드삭제/창시작/창종료), 중복 0·누락 0. 기존 `SYNC_DEVICE` 무회귀 확인.

- [x] (D-1) 무변경 확인 → **D-2 로 변경 발생**(CMD_SUBJECT_MAP 1행 + 경고 로그)
- [x] (D-2) `SYNC_EVENT_SUPPRESSION` 발행 + 브로커 스펙 **v1.6 §9.12** 개정 완료
- [ ] 배포 시 **db-monitor 먼저** 재빌드·기동 후 api-server (순서 준수)
