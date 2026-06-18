# PRD: v4.5 잔존 부채 정밀 정리 (Debt Cleanup Plan)

> **작성일**: 2026-06-19 (오늘 하루 묶음 — 1차수)
> **차수**: v4.5
> **선행 안전점**: `v4.4-final-stable` (commit 050cf6d)
> **작성 도구**: Workflow 46 agent (Discovery 1 + Per-Group Analysis 15 + Scenario Sim Minimal 15 + Full 15) — 3,492,386 token / 16분

---

## 1. Executive Summary

174건 테스트 부채 중 158건(91%)이 minimal(테스트만 정정) 시나리오로 회복 가능하며, 실 API/매니저 통합/Swagger는 이미 v4.x 차수와 정합 상태이므로 운영 중단 위험 0. P1 그룹(G09 Logs/Audit 1:N, G12 EM Bulk envelope) 2건만 매니저 통합 직전 full 정합 필수이고, 나머지 13건은 v4.5/v4.6 분산 정리로 CI Red 해소 가능. 총 23시간 minimal + 7시간 P1 full = 30시간으로 174건 전량 정리 가능하며, 차장 결재 5건(envelope 표준화 / Enum LAMP 동기화 / Server v2.9 확정 / DetectionLog 1:N 계약 / ROI points 필수 정책)이 선행 필요.

- **총 잔존 부채**: 174건 (pytest fail)
- **총 작업량**: 30h (= 약 3.8 인일)
- **그룹 수**: 15개

---

## 2. 부채 그룹 인벤토리 (15 그룹)

