# PRD: Swagger OpenAPI Examples 적용

**버전**: v1.0
**작성일**: 2026-01-14
**상태**: Draft
**관련 문서**: GOP_Restful_Api_연동설계.md v2.8

---

## 1. 개요

### 1.1 목적

GOP_Restful_Api_연동설계.md 문서에 정의된 각 API의 Request/Response Example들을
FastAPI Swagger UI(OpenAPI)에 자동으로 표시되도록 적용한다.

### 1.2 현재 상태

| 항목 | 현재 상태 | 목표 상태 |
|------|----------|----------|
| 스키마 필드 예제 | 일부 적용 (`json_schema_extra`) | 전체 적용 |
| Request Body 예제 | 미적용 | 전체 적용 |
| Response 예제 | 미적용 | 전체 적용 |
| Error Response 예제 | 미적용 | 전체 적용 |

### 1.3 기대 효과

- **API 문서화 자동화**: Swagger UI에서 바로 Example 확인 가능
- **개발 생산성 향상**: 프론트엔드 개발자가 즉시 API 테스트 가능
- **문서 일관성**: GOP_Restful_Api_연동설계.md와 Swagger 동기화

---

## 2. 기술적 접근 방법

### 2.1 FastAPI에서 Example 적용 방법 (3가지)

#### 방법 1: 스키마 레벨 - `model_config` (권장)

Pydantic 모델 전체에 대한 예제를 정의합니다.

```python
from pydantic import BaseModel, ConfigDict

class ControllerCreate(BaseModel):
    number_device: int
    name_device: str
    # ... 필드들

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "number_device": 3,
                "group_device": 1,
                "name_device": "Controller-C",
                "type_device": "Controller",
                "version": "v2.1.0",
                "status": "ACTIVATED",
                "is_enable": True,
                "ip_address": "192.168.1.103",
                "ip_port": 8003
            }
        }
    )
```

**장점**: 스키마 정의와 예제가 함께 있어 유지보수 용이
**단점**: 여러 예제 정의 불가

#### 방법 2: 라우터 레벨 - `responses` 파라미터 (권장)

각 엔드포인트별로 다양한 Response 예제를 정의합니다.

```python
from fastapi import APIRouter

# 예제 데이터 정의 (별도 파일로 분리 권장)
CONTROLLER_EXAMPLES = {
    "create_success": {
        "summary": "Controller 생성 성공",
        "description": "Controller 생성 성공 응답",
        "value": {
            "success": True,
            "message": "Controller created successfully",
            "data": {
                "id": 3,
                "number_device": 3,
                "name_device": "Controller-C",
                # ... 전체 데이터
            }
        }
    },
    "validation_error": {
        "summary": "Validation Error",
        "value": {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data"
            }
        }
    }
}

@router.post(
    "",
    response_model=ApiResponse[ControllerResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Controller 생성 성공",
            "content": {
                "application/json": {
                    "examples": {
                        "success": CONTROLLER_EXAMPLES["create_success"]
                    }
                }
            }
        },
        400: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "examples": {
                        "error": CONTROLLER_EXAMPLES["validation_error"]
                    }
                }
            }
        }
    }
)
async def create_controller(...):
    ...
```

**장점**: 상태 코드별 다양한 예제 정의 가능
**단점**: 라우터 코드가 복잡해짐 → 별도 파일 분리 필요

#### 방법 3: Body 파라미터 - `Body(examples=...)` (Request용)

Request Body에 여러 예제를 정의합니다.

```python
from fastapi import Body

@router.post("")
async def create_controller(
    controller: ControllerCreate = Body(
        ...,
        openapi_examples={
            "basic": {
                "summary": "기본 Controller 생성",
                "description": "필수 필드만 포함",
                "value": {
                    "number_device": 3,
                    "group_device": 1,
                    "name_device": "Controller-C",
                    "type_device": "Controller",
                    "version": "v2.1.0",
                    "status": "ACTIVATED",
                    "ip_address": "192.168.1.103",
                    "ip_port": 8003
                }
            },
            "with_geolocation": {
                "summary": "위치 정보 포함",
                "description": "geolocation 필드 포함",
                "value": {
                    "number_device": 3,
                    "group_device": 1,
                    "name_device": "Controller-C",
                    "type_device": "Controller",
                    "version": "v2.1.0",
                    "status": "ACTIVATED",
                    "ip_address": "192.168.1.103",
                    "ip_port": 8003,
                    "geolocation": {
                        "location": "GOP 3초소",
                        "latitude": 38.1234,
                        "longitude": 127.5678
                    }
                }
            }
        }
    )
):
    ...
```

