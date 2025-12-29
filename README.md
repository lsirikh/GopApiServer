# GOP RESTful API Test Server

GOP 통제시스템 연동을 위한 RESTful API 테스트 서버입니다.

## 기술 스택

- **Framework**: FastAPI
- **Database**: SQLite
- **Container**: Docker
- **Documentation**: Swagger UI / ReDoc (한글화)

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
| DB Admin | 8080 | http://localhost:8080 | SQLite 웹 관리자 |

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
├── tests/                   # 테스트 파일
├── data/                    # SQLite DB 파일
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 문서

- [GOP RESTful API 연동설계서](Docs/GOP_Restful_Api_연동설계.md) - API 상세 설계 문서 (v1.9)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.9 | 2025-12-29 | Server Monitoring API 추가, API 문서 한글화 |
| v1.8 | 2025-11-29 | Camera Event Mapping API 추가 |
| v1.7 | 2025-11-29 | Event Mapping API 추가 |
| v1.6 | 2025-11-29 | Detection/Action 연결 기능 추가 |
| v1.5 | 2025-11-28 | Connection 이벤트 API 추가 |
| v1.4 | 2025-11-28 | Malfunction 이벤트 API 추가 |
| v1.3 | 2025-11-28 | Detection/Action 이벤트 API 추가 |

---

**버전**: v1.9
**최종 업데이트**: 2025-12-29
