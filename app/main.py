"""
GOP API Server - Main Application

General Outpost(GOP) 통합 관제 시스템을 위한 RESTful API 서버입니다.

주요 기능:
- Device Management: Controller, Sensor, Camera CRUD
- Device Groups: N:N 관계 기반 디바이스 그룹 관리
- Event Management: Detection, Malfunction, Connection, Action 이벤트
- Server Integration: 외부 서버 연동 및 이벤트 매핑

Version: 1.5.0
"""
from fastapi import FastAPI, Request, Response, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Patch FastAPI's datetime encoder to output ISO 8601 with +09:00 (KST)
# Covers plain-dict responses that bypass Pydantic model serialization
from fastapi.encoders import ENCODERS_BY_TYPE as _ENCODERS_BY_TYPE
_KST = timezone(timedelta(hours=9))
_ENCODERS_BY_TYPE[datetime] = lambda v: (v.replace(tzinfo=_KST) if v.tzinfo is None else v).isoformat()

from app.config import settings
from app.database import engine
from app.db_triggers import apply_triggers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import APILoggingMiddleware
from app.routers import auth, logs, controllers, sensors, cameras, speakers, enclosures, lamps, detections, malfunctions, connections, actions, detection_logs, event_mappings, server_categories, servers, server_metrics, proxy_settings, camera_settings, system_events, device_groups, camera_presets, rois, xypoints, event_mapping_cameras, event_mapping_speakers, event_mapping_lamps, file_groups, enclosure_metrics, users, user_groups, grants, user_sessions, audit_logs, config_change_logs, reports, thumbnails, event_statistics, tracking, settings as settings_router
from app.models.report import ReportGeneration
from app.dependencies import get_db
from app.utils.init_db import initialize_database_async, apply_idempotent_migrations
from app.schemas.common import ApiResponse
from app.security.matrix_enforcer import enforce_matrix