**장점**: Request에 여러 예제 제공 가능
**단점**: 함수 시그니처가 복잡해짐

---

## 3. 권장 구현 전략

### 3.1 파일 구조

```
app/
├── routers/
│   ├── controllers.py
│   ├── sensors.py
│   └── ...
├── schemas/
│   ├── device.py
│   └── ...
└── openapi/                    # 신규 폴더
    ├── __init__.py
    ├── examples/
    │   ├── __init__.py
    │   ├── controller_examples.py
    │   ├── sensor_examples.py
    │   ├── camera_examples.py
    │   ├── speaker_examples.py
    │   ├── event_examples.py
    │   └── common_examples.py
    └── responses/
        ├── __init__.py
        └── error_responses.py
```

### 3.2 예제 파일 구조

```python
# app/openapi/examples/controller_examples.py
"""
Controller API OpenAPI Examples
Source: GOP_Restful_Api_연동설계.md Section 5.1
"""

# ============================================================================
# Request Body Examples
# ============================================================================

CONTROLLER_CREATE_EXAMPLES = {
    "basic": {
        "summary": "기본 Controller 생성",
        "description": "필수 필드만 포함한 Controller 생성 요청",
        "value": {
            "number_device": 3,
            "group_device": 1,
            "name_device": "Controller-C",
            "type_device": "Controller",
            "version": "v2.1.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.1.103",
            "ip_port": 8003
        }
    },
    "with_geolocation": {
        "summary": "위치 정보 포함",
        "description": "geolocation 필드를 포함한 Controller 생성 요청",
        "value": {
            "number_device": 3,
            "group_device": 1,
            "name_device": "Controller-C",
            "type_device": "Controller",
            "version": "v2.1.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.1.103",
            "ip_port": 8003,
            "geolocation": {
                "location": "GOP 3초소",
                "latitude": 38.1234,
                "longitude": 127.5678
            }
        }
    },
    "with_group_ids": {
        "summary": "디바이스 그룹 포함",
        "description": "group_ids 배열을 포함한 Controller 생성 요청",
        "value": {
            "number_device": 3,
            "group_device": 1,
            "name_device": "Controller-C",
            "type_device": "Controller",
            "version": "v2.1.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.1.103",
            "ip_port": 8003,
            "group_ids": [1, 2]
        }
    }
}

CONTROLLER_UPDATE_EXAMPLES = {
    "update_name": {
        "summary": "이름만 수정",
        "value": {
            "name_device": "Controller-C-Updated"
        }
    },
    "update_status": {
        "summary": "상태 수정",
        "value": {
            "status": "DEACTIVATED"
        }
    },
    "update_is_enable": {
        "summary": "활성화 상태 수정",
        "value": {
            "is_enable": False
        }
    },
    "update_multiple": {
        "summary": "여러 필드 수정",
        "value": {
            "name_device": "Controller-C-Updated",
            "version": "v2.2.0",
            "status": "MAINTENANCE",
            "is_enable": False
        }
    }
}

# ============================================================================
# Response Examples
# ============================================================================

CONTROLLER_RESPONSE_EXAMPLES = {
    "single": {
        "summary": "단일 Controller 조회",
        "description": "GET /api/devices/controllers/{id} 응답",
        "value": {
            "success": True,
            "message": "Controller retrieved successfully",
            "data": {
                "id": 1,
                "number_device": 1,
                "group_device": 1,
                "name_device": "Controller-A",
                "type_device": "Controller",
                "version": "v2.1.0",
                "status": "ACTIVATED",
                "is_enable": True,
                "ip_address": "192.168.1.101",
                "ip_port": 8001,
                "geolocation": {
                    "location": "GOP 1구역 초소",
                    "latitude": 38.1234,
                    "longitude": 127.5678
                },
                "created_at": "2025-01-01T00:00:00.000Z",
                "updated_at": "2025-01-01T00:00:00.000Z",
                "device_groups": [
                    {
                        "id": 1,
                        "name": "GOP 1구역",
                        "description": "GOP 1구역 장비 그룹",
                        "device_count": 5
                    }
                ]
            }
        }
    },
    "with_sensors": {
        "summary": "센서 목록 포함",
        "description": "GET /api/devices/controllers/{id}?include_sensors=true 응답",
        "value": {
            "success": True,
            "message": "Controller retrieved successfully",
            "data": {
                "id": 1,
                "number_device": 1,
                "group_device": 1,
                "name_device": "Controller-A",
                "type_device": "Controller",
                "version": "v2.1.0",
                "status": "ACTIVATED",
                "is_enable": True,
                "ip_address": "192.168.1.101",
                "ip_port": 8001,
                "geolocation": None,
                "created_at": "2025-01-01T00:00:00.000Z",
                "updated_at": "2025-01-01T00:00:00.000Z",
                "device_groups": [],
                "sensors": [
                    {
                        "id": 101,
                        "number_device": 101,
                        "group_device": 1,
                        "name_device": "Sensor-A-1",
                        "type_device": "Multi",
                        "version": "v1.5.0",
                        "status": "ACTIVATED",
                        "is_enable": True,
                        "controller_id": 1,
                        "geolocation": None,
                        "device_groups": []
                    },
                    {
                        "id": 102,
                        "number_device": 102,
                        "group_device": 1,
                        "name_device": "Sensor-A-2",
                        "type_device": "Fence",
                        "version": "v1.5.0",
                        "status": "ACTIVATED",
                        "is_enable": True,
                        "controller_id": 1,
                        "geolocation": None,
                        "device_groups": []
                    }
                ]
            }
        }
    }
}

CONTROLLER_LIST_RESPONSE_EXAMPLE = {
    "summary": "Controller 목록 조회",
    "description": "GET /api/devices/controllers 응답",
    "value": {
        "success": True,
        "message": "3 controllers retrieved",
        "data": [
            {
                "id": 1,
                "number_device": 1,
                "group_device": 1,
                "name_device": "Controller-A",
                "type_device": "Controller",
                "version": "v2.1.0",
                "status": "ACTIVATED",
                "is_enable": True,
                "ip_address": "192.168.1.101",
                "ip_port": 8001,
                "geolocation": None,
                "created_at": "2025-01-01T00:00:00.000Z",
                "updated_at": "2025-01-01T00:00:00.000Z",
                "device_groups": []
            },
            {
                "id": 2,
                "number_device": 2,
                "group_device": 1,
                "name_device": "Controller-B",
                "type_device": "Controller",
                "version": "v2.1.0",
                "status": "ACTIVATED",
                "is_enable": True,
                "ip_address": "192.168.1.102",
                "ip_port": 8002,
                "geolocation": None,
                "created_at": "2025-01-01T00:00:00.000Z",
                "updated_at": "2025-01-01T00:00:00.000Z",
                "device_groups": []
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 3,
            "total_pages": 1
        }
    }
}

CONTROLLER_CREATE_RESPONSE_EXAMPLE = {
    "summary": "Controller 생성 성공",
    "description": "POST /api/devices/controllers 응답 (201 Created)",
    "value": {
        "success": True,
        "message": "Controller created successfully",
        "data": {
            "id": 3,
            "number_device": 3,
            "group_device": 1,
            "name_device": "Controller-C",
            "type_device": "Controller",
            "version": "v2.1.0",
            "status": "ACTIVATED",
            "is_enable": True,
            "ip_address": "192.168.1.103",
            "ip_port": 8003,
            "geolocation": {
                "location": "GOP 3초소",
                "latitude": 38.1234,
                "longitude": 127.5678
            },
            "created_at": "2025-01-10T10:30:00.000Z",
            "updated_at": "2025-01-10T10:30:00.000Z",
            "device_groups": [
                {
                    "id": 1,
                    "name": "GOP 1구역",
                    "description": "GOP 1구역 장비 그룹",
                    "device_count": 6
                }
            ]
        }
    }
}
```

