# PRD: v4.6 — Critical Mismatch 10건 정정 + Camera Preset 감시금지구역 신설

> **작성일**: 2026-06-19 (오늘 하루 1차수)
> **차수**: v4.6
> **선행 안전점**: `v4.5-final-stable` (commit e7a611e)
> **작성 도구**: Workflow (11 agent Critical + 9 agent Preset)

---

## 1. Executive Summary

v4.6 차수에서 Critical Mismatch 10건(P0 1건 + P1 9건)을 일괄 정정한다. 총 공수 9.5h(약 1.5일)로 압축 가능하며, M01 P0 핫픽스(server_categories.py 500 에러)를 선행한 뒤 명세 정정 8건(M02·M03·M05·M06·M08·M09·M10 + M04 부분)을 병렬 처리하고, 마지막으로 코드 정정 2건(M04 enclosure_metrics envelope 재작성, M07 system-events response_model 부착)을 매니저 영향 통제 하에 순차 적용한다. 전체 변경 중 코드 수정은 3개 파일(server_categories.py·enclosure_metrics.py·servers.py)에 국한되며 명세 정정 7건은 backward-compatible, 매니저 측 강제 마이그레이션은 M02/M03/M04 3건뿐이다. 완료 후 GOP_Restful_Api_연동설계.md ↔ 코드 ↔ Swagger UI 3-way 정합 100% 달성을 목표로 하며, 차장 결재가 필요한 핵심 의사결정 9건(특히 M04 item shape, M02/M03 매니저 마이그레이션 일정, M07 명세 envelope 표준화)이 v4.7 진입 전 종결되어야 한다.

- **총 작업량**: Critical 9.5h + Camera Preset (별도 산정 대기)
- **Open Decisions**: 21건
- **Risks**: 15건

---

## 2. Critical 10건 — 작업 순서

