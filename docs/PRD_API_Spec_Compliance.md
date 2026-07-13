# PRD: API 스펙 준수 점검 및 수정

**작성일**: 2026-01-14
**버전**: v1.0
**참조 문서**: GOP_Restful_Api_연동설계.md v2.8
**목적**: api-test-server 구현체와 연동설계서 스펙 간의 차이점 분석 및 수정 계획

---

## 1. 개요

### 1.1 분석 범위

- **스펙 문서**: `GOP_Restful_Api_연동설계.md` v2.8 (2026-01-12)
- **구현체**: `api-test-server` 프로젝트
- **분석 대상**: Router, Schema, Model, Error Handling

### 1.2 분석 결과 요약

| 카테고리 | 이슈 수 | 심각도 |
|---------|--------|--------|
| Error Response Format | 2 | HIGH |
| Response Meta Field | 1 | HIGH |
| Enclosure is_enable 필드 | 1 | MEDIUM |
| Delete Response Format | 1 | LOW |
| 기타 불일치 | 3 | LOW |

---

## 2. 상세 이슈 목록

### 2.1 [HIGH] Error Response Format 불일치

**Issue ID**: SPEC-001
**파일 위치**: `app/main.py:294-341`

#### 현재 구현
```python
# app/main.py - http_exception_handler
return JSONResponse(
    status_code=exc.status_code,
    content={
        "success": False,
        "message": exc.detail,
        "data": None
    }
)
```

#### 스펙 요구사항 (Section 3.2)
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Controller not found with Id=999",
    "details": "No controller exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 차이점
1. `error` 객체 구조 누락 - `code`, `message`, `details` 필드가 구조화되지 않음
2. `meta` 객체 누락 - `timestamp`, `request_id` 미포함
3. `data` 필드 사용 - 스펙은 에러 응답에 `data` 필드 미포함

#### 수정 계획
- [ ] `ApiErrorResponse` 스키마를 활용한 에러 응답 포맷 통일
- [ ] `http_exception_handler`에 에러 코드 매핑 로직 추가
- [ ] `RequestIDMiddleware`에서 생성된 request_id를 에러 응답에 포함
- [ ] 에러 발생 시 현재 타임스탬프 자동 생성

---

### 2.2 [HIGH] Validation Error Response Format 불일치

**Issue ID**: SPEC-002
**파일 위치**: `app/main.py:309-326`

#### 현재 구현
```python
return JSONResponse(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    content={
        "success": False,
        "message": "Validation error: " + "; ".join(errors),
        "data": None
    }
)
```

#### 스펙 요구사항 (Section 5.1.1 - 422 Error)
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
  }
}
```

#### 차이점
1. `error.details` 배열 형식 미준수 - 필드별 오류가 구조화되지 않음
2. 필드별 오류가 문자열로 직렬화됨

#### 수정 계획
- [ ] `ValidationErrorResponse` 스키마 활용
- [ ] FastAPI의 `exc.errors()` 파싱하여 `details` 배열 구성
- [ ] 각 오류를 `{ field, message }` 형식으로 변환

---

### 2.3 [HIGH] Response Meta Field 미포함

**Issue ID**: SPEC-003
**파일 위치**: `app/schemas/common.py`, 모든 Router 파일

#### 현재 구현
`ApiResponse` 스키마에 `meta` 필드가 정의되어 있으나, 실제 응답에서 `request_id`가 동적으로 설정되지 않음

```python
# app/schemas/common.py:31-38
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T
    pagination: Optional[PaginationMeta] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
