# GOP RESTful API Test Server

GOP 통제시스템 연동을 위한 RESTful API 테스트 서버입니다.

## 기술 스택

- **Framework**: FastAPI
- **Database**: SQLite
- **Container**: Docker

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
| DB Admin | 8080 | http://localhost:8080 | SQLite 웹 관리자 |

---

## API 엔드포인트

### Device API
- `GET /api/devices/controllers` - Controller 목록
- `GET /api/devices/sensors` - Sensor 목록
- `GET /api/devices/cameras` - Camera 목록

### Event API
- `GET/POST /api/events/detections` - Detection 이벤트
- `GET/POST /api/events/malfunctions` - Malfunction 이벤트
- `GET/POST /api/events/connections` - Connection 이벤트
- `GET/POST /api/events/actions` - Action 이벤트

### Integration API
- `GET/POST /api/integrations/camera-event-mappings` - Camera Event Mapping

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
```

---

## 프로젝트 구조

```
api-test-server/
├── app/
│   ├── main.py           # FastAPI 앱 진입점
│   ├── config.py         # 설정
│   ├── database.py       # DB 연결
│   ├── models/           # SQLAlchemy 모델
│   ├── schemas/          # Pydantic 스키마
│   ├── routers/          # API 라우터
│   └── utils/            # 유틸리티 (Enum 등)
├── tests/                # 테스트 파일
├── data/                 # SQLite DB 파일
├── docs/                 # 문서
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 문서

- [GOP RESTful API 연동설계서](Docs/GOP_Restful_Api_연동설계.md)
- [Enum Update PRD](docs/Enum-Update-PRD.md)

---

**버전**: v1.3
**최종 업데이트**: 2025-11-28
