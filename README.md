# GOP RESTful API Test Server

GOP 통제시스템 연동을 위한 RESTful API 테스트 서버입니다.

**현재 버전**: v4.8 (2026-06-22) — 변경 이력은 [CHANGELOG.md](CHANGELOG.md) 참조.

## 기술 스택

- **Framework**: FastAPI + Pydantic v2
- **Database**: PostgreSQL 16 (alpine)
- **Container**: Docker Compose
- **Documentation**: Swagger UI / ReDoc (한글화)
- **Auth**: JWT (HS256, 24h access + 7d refresh)
- **NATS**: SYNC 이벤트 발행 (statement-level 트리거, db_monitor 연동)

---

## Docker 사용법

### 서버 실행

```bash
# 빌드 및 실행 (백그라운드)
docker-compose up -d --build

# 로그 확인하며 실행
docker-compose up --build
```

### 서버 중지

```bash
# 컨테이너 중지 (데이터 유지)
docker-compose stop

# 컨테이너 중지 및 삭제 (데이터 유지)
docker-compose down
```

### 서버 완전 삭제

```bash
# 컨테이너 + 볼륨 삭제 (데이터 삭제됨)
docker-compose down -v

# 이미지까지 삭제
docker-compose down --rmi all
```

### 기타 명령어

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 컨테이너 재시작
docker-compose restart
```

---

## 접속 정보

| 서비스 | 포트 | URL | 설명 |
|--------|------|-----|------|
| API Server | 8000 | http://localhost:8000 | FastAPI 서버 |
| API Docs (Swagger) | 8000 | http://localhost:8000/docs | API 문서 (Swagger UI) |
| API Docs (ReDoc) | 8000 | http://localhost:8000/redoc | API 문서 (ReDoc) |
| Log Viewer | 8000 | http://localhost:8000/api/logs/viewer | API 로그 뷰어 |
| DB Admin (Adminer) | 8080 | http://localhost:8080 | PostgreSQL 웹 관리자 (server=postgres, user=gop_user, db=gop) |

---

## API 엔드포인트

### Authentication API
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `GET /api/auth/me` - 현재 사용자 정보

### Device API
- `GET/POST/PATCH/PUT/DELETE /api/devices/controllers` - Controller CRUD
- `GET/POST/PATCH/PUT/DELETE /api/devices/sensors` - Sensor CRUD
- `GET/POST/PATCH/PUT/DELETE /api/devices/cameras` - Camera CRUD

### Event API
- `GET/POST/PATCH/PUT/DELETE /api/events/detections` - Detection 이벤트
- `GET/POST/PATCH/PUT/DELETE /api/events/malfunctions` - Malfunction 이벤트
- `GET/POST/PATCH/PUT/DELETE /api/events/connections` - Connection 이벤트
- `GET/POST/PATCH/PUT/DELETE /api/events/actions` - Action 이벤트

### Integration API
- `GET/POST/PATCH/PUT/DELETE /api/integrations/event-mappings` - Event Mapping
- `GET/POST/PATCH/PUT/DELETE /api/integrations/camera-event-mappings` - Camera Event Mapping

### Server Monitoring API (v1.9 신규)
- `GET/POST/PATCH/PUT/DELETE /api/servers/categories` - 서버 카테고리 CRUD
- `GET/POST/PATCH/PUT/DELETE /api/servers` - 서버 인스턴스 CRUD
- `GET /api/servers/summary` - 대시보드 요약 (카테고리별 상태 집계)

### Logs API
- `GET /api/logs` - API 로그 조회
- `GET /api/logs/viewer` - 웹 기반 로그 뷰어

---

## Enum 정의

### Device Enums
- `EnumDeviceType`: 장치 유형 (CONTROLLER, SENSOR, CAMERA 등)
- `EnumDeviceStatus`: 장치 상태 (ACTIVE, INACTIVE, ERROR 등)
- `EnumCameraMode`: 카메라 모드 (FIXED, PTZ 등)
- `EnumCameraCategory`: 카메라 카테고리 (GOP, CCTV 등)

### Event Enums
- `EnumDetectionType`: 탐지 결과 (TRUE, FALSE, RECOGNITION, UNKNOWN)
- `EnumMalfunctionType`: 고장 유형 (TRUE, FALSE)
- `EnumConnectionType`: 연결 상태 (CONNECT, DISCONNECT)
- `EnumTrueFalse`: 조치보고 여부 (TRUE, FALSE)

### Server Enums (v1.9 신규)
- `EnumServerType`: 서버 유형 (26종)
  - VMS, NVR_API, STREAMING, AI_ANALYSIS, DB, WEB, LOG, BACKUP
  - SECURITY, AUTHENTICATION, API_GATEWAY, MESSAGE_QUEUE
  - FILE_STORAGE, CACHE, SEARCH, MONITORING, NOTIFICATION
  - REPORT, SCHEDULER, LICENSE, CONFIG, PROXY, CDN, DNS, MAIL, CUSTOM
- `EnumServerStatus`: 서버 상태 (NORMAL, WARNING, ERROR)

---

## 로컬 개발 (Docker 없이)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 테스트 실행

```bash
# 전체 테스트
python -m pytest

# 특정 테스트 파일
python -m pytest tests/test_detection_event_model.py

# 커버리지 포함
python -m pytest --cov=app