### 3.3 공통 에러 응답 정의

```python
# app/openapi/responses/error_responses.py
"""
Common Error Response Examples
"""

ERROR_RESPONSES = {
    400: {
        "description": "Bad Request - 요청 데이터 검증 실패",
        "content": {
            "application/json": {
                "examples": {
                    "validation_error": {
                        "summary": "Validation Error",
                        "value": {
                            "success": False,
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "Invalid input data",
                                "details": [
                                    {
                                        "field": "ip_address",
                                        "message": "Invalid IP address format"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    },
    404: {
        "description": "Not Found - 리소스를 찾을 수 없음",
        "content": {
            "application/json": {
                "examples": {
                    "not_found": {
                        "summary": "Resource Not Found",
                        "value": {
                            "success": False,
                            "error": {
                                "code": "NOT_FOUND",
                                "message": "Controller not found with Id=999",
                                "details": "No controller exists with the specified ID"
                            }
                        }
                    }
                }
            }
        }
    },
    409: {
        "description": "Conflict - 중복 리소스",
        "content": {
            "application/json": {
                "examples": {
                    "duplicate": {
                        "summary": "Duplicate Resource",
                        "value": {
                            "success": False,
                            "error": {
                                "code": "CONFLICT",
                                "message": "Controller with number_device=3 already exists",
                                "details": "A controller with the same number_device already exists"
                            }
                        }
                    }
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error - 서버 내부 오류",
        "content": {
            "application/json": {
                "examples": {
                    "server_error": {
                        "summary": "Server Error",
                        "value": {
                            "success": False,
                            "error": {
                                "code": "INTERNAL_ERROR",
                                "message": "An unexpected error occurred",
                                "details": "Please contact system administrator"
                            }
                        }
                    }
                }
            }
        }
    }
}
```

