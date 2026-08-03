# 이벤트 억제(정비 창) — 서브시스템 연동 문서 (진입점)

- **갱신일**: 2026-08-03 · **대상 API**: **6.3.2** · **브로커 명세**: **v1.6 §9.12**

---

## 📄 → [**INTEGRATION.md**](INTEGRATION.md) — 통합 연동 가이드 (마스터)

**이 하나만 읽으면 됩니다.** 여러 서브시스템을 함께 담당하는 개발자를 위해
팀별 문서 7종을 하나로 합쳤습니다. 공통 계약 + 팀별 상세 + 통합 체크리스트가 모두 들어 있습니다.

| 찾는 것 | 위치 |
|---|---|
| **우리 팀은 뭘 해야 하나** | [§0.1 팀별 할 일 한눈에](INTEGRATION.md#01-팀별-할-일-한눈에) |
| **NATS 수신 팀 공통 3원칙** | [§0.2](INTEGRATION.md#02--nats-수신-팀-공통-3원칙-이번-차수-필수--central-제외) |
| REST 엔드포인트 7개 · 필드 사전 | [§2.1](INTEGRATION.md#21-rest-엔드포인트-7개) · [§2.2](INTEGRATION.md#22-필드-사전) |
| **시간대 규약**(offset 필수) | [§2.3](INTEGRATION.md#23--시간대-규약--가장-흔한-사고) |
| **장비 ID 주의**(`devices.id`) | [§2.4](INTEGRATION.md#24--장비-id-주의--devicesid-를-보낼-것) |
| 억제 판정 규칙(의사코드) | [§2.5](INTEGRATION.md#25-억제-판정-규칙-클라이언트-측-복제-시-동일-로직) |
| 202 억제 응답 | [§2.6](INTEGRATION.md#26-억제된-이벤트-post-응답--202-proxyaianalysis-필독) |
| **NATS `SYNC_EVENT_SUPPRESSION`** | [§2.7](INTEGRATION.md#27--nats-알림-sync_event_suppression-v632-신설) |
| **fail-safe 규범**(해제는 신호 의존 금지) | [§2.8](INTEGRATION.md#28--fail-safe-규범-must) |
| 서브시스템별 상세 | [§3](INTEGRATION.md#3-서브시스템별-상세) |
| 알려진 서버 제약 + 회피 | [§4](INTEGRATION.md#4--알려진-서버-제약-회피-필요) |
| 통합 체크리스트 | [§5](INTEGRATION.md#5-통합-체크리스트) |

---

## 팀별 진입 (통합본의 해당 절로 이동)

| 서브시스템 | 절 | 요약 |
|---|---|---|
| [GIS](GIS.md) | [§3.1](INTEGRATION.md#31-gis-관제--central-ui) | 정비 창 관리 UI · 활성 배너 · 삭제 2종 |
| [PidsProxy](Proxy.md) | [§3.2](INTEGRATION.md#32-pidsproxy) | 202 처리 · connection 토큰 · 라이브 발행 skip |
| [AiAnalysis](AiAnalysis.md) | [§3.3](INTEGRATION.md#33-aianalysis) | 202 처리 · AI 탐지 발행 skip |
| [VMS](VMS.md) | [§3.4](INTEGRATION.md#34-vms) | 이벤트 트리거 녹화/PTZ/팝업 억제 |
| [NVRManager](NVR.md) | [§3.5](INTEGRATION.md#35-nvrmanager) | 이벤트 트리거 녹화 억제 |
| BroadcastingManager | [§3.6](INTEGRATION.md#36-broadcastingmanager) | 이벤트 연동 자동 방송 억제 |
| Central | [§3.7](INTEGRATION.md#37-central) | **NATS 미수신** — HTTP 폴링만 |
| [db_monitor](db_monitor.md) | [§3.8](INTEGRATION.md#38-db_monitor-참고) | 서버측 완료(우리 컴포넌트) |

> 위 개별 파일은 **포인터 스텁**입니다. 실제 내용은 통합본에만 있으며,
> **불일치 시 INTEGRATION.md 가 우선**합니다(사본 드리프트 방지 — 마스터는 하나).

---

## 계약 원본 (서버측 마스터)

| 계약 | 문서 |
|---|---|
| **REST API** | `GOP_Restful_Api_연동설계.md` **§6.8** |
| **NATS 메시지** | `Gop_Message_Broker_연동설계_v1.6.md` **§9.12** |
| 서버 결함 수정 계획 | `docs/prds/event-suppression-hardening-prd.md` |

---

## ⚠ 배포 상태 (2026-08-03)

테스트 서버 `123.141.236.253:8136` 는 **6.3.2 초기 커밋** 상태로
`SYNC_EVENT_SUPPRESSION` **미발행** + PATCH 500 미수정입니다.
`info.version` 이 개발 서버와 똑같이 6.3.2 라 **버전으로 구분되지 않습니다** —
device 대상 창에 **이름만 바꾸는 PATCH → 200 이면 최신 / 500 이면 재배포 전**.
자세히는 [§0.3](INTEGRATION.md#03--배포-상태-2026-08-03-기준).