```

#### 스펙 요구사항
모든 응답에 `meta.request_id`가 요청 헤더의 `X-Request-ID` 또는 자동 생성된 UUID로 설정되어야 함

#### 수정 계획
- [ ] Request Context에서 `request_id` 추출하는 유틸리티 함수 생성
- [ ] Router 응답 생성 시 `meta.request_id` 동적 설정
- [ ] 또는 Middleware에서 응답 변환 로직 추가

---

### 2.4 [MEDIUM] Enclosure 스키마 `is_enable` 필드 누락

**Issue ID**: SPEC-004
**파일 위치**: `app/schemas/device.py:729-857`

#### 현재 상황
| Device Type | is_enable 필드 | 스펙 명시 |
|-------------|---------------|----------|
| Controller | ✅ 있음 | ❌ 없음 |
| Sensor | ✅ 있음 | ❌ 없음 |
| Camera | ✅ 있음 | ❌ 없음 |
| Speaker | ✅ 있음 | ❌ 없음 |
| Enclosure | ❌ 없음 | ❌ 없음 |

#### 분석
- 스펙 문서에는 `is_enable` 필드가 Device 스키마에 명시되어 있지 않음
- 그러나 구현에서는 Controller, Sensor, Camera, Speaker에 `is_enable` 필드가 존재
- Enclosure만 `is_enable` 필드가 없어 **일관성 문제** 발생

#### 수정 계획 (옵션 선택 필요)

**옵션 A - Enclosure에 is_enable 추가** (권장)
- 구현 일관성 유지를 위해 Enclosure에도 `is_enable` 필드 추가
- [ ] `EnclosureCreate`에 `is_enable: bool = Field(True)` 추가
- [ ] `EnclosureUpdate`에 `is_enable: Optional[bool] = None` 추가
- [ ] `EnclosureResponse`에 `is_enable: bool` 추가
- [ ] Enclosure Model에 `is_enable` 컬럼 추가 (if not exists)
- [ ] 스펙 문서 업데이트 요청

**옵션 B - 모든 Device에서 is_enable 제거**
- 스펙 준수를 위해 모든 Device에서 `is_enable` 제거
- 이 경우 기존 클라이언트 호환성 문제 발생 가능

---

### 2.5 [LOW] Delete Response data 필드 차이

**Issue ID**: SPEC-005
**파일 위치**: 모든 Router의 DELETE 엔드포인트

#### 현재 구현
```python
return ApiResponse(
    success=True,
    message="Controller deleted successfully",
    data={"id": controller_id}
)
```

#### 스펙 요구사항 (Section 7.2.6)
```json
{
  "success": true,
  "message": "Event mapping deleted successfully",
  "data": null,
  "meta": { ... }
}
```

#### 차이점
- 현재: `data: { id: ... }` 반환
- 스펙: `data: null` 반환

#### 수정 계획
- [ ] DELETE 응답의 `data` 필드를 `None`으로 변경
- [ ] 또는 스펙 문서에 `{ id }` 반환이 유용하다면 스펙 업데이트 요청

---

### 2.6 [LOW] Speaker Response `category_device` 필드

**Issue ID**: SPEC-006
**파일 위치**: `app/schemas/device.py:643-670`

#### 현재 구현
```python
class SpeakerResponse(BaseModel):
    category_device: str = Field("speaker", description="디바이스 카테고리")
    # ...
```

#### 스펙 요구사항
스펙 예제(Section 5.4)에서 `category_device` 필드가 포함되어 있지 않음

#### 분석
- `category_device`는 Polymorphic Discriminator 용도
- 내부용 필드이므로 Response에서 노출 여부 결정 필요

#### 수정 계획
- [ ] 스펙 담당자와 협의하여 `category_device` 노출 여부 결정
- [ ] 불필요 시 Response 스키마에서 제거 또는 스펙에 추가 요청

---

### 2.7 [INFO] Server Router user_name/user_password 필드 미반환

**Issue ID**: SPEC-007
**파일 위치**: `app/routers/servers.py:61-77`

#### 현재 상황
`ServerResponse` 스키마에 `user_name`, `user_password` 필드가 정의되어 있으나, 실제 응답 생성 시 포함되어 있음

```python
# app/schemas/server.py
class ServerResponse(BaseModel):
    user_name: Optional[str] = None
    user_password: Optional[str] = None
```

#### 스펙 요구사항
스펙 예제(Section 5.4.3)에서 Speaker의 nested `server` 객체에 `user_name`, `user_password` 포함

#### 수정 계획
- [x] 현재 구현이 스펙과 일치함 - **수정 불필요**

---

## 3. 수정 우선순위

### Phase 1: Critical (즉시 수정)
1. SPEC-001: Error Response Format 불일치
2. SPEC-002: Validation Error Response Format 불일치
3. SPEC-003: Response Meta Field 미포함

### Phase 2: Important (1주 내)
4. SPEC-004: Enclosure is_enable 필드 일관성

### Phase 3: Minor (추후 정리)
5. SPEC-005: Delete Response data 필드
6. SPEC-006: Speaker category_device 필드

---

## 4. 구현 계획

### 4.1 Error Response 통일 (Phase 1)

**파일 수정**: `app/main.py`

```python
from datetime import datetime
from uuid import uuid4
from fastapi import Request