# 서버 모니터링 테스트
python -m pytest tests/test_server_summary_router.py
```

---

## 프로젝트 구조

```
api-test-server/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 설정
│   ├── database.py          # DB 연결
│   ├── dependencies.py      # 의존성 주입
│   ├── models/              # SQLAlchemy 모델
│   │   ├── device.py        # Controller, Sensor, Camera
│   │   ├── event.py         # Detection, Malfunction, Connection, Action
│   │   ├── server.py        # ServerCategory, Server (v1.9)
│   │   └── ...
│   ├── schemas/             # Pydantic 스키마
│   │   ├── device.py
│   │   ├── event.py
│   │   ├── server.py        # Server 스키마 (v1.9)
│   │   └── common.py        # ApiResponse, PaginationMeta
│   ├── routers/             # API 라우터 (한글 문서화)
│   │   ├── controllers.py
│   │   ├── sensors.py
│   │   ├── cameras.py
│   │   ├── detections.py
│   │   ├── malfunctions.py
│   │   ├── connections.py
│   │   ├── actions.py
│   │   ├── server_categories.py  # (v1.9)
│   │   ├── servers.py            # (v1.9)
│   │   └── ...
│   ├── middleware/          # 미들웨어
│   │   ├── request_id.py    # Request ID 생성
│   │   └── logging.py       # API 로깅
│   └── utils/               # 유틸리티
│       ├── enums.py         # Enum 정의
│       ├── init_db.py       # DB 초기화
│       └── init_server_data.py  # 서버 Seed 데이터 (v1.9)
├── tests/                   # 테스트 파일 (pytest, SQLite in-memory fixture)
├── data/                    # 컨테이너 데이터 mount point
├── logs/                    # 애플리케이션 로그
├── app/migrations/          # 수동 마이그레이션 SQL (v47 JSON→JSONB, v48 is_restricted_zone 등)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

> DB 데이터는 Docker volume (`api-test-pgdata`)에 영구 저장. `docker-compose down -v`만 데이터 초기화.

---

## 시드 데이터 (자동 초기화)

`docker-compose up` 시 빈 DB일 때 `INIT_SAMPLE_DATA=true` 환경변수로 자동 시드 (v4.6 차장님 명세):

| 디바이스 | 카운트 | 분포 |
|---|---|---|
| 제어기 | 4 | A/B/C/D 구역 1개씩 |
| 센서 | 402 | 제어기1: 펜스 100(1~100) + 복합 21(180~200) / 제어기2 동일 / 제어기3: 스마트복합 60(1~60) / 제어기4: 스마트센서 100(1~100) |
| 카메라 | 300 | 4구역 분배, PTZ 100대 × 5 프리셋 |
| 스피커 | 200 | 4구역 분배 |
| 함체 | 30 | 4구역 분배 |
| 경광등 | 30 | 4구역 분배 |

기존 데이터가 있으면 시드 skip. 시드 동작 비활성화: `INIT_SAMPLE_DATA=false`.

---

## 문서

- [GOP RESTful API 연동설계서](GOP_Restful_Api_연동설계.md) — API 상세 설계 (v4.6)
- [GOP 통합 DB 스키마](docs/GOP_스키마_전체.md) — DB 스키마 (v2.12)
- [v4.6 Camera Preset 감시금지구역 가이드](docs/v46_camera_preset_restricted_zone_guide.md) — 매니저 통합용 (.NET/TypeScript 의사 코드)
- [CHANGELOG.md](CHANGELOG.md) — 전체 차수 변경 이력

---

## 변경 이력 (요약)

전체 차수 + 세부 변경은 [CHANGELOG.md](CHANGELOG.md) 참조.

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| **v4.8** | 2026-06-22 | DELETE 응답 envelope sweep — Phase 1~8 통합 (P1 11 + Events 4 = 15 endpoint, 하루 1차수 묶음) |
| **v4.7** | 2026-06-21 | Account/Auth/Session 도메인 전수 조사 (113 이슈, Verdict FAIL) + DELETE 응답 P0 정정 (4 endpoint) |
| **v4.6** | 2026-06-19 | Critical Mismatch 정정 8건 + Camera Preset 감시금지구역(`is_restricted_zone`) + 시드 재설계(차장님 명세) + pagination 안정성 검증 |
| **v4.5** | 2026-06-19 | 잔존 부채 minimal 6 그룹 적용 (37 fail 회복) + Workflow 부채 정밀 분석 PRD |
| **v4.4** | 2026-06-18 | Bulk API 4단계 정합화 (Phase 1~5) + 지향성(`heading`) + JSON→JSONB 23 컬럼 + multi-line Column 정정 |
| **v4.3** | 2026-06-17 | ActionEvent 1:N 관계 + Bulk API 7건 신설 (DeviceGroup + EventMapping Camera/Speaker/Lamp) + statement-level NATS 트리거 |
| v4.2 | 2026-03-03 | Event Statistics API (6.7) |
| v4.1 | 2026-02-15 | Camera Settings 통합 + PRD_Camera_Urls_JsonB |
| v4.0 | 2026-02-01 | DetectionLog API + ActionEvent JOIN |
| v3.x | 2026-01-15 | Account/Auth 시스템 + Lamp Device + ROI 정밀화 |
| v2.x | 2025-12-15 | PostgreSQL 마이그레이션 + ServerMetrics 분리 + Enclosure Metrics |
| v1.9 | 2025-12-29 | Server Monitoring API + 한글 Swagger |
| v1.3~v1.8 | 2025-11-28~29 | Detection / Malfunction / Connection / EventMapping API 신설 |

---

**버전**: v4.8
**최종 업데이트**: 2026-06-22
