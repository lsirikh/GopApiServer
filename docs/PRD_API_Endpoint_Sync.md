# PRD: API 엔드포인트 정합성 동기화

**작성일**: 2026-02-13
**소스**: OpenAPI 스펙 (localhost:8000/openapi.json) vs GOP 문서 분석

---

## 1. 개요

Test API Server의 실제 엔드포인트(202개)와 GOP 문서(GOP_Restful_Api_연동설계.md, 개발현황_20260213.md) 간 불일치를 해소한다.

**현황 요약**:
- 실제 API 엔드포인트: **202개** (/, /health, /api/logs, /api/logs/viewer, /api/auth/login/oauth2(deprecated) 제외)
- 개발현황 부록: **158개** (경로 오류 2건, 존재하지 않는 엔드포인트 5건, 누락 다수)
- GOP 12.1 부록: 카테고리 4개 통째 누락, PUT 6건 누락, 완전 누락 2건

**범위 제외**: `GET /api/logs`, `GET /api/logs/viewer`

---

## 2. 변경 영역 요약

| # | 영역 | 변경 | 상세 |
|---|------|:---:|------|
| 1 | 코드 (라우터) | 없음 | 202개 엔드포인트 모두 정상 동작 중. 코드 변경 불필요 |
| 2 | DB 스키마 | 없음 | 테이블/컬럼 변경 없음 |
| 3 | Swagger/Docs/Redoc | **수정** | `tags_metadata` 누락 태그 보강, Preview Page 경로 정합성 |
| 4 | GOP_스키마_전체.md | 없음 | DB 구조 변경 없으므로 v2.10 유지 |
| 5 | GOP_Restful_Api_연동설계.md | **수정** | 12.1 부록 정합성, 누락 섹션 3건 추가 → **v3.9** |
| 6 | 개발현황_20260213.md | **수정** | 경로/Method 오류, 누락 엔드포인트, 부록 전면 재작성 |

---

## 3. 코드 변경

### 3.1 변경 없음 확인

실제 라우터 코드와 GOP_Restful_Api_연동설계.md 본문 섹션 대조 결과, **모든 엔드포인트가 이미 올바르게 구현**되어 있다. 불일치는 문서(12.1 부록, 개발현황) 측의 기록 오류.

| 확인 항목 | GOP 본문 | 실제 코드 | 결과 |
|-----------|---------|----------|:---:|
| Camera Settings | GET/PATCH/PUT (5.3.7~9) | GET/PATCH/PUT | ✓ |
| Proxy Settings | GET/PATCH/PUT (8.8.1~3) | GET/PATCH/PUT | ✓ |
| Server Metrics | POST/GET/GET latest/DELETE (8.6) | POST/GET/GET latest/DELETE | ✓ |
| Controllers PATCH+PUT | 5.1.4 + 5.1.5 | PATCH + PUT | ✓ |
| Events PATCH+PUT | 6.x.4 + 6.x.5 | PATCH + PUT | ✓ |

### 3.2 Swagger tags_metadata 보강

`app/main.py`의 `tags_metadata` 배열에 누락된 태그 추가.

**현재 누락 확인 필요 태그**:

| 태그 | 설명 | 비고 |
|------|------|------|
| `Enclosure Metrics` | 함체 환경 모니터링 메트릭 | flat list 포함 |
| `Detection Logs` | 탐지 로그 조회 | v3.8 추가 |
| `Mapping Cameras` | 매핑 카메라 독립 목록 | v3.8 추가 |
| `Mapping Speakers` | 매핑 스피커 독립 목록 | v3.8 추가 |
| `Mapping Lamps` | 매핑 경광등 독립 목록 | v3.8 추가 |

> 이미 등록된 태그는 스킵. `main.py`의 `tags_metadata` 배열을 실제 코드와 대조하여 누락분만 추가.

### 3.3 Report Preview Page 경로 정합성

| 문서 (GOP 10.5) | 실제 코드 |
|---|---|
| `GET /reports/preview/{generation_id}` (Non-API, HTML) | `GET /api/reports/generations/{generation_id}/preview-page` |

**조치**: 경로가 다르나 동일 기능. GOP 문서를 실제 코드 경로로 업데이트한다 (코드가 API 규칙에 부합).

---

## 4. 스키마 변경

**변경 없음**. DB 테이블/컬럼 구조 변경이 없으므로 Pydantic 스키마, DB 모델 수정 불필요.

