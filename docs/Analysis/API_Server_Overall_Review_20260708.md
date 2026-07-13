# GOP API 서버 전체 기능 및 개선 필요사항 분석

**작성일**: 2026-07-08  
**검토 기준**: 현재 워크트리 및 실행 중인 Docker Compose 환경  
**API 버전**: Swagger `6.0.0`  
**검토 자료**: `README.md`, `CHANGELOG.md`, `GOP_Restful_Api_연동설계.md`, FastAPI OpenAPI, 애플리케이션 코드, PostgreSQL/NATS/Docker 실환경

---

## 1. 요약

현재 프로젝트는 단순 REST API 서버가 아니라 다음 기능을 묶은 GOP 통합 백엔드다.

- FastAPI 기반 비동기 REST API
- PostgreSQL 16 영속 계층
- JWT 인증 및 사용자 그룹/기간성 Grant 기반 RBAC
- 장치·이벤트·서버·이벤트 매핑 관리
- HTML/Chromium 기반 PDF 보고서 생성
- PostgreSQL 변경 감지 후 NATS SYNC 메시지 발행
- NATS GIS 추적 메시지 수신 후 PostgreSQL 저장
- API 감사·설정 변경·시스템 이벤트 기록
- HTTPS 인증서 및 Windows 1-Click 배포
- Docker healthcheck와 autoheal 기반 운영

코드 생성 OpenAPI 기준으로 **128 path, 241 operation, 276 schema**가 존재한다. 주요 기능은 폭넓게 구현되어 있고 최근 v6.0에서 async 전환과 배포 안정화가 크게 진행됐다.

다만 다음 항목은 운영 전 반드시 수정해야 한다.

| 우선순위 | 핵심 문제 | 판정 |
|---|---|---|
| **P0** | 인증 없는 API 로그 조회 + 로그인 비밀번호/토큰 요청 본문 평문 저장 | 즉시 차단 필요 |
| **P0** | 고정 관리자 계정 9개 및 개발용 JWT/서명 키가 운영에서도 허용될 수 있음 | 운영 배포 차단 조건 필요 |
| **P1** | Camera 등 subtype 전용 컬럼 변경 시 `SYNC_DEVICE` NATS 메시지 미발행 | 실측 재현 |
| **P1** | 중앙 RBAC 매핑이 실제 mutation endpoint를 완전히 덮지 못함 | 권한 우회 가능성 감사 필요 |
| **P1** | `db-monitor` PostgreSQL 재연결·healthcheck·메시지 재처리 없음 | 장애 후 조용한 동기화 중단 가능 |
| **P1** | DB 마이그레이션이 `create_all + 수동 SQL + 일부 startup SQL`로 혼재 | 배포 이력별 스키마 편차 발생 |
| **P1** | `api_logs` 파티션이 2026-10까지만 존재 | 2026-11부터 INSERT 실패 가능 |
| **P1** | 테스트 2,518건이 로컬에 있으나 `tests/`가 Git ignore됨 | clone/CI 재현 불가 |

종합 판정은 **기능 구현도는 높지만 보안·배포 재현성·메시징 복원력은 보강이 필요한 상태**다.

---

## 2. 검토 방법과 실측 범위

다음 항목을 정적 분석과 실행 검증으로 교차 확인했다.

1. README와 CHANGELOG의 최근 기능 목록 확인
2. FastAPI `app.openapi()`로 실제 Swagger operation 추출
3. 40개 router 모듈과 서비스·모델·스키마 구조 확인
4. PostgreSQL 43개 ORM 테이블과 설치된 trigger 확인
5. Docker Compose 6개 서비스 및 외부 NATS 네트워크 확인
6. 실제 PostgreSQL 변경 후 NATS 메시지 구독
7. RBAC 중앙 매핑과 실제 OpenAPI endpoint 자동 비교
8. API 로그 인증 여부 및 민감 요청 본문 저장 상태 실측
9. pytest collection 및 주요 선택 테스트 확인

실행 당시 다음 컨테이너가 모두 실행 중이었다.

| 컨테이너 | 역할 | 상태 |
|---|---|---|
| `pids-api-server` | FastAPI API 서버 | healthy |
| `pids-api-postgres` | PostgreSQL 16 | healthy |
| `pids-api-db-monitor` | PostgreSQL `LISTEN` → NATS PUB | running |
| `pids-api-gis-ingest` | NATS tracking → PostgreSQL | running |
| `pids-api-autoheal` | unhealthy 컨테이너 재기동 | healthy |
| `pids-api-db-admin` | Adminer | running |

NATS는 Compose 내부 서비스가 아니라 외부 `nats-core_nats-network`의 `nats-server-01:4222`에 연결한다.

---

## 3. 시스템 아키텍처

