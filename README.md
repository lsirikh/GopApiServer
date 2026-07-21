# GOP RESTful API Server

![version](https://img.shields.io/badge/version-v6.3.0-navy)
![python](https://img.shields.io/badge/python-3.11-blue)
![framework](https://img.shields.io/badge/FastAPI-async-teal)
![sqlalchemy](https://img.shields.io/badge/SQLAlchemy-2.x%20async-red)
![postgres](https://img.shields.io/badge/PostgreSQL-16-blue)
![status](https://img.shields.io/badge/release-2026--07--13-success)

GOP 통제시스템 연동을 위한 **RESTful API 서버**. 6개 컴포넌트 통합 아키텍처(C1~C6)의 백엔드로 동작하며, 장치 관리 · 이벤트 추적 · 리포트 생성 · RBAC 인가를 제공한다.

> **현재 버전**: v6.3.0 (2026-07-13 승격 — v6.0 Async 대전환 → 후속 21 topic 확정, `release/v6.0` 브랜치).
> 전체 변경 이력은 [CHANGELOG.md](CHANGELOG.md) 참조.
>
> 🚧 **진행 중 (v6.3 후속 · `grant-enforcement-hardening`)** — 권한부여(grant) 시간기반 집행 하드닝:
> - **Phase 1 검증부채**: 경계초(`valid_until==now`) 삼중 회귀 · `AUTH_MODE=token` 집행 E2E · `async_db` 격리(운영 DB 무접촉)
> - **Phase 2 통지/집행**: per-grant 실시간 만료 통지(FR-07) · 스윕 주기 설정화(`GRANT_SWEEP_INTERVAL_MINUTES`) · NATS 통지 게이트(FR-06) · matrix `default-deny` observe/enforce 모드(`MATRIX_DENY_MODE`, 기본 `off`=현행 보존)
> - **상태**: 코드·테스트 완료(로컬, 신규 44+ passed). **실제 활성**(NATS `NATS_REVOKE_ENABLED` flip · `default-deny` enforce)은 라우트 audit·클라 조율 후 **배포 게이트**.
> - 근거: [PRD](docs/prds/grant-enforcement-hardening-prd.md) · [시뮬 128/128](docs/Analysis/grant-enforcement-sim/SIMULATION_REPORT.md) · [GIS 회신](docs/Analysis/Grant_Enforcement_Server_Analysis_REPLY.md)

---

## 목차

- [최근 릴리즈 (v6.0)](#최근-릴리즈-v60--async-대전환)
- [기술 스택](#기술-스택)
- [주요 기능](#주요-기능)
- [Quick Start](#quick-start)
- [접속 정보](#접속-정보)
- [아키텍처](#아키텍처)
- [환경 변수](#환경-변수)
- [API 엔드포인트](#api-엔드포인트-요약)
- [로컬 개발](#로컬-개발-docker-없이)
- [테스트](#테스트)
- [프로젝트 구조](#프로젝트-구조)
- [문서](#문서)

---

## 최근 릴리즈 (v6.0) — Async 대전환

**태그**: `v6.0` (커밋 `61e46fe`, 브랜치 `release/v6.0`)
**Swagger `info.version`**: `6.0.0`

### 성과 요약

| 항목 | 결과 |
|---|---|
| **문서 A-7 근본 봉합** | 6/6 완결 (batch queue + PostgreSQL 파티셔닝 포함) |
| **async 전환 라우터** | 41개 / 41개 (100%) |
| **RBAC 매트릭스 등록** | 약 99 endpoint |
| **api_logs 파티셔닝** | 월별 partition + before-partition catch-all |
| **INSERT 파이프라인** | `asyncio.Queue` batch consumer (100건 / 500ms) |
| **자가 회복 인프라** | Docker `autoheal` 컨테이너 (healthcheck unhealthy 감시) |
| **회귀 시나리오** | 247 / 247 PASS |

### 핵심 스택 전환

- `sync SessionLocal` → `AsyncSessionLocal` (dual-stack 병존)
- `db.query(...)` → `await db.execute(select(...))` (약 397 호출부)
- Report Service 완전 async(`ReportServiceAsync`, 20 async 메서드)
- init 모듈 4종 async 화(`init_db` / `init_server_data` / `init_report_data` / `init_sample_data`)
- Polymorphic eager load: `selectin_polymorphic(Device, [...])`

### 후속 안정화 (2026-07-04~07, `release/v6.0` 위 소분 태그)

> clone 배포·운영 실측으로 드러난 결함을 근본 수정. 각 `v6.0-{topic}` 태그로 누적.

| 영역 | 태그 | 요약 |
|---|---|---|
| 리포트 | `report_fixes` / `report_lifecycle_persistence` / `report_progress_perf` / `report_date_range` | 그리드 컬럼 확장·필터 통일, PDF 영속화·수명주기, 진행률+stall 워치도그+SQL 집계, 커스텀 날짜 범위 |
| 인증·계정 | `auth_mode_secure_default` / `account_rbac` / `account_managers_expand` / `role_seed_normalize` | AUTH_MODE=token 기본, ADMIN 9종 seed, role 규칙 v5.3 2종 재적용 |
| API 계약 | `servers_port_response_relax` / `users_role_response_relax` / `response_schema_audit` | 응답 스키마 strict Enum 지뢰 전수 완화(21건) — 옛/임의 값 목록 500 원천 차단 |
| 안정성 | `clone_deploy_bugfix` / `force_logout_tz_fix` | 신규 PC 6버그(startup 자동 마이그레이션 포함), 세션 강제 로그아웃 500 수정 |
| 배포·인프라 | `rename_pids` / `cert_installer_fix` / `installer_ps2exe_path_fix` / `bootstrap_automation` | 컨테이너 `pids-api-*` 리네임, HTTPS 인증서 fail-fast, PS2EXE 경로 근본 수정, 1-Click bootstrap.ps1 |

---

## 기술 스택

| 계층 | 스택 |
|---|---|
| **Runtime** | Python 3.11 |
| **Framework** | FastAPI (async) + Pydantic v2 |
| **ORM** | SQLAlchemy 2.x (Async ORM, AsyncSession) |
| **DB Driver** | asyncpg (async) + psycopg2 (dual-stack 유지) |
| **Database** | PostgreSQL 16 |
| **Auth** | JWT (HS256, 24h access + 7d refresh), RBAC matrix enforcer |
| **Messaging** | NATS (SYNC 이벤트 발행 · Force-Logout revoke publisher) |
| **Report** | Playwright (Chromium) — HTML → PDF |
| **Container** | Docker Compose (`pids-api-server` / `pids-api-postgres` / `pids-api-autoheal` / `pids-api-gis-ingest` / `pids-api-db-monitor` / `pids-api-db-admin`) |
| **Test** | pytest + pytest-asyncio (dual-stack fixture) |
| **Docs** | Swagger UI / ReDoc (한글 문서화) |

---

## 주요 기능

### Device Management (장치 관리)
- Controller / Sensor / Camera / Speaker / Lamp / Enclosure 폴리모픽 CRUD
- Device Group / ROI / XY Point (감시금지구역 포함) 관리
- Camera Preset · Settings · Thumbnails

### Event Tracking (이벤트 추적)
- Detection / Malfunction / Connection / Action 이벤트 CRUD
- Detection Log 상세 이력 (조치보고 흐름 포함)
- Event Statistics (통계 집계 API)
- Event Mapping (Camera / Speaker / Lamp) — 이벤트 트리거 시 장치 연동
- GIS Tracking (keyset cursor · `track_points` 인제스트 워커)

### Reports (리포트)
- 정형 보고서 HTML 렌더 → PDF 생성 (Playwright)
- 리포트 마스터 데이터 async 파이프라인
- 미리보기 라우트 (`/api/reports/preview`)

### RBAC (인가)
- User / Admin 2계층 인가
- SuperUser(ADMIN) · UserGroupGrant(USER) 그룹 permissions 게이팅
- `matrix_enforcer` — 라우터 · endpoint · method 단위 정합 검사
- Force-Logout (per-session NATS subject + HMAC-SHA256 서명)

### Monitoring & Ops
- API 로그 배치 큐 (`asyncio.Queue`) → 파티션 테이블 INSERT
- Health endpoint 경량화 (`/api/tracking/health`, 무인증 JSON)
- Docker `autoheal` unhealthy 감지 시 자동 재기동
- Docker 로그 회전 (`json-file` max-size 10m × 3 파일)

---

## Quick Start

> **처음 배포하는 PC (Windows)**: 아래 **1-Click 방식** 권장 — `bootstrap.ps1` 하나가 인증서 발급 + 컨테이너 기동까지 자동.

### 🚀 1-Click 배포 (신규 PC 권장)

Windows Explorer 에서 `bootstrap.ps1` 우클릭 → **PowerShell 로 실행** (UAC 승인).
또는 PowerShell 창에서:

```powershell
git clone <repo-url>
cd api-test-server
powershell -ExecutionPolicy Bypass -File bootstrap.ps1
```

이 스크립트가 자동으로 처리하는 것:

| 단계 | 내용 |
|---|---|
| 0 | 관리자 권한 UAC 자동 상승 (mkcert 로컬 CA 등록에 필수) |
| 1 | Docker Desktop 실행 상태 확인 · `.env` 자동 생성 |
| 2 | `certs/server.crt` · `server.key` 없으면 `certs/server_install.exe` 자동 실행 → mkcert 자동 다운로드 + rootCA 등록 + 인증서 발급 |
| 3 | `docker compose build` |
| 4 | `docker compose up -d` + `pids-api-server` healthy 대기 (최대 120초) |
| 5 | 접속 URL · 기본 계정 · 클라 rootCA 배포 방법 안내 |

**옵션 스위치**:
| 스위치 | 용도 |
|---|---|
| `-SkipCerts` | 인증서 발급 스킵 (이미 발급된 경우) |
| `-SkipDocker` | 인증서만 발급, docker 실행 스킵 |
| `-Rebuild` | `docker compose build --no-cache` |
| `-AllowHttpFallback` | 인증서 없이 HTTP 로 기동 (개발 편의, **프로덕션 금지**) |

### 🔧 수동 배포 (Linux / macOS / 세부 제어)

```bash
# 1. 저장소 준비
git clone <repo-url>
cd api-test-server
cp .env.example .env

# 2. HTTPS 인증서 발급
# Windows: certs\server_install.exe 를 관리자 권한으로 실행 (mkcert 자동 발급)
# Linux/macOS: mkcert 를 직접 설치 후 아래 실행
mkcert -install
mkcert -cert-file certs/server.crt -key-file certs/server.key localhost 127.0.0.1 ::1 host.docker.internal

# 3. 컨테이너 기동
docker compose up -d --build

# (선택) 인증서 없이 HTTP 로 급히 기동 (프로덕션 금지)
ALLOW_HTTP_FALLBACK=true docker compose up -d --build
```

### 로그인

```
기본 관리자    : admin / admin123
매니저 계정 8종 : m_manager, vms_manager, popup_manager,
                CameraManager, BroadcastingManager, QLiteLampManager,
                NVRManager, EnclosureManager  (모두 pw: sensorway1)
```

> ⚠️ 매니저 계정 pw `sensorway1` 은 **dev/시연 기본값**. 프로덕션에서는 최초 로그인 후 즉시 변경.

Swagger UI 우측 상단 **Authorize** 버튼 → Bearer token 입력 후 보호 endpoint 호출.

### 상태 확인

```bash
docker compose ps
docker logs -f pids-api-server
```

### 종료

```bash
docker compose stop       # 컨테이너 중지 (데이터 유지)
docker compose down       # 컨테이너 삭제 (데이터·볼륨 유지)
docker compose down -v    # 데이터·볼륨까지 완전 초기화 ⚠️
```

### 클라이언트 PC 에 rootCA 배포

브라우저/.NET 클라이언트가 mkcert 발급 인증서를 신뢰하려면 각 클라 PC 에 rootCA 등록 필요:

```
1. certs/client_install.exe 를 클라 PC 로 복사 (USB, 파일공유 등)
2. 클라 PC 에서 관리자 권한으로 실행
3. Windows LocalMachine\Root 저장소에 rootCA 자동 등록
4. 브라우저/앱 재시작 → HTTPS 경고 없이 접속
```

---

## 접속 정보

| 서비스 | 포트 | URL | 설명 |
|---|---|---|---|
| API Server | 8000 | https://localhost:8000 | FastAPI 서버 (HTTPS 우선, HTTP fallback) |
| Swagger UI | 8000 | https://localhost:8000/docs | API 문서 (인터랙티브) |
| ReDoc | 8000 | https://localhost:8000/redoc | API 문서 (읽기 전용) |
| Log Viewer | 8000 | https://localhost:8000/api/logs/viewer | 웹 기반 API 로그 뷰어 |
| Reports Preview | 8000 | https://localhost:8000/api/reports/preview | 정형 보고서 HTML 미리보기 |
| Health | 8000 | https://localhost:8000/api/tracking/health | 경량 헬스체크 (무인증 JSON) |
| Adminer | 8080 | http://localhost:8080 | PostgreSQL 웹 관리자 |

**Adminer 접속 정보**
- Server: `postgres`
- User: `gop_user`
- Password: `gop_pass`
- Database: `gop`

---

## 아키텍처

```
┌────────────────────────────────────────────────────────────────────┐
│                       Client Layer (C1~C6)                         │
│  Central UI / Ironwall.Dotnet / DBApi / db_monitor / RtspViewer    │
└──────────────────────┬─────────────────────────────────────────────┘
                       │ HTTPS + JWT (Bearer)
                       ▼
┌────────────────────────────────────────────────────────────────────┐
│                  pids-api-server (FastAPI · Async)                 │
│  ┌──────────────┬───────────────┬──────────────┬──────────────┐    │
│  │  Middleware  │  RBAC Matrix  │  Routers x41 │   Services   │    │
│  │ Request ID · │  Enforcer     │ (all async)  │ audit/grant/ │    │
│  │ API Log(Q)   │  Auth(async)  │              │ session_sweep│    │
│  └──────┬───────┴───────┬───────┴──────┬───────┴──────┬───────┘    │
│         │               │              │              │            │
│         ▼               ▼              ▼              ▼            │
│   asyncio.Queue    JWT+matrix     AsyncSession    to_thread        │
│   batch(100/500ms) permission_map  selectinload    (bcrypt/PDF)    │
└────────┬────────────────────────────┬──────────────────────────────┘
         │                            │
         │ INSERT batch               │ await db.execute(select())
         ▼                            ▼
┌───────────────────────┐   ┌────────────────────────────────────────┐
│   api_logs partitions │   │       PostgreSQL 16 (asyncpg)          │
│   (월별 + catch-all)  │   │       + statement-level NATS trigger   │
└───────────────────────┘   └────────────────┬───────────────────────┘
                                             │ NATS SYNC
                     ┌───────────────────────┼───────────────────────┐
                     ▼                       ▼                       ▼
              ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
              │  db-monitor   │      │  gis-ingest   │      │  autoheal     │
              │ (NATS pub)    │      │ (NATS sub →   │      │ (docker.sock  │
              │               │      │  track_points)│      │  reader)      │
              └───────────────┘      └───────────────┘      └───────────────┘
```

- **매 요청 이벤트루프 자유**: async 전환으로 `MissingGreenlet` 회피, 커넥션 획득 절감
- **Dual-stack 원칙**: sync 경로 유지(안전 롤아웃), 신규 라우터는 async 우선

---

## 환경 변수

전체 변수는 [`.env.example`](.env.example) 참조. 핵심 항목:

| 변수 | 기본값 | 설명 |
|---|---|---|
| `AUTH_MODE` | `token` | `public` = 무인증 통과 / `token` = Bearer 필수 + matrix_enforcer 활성 (v5.4~) |
| `JWT_SECRET_KEY` | (dev 값) | **운영 배포 시 반드시 랜덤 값으로 교체** |
| `JWT_EXPIRATION_HOURS` | `24` | access token 유효시간 |
| `API_DATABASE_URL` | `postgresql://gop_user:gop_pass@postgres:5432/gop` | API 서버 → Postgres |
| `MONITOR_DATABASE_URL` | (동일) | db-monitor · gis-ingest 전용 |
| `INIT_SAMPLE_DATA` | `true` | 빈 DB일 때 시드 자동 삽입 (v4.6 차장님 명세) |
| `NATS_URL` | `nats://nats-server-01:4222` | NATS 클러스터 |
| `UNIT_ID` | `unit001` | 이 유닛의 NATS subject 네임스페이스 |
| `NATS_REVOKE_ENABLED` | `false` | Force-Logout NATS revoke 실발행 스위치 (3게이트 통과 후 true) |
| `REVOKE_SIGNING_KEY` | (dev 값) | HMAC-SHA256 서명 키, JWT_SECRET_KEY 와 반드시 분리 |
| `LOG_LEVEL` | `INFO` | 애플리케이션 로그 레벨 |
| `CORS_ORIGINS` | `["*"]` | 프로덕션에서는 명시 도메인으로 좁힐 것 |

---

## API 엔드포인트 요약

전체 스펙은 Swagger UI 및 [`GOP_Restful_Api_연동설계.md`](GOP_Restful_Api_연동설계.md) 참조.

### 주요 라우터 그룹

| 그룹 | 대표 경로 | 비고 |
|---|---|---|
| Authentication | `/api/auth/login`, `/logout`, `/me`, `/refresh` | Force-Logout · session 관리 |
| Accounts / Users | `/api/users`, `/api/user-groups`, `/api/user-sessions` | RBAC ADMIN 전용 게이트 |
| Devices | `/api/devices/controllers`, `/sensors`, `/cameras`, `/speakers`, `/lamps`, `/enclosures` | 폴리모픽 CRUD |
| Device Groups / ROI | `/api/device-groups`, `/rois`, `/xypoints` | 감시금지구역(`is_restricted_zone`) 포함 |
| Camera 부속 | `/api/cameras/presets`, `/settings`, `/thumbnails` | Preset · Settings 통합 |
| Events | `/api/events/detections`, `/malfunctions`, `/connections`, `/actions` | Detection Log 포함 |
| Event Statistics | `/api/events/statistics` | 통계 집계 |
| Event Mappings | `/api/integrations/event-mappings`, `/camera-event-mappings`, `/lamp-`, `/speaker-` | Bulk API 지원 |
| Servers | `/api/servers`, `/categories`, `/metrics`, `/summary` | 서버 모니터링 (26종) |
| Files / Configs | `/api/files/groups`, `/api/settings`, `/api/proxy-settings`, `/api/config-change-logs` | 시스템 설정 |
| Reports | `/api/reports`, `/preview`, `/status` | HTML → PDF 생성 |
| Tracking (GIS) | `/api/tracking/points`, `/health` | keyset cursor (limit 1~5000) |
| Audit / System | `/api/audit-logs`, `/api/system-events` | append-only |
| Logs | `/api/logs`, `/api/logs/viewer` | 배치 큐 파티셔닝 |

### RBAC 정책 요약

- `AUTH_MODE=token` 모드에서 대부분 endpoint는 Bearer JWT 필수
- ADMIN 전용 게이트: 계정/그룹 관리, 권한 부여(`grants`), 시스템 설정 변경
- USER는 `UserGroupGrant` 그룹의 permissions 매트릭스에 정의된 endpoint만 접근
- 자기 계정 self-service (예: `/auth/me`, `/logout`) 는 USER도 허용

---

## 로컬 개발 (Docker 없이)

```bash
# 1. 가상환경
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS/Linux

# 2. 의존성
pip install -r requirements.txt

# 3. 별도 PostgreSQL 필요 (또는 docker-compose up postgres만 기동)

# 4. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 테스트

```bash
# 전체
python -m pytest

# 커버리지
python -m pytest --cov=app

# 특정 파일
python -m pytest tests/test_detection_event_model.py

# async fixture (v6.0 후속 P1 반영)
python -m pytest tests/test_report_service_async.py
```

- **Fixture 원칙**: SQLite in-memory (unit) + PostgreSQL 컨테이너 (integration)
- **Dual-stack**: 신규 async 테스트는 `pytest-asyncio` 기반
- **명명 규칙**: `test_should_{expected_behavior}_when_{condition}`

---

## 프로젝트 구조

```
api-test-server/
├── app/
│   ├── main.py                     # FastAPI 진입점 (async lifespan)
│   ├── config.py                   # 설정
│   ├── database.py                 # sync + async engine (dual-stack)
│   ├── dependencies.py             # get_db / get_async_db
│   ├── models/                     # SQLAlchemy 모델 (polymorphic Device/Event)
│   ├── schemas/                    # Pydantic v2 스키마
│   ├── routers/                    # 41 라우터 (전부 async)
│   ├── services/                   # 도메인 서비스 (dual-stack)
│   │   ├── audit_service.py
│   │   ├── grant_sweep_service.py
│   │   ├── session_sweep_service.py
│   │   ├── api_logs_sweep_service.py
│   │   ├── token_blacklist_service.py
│   │   ├── settings_service.py
│   │   └── report_service.py       # ReportServiceAsync (v6.0 후속 P3)
│   ├── middleware/
│   │   ├── request_id.py
│   │   └── logging.py              # asyncio.Queue batch consumer (v6.0 후속 P4)
│   ├── auth/                       # JWT + matrix_enforcer + permission_map
│   ├── migrations/                 # 수동 SQL 마이그레이션
│   └── utils/
│       ├── enums.py
│       ├── init_db.py              # async (v6.0 후속 P2)
│       ├── init_server_data.py     # async
│       ├── init_report_data.py     # async
│       └── init_sample_data.py     # async (_bulk_insert_async 500-row chunks)
├── db_monitor/                     # NATS pub 워커 (별도 컨테이너)
├── gis_ingest/                     # NATS sub → track_points 워커
├── tests/                          # pytest + pytest-asyncio
├── data/                           # 컨테이너 데이터 mount (프로필 사진 등)
├── logs/                           # 애플리케이션 로그
├── certs/                          # HTTPS 인증서 (mkcert, git-ignored)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── CHANGELOG.md
├── GOP_Restful_Api_연동설계.md
├── docs/
│   ├── INDEX.md                    # 문서 인덱스
│   ├── Manual.md                   # 하네스 전체 설명
│   └── memory/session-context.md   # 세션 상태
└── README.md                       # 이 파일
```

> DB 데이터는 Docker volume (`api-test-pgdata`)에 영구 저장. `docker-compose down -v`만 데이터 초기화.

---

## 문서

| 문서 | 설명 |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | 전체 차수 변경 이력 (Keep a Changelog 형식) |
| [GOP_Restful_Api_연동설계.md](GOP_Restful_Api_연동설계.md) | API 상세 설계 명세서 (마스터, v6.0) |
| [docs/INDEX.md](docs/INDEX.md) | docs/ 산출 문서 인덱스 |
| [docs/Manual.md](docs/Manual.md) | 하네스 · 스킬 · Hook 전체 매뉴얼 |
| [docs/GOP_스키마_전체.md](docs/GOP_스키마_전체.md) | DB 스키마 마스터 |
| [docs/GOP_ForceLogout_Activation_Guide.md](docs/GOP_ForceLogout_Activation_Guide.md) | Force-Logout 활성화 3게이트 절차 |
| `.env.example` | 환경변수 전체 목록 + 주석 |

---

## 릴리즈 이력 (요약)

전체는 [CHANGELOG.md](CHANGELOG.md) 참조.

| 버전 | 날짜 | 헤드라인 |
|---|---|---|
| **v6.0** | 2026-07-03 | **Async 대전환** — 41 라우터 async, GOPDB A-7 6/6 완결, autoheal + partition |
| v5.4 | 2026-07-03 | Reports RBAC + `AUTH_MODE=token` 기본화 + A-7 저리스크 4건 |
| v5.2 | 2026-06-30 | Force-Logout jti + PG statement_timeout + Docker 로그 회전 |
| v5.0 | 2026-06-29 | 그룹 권한 관리 endpoint (POST 전용 ADMIN 게이트) |
| v4.12 | 2026-06-27 | RBAC ADMIN 전용 게이트 (계정 8 endpoint) |
| v4.11 | 2026-06-26 | Tracking keyset cursor + 프로필 사진 파일시스템 저장 + audit FK 익명화 예외 |
| v4.10 | 2026-06-25 | HTTPS 도입 (mkcert + Inno Setup rootCA) |
| v4.8 | 2026-06-22 | DELETE 응답 envelope sweep (15 endpoint) |
| v4.6 | 2026-06-19 | Camera Preset 감시금지구역 + 시드 재설계 |
| v4.3 | 2026-06-17 | ActionEvent 1:N + Bulk API 7건 + statement-level NATS |
| v1.9 | 2025-12-29 | Server Monitoring API + 한글 Swagger |

---

## 라이선스 · 문의

내부 프로젝트. 문의는 프로젝트 리드(이기호 차장) 또는 이슈 트래커.

---

**버전**: v6.0.0
**최종 업데이트**: 2026-07-03
**브랜치**: `release/v6.0`