def get_request_id(request: Request) -> str:
    """Get request ID from header or generate new one"""
    return request.headers.get("X-Request-ID") or str(uuid4())

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with spec-compliant format"""
    error_code = HTTP_ERROR_CODES.get(exc.status_code, "UNKNOWN_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail,
                "details": None
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": get_request_id(request)
            }
        }
    )
```

### 4.2 Validation Error 통일 (Phase 1)

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with spec-compliant format"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field,
            "message": error["msg"]
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
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": get_request_id(request)
            }
        }
    )
```

### 4.3 Enclosure is_enable 추가 (Phase 2)

**파일 수정**: `app/schemas/device.py`

```python
class EnclosureCreate(BaseModel):
    # ... existing fields
    is_enable: bool = Field(True, description="장비 활성화 여부")

class EnclosureUpdate(BaseModel):
    # ... existing fields
    is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")

class EnclosureResponse(BaseModel):
    # ... existing fields
    is_enable: bool = Field(..., description="장비 활성화 여부")
```

**파일 수정**: `app/models/device.py` (if Enclosure model needs update)

---

## 5. 테스트 계획

### 5.1 Error Response 테스트

```python
def test_http_exception_returns_spec_format():
    """404 에러 응답이 스펙 형식을 준수하는지 검증"""
    response = client.get("/api/devices/controllers/99999")
    assert response.status_code == 404

    data = response.json()
    assert data["success"] == False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert "request_id" in data["meta"]

def test_validation_error_returns_spec_format():
    """422 에러 응답이 스펙 형식을 준수하는지 검증"""
    response = client.get("/api/devices/controllers?page=0")
    assert response.status_code == 422

    data = response.json()
    assert data["success"] == False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["details"], list)
```

### 5.2 Enclosure is_enable 테스트

```python
def test_enclosure_create_has_is_enable():
    """Enclosure 생성 시 is_enable 필드 지원 확인"""
    from app.schemas.device import EnclosureCreate

    create_data = EnclosureCreate(
        number_device=101,
        group_device=1,
        name_device="Test Enclosure",
        is_enable=True
    )
    assert create_data.is_enable == True

def test_enclosure_response_has_is_enable():
    """Enclosure 응답에 is_enable 필드 포함 확인"""
    from app.schemas.device import EnclosureResponse
    from datetime import datetime

    response = EnclosureResponse(
        id=1,
        number_device=101,
        group_device=1,
        name_device="Test",
        type_device="IoController",
        status="ACTIVATED",
        door_status="CLOSED",
        is_enable=True,
        heater_enabled=False,
        fan_enabled=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert response.is_enable == True
```

---

## 6. 마이그레이션 고려사항

### 6.1 Breaking Changes

1. **Error Response Format 변경**
   - 기존: `{ success, message, data }`
   - 변경: `{ success, error: { code, message, details }, meta }`
   - **영향**: 에러 처리 로직을 사용하는 클라이언트 수정 필요

2. **Delete Response data 변경** (선택적)
   - 기존: `data: { id: ... }`
   - 변경: `data: null`
   - **영향**: 삭제 후 ID 사용하는 클라이언트 수정 필요

### 6.2 Backward Compatibility

- Error Response 변경은 Breaking Change이므로 API 버전 업그레이드 시 적용 권장
- 또는 `X-API-Version` 헤더로 응답 형식 선택 가능하도록 구현

---

## 7. 관련 파일 목록

| 파일 | 수정 필요 | 이슈 |
|------|----------|------|
| `app/main.py` | ✅ | SPEC-001, SPEC-002, SPEC-003 |
| `app/schemas/common.py` | ⚪ (검토) | SPEC-003 |
| `app/schemas/device.py` | ✅ | SPEC-004, SPEC-006 |
| `app/routers/controllers.py` | ✅ | SPEC-005 |
| `app/routers/sensors.py` | ✅ | SPEC-005 |
| `app/routers/cameras.py` | ✅ | SPEC-005 |
| `app/routers/speakers.py` | ✅ | SPEC-005 |
| `app/routers/enclosures.py` | ✅ | SPEC-004, SPEC-005 |
| `app/routers/event_mappings.py` | ✅ | SPEC-005 |
| `app/routers/server_categories.py` | ✅ | SPEC-005 |
| `app/routers/servers.py` | ✅ | SPEC-005 |
| `app/models/device.py` | ⚪ (확인 필요) | SPEC-004 |

---

## 8. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| 작성자 | | | 2026-01-14 |
| 검토자 | | | |
| 승인자 | | | |

---

## 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2026-01-14 | Claude | 초안 작성 |
