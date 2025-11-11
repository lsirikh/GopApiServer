# Product Requirements Document (PRD)

## GOP RESTful API Server

**Version**: 1.0
**Created**: 2025-11-11
**Author**: API Development Team
**Status**: Draft

---

## 1. Executive Summary

### 1.1 Product Overview
FastAPI 기반의 GOP(Guarding Operation Platform) RESTful API 서버를 구축하여 통제시스템과의 연동을 제공합니다. 이 서버는 Device(Controller, Sensor, Camera) 및 Event(Detection, Malfunction, Connection, Action) 관리를 위한 표준 RESTful API를 제공하며, Docker 컨테이너로 배포됩니다.

### 1.2 Product Goals
- ✅ FastAPI 기반의 고성능 RESTful API 서버 구축
- ✅ 두 가지 인증 방식 지원 (토큰 방식 / 공개 방식)
- ✅ GOP_Restful_Api_연동설계.md 문서의 모든 기능 구현
- ✅ SQLite 데이터베이스 연동
- ✅ Docker 컨테이너화 및 포트 충돌 방지
- ✅ OpenAPI/Swagger 기반 자동 API 문서화
- ✅ 기존 컨테이너와의 포트 충돌 없는 안정적인 배포

---

## 2. Technical Architecture

### 2.1 Technology Stack

#### Backend Framework
- **FastAPI**: 최신 Python 웹 프레임워크
  - 자동 API 문서 생성 (OpenAPI/Swagger)
  - 타입 힌팅 기반 데이터 검증 (Pydantic)
  - 비동기 처리 지원
  - 높은 성능

#### Database
- **SQLite**: 경량 데이터베이스
  - 파일 기반 DB (별도 서버 불필요)
  - ACID 트랜잭션 지원
  - 개발 및 소규모 배포에 적합

#### Authentication
- **JWT (JSON Web Token)**: 토큰 기반 인증
- **OAuth2 Password Bearer**: FastAPI 표준 인증 스키마

#### Containerization
- **Docker**: 컨테이너 배포
  - 이미지명: `api_server-fastapi`
  - 독립적인 실행 환경 제공

### 2.2 Port Configuration

**기존 컨테이너 포트 현황**:
```
tuberank-nginx:    80:80
tuberank-flask:    5000:5000
tuberank-postgres: 5432:5432
```

**신규 FastAPI 서버 포트**:
```
api_server-fastapi: 8000:8000 (외부:내부)
```

### 2.3 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web Browser, Mobile App, External Systems)                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Authentication Middleware                       │
│  ┌──────────────────┐         ┌─────────────────┐          │
│  │  Token Mode      │   OR    │  Public Mode    │          │
│  │  (JWT Required)  │         │  (No Auth)      │          │
│  └──────────────────┘         └─────────────────┘          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Routers                                           │     │
│  │  - /api/auth (login, token)                        │     │
│  │  - /api/devices/controllers                        │     │
│  │  - /api/devices/sensors                            │     │
│  │  - /api/devices/cameras                            │     │
│  │  - /api/events/detections                          │     │
│  │  - /api/events/malfunctions                        │     │
│  │  - /api/events/connections                         │     │
│  │  - /api/events/actions                             │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Business Logic Layer (Services)                   │     │
│  │  - DeviceService                                   │     │
│  │  - EventService                                    │     │
│  │  - AuthService                                     │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Data Access Layer (Repositories)                  │     │
│  │  - ControllerRepository                            │     │
│  │  - SensorRepository                                │     │
│  │  - CameraRepository                                │     │
│  │  - EventRepository                                 │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│  - devices.db (Controllers, Sensors, Cameras)               │
│  - events.db (Detections, Malfunctions, Connections,        │
│               Actions)                                       │
│  - users.db (Authentication)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Authentication System

### 3.1 Two Authentication Modes

#### Mode 1: Token-based Authentication (토큰 방식)
- 사용자는 아이디/비밀번호로 로그인
- JWT 토큰 발급
- 모든 API 요청 시 `Authorization: Bearer {token}` 헤더 필수
- 토큰 만료 시간: 24시간 (설정 가능)