| ID | 그룹 | 우선순위 | 매니저 영향 | 런타임 영향 | minimal 회복 | minimal 분량 | 선택 |
|---|---|---|---|---|---|---|---|
| **G01** | Camera URLs 통합 (StreamUrls/HomepageUrl/OnvifUrl 삭제 → urls JS | P2 | medium | none | 23건 | 1.5h | **minimal** (1.5h) |
| **G02** | Device is_enable 필수화 + nested 스키마 | P2 | medium | none | 19건 | 2.5h | **minimal** (2.5h) |
| **G03** | ConfigChangeLog 응답 envelope key 변경 | P2 | low | none | 2건 | 0.3h | **minimal** (0.3h) |
| **G04** | ServerMetrics 분리 (cpu_usage 등 Server에서 분리) | P2 | medium | low | 14건 | 1.5h | **minimal** (1.5h) |
| **G05** | ActionEvent 1:N 구조 변경 (v4.3 변경 잔존 가정) — Stale tests vs PRD v | P2 | low | none | 11건 | 0.5h | **minimal** (0.5h) |
| **G06** | PDF/Report 시스템 변경 (폰트 NanumGothic / FAILED enum) | P2 | medium | none | 11건 | 0.75h | **minimal** (0.75h) |
| **G07** | Account/Auth 시스템 변경 (role enum 대문자 등) | P2 | medium | low | 12건 | 1.5h | **minimal** (1.5h) |
| **G08** | Camera Preset / ROI / include params | P2 | medium | low | 11건 | 2.5h | **minimal** (2.5h) |
| **G09** | Logs/Audit 응답 형식 변경 | P1 | high | none | 10건 | 1.5h | **full** (6.5h) |
| **G10** | Sensor/Speaker/Enclosure geolocation 잔존 가정 | P2 | medium | none | 7건 | 0.5h | **minimal** (0.5h) |
| **G11** | EM single router envelope | P2 | low | none | 7건 | 0.5h | **minimal** (0.5h) |
| **G12** | EM Bulk envelope detail | P1 | medium | medium | 8건 | 1h | **full** (6.5h) |
| **G13** | Enum NONE / device_category 추가 | P2 | low | none | 4건 | 0.5h | **minimal** (0.5h) |
| **G14** | rtsp_uri/rtsp_port 컬럼 삭제 잔존 가정 | P2 | low | none | 4건 | 0.25h | **minimal** (0.25h) |
| **G15** | 기타 (config / device_version / event base / camera_schema) | P2 | low | none | 8건 | 1.5h | **minimal** (1.5h) |

---

## 3. 그룹별 결정 — Minimal vs Full 시나리오

### G01 — Camera URLs 통합 (StreamUrls/HomepageUrl/OnvifUrl 삭제 → urls JSONB)

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: none

**원인 (요약)**: 테스트는 PRD_Camera_Urls_JsonB.md v1.0 Section 2의 "이상적 nested 스키마"(StreamUrls{main,sub,extra=allow}, HomepageUrl{url}, OnvifUrl{device_service,media_service,ptz_service}, CameraUrls{homepage:HomepageUrl, onvif:OnvifUrl, streams:Dict[str,StreamUrls], snapshot:Dict[str,str]})를 import/검증하지만, 실제 구현(app/schemas/device.py:40-88)은 단순화된 flat 버전 — CameraUrls의 4개 필드 모두 Optional[dict] + extra="allow"만으로 처리한다. St

**Why this priority**: 런타임 영향 0: 모델(JSONB urls 컬럼), 4개 이벤트 라우터(detections/connections/malfunctions/actions), Camera CRUD 모두 PRD대로 동작하며 응답 JSON shape도 PRD 예시와 일치. GIS/VMS/NVR/Speaker 매니저는 device.urls의 dict 구조(homepage.url, streams.rtsp.main 등 경로)로 접근하므로 nested vs flat Pydantic 클래스 차이 무관 — manager-facing API는 안정. Swagger/Op

**책임 commit (옛 차수)**: `a3e411d (2026-01-07) "updated Camera Urls(Jsonb), Event mapping cameras, Speaker Api" — Camera urls JSONB 통합 본 작업. app/models/device.py +6, 4개 라우터 _build_device_nested_response 갱신. PRD_Camera_Urls_Jso`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 23건 | 1.5h | low | 채택 권장. 모델·라우터·런타임 응답 shape는 PRD와 동일하며 schema 단순화는 명시적 설계 결정(주석 존재). 테스트만 현 코드 동작에 맞춰 dict 기반으로 정정하면 23 fail 전부 회복. 7건 skip은 부채 시각화 효과(언제든 unskip으로 nested 도입 추적 가능). 후속으로 PRD Section 2에 '실 구현 = flat di |
| Full | 23건 | 6h | medium | 권장 — 부채 G01은 schema/test/spec 3-way 불일치가 명백하고, PRD v1.0이 이미 nested 디자인을 명세로 선언했기 때문에 simplified dict를 정식 채택하기 어렵다(매니저 통합 시 OpenAPI 정확도가 떨어지고 다른 컴포넌트가 wrapper class를 임시 정의해야 함). 6시간 투자로 23개 fail 회복 + O |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 런타임 영향 0, schema 단순화는 의도된 설계 결정(주석 명시). nested 격상은 매니저 OpenAPI 영향 동반하므로 v5.x로 분리. minimal 1.5h로 23건 회복.

---

### G02 — Device is_enable 필수화 + nested 스키마

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: none

**원인 (요약)**: 테스트는 스키마의 옛 형태를 가정하고 있고, 실제 코드는 PRD 차수에 따라 이미 리팩터링이 완료된 상태다. 부채의 본질은 '스펙 변경 후 테스트 미동기화'다. 구체적으로 4계열의 미스매치가 누적되어 26건이 깨진다.

(1) DeviceNestedResponse의 is_enable 필수화 vs 테스트 미반영
- 현재 app/schemas/device.py L213, L312, L377, L497, L567 등에서 모든 *NestedResponse 의 is_enable 이 `Field(..., description=...)` 즉 required.
- 그러나 tests/test_device_nested_schema.py L38~46, L94~103, L114~122, L146~153, L164~173, L19

**Why this priority**: P2 — 테스트만 깨지고 실 API 동작 정상. (1) controllers/sensors/cameras 라우터는 is_enable 을 정상 직렬화/역직렬화, group_ids 배열 처리, geolocation JSONB 처리 모두 PRD 최신 차수와 일치. (2) 매니저 통합(GIS/VMS/NVR/Speaker)은 urls JSONB와 device_groups[] 를 소비하며 OpenAPI 명세(temp_openapi.json)에 정확히 반영됨 — Swagger 불일치 아님. (3) 보안/운영 중단 위험 없음 → P0/P1 아님.

**책임 commit (옛 차수)**: `35e5092 (updated v2.9: is_enable 도입), 73d74ea (feat: Add Lamp Device and EventMappingLamp APIs — is_enable 일관 적용), 0542853 / a3e411d (Camera urls JSONB 통합으로 rtsp_uri/rtsp_port 제거, v2.3 breaking), 68c2`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 19건 | 2.5h | low | 권고: 본 최소 정정 시나리오 즉시 채택. 26건 중 19건이 순수 테스트 페이로드/어서션 미동기화로 분류되며, 프로덕션 0줄 수정으로 회복 가능. 잔여 7건(추정)은 test_db SQLAlchemy 환경 또는 일부 enum 미스매치로 본 시나리오 범위 밖. (1) 본 최소 시나리오를 먼저 적용해 부채 카운트를 26→7로 낮추고, (2) 잔여 7건은 도커 |
| Full | 26건 | 8h | medium | 권고: 본 시나리오(완전 정합)는 G02의 부채 본질('스펙 변경 후 테스트 미동기화')을 근본 차단하는 유일한 경로다. 26건 전량 회복 + PRD/OpenAPI/테스트 3자 일치 + 외부 노출 스펙 확정이라는 4중 이득이 있다. 단계: ① 코드는 '현 차수 확정' 모드(주석/도크스트링 보강만, behavior 변화 0) — 1H, ② 테스트 6종 dic |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 코드는 PRD v4.x 정합 완료, 테스트만 stale. minimal 2.5h로 19/26건 회복 후 잔여 7건은 환경 정합으로 분리. full(8h)은 OpenAPI discriminator 도입을 동반해 매니저 SDK 재생성 필요 — v4.7 이후 검토.

---

### G03 — ConfigChangeLog 응답 envelope key 변경

**우선순위**: P2 / **매니저 영향**: low / **런타임 영향**: none

**원인 (요약)**: 그룹명은 "envelope key 변경"이지만, 실제 18건 실패는 5개 서브-원인의 혼합 그룹입니다.

[1] 응답 envelope 불일치 (2건, 그룹명의 본질):
- 실패: TestConfigChangeLogAPI.test_get_config_change_logs_empty / test_get_config_change_logs_pagination
- 테스트 기대: data = {"logs": [...], "total": ..., "page": ..., "limit": ...}
- 실제 라우터(app/routers/config_change_logs.py:60-187): ApiResponse[list[ConfigChangeLogResponse]]를 사용하여 data=[...] (bare list) + pa

**Why this priority**: P2(테스트만 깨짐, 실 API 정상)로 판정.
근거:
- 응답 envelope: 라우터 출력 = 스펙(GOP_Restful_Api_연동설계.md §9.7.2) 일치. 매니저(GIS/VMS/NVR/Speaker)는 스펙 기준으로 통합하므로 운영 영향 0. Swagger/OpenAPI도 라우터 response_model에서 자동 생성되므로 외부 컨슈머 불일치 없음.
- 운영 중단/보안 사고 없음 (P0 아님).
- 매니저 통합 영향이 발생하려면 라우터-스펙 간 불일치여야 하는데 두 곳 모두 ApiResponse[list[T]]+pag

**책임 commit (옛 차수)**: `26f3125 struct: Add ApiSingleResponse schema, update all router response_model for single-item endpoints (2026-02-09) — 이 commit에서 list endpoints는 ApiResponse[list[T]]+pagination 사이드카, single endpoint`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 2건 | 0.3h | low | 권고: 본 최소 정정을 즉시 적용. (1) 코드 변경 0건 — 라우터가 이미 스펙(GOP_Restful_Api_연동설계.md §9.7.2)을 준수하므로 테스트만 stale. (2) 회복 2건은 G03 그룹명의 본질에 정확히 해당. (3) 후속 작업으로 G03을 G03-A(envelope 2건, 본 시나리오), G03-B(EnumConfigResourceTy |
| Full | 18건 | 7.5h | medium | G03을 그대로 두지 말고 5개 서브-그룹(G03a envelope-stale-test 2건 / G03b enum-count-drift 1건 / G03c ROI-points-required 3건 / G03d EnumEventType-values 8건 / G03e EventMapping-DELETE-data 2건)으로 분할 후 각각 별도 PR로 처리할 것.  |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 그룹명(envelope) 본질 2건만 minimal로 즉시 처리. 나머지 16건(enum/ROI/EventMapping DELETE)은 G11/G13/G08에 자연 흡수되므로 G03 자체는 0.3h로 종결.

---

### G04 — ServerMetrics 분리 (cpu_usage 등 Server에서 분리)

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: low

**원인 (요약)**: commit 35e5092 (v2.9, 2026-01-15)에서 서버 리소스 메트릭(cpu_usage, ram_usage, disk_usage, network_throughput 등)을 Server 테이블에서 분리하여 별도 ServerMetrics 테이블(시계열 1:N)로 이관함. 동시에 app/routers/server_metrics.py(371줄) 신규 라우터 추가, Server / ServerCreate / ServerUpdate / ServerResponse / ServerNestedResponse 에서 해당 5개 인라인 메트릭 필드 제거. 그러나 G04에 묶인 5개 테스트 파일은 v1.6 시점(commit 5e8ff25) 그대로이며 (1) Server 모델 컬럼 inspect 시 cpu_usage/

**Why this priority**: 실 런타임은 v2.9 설계대로 정상 동작 — /api/servers 는 메트릭을 인라인 노출하지 않고 /api/server-metrics/* 시계열 라우터가 별도 제공되어 Swagger/OpenAPI 와도 일치한다. 따라서 운영 중단·보안 사고 가능성 없음(P0 제외), 매니저(GIS/VMS/NVR/Speaker) 통합도 v2.9 이후 별도 메트릭 엔드포인트 사용을 가정하면 Swagger 와 일치(P1 제외). 단 (a) 테스트가 14건 깨져 있어 CI red 상태가 고착되면 회귀 검출력 상실 (b) 신규 컨트리뷰터가 Server 

**책임 commit (옛 차수)**: `35e5092 'updated v2.9 not completely finished' (2026-01-15) — Server 인라인 메트릭 5필드 제거 + ServerMetrics 모델 + server_metrics.py 라우터 신설. 5e8ff25 'v1.6 was updated for servers' — 인라인 메트릭이 있던 직전 상태. 35e5092 c`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 14건 | 1.5h | low | 권고: 채택. v2.9 ServerMetrics 분리는 PRD_System_Event.md §2.4에 명시된 의도된 정규화이며 라우터/스키마/관계가 이미 일관되게 정렬돼 있음 — 테스트만 1.5h 정정으로 14건이 회복된다. 단, '메트릭 시계열' E2E 커버리지가 비게 되므로, 본 시나리오 머지 직후 별도 작업으로 test_server_metrics.py |
| Full | 14건 | 14h | medium | 권고: 시나리오 2(완전 정합) 채택 권장. 이유 3가지 — (1) 코드 측은 이미 v2.9 분리가 완료되어 있어 'rollback 시나리오 1(인라인 메트릭 부활)'은 v2.9 이후 6개월간 누적된 server_metrics 시계열 데이터·임계치 알림 로직·SystemEvent 연동을 전부 폐기해야 함 → 손실 비용 압도적. (2) 14건 fail은 전부 |

**채택 시나리오**: **MINIMAL**

**채택 이유**: v2.9 ServerMetrics 분리는 의도된 정규화. minimal 1.5h로 14건 회복하되, full(14h)은 db_monitor 인제스트 경로 전환 + Central UI latest_metrics 바인딩 동시 작업 필요 — v5.x로 분리 후 통합 마일스톤에 묶음.

---

### G05 — ActionEvent 1:N 구조 변경 (v4.3 변경 잔존 가정) — Stale tests vs PRD v1.5/v2.1 (from_event_id polymorphic)

**우선순위**: P2 / **매니저 영향**: low / **런타임 영향**: none

**원인 (요약)**: 두 PRD 리팩터가 누적되면서 옛 테스트가 정리되지 않음. 옛 구조(`from_event:int` + `from_type_event:str` discriminator)를 가정한 테스트들이 PRD v1.5(`from_type_event` 제거)와 PRD v2.1(`from_event`→`from_event_id` 단일 FK Polymorphic 전환) 이후에도 그대로 남아있다. 현재 `app/models/event.py` ActionEvent는 `from_event_id = Column(Integer, ForeignKey('events.id', ondelete='SET NULL'))` 단일 FK + `relationship('Event', back_populates='actions')` polymorphic 

**Why this priority**: 실 모델·스키마·라우터·Swagger는 모두 PRD v1.5/v2.1 신구조(`from_event_id` 단일 FK polymorphic)로 일관됨. 매니저 측(DBApi/db_monitor/Central UI) 통합은 Swagger OpenAPI 응답(`from_event` nested 객체)을 소비하므로 영향 없음 — 운영/보안 위험 없음(P0/P1 배제). 그러나 8건(legacy 테스트)이 신구조에 영구 실패하고, 3건(신구조 edge)도 fixture 보완 필요라서 CI 신뢰도가 떨어지는 단순 정리 부채(P2). 처리 비용

**책임 commit (옛 차수)**: `908d373 'updated v1.3' (2025-11-17) — PRD v1.5 from_type_event 제거 + actions.py 274줄 대규모 변경; 11fc4b6 'updated for event schema and api format' — from_event_id 단일 FK polymorphic 도입(PRD v2.1); b7d60a1 'f`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 11건 | 0.5h | low | 권고: 시나리오 1(최소 정정) 채택. 운영 코드(`app/models/event.py`, `app/schemas/event.py`, `app/routers/actions.py`)는 이미 PRD v2.1 단일 FK Polymorphic 구조로 정합하며 실 API·Swagger·DB 모두 일관. 부채는 100% '문서 누락된 테스트 정리'이므로 코드 변경 없 |
| Full | 11건 | 6.5h | medium | 권고: 본 시나리오는 '완전 정합'을 보장하나, 운영 코드(모델/라우터)는 이미 PRD v2.1 신구조이고 실 API/Swagger와 일관되므로 운영 리스크는 거의 없다. 다만 (a) Pydantic v2 discriminator Union 적용은 OpenAPI 스펙 변경을 동반하므로 Central UI 팀과 사전 공유 후 진행, (b) PRD 본문 변경은 |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 코드는 PRD v2.1 from_event_id 완전 정합. legacy 테스트 2파일은 skip 마크로 격리하면 충분. full(6.5h)의 discriminator 도입은 Central UI SDK 재생성 트리거 — 회피. minimal 0.5h.

---

### G06 — PDF/Report 시스템 변경 (폰트 NanumGothic / FAILED enum)

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: none

**원인 (요약)**: 테스트 경직성 vs 생산 코드의 OS-aware fallback 설계 충돌. (1) `tests/test_pdf_korean_fix.py`는 Windows 환경 가정으로 작성됨: `_register_fonts()` 후 reportlab에 `MalgunGothic`이 반드시 등록되어 있어야 한다고 단정(line 73), `_get_styles()` 의 4개 스타일이 모두 `fontName=='MalgunGothic'` 이라고 단정(line 88), matplotlib `font.family`에 `'Malgun Gothic'` 포함되어야 한다고 단정(line 130). 그러나 commit e472a03 (2026-02-12 'Docker 한글 폰트 지원 fonts-nanum fallback 체인')에서 `app

**Why this priority**: 실 API/매니저 통합 영향 없음. Windows 환경(개발 PC)에선 MalgunGothic이 등록되어 PDF·차트 모두 한글 정상 렌더링되고 Linux/Docker 환경에선 NanumGothic으로 정상 렌더링됨. 모델 status가 String(20)이라 Swagger/OpenAPI 스키마 불일치도 없고 GIS/VMS/NVR/Speaker 매니저 어느 것도 본 PDF 레이어를 호출하지 않음. 따라서 운영 중단·보안·통합 충격 0. 단, CI(Docker 기반)에서 12건 적색이 잔존 부채 가시성을 흐리고 개발자가 폰트 코드를 

**책임 commit (옛 차수)**: `e472a03 fix: Docker 한글 폰트 지원 (fonts-nanum fallback 체인) — pdf_generator/chart_generator에 Malgun→Nanum→Helvetica fallback 도입. 선행 4f8203a fix: PDF/Chart 한글 깨짐 수정 + 다운로드 파일명 인코딩 — MalgunGothic 단일 등록을 도입한 `

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 11건 | 0.75h | low | 권고: 시나리오 1(최소 정정) 채택. 사유 — (a) e472a03에서 NanumGothic fallback은 Docker/CI 의도된 기능 강화이므로 테스트가 따라가야 함(생산 코드 회귀 없음), (b) 변경 범위가 단일 테스트 파일 4개 assert로 국소화되어 리스크 최저, (c) test_report_async 8건은 OS-경직성의 cascade이 |
| Full | 12건 | 14h | medium | 권고: 전체 정합 시나리오는 14h 투자로 12 fail 회복 + 향후 OS 의존 회귀 차단(ROI 우수). 단, 단순히 fail 죽이는 목적이라면 시나리오1(최소 정합: 테스트만 OS-agnostic 패치, 2h)이 효율적이다. 본 시나리오 채택 조건: (a) Docker 운영 환경 PDF 보고서가 실제 사용된다, (b) Central UI에 COMPLE |

**채택 시나리오**: **MINIMAL**

**채택 이유**: Windows/Docker fallback은 의도된 OS-aware 설계. 테스트 단정만 완화하면 11건 회복(0.75h). full(14h)의 status enum 5값 도입은 Central UI UI 작업 동반 — v5.x로 분리.

---

### G07 — Account/Auth 시스템 변경 (role enum 대문자 등)

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: low

**원인 (요약)**: Legacy User 모델(`users` 테이블)은 role을 소문자(`"admin"`, `"user"`)로 저장/사용하는데, commit 8cfac2b (CameraSetting, ProxyServer api updated, 2026-02-07)에서 `app/schemas/user.py`의 `UserResponse.role`을 `str` → `EnumUserRole`로 일괄 상향했음. EnumUserRole은 대문자 5종(ADMIN/MAINTAINER/OPERATOR/VIEWER/GUEST)만 허용(app/utils/enums.py:359-370). 결과:\n\n(1) `tests/test_user_schemas.py:28` — `UserResponse(role=\"admin\")` 호출 시 Pydanti

**Why this priority**: 실 API 런타임 영향은 낮음: 신규 인증 흐름(POST /api/auth/login → AccountUser → AccountUserResponse)은 DB가 대문자 role을 저장하고 init_db의 `create_admin_account_user`가 `role=\"ADMIN\"`을 시드하므로 정상 동작. 매니저 통합 영향도 낮음: 매니저들은 JWT 토큰만 받고 로그인 응답 본문의 role enum까지 강하게 검증하지 않음. 단, (a) 레거시 `/api/auth/login/oauth2` + legacy `UserResponse

**책임 commit (옛 차수)**: `8cfac2b (CameraSetting, ProxyServer api updated) — `app/schemas/user.py`의 UserResponse.role을 str → EnumUserRole로 상향. d8c0fbf (docs: Add [LEGACY] annotations) — User 모델/스키마에 LEGACY 주석 표기. d712b19 (v4.1`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 12건 | 1.5h | low | 권고: 최소 정정 시나리오 채택. 코드 0건 변경 + 테스트 7파일 갱신/일부 skip으로 12건 모두 회복(녹색화). 비용 1.5h, 리스크 low (PRD_Account_Design + PRD_UserSession_Improvement v1.2가 이미 권위 있는 기준이고, 변경되는 단언이 그 기준을 따르도록 정렬). 단, skip 처리한 7건의 토큰→사 |
| Full | 12건 | 6h | medium | 권고: 즉시 실행. 12건 fail을 일괄 회복하고 신구 모델 분리 정책을 코드/테스트/명세에 동시 박제하므로 향후 EnumUserRole 단방향 업그레이드 재발 방지 효과 큼. 단, 6h 작업 중 절반(약 3h)은 GOP_Restful_Api_연동설계.md Auth 섹션 정합 + PRD cross-reference + OpenAPI 검증에 투입 필요. 실 |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 신구 모델(User/AccountUser) 병존을 명시적 분리는 full(6h)이지만, OpenAPI 영향이 있어 v4.5는 minimal(1.5h)로 12건 회복 + /me 응답 분기는 별도 PR로 분리. 7건 skip은 conftest 의도된 단순화로 격리.

---

### G08 — Camera Preset / ROI / include params

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: low

**원인 (요약)**: G08의 11건 실패는 4개의 독립된 근본 원인으로 분류됨. 핵심은 "v4.x 스펙 진화에 맞춰 schema/router는 갱신되었으나 테스트가 구버전(v2.x ~ v3.x) 계약에 묶여 있음"이다.

[원인 1] ROICreate.points 필드가 required(min_length=3)로 강화됨 (app/schemas/camera_preset.py:67) — 테스트 2건(test_camera_preset_schema.py::TestROISchema 2건) 및 integration 1건(test_camera_preset_integration.py)이 points 없이 ROI 생성 후 PUT /api/rois/{id}/points로 분리 부여하는 워크플로를 기대. 스펙 변경으로 422 발생.

[원인 2]

**Why this priority**: 실 API 운영 영향은 낮음 — (1) ROI 생성 워크플로는 v4.x에서 points 동시 입력이 정상 계약이므로 클라이언트 코드도 이미 그렇게 호출. (2) is_enable은 ORM 모델/시드 데이터에 기본값으로 채워져 실 응답은 정상. (3) rois/points 키 누락 차이는 추가 키 노출일 뿐 OpenAPI 응답 모델(CameraPresetListItem 등)이 해당 키를 정의하므로 매니저 통합 시 무해. (4) 컨트롤러 Query(None) 바인딩 버그는 FastAPI 정상 라우팅 경로에서는 발생하지 않음(테스트가 핸

**책임 commit (옛 차수)**: `71ba91b(v2.2 ROICreate 도입) → 73d74ea(is_enable 격상, Lamp 추가) → ba91395(db_monitor 알림, v3.8 SensorNestedResponse 도입) → 7aced94(v4.3 Bulk API). ROICreate.points의 required 전환과 SensorNestedResponse 도입이 테스트`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 11건 | 2.5h | low | 권고: 채택. 사유 — (1) 코드(스키마/라우터)가 v4.x 스펙·PRD(PRD_Device_Structure_Refactoring is_enable 공통필드 격상, ROI min_length=3 polygon 보장, v2.4 Nested 규칙)와 이미 정합하며, 테스트만 구버전 계약에 묶여 있는 명백한 '테스트 부채' 케이스. (2) 11건/4원인 모두 |
| Full | 11건 | 9h | medium | 권고: 2단계 분할 머지. 1단계(약 4h, 저위험) — C2(is_enable 테스트 보강) + C3(라우터 조건부 키 헬퍼 추출) + C4a(SensorNestedResponse 단언 정정)를 한 PR로. 이는 순수 정합화이며 외부 클라이언트 영향 없음. 2단계(약 5h, 중위험) — C1(ROI.points 필수 정책 확정) + C4b(controll |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 11건 전부 v4.x 스펙 진화에 따른 테스트 미동기화. minimal 2.5h로 코드 무변경 회복. full(9h)의 controllers 서비스 함수 분리는 Tidy First 차원에서 별도 PR로 분리 가능.

---

### G09 — Logs/Audit 응답 형식 변경

**우선순위**: P1 / **매니저 영향**: high / **런타임 영향**: none

**원인 (요약)**: 두 갈래의 의도된 응답 형식 변경이 테스트 동기화 누락으로 fail. (1) DetectionLog: 초기 PRD(b7d60a1)에서는 1 detection : 1 action (`action: Optional[ActionNested]`)로 설계됐고 tests/test_detection_log_schema.py와 test_detection_log_api.py(`assert "action" in fields`, `event_data["action"] is None`, `event_data["action"]["id"]`)가 이를 검증함. 그러나 commit e087af4 "updated"에서 1:N 모델로 리팩터링하면서 app/schemas/event.py L406을 `actions: list[ActionNes

**Why this priority**: 실 API/스키마/Swagger는 일관됨(P0/P2 아님) — 런타임 운영 중단 없음. 그러나 (a) action(single) → actions(list) 변경은 Central UI/DB monitor가 detection log 조회 시 JSON 키 이름과 타입(객체 vs 배열)이 바뀌는 brake change이고, (b) /api/logs 봉투화 + skip→page 파라미터 변경은 매니저/관제 UI의 로그 뷰어 통합에 직접 영향. 두 변경 모두 OpenAPI 스펙은 최신이지만 외부 통합 측은 이전 계약을 캐싱하고 있을 가능성이

**책임 commit (옛 차수)**: `b7d60a1 feat: Add Detection Log API (action single, 초기 PRD) → e087af4 updated (action→actions list 1:N 리팩터) ; f2278a0/5e8ff25 v1.6 (logs/* ApiResponse 봉투 + page/limit 표준화)`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 10건 | 1.5h | low | 권장: minimal 시나리오 채택. 두 변경 모두 의도된 API 계약 진화(1:N actions, ApiResponse 봉투 통일)이며 다른 라우터/테스트는 이미 새 계약을 따르고 있어 G09는 순수한 테스트 누락 부채임. 코드 롤백 시 detection_logs 라우터/스키마 + logs 라우터 + 다른 통합 테스트까지 동반 수정이 필요해 비용이 10배 |
| Full | 11건 | 6.5h | high | 권고: 본 시나리오는 부채 청산도(완전 정합)는 최고이나 risk=high. 단계 분리 권고 — (Step A, 2h) DetectionLog 테스트만 새 계약(actions list)으로 즉시 정정 + PRD v1.1 변경이력 갱신. 코드는 verify-keep으로 무변경, 빠른 GREEN 회복. (Step B, 2h) ApiLogs 테스트를 envelo |

**채택 시나리오**: **FULL**

**채택 이유**: P1 그룹 — DetectionLog 1:1→1:N 및 /api/logs 평면→ApiResponse 봉투 변경은 매니저(C2 db_monitor, C5 Central UI) 통합 시 와이어 계약 충돌 가능. PRD_DetectionLog_API.md v1.1 + GOP_Restful_Api 본문 동기화 필수. full 6.5h로 통합 직전 청산.

---

### G10 — Sensor/Speaker/Enclosure geolocation 잔존 가정

**우선순위**: P2 / **매니저 영향**: medium / **런타임 영향**: none

**원인 (요약)**: G10은 단일 원인이 아니라 4가지 잔존 가정의 묶음입니다.

[1] **Speaker tests — category_device 잔존 (2건)**
`tests/test_speaker_geolocation.py:122` `SpeakerResponse(category_device="speaker", ...)` 및 `:142` `SpeakerNestedResponse(category_device="speaker", ...)`. 
실제 스키마 (`app/schemas/device.py:681,685`): "SPEC-6.1: category_device 제거 (polymorphic discriminator - API 노출 불필요)". `SpeakerResponse`에서 `category_device` 필드가 삭제되

**Why this priority**: 실 API 영향 없음: 모델(`Sensor/Speaker/Enclosure.geolocation`), 스키마(`Geolocation`, `SensorCreate/Response`, `SpeakerCreate/Response`, `EnclosureCreate/Response`), 라우터 모두 정상 동작. Swagger/OpenAPI 노출도 현재 정책(SPEC-6.1 = category_device 제거, SPEC-004 = is_enable 필수)과 일치.

깨진 것은 테스트가 들고 있는 옛 가정 4종뿐: (1) SpeakerResp

**책임 commit (옛 차수)**: `- `bd42edc` (v2.9 enclosure/lamp 추가): EnclosureDetailInfo→EnclosureMetric 분리, threshold_config 신설
- `73d74ea` (Lamp + EventMappingLamp): Device 다형성 카테고리 확장 (SPEAKER/ENCLOSURE/LAMP)
- `b8b73ed` (report`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 7건 | 0.5h | low | 권고: 본 시나리오로 즉시 적용. (1) 명세 변경(SPEC-004 is_enable 필수, SPEC-6.1 category_device 비노출, Enclosure 오타)이 이미 코드에 반영 완료된 상태이므로, 테스트만 갱신하는 것이 정합적이고 가장 안전합니다. (2) 7건 회복은 grep 가능한 단순 키워드(`is_enable=`, `IpControlle |
| Full | 8건 | 3.5h | medium | 권고: 본 풀-정합 시나리오 채택. 다만 SpeakerNestedResponse.category_device 제거는 NATS/외부 소비처 검색(grep \"category_device\" repo-wide) 후 'Nested에서도 비노출' 정책 결재(1주차 결재 5건과 동일 절차)를 30분 내 받고 진행. 결재 보류 시 Minimal 시나리오로 우회(테스트 |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 코드는 SPEC-004/SPEC-6.1 정합 완료. is_enable 누락 + IpController 오타만 정정하면 7건 회복(0.5h). full(3.5h)의 SpeakerNestedResponse category_device 제거는 NATS 컨슈머 영향 검토 필요 — 별도 결재 안건.

---

### G11 — EM single router envelope

**우선순위**: P2 / **매니저 영향**: low / **런타임 영향**: none

**원인 (요약)**: EM single router CRUD envelope correct, failures from log_config_change internal commit conflicting with SQLite nested transaction fixture.

**Why this priority**: Tests only break, real API works fine. b0c3afe commit explicitly classified as manager impact zero. Postgres JSONB normal operation.

**책임 commit (옛 차수)**: `b0c3afe v4.4 Phase5 21 single ApiSingleResponse[dict] residual 8 manager impact zero; de15ba0 v4.5 PR-D bulk 6 ApiSingleResponse[T]; f0a59c7 v4.6 FR-5 dedup`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 7건 | 0.5h | low | 권고: 최소 정정으로 채택. 실제 원인은 가설(log_config_change×SQLite)이 아니라 단순 envelope 누락이며, 3 라우터에 한 줄씩 `\"data\": {}`만 추가하면 7개 fail 전체가 즉시 회복된다. 테스트는 envelope 표준(`ApiSingleResponse[dict]`)에 부합한 올바른 단언만 하고 있으므로 손대지 않는 |
| Full | 7건 | 3.5h | low | 권고: 시나리오 채택(low risk, 7건 100% 회복). 단, plan.md의 근본원인 기술은 정정 필요 — "log_config_change 내부 commit + SQLite nested transaction" 가설은 traceback과 일치하지 않음(실제 원인은 ApiSingleResponse[dict].data 필수 필드 누락/타입불일치). 작업 |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 실제 원인은 envelope data 필드 누락(가설인 SQLite 충돌 아님). 3개 라우터에 'data: {}' 한 줄씩 추가하면 7건 즉시 회복(0.5h). full(3.5h)의 전용 DeleteResponse 스키마 도입은 OpenAPI 영향 동반 — v4.7 이후.

---

### G12 — EM Bulk envelope detail

**우선순위**: P1 / **매니저 영향**: medium / **런타임 영향**: medium

**원인 (요약)**: Three envelope mismatches across EventMapping Bulk cameras/speakers/lamps causing 8 failures.

**Why this priority**: P1 due to manager integration and Swagger/PRD inconsistency.

**책임 commit (옛 차수)**: `aeb1074 initial bulk endpoints; b4564ff v4.5 PR-A/B; f0a59c7 v4.6 FR-5; de15ba0 v4.5 PR-D; 7aced94 spec v4.3; b0c3afe v4.4 Phase 5.`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 8건 | 1h | low | 최소 정정 시나리오로 즉시 적용 권고. 8건 실패가 모두 envelope 정의 차이(테스트가 v4.4 가정, 코드가 v4.6 PR-B 분류 적용)에서 발생 — 코드는 PRD §4.3/§4.5 및 변경 이력(7aced94, aeb1074)과 일치하므로 테스트가 따라가는 것이 정합. 단, FR 후속 작업으로 (1) preset/file_group 부재를 not |
| Full | 8건 | 6.5h | medium | 권고: 채택. 8 fail 완전 회복 + EM Bulk 3 리소스(카메라/스피커/램프) envelope·로그 키·스펙·PRD가 한 번에 정합되는 단일 PR로 묶을 가치가 있다. Scenario 1(minimal)이 코드만 손대 fail만 끄는 데 비해, Scenario 2는 (a) ConfigChangeLog 키 호환(config_ids+resource_i |

**채택 시나리오**: **FULL**

**채택 이유**: P1 그룹 — EM Bulk envelope(not_found_config_ids 분류, in-request 중복 처리, ConfigChangeLog 키 호환)은 매니저 UI 라벨/감사 소비자에 직접 영향. PRD §4.3 + 마스터 스펙 v4.4 본문 동기화 필수. full 6.5h로 통합 직전 청산.

---

### G13 — Enum NONE / device_category 추가

**우선순위**: P2 / **매니저 영향**: low / **런타임 영향**: none

**원인 (요약)**: 테스트는 옛 PRD 스냅샷(Enum-Update-PRD.md + PRD_Device_Inheritance_Structure_Refactoring v1) 기준으로 작성됐는데, 그 후 두 차례 리네이밍/확장이 일어남. (1) EnumEventCategory(8값: NONE/FENCE_SENSOR_ONLY/.../CAMERA_ONLY)가 PRD_CategoryEvent_Refactoring 단계에서 EnumMappingEventCategory로 이름이 바뀌고, 동명 EnumEventCategory는 Event 모델의 polymorphic discriminator로 재정의됨(현재 3값: detection/malfunction/connection). 테스트는 여전히 옛 8값 enum을 EnumEventCategory

**Why this priority**: 운영 API는 신규 enum 정의(EnumMappingEventCategory 8값, EnumDeviceCategory 6값, EnumEventCategory 3값 polymorphic discriminator)를 일관되게 사용 중이며 Swagger/OpenAPI도 신규 값 기준으로 노출돼 매니저 통합(GIS/VMS/NVR/Speaker)에 불일치 없음. 4개 실패는 모두 테스트가 옛 PRD 스냅샷에 동결된 결과로 코드 결함이 아닌 테스트 부채. 다만 enum은 외부 통신 계약의 일부라 C# 클라이언트와 string value 동기

**책임 commit (옛 차수)**: `2bdf6b0 (EnumEventCategory→EnumMappingEventCategory 분리 + EnumEventCategory 재정의 3값), a3e411d (SPEAKER 추가, v2.5), 75a5832 (ENCLOSURE 추가, v2.6), 73d74ea (LAMP Device + EventMappingLamp APIs, v3.4)`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 4건 | 0.5h | low | 권고: 본 최소 정정 시나리오 채택. 운영 코드가 이미 신규 PRD(CategoryEvent_Refactoring + Speaker/Enclosure/Lamp)와 정합하고 런타임이 정상이므로, 테스트는 단순히 현 enum 정의에 맞추는 것이 안전. 변경 범위는 테스트 2파일·실 수정 라인 약 10줄 내외, 회복 기대 fail 4건(8값/legacy/sens |
| Full | 4건 | 3.5h | medium | 권고: G13은 완전 정합 시나리오를 채택. 테스트가 강제하는 옛 스냅샷(EnumEventCategory 8값 / EnumDeviceCategory 3값)은 이미 폐기된 두 PRD 기준이므로 그대로 두면 잘못된 계약을 영구화한다. (1) 테스트는 신규 EnumMappingEventCategory(8값) + EnumEventCategory(3값 discrim |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 테스트만 옛 PRD 스냅샷에 동결. minimal 0.5h로 4건 회복. full(3.5h)의 GOP_Restful_Api §EnumDeviceCategory LAMP 추가는 매니저(C# 클라이언트) 동기화 확인이 선행되어야 함 — 결재 안건으로 분리.

---

### G14 — rtsp_uri/rtsp_port 컬럼 삭제 잔존 가정

**우선순위**: P2 / **매니저 영향**: low / **런타임 영향**: none

**원인 (요약)**: PRD_Camera_Urls_JsonB.md (v2.3 Breaking Change, commit a3e411d, 2026-01-07)에서 Camera 모델의 rtsp_uri/rtsp_port 컬럼이 삭제되고 urls JSONB 필드(CameraUrls 스키마)로 통합되었음. app/models/device.py:187 에 urls 컬럼만 존재하고 rtsp_uri/rtsp_port 컬럼은 존재하지 않음. 그러나 tests/test_device_base_model.py 의 Camera 생성자 호출 4곳(line 147-148, 196-197, 237-238, 370-371)이 여전히 rtsp_uri='/stream', rtsp_port=554 kwargs를 전달하여 SQLAlchemy가 'invalid key

**Why this priority**: 운영 코드(models/schemas/routers/Swagger), GIS/VMS/NVR/Speaker 매니저 통합 인터페이스(urls JSONB), GOP_Restful_Api 연동설계 v4.3 모두 일관되게 urls JSONB만 노출. 별도 regression 테스트(test_camera_api_urls.py)가 이미 rtsp_uri/rtsp_port 부재를 능동적으로 검증. 4건 실패는 test 픽스처에 한정된 단순 잔재이며 Camera(...) 호출에서 rtsp_uri='/stream', rtsp_port=554 두 줄만 

**책임 commit (옛 차수)**: `a3e411d (2026-01-07) updated Camera Urls(Jsonb), Event mapping cameras, Speaker Api — Camera 모델에서 rtsp_uri/rtsp_port 제거하고 urls JSONB로 통합한 Breaking Change v2.3. test_device_base_model.py 가 이 마이그레이션 후 업`

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 4건 | 0.25h | low | 즉시 적용 권고. 부채가 테스트 픽스처 한 파일·4곳·8줄에 국한되며, 운영 코드는 PRD v2.3 마이그레이션 완료 상태이므로 테스트만 현 코드 동작에 맞추는 것이 정석이다. urls를 nullable 컬럼으로 두는 모델 설계가 의도된 변경이고 회귀 테스트(test_camera_api_urls.py)가 별도 보호중이므로, kwargs 단순 제거가 가장 안 |
| Full | 4건 | 2.5h | low | 권고: 즉시 수행(저위험·고가치). 부채는 테스트 픽스처 한 파일에 국한되어 있고 운영 코드는 a3e411d에서 이미 정합 완료 상태. 완전 정합 시나리오는 최소 수정 시나리오(4줄 삭제) 대비 +1.5h 추가 공수로 (a) PRD-스키마-테스트 3-축 추적성, (b) OpenAPI example v2.3 정합, (c) 모델 레벨 회귀 방지 테스트, (d) |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 테스트 픽스처 4곳·8줄 단순 제거로 4건 회복(0.25h). full(2.5h)의 OpenAPI example 보강은 v5.x 매니저 통합 시 일괄 정렬.

---

### G15 — 기타 (config / device_version / event base / camera_schema)

**우선순위**: P2 / **매니저 영향**: low / **런타임 영향**: none

**원인 (요약)**: G15는 단일 원인이 아닌 4개 독립 부채의 묶음이며, 공통점은 "스키마/설정이 운영 요구에 맞춰 외부적으로 변경되면서 기존 PRD 기반 테스트가 갱신되지 않은 잔존 부채". 세부 원인:

(1) test_config.py (~3건): commit ba91395/da8b6b6에서 .env.example을 db_monitor 멀티 컨테이너 배포용으로 재작성. 원본(07c79ca: feat: create .env.example)에는 DATABASE_URL/HOST/PORT/DEBUG가 있었으나 현재는 API_DATABASE_URL/MONITOR_DATABASE_URL/SERVER_HOST/SERVER_PORT/POSTGRES_*로 교체되고 DEBUG 항목 자체 삭제. 테스트는 원본 변수명 10종을 모두 .env

**Why this priority**: 실제 운영 API는 모두 정상 동작 (Device.version nullable, Event polymorphic, CameraUrls dict-based, .env 실파일은 자체 운영용 변수 사용). 매니저(GIS/VMS/NVR/Speaker) 통합 영향 없음 — Swagger/OpenAPI 스키마는 현행 dict 기반 CameraUrls 그대로 노출되며 매니저 측은 streams.rtsp.main을 dict 키로 접근하므로 통합에는 dict 기반이 오히려 호환적. config 변경도 db_monitor 배포 요구에 맞춘 의도적 

**책임 commit (옛 차수)**: `07c79ca feat: create .env.example with all required environment variables (원본 — DATABASE_URL/HOST/PORT/DEBUG 포함) / ba91395 updated for notifying to DB monitor (.env.example을 멀티컨테이너 배포용으로 재작성, 테스트 호환성 `

| 시나리오 | 회복 | 분량 | risk | 권고 |
|---|---|---|---|---|
| Minimal | 8건 | 1.5h | low | 권고: 본 minimal 시나리오 채택. 코드(.env.example/schemas/models) 변경 0건으로 운영 배포 형상과 PRD(_Camera_Urls_JsonB v1.0, _Device_Inheritance v1.2)를 그대로 보존하면서 잔존 fail 약 7~8건을 회복한다. 변경은 모두 테스트 파일 한정이며, 라인 단위 수정(required_v |
| Full | 8건 | 14h | medium | G15는 단일 패치로 처리 가능하지만 '4개 독립 부채 + PRD 3종 동시 갱신' 특성상 minimal(잔존 5건 회복) 대비 ROI 임계가 분명히 갈린다. 권고: (1) C1(api-test-server) 단독 수정으로 .env.example 별칭 추가 + test_event_base_model malfunction detail 단언 갱신 + test_ |

**채택 시나리오**: **MINIMAL**

**채택 이유**: 4개 독립 부채 묶음 — 코드 무변경으로 8건 회복(1.5h). full(14h)은 PRD 3종 동시 갱신 + Camera typed StreamGroup 격상이 G01 결정과 연동되어 v5.x로 분리.

---

## 4. 차수별 작업 분산 (recommended_distribution)

| 차수 | 그룹 | 분량 | 근거 |
|---|---|---|---|
| **v4.5 (즉시, 1주차)** | G11, G14, G05, G13, G10, G07 | 5.5h | Low-risk 즉효 정리. G11(EM single DELETE envelope 3줄 코드 패치)·G14(rtsp kwargs 4곳 삭제)·G05(legacy test skip)·G13(enum count 갱신)·G10(is_enable/오타 정정)·G07(role enum 정정+일부 skip). 모두 minimal로 7+4+11+4+7+12 = 45건 회복, 외부 영향 없음, 매니저 통합 영향 0. |
| **v4.6 (2주차, 매니저 통합 직전)** | G09, G12 | 13h | P1 그룹 2건은 full 정합 강제. G09(DetectionLog 1:N actions + ApiResponse envelope)·G12(EM Bulk envelope 3종)는 매니저(C2 db_monitor, C5 Central UI) 통합 시 와이어 계약 변경을 동반하므로 통합 시작 전 PRD/OpenAPI/테스트 3축 동기화 필수. 10+8 = 18건 회복 + 외부 클라이언트 영향 사전 차단. |
| **v4.7 (3주차)** | G02, G03, G08, G15 | 7.3h | Medium-effort minimal 정리. G02(스키마 26건, 2.5h)·G03(envelope 2건 + 후속 4개 서브-그룹 분리 권고)·G08(Camera Preset 11건)·G15(기타 8건). 모두 minimal로 진행하고 G03의 enum/ROI/EventMapping DELETE는 G13/G11과 자연 통합. 19+2+11+8 = 40건 회복. |
| **v5.x (백로그, 매니저 통합 완료 후)** | G01, G04, G06 | 4.5h | OpenAPI 구조 영향이 있는 그룹은 매니저 통합 안정화 후 차장 결재로 별도 처리. G01(CameraUrls nested vs flat 결정)·G04(ServerMetrics 분리 확정 + Central UI latest_metrics 바인딩 동시 작업)·G06(PDF 폰트 OS-aware 정합). 23+14+12 = 49건 회복 가능하나 매니저 동시 작업 필요로 일정 분리. |

---

## 5. Risk Log (잠재 위험)

- **R1**: [매니저 영향 — High] G09 DetectionLog action(single) → actions(list) 계약 변경은 Central UI ViewModel/db_monitor detection-log 컨슈머 동시 수정 필요. OpenAPI 재생성 + 호환 모드(action 키 deprecated 별칭 유지) 2주간 운영 권고.
- **R2**: [매니저 영향 — High] G12 EM Bulk ConfigChangeLog after_state 키 변경(camera_ids/speaker_ids/lamp_ids 추가)은 감사 리포트/매니저 UI 토스트 라벨 직접 영향. config_ids 키 동시 발행으로 호환 모드 유지 필수.
- **R3**: [매니저 영향 — Medium] G07 /api/auth/me 응답 role 케이스('admin' → 'ADMIN') 변경 시 Central UI 권한 분기 코드 회귀 가능. minimal 시나리오는 이 변경을 보류하므로 회피.
- **R4**: [매니저 영향 — Medium] G04 Server 인라인 메트릭이 db_monitor v1.6 시점 인제스트 경로에 잔존할 가능성 — db_monitor 코드 grep 후 v5.x 통합 시 동시 전환 필요.
- **R5**: [사이드 이펙트 — Medium] G02 minimal 시 잔여 7건은 conftest test_db fixture의 SQLAlchemy 환경 의존 — 도커 환경 재실행 후 진성 실패 재판정 필요.
- **R6**: [사이드 이펙트 — Low] G06 minimal은 Windows 단정 강도 감소 트레이드오프. 향후 OS별 분기 회귀 가드는 별도 작업.
- **R7**: [데이터 손실 — None] 모든 minimal 시나리오는 코드/DB 변경 0건이므로 운영 데이터 손실 위험 없음.
- **R8**: [데이터 손실 — Low] G09/G12 full은 OpenAPI 스키마만 변경, DB 마이그레이션 없음. 단 ActionEvent.from_event_id UNIQUE 제약 점검 필요(1:N 허용 확인).
- **R9**: [CI 신호 손실 — Low] G05/G07에서 8+7 = 15건 skip 처리로 'skipped' 카운트 증가. reason 문구에 superseded PRD 명시로 추적성 확보.
- **R10**: [명세-구현 drift — Medium] G01 minimal 채택 시 PRD v1.0의 nested 디자인과 실 구현 simplified dict 간 차이 잔존 — PRD에 'flat dict simplified 결정' 1줄 명시 권고.

---

## 6. Open Decisions (차장 결재 필요)

- **D1**: [결재-1] ApiResponse envelope 표준화 확정 — data=[...]+pagination 사이드카(현행 §9.7.2) vs data={logs,total,page,limit} 통합. G03/G09 정합 방향 확정 필요. 권고: 현행 유지(스펙 일치).
- **D2**: [결재-2] EnumDeviceCategory LAMP 매니저(C# Ironwall.Dotnet.Libraries.Enums) 동기화 확인 — NATS payload 'lamp' 문자열 round-trip 검증. G13 full 시나리오 진행 조건.
- **D3**: [결재-3] Server 인라인 메트릭 v2.9 분리 확정 — db_monitor 인제스트 경로를 POST /api/servers/{id}/metrics로 전환할지 여부. G04 v5.x 통합 작업 선행 조건.
- **D4**: [결재-4] DetectionLog 1:1 → 1:N actions 계약 변경 공식화 — PRD_DetectionLog_API.md v1.1 + Central UI ViewModel 동시 수정 일정. G09 full 진행 조건.
- **D5**: [결재-5] ROICreate.points 필수화 정책 확정 — '빈 ROI 생성 후 points 추가' 워크플로 폐기 vs 유지. 매니저 UI 폼 흐름 변경 영향. G08 full 진행 조건.
- **D6**: [결재-추가] SpeakerNestedResponse.category_device 제거(SPEC-6.1 Nested 일관 적용) — NATS 컨슈머 grep 결과 외부 사용 없을 시 진행. G10 full 조건.
- **D7**: [결재-추가] G15 .env.example을 운영 배포용 + 단일 컨테이너 폴백 듀얼 모드로 운영할지 여부. minimal 채택 시 보류 가능.

---

## 7. Rollback Strategy

"3단계 롤백 전략: (1) 그룹별 단일 commit 원칙 — 각 그룹의 minimal/full 정정을 독립 commit으로 분리(Tidy First: 구조 변경과 행위 변경 별도 commit). 사고 시 `git revert <group-commit>`로 그룹 단위 원복 가능. (2) 차수별 태그 — v4.5/v4.6/v4.7 완료 시점마다 `v4.5-stable`, `v4.6-stable` 태그 부여. v4.6 매니저 통합 후 사고 시 `git reset --hard v4.5-stable`로 통합 직전 상태 복귀. (3) v4.4-final-stable 마스터 백업 — 현재 시점(7aced94 docs v4.3 + 081c8ca audit revert)을 `v4.4-final-stable` 태그로 박제. 전 그룹 정합 중 비상 시 `git checkout v4.4-final-stable` 즉시 가능. P1 그룹(G09/G12)은 full 시나리오 머지 전 OpenAPI 스냅샷(`temp_openapi.json`)을 백업하여 매니저 SDK 재생성 시 diff 비교용으로 보존. ConfigChangeLog 키 변경(G12)은 호환 모드(config_ids + resource_ids 동시 발행)로 무중단 롤백 가능 — DB 데이터 손실 0건 보장. legacy test skip 처리(G05/G07)는 unskip만으로 즉시 복원."

---

## 8. 검증 절차

1. **사전 안전**: `v4.4-final-stable` 태그 보호 (이미 적용)
2. **그룹별 commit 단위 적용**: 각 그룹마다 별도 commit + 태그 (예: `pre-v45-G01`, `pre-v45-G02`)
3. **각 그룹 적용 후 pytest 회귀 0건 확인**
4. **실 API 시나리오 회귀** (Camera/Lamp/Server/EM GET/POST/PATCH/DELETE)
5. **OpenAPI 노출 회귀** (Swagger UI ApiSingleResponse 141건 유지)
6. **매니저 통합 가이드 갱신** (`docs/v45_sync_guide.md` 신설)

---

## 9. 작업 인벤토리 raw 데이터

- **분석 raw**: `tasks/w2uvtdbg0.output` (266KB, 46 agent 결과)
- **Workflow run ID**: `wf_a6e08647-009`
- **Subagent token 사용량**: 3,492,386 token
- **Tool 호출**: 935건
- **소요 시간**: 16분

---

**문서 버전**: v4.5 (PRD 본문)
**최종 업데이트**: 2026-06-19