```text
Central UI / GIS / NVR / 장비 관리 클라이언트
                     │
                     │ HTTPS + Bearer JWT
                     ▼
┌──────────────────────────────────────────────────────────┐
│ FastAPI API Server                                       │
│ Router → RBAC → Service → AsyncSession                   │
│ Request-ID / API Log Queue / Scheduler / Report Worker   │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
                 PostgreSQL 16
                    │          ▲
       pg_notify    │          │ track_points INSERT
                    ▼          │
              db-monitor   gis-ingest
                    │          ▲
               NATS PUB    NATS SUB
                    ▼          │
                 NATS Cluster
```

주요 코드:

- FastAPI 진입점: [`app/main.py`](../../app/main.py)
- DB 연결: [`app/database.py`](../../app/database.py)
- Docker 구성: [`docker-compose.yml`](../../docker-compose.yml)
- SYNC trigger: [`app/db_triggers.py`](../../app/db_triggers.py)
- NATS 발행 워커: [`db_monitor/main.py`](../../db_monitor/main.py)
- GIS 인제스트: [`gis_ingest/main.py`](../../gis_ingest/main.py)

---

## 4. 기술 스택과 규모

| 계층 | 구현 |
|---|---|
| Runtime | Python 3.11 |
| API | FastAPI, Pydantic v2 |
| ORM | SQLAlchemy 2.x, AsyncSession 중심 |
| DB Driver | asyncpg + psycopg2 dual-stack |
| DB | PostgreSQL 16 |
| 인증 | JWT HS256, access/refresh, token blacklist |
| 인가 | ADMIN bypass + USER permission matrix + 기간성 Grant |
| 메시징 | NATS Core |
| PDF | Playwright Chromium + PyMuPDF |
| 이미지 | Pillow |
| 배포 | Docker Compose, mkcert, PowerShell bootstrap |
| 테스트 | pytest, pytest-asyncio |

현재 OpenAPI 규모:

| 항목 | 수량 |
|---|---:|
| Path | 128 |
| Operation | 241 |
| GET | 105 |
| POST | 45 |
| PUT | 28 |
| PATCH | 25 |
| DELETE | 38 |
| OpenAPI schema | 276 |
| ORM table | 43 |
| Router 모듈 | 40 |

README의 “41개 router” 표기와 실제 router 파일 수 40개는 산정 기준을 통일할 필요가 있다. flat router를 별도 router로 셌다면 README에 기준을 명시해야 한다.

---

## 5. 전체 기능 목록

### 5.1 인증·계정·세션

- 로그인, 로그아웃, access/refresh token 발급
- refresh rotation 및 token blacklist
- 현재 사용자 정보와 유효 권한 조회
- 사용자 CRUD, 잠금·잠금해제·비밀번호 초기화
- 본인 정보·비밀번호·프로필 사진 수정
- 기본 프로필 이미지 자동 생성 및 fallback
- 사용자 그룹 CRUD 및 permissions 관리
- 사용자별 기간성 UserGroupGrant 부여·회수·만료
- 세션 목록, 자기 세션 종료, 관리자 강제 로그아웃
- 마지막 ADMIN 세션 보호
- NATS 기반 per-session revoke 및 사용자 권한 변경 통지

대표 경로:

- `/api/auth/*`
- `/api/users/*`
- `/api/user-groups/*`
- `/api/user-sessions/*`
- `/api/grants`, `/api/users/{id}/grants`
- `/api/settings/session`

### 5.2 RBAC

현재 권한 모델은 다음과 같다.

```text
ADMIN role → 전체 bypass
USER role  → 기본 group permissions ∪ 활성 기간성 grant permissions
```

- module × verb 기반 매트릭스
- `view`, `edit`, `delete`, `control`
- request 시점에 Grant 유효기간 확인
- scheduler가 만료 Grant 정리
- 비-ADMIN의 자기 role/group 상승 및 ADMIN 계정 탈취 방지 가드

관련 코드:

- [`app/security/permission_map.py`](../../app/security/permission_map.py)
- [`app/security/matrix_enforcer.py`](../../app/security/matrix_enforcer.py)
- [`app/routers/auth.py`](../../app/routers/auth.py)

### 5.3 장치 관리

- Controller CRUD
- Sensor CRUD 및 Controller 종속 관계
- Camera CRUD
- Speaker CRUD
- Lamp CRUD
- Enclosure CRUD 및 환경 제어
- 공통 Device joined-table inheritance
- HardwareSpec, Geolocation, JSONB URL 등 확장 필드
- 활성 여부 및 상태 관리
- DeviceGroup N:N 할당·단건/벌크 해제

대표 경로:

- `/api/devices/controllers`
- `/api/devices/sensors`
- `/api/devices/cameras`
- `/api/devices/speakers`
- `/api/devices/lamps`
- `/api/devices/enclosures`
- `/api/devices/groups`

### 5.4 카메라 부속 기능

- CameraSetting 조회·부분수정·전체교체
- CameraPreset CRUD
- ROI CRUD
- XY Point 조회·생성·일괄교체·삭제
- 제한구역/감시금지구역 표현
- Thumbnail 업로드·조회·파일 반환·삭제

### 5.5 이벤트

- DetectionEvent CRUD
- MalfunctionEvent CRUD
- ConnectionEvent CRUD
- ActionEvent CRUD
- Detection/Malfunction 1:N Action 관계
- Detection Log 읽기 모델
- 이벤트 통계 summary/trend/by-device/dashboard
- 장치 삭제 후에도 과거 이벤트 설명을 유지하는 snapshot 구조

### 5.6 이벤트 매핑과 장치 동작 구성

- DeviceGroup과 EventMapping 연결
- EventMapping Camera/Speaker/Lamp 하위 설정
- 단건 CRUD 및 1~100건 bulk 등록·해제
- mapping별 preset, file group, lamp 동작 구성
- 독립 flat list API
- statement-level trigger로 bulk NATS 메시지 중복 억제

### 5.7 서버 모니터링

- ServerCategory CRUD
- Server CRUD
- 서버 상태 summary
- ServerMetrics 기록·최신값·기간 조회·삭제
- SystemEvent CRUD·확인 처리·요약
- 서버별 SystemEvent 조회
- ProxySetting 조회·부분수정·전체교체

### 5.8 보고서

- Report component 목록
- ReportTemplate CRUD
- 보고서 생성 요청 및 생성 이력
- HTML preview와 PDF 다운로드
- 생성 진행률과 진행 단계
- 진행 정체 stall watchdog
- 사용자 취소와 생성 결과 삭제
- 상세 데이터 CSV 다운로드
- custom 시작일/종료일 및 최대 366일 범위
- PDF named volume 영속화
- 재시작 시 고아 PENDING/GENERATING 작업을 FAILED로 확정

현재 보고서 생성은 별도 durable job queue가 아니라 API 프로세스 내부 background task다. 재시작 시 상태는 정리되지만 작업 자체는 이어서 실행되지 않는다.

### 5.9 로그·감사·설정 이력

- Request ID 자동 생성·전파
- API 요청 로그 queue 적재 후 100건/500ms batch INSERT
- AuditLog 조회
- ConfigChangeLog 조회
- 사용자·세션·그룹 변경 감사 기록
- 장치·서버·이벤트 매핑 설정 변경 기록
- append-only DB trigger 지원
- 30일 초과 API 로그 sweep

### 5.10 NATS 메시징

#### PostgreSQL → NATS

PostgreSQL master data 변경을 `pg_notify('gop_sync')`로 발생시키고 `db-monitor`가 NATS로 변환한다.

| Command | Subject suffix |
|---|---|
| `SYNC_DEVICE` | `all.sync.device` |
| `SYNC_SERVER` | `all.sync.server` |
| `SYNC_CATEGORY` | `all.sync.category` |
| `SYNC_DEVICE_GROUP` | `all.sync.device-group` |
| `SYNC_EVENT_MAPPING` | `all.sync.event-mapping` |
| `SYNC_PRESET` | `all.sync.preset` |
| `SYNC_FILE_GROUP` | `all.sync.file-group` |
| `SYNC_CAMERA_SETTING` | `all.sync.camera-setting` |
| `SYNC_PROXY_SETTING` | `all.sync.proxy-setting` |

최종 subject 예:

```text
sensorway.unit001.all.sync.device
```

#### NATS → PostgreSQL

- `sensorway.*.gis.tracking-status` 구독
- `tracking=active`인 targets만 `track_points`에 저장
- `(track_id, observed_at)` unique 및 `ON CONFLICT DO NOTHING`
- UTC timestamp를 naive KST 컨벤션으로 변환
- legacy 단일 target payload 방어 정규화

#### 계정 NATS

- 세션별 revoke 메시지
- 사용자별 permissions.changed 메시지
- HMAC-SHA256 서명
- 기본 `NATS_REVOKE_ENABLED=false`

### 5.11 추적 이력

- 기간별 tracking point 조회
- keyset cursor pagination
- tracking session 타임라인 집계
- tracking 저장소 health 확인

### 5.12 배포·운영

- HTTPS 우선, 인증서 없으면 fail-fast
- 명시적 `ALLOW_HTTP_FALLBACK=true`만 HTTP 허용
- Windows `bootstrap.ps1` 1-Click 배포
- PS2EXE 인증서 설치기
- Docker healthcheck와 autoheal
- 로그 파일 회전 10MB × 3
- PostgreSQL/Adminer 운영 구성
- 보고서 PDF named volume