---

## 5. GOP_스키마_전체.md

**변경 없음**. DB 구조 변경이 없으므로 v2.10 유지. 변경이력 추가하지 않음.

---

## 6. GOP_Restful_Api_연동설계.md 업데이트 → v3.9

### 6.1 헤더 업데이트 (규칙 5-3)

```
**최종 수정일**: 2026-02-13
**버전**: v3.9
```

### 6.2 본문 섹션 추가/수정 (규칙 5-1)

#### 6.2.1 Server API — 서버별 시스템 이벤트 조회 추가 (8.3)

**8.3 하위** 섹션 추가 (8.3.7 신규):

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/servers/{server_id}/system-events` | 특정 서버의 시스템 이벤트 목록 |

- Query Parameters: page, limit, severity, acknowledged
- 응답: SystemEvent 목록 (해당 서버 source 기준 필터)

#### 6.2.2 Enclosure Metrics — 전체 목록 조회 추가 (5.5)

**5.5 하위** 섹션 추가 (5.5.13 신규):

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/enclosure-metrics` | 전체 함체 메트릭 목록 (독립 조회) |

- flat_router 패턴 (Device Groups 독립 목록과 동일)
- Query Parameters: page, limit, enclosure_id, from_date, to_date

#### 6.2.3 Report Preview Page 경로 수정 (10.5)

**변경 전** (10.5.1~2):
```
GET /reports/preview/{generation_id}  (Non-API)
```

**변경 후**:
```
GET /api/reports/generations/{generation_id}/preview-page
```

### 6.3 12.1 부록 정합성 수정 (규칙 5-1, 5-2)

#### 6.3.1 누락 카테고리 추가

**Camera Settings** (Cameras 하위에 추가):
```
- GET /api/devices/cameras/{camera_id}/settings — 카메라 설정 조회
- PATCH /api/devices/cameras/{camera_id}/settings — 카메라 설정 수정 (부분)
- PUT /api/devices/cameras/{camera_id}/settings — 카메라 설정 수정 (전체)
```

**Lamps** (Speakers 다음에 추가):
```
- GET /api/devices/lamps — 경광등 목록 조회
- POST /api/devices/lamps — 경광등 생성
- GET /api/devices/lamps/{id} — 경광등 단일 조회
- PATCH /api/devices/lamps/{id} — 경광등 수정 (부분)
- PUT /api/devices/lamps/{id} — 경광등 수정 (전체)
- DELETE /api/devices/lamps/{id} — 경광등 삭제
```

**Event Mapping Lamps** (Event Mapping Speakers 다음에 추가):
```
- GET /api/integrations/event-mappings/{mapping_id}/lamps — 경광등 연동 목록 조회
- POST /api/integrations/event-mappings/{mapping_id}/lamps — 경광등 연동 생성
- GET /api/integrations/event-mappings/{mapping_id}/lamps/{config_id} — 경광등 연동 단일 조회
- PATCH /api/integrations/event-mappings/{mapping_id}/lamps/{config_id} — 경광등 연동 수정 (부분)
- PUT /api/integrations/event-mappings/{mapping_id}/lamps/{config_id} — 경광등 연동 수정 (전체)
- DELETE /api/integrations/event-mappings/{mapping_id}/lamps/{config_id} — 경광등 연동 삭제
```

**Proxy Settings** (Server Metrics 다음에 추가):
```
- GET /api/servers/{server_id}/proxy-settings — 프록시 설정 조회
- PATCH /api/servers/{server_id}/proxy-settings — 프록시 설정 수정 (부분)
- PUT /api/servers/{server_id}/proxy-settings — 프록시 설정 수정 (전체)
```

**Enclosure Metrics 독립 목록** 추가:
```
- GET /api/enclosure-metrics — 전체 함체 메트릭 목록 조회 (독립)
```

#### 6.3.2 누락 PUT 추가 (PATCH만 있던 항목)

| 카테고리 | 추가 엔드포인트 |
|----------|----------------|
| Controllers | `PUT /api/devices/controllers/{id}` — 수정 (전체) |
| Sensors | `PUT /api/devices/sensors/{id}` — 수정 (전체) |
| Detection Events | `PUT /api/events/detections/{id}` — 수정 (전체) |
| Malfunction Events | `PUT /api/events/malfunctions/{id}` — 수정 (전체) |
| Connection Events | `PUT /api/events/connections/{id}` — 수정 (전체) |
| Action Events | `PUT /api/events/actions/{id}` — 수정 (전체) |

