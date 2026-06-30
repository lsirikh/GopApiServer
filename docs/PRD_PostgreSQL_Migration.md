# PRD: SQLite → PostgreSQL 마이그레이션

**문서 버전**: v1.0
**작성일**: 2026-03-04
**상태**: Proposed
**관련 문서**:
- GOP_Restful_Api_연동설계.md
- GOP_스키마_전체.md

---

## 1. 개요

### 1.1 목적

운영 환경에서 발생하는 **SQLAlchemy QueuePool 고갈 오류**를 근본적으로 해결하기 위해 데이터베이스를 SQLite에서 PostgreSQL로 교체합니다.

### 1.2 배경 및 문제점

서브시스템 API 연동 중 아래 오류가 발생하고 있습니다.

```
QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 30.00
```

**오류 원인 분석:**

| 항목 | SQLite 동작 | 결과 |
|------|------------|------|
| 동시 쓰기 | 파일 레벨 락(WAL/Exclusive) — 단일 writer | 다중 요청이 락 해제 대기하며 커넥션 점유 |
| QueuePool 기본값 | pool_size=5, max_overflow=10 → 최대 15 커넥션 | 15개 커넥션이 모두 락 대기 상태로 고갈 |
| 신규 요청 | pool에 커넥션 없음 → 30초 대기 | 타임아웃 → 클라이언트 요청 실패 |

SQLite는 **단일 프로세스 임베디드 DB**로 설계되어 다중 동시 접속 서버 환경에 적합하지 않습니다. QueuePool 수치를 늘려도 SQLite 파일 락 특성상 근본 해결이 되지 않습니다.

### 1.3 목표

- QueuePool 고갈 오류 완전 제거
- 다중 동시 커넥션 지원 (pool_size 설정 가능)
- 기존 API 동작 변경 없음 (하위 호환 유지)
- 코드 변경 최소화

---

## 2. 변경 범위

### 2.1 변경 파일 목록

| 파일 | 변경 유형 | 변경 내용 |
|------|----------|----------|
| `app/database.py` | 수정 | `connect_args` 제거, Pool 설정 추가 |
| `requirements.txt` | 수정 | `psycopg2-binary` 추가 |
| `Dockerfile` | 수정 | `libpq-dev` 시스템 패키지 추가 |
| `docker-compose.yml` | 수정 | `api_server-fastapi` DATABASE_URL 교체, `db-admin`(sqlite-web) → Adminer 교체, `postgres` 서비스 추가 |
| `.env` | 수정 | `DATABASE_URL` 교체 |

### 2.2 변경 불필요 목록

- 모든 모델 파일 (`app/models/`) — SQLAlchemy ORM이 방언 자동 처리
- 모든 라우터 (`app/routers/`) — 쿼리 코드 변경 없음
- 모든 스키마 (`app/schemas/`) — 변경 없음
- `app/dependencies.py` — `get_db()` 변경 없음
- `app/config.py` — `DATABASE_URL` 환경변수 방식 유지

---

## 3. 상세 설계

### 3.1 `app/database.py` 변경

**현재:**
```python
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 전용
)
```

**변경 후:**
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,        # 기본 커넥션 수
    max_overflow=20,     # 최대 초과 커넥션 수 (총 30)
    pool_timeout=30,     # 커넥션 대기 타임아웃 (초)
    pool_pre_ping=True,  # 커넥션 유효성 사전 확인 (stale connection 방지)
    pool_recycle=1800,   # 30분마다 커넥션 재생성 (장시간 idle 커넥션 정리)
)
```

`check_same_thread=False`는 SQLite 전용 인자이므로 제거합니다. PostgreSQL은 스레드 안전(thread-safe)이므로 불필요합니다.

### 3.2 `requirements.txt` 변경

```text
# 추가
psycopg2-binary==2.9.9
```

`psycopg2-binary`는 PostgreSQL Python 드라이버입니다. `-binary` 패키지는 컴파일 없이 설치 가능합니다.

### 3.3 `Dockerfile` 변경

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    fonts-nanum \
    fontconfig \
    libpq-dev \        # PostgreSQL 클라이언트 라이브러리 추가
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv
```

### 3.4 `docker-compose.yml` 변경

**현재 구성:**
```
api_server-fastapi  ← DATABASE_URL=sqlite:///./data/gop.db
db-admin            ← coleifer/sqlite-web (SQLite 전용 웹 UI, port 8080)
```

**변경 후 구성:**
```
postgres            ← PostgreSQL 16 DB 서버 (신규)
api_server-fastapi  ← DATABASE_URL=postgresql://... (교체)
db-admin            ← Adminer (PostgreSQL 지원 웹 UI, port 8080으로 유지) (교체)
```

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: gop-postgres
    environment:
      POSTGRES_DB: gop
      POSTGRES_USER: gop_user
      POSTGRES_PASSWORD: gop_pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gop_user -d gop"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  api_server-fastapi:
    container_name: api_server-fastapi
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - AUTH_MODE=public
      - JWT_SECRET_KEY=your-secret-key-change-in-production
      - JWT_ALGORITHM=HS256
      - JWT_EXPIRATION_HOURS=24
      - DATABASE_URL=postgresql://gop_user:gop_pass@postgres:5432/gop  # 변경
      - INIT_SAMPLE_DATA=true
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
    depends_on:
      postgres:
        condition: service_healthy   # DB 준비 완료 후 API 시작 (신규)
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db-admin:
    container_name: db-admin
    image: adminer                   # sqlite-web → Adminer로 교체
    ports:
      - "8080:8080"
    environment:
      ADMINER_DEFAULT_SERVER: postgres
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  pgdata:
```

**Adminer 접속 정보 (port 8080 유지):**

| 항목 | 값 |
|------|-----|
| System | PostgreSQL |
| Server | `postgres` |
| Username | `gop_user` |
| Password | `gop_pass` |
| Database | `gop` |

### 3.5 `.env` 변경

```bash
# 변경 전
DATABASE_URL=sqlite:///./data/gop.db