---

## 6. 최근 변경사항 정리

### 6.1 v6.0 async 전환 — 2026-07-03

- 주요 router를 `AsyncSession`으로 전환
- `select()`/`await db.execute()` 기반 ORM 사용
- ReportService async 전환
- API 로그를 요청당 INSERT에서 queue batch INSERT로 변경
- 월별 `api_logs` 파티셔닝 도입
- autoheal 도입
- startup DB 초기화 async 경로 추가

### 6.2 보고서 안정화 — 2026-07-04~05

- PDF 파일 named volume 영속화
- 재시작 중 작업 고아 상태 정리
- 진행률, 단계, stall watchdog
- 상세 CSV 다운로드
- SQL 집계 최적화
- custom 날짜 범위
- 파일 소실 시 `PDF_FILE_MISSING`/410 구분

### 6.3 인증·계정·세션 — 2026-07-05~07

- `AUTH_MODE=token` 기본값 전환
- ADMIN 관리자 계정 확대
- Role을 ADMIN/USER 2종으로 정규화
- strict response Enum으로 인한 500 완화
- force logout timezone 오류 수정
- 세션 설정을 login/refresh에 실제 연결
- refresh blacklist TTL을 런타임 설정과 정합
- `session_enabled=false`를 10년 JWT로 구현
- 계정/그룹/세션 endpoint를 permission matrix로 확대
- 권한상승 방지 가드 추가

### 6.4 배포 안정화 — 2026-07-06~07

- 컨테이너 이름 `pids-api-*`로 통일
- 인증서 누락 시 HTTPS fail-fast
- PS2EXE에서 비어 있던 경로 탐색 수정
- clone 후 1-Click bootstrap
- 신규 PC 스키마 누락을 일부 startup migration으로 보정
- 서버 port/사용자 role/응답 Enum 때문에 발생하던 목록 500 완화
- 기본 프로필 이미지 자동 생성

관련 변경 이력은 [`CHANGELOG.md`](../../CHANGELOG.md)에 상세히 기록되어 있다.

---

## 7. 실측 검증 결과

### 7.1 OpenAPI

- OpenAPI 생성 성공
- version `6.0.0`
- 128 path / 241 operation
- operationId 중복으로 OpenAPI 생성이 실패하는 문제는 없었음
- 218개 operation은 OpenAPI상 security 표시가 있고 23개는 표시가 없음
- 168개 operation에 동일 tag가 중복 등록됨

### 7.2 PostgreSQL/NATS

실DB에서 다음을 검증했다.

| 검증 | 결과 |
|---|---|
| DeviceGroup INSERT | `CREATED` 수신 |
| DeviceGroup UPDATE | `UPDATED` 수신 |
| DeviceGroup DELETE | `DELETED` 수신 |
| Device base UPDATE | `SYNC_DEVICE` 수신 |
| 17개 DeviceGroupMapping 일괄 UPDATE | `SYNC_DEVICE_GROUP` 1건 수신 |
| 9개 SYNC command → subject 변환 | 전부 일치 |
| Camera subtype `mode` 직접 UPDATE | 메시지 0건 — 결함 |
| SQLAlchemy Camera subtype `mode` 변경 | 메시지 0건 — 결함 |

### 7.3 API 로그 보안

무인증 요청 실측:

```text
GET /api/logs?limit=1 → HTTP 200
GET /api/logs/viewer  → HTTP 200
```

DB 집계:

```text
auth/login 로그: 476건
body에 password 키 포함: 474건
body가 저장된 전체 API 로그: 1,227건
```

실제 비밀번호 값은 조회하거나 문서에 기록하지 않았다.

### 7.4 테스트

- pytest collection: **2,518 tests**
- 파일시스템의 test 관련 파일: 539개
- Git 추적 test 파일: **0개**
- DB trigger 선택 테스트: 14 passed, 2 skipped
- Swagger/tag 선택 테스트: 25 passed, 2 skipped
- 전체 회귀 실행은 async fixture가 실제 PostgreSQL에 연결하고 sync override만 적용하는 구조 때문에 안전하고 재현 가능한 상태가 아님

---

## 8. 문제 및 수정 필요사항

## 8.1 P0 — 즉시 수정

### SEC-01. API 로그가 무인증 공개되고 민감 요청 본문이 평문 저장됨

**현상**

- [`app/middleware/logging.py`](../../app/middleware/logging.py)가 POST/PUT/PATCH body를 그대로 저장한다.
- `/api/auth/login`, `/api/auth/refresh`, 비밀번호 변경·초기화 요청도 제외되지 않는다.
- [`app/routers/logs.py`](../../app/routers/logs.py)는 인증/권한 dependency가 없다.
- 중앙 permission map에도 `/api/logs`가 없다.