| Step | ID | P | 작업 | 분량 | risk | depends_on |
|---|---|---|---|---|---|---|
| 1 | **M01** | P0 | P0 핫픽스 — app/routers/server_categories.py:123-140의 ServerResponse 생성문에서 cpu_usag | 0.5h | low | [] |
| 2 | **M02** | P1 | 명세 정정 — GOP_Restful_Api_연동설계.md §6.5.1 (목록 조회) 응답 예시의 action 단수 객체를 actions 배열로  | 0.5h | low | [] |
| 3 | **M03** | P1 | 명세 정정 — §6.5.2 (단건 조회) 본문 'action 필드 (ActionNested 또는 null)' → 'actions 필드 (list | 0.5h | low | ['M02'] |
| 4 | **M05** | P1 | 명세 정정 — §8.6.3 GET /api/servers/{id}/metrics/latest 응답 예시를 ServerMetricsLatestRe | 0.5h | low | [] |
| 5 | **M06** | P1 | 명세 정정 — §10.4.4 PDF 다운로드 응답을 JSON envelope에서 application/pdf 바이너리 스트림 + Content- | 0.5h | low | [] |
| 6 | **M08** | P1 | 명세 정정 — §6.2.5 Malfunction PUT Request Example/Body에서 action_reported 필드 제거 (v2. | 0.5h | low | [] |
| 7 | **M09** | P1 | 명세 정정 — §6.4.2 GET /api/events/actions의 start_date/end_date를 required→optional로  | 1.5h | low | [] |
| 8 | **M10** | P1 | 명세 정정 — §6.4.5 PUT /api/events/actions/{id} Request Example/Body에 type_event, fr | 0.5h | low | [] |
| 9 | **M07** | P1 | 코드 정정 — app/routers/servers.py:191 GET /api/servers/{id}/system-events 데코레이터에 re | 1.5h | low | ['M01'] |
| 10 | **M04** | P1 | 코드 정정 — app/routers/enclosure_metrics.py:328-367 GET /api/enclosure-metrics를 명세  | 3h | high | ['M07'] |

## 3. Mismatch별 정정 본문

### M01 (P0) — GET /api/servers/categories/{category_id}는 ServerResponse 생성 시 Server 모델에 존재하지 않

**현 상태**: app/routers/server_categories.py:123-140의 ServerResponse 생성문이 Server 모델 인스턴스에서 cpu_usage, ram_usage, disk_usage, network_throughput을 읽으려 시도. 해당 컬럼은 Server 모델(app/models/server.py:67-102)에 존재하지 않으며 ServerMetrics(app/models/server.py:105-153)에 1:N로 분리됨. 실제 호출 시 `AttributeError: 'Server' object has no 

**목표 상태**: 동일 파일의 ServerResponse 생성문이 app/routers/servers.py:26-41의 _server_to_response 헬퍼와 동일한 필드 셋(id, category_id, name, status, ip_address, port, hostname, user_name, user_password, threshold_config, created_at, updated_at)을 사용. 500 제거, test_get_category_with_servers 통과, 응답 스키마와 일치(user_name/user_password/

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: backward-compatible 평가: 응답 키 셋이 변경됨 — cpu_usage/ram_usage/disk_usage/network_throughput 4개 키가 사라지고 user_name/user_password/threshold_config 3개 키가 추가됨. 단, 현재 코드는 100% 500을 반환하므로 실제로 사라지는 데이터는 없음(매니저 측에

**Code Changes**:
- `c:\workspace_python\api-test-server\app\routers\server_categories.py` @ lines 123-140 (ServerResponse 생성 블록)

**검증 절차**:
- 1) pytest 단위: `python -m pytest tests/test_server_categories_router.py::TestServerCategoryGetById::test_get_category_with_servers -x` → PASSED 확인 (현재 ERROR)
- 2) 회귀 묶음: `python -m pytest tests/test_server_categories_router.py tests/test_servers_router.py --tb=short` → 전체 통과 확인
- 3) Swagger UI: http://localhost:8000/docs → `GET /api/servers/categories/{category_id}` 실행. 카테고리에 server를 1건 이상 시드 후 200 응답 + data.servers[0]에 user_name/user_password/threshold_config 키 노출 확인
- 4) curl: `curl -s http://localhost:8000/api/servers/categories/1 | jq '.data.servers[0] | keys'` → cpu_usage/ram_usage/disk_usage/network_throughput 키 부재, user_name/user_password/threshold_config 포함 확

---

### M02 (P1) — GOP_Restful_Api_연동설계.md §6.5.1 / §6.5.2 의 Detection Log 응답 스키마가 `action`(1:1, 단일

**현 상태**: 명세 §6.5.1 응답 예시(line 9543~9549)에 `"action": { id, content, user, created_at, updated_at }` 단일 객체로 기술. 두번째 예시(line 9561)에 `"action": null`. §6.5.2 본문(line 9577)에 `+ action 필드 (ActionNested 또는 null)`로 기술. 코드는 `actions: list[ActionNested] = Field(default_factory=list)` 로 1:N 리스트 반환 (event.py:406). _bui

**목표 상태**: 명세 §6.5.1 응답 예시에서 단일 `action` 객체를 `actions` 배열로 정정 — 미조치 행은 `"actions": []`, 조치 1건은 `"actions": [{...}]`, 다건 조치도 표현 가능. §6.5.2 본문도 `+ actions 필드 (ActionNested 리스트, 미조치 시 빈 리스트)`로 정정. 본문 도입부 "DetectionEvent 기준 LEFT JOIN ActionEvent" 표현은 유지하되 1:N 관계임을 보강 메모로 추가. 매니저(GIS/VMS/NVR/Speaker)는 actions[0]을 기

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: 매니저(GIS/VMS/NVR/Speaker) 통합 영향 — **NOT backward-compatible** (필드명 `action` → `actions`, 타입 단일 객체 → 배열). 단, 코드는 이미 v2.0 시점부터 1:N 반환 중이므로 명세만 뒤늦게 따라가는 형국. 매니저측 영향 매트릭스: (1) GIS 통제 UI — DetectionLog 화면에서

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §6.5 도입부 (line 9492~9493)`
- `GOP_Restful_Api_연동설계.md §6.5.1 응답 예시 첫번째 행 (line 9543~9549)`
- `GOP_Restful_Api_연동설계.md §6.5.1 응답 예시 두번째 행 (line 9561)`
- `GOP_Restful_Api_연동설계.md §6.5.2 응답 본문 설명 (line 9576~9577)`

**검증 절차**:
- 1. git diff GOP_Restful_Api_연동설계.md — §6.5 4곳 정정만 보이고 다른 섹션 변경 없는지 확인
- 2. Swagger UI(http://localhost:8000/docs)에서 GET /api/detection-logs 응답 스키마 확인 — `actions: array[ActionNested]`로 노출되는지
- 3. curl -u admin:admin123 http://localhost:8000/api/detection-logs?limit=2 실행 — 조치 1건 row는 actions=[{...}], 미조치 row는 actions=[] 반환 확인
- 4. curl -u admin:admin123 http://localhost:8000/api/detection-logs/{event_id} 단건 조회 — actions 필드(리스트) 확인

---

### M03 (P1) — GET /api/detection-logs/{event_id} 응답 스키마 1:N drift 정정 — 명세는 action 단수(ActionNes

**현 상태**: §6.5.2 본문 "DetectionEventResponse 전체 필드 + `action` 필드 (ActionNested 또는 null)" — 단수 action, ActionNested|null 1:1 구조로 기술. 실제 app/routers/detection_logs.py:263-308 get_detection_log()는 DetectionLogResponse.actions: list[ActionNested] = Field(default_factory=list)로 1:N 빈 리스트 반환(app/schemas/event.py:406

**목표 상태**: §6.5.2 본문을 "DetectionEventResponse 전체 필드 + `actions` 필드 (list[ActionNested], 조치보고 없으면 빈 리스트 [])"로 정정. PRD_ActionEvent_1N_Refactoring v2.0 결론(1 Detection : N Action) 반영. 응답 스키마 ApiSingleResponse[DetectionLogResponse] 표기는 유지. 매니저(GIS/VMS/NVR/Speaker)는 actions[0] 또는 actions.length로 1차 조치 + 추가 조치 표시 가능.

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: backward-compatible 아님 (응답 구조 변경: 단수 action → 복수 actions 배열). 단 실제 서버는 이미 v4.x부터 actions를 반환 중이므로 매니저 측이 명세대로 단수 `action`을 구현했다면 현재 시점 이미 깨진 상태(spec drift). 정정 후 영향: ① GIS/VMS/NVR/Speaker 매니저 모두 응답 파서

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §6.5.2 Detection Log 단건 조회 (line 9576-9577)`

**검증 절차**:
- 1) 명세 변경 후 grep 확인: Grep '`action` 필드' GOP_Restful_Api_연동설계.md §6.5 영역 — 0건이어야 함
- 2) curl로 실측 응답 확인: curl -s -H 'Authorization: Bearer <token>' http://localhost:8000/api/detection-logs/1 | jq '.data | keys' — `actions` 키 존재, `action` 키 없음 확인
- 3) 빈 조치 케이스 확인: 미조치 DetectionEvent로 curl — `"actions": []` 반환 확인 (null 아님)
- 4) 다중 조치 케이스 확인: ActionEvent 2건 이상 연결된 DetectionEvent로 curl — actions 배열에 2개 이상 객체 반환 확인