# 변경 후
DATABASE_URL=postgresql://gop_user:gop_pass@localhost:5432/gop
```

Docker 환경에서는 `docker-compose.yml`의 `environment`로 주입되므로 `.env`는 로컬 개발용입니다.

---

## 4. 데이터 마이그레이션

### 4.1 신규 환경 (데이터 없음)

`initialize_database()`가 `Base.metadata.create_all()`을 호출하므로 **자동으로 PostgreSQL에 테이블 생성**됩니다. 별도 마이그레이션 스크립트 불필요.

```python
# app/utils/init_db.py (기존 로직 — 변경 없음)
def initialize_database():
    Base.metadata.create_all(bind=engine)
    ...
```

### 4.2 기존 SQLite 데이터 이전이 필요한 경우

SQLite → PostgreSQL 데이터 이전은 아래 순서로 진행합니다.

1. `pgloader` 또는 `sqlite3 dump` + `psql import` 사용
2. 또는 `INIT_SAMPLE_DATA=true` 환경변수로 샘플 데이터 재생성

> **현재 운영 데이터가 없다면 신규 구성으로 진행합니다.**

---

## 5. Pool 설정 근거

| 파라미터 | 값 | 근거 |
|---------|-----|------|
| `pool_size` | 10 | 기존 SQLite 기본값 5의 2배. API 서버 단일 인스턴스 기준 적정 |
| `max_overflow` | 20 | 피크 트래픽 대응. 총 최대 30 커넥션 |
| `pool_timeout` | 30 | 기존 SQLite 동작과 동일 유지 |
| `pool_pre_ping` | True | 장시간 idle 후 끊긴 커넥션 사용 방지 |
| `pool_recycle` | 1800 | 30분 이상 idle 커넥션 재생성 (DB 서버 side timeout 대응) |

---

## 6. PostgreSQL 스키마 호환성

SQLAlchemy ORM 레이어가 방언(dialect)을 추상화하므로 대부분의 타입이 자동 변환됩니다.

| SQLite 타입 | PostgreSQL 변환 | 비고 |
|-------------|----------------|------|
| `VARCHAR` | `VARCHAR` | 동일 |
| `INTEGER` | `INTEGER` | 동일 |
| `DATETIME` | `TIMESTAMP` | 자동 변환 |
| `JSON` | `JSON` | 동일 (JSONB 사용 권장 — 추후 개선) |
| `Enum` (String) | `VARCHAR` + CHECK | SQLAlchemy native enum 방식 유지 |

**주의:** SQLAlchemy의 `Enum` 타입을 PostgreSQL에서 사용할 경우, 기본적으로 PostgreSQL ENUM 타입을 생성합니다. 마이그레이션 시 타입 충돌을 방지하려면 `create_constraint=False` 또는 `native_enum=False` 옵션을 고려합니다.

현재 프로젝트는 `SQLEnum(EnumClass)`를 사용하므로 PostgreSQL에서 `CREATE TYPE` 구문이 실행됩니다. `Base.metadata.create_all()`이 이를 자동 처리합니다.

---

## 7. 구현 체크리스트

### Phase 1: 의존성 설치
- [ ] `requirements.txt`에 `psycopg2-binary` 추가
- [ ] `Dockerfile`에 `libpq-dev` 추가

### Phase 2: DB 엔진 설정
- [ ] `app/database.py`에서 `connect_args` 제거
- [ ] Pool 파라미터 (`pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle`) 추가

### Phase 3: 인프라 구성
- [ ] `docker-compose.yml`에 `postgres` 서비스 추가 (healthcheck 포함)
- [ ] `api_server-fastapi` 서비스 `DATABASE_URL` → PostgreSQL URL 교체
- [ ] `api_server-fastapi` 서비스 `depends_on: postgres: condition: service_healthy` 추가
- [ ] `db-admin` 서비스 `coleifer/sqlite-web` → `adminer` 이미지 교체
- [ ] `db-admin` 서비스 `command` 제거, `ADMINER_DEFAULT_SERVER: postgres` 환경변수 추가
- [ ] `pgdata` 볼륨 선언

### Phase 4: 환경변수 설정
- [ ] `.env` 파일 `DATABASE_URL` 교체 (로컬 개발용)

### Phase 5: 검증
- [ ] `docker-compose up` 정상 기동 확인
- [ ] `GET /health` 응답 200 확인
- [ ] 기존 테스트 전체 통과 확인
- [ ] `GET /api/events/statistics/by-device` 응답 정상 확인
- [ ] 동시 요청 테스트 (QueuePool 오류 재현 없음 확인)

---

## 8. 비기능 요구사항

| 항목 | 요구사항 |
|------|---------|
| 하위 호환성 | 모든 기존 API 응답 형식 동일 유지 |
| 성능 | 동시 요청 30개 이상에서 QueuePool 오류 없음 |
| 데이터 정합성 | 기존 샘플 데이터 재생성 가능 (`INIT_SAMPLE_DATA=true`) |
| 무중단 | 기존 SQLite 파일은 백업 보존 (`data/gop.db`) |

---

## 9. 롤백 계획

PostgreSQL 전환 후 문제 발생 시:

1. `docker-compose.yml`에서 `DATABASE_URL`을 `sqlite:///./data/gop.db`로 복원
2. `app/database.py`에서 `connect_args={"check_same_thread": False}` 복원
3. `docker-compose up --build` 재기동

SQLite 파일(`data/gop.db`)은 삭제하지 않으므로 즉시 롤백 가능합니다.