**영향**

- 로그인 비밀번호 노출
- refresh token 및 변경 비밀번호 노출 가능
- 장비 접속 계정·비밀번호 노출 가능
- 공격자가 별도 인증 없이 로그 API로 조회 가능

**수정안**

1. `/api/logs`와 `/api/logs/viewer`를 ADMIN 또는 `audit_logs:view` 이상의 권한으로 즉시 차단
2. 로그인·refresh·비밀번호·token 관련 endpoint는 body 저장 금지
3. 공통 recursive redaction 적용

```text
password, current_password, new_password, user_password,
access_token, refresh_token, token, secret, authorization
```

4. 기존 `api_logs.body`의 민감 데이터 삭제 또는 마스킹 migration 수행
5. 로그 viewer에서 body 표시 자체를 기본 비활성화

### SEC-02. 고정 ADMIN 계정과 개발 키가 운영에서 활성화될 수 있음
=====> 이건 일단 보류해줘

**현상**

- 관리자 계정 9개가 고정 비밀번호로 자동 seed된다.
- `admin123`, `sensorway1`이 README에 공개되어 있다.
- JWT와 revoke signing key는 dev 기본값을 가진다.
- `ENVIRONMENT=prod`를 명확히 설정하지 않으면 기본 키 거부 validator가 작동하지 않는다.

**영향**

- 신규 설치 직후 전체 관리자 권한 탈취 가능
- 기본 JWT 키가 사용되면 임의 토큰 위조 가능

**수정안**

1. `prod/staging`에서 고정 계정 seed 금지
2. 최초 부팅 시 일회성 관리자 비밀번호를 랜덤 생성하거나 외부 secret으로 주입
3. `ENVIRONMENT`를 Compose 필수 환경변수로 지정
4. prod에서 JWT/revoke key, DB password, CORS whitelist 미설정 시 fail-fast
5. 현재 운영 계정의 고정 비밀번호 즉시 교체

---

## 8.2 P1 — 다음 배포 전 수정

### MSG-01. Device subtype 전용 변경은 NATS SYNC가 발생하지 않음

**현상**

현재 trigger는 `devices` 부모 테이블에만 설치되고 다음 subtype trigger는 제거된다.

- controllers
- sensors
- cameras
- speakers
- enclosures
- lamps

Camera `mode`를 직접 SQL과 SQLAlchemy ORM 양쪽에서 변경했지만 NATS 메시지가 0건이었다.

**영향**

- Camera mode/category/urls
- Sensor controller 연결
- Speaker/Enclosure/Lamp subtype 설정

등을 변경해도 하위 시스템 캐시가 갱신되지 않을 수 있다.

**수정안**

- 부모 `devices` trigger는 공통 컬럼과 lifecycle용으로 유지
- 6개 subtype 테이블에 최소 `AFTER UPDATE` trigger 추가
- subtype table 이름으로 `type_device`를 결정
- 같은 트랜잭션에서 부모·자식이 함께 UPDATE될 때 중복 메시지를 억제하는 테스트 추가
- 직접 SQL과 API PATCH 양쪽 E2E 테스트 추가

### MSG-02. db-monitor가 PostgreSQL 재연결을 수행하지 않음

**현상**

- PostgreSQL 연결 후 `while True: sleep()`만 수행
- DB 연결 종료 감지와 재연결 루프 없음
- db-monitor healthcheck 없음
- Docker autoheal 대상이 될 health 상태가 없음
- PRD에는 DB 재연결과 publish retry가 기재되어 있으나 코드에는 없음

**영향**

PostgreSQL 재시작 후 컨테이너는 `Up`이지만 `LISTEN gop_sync`가 사라진 상태로 남을 수 있다.

**수정안**

- PostgreSQL/NATS 연결을 supervision loop로 감싸기
- exponential backoff + jitter
- LISTEN 재등록 확인
- 마지막 수신 시각, NATS 연결 상태, DB 연결 상태를 healthcheck로 노출
- db-monitor Docker healthcheck 추가

### MSG-03. Core NATS/pg_notify 구조는 장애 중 메시지를 보존하지 않음

**현상**

- PostgreSQL NOTIFY는 consumer가 없으면 보존되지 않는다.
- NATS Core도 durable replay를 제공하지 않는다.
- outbox와 JetStream이 없다.

**판단**

메시지가 단순 cache invalidation이고 클라이언트가 주기적으로 full refresh한다면 허용 가능하다. 반드시 한 번은 처리해야 하는 업무 이벤트라면 현재 구조는 부적합하다.

**수정안**