#### 6.3.3 기타 누락 추가

| 위치 | 추가 엔드포인트 |
|------|----------------|
| Servers | `GET /api/servers/{server_id}/system-events` — 서버별 이벤트 |
| Reports | `GET /api/reports/generations/{id}/preview-page` — 미리보기 페이지 |

#### 6.3.4 경로 수정 (규칙 5-2 — 변경 사항 삭제/교체)

| 변경 전 | 변경 후 | 비고 |
|---------|---------|------|
| `GET /reports/preview/{generation_id}` (Non-API) | `GET /api/reports/generations/{generation_id}/preview-page` | 경로 통일 |

### 6.4 변경이력 추가 (규칙 5-4)

부록 변경이력에 v3.9 엔트리 추가 (금일 변경 내용 묶음):

```
| v3.9 | 2026-02-13 | **API 엔드포인트 정합성 동기화 (12.1 부록 수정, 누락 섹션 추가)**<br><br>
**[1. 12.1 부록 정합성 수정]**<br>
- Lamps 6개 엔드포인트 추가<br>
- Camera Settings 3개 엔드포인트 추가<br>
- Proxy Settings 3개 엔드포인트 추가<br>
- Event Mapping Lamps 6개 엔드포인트 추가<br>
- Controllers, Sensors, Events(4종) PUT 엔드포인트 6건 추가<br>
- Server system-events, Enclosure-metrics flat, Report preview-page 추가<br><br>
**[2. Server 시스템 이벤트 조회 추가 (8.3.7)]**<br>
- GET /api/servers/{server_id}/system-events: 서버별 시스템 이벤트 필터 조회<br><br>
**[3. Enclosure Metrics 독립 목록 추가 (5.5.13)]**<br>
- GET /api/enclosure-metrics: 전체 함체 메트릭 독립 조회 (flat_router 패턴)<br><br>
**[4. Report Preview Page 경로 수정 (10.5)]**<br>
- GET /reports/preview/{id} → GET /api/reports/generations/{id}/preview-page |
```

> **규칙 5-5**: PRD 참조 문구 제외

---

## 7. 개발현황_20260213.md 업데이트

### 7.1 경로 오류 수정 (2건)

| 현재 (잘못됨) | 수정 후 | 위치 |
|-------------|---------|------|
| `/api/device-groups` | `/api/devices/groups` | 섹션 4, 부록 #23~29 |
| `/api/servers/proxy-settings` | `/api/servers/{server_id}/proxy-settings` | 섹션 6, 부록 #92~93 |

### 7.2 존재하지 않는 엔드포인트 수정 (5건)

| # | 현재 (잘못됨) | 수정 | 비고 |
|---|-------------|------|------|
| 1 | `POST /api/devices/cameras/{id}/settings` | **삭제** | 실제: PUT (전체 교체) |
| 2 | `DELETE /api/devices/cameras/{id}/settings` | **삭제** | CASCADE 삭제만 (별도 API 없음) |
| 3 | `GET /api/servers/{id}/metrics/{mid}` | → `GET .../metrics/latest` | 단건 조회 없음, 최신 조회로 변경 |
| 4 | `DELETE /api/servers/{id}/metrics/{mid}` | → `DELETE .../metrics` | 단건 삭제 없음, bulk 삭제로 변경 |
| 5 | `DELETE /api/devices/enclosures/{id}/metrics/{mid}` | → `DELETE .../metrics` | 단건 삭제 없음, bulk 삭제로 변경 |

### 7.3 카메라 설정 섹션 수정

**변경 전** (현재):

| 기능 | 엔드포인트 | UI | 백엔드 |
|------|-----------|:--:|:------:|
| 설정 조회 | GET | O | O |
| 설정 등록 | POST | — | O |
| 설정 수정 | PATCH | — | **X** |
| 설정 삭제 | DELETE | — | O |

**변경 후**:

| 기능 | 엔드포인트 | UI | 백엔드 |
|------|-----------|:--:|:------:|
| 설정 조회 | `GET /api/devices/cameras/{id}/settings` | O | O |
| 설정 수정 (부분) | `PATCH /api/devices/cameras/{id}/settings` | — | **X** |
| 설정 수정 (전체) | `PUT /api/devices/cameras/{id}/settings` | — | O |

### 7.4 누락 카테고리 추가