**Flow**:
```
1. POST /api/auth/login
   Request: {"username": "admin", "password": "secret"}
   Response: {"access_token": "eyJ...", "token_type": "bearer"}

2. GET /api/devices/controllers
   Headers: Authorization: Bearer eyJ...
   Response: [controllers list]
```

#### Mode 2: Public Mode (공개 방식)
- 인증 없이 모든 엔드포인트 접근 가능
- 개발/테스트 환경에서 사용
- 환경 변수로 제어: `AUTH_MODE=public` 또는 `AUTH_MODE=token`

### 3.2 Authentication Endpoints

```
POST /api/auth/login
POST /api/auth/register (optional, for admin user creation)
POST /api/auth/refresh (optional, for token refresh)
GET  /api/auth/me (현재 사용자 정보)
```

### 3.3 User Management
- 초기 관리자 계정 자동 생성
- 비밀번호 해싱 (bcrypt)
- 사용자 Role 지원 (admin, user)

---

## 4. API Specifications

### 4.1 Base URL
```
http://localhost:8000/api
```

### 4.2 API Categories

#### 4.2.1 Device APIs
**Controllers**:
- `GET /api/devices/controllers` - 목록 조회
- `GET /api/devices/controllers/{id}` - 단일 조회
- `POST /api/devices/controllers` - 생성
- `PATCH /api/devices/controllers/{id}` - 부분 수정
- `PUT /api/devices/controllers/{id}` - 전체 수정
- `DELETE /api/devices/controllers/{id}` - 삭제

**Sensors**:
- `GET /api/devices/sensors` - 목록 조회
- `GET /api/devices/sensors/{id}` - 단일 조회
- `POST /api/devices/sensors` - 생성
- `PATCH /api/devices/sensors/{id}` - 부분 수정
- `PUT /api/devices/sensors/{id}` - 전체 수정
- `DELETE /api/devices/sensors/{id}` - 삭제

**Cameras**:
- `GET /api/devices/cameras` - 목록 조회
- `GET /api/devices/cameras/{id}` - 단일 조회
- `POST /api/devices/cameras` - 생성
- `PATCH /api/devices/cameras/{id}` - 부분 수정
- `PUT /api/devices/cameras/{id}` - 전체 수정
- `DELETE /api/devices/cameras/{id}` - 삭제

#### 4.2.2 Event APIs
**Detection Events**:
- `GET /api/events/detections` - 목록 조회
- `GET /api/events/detections/{id}` - 단일 조회
- `POST /api/events/detections` - 생성
- `PATCH /api/events/detections/{id}` - 부분 수정
- `DELETE /api/events/detections/{id}` - 삭제

**Malfunction Events**:
- `GET /api/events/malfunctions` - 목록 조회
- `GET /api/events/malfunctions/{id}` - 단일 조회
- `POST /api/events/malfunctions` - 생성
- `PATCH /api/events/malfunctions/{id}` - 부분 수정
- `DELETE /api/events/malfunctions/{id}` - 삭제

**Connection Events**:
- `GET /api/events/connections` - 목록 조회
- `GET /api/events/connections/{id}` - 단일 조회
- `POST /api/events/connections` - 생성
- `PATCH /api/events/connections/{id}` - 부분 수정
- `DELETE /api/events/connections/{id}` - 삭제

**Action Events**:
- `GET /api/events/actions` - 목록 조회
- `GET /api/events/actions/{id}` - 단일 조회
- `POST /api/events/actions` - 생성
- `PATCH /api/events/actions/{id}` - 부분 수정
- `DELETE /api/events/actions/{id}` - 삭제

### 4.3 Common Query Parameters
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `sort`: 정렬 기준 (예: `created_at`, `-created_at`)
- `group_device`: 디바이스 그룹 필터
- `status`: 상태 필터
- `start_date`: 시작 날짜 (ISO 8601)
- `end_date`: 종료 날짜 (ISO 8601)

### 4.4 Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {},
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 5. Data Models

### 5.1 Device Models