# OpenAPI 태그 메타데이터 정의
tags_metadata = [
    {
        "name": "Authentication",
        "description": "사용자 인증 및 토큰 관리 API. PRD: PRD_Account_Design.md Section 6",
    },
    {
        "name": "Users",
        "description": "사용자 계정 관리 API. 사용자 CRUD 및 권한 관리. PRD: PRD_Account_Design.md Section 7",
    },
    {
        "name": "User Groups",
        "description": "사용자 그룹 관리 API. 권한 및 접근 제어 그룹. PRD: PRD_Account_Design.md Section 8",
    },
    {
        "name": "User Sessions",
        "description": "사용자 세션 관리 API. 로그인 세션 조회 및 강제 로그아웃. PRD: PRD_Account_Design.md Section 9",
    },
    {
        "name": "Audit Logs",
        "description": "감사 로그 조회 API. 사용자 활동 감사 로그를 조회합니다. PRD: PRD_Audit_Log.md v1.0",
    },
    {
        "name": "Tracking",
        "description": "추적 이력(Tracking) 조회 API. NATS gis.tracking-status 로 수집된 추적점을 기간/세션으로 조회합니다(read-only). PRD: PRD_Tracking_History_API.md v1.0",
    },
    {
        "name": "Config Change Logs",
        "description": "설정 변경 이력 조회 API. 리소스 설정 변경 이력을 추적합니다. PRD: PRD_ConfigChangeLog.md v1.0",
    },
    {
        "name": "DeviceGroups",
        "description": "디바이스 그룹 관리 API. N:N 관계로 디바이스를 그룹화합니다. PRD Section 2.3 참조.",
    },
    {
        "name": "Controllers",
        "description": "컨트롤러 디바이스 CRUD API. 센서를 관리하는 상위 장치입니다.",
    },
    {
        "name": "Sensors",
        "description": "센서 디바이스 CRUD API. 컨트롤러에 종속된 감지 장치입니다.",
    },
    {
        "name": "Cameras",
        "description": "카메라 디바이스 CRUD API. 영상 감시 장치로 HardwareSpec, Geolocation 확장 필드를 지원합니다. PRD Section 3.2 참조.",
    },
    {
        "name": "Camera Settings",
        "description": "카메라 기능 설정 API. PRD: PRD_Device_Setting.md Section 5.2",
    },
    {
        "name": "Speakers",
        "description": "스피커 디바이스 CRUD API. 방송 단말 장치로 Server 연동을 지원합니다. PRD_Speaker_Device.md 참조.",
    },
    {
        "name": "Enclosures",
        "description": "함체(Enclosure) 디바이스 CRUD API. IoController 디바이스로 환경 모니터링 및 문 상태 관리를 제공합니다.",
    },
    {
        "name": "Enclosure Metrics",
        "description": "함체 환경 모니터링 메트릭 API. 온도, 습도, 전류, 전압, 진동, UPS 상태 등을 기록하고 임계치 초과를 감지합니다. PRD: PRD_Enclosure_Metrics_Separation.md v1.0",
    },
    {
        "name": "Lamps",
        "description": "경광등(Lamp) 디바이스 CRUD API. 경광등/경보기 디바이스로 색상, 부저음, 점등모드를 제어합니다. PRD: PRD_Lamp_Device.md v1.1",
    },
    {
        "name": "FileGroups",
        "description": "방송음원 파일풀 관리 API. 서버별 음원 그룹 및 파일 목록을 관리합니다. PRD_Speaker_Device.md 참조.",
    },
    {
        "name": "Detections",
        "description": "탐지 이벤트 관리 API. 센서에서 발생하는 탐지 이벤트를 기록합니다.",
    },
    {
        "name": "Malfunctions",
        "description": "고장 이벤트 관리 API. 디바이스 고장 및 복구 이벤트를 기록합니다.",
    },
    {
        "name": "Connections",
        "description": "연결 상태 이벤트 관리 API. 디바이스 연결/해제 이벤트를 기록합니다.",
    },
    {
        "name": "Actions",
        "description": "액션 이벤트 관리 API. 시스템 동작 이벤트를 기록합니다.",
    },
    {
        "name": "Integration",
        "description": "외부 시스템 연동을 위한 이벤트 매핑 API.",
    },
    {
        "name": "Event Mapping Cameras",
        "description": "이벤트 매핑 카메라 설정 API. EventMapping에 연동된 카메라 동작을 관리합니다. PRD: PRD_CameraEventMapping_Refactoring.md v2.1",
    },
    {
        "name": "Event Mapping Speakers",
        "description": "이벤트 매핑 스피커 설정 API. EventMapping에 연동된 스피커 방송을 관리합니다. PRD: PRD_EventMappingSpeaker.md v1.0",
    },
    {
        "name": "Event Mapping Lamps",
        "description": "이벤트 매핑 경광등 설정 API. EventMapping에 연동된 경광등 동작을 관리합니다. PRD: PRD_Lamp_Device.md v1.1",
    },
    {
        "name": "Mapping Cameras",
        "description": "이벤트 매핑 카메라 독립 목록 API. 전체 매핑 카메라를 조회합니다.",
    },
    {
        "name": "Mapping Speakers",
        "description": "이벤트 매핑 스피커 독립 목록 API. 전체 매핑 스피커를 조회합니다.",
    },
    {
        "name": "Mapping Lamps",
        "description": "이벤트 매핑 경광등 독립 목록 API. 전체 매핑 경광등을 조회합니다.",
    },
    {
        "name": "Detection Logs",
        "description": "탐지 로그 조회 API. 탐지 이벤트 로그를 조회합니다.",
    },
    {
        "name": "Server Categories",
        "description": "서버 카테고리 관리 API.",
    },
    {
        "name": "Servers",
        "description": "외부 서버 관리 API.",
    },
    {
        "name": "Server Metrics",
        "description": "서버 리소스 메트릭 API. PRD: PRD_System_Event.md Section 2.4",
    },
    {
        "name": "Proxy Settings",
        "description": "PidsProxy 서버 운용 설정 API. PRD: PRD_Device_Setting.md Section 5.1",
    },
    {
        "name": "System Events",
        "description": "시스템 이벤트 관리 API. PRD: PRD_System_Event.md Section 3",
    },
    {
        "name": "CameraPresets",
        "description": "카메라 프리셋 관리 API. 카메라별 PTZ 프리셋 위치를 관리합니다.",
    },
    {
        "name": "ROIs",
        "description": "관심 영역(ROI) 관리 API. 프리셋에 대한 ROI 영역을 정의합니다.",
    },
    {
        "name": "XyPoints",
        "description": "XY 좌표점 관리 API. ROI의 다각형 좌표점을 관리합니다.",
    },
    {
        "name": "Logs",
        "description": "시스템 로그 조회 및 뷰어 API.",
    },
    {
        "name": "Reports",
        "description": "보고서 템플릿 및 생성 이력 관리 API. PRD: PRD_Report_System.md Section 6",
    },
    {
        "name": "Thumbnails",
        "description": "카메라 썸네일 이미지 업로드/조회/삭제 API. PRD: PRD_Thumbnail_Image.md v1.0",
    },
    {
        "name": "Event Statistics",
        "description": "이벤트 통계 집계 API. 대시보드 차트용 경량 응답. PRD: PRD_EventStatistics_Api.md v2.1",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    v6.0 후속 Phase 2: `initialize_database_async()` 로 재배선.
    - admin / preset groups 는 AsyncSessionLocal 경로 (진짜 async)
    - downstream 시드(init_server/report/sample) 는 함수 내부에서 sync SessionLocal 로 실행
    - apply_triggers 는 sync SQL 실행이라 `asyncio.to_thread` 그대로 유지
    """
    import asyncio as _asyncio

    # Startup
    print("=" * 60)
    print("GOP API Server Starting...")
    print("=" * 60)

    # Initialize database (async — v6.0 후속 Phase 2)
    # AsyncSessionLocal 기반 admin/preset + sync 하위 시드 위임을 함수 내부에서 처리.
    await initialize_database_async()

    # Apply PostgreSQL pg_notify triggers (skips if SQLite) — sync SQL 실행이라 to_thread 유지
    await _asyncio.to_thread(apply_triggers, engine)

    # v6.0-clone_deploy_bugfix (#5·#6): startup 스키마 보정 마이그레이션 (idempotent, 화이트리스트).
    # create_all() 은 기존 테이블에 새 컬럼을 추가하지 않으므로, git pull 만 한 기존 DB 에서
    # progress_pct 등 누락 → 500. 여기서 IF NOT EXISTS 마이그레이션을 실행해 스키마를 보정한다.
    await _asyncio.to_thread(apply_idempotent_migrations, engine)

    # v6.0-report_lifecycle FR-RGL-01+04: Startup 재조정
    # FastAPI BackgroundTasks는 인프로세스·비영속이라 컨테이너 recreate/재시작 시 in-flight 태스크가 소멸된다.
    # 부팅 시점에 남아있는 PENDING/GENERATING은 반드시 고아 → FAILED로 확정 (CANCELLED는 사용자 취소로 유지).
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as _adb:
            _result = await _adb.execute(text(
                "UPDATE report_generations "
                "SET status = 'FAILED', "
                "    error_message = COALESCE(error_message, 'server restarted during generation'), "
                "    completed_at = COALESCE(completed_at, NOW()) "
                "WHERE status IN ('PENDING', 'GENERATING') "
                "RETURNING id"
            ))
            _rows = _result.all()
            await _adb.commit()
            if _rows:
                print(f"[OK] Report generation reconciled: {len(_rows)} stale → FAILED (ids: {[r[0] for r in _rows]})")
            else:
                print("[OK] Report generation reconciled: no stale generations")
    except Exception as _e:
        print(f"[WARN] Report generation reconciliation failed: {_e}")

    print(f"Server running on http://{settings.HOST}:{settings.PORT}")
    print(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    # v6.0-auth_mode_secure_default (2026-07-05): AUTH_MODE 상태를 부팅 로그에 명확히 노출.
    # public 모드는 RBAC 무집행이라 실수 배포 즉시 감지되도록 큰 경고 표시.
    if settings.AUTH_MODE == "public":
        print("!" * 60)
        print(f"[WARN] Authentication Mode: PUBLIC — RBAC dormant, Bearer 없이 API 접근 가능")
        print(f"[WARN] 프로덕션 배포 시 .env 또는 환경변수에 AUTH_MODE=token 명시 필요")
        print("!" * 60)
    else:
        print(f"Authentication Mode: {settings.AUTH_MODE} (RBAC enforced)")
    print("=" * 60)

    # 경량 sweep 스케줄러 (FR-04, PRD_Permission_Group_Scheduling) — 만료 grant is_active=false.
    # ★ 보안 비의존(요청시점 계산이 권위). APScheduler 미설치/시작실패가 앱 기동을 막지 않도록 방어적.
    # v5.4 P1-A: session sweep 추가 (만료된 활성 user_sessions 정리).
    scheduler = None
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from app.services.grant_service import run_grant_sweep
        from app.services.session_sweep_service import run_session_sweep
        from app.services.api_logs_sweep_service import run_api_logs_sweep

        scheduler = AsyncIOScheduler(timezone=settings.tz)
        scheduler.add_job(run_grant_sweep, "interval", minutes=10, id="grant_sweep",
                          coalesce=True, max_instances=1)
        scheduler.add_job(run_session_sweep, "interval", minutes=5, id="session_sweep",
                          coalesce=True, max_instances=1)
        # v5.4 후속 (문서 A-7 #6): api_logs 무제한 성장 방지 — 일 1회(정오) 30일 이상 삭제
        scheduler.add_job(run_api_logs_sweep, "cron", hour=12, minute=0, id="api_logs_sweep",
                          coalesce=True, max_instances=1)
        scheduler.start()
        print("Grant sweep scheduler started (interval 10m)")
        print("Session sweep scheduler started (interval 5m)")
        print("API logs sweep scheduler started (cron 12:00 daily, retention 30d)")
    except Exception as e:  # 미설치/시작실패 → 휴면 표시만, 인가는 요청시점 계산이 담당
        print(f"[WARN] sweep schedulers not started: {e}")

    # v6.0 Phase 4 (A-7 #1) — API log 배치 consumer 기동.
    # 미들웨어(APILoggingMiddleware) 는 요청마다 asyncio.Queue 에 payload 를 enqueue 만 수행하고,
    # 실제 INSERT 는 이 consumer 태스크가 배치(100건 or 500ms) 로 flush 한다.
    # 실패해도 앱 기동은 계속 진행 (로그 손실은 있으나 서비스 자체는 유지).
    try:
        from app.middleware.logging import start_log_consumer
        await start_log_consumer()
        print("API log batch consumer started")
    except Exception as e:
        print(f"[WARN] log consumer not started: {e}")

    yield

    # Shutdown
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
    # v6.0 Phase 4 — API log consumer graceful stop (큐 drain 후 종료).
    try:
        from app.middleware.logging import stop_log_consumer
        await stop_log_consumer()
        print("API log batch consumer stopped")
    except Exception:
        pass
    print("GOP API Server Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="GOP RESTful API Server",
    description="""
## General Outpost(GOP) 통합 관제 시스템 RESTful API

GOP 시스템의 디바이스, 이벤트, 서버 통합을 위한 REST API를 제공합니다.

### 🔐 인증 방법 (Authentication)

1. **로그인**: `POST /api/auth/login` 호출
```json
{
  "login_id": "admin",
  "password": "admin123"
}
```

2. **토큰 획득**: Response에서 `access_token` 복사

3. **Swagger 인증**:
   - 우측 상단 **[Authorize]** 버튼 클릭
   - 토큰만 입력 (Bearer 접두사 불필요)
   - **[Authorize]** 클릭

### 주요 기능

- **User Management**: 사용자 계정, 그룹, 세션 관리 (PRD v1.1)
- **Device Management**: Controller, Sensor, Camera 디바이스 CRUD
- **Device Groups**: N:N 관계 기반 디바이스 그룹화 (PRD v1.5)
- **Event Management**: Detection, Malfunction, Connection, Action 이벤트
- **Server Integration**: 외부 서버 연동 및 이벤트 매핑

### 응답 형식

모든 API는 통일된 `ApiResponse` 형식으로 응답합니다:

```json
{
  "success": true,
  "message": "작업 성공",
  "data": { ... },
  "pagination": { ... }  // 목록 조회 시
}
```

### 버전 정보

- **API Version**: 6.0 (release/v6.0 브랜치, 2026-07-03 배포 → 후속 픽스 진행 중)
- **명세**: GOP_Restful_Api_연동설계.md v5.0
- **주요 PRD**: PRD_v5.0_Permission_Management.md, PRD_Tracking_History_API.md, PRD_v4.9_Followup_AccountIntegration.md, PRD_Account_Design.md, PRD_Device_Structure_Refactoring.md, PRD_Report_System.md
- **최신 CHANGELOG**: `CHANGELOG.md` 참조

### v6.0 주요 업데이트 (2026-07-03 ~ 진행 중)

#### Async 대전환 (`v6.0`, 2026-07-03)
- SQLAlchemy 2.x + asyncpg + AsyncSession 완전 전환
- 41 라우터 async 100%, ~99 endpoint RBAC 매트릭스
- api_logs PostgreSQL RANGE 파티셔닝 + `asyncio.Queue` batch INSERT
- Docker autoheal · Chromium PDF 렌더 (Playwright to_thread)

#### 리포트 시스템 (`v6.0-report_*`, 2026-07-04 ~ 07-05)
- **`v6.0-report_fixes`** — 세션/감사/설정/시스템 그리드 컬럼 확장, JSON preview ↔ HTML/PDF 필터 통일, 라벨 통일
- **`v6.0-report_lifecycle_persistence`** — Startup 재조정(PENDING/GENERATING→FAILED), PDF named volume 영속화, 파일 소실 시 HTTP 410
- **`v6.0-report_progress_perf`** — 진행률 필드 3개(`progress_pct`, `progress_stage`, `progress_updated_at`), Stall 워치도그(60s no-progress → FAILED), SQL 집계 이관, 상세 CSV 다운로드 endpoint (`GET /generations/{id}/detail.csv?type=...`)
- **`v6.0-report_date_range`** — 요청에 `start_date/end_date` 커스텀 범위, `period_type="custom"`, 366일 상한

#### 인증 · 계정 (`v6.0-auth_*`, `v6.0-account_*`)
- **`v6.0-auth_mode_secure_default`** — `AUTH_MODE=token` 기본값 (public fallback 시 부팅 WARN + staging/prod 거부)
- **`v6.0-account_rbac`** — ADMIN Static seed 3종(m_manager, vms_manager, popup_manager)
- **`v6.0-account_managers_expand`** — 장비 도메인별 ADMIN 5종 신규(CameraManager, BroadcastingManager, QLiteLampManager, NVRManager, EnclosureManager). 총 9 ADMIN
- 모두 password `sensorway1` (dev/시연 기본값)

#### API 계약 개선
- **`v6.0-servers_port_response_relax`** — `ServerResponse.port` `ge=1 → ge=0` (Postel's Law: 요청 엄격, 응답 관대). 목록 응답 fault tolerance
- 다운로드 응답 분화: 파일 소실 시 404 → **HTTP 410 `PDF_FILE_MISSING`**

#### 인프라 · 배포 (`v6.0-rename_pids`, `v6.0-cert_installer_fix`, `v6.0-bootstrap_automation`)
- **`v6.0-rename_pids`** — 컨테이너/이미지 `api-test-*` → `pids-api-*` (볼륨·데이터 보전)
- **`v6.0-cert_installer_fix`** — HTTPS 인증서 인스톨러 6 버그 픽스. Dockerfile CMD **fail-fast** (인증서 없으면 exit 1, 개발 편의는 `ALLOW_HTTP_FALLBACK=true` 명시 opt-in)
- **`v6.0-bootstrap_automation`** — `bootstrap.ps1` 1-Click 배포 (관리자 상승 + 인증서 발급 + docker up + healthy 대기)

### 신규 · 변경 endpoint 요약

| Endpoint | 변경 |
|---|---|
| `GET /api/reports/generations/{id}` | 응답에 `progress_pct` · `progress_stage` · `progress_updated_at` 3필드 추가 |
| `POST /api/reports/generate` | `start_date` · `end_date` Optional 필드 추가 (커스텀 범위) |
| `GET /api/reports/generations/{id}/detail.csv?type=…` | **신규** — 상세 rows CSV (8 grid type: detection/malfunction/action/system/config/audit/login/session) |
| `POST /api/reports/generations/{id}/cancel` | 진행 중 리포트 취소 (v6.0 후속에서 도입) |
| `GET /api/reports/generations/{id}/download` | 파일 소실 시 404 → **HTTP 410 `PDF_FILE_MISSING`** 분화 |
| `GET /api/servers` | 응답 `port` 제약 `ge=1` → `ge=0`. 목록 응답 fault tolerance |
""",
    version="6.0.0",
    docs_url=None,  # Disable default docs to use custom
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={
        "name": "GOP API Support",
        "email": "support@gop-system.com",
    },
    license_info={
        "name": "Proprietary",
    },
    generate_unique_id_function=lambda route: f"{route.name}",
    # 매트릭스 중앙 집행(미들웨어형) — 전역 단일 choke point. 휴면(public)에선 무집행.
    dependencies=[Depends(enforce_matrix)],
)

# Jinja2 Templates for HTML rendering (PRD Section 10: Preview Page)
templates = Jinja2Templates(directory="app/templates")


# Custom Swagger UI with Log Viewer button
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI with additional navigation buttons
    """
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GOP API - Swagger UI</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                }}
                .custom-header {{
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    padding: 12px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                }}
                .custom-header h1 {{
                    color: #fff;
                    margin: 0;
                    font-size: 1.4em;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                .header-buttons {{
                    display: flex;
                    gap: 10px;
                }}
                .header-btn {{
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    transition: all 0.2s;
                }}
                .btn-logs {{
                    background: #4CAF50;
                    color: white;
                }}
                .btn-logs:hover {{
                    background: #45a049;
                    transform: translateY(-1px);
                }}
                .btn-admin {{
                    background: #2196F3;
                    color: white;
                }}
                .btn-admin:hover {{
                    background: #1976D2;
                    transform: translateY(-1px);
                }}
                .btn-redoc {{
                    background: #607D8B;
                    color: white;
                }}
                .btn-redoc:hover {{
                    background: #546E7A;
                    transform: translateY(-1px);
                }}
            </style>
        </head>
        <body>
            <div class="custom-header">
                <h1>🛡️ GOP RESTful API Server</h1>
                <div class="header-buttons">
                    <a href="/api/logs/viewer" class="header-btn btn-logs">
                        📋 Log Viewer
                    </a>
                    <a href="/redoc" class="header-btn btn-redoc">
                        📖 ReDoc
                    </a>
                </div>
            </div>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
                window.onload = function() {{
                    SwaggerUIBundle({{
                        url: "/openapi.json",
                        dom_id: '#swagger-ui',
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.SwaggerUIStandalonePreset
                        ],
                        layout: "BaseLayout",
                        deepLinking: true,
                        showExtensions: true,
                        showCommonExtensions: true
                    }});
                }}
            </script>
        </body>
        </html>
        """,
        media_type="text/html"
    )


# HTTP Error Code Mapping (PRD: PRD_API_Spec_Compliance.md - SPEC-001)
HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
}


def get_request_id(request: Request) -> str:
    """
    Get request ID from header or generate new one

    PRD: PRD_API_Spec_Compliance.md - SPEC-003
    """
    return request.headers.get("X-Request-ID") or str(uuid4())


def create_error_meta(request: Request) -> dict:
    """
    Create meta object for error response

    PRD: PRD_API_Spec_Compliance.md - SPEC-003
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": get_request_id(request)
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPException and return spec-compliant format

    PRD: PRD_API_Spec_Compliance.md - SPEC-001
    Response format:
    {
      "success": false,
      "error": { "code": "NOT_FOUND", "message": "...", "details": null },
      "meta": { "timestamp": "...", "request_id": "..." }
    }
    """
    # FR-SVF-10: detection 지점이 부여한 안정 sub-code(예: SESSION_REVOKED)를 우선,
    # 없으면 status→code 매핑으로 폴백. details 도 예외가 제공하면 노출.
    error_code = getattr(exc, "code", None) or HTTP_ERROR_CODES.get(exc.status_code, "UNKNOWN_ERROR")
    error_details = getattr(exc, "details", None)

    # PRD v4.9 Phase 2-B1: WWW-Authenticate 등 라우터에서 설정한 헤더 보존 (RFC 6750/7235)
    # 라우터의 HTTPException(headers={"WWW-Authenticate": "Bearer"}) 이 envelope 직렬화 시 손실되지 않도록 전달
    response_headers = getattr(exc, 'headers', None)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail,
                "details": error_details
            },
            "meta": create_error_meta(request)
        },
        headers=response_headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with spec-compliant format

    PRD: PRD_API_Spec_Compliance.md - SPEC-002
    Response format:
    {
      "success": false,
      "message": "Validation error",
      "error": {
        "code": "VALIDATION_ERROR",
        "details": [{"field": "...", "message": "..."}]
      }
    }
    """
    details = []
    for error in exc.errors():
        # Extract field name without 'body' prefix
        loc = error.get("loc", [])
        field_parts = [str(part) for part in loc if part != "body"]
        field = ".".join(field_parts) if field_parts else "unknown"

        details.append({
            "field": field,
            "message": error.get("msg", "Validation error")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": details
            },
            "meta": create_error_meta(request)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions with spec-compliant format

    PRD: PRD_API_Spec_Compliance.md - SPEC-001
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"Internal server error: {str(exc)}",
                "details": None
            },
            "meta": create_error_meta(request)
        }
    )