본문과 부록 모두에 추가:

| 카테고리 | 엔드포인트 수 | 추가 위치 |
|----------|:-----------:|---------|
| Audit Logs | 2 | 사용자 세션 뒤 (신규 섹션) |
| Config Change Logs | 2 | Audit Logs 뒤 (신규 섹션) |
| Detection Logs | 2 | 이벤트 관리 섹션 내 |
| Mapping 독립 목록 | 3 | 이벤트 매핑 뒤 |

### 7.5 기존 카테고리 누락 엔드포인트 추가

**인증 (Authentication)** — 1건 추가:

| 기능 | 엔드포인트 | UI | 백엔드 |
|------|-----------|:--:|:------:|
| 내 정보 조회 | `GET /api/auth/me` | O | **X** |

> `POST /api/auth/login/oauth2`는 deprecated 레거시 (Legacy User 모델). 문서 반영 제외.

**사용자 그룹** — 1건 추가:

| 기능 | 엔드포인트 | UI | 백엔드 |
|------|-----------|:--:|:------:|
| 그룹 소속 사용자 | `GET /api/user-groups/{id}/users` | O | **X** |

**사용자 세션** — 3건 추가:

| 기능 | 엔드포인트 | UI | 백엔드 |
|------|-----------|:--:|:------:|
| 내 세션 목록 | `GET /api/user-sessions/me` | O | **X** |
| 내 다른 세션 종료 | `DELETE /api/user-sessions/me/{id}` | O | **X** |
| 사용자별 전체 세션 종료 | `DELETE /api/user-sessions/user/{user_id}` | O | **X** |

**모든 장비 CRUD** — PATCH 추가 (PUT과 별도):
- 장비 그룹, 제어기, 센서, 카메라, 스피커, 경광등, 파일 그룹 각각에 PATCH 행 추가
- 프리셋, ROI 각각에 PATCH 행 추가

**서버 관리** — 6건 추가:

| 기능 | 엔드포인트 | UI | 백엔드 |
|------|-----------|:--:|:------:|
| 서버 요약 | `GET /api/servers/summary` | O | O |
| 서버별 이벤트 | `GET /api/servers/{id}/system-events` | O | **X** |
| 서버 카테고리 PATCH | `PATCH /api/servers/categories/{id}` | O | **X** |
| 서버 PATCH | `PATCH /api/servers/{id}` | O | **X** |
| 메트릭 최신 조회 | `GET /api/servers/{id}/metrics/latest` | O | **X** |
| 프록시 설정 PUT | `PUT /api/servers/{server_id}/proxy-settings` | — | **X** |

**이벤트 관리** — 다수 추가:
- 이벤트 매핑 + 하위(카메라/스피커/경광등) 각각에 PATCH 행 추가
- 매핑 독립 목록 3건 (mapping-cameras, mapping-speakers, mapping-lamps)
- 시스템 이벤트: `DELETE /api/system-events/{id}` 추가
- 탐지 이벤트: `PUT`, `GET /{id}/action` 추가
- 고장 이벤트: `PUT`, `GET /{id}/action` 추가
- 연결/액션 이벤트: `PUT` 추가

**함체** — 5건 추가:
- `PATCH /api/devices/enclosures/{id}` (부분 수정)
- `POST /api/devices/enclosures/{id}/control` (히터/팬 제어)
- `PATCH /api/devices/enclosures/{id}/status` (도어 상태)
- `GET /api/devices/enclosures/{id}/metrics/latest` (최신 메트릭)
- `GET /api/enclosure-metrics` (전체 메트릭 독립 목록)

**보고서** — 1건 추가:
- `GET /api/reports/generations/{id}/preview-page` (미리보기 페이지)

### 7.6 부록 전체 엔드포인트 재작성

158개 → **202개**로 전면 재작성.

엔드포인트 번호 기준 (실제 코드 순서):