---

### M04 (P1) — GET /api/enclosure-metrics 응답 envelope이 명세(§5.5.13)와 불일치. 코드는 enclosure 그룹화된 fla

**현 상태**: app/routers/enclosure_metrics.py:333-367 `get_all_enclosure_metrics`가 Query 파라미터 없이 모든 Enclosure를 순회하여 각 함체당 최신 1건의 메트릭을 묶은 객체(`{enclosure_id, enclosure_name, latest_metrics}`)를 flat list로 반환. envelope은 `{success, message, data: [...]}` 3-키 단순 구조. pagination 키 없음, total 없음, 필터 없음. 기존 tests/test_encl

**목표 상태**: 명세 §5.5.13(라인 4918-4958)에 따라 (1) Query Parameters 5종 수용: page(default 1), limit(default 50), enclosure_id(optional 필터), from_date/to_date(ISO 8601 범위 필터); (2) flat metric row 반환 — id, enclosure_id, temperature, humidity, voltage, current, created_at; (3) envelope을 `{success, message, data: {items: [

**Effort**: 3h / **Risk**: high / **매니저 영향**: Backward-INCOMPATIBLE 변경. (1) 응답 최상위 키 구조가 `data: [array]` → `data: {items, total}` + 신규 `pagination` 블록으로 바뀜 — 클라이언트의 JSON 파서 전수 수정 필요. (2) item 필드가 `{enclosure_id, enclosure_name, latest_metrics{...

**Code Changes**:
- `app/routers/enclosure_metrics.py` @ 328-367 (list_router GET handler)

**검증 절차**:
- pytest tests/test_enclosure_metrics.py::TestEnclosureMetricsListAPI -v — 기존 5건 실패 확인(의도된 회귀). 새 envelope에 맞게 테스트 수정 후 재실행하여 5건 전부 green.
- curl 'http://localhost:8000/api/enclosure-metrics?page=1&limit=10' | jq '.data.items, .data.total, .pagination' — items 배열, total 정수, pagination{page,limit,total_pages} 3-키 확인
- curl 'http://localhost:8000/api/enclosure-metrics?enclosure_id=1&from_date=2026-01-01T00:00:00Z&to_date=2026-12-31T23:59:59Z' — 필터 4종 동작 확인
- Swagger UI(/docs)에서 GET /api/enclosure-metrics가 5개 Query Parameter를 노출하는지 확인

---

### M05 (P1) — GOP_Restful_Api_연동설계.md §8.6.3 GET /api/servers/{server_id}/metrics/latest 응답 본문

**현 상태**: §8.6.3 명세(라인 13564-13585): data.metrics 단일 객체와 data.threshold_config 객체를 반환한다고 기술. 그러나 실제 코드(app/routers/server_metrics.py:328-336)는 ServerMetricsLatestResponse 모델로 {server_id, server_name, latest_metrics}를 반환하며, latest_metrics는 ServerMetricsResponse(threshold_exceeded 포함) 또는 null. threshold_config는

**목표 상태**: §8.6.3 명세 응답 본문을 실제 코드 반환 구조로 정정: {success, message, data:{server_id, server_name, latest_metrics:{id, server_id, cpu_usage, ram_usage, disk_usage, network_*, created_at, threshold_exceeded}}}. latest_metrics가 null인 경우(메트릭 없음) 명시. threshold_config는 응답 객체에서 제거(서버 설정 조회는 §8.x.x Server CRUD 별도). 코드 무변경

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: 매니저 호환: backward-compatible (코드 무변경, 매니저 런타임 영향 0). GIS/VMS/NVR/Speaker 매니저는 메트릭 latest 엔드포인트를 직접 호출하지 않음(서버 자체 리소스 모니터링용). Ironwall.Central UI ResourceMonitor만 잠재 소비자이며, 이미 실제 코드 응답(latest_metrics 키)

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §8.6.3 (라인 13564-13585)`

**검증 절차**:
- 1) 정정 라인 확인: Read c:/workspace_python/api-test-server/GOP_Restful_Api_연동설계.md offset=13560 limit=40 — §8.6.3 본문이 새 스키마로 갱신되었는지 시각 확인
- 2) 실측 응답 캡처(로컬 정상 환경): curl -s -H 'Authorization: Bearer <token>' http://localhost:8000/api/servers/1/metrics/latest | jq '.data | keys' → ['latest_metrics','server_id','server_name'] 출력 확인
- 3) Swagger UI 교차확인: http://localhost:8000/docs#/servers/get_server_metrics_latest → 응답 스키마 ServerMetricsLatestResponse 키 셋이 정정된 명세와 일치
- 4) 메트릭 0건 케이스: 신규 서버 INSERT 직후 동일 GET 호출 → data.latest_metrics == null 확인

---

### M06 (P1) — §10.4.4 다운로드 응답을 JSON envelope에서 PDF 바이너리 스트림(application/pdf, Content-Dispositi

**현 상태**: 명세 §10.4.4는 200 응답을 `ApiResponse` JSON envelope (success/message/data{id, pdf_file_path}) 로 기술. 실제 코드 app/routers/reports.py:491-530 `download_report`는 `FileResponse(path=..., media_type="application/pdf")` 를 반환하며 `Content-Disposition: attachment; filename="report_{id}.pdf"; filename*=UTF-8''<encode

**목표 상태**: 명세 §10.4.4가 다음 사실을 반영: (1) 200 응답은 `application/pdf` 바이너리 스트림이며 본문은 JSON 아님, (2) `Content-Disposition: attachment; filename="report_{id}.pdf"; filename*=UTF-8''<URL-encoded title>.pdf` 헤더 명시, (3) 400/404 에러 본문은 FastAPI `HTTPException` 표준 `{"detail": "..."}` 형태 (현재 다른 §과 동일 패턴), (4) 클라이언트 가이드라인 한 줄 추

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: 매니저 호환 backward-compatible 100% — 코드 변경 0건이므로 SVMS/GIS/VMS/NVR/Speaker 매니저 런타임 동작 무변경. 단, 매니저 측 구현자가 과거 잘못된 명세(JSON envelope)를 보고 `JsonConvert.DeserializeObject<ApiResponse<DownloadDto>>` 로 파싱하도록 구현했다

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §10.4.4 GET /api/reports/generations/{id}/download (lines 15135-15160)`

**검증 절차**:
- curl -v http://localhost:8000/api/reports/generations/{COMPLETED_ID}/download -o /tmp/r.pdf 로 받아 `Content-Type: application/pdf` 헤더와 `Content-Disposition: attachment; filename="report_*.pdf"; filename
- curl -v http://localhost:8000/api/reports/generations/{NOT_COMPLETED_ID}/download 로 HTTP 400 + `{"detail":"Report is not COMPLETED yet"}` 본문 확인 (ApiResponse envelope 아님 재확인)
- curl -v http://localhost:8000/api/reports/generations/999999/download 로 HTTP 404 + `{"detail":"Report generation not found"}` 확인
- Swagger UI (/docs) 에서 GET /api/reports/generations/{id}/download Execute → Response body가 'Download file' 링크로 표시되는지 확인 (JSON 표시되면 명세-코드 불일치 재발)

---

### M07 (P1) — GET /api/servers/{server_id}/system-events 가 (1) response_model 미부착, (2) 잘못된 env

**현 상태**: app/routers/servers.py:191-250 — `@router.get("/{server_id}/system-events")` 데코레이터에 response_model 없음. 함수 본문 line 246-250 에서 `ApiSingleResponse(success, message, data=event_responses)` 반환. event_responses 는 dict 의 list 로 직접 구성(line 229-244). 페이지네이션 정보(total, total_pages)는 응답에 포함되지 않음. 명세상 필수 쿼리 seve

**목표 상태**: app/routers/servers.py:191 데코레이터를 `@router.get("/{server_id}/system-events", response_model=ApiResponse[list[SystemEventResponse]])` 로 변경. severity / acknowledged 쿼리 파라미터 추가. total 카운트 산출 + PaginationMeta 구성. 응답 data 는 List[SystemEventResponse](기존 dict 수동 매핑을 SystemEventResponse(...) 생성으로 교체). 명세 §8

**Effort**: 1.5h / **Risk**: low / **매니저 영향**: backward-compatible. (1) 응답 최상위 키 success/message/data/meta 동일 유지. (2) data 는 종전과 같이 `list[event]` — items 래핑 도입하지 않음(매니저 파서 무수정). (3) 신규 추가는 `pagination` 객체와 `meta` 의 timestamp/request_id — 매니저 측에서 미

**Code Changes**:
- `app/routers/servers.py` @ line 15-21 (imports)
- `app/routers/servers.py` @ line 191-250 (get_server_system_events 전체)
**Spec Changes**:
- `§8.3.7 서버별 시스템 이벤트 조회 — Response (200 OK)`

**검증 절차**:
- 로컬에서 `pytest tests/test_system_event.py -k 'server_system_events' -v` 실행 → 기존 3건(test_get_server_system_events / test_get_server_system_events_empty / test_server_system_events_has_meta) 전부 green 확인. 
- Swagger UI 에서 `GET /api/servers/{server_id}/system-events` 열어 Response Schema 가 `ApiResponse_list_SystemEventResponse_` 로 표시되는지 확인 — 매니저 측 OpenAPI 클라이언트 생성 가능.
- curl 검증: `curl -s http://localhost:8000/api/servers/1/system-events?page=1&limit=10&severity=WARNING | jq '{success, dataCount: (.data|length), pagination, meta_keys: (.meta|keys)}'` → success=true, p
- severity 필터: 동일 서버에 INFO/WARNING 두 건 시드 후 `?severity=WARNING` 호출 시 1건만 반환되는지 확인.

---

### M08 (P1) — PUT /api/events/malfunctions/{id} 명세 §6.2.5 Request Example/Request Body에 action

**현 상태**: GOP_Restful_Api_연동설계.md §6.2.5 (line 8277~8361)의 Request Example(line 8289~8300)과 Request Body(line 8306~8319)에 `action_reported: "True"` 필드가 포함되어 있음. 그러나 app/schemas/event.py:175~206의 MalfunctionEventCreate DTO에는 action_reported 필드가 없으며(PRD v2.8 적용), app/routers/malfunctions.py:534~626 replace_malf

**목표 상태**: §6.2.5의 Request Example과 Request Body에서 `action_reported` 필드 제거. POST §6.2.3과 동일한 v2.8 자동 관리 주석을 추가하여 매니저가 ActionEvent CRUD를 통해서만 action_reported가 변경됨을 명확화. Response Example의 action_reported는 유지(응답 필드이므로 변경 없음). DELETE §6.2.6의 기존 자동 복원 설명(line 8378~8380)과 일관되게 유지.

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: Backward-compatible. (1) 응답 스키마 무변경 — 매니저(GIS/VMS/NVR/Speaker) 모두 응답에서 action_reported를 그대로 읽을 수 있음. (2) 요청 측: 현재 코드는 요청 본문의 action_reported를 Pydantic이 자동 무시(MalfunctionEventCreate에 필드 없음)하므로, 기존 매니저가

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §6.2.5 Request Example (line 8289~8300)`
- `GOP_Restful_Api_연동설계.md §6.2.5 Request Body (line 8305~8319)`

**검증 절차**:
- 1) 명세 diff 검토 — git diff GOP_Restful_Api_연동설계.md로 §6.2.5 두 블록(Request Example, Request Body) 변경 확인, Response Example/Endpoint/Error 섹션은 무변경 확인
- 2) POST §6.2.3과 일관성 확인 — POST Request Body에 action_reported 없음(현재 line 8140~8153) vs PUT 정정본 모두 action_reported 없음, v2.8 주석 패턴 일치
- 3) Detection PUT §6.1.5와 일관성 메모(별도 mismatch로 추적) — 동일한 누락 패턴이 §6.1.5에도 존재함을 부록/CHANGELOG에 명시
- 4) pytest 회귀 — pytest tests/ -k 'malfunction and put' 또는 tests/test_malfunctions_put.py 실행하여 기존 PUT 동작(action_reported 미포함 본문으로도 200 OK, action_reported 응답 유지) 확인. v2.8 변경 이후 추가된 테스트가 회귀 없음을 보장

---

### M09 (P1) — GET /api/events/actions §6.4.2 명세 정정 — start_date/end_date를 required → optional로

**현 상태**: [명세 §6.4.2] start_date/end_date가 required로 표기되어 있고 from_event_id 필터 자체가 누락. 422 에러 예시에는 "start_date Invalid datetime format"이 등장하나 코드는 default=None이므로 미지정 시 검증 자체가 발생하지 않음. [코드 actions.py:202-245] page/limit/user/from_event_id/start_date/end_date 6개 쿼리 파라미터 모두 Optional이며 5개 필터 분기(if not None)로 동작. A

**목표 상태**: [명세 §6.4.2] start_date/end_date를 optional로 표기, from_event_id (int, optional) 라인 추가, 잘못된 422 예시(end_date > start_date 검증)는 현재 코드에 없으므로 제거 또는 "참고용 권고"로 강등. [코드] 변경 없음(코드가 진실 원본). 결과: 매니저들이 from_event_id=1002 로 단일 원본 이벤트의 조치 이력 1:N 조회 가능, 날짜 미지정 시 전체 조회 가능(페이지네이션으로 제한).

**Effort**: 1.5h / **Risk**: low / **매니저 영향**: 매니저 통합 영향: **backward-compatible (호환 깨짐 없음)**. (1) GIS/VMS/NVR/Speaker 매니저가 기존처럼 start_date/end_date를 항상 전송하던 호출은 변경 없이 정상 동작. (2) 신규로 from_event_id 단독 호출이 명세상 합법화되어 매니저들이 ActionEvent 1:N 조회(특정 침입/장애 

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §6.4.2 Query Parameters (lines 9033-9038)`
- `GOP_Restful_Api_연동설계.md §6.4.2 Request Example (lines 9040-9046)`
- `GOP_Restful_Api_연동설계.md §6.4.2 Error Response 422 (lines 9138-9151)`

**검증 절차**:
- [명세 검증] Read GOP_Restful_Api_연동설계.md offset=9029 limit=130 — §6.4.2 본문이 Optional 표기 + from_event_id 라인 + 두 번째 Request Example 포함하는지 확인
- [코드 회귀 없음] cd c:/workspace_python/api-test-server && python -m pytest tests/ -k action_event -v — 기존 ActionEvent 테스트(목록/단건/생성/수정/삭제) 모두 PASS 확인 (변경한 것은 명세뿐이므로 코드 테스트는 영향 없음)
- [Swagger UI 일치] uvicorn app.main:app --reload 후 http://localhost:8000/docs#/Action%20Events/get_action_events 의 6개 파라미터(page/limit/user/from_event_id/start_date/end_date)가 모두 Optional로 표시되고 from_event
- [curl 검증 1 — 날짜 미지정 전체 조회] curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/events/actions | jq '.pagination.total' — 422 아닌 200 응답 확인

---

### M10 (P1) — PUT /api/events/actions/{event_id} — 명세 §6.4.5 Request Example/Body가 2필드(content

**현 상태**: GOP_Restful_Api_연동설계.md §6.4.5 (line 9308~9332): "Action Event 수정 (전체)" 제목과 PUT 메서드가 일치하지만 Request Example/Body 예시는 content, user 2필드뿐. 매니저(GIS/VMS) 구현자는 예시대로 보내면 422 Unprocessable Entity(type_event/from_event_id missing)을 받게 됨. 실제 코드 app/routers/actions.py:553-623 replace_action_event는 ActionEventC

**목표 상태**: §6.4.5 Request Example/Body가 type_event, content, user, from_event_id 4필드를 모두 표기. "**Request Body** (전체 업데이트)" 헤딩 옆에 "모든 필드 필수 (PUT = 전체 교체)" 단서 추가. PATCH(부분 수정)는 별도 §섹션 또는 동일 §섹션 보조 노트로 안내(차장 결재 시 결정). 매니저 구현자가 예시 페이로드를 그대로 복사해도 200 OK를 받음.

**Effort**: 0.5h / **Risk**: low / **매니저 영향**: GIS/VMS/NVR/Speaker 매니저 전부 backward-compatible. 코드/응답 스키마 변경 0건이므로 매니저 송신/수신 코드를 손댈 필요 없음. 단, 명세 예시를 보고 구현 중인 매니저(현재 2필드만 보내 422를 받던 측)는 본 정정 후 4필드 송신으로 전환해야 정상 동작 — 이건 명세 정정의 의도된 효과(매니저 구현자에게 올바른 페이로

**Spec Changes**:
- `GOP_Restful_Api_연동설계.md §6.4.5 — Request Example (line 9320~9323)`
- `GOP_Restful_Api_연동설계.md §6.4.5 — Request Body 블록 (line 9326~9332)`

**검증 절차**:
- 1) git diff GOP_Restful_Api_연동설계.md로 §6.4.5 변경 라인 4개(Request Example JSON 2개, Body JSON 1개, 표 1개) 확인
- 2) openapi_snapshot.json에서 PUT /api/events/actions/{event_id} 의 requestBody.required = ['type_event','content','user','from_event_id'] 4개와 일치하는지 jq로 검증
- 3) curl -X PUT http://localhost:8000/api/events/actions/4001 -H 'Content-Type: application/json' -d '{"content":"x","user":"y"}' → 422 응답 + missing field 메시지에 type_event, from_event_id 포함 (명세 정정 전 예시가
- 4) curl 동일 URL에 정정된 4필드 페이로드 → 200 OK + ActionEventResponse 반환 (data.type_event, data.from_event.id 채워짐)

