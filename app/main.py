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
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from contextlib import asynccontextmanager

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import APILoggingMiddleware
from app.routers import auth, logs, controllers, sensors, cameras, speakers, enclosures, detections, malfunctions, connections, actions, event_mappings, server_categories, servers, device_groups, camera_presets, rois, xypoints, event_mapping_cameras, event_mapping_speakers, file_groups
from app.utils.init_db import initialize_database
from app.schemas.common import ApiResponse


# OpenAPI 태그 메타데이터 정의
tags_metadata = [
    {
        "name": "Authentication",
        "description": "사용자 인증 및 토큰 관리 API",
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
        "name": "Speakers",
        "description": "스피커 디바이스 CRUD API. 방송 단말 장치로 Server 연동을 지원합니다. PRD_Speaker_Device.md 참조.",
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
        "name": "Server Categories",
        "description": "서버 카테고리 관리 API.",
    },
    {
        "name": "Servers",
        "description": "외부 서버 관리 API.",
    },
    {
        "name": "Logs",
        "description": "시스템 로그 조회 및 뷰어 API.",
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

### 주요 기능

- **Device Management**: Controller, Sensor, Camera 디바이스 CRUD
- **Device Groups**: N:N 관계 기반 디바이스 그룹화 (PRD v1.5)
- **Camera Extended Fields**: HardwareSpec, Geolocation 복합 타입 지원
- **Event Management**: Detection, Malfunction, Connection, Action 이벤트
- **Server Integration**: 외부 서버 연동 및 이벤트 매핑

### 인증

API는 선택적 JWT 토큰 인증을 지원합니다. `AUTH_MODE` 설정에 따라 인증이 활성화됩니다.

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

- API Version: 1.5.0
- PRD: PRD_Device_Structure_Refactoring.md
""",
    version="1.5.0",
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


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPException and return ApiResponse format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and return ApiResponse format
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error: " + "; ".join(errors),
            "data": None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions and return ApiResponse format
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"Internal server error: {str(exc)}",
            "data": None
        }
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middlewares (order matters - applied in reverse)
app.add_middleware(APILoggingMiddleware)  # Applied second
app.add_middleware(RequestIDMiddleware)   # Applied first

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(controllers.router, prefix="/api/devices/controllers", tags=["Controllers"])
app.include_router(sensors.router, prefix="/api/devices/sensors", tags=["Sensors"])
app.include_router(cameras.router, prefix="/api/devices/cameras", tags=["Cameras"])
app.include_router(speakers.router, prefix="/api/devices/speakers", tags=["Speakers"])
app.include_router(enclosures.router, prefix="/api/devices/enclosures", tags=["Enclosures"])
app.include_router(file_groups.router, prefix="/api/file-groups", tags=["FileGroups"])
app.include_router(detections.router, prefix="/api/events/detections", tags=["Detections"])
app.include_router(malfunctions.router, prefix="/api/events/malfunctions", tags=["Malfunctions"])
app.include_router(connections.router, prefix="/api/events/connections", tags=["Connections"])
app.include_router(actions.router, prefix="/api/events/actions", tags=["Actions"])
app.include_router(event_mappings.router, prefix="/api/integrations/event-mappings", tags=["Integration"])
app.include_router(event_mapping_cameras.router, prefix="/api/integrations/event-mappings", tags=["Event Mapping Cameras"])
app.include_router(event_mapping_speakers.router, prefix="/api/integrations/event-mappings", tags=["Event Mapping Speakers"])
app.include_router(server_categories.router, prefix="/api/servers/categories", tags=["Server Categories"])
app.include_router(servers.router, prefix="/api/servers", tags=["Servers"])
app.include_router(device_groups.router, prefix="/api", tags=["DeviceGroups"])
app.include_router(camera_presets.router, prefix="/api/devices/cameras", tags=["CameraPresets"])
app.include_router(rois.router, prefix="/api/presets", tags=["ROIs"])
app.include_router(xypoints.router, prefix="/api/rois", tags=["XyPoints"])

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