#### Controller Model
```python
{
  "id": int,
  "number_device": int,
  "group_device": int,
  "name_device": str,
  "type_device": str,  # EnumDeviceType
  "version": str,
  "status": str,  # EnumDeviceStatus
  "ip_address": str,
  "ip_port": int,
  "created_at": datetime,
  "updated_at": datetime
}
```

#### Sensor Model
```python
{
  "id": int,
  "number_device": int,
  "group_device": int,
  "name_device": str,
  "type_device": str,  # EnumDeviceType
  "version": str,
  "status": str,  # EnumDeviceStatus
  "controller_id": int,
  "created_at": datetime,
  "updated_at": datetime
}
```

#### Camera Model
```python
{
  "id": int,
  "number_device": int,
  "group_device": int,
  "name_device": str,
  "type_device": str,  # EnumDeviceType (IpCamera)
  "version": str,
  "status": str,  # EnumDeviceStatus
  "ip_address": str,
  "ip_port": int,
  "user_name": str,
  "user_password": str,
  "rtsp_uri": str,
  "rtsp_port": int,
  "mode": str,  # EnumCameraMode
  "category": str,  # EnumCameraType
  "created_at": datetime,
  "updated_at": datetime
}
```

### 5.2 Event Models

#### Detection Event Model
```python
{
  "id": int,
  "message_type": int,
  "device_id": int,
  "group_event": str,
  "status": str,  # EnumTrueFalse
  "result": str,  # EnumDetectionType
  "datetime": datetime,
  "created_at": datetime,
  "updated_at": datetime
}
```

#### Malfunction Event Model
```python
{
  "id": int,
  "message_type": int,
  "device_id": int,
  "group_event": str,
  "status": str,  # EnumTrueFalse
  "reason": str,  # EnumFaultType
  "first_start": int,
  "first_end": int,
  "second_start": int,
  "second_end": int,
  "datetime": datetime,
  "created_at": datetime,
  "updated_at": datetime
}
```

#### Connection Event Model
```python
{
  "id": int,
  "message_type": int,
  "device_id": int,
  "group_event": str,
  "status": str,  # EnumTrueFalse
  "datetime": datetime,
  "created_at": datetime,
  "updated_at": datetime
}
```

#### Action Event Model
```python
{
  "id": int,
  "content": str,
  "user": str,
  "from_event_id": int,
  "from_event_type": str,
  "datetime": datetime,
  "created_at": datetime,
  "updated_at": datetime
}
```

### 5.3 Enum Types

#### EnumDeviceType
```
NONE, Controller, Multi, Fence, Underground, Contact, PIR,
IoController, Laser, Cable, IpCamera, SmartSensor, SmartSensor2,
SmartCompound, IpSpeaker, Radar, OpticalCable, Fence_Group
```

#### EnumDeviceStatus
```
ACTIVATED, ERROR, DEACTIVATED
```

#### EnumCameraMode
```
NONE, ONVIF, EMSTONE_API, INNODEP_API, ETC
```

#### EnumCameraType
```
NONE, FIXED, PTZ, FISHEYES, THERMAL
```

#### EnumEventType
```
None, Intrusion, ContactOn, ContactOff, Connection, Action, Fault, WindyMode
```

#### EnumDetectionType
```
NONE, CABLE_CUTTING, CABLE_CONNECTED, PIR_SENSOR, THERMAL_SENSOR,
VIBRATION_SENSOR, CONTACT_SENSOR, DISTANCE_SENSOR
```

#### EnumFaultType
```
FAULT_CONTROLLER, FAULT_FENCE, FAULT_MULTI, FAULT_CABLE_CUTTING, FAULT_ETC
```

#### EnumTrueFalse
```
False, True
```

---

## 6. Docker Configuration

### 6.1 Container Specifications
- **Container Name**: `api_server-fastapi`
- **Base Image**: `python:3.11-slim`
- **Port Mapping**: `8000:8000`
- **Volume Mounts**:
  - `./data:/app/data` (SQLite DB 파일)
  - `./logs:/app/logs` (로그 파일)