### 3.4 라우터 적용 예시

```python
# app/routers/controllers.py

from fastapi import APIRouter, Body
from app.openapi.examples.controller_examples import (
    CONTROLLER_CREATE_EXAMPLES,
    CONTROLLER_UPDATE_EXAMPLES,
    CONTROLLER_RESPONSE_EXAMPLES,
    CONTROLLER_LIST_RESPONSE_EXAMPLE,
    CONTROLLER_CREATE_RESPONSE_EXAMPLE
)
from app.openapi.responses.error_responses import ERROR_RESPONSES

router = APIRouter(tags=["Controllers"])


@router.get(
    "",
    response_model=ApiResponse[list[ControllerResponse]],
    responses={
        200: {
            "description": "Controller 목록 조회 성공",
            "content": {
                "application/json": {
                    "examples": {
                        "list": CONTROLLER_LIST_RESPONSE_EXAMPLE
                    }
                }
            }
        },
        **{k: v for k, v in ERROR_RESPONSES.items() if k in [400, 500]}
    }
)
async def list_controllers(...):
    ...


@router.get(
    "/{controller_id}",
    response_model=ApiResponse[ControllerResponse],
    responses={
        200: {
            "description": "Controller 조회 성공",
            "content": {
                "application/json": {
                    "examples": CONTROLLER_RESPONSE_EXAMPLES
                }
            }
        },
        **{k: v for k, v in ERROR_RESPONSES.items() if k in [404, 500]}
    }
)
async def get_controller(...):
    ...


@router.post(
    "",
    response_model=ApiResponse[ControllerResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Controller 생성 성공",
            "content": {
                "application/json": {
                    "examples": {
                        "created": CONTROLLER_CREATE_RESPONSE_EXAMPLE
                    }
                }
            }
        },
        **{k: v for k, v in ERROR_RESPONSES.items() if k in [400, 409, 500]}
    }
)
async def create_controller(
    controller: ControllerCreate = Body(
        ...,
        openapi_examples=CONTROLLER_CREATE_EXAMPLES
    ),
    db: Session = Depends(get_db)
):
    ...


@router.patch(
    "/{controller_id}",
    response_model=ApiResponse[ControllerResponse],
    responses={
        200: {
            "description": "Controller 수정 성공",
            "content": {
                "application/json": {
                    "examples": {
                        "updated": CONTROLLER_RESPONSE_EXAMPLES["single"]
                    }
                }
            }
        },
        **{k: v for k, v in ERROR_RESPONSES.items() if k in [400, 404, 500]}
    }
)
async def update_controller(
    controller_id: int,
    controller_update: ControllerUpdate = Body(
        ...,
        openapi_examples=CONTROLLER_UPDATE_EXAMPLES
    ),
    db: Session = Depends(get_db)
):
    ...
```