- 신뢰성 요구사항을 명시
- cache invalidation이라면 주기적 full sync와 sequence/version 제공
- 보장 전달이 필요하면 transactional outbox + JetStream durable consumer 도입

### AUTH-01. 중앙 RBAC permission map이 실제 API를 완전하게 덮지 못함
(개발자의견 : 참고로 GIS에 Map 에디팅 기능에 관한 권한도 있는데 그건 API쪽에 연관된 endpoint 가 없다 하지만 GIS에서 필요하니까 권한맵도 존재해야됨)
자동 비교 결과:

- permission map 등록: 97개
- 실제 OpenAPI와 일치: 92개
- 존재하지 않는 stale map: 5개 
- 전체 mutation 133개 중 중앙 map 미등록: 46개

미등록 46개 중 일부는 라우터 자체 strict dependency로 보호되지만, 중앙 집행을 “단일 choke point”라고 부를 수 없는 상태다. 특히 EventMapping 하위 detail/bulk, ROI/XYPoint, DeviceGroup mapping 등을 전수 확인해야 한다.

대표 stale map:

- 존재하지 않는 `POST /api/devices/cameras/{id}/settings`
- 잘못된 `/api/enclosure-metrics` 경로
- 실제 POST인 acknowledge를 PATCH로 등록
- 존재하지 않는 ReportTemplate PUT

**수정안**

1. OpenAPI route를 기준으로 mutation endpoint와 permission map을 CI에서 자동 비교
2. 미등록 mutation은 테스트 실패 처리하는 default-deny 정책 검토
3. 라우터 dependency와 중앙 map 중 하나를 권위로 정하고 중복 제거
4. module/verb가 없는 endpoint를 승인 목록으로 명시

### DB-01. DB migration 체계가 혼재됨

현재 방식:

- 신규 테이블: `Base.metadata.create_all()`
- 다수 변경: 수동 SQL
- startup 자동 적용: v61, v62 두 파일만 whitelist
- trigger: 애플리케이션 시작 시 별도 재생성

**문제**

- `create_all()`은 기존 테이블에 컬럼을 추가하지 않는다.
- clone/기존 volume/신규 volume의 결과가 달라질 수 있다.
- audit immutability, partition, invariant trigger 적용 여부가 설치 이력에 의존한다.
- migration version table이 없어 적용 상태를 추적하기 어렵다.

**수정안**

- Alembic 등 단일 migration 체계 도입
- schema version table 관리
- 모든 신규 설치는 migration `base → head`로 생성
- startup에서 실패를 무시하지 말고 필수 migration 실패 시 fail-fast
- 수동 migration 목록과 적용 체크 명령 제공

### DB-02. api_logs 파티션이 2026-10까지만 존재함

실DB 파티션:

- `api_logs_before_partition`
- `api_logs_2026_07`
- `api_logs_2026_08`
- `api_logs_2026_09`
- `api_logs_2026_10`

미래 default partition이나 자동 생성 scheduler가 없다. 따라서 2026-11-01 이후 로그 INSERT가 실패할 수 있다.

**수정안**

- 매월 다음 3~6개월 파티션을 사전 생성하는 scheduler
- 또는 pg_partman 사용
- 미래 범위 default partition 마련
- healthcheck에서 “다음 달 파티션 존재 여부” 검사
- 오래된 파티션은 row DELETE가 아닌 DROP/DETACH 정책 사용

### TEST-01. 테스트와 CI를 clone 환경에서 재현할 수 없음

**현상**

- 로컬: 2,518 tests 수집
- `git ls-files tests`: 0개
- `.gitignore`가 `tests/` 전체를 제외
- async fixture가 실제 PostgreSQL `AsyncSessionLocal`을 사용
- 기존 `client` fixture는 sync `get_db`만 override하여 async router에는 적용되지 않음
- `requirements.txt`에 SQLite async fallback용 `aiosqlite`가 없음

**영향**

- 다른 PC와 CI에는 테스트가 전달되지 않음
- README의 PASS 수치를 재현할 수 없음
- 테스트가 실운영 DB를 건드릴 위험

**수정안**

1. `tests/`를 Git 추적 대상으로 복원
2. test dependencies 분리 (`requirements-test.txt` 또는 dependency group)
3. `get_async_db` override fixture 구현
4. PostgreSQL integration test는 별도 test DB/container 사용
5. 운영 DB URL 감지 시 pytest 즉시 중단
6. CI에서 unit/integration/OpenAPI-contract 단계를 분리

### SEC-03. Docker build context에 .env와 인증서가 포함될 수 있음

Dockerfile은 `COPY . .`을 사용하지만 `.dockerignore`에는 `.env`, `certs/*.key`, `certs/*.pem` 제외 규칙이 없다.