---

## 4. Integration Strategy

**그룹별 분리 commit + 단일 PR(v4.6-mismatch-batch) 머지** 전략 채택. (1) Commit #1 (M01 P0 핫픽스, 0.5h): 단독 commit으로 즉시 main 머지 — 500 에러 차단이 최우선. (2) Commit #2 (M02+M03 명세 정정, 1h): 동일 §6.5 섹션 1:N drift 일괄 정정, 단일 commit으로 일관성 보장. (3) Commit #3~6 (M05, M06, M08, M09, M10 명세 정정, 3.5h): 각 mismatch별 독립 commit — 차장 리뷰 가독성 우선, 사고 시 개별 revert 용이. (4) Commit #7 (M07 코드 정정 + §8.3.7 명세 동반 정정, 1.5h): 코드와 명세를 한 commit에 묶어 3-way 정합 유지. (5) Commit #8 (M04 코드 정정 + §5.5.13 잠재 동반 정정, 3h): 차장 결재(item shape) 완료 후 단독 commit, 기존 pytest 5건 재작성과 동시 진행. Tidy First 원칙 준수 — 구조적 변경(명세 정정 7건)과 행위 변경(코드 정정 3건: M01·M04·M07)을 commit 메시지 prefix(`docs:` vs `fix:`)로 명확히 구분. 전체 8개 commit을 단일 feature 브랜치(`feature/v4.6-critical-mismatch-10`)에 누적 후 PR로 차장 결재 → main 머지. 매니저(GIS/VMS/NVR/Speaker) 공지는 PR 머지 직후 NATS 정책 채널 + 주간 회의에서 일괄 통보 (M02/M03/M04 3건은 매니저 측 마이그레이션 동반 필요).

## 5. Rollback Strategy

**v4.4-final-stable 태그 + 그룹별 commit 기반 단계적 롤백** 전략. (1) **선행 안전망**: v4.6 작업 시작 전 `git tag v4.4-final-stable` (현재 e7a611e 시점)로 기준점 고정 — Phase 9 회복 직후 안정 상태. (2) **롤백 우선순위 매트릭스**: 우선 단일 commit revert(git revert <SHA>) → 그룹 commit 일괄 revert(M02+M03) → 차수 전체 rollback(`git reset --hard v4.4-final-stable`은 최후 수단). (3) **commit별 롤백 영향 범위**: ①M01: 라우터 1파일 1블록, 즉시 복귀 가능, 사고 시 500 에러 재발 — 대안은 명세 측에서 4 메트릭 필드를 ServerMetrics join으로 다시 노출(별도 PRD). ②M02~M10 명세 정정 7건: 문서만 변경, 런타임 영향 0, revert 즉시 복구. ③M07 코드 정정: backward-compatible(매니저 응답 파서 무수정), 단일 파일 단일 commit revert로 복구. ④M04 코드 정정: backward-INCOMPATIBLE — 매니저 측 envelope 파서 동시 롤백 필요, 가장 위험. (4) **사고 시 검증 순서**: ①`pytest tests/` 전체 실행으로 회귀 확인, ②Swagger UI(/docs)로 응답 스키마 시각 검증, ③매니저 4종 dry-run 호출로 통합 영향 확인. (5) **롤백 후 의무 절차**: `docs/memory/session-context.md`에 롤백 사유/SHA/영향 범위 기록 + 차장 결재 재상정 + 매니저 측 통보(NATS 정책 채널). (6) **DB/마이그레이션 영향**: 10건 모두 DB 스키마 변경 없음 — 마이그레이션 rollback 불요, 데이터 무결성 영향 0.

## 6. Open Decisions (19건)

- [차장 결재 #1 — M01] ServerResponse에서 분리된 cpu_usage/ram_usage/disk_usage/network_throughput 4개 메트릭을 카테고리 상세 응답에 다시 포함시킬지 — 포함 시 ServerMetrics 최신 1건 join 정책 별도 PRD 필요. 현 차수 권고: 500 제거에 한정
- [차장 결재 #2 — M02/M03] 매니저(GIS/VMS/NVR/Speaker) 4종 1:N 마이그레이션 일정 — 명세 정정과 동시에 actions 배열 처리 PR 요청 vs 명세만 선반영 + 매니저는 actions[-1] 폴백 유지. 권고: 즉시 통보 + v4.3 마감 RC 단계에서 actions 전환
- [차장 결재 #3 — M02/M03] 다건 조치 정렬 순서 명세에 'created_at 오름차순' 명시 — 결정적 정렬 보장 위해 코드에 ORDER BY 추가 필요할 수 있음
- [차장 결재 #4 — M02/M03] M02(목록)와 M03(단건)을 단일 PR/단일 commit으로 묶을지 — 권고: 단일 commit (동일 §6.5 섹션, 동일 drift)
- [차장 결재 #5 — M04 P1 핵심] item shape 결정: 명세대로 flat metric row vs 현행 enclosure-그룹+latest_metrics — 후자 유지 시 task 방향이 '코드 정정→명세 정정'으로 역전. **본 차수 최대 의사결정 포인트**
- [차장 결재 #6 — M04] enclosure_name 필드 보존 여부 — 명세 보강(필드 추가 OK) vs 클라이언트가 별도 GET /api/devices/enclosures/{id} 조인
- [차장 결재 #7 — M04] pagination.total 키 위치(data.total + pagination.total_pages 이중 vs pagination.total 단일) — 프로젝트 표준 envelope 통일 PRD_ApiResponse_Split 정합성 재검토
- [차장 결재 #8 — M05] threshold_config를 §8.6.3에서 완전 제거하는 본 정정안 vs 별도 §8.6.5 'metrics/latest-with-threshold' 엔드포인트 신설
- [차장 결재 #9 — M05] latest_metrics=null 케이스 status code 정책 통일 — 현재 server는 200+null, enclosure(§5.5.11)는 404. v4.4 차수 범위 포함 여부
- [차장 결재 #10 — M06] PDF 다운로드/HTML preview를 §3.x ApiResponse envelope 공식 예외로 인정할지 — 인정 시 §3.x에 '파일/렌더링 엔드포인트 예외' 문구 추가
- [차장 결재 #11 — M06] 에러 응답을 FastAPI HTTPException `{detail}` 그대로 둘지 vs ApiResponse `{success:false, error:{...}}` 로 정규화하는 후속 P2 작업으로 분리
- [차장 결재 #12 — M07] 명세 §8.3.7 응답 data:{items,total} 이중 래핑 제거안 승인 — 사내 ApiResponse 표준(평탄 배열)과 일치 vs 명세 원안 보존
- [차장 결재 #13 — M07] limit 기본값 정책 — 현재 코드 20, 명세 50, 본 설계에서 50 상향. 다른 list 엔드포인트(20)와 불일치 — 명세 일관성 우선 vs 사내 일관성 우선
- [차장 결재 #14 — M08] Detection PUT §6.1.5 동일 누락 — 별도 mismatch ID로 발급 후 같은 PR에 묶을지, 별도 차수로 분리할지
- [차장 결재 #15 — M08] Pydantic MalfunctionEventCreate extra 정책 — 'ignore'면 backward-compatible, 'forbid'면 매니저 동시 업데이트 긴급 필요. 사전 코드 확인 의무
- [차장 결재 #16 — M09] end_date > start_date 순서 검증 코드 추가 여부 — 본 설계 권고: 명세를 코드에 맞춰 검증 없음. 검증 추가 시 별도 차수 코드 변경 PR
- [차장 결재 #17 — M09] from_event_id 단독 조회 시 limit 기본값 20이 1:N 이력 전체를 가리는 케이스 — 자동 100 상향 vs 클라이언트 책임. 현 설계: 클라이언트 책임
- [차장 결재 #18 — M10] §6.4.5를 PUT 단독 유지 vs §6.4.5-a PATCH 별도 §섹션 신설 — 코드는 PUT/PATCH 둘 다 존재하나 명세는 PUT만 문서화
- [차장 결재 #19 — M10] type_event 예시 값을 'Action' 고정으로 둘지 EnumEventType 전체 값 나열 추가 — from_event 타입별 정책 결재
- [정책 결재 — 공통] user_password 평문 응답 노출 정책 — 현재 메모리 기준 v4.x 차수 범위 외 유지 결정됨 (M01에서 schema 그대로 따라감)
- [운영 결재 — 공통] 매니저 4팀 공지 채널 통일 — NATS 정책 채널 vs 주간 회의 vs Slack #gop-api-spec. 권고: 정정 commit 머지 직후 NATS 정책 채널 + 주간 회의 동시

## 7. Risks (14건)

- [HIGH — M04] backward-INCOMPATIBLE envelope 변경 — Central UI 함체 모니터링 패널이 enclosure_name 의존 시 즉시 깨짐. enclosure_id별 그룹화 화면 로직 전면 재작성 필요. **본 차수 최대 위험**
- [HIGH — M04] item shape 결재 지연 시 v4.7 진입 차단 — 코드/명세 어느 쪽을 정정할지 결정 못 하면 작업 자체 불가
- [MED — M02/M03] 매니저 측이 이미 명세 단수 action 기준으로 구현했다면 정정 시점에 매니저 측 파서 동시 패치 필요 (4컴포넌트 × 1h ≈ 4h 추가 공수)
- [MED — M02/M03] action_reported 필드와 actions 리스트 정합성 — action_reported='True'인데 actions=[] 또는 그 반대 케이스 발생 가능, 현재 별개 필드로 동기화 안 됨
- [MED — M07] 매니저 측 system-events 클라이언트가 pagination 키 활용 여부 미확인 — 사용 시 total 필드 추가만 영향이나 사전 통보 필요
- [MED — M08] Pydantic extra 정책이 'forbid'인 경우 명세 정정 전에 매니저가 action_reported 전송 시 422 발생 — 코드 사전 확인 의무
- [LOW — M01] _server_to_response 헬퍼 재사용 시 순환 의존 우려 — 본 fix는 인라인 유지, 추출은 별도 commit(Tidy First)
- [LOW — M01] 회색지대: UI가 카테고리 상세에서 cpu_usage 등 4개 키 의존 시 깨질 수 있으나, 현재 500이므로 실질 영향 0
- [LOW — M05] 외주 매니저 개발사가 구버전 명세(data.metrics) 기준 stub 코딩 중일 가능성 — 정정 공지 필요
- [LOW — M06] 매니저 구현자가 잘못된 명세(JSON envelope) 기준으로 PDF 다운로드 파싱 시도 시 현재 코드에서 동작 안 함 — SVMS 4주차 작업 착수 전 사전 확인 필수
- [LOW — M09] dead code 위험: 매니저 측 422 핸들러(end_date>start_date)가 동작 안 함 — 매니저 측 코드 정리 필요
- [LOW — M10] 매니저 구현자가 명세 2필드 예시 그대로 보내면 422 발생 (이미 현 상태에서 발생 중) — 정정 후 4필드 송신 전환 필요, 단 Central UI는 이미 4필드 송신 가능성 높음
- [LOW — 공통] 사본 5곳 동기화 누락 — 마스터는 c:/workspace_python/api-test-server/GOP_Restful_Api_연동설계.md, 사본 갱신 시 함께 정정 필요
- [LOW — 공통] docs/memory/session-context.md 갱신 누락 시 다음 세션에서 v4.6 진행 상황 파악 곤란 — 매 commit 후 갱신 필수
- [LOW — 공통] 검증 환경 3종(로컬 정상 / 외부IP 데이터 0건 / 내부IP 502) 차이로 인해 매니저 통합 검증이 로컬 환경에 국한 — 외부 검증 불가, 매니저 측 자체 dry-run 의존

## 8. Success Criteria

- **3-way 정합 100%**: GOP_Restful_Api_연동설계.md ↔ app/routers/*.py 코드 ↔ Swagger UI(/docs) 응답 스키마가 10건 mismatch 영역에서 완전 일치 — 차장 시각 확인 + grep 검증
- **pytest 회귀 0건**: tests/ 전체 실행 시 신규 회귀 0건. M04 영향 5건 + M07 영향 3건은 신규 envelope/response_model에 맞춰 재작성 후 green. M01 영향 1건(test_get_category_with_servers)은 ERROR → PASSED 전환
- **M01 500 에러 완전 제거**: GET /api/servers/categories/{id} 호출 시 200 응답 + data.servers[].user_name/user_password/threshold_config 키 존재 + cpu/ram/disk/network_throughput 키 부재
- **매니저 통합 가능 상태**: GIS/VMS/NVR/Speaker 4종 매니저가 정정된 명세대로 클라이언트 코드 구현 시 422/500 에러 없이 200 응답 수신. 특히 ActionEvent 1:N(M02/M03) + ActionEvent PUT 4필드(M10) + from_event_id 필터(M09) 사용 가능
- **Swagger UI OpenAPI 스키마 정식화**: M07 response_model 부착으로 매니저 측 OpenAPI 기반 .NET 클라이언트 코드 생성 가능 상태 — 수동 dict 매핑 추정 작업 제거
- **backward-compatible 검증**: M02/M03/M04 3건의 backward-INCOMPATIBLE 변경에 대해 매니저 측 패치 일정 합의 + 나머지 7건은 매니저 런타임 영향 0 확인
- **차장 결재 완료**: 19건 결재 항목 중 본 차수 진행에 직결되는 11건(특히 M04 item shape, M02/M03 매니저 일정, M07 limit 기본값) 종결 + 결재 결과 docs/memory/session-context.md 기록
- **문서 정합 검증**: docs/INDEX.md 자동 갱신 Hook 정상 동작 + 사본 5곳(c\357\200\272workspace_python..., e:\01.사업관련자료, c:\workspace_app\Ironwall.Dotnet.Libraries\Docs) 마스터와 동기화 또는 명시적 deprecated 마킹
- **롤백 가능 상태 유지**: v4.4-final-stable 태그 존재 + 8개 commit 모두 단독 revert 가능한 단위 + 매 commit 메시지에 mismatch_id + 'docs:' vs 'fix:' prefix 명시
- **effort 9.5h 내 완료**: 차장님께 보고된 1.5일 추정 내 마감 — 초과 시 즉시 보고 + 잔여 항목 v4.7 이월

## 9. Camera Preset 감시금지구역 (Option C) — 별도 Workflow 결과 대기

> 결재: **Option C — is_restricted_zone + restricted_actions Enum list** + **v4.6에 통합**
> Enum 4종: BLOCK_RTSP / BLOCK_RECORDING / BLOCK_EVENT_NOTIFY / MASK_DISPLAY
> Workflow 9 agent 정밀 설계 진행 중 (Domain + 7 layers + Synthesize)
> 완료 시 본 섹션에 DB 마이그레이션 + Enum 정의 + Model/Schema/Router 변경 + 명세 §5.7 갱신 + 매니저 가이드 통합

## 10. Next Actions (v4.6 적용 단계)

1. **M01 P0 즉시 핫픽스** (0.5h) — server_categories.py 500 차단
2. **명세 정정 7건** (M02/M03/M05/M06/M08/M09/M10) — 백그래운드 변경 0
3. **코드 정정 2건** (M07 + M04) — M04는 high risk, 차장 결재 후
4. **Camera Preset Option C 적용** — DB + 모델 + 스키마 + 라우터 + 명세 + 가이드
5. **Image rebuild + Container 재시작**
6. **Swagger UI 검증** — 정정된 응답 envelope 노출 확인
7. **명세 v4.6 차수 신설** — 하루 1차수 묶음 원칙
8. **git commit** + v4.6-final-stable 태그 신설