---

## 4. 구현 계획

### 4.1 Phase별 구현

| Phase | 작업 내용 | 우선순위 |
|-------|----------|----------|
| 1 | 폴더 구조 생성 (`app/openapi/`) | High |
| 2 | 공통 에러 응답 정의 | High |
| 3 | Controller API Examples | High |
| 4 | Sensor API Examples | High |
| 5 | Camera API Examples | Medium |
| 6 | Speaker API Examples | Medium |
| 7 | Enclosure API Examples | Medium |
| 8 | DeviceGroup API Examples | Medium |
| 9 | Event API Examples | Low |
| 10 | Integration API Examples | Low |
| 11 | Server Monitoring API Examples | Low |

### 4.2 API별 Example 매핑 (GOP_Restful_Api_연동설계.md 기준)

| API | Section | Request Examples | Response Examples |
|-----|---------|------------------|-------------------|
| Controller | 5.1 | Create, Update | List, Single, WithSensors |
| Sensor | 5.2 | Create, Update | List, Single, WithController |
| Camera | 5.3 | Create, Update | List, Single |
| Speaker | 5.4 | Create, Update | List, Single |
| Enclosure | 5.5 | Create, Update | List, Single |
| DeviceGroup | 5.6 | Create, Update, Assign | List, Single, WithDevices |
| Detection Event | 6.1 | Create | List, Single |
| Malfunction Event | 6.2 | Create | List, Single |
| Connection Event | 6.3 | Create | List, Single |
| Action Event | 6.4 | Create, Update | List, Single |
| EventMapping | 7.2 | Create, Update | List, Single |

---

## 5. Swagger UI 결과 예시

적용 후 Swagger UI에서:

1. **Request Body**: 드롭다운으로 여러 예제 선택 가능
   - "기본 Controller 생성"
   - "위치 정보 포함"
   - "디바이스 그룹 포함"

2. **Response**: 상태 코드별 예제 표시
   - 200: 성공 응답 예제
   - 400: Validation Error 예제
   - 404: Not Found 예제
   - 500: Server Error 예제

3. **Try it out**: 예제 데이터가 자동으로 채워짐

---

## 6. 테스트 방법

### 6.1 Swagger UI 확인

```bash
# 서버 실행
uvicorn app.main:app --reload

# 브라우저에서 확인
http://localhost:8000/docs
```

### 6.2 OpenAPI JSON 검증

```bash
# OpenAPI spec 다운로드
curl http://localhost:8000/openapi.json > openapi.json

# JSON 검증
python -m json.tool openapi.json > /dev/null && echo "Valid JSON"
```

---

## 7. 참고 사항

### 7.1 FastAPI 버전 요구사항

- FastAPI >= 0.100.0 (`openapi_examples` 파라미터 지원)
- Pydantic >= 2.0 (`model_config` 지원)

### 7.2 주의사항

1. **Example 데이터 일관성**: GOP_Restful_Api_연동설계.md의 예제와 동일하게 유지
2. **is_enable 필드**: 모든 Device 관련 예제에 포함 필수
3. **Nested Response 규칙**: device_groups에서 timestamp 제외
4. **URL 형식**: urls 필드는 CameraUrls 스키마 형식 준수

### 7.3 관련 문서

- [FastAPI Request Body Examples](https://fastapi.tiangolo.com/tutorial/schema-extra-example/)
- [FastAPI Additional Responses](https://fastapi.tiangolo.com/advanced/additional-responses/)
- [OpenAPI 3.0 Examples](https://spec.openapis.org/oas/v3.0.3#example-object)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-01-14 | 초안 작성 |