**영향**

- 환경변수와 private key가 이미지 layer에 남을 수 있음
- 컨테이너 bind mount로 파일을 덮어도 image history에서는 제거되지 않음

**수정안**

`.dockerignore`에 최소 다음을 추가한다.

```gitignore
.env
.env.*
certs/*.key
certs/*.crt
certs/*.pem
certs/rootCA*
tests/
data/
logs/
```

### SEC-04. 일반 예외 메시지에 내부 예외 문자열 노출

전역 500 handler가 다음처럼 응답한다.

```python
"message": f"Internal server error: {str(exc)}"
```

SQL, 파일 경로, 내부 구조, DB driver 메시지가 클라이언트로 노출될 수 있다.

**수정안**

- 클라이언트에는 고정 메시지와 request_id만 반환
- 전체 stack trace는 서버 로그에만 기록
- 환경별 DEBUG 응답 분리

### SEC-05. `session_enabled=false`가 10년 JWT를 발급함
=====> 이건 일단 보류해줘 ( 세션의 타임아웃 기능을 끌 수 있어야 되는 경우도 있어서 그래)

세션 비활성화를 “사실상 무기한”으로 구현하면서 access/refresh token을 10년으로 발급한다.

**위험**

- token 탈취 시 매우 긴 공격 창
- blacklist DB와 강제 로그아웃 기능에 장기 의존
- signing key rotation 시 대규모 세션 단절

**수정안**

- access token은 짧게 유지하고 refresh/session 정책만 장기화
- device-bound refresh rotation 적용
- UI에 보안 경고와 운영 정책 명시
- prod에서 session_enabled=false 금지 또는 별도 승인

---

## 8.3 P2 — 계획적으로 개선

### DOC-01. 문서·Swagger 버전 및 endpoint 목록 불일치

- 연동설계서 본문 version: v5.4
- Swagger version: 6.0.0
- Swagger description 일부는 명세 v5.0이라고 표시
- 연동설계서 부록: 226 operation
- 실제 `/api` operation: 239

부록에 빠진 주요 기능:

- 권한 조회와 Grant
- API Logs
- Report 취소·삭제·CSV·실제 preview 경로
- Session settings

**수정안**

- OpenAPI를 endpoint 인벤토리의 단일 권위로 사용
- Markdown endpoint 부록 자동 생성
- 문서 version을 Swagger와 함께 release pipeline에서 갱신

### DOC-02. README에서 clone 후 존재하지 않을 수 있는 문서를 링크함

`docs/Manual.md`, schema 문서, tests 등 일부 파일은 로컬에 있지만 ignore 상태라 clone/배포본에 없을 수 있다.

**수정안**

- README 링크 대상은 모두 Git 추적 확인
- `git ls-files` 기반 broken documentation link 검사 추가

### API-01. Swagger tag 중복

168개 operation에 동일 tag가 두 번 들어간다. router 선언과 `include_router(tags=...)`에서 동시에 지정하기 때문이다.

**수정안**

- tag는 router 또는 include_router 한쪽에서만 지정
- OpenAPI snapshot test에서 duplicate tag 검사

### API-02. Response schema를 광범위하게 `str`로 완화

최근 strict Enum으로 인한 500을 피하기 위해 여러 response field를 `str`로 바꿨다. 런타임 안정성은 좋아졌지만 Swagger가 허용값을 설명하지 못한다.

**수정안**

- 입력은 strict Enum 유지
- 출력은 tolerant serializer + 문서용 examples/description 제공
- 장기적으로 DB String 값을 정규화한 뒤 native Enum 또는 check constraint 검토

### OPS-01. 보고서 생성이 API 프로세스 내부 작업임

PDF 생성 작업은 API 프로세스 재시작 시 이어서 실행되지 않는다. 현재는 startup에서 고아 작업을 FAILED로 바꾸므로 상태 무결성은 있으나 작업 내구성은 없다.

**수정안**

- 작업량이 커지면 Celery/RQ/Arq 또는 DB-backed worker queue 분리
- generation id 기반 idempotent 재시도
- API와 PDF worker의 CPU/메모리 격리

### OPS-02. 관측성 부족

현재 로그는 있으나 다음 핵심 지표가 체계적으로 노출되지 않는다.

- DB pool 사용률/대기시간
- API log queue size/drop count
- db-monitor 마지막 NOTIFY 수신 시각
- NATS publish 성공/실패/재연결 횟수
- GIS ingest skip/error count
- report queue/진행 정체 건수
- 다음 달 파티션 존재 여부

Prometheus metric 또는 최소 운영 health endpoint로 노출하는 것이 좋다.

### OPS-03. CORS 기본값 `*`

