# PRD: ServerNestedResponse 스키마 통합 및 수정

**문서 버전**: v1.0
**작성일**: 2026-01-26
**상태**: Draft

---

## 1. 개요

### 1.1 배경

`ServerNestedResponse` 스키마가 두 파일에서 서로 다르게 정의되어 있어 Swagger 문서와 실제 API 응답 간 불일치가 발생하고 있습니다.

### 1.2 문제점

| 파일 | 위치 | 문제 |
|------|------|------|
| `app/schemas/device.py` | Line 575 | v2.9에서 제거된 필드 포함, `threshold_config` 누락 |
| `app/schemas/server.py` | Line 111 | 문서와 일치 (정상) |

### 1.3 영향 범위

- **Swagger 문서**: `ServerNestedResponse`가 `device.py` 버전으로 표시됨
- **Speaker API**: `device.py`의 `ServerNestedResponse`를 사용 중
- **API 일관성**: 문서(GOP_Restful_Api_연동설계.md)와 불일치

---

## 2. 현재 상태 분석

### 2.1 device.py의 ServerNestedResponse (문제 있음)

```python
# app/schemas/device.py:575
class ServerNestedResponse(BaseModel):
    id: int
    category_id: int
    name: str
    status: str
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    cpu_usage: Optional[float] = None       # ← v2.9에서 제거됨
    ram_usage: Optional[float] = None       # ← v2.9에서 제거됨
    disk_usage: Optional[float] = None      # ← v2.9에서 제거됨
    network_throughput: Optional[str] = None # ← v2.9에서 제거됨
    # threshold_config 누락!
```

### 2.2 server.py의 ServerNestedResponse (정상)

```python
# app/schemas/server.py:111
class ServerNestedResponse(BaseModel):
    id: int
    category_id: int
    name: str
    status: str
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    threshold_config: Optional[Dict[str, Any]] = None  # ✅ 문서와 일치
```

### 2.3 문서 기준 (GOP_Restful_Api_연동설계.md v2.9)

> **Note (v2.9 변경)**: `cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput` 필드는 `server_metrics` API로 분리되었습니다.

---

## 3. 수정 방안

### 3.1 목표

1. `device.py`의 `ServerNestedResponse`를 **삭제**
2. `server.py`의 `ServerNestedResponse`를 **재사용**
3. 모든 API에서 일관된 스키마 사용

### 3.2 수정 대상 파일

| 파일 | 수정 내용 |
|------|----------|
| `app/schemas/device.py` | `ServerNestedResponse` 클래스 삭제, import 추가 |
| `app/routers/speakers.py` | import 경로 변경 |

---

## 4. 상세 수정 내용

### 4.1 app/schemas/device.py

**Before (삭제 대상)**:
```python
# Line 575-597 삭제
class ServerNestedResponse(BaseModel):
    """Server Nested Response for Speaker..."""
    id: int
    category_id: int
    name: str
    status: str
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    cpu_usage: Optional[float] = None
    ram_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_throughput: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
```

**After**:
```python
# Line 575 부근에 import 추가
from app.schemas.server import ServerNestedResponse

# ServerNestedResponse 클래스 삭제 (server.py에서 import)
```

### 4.2 app/routers/speakers.py

**Before**:
```python
from app.schemas.device import SpeakerCreate, SpeakerUpdate, SpeakerResponse, ServerNestedResponse
```

**After**:
```python
from app.schemas.device import SpeakerCreate, SpeakerUpdate, SpeakerResponse
from app.schemas.server import ServerNestedResponse
```

---

## 5. 검증 항목

### 5.1 Swagger 확인

수정 후 Swagger에서 `ServerNestedResponse` 스키마가 다음 필드를 포함해야 함:

```
id, category_id, name, status, ip_address, port, hostname,
user_name, user_password, threshold_config
```

**제거되어야 할 필드**:
- `cpu_usage`
- `ram_usage`
- `disk_usage`
- `network_throughput`

### 5.2 API 테스트

| 엔드포인트 | 확인 사항 |
|-----------|----------|
| `GET /api/speakers` | server nested 응답에 `threshold_config` 포함 확인 |
| `GET /api/speakers/{id}` | server nested 응답에 `threshold_config` 포함 확인 |

### 5.3 문서 일치 확인

GOP_Restful_Api_연동설계.md의 Server Response 구조와 일치하는지 확인

---

## 6. 참조 문서

- **GOP_Restful_Api_연동설계.md**: Section 8.3 Server Instance API
- **PRD_Server_Monitoring.md**: Server 스키마 정의
- **PRD_Speaker_Device.md**: Speaker-Server 관계

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| v1.0 | 2026-01-26 | 초안 작성 | Claude |