| 카테고리 | 엔드포인트 수 |
|---------|:-----------:|
| Auth | 4 |
| Users | 11 |
| User Groups | 6 |
| User Sessions | 6 |
| Audit Logs | 2 |
| Config Change Logs | 2 |
| Device Groups | 8 |
| Controllers | 6 |
| Sensors | 6 |
| Cameras | 6 |
| Camera Settings | 3 |
| Camera Presets | 6 |
| Speakers | 6 |
| Lamps | 6 |
| File Groups | 6 |
| Enclosures | 8 |
| Enclosure Metrics | 5 |
| ROIs | 6 |
| XY Points | 4 |
| Server Categories | 6 |
| Servers | 8 |
| Server Metrics | 4 |
| Proxy Settings | 3 |
| System Events | 7 |
| Event Mappings | 6 |
| Mapping Cameras | 6 |
| Mapping Speakers | 6 |
| Mapping Lamps | 6 |
| Mapping 독립 목록 | 3 |
| Detection Events | 7 |
| Malfunction Events | 7 |
| Connection Events | 6 |
| Action Events | 6 |
| Detection Logs | 2 |
| Reports | 12 |
| **합계** | **202** |

### 7.7 요약/진행률 재산정

부록 재작성 후 UI/백엔드 O/X 개수를 다시 세어 요약 섹션 및 게이지 업데이트.

---

## 8. 수정 대상 파일 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| **수정** | `app/main.py` | tags_metadata 누락 태그 보강 |
| **수정** | `GOP_Restful_Api_연동설계.md` | v3.9: 헤더, 섹션 3건 추가, 12.1 부록 정합성, 변경이력 |
| **수정** | `docs/Checks/개발현황_20260213.md` | 경로/Method 수정, 누락 추가, 부록 재작성, 총계 재산정 |

**변경 없음**:
- `app/routers/*.py` — 코드 이미 올바름
- `app/schemas/*.py` — Pydantic 스키마 변경 없음
- `app/models/*.py` — DB 모델 변경 없음
- `docs/GOP_스키마_전체.md` — DB 구조 변경 없으므로 v2.10 유지

---

## 9. 실행 계획

### Phase 1: Swagger tags_metadata 보강
- [ ] 1.1 `app/main.py` tags_metadata 배열 확인
- [ ] 1.2 누락 태그 추가 (Enclosure Metrics, Detection Logs, Mapping flat 등)
- [ ] 1.3 서버 재시작 후 Swagger UI 확인

### Phase 2: GOP_Restful_Api_연동설계.md → v3.9
- [ ] 2.1 헤더 업데이트 (v3.9, 2026-02-13)
- [ ] 2.2 목차에 신규 섹션 번호 추가 (8.3.7, 5.5.13)
- [ ] 2.3 섹션 8.3 — Server 시스템 이벤트 조회 추가 (8.3.7)
- [ ] 2.4 섹션 5.5 — Enclosure Metrics 독립 목록 추가 (5.5.13)
- [ ] 2.5 섹션 10.5 — Report Preview Page 경로 수정
- [ ] 2.6 12.1 부록 — 누락 카테고리 4개 추가 (Lamps, Camera Settings, Proxy Settings, Mapping Lamps)
- [ ] 2.7 12.1 부록 — 누락 PUT 6건 추가 (Controllers, Sensors, Events 4종)
- [ ] 2.8 12.1 부록 — 기타 누락 2건 추가 (server system-events, enclosure-metrics)
- [ ] 2.9 12.1 부록 — Report Preview 경로 수정
- [ ] 2.10 변경이력 v3.9 추가
- [ ] 2.11 12.1 부록 전체 엔드포인트 수 검증

### Phase 3: 개발현황_20260213.md 수정
- [ ] 3.1 경로 오류 수정 (device-groups → devices/groups, proxy-settings 경로)
- [ ] 3.2 존재하지 않는 엔드포인트 5건 삭제/수정
- [ ] 3.3 카메라 설정 섹션 수정 (POST/DELETE 제거 → PUT 추가)
- [ ] 3.4 서버 메트릭 섹션 수정 (/{mid} → /latest, bulk delete)
- [ ] 3.5 함체 메트릭 섹션 수정 (/{mid} → bulk delete)
- [ ] 3.6 누락 카테고리 추가 (Audit Logs, Config Change Logs, Detection Logs)
- [ ] 3.7 누락 엔드포인트 추가 (Auth, Users, Sessions, Devices PATCH, Servers, Events 등)
- [ ] 3.8 부록 전체 엔드포인트 202개로 재작성
- [ ] 3.9 요약/게이지 재산정

### Phase 4: 검증
- [ ] 4.1 서버 기동 확인 (Swagger UI, Redoc 정상 표시)
- [ ] 4.2 GOP 12.1 부록 vs OpenAPI 엔드포인트 수 일치 확인
- [ ] 4.3 개발현황 부록 vs OpenAPI 엔드포인트 수 일치 확인