# CORS middleware (v4.6 FR-3: 화이트리스트 + 메서드/헤더 한정)
# dev 환경은 ["*"] 허용 (편의), staging/prod는 settings.CORS_ORIGINS 명시 도메인만
_cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept"],
)

# Custom middlewares (order matters - applied in reverse)
app.add_middleware(APILoggingMiddleware)  # Applied second
app.add_middleware(RequestIDMiddleware)   # Applied first


@app.middleware("http")
async def add_utf8_charset(request: Request, call_next):
    """JSON 응답에 charset=utf-8 명시 — 클라이언트 한글 인코딩 보장"""
    response = await call_next(request)
    ct = response.headers.get("content-type", "")
    if "application/json" in ct and "charset" not in ct:
        response.headers["content-type"] = ct + "; charset=utf-8"
    return response

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(user_groups.router, prefix="/api/user-groups", tags=["User Groups"])
app.include_router(grants.router, prefix="/api", tags=["User Group Grants"])
app.include_router(user_sessions.router, prefix="/api/user-sessions", tags=["User Sessions"])
app.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["Audit Logs"])
app.include_router(config_change_logs.router, prefix="/api/config-change-logs", tags=["Config Change Logs"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(controllers.router, prefix="/api/devices/controllers", tags=["Controllers"])
app.include_router(sensors.router, prefix="/api/devices/sensors", tags=["Sensors"])
app.include_router(cameras.router, prefix="/api/devices/cameras", tags=["Cameras"])
app.include_router(camera_settings.router, prefix="/api/devices/cameras", tags=["Camera Settings"])
app.include_router(speakers.router, prefix="/api/devices/speakers", tags=["Speakers"])
app.include_router(enclosures.router, prefix="/api/devices/enclosures", tags=["Enclosures"])
app.include_router(lamps.router, prefix="/api/devices/lamps", tags=["Lamps"])
app.include_router(enclosure_metrics.router, prefix="/api/devices/enclosures", tags=["Enclosure Metrics"])
app.include_router(enclosure_metrics.list_router, prefix="/api/enclosure-metrics", tags=["Enclosure Metrics"])
app.include_router(file_groups.router, prefix="/api/file-groups", tags=["FileGroups"])
app.include_router(detections.router, prefix="/api/events/detections", tags=["Detections"])
app.include_router(malfunctions.router, prefix="/api/events/malfunctions", tags=["Malfunctions"])
app.include_router(connections.router, prefix="/api/events/connections", tags=["Connections"])
app.include_router(actions.router, prefix="/api/events/actions", tags=["Actions"])
app.include_router(detection_logs.router, prefix="/api/detection-logs", tags=["Detection Logs"])
app.include_router(event_mappings.router, prefix="/api/integrations/event-mappings", tags=["Integration"])
app.include_router(event_mapping_cameras.router, prefix="/api/integrations/event-mappings", tags=["Event Mapping Cameras"])
app.include_router(event_mapping_speakers.router, prefix="/api/integrations/event-mappings", tags=["Event Mapping Speakers"])
app.include_router(event_mapping_lamps.router, prefix="/api/integrations/event-mappings", tags=["Event Mapping Lamps"])
app.include_router(event_mapping_cameras.flat_router, prefix="/api/integrations/mapping-cameras", tags=["Mapping Cameras"])
app.include_router(event_mapping_speakers.flat_router, prefix="/api/integrations/mapping-speakers", tags=["Mapping Speakers"])
app.include_router(event_mapping_lamps.flat_router, prefix="/api/integrations/mapping-lamps", tags=["Mapping Lamps"])
app.include_router(server_categories.router, prefix="/api/servers/categories", tags=["Server Categories"])
app.include_router(servers.router, prefix="/api/servers", tags=["Servers"])
app.include_router(server_metrics.router, prefix="/api/servers", tags=["Server Metrics"])
app.include_router(proxy_settings.router, prefix="/api/servers", tags=["Proxy Settings"])
app.include_router(system_events.router, prefix="/api/system-events", tags=["System Events"])
app.include_router(device_groups.router, prefix="/api", tags=["DeviceGroups"])
app.include_router(camera_presets.router, prefix="/api/devices/cameras", tags=["CameraPresets"])
app.include_router(rois.router, prefix="/api/presets", tags=["ROIs"])
app.include_router(xypoints.router, prefix="/api/rois", tags=["XyPoints"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(thumbnails.router, prefix="/api/thumbnails", tags=["Thumbnails"])
app.include_router(event_statistics.router, prefix="/api/events/statistics", tags=["Event Statistics"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "GOP RESTful API Server",
        "version": "1.0.0",
        "status": "running",
        "auth_mode": settings.AUTH_MODE,
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(response: Response):
    """
    Health check endpoint — v5.4 후속: silent failure 감지 강화.

    - DB `SELECT 1` 실행 → 커넥션 풀이 살아있는지 실제 검사
    - 실패 시 **503** 반환 → Docker healthcheck가 unhealthy 감지 가능
    - 이전 정적 응답은 이벤트루프 정지·풀 데드락을 못 잡아냄(문서 A-7 #5)

    Note: async def이지만 DB 검사는 asyncio.to_thread로 threadpool 이관 →
    이벤트루프 정지 상황에서는 timeout으로 걸린다(threadpool도 정지된 경우).
    """
    import asyncio
    from sqlalchemy import text as _text
    from app.database import SessionLocal as _SessionLocal

    def _probe_db() -> None:
        db = _SessionLocal()
        try:
            db.execute(_text("SELECT 1")).scalar()
        finally:
            db.close()

    try:
        # 짧은 timeout (2초). 초과하면 db 문제로 간주.
        await asyncio.wait_for(asyncio.to_thread(_probe_db), timeout=2.0)
        return {
            "status": "healthy",
            "auth_mode": settings.AUTH_MODE,
            "db": "ok",
        }
    except Exception as e:
        response.status_code = 503
        return {
            "status": "unhealthy",
            "auth_mode": settings.AUTH_MODE,
            "db": "error",
            "detail": str(e)[:200],
        }


# ==============================================================================
# Report Preview Page → v5.4 P0-1: /api/reports/preview/{id} 로 이관 (인증 강제)
# 이전 무인증 @app.get 엔드포인트는 삭제됨. routers/reports.py::report_preview_page 참조.
# ==============================================================================