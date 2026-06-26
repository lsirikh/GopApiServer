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
from fastapi import FastAPI, Request, status, Depends
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
from app.routers import auth, logs, controllers, sensors, cameras, speakers, enclosures, lamps, detections, malfunctions, connections, actions, detection_logs, event_mappings, server_categories, servers, server_metrics, proxy_settings, camera_settings, system_events, device_groups, camera_presets, rois, xypoints, event_mapping_cameras, event_mapping_speakers, event_mapping_lamps, file_groups, enclosure_metrics, users, user_groups, user_sessions, audit_logs, config_change_logs, reports, thumbnails, event_statistics, tracking
from app.models.report import ReportGeneration
from app.dependencies import get_db
from app.utils.init_db import initialize_database
from app.schemas.common import ApiResponse


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
    Application lifespan events
    """
    # Startup
    print("=" * 60)
    print("GOP API Server Starting...")
    print("=" * 60)

    # Initialize database
    initialize_database()

    # Apply PostgreSQL pg_notify triggers (skips if SQLite)
    apply_triggers(engine)

    print(f"Server running on http://{settings.HOST}:{settings.PORT}")
    print(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Authentication Mode: {settings.AUTH_MODE}")
    print("=" * 60)

    yield

    # Shutdown
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

- API Version: 2.10
- PRD: PRD_Account_Design.md, PRD_Device_Structure_Refactoring.md, PRD_DeviceGroup_BulkUnassign.md
""",
    version="1.6.0",
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
    generate_unique_id_function=lambda route: f"{route.name}"
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
    error_code = HTTP_ERROR_CODES.get(exc.status_code, "UNKNOWN_ERROR")

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
                "details": None
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
app.include_router(user_sessions.router, prefix="/api/user-sessions", tags=["User Sessions"])
app.include_router(audit_logs.router, prefix="/api/audit-logs", tags=["Audit Logs"])
app.include_router(config_change_logs.router, prefix="/api/config-change-logs", tags=["Config Change Logs"])
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
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "auth_mode": settings.AUTH_MODE
    }


# ==============================================================================
# Report Preview Page (HTML)
# ==============================================================================

@app.get("/reports/preview/{generation_id}", include_in_schema=False)
def report_preview_page(
    request: Request,
    generation_id: int,
    db: Session = Depends(get_db)
):
    """
    Report Preview Page (HTML)

    개발용 보고서 미리보기 페이지
    PRD Reference: PRD_Report_System.md Section 10
    """
    from app.services.report_service import ReportService

    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    # Get structured preview data from ReportService
    service = ReportService(db)
    preview_data = service.get_structured_preview_data()

    return templates.TemplateResponse(request, "reports/preview.html", {
        "report": generation,
        "preview": preview_data
    })