### 6.2 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.3 Docker Compose (Optional)
```yaml
version: '3.8'

services:
  api-server:
    container_name: api_server-fastapi
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - AUTH_MODE=token
      - JWT_SECRET_KEY=your-secret-key-change-in-production
      - JWT_ALGORITHM=HS256
      - JWT_EXPIRATION_HOURS=24
      - DATABASE_URL=sqlite:///./data/gop.db
    restart: unless-stopped
    networks:
      - gop-network

networks:
  gop-network:
    driver: bridge
```

---

## 7. API Documentation

### 7.1 OpenAPI/Swagger Integration
FastAPI는 자동으로 다음 문서화 도구를 제공합니다:

- **Swagger UI**: `http://localhost:8000/docs`
  - 인터랙티브 API 탐색
  - API 테스트 가능
  - Request/Response 예제

- **ReDoc**: `http://localhost:8000/redoc`
  - 깔끔한 문서 레이아웃
  - 읽기 중심 문서화

### 7.2 OpenAPI Specification
- OpenAPI 3.0+ 표준 준수
- JSON Schema 기반 데이터 검증
- API 스펙 다운로드: `http://localhost:8000/openapi.json`

---

## 8. Development Plan

### 8.1 Project Structure
```
api-test-server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 애플리케이션 엔트리포인트
│   ├── config.py               # 환경 설정
│   ├── database.py             # DB 연결 설정
│   ├── dependencies.py         # 의존성 주입
│   │
│   ├── models/                 # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── device.py           # Controller, Sensor, Camera
│   │   ├── event.py            # Detection, Malfunction, etc.
│   │   └── user.py             # User 모델
│   │
│   ├── schemas/                # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── event.py
│   │   ├── user.py
│   │   └── common.py           # 공통 응답 스키마
│   │
│   ├── routers/                # API 라우터
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── controllers.py
│   │   ├── sensors.py
│   │   ├── cameras.py
│   │   ├── detections.py
│   │   ├── malfunctions.py
│   │   ├── connections.py
│   │   └── actions.py
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   └── event_service.py
│   │
│   ├── repositories/           # 데이터 액세스
│   │   ├── __init__.py
│   │   ├── device_repository.py
│   │   └── event_repository.py
│   │
│   └── utils/                  # 유틸리티
│       ├── __init__.py
│       ├── auth.py             # JWT 생성/검증
│       ├── enums.py            # Enum 정의
│       └── exceptions.py       # 커스텀 예외
│
├── tests/                      # 테스트 코드
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_devices.py
│   └── test_events.py
│
├── data/                       # SQLite DB 파일
│   └── gop.db
│
├── logs/                       # 로그 파일
│   └── app.log
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── PRD.md                      # 본 문서
```

### 8.2 Dependencies (requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
```

### 8.3 Development Phases

#### Phase 1: Project Setup (Week 1)
- [ ] 프로젝트 구조 생성
- [ ] FastAPI 애플리케이션 초기화
- [ ] SQLite 데이터베이스 설정
- [ ] Docker 환경 구성
- [ ] 개발 환경 구축

#### Phase 2: Authentication System (Week 1-2)
- [ ] JWT 인증 구현
- [ ] User 모델 및 스키마
- [ ] 로그인/토큰 발급 API
- [ ] 인증 미들웨어
- [ ] 공개/토큰 모드 전환 기능

#### Phase 3: Device APIs (Week 2-3)
- [ ] Controller CRUD API
- [ ] Sensor CRUD API
- [ ] Camera CRUD API
- [ ] 필터링 및 페이징
- [ ] 관계형 데이터 조회 (include_sensors, include_controller)

#### Phase 4: Event APIs (Week 3-4)
- [ ] Detection Event CRUD API
- [ ] Malfunction Event CRUD API
- [ ] Connection Event CRUD API
- [ ] Action Event CRUD API
- [ ] 날짜 범위 필터링

#### Phase 5: Testing & Documentation (Week 4)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트
- [ ] API 문서화 완성
- [ ] Docker 이미지 빌드 및 테스트

#### Phase 6: Deployment & Monitoring (Week 5)
- [ ] 프로덕션 설정
- [ ] 로깅 시스템
- [ ] 에러 모니터링
- [ ] 성능 튜닝

---

## 9. Non-Functional Requirements

### 9.1 Performance
- API 응답 시간: < 200ms (일반 쿼리)
- 동시 접속: 최소 100 concurrent users
- 페이징 지원: 대용량 데이터 처리

### 9.2 Security
- JWT 토큰 기반 인증
- 비밀번호 해싱 (bcrypt)
- CORS 설정
- Rate Limiting (선택)
- SQL Injection 방지 (SQLAlchemy ORM)

### 9.3 Reliability
- Docker 컨테이너 자동 재시작
- 에러 로깅 및 추적
- 데이터베이스 트랜잭션 보장
- 적절한 HTTP 상태 코드 반환

### 9.4 Maintainability
- 클린 아키텍처 (Router → Service → Repository)
- 타입 힌팅 및 Pydantic 검증
- 일관된 코드 스타일 (PEP 8)
- 자동 API 문서 생성

### 9.5 Scalability
- 수평 확장 가능한 구조
- 데이터베이스 마이그레이션 지원 (Alembic)
- 환경 변수 기반 설정

---

## 10. Success Criteria

### 10.1 Functional Completeness
- [ ] GOP_Restful_Api_연동설계.md의 모든 API 엔드포인트 구현
- [ ] 두 가지 인증 모드 정상 동작
- [ ] CRUD 작업 모두 지원
- [ ] 필터링, 정렬, 페이징 기능 동작

### 10.2 Quality Metrics
- [ ] 테스트 커버리지 > 80%
- [ ] API 응답 시간 < 200ms
- [ ] 제로 다운타임 배포
- [ ] Docker 컨테이너 정상 실행

### 10.3 Documentation
- [ ] OpenAPI 문서 완성
- [ ] README 작성
- [ ] 배포 가이드 작성
- [ ] API 사용 예제 제공

---

## 11. Risks & Mitigations

### 11.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| 포트 충돌 | High | Low | 포트 8000 사용, docker-compose로 관리 |
| SQLite 성능 | Medium | Medium | 필요시 PostgreSQL 마이그레이션 가능하도록 설계 |
| 인증 보안 | High | Low | JWT 표준 준수, 환경 변수로 비밀키 관리 |
| Docker 빌드 실패 | Medium | Low | Dockerfile 테스트 및 CI/CD 파이프라인 구축 |

### 11.2 Schedule Risks
- 기능 범위가 큼 → MVP 먼저 구현 후 점진적 기능 추가
- 기존 컨테이너와 통합 이슈 → 독립적으로 동작하도록 설계

---

## 12. Future Enhancements

### 12.1 Version 2.0 Features
- PostgreSQL 지원
- Redis 캐싱
- WebSocket 실시간 이벤트 알림
- 파일 업로드 (카메라 이미지)
- 백업/복원 기능
- Role-based Access Control (RBAC)

### 12.2 DevOps Improvements
- CI/CD 파이프라인 (GitHub Actions)
- 자동화된 테스트
- 로그 수집 (ELK Stack)
- 모니터링 (Prometheus + Grafana)

---

## 13. References

### 13.1 Documentation
- [GOP_Restful_Api_연동설계.md](./Docs/GOP_Restful_Api_연동설계.md) - API 설계 사양서
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### 13.2 Related Systems
- tuberank-flask: 기존 Flask 애플리케이션 (포트 5000)
- tuberank-postgres: PostgreSQL 데이터베이스 (포트 5432)
- tuberank-nginx: Nginx 웹서버 (포트 80)

---

## Appendix A: Environment Variables

```bash
# Authentication
AUTH_MODE=token                 # token or public
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database
DATABASE_URL=sqlite:///./data/gop.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# CORS
CORS_ORIGINS=["*"]              # Production에서는 제한 필요
```

---

## Appendix B: Initial Admin User

```python
# 초기 관리자 계정 (자동 생성)
username: admin
password: admin123
role: admin
```

⚠️ **프로덕션 환경에서는 반드시 비밀번호를 변경하세요.**

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-11 | API Team | Initial PRD creation |

---

**Approval**

- Product Owner: _______________  Date: ___________
- Tech Lead: ___________________  Date: ___________
- QA Lead: _____________________  Date: ___________