개발 편의값이 운영에 남을 수 있다. prod에서는 허용 Origin을 명시하고 startup validator로 강제해야 한다.

---

## 9. 수정 우선순위 제안

### 9.1 즉시 — 24시간 내

1. `/api/logs`, `/api/logs/viewer` 인증·인가 적용
2. 요청 로그 secret redaction 및 기존 민감 body 정리
3. 운영 JWT/revoke key와 관리자 비밀번호 교체
4. `.dockerignore`에 `.env`·private key 제외
5. 2026-11 이후 `api_logs` 파티션 사전 생성

### 9.2 단기 — 다음 배포

1. Device subtype UPDATE trigger 추가
2. db-monitor 재연결 supervisor와 healthcheck
3. RBAC map/OpenAPI 자동 정합 테스트
4. 500 응답 내부 예외 제거
5. tests Git 복원 및 async fixture 격리
6. 문서 v6.0 endpoint 목록 자동 동기화

### 9.3 중기 — 2~4주

1. Alembic 기반 migration 단일화
2. NATS 전달 보장 수준 결정 및 outbox/JetStream 검토
3. API/worker/report 관측성 구축
4. 보고서 worker 분리
5. CI pipeline 구축

---

## 10. 권장 회귀 검증 시나리오

| 영역 | 필수 시나리오 |
|---|---|
| 로그 보안 | 무인증 `/api/logs` 401, USER 403, ADMIN/권한그룹만 200 |
| 로그 redaction | login/refresh/password/user_password/token 값이 저장되지 않음 |
| NATS Device | 부모 공통 필드와 6개 subtype 전용 필드 각각 UPDATE 시 1건 발행 |
| NATS bulk | N개 mapping 변경 시 부모 ID별 1건 발행 |
| NATS recovery | PostgreSQL/NATS 재시작 후 자동 재연결 및 후속 메시지 수신 |
| RBAC | 모든 mutation endpoint가 permission 또는 명시적 승인 목록에 존재 |
| Migration | 빈 DB와 이전 version DB가 모두 `head` schema로 수렴 |
| Partition | 현재 월+6개월 파티션 존재, 월 경계 INSERT 성공 |
| Session | runtime timeout/refresh/lockout, force logout, 10년 정책 보안 검토 |
| Reports | 생성·진행률·취소·재시작·파일 소실·CSV·custom range |
| Clone deploy | 빈 PC clone → bootstrap → HTTPS → login → Swagger smoke |

---

## 11. 최종 평가

| 영역 | 평가 | 설명 |
|---|---|---|
| 기능 범위 | 좋음 | 장치·이벤트·계정·보고서·NATS·추적까지 폭넓음 |
| API 계약 | 보통 이상 | Swagger는 크고 상세하지만 Markdown 문서가 뒤처짐 |
| 비동기 구조 | 좋음 | v6.0에서 async 전환과 queue batch가 진행됨 |
| 데이터 모델 | 좋음 | Device/Event polymorphism과 snapshot 정책이 명확함 |
| 보안 | 위험 | 공개 로그와 평문 credential 저장은 즉시 수정 필요 |
| RBAC | 보통 | 모델은 발전했지만 중앙 map 정합 보장이 부족함 |
| 메시징 | 보통 | 정상 경로는 동작하나 subtype 누락과 장애 복구가 약함 |
| DB 배포 | 위험 | migration 혼재와 파티션 기한 문제 |
| 테스트 | 위험 | 테스트가 Git에 없어 재현 불가, async fixture도 불완전 |
| 운영성 | 보통 | health/autoheal은 있으나 메시징·파티션 관측성이 부족함 |

가장 먼저 해결해야 할 것은 **API 로그 보안**, **운영 secret/관리자 계정**, **Device subtype NATS 누락**, **db-monitor 복원력**, **DB migration/파티션**, **테스트 재현성**이다. 이 여섯 항목을 해결하면 현재의 풍부한 기능을 운영 환경에서도 신뢰할 수 있는 형태로 끌어올릴 수 있다.

---

## 12. 참고 문서

- [`README.md`](../../README.md)
- [`CHANGELOG.md`](../../CHANGELOG.md)
- [`GOP_Restful_Api_연동설계.md`](../../GOP_Restful_Api_연동설계.md)
- [`docs/PRD_DB_Change_Monitor.md`](../PRD_DB_Change_Monitor.md)
- [`docs/PRD_PostgreSQL_Migration.md`](../PRD_PostgreSQL_Migration.md)
- [`docs/PRD_v5.0_Permission_Management.md`](../PRD_v5.0_Permission_Management.md)
- [`docs/PRD_Tracking_History_API.md`](../PRD_Tracking_History_API.md)
- [`docs/PRD_Report_System.md`](../PRD_Report_System.md)

