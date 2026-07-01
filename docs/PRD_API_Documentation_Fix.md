# PRD: GOP REST API 연동설계 문서 보완

**문서 버전**: 1.0
**작성일**: 2026-01-12
**대상 문서**: `GOP_Restful_Api_연동설계.md` (v2.8)

---

## 1. 개요

### 1.1 목적
GOP REST API 연동설계 문서의 누락된 항목 및 일관성 문제를 파악하고, 표준화된 형식으로 보완하기 위한 PRD 문서입니다.

### 1.2 표준 응답 형식

#### Success Response (목록 조회)
```json
{
  "success": true,
  "message": "...",
  "data": [...],
  "pagination": { "page": 1, "limit": 20, "total": n, "total_pages": n },
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

#### Success Response (단일/생성/수정/삭제)
```json
{
  "success": true,
  "message": "...",
  "data": {...},
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

#### Error Response - 404 Not Found (표준)
```json
{
  "success": false,
  "message": "{Resource} with id {id} not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### Error Response - 422 Validation Error
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "...", "message": "..."}
    ]
  }
}
```

---

## 2. 문제점 요약

| 카테고리 | 문제 유형 | 영향 API 수 | 우선순위 |
|---------|----------|------------|---------|
| Request Example | 누락 | 약 85개 | 중 |
| Error Response 404 | 누락 | 약 30개 | 고 |
| Error Response 422 | 누락 | 약 25개 | 중 |
| Field Table | PATCH API 누락 | 약 20개 | 중 |
| Error Format | 비표준 형식 | 12개 | 고 |
| Response Body | 누락 | 5개 | 고 |

---

## 3. 섹션별 상세 보완 항목

### 3.1 Device API (5.x)

#### 3.1.1 Controller API (5.1)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.1.1 목록 조회 | - | 완전 (참고용) |
| 5.1.2 단일 조회 | - | 완전 (참고용) |
| 5.1.3 생성 | Request Example | HTTP Request 헤더 포함 예제 추가 |
| 5.1.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.1.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.1.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.2 Sensor API (5.2)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.2.1 목록 조회 | Request Example | HTTP GET 요청 예제 추가 |
| 5.2.2 단일 조회 | - | 완전 |
| 5.2.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.2.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.2.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.2.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.3 Camera API (5.3)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.3.1 목록 조회 | Request Example | HTTP GET 요청 예제 추가 |
| 5.3.2 단일 조회 | - | 완전 |
| 5.3.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.3.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.3.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.3.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.4 Speaker API (5.4)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.4.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 5.4.2 상세 조회 | Request Example | HTTP 예제 추가 |
| 5.4.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.4.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.4.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.4.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.5 Enclosure API (5.5)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.5.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 5.5.2 상세 조회 | Request Example, Response Example, Error Response 404 | 전체 보완 필요 |
| 5.5.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.5.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.5.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.5.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |
| **5.5.7 환경 데이터** | **Path Params, Response JSON, Error Response** | **전체 보완 필요 (긴급)** |
| **5.5.8 히터/팬 제어** | **Path Params, Response JSON, Error Response** | **전체 보완 필요 (긴급)** |

#### 3.1.6 DeviceGroup API (5.6)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.6.1 목록 조회 | - | 완전 (Request Example O) |
| 5.6.2 상세 조회 | - | 완전 (Request Example O) |
| 5.6.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.6.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.6.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.6.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |
| 5.6.7 디바이스 할당 | Request Example | HTTP 요청 예제 추가 |
| 5.6.8 디바이스 제거 | Request Example | HTTP 요청 예제 추가 |

#### 3.1.7 CameraPreset API (5.7)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.7.1 목록 조회 | - | 완전 (Request Example O) |
| 5.7.2 상세 조회 | Request Example | HTTP 예제 추가 |
| 5.7.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.7.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.7.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.7.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.8 ROI API (5.8)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.8.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 5.8.2 상세 조회 | Request Example | HTTP 예제 추가 |
| 5.8.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.8.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.8.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 5.8.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.9 XyPoint API (5.9)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.9.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 5.9.2 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 5.9.3 일괄 수정 | Request Example | HTTP 요청 예제 추가 |
| 5.9.4 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.1.10 FileGroup API (5.10) - **Error Format 표준화 필요**

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 5.10.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 5.10.2 상세 조회 | Request Example | HTTP 예제 추가 |
| **5.10.3 생성** | Request Example, **Error Format 수정** | **404/409 형식을 표준 형식으로 변경** |
| **5.10.4 수정(PATCH)** | Request Example, **Error Format 수정** | **404 형식을 표준 형식으로 변경** |
| **5.10.5 수정(PUT)** | Request Example, **Error Format 수정** | **404 형식을 표준 형식으로 변경** |
| **5.10.6 삭제** | Request Example, **Error Format 수정** | **404 형식을 표준 형식으로 변경** |

---

### 3.2 Event API (6.x)

#### 3.2.1 Detection Event API (6.1)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 6.1.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 6.1.2 단일 조회 | - | 완전 |
| 6.1.3 생성 | Request Example, Field Table, Response 201, Error Response | 전체 보완 필요 |
| 6.1.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.1.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.1.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |
| 6.1.7 Action Event 조회 | - | 완전 (Request Example O) |

#### 3.2.2 Malfunction Event API (6.2)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 6.2.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 6.2.2 단일 조회 | - | 완전 (Request Example O) |
| 6.2.3 생성 | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.2.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.2.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.2.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |
| 6.2.7 Action Event 조회 | - | 완전 (Request Example O) |

#### 3.2.3 Connection Event API (6.3)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 6.3.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 6.3.2 단일 조회 | - | 완전 (Request Example O) |
| 6.3.3 생성 | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.3.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.3.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.3.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.2.4 Action Event API (6.4)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 6.4.1 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 6.4.2 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 6.4.3 단일 조회 | - | 완전 (Request Example O) |
| 6.4.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.4.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 6.4.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

---

### 3.3 Integration API (7.x)

#### 3.3.1 EventMapping API (7.2)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 7.2.1 목록 조회 | - | 완전 (Request Example O) |
| 7.2.2 상세 조회 | - | 완전 (Request Example O) |
| 7.2.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 7.2.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 7.2.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 7.2.6 삭제 | - | 완전 (Request Example O) |

#### 3.3.2 EventMappingCamera API (7.3) - **완전**

모든 6개 API 완전 (Request Example 포함)

#### 3.3.3 EventMappingSpeaker API (7.4) - **완전**

모든 6개 API 완전 (Request Example 포함)

---

### 3.4 Server API (8.x)

#### 3.4.1 Server Category API (8.2)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 8.2.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| 8.2.2 상세 조회 | Request Example | HTTP 예제 추가 |
| 8.2.3 생성 | Request Example | HTTP POST 요청 예제 추가 |
| 8.2.4 수정(PATCH) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 8.2.5 수정(PUT) | Request Example, Field Table | HTTP 예제 + 필드 테이블 추가 |
| 8.2.6 삭제 | Request Example | HTTP DELETE 요청 예제 추가 |

#### 3.4.2 Server Instance API (8.3) - **긴급 수정 필요**

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 8.3.1 목록 조회 | Request Example, Error Response 422 | HTTP 예제 + 422 에러 추가 |
| **8.3.2 상세 조회** | Request Example, **Response JSON** | **Response 예제 JSON 추가 필요** |
| **8.3.3 생성** | Request Example, **Response 201 JSON, Error Response** | **전체 보완 필요 (긴급)** |
| **8.3.4 수정(PATCH)** | Request Example, **Error Format 수정** | **404 형식을 표준 형식으로 변경** |
| **8.3.5 수정(PUT)** | Request Example, **Error Format 수정** | **404 형식을 표준 형식으로 변경** |
| 8.3.6 삭제 | Request Example, Error Response 404 | HTTP 예제 + 404 에러 추가 |

#### 3.4.3 Dashboard Summary API (8.4)

| API | 누락 항목 | 보완 내용 |
|-----|----------|----------|
| 8.4.1 서버 요약 조회 | Request Example | HTTP GET 요청 예제 추가 |

---

## 4. Error Response 형식 표준화

### 4.1 비표준 형식 발견 위치

다음 API들은 `{"detail": "..."}` 형식을 사용하고 있어 표준 형식으로 변경 필요:

| 섹션 | API | 현재 형식 | 변경 필요 |
|-----|-----|----------|----------|
| 5.10.3 | FileGroup 생성 | `{"detail": "Server with id 999 not found"}` | 표준 404 형식 |
| 5.10.3 | FileGroup 생성 | `{"detail": "FileGroup ... already exists"}` | 표준 409 형식 추가 |
| 5.10.4 | FileGroup 수정(PATCH) | `{"detail": "FileGroup with id 999 not found"}` | 표준 404 형식 |
| 5.10.5 | FileGroup 수정(PUT) | `{"detail": "FileGroup/Server with id 999 not found"}` | 표준 404 형식 |
| 5.10.6 | FileGroup 삭제 | `{"detail": "FileGroup with id 999 not found"}` | 표준 404 형식 |
| 8.3.4 | Server 수정(PATCH) | `{"detail": "Server with id 999 not found"}` | 표준 404 형식 |
| 8.3.5 | Server 수정(PUT) | `{"detail": "Server with id 999 not found"}` | 표준 404 형식 |

### 4.2 표준 409 Conflict Error 형식 추가

```json
{
  "success": false,
  "message": "Resource already exists",
  "error": {
    "code": "CONFLICT",
    "details": "FileGroup with server_id=1 and group_id=2 already exists"
  }
}
```

---

## 5. 우선순위별 작업 계획

### Phase 1: 긴급 (Error Format + Missing Response)

1. **5.5.7 환경 데이터 업데이트** - Response JSON, Error Response 추가
2. **5.5.8 히터/팬 제어** - Response JSON, Error Response 추가
3. **8.3.3 서버 생성** - Response 201 JSON, Error Response 추가
4. **8.3.2 서버 상세 조회** - Response JSON 예제 추가
5. **5.10.x FileGroup** - Error Response 형식 표준화 (6개 API)
6. **8.3.4-8.3.5 Server** - Error Response 형식 표준화 (2개 API)

### Phase 2: 고 (Error Response 누락)

1. 목록 조회 API 422 Validation Error 추가 (약 25개)
2. 삭제 API 404 Error Response 추가 (약 10개)

### Phase 3: 중 (Request Example + Field Table)

1. 모든 POST 생성 API에 Request Example 추가
2. 모든 PATCH 수정 API에 Field Table + Request Example 추가
3. 모든 PUT 수정 API에 Field Table + Request Example 추가
4. 모든 DELETE 삭제 API에 Request Example 추가
5. 목록 조회 API에 Request Example 추가

---

## 6. Request Example 템플릿

### GET 요청 (목록 조회)
```http
GET /api/{resource}?page=1&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

### GET 요청 (단일 조회)
```http
GET /api/{resource}/{id} HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

### POST 요청 (생성)
```http
POST /api/{resource} HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "field1": "value1",
  "field2": "value2"
}
```

### PATCH 요청 (부분 수정)
```http
PATCH /api/{resource}/{id} HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "field_to_update": "new_value"
}
```

### PUT 요청 (전체 수정)
```http
PUT /api/{resource}/{id} HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "all_required_fields": "..."
}
```

### DELETE 요청 (삭제)
```http
DELETE /api/{resource}/{id} HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

---

## 7. 완전한 API 목록 (참고용)

다음 API들은 모든 필수 항목이 완전히 문서화되어 있습니다:

| 섹션 | API |
|-----|-----|
| 5.1.1 | Controller 목록 조회 |
| 5.1.2 | Controller 단일 조회 |
| 5.2.2 | Sensor 단일 조회 |
| 5.3.2 | Camera 단일 조회 |
| 5.6.1 | DeviceGroup 목록 조회 |
| 5.6.2 | DeviceGroup 상세 조회 |
| 5.7.1 | CameraPreset 목록 조회 |
| 6.1.2 | Detection Event 단일 조회 |
| 6.1.7 | Detection Event의 Action Event 조회 |
| 6.2.2 | Malfunction Event 단일 조회 |
| 6.2.7 | Malfunction Event의 Action Event 조회 |
| 6.3.2 | Connection Event 단일 조회 |
| 6.4.3 | Action Event 단일 조회 |
| 7.2.1 | EventMapping 목록 조회 |
| 7.2.2 | EventMapping 상세 조회 |
| 7.2.6 | EventMapping 삭제 |
| 7.3.1-7.3.6 | EventMappingCamera API (전체) |
| 7.4.1-7.4.6 | EventMappingSpeaker API (전체) |

---

## 8. 체크리스트

### 수정 완료 시 체크 항목

- [ ] Phase 1: 긴급 항목 완료
  - [ ] 5.5.7 환경 데이터 업데이트
  - [ ] 5.5.8 히터/팬 제어
  - [ ] 8.3.3 서버 생성
  - [ ] 8.3.2 서버 상세 조회
  - [ ] 5.10.x FileGroup Error Format
  - [ ] 8.3.4-8.3.5 Server Error Format

- [ ] Phase 2: 고 우선순위 항목 완료
  - [ ] 목록 조회 API 422 Error 추가
  - [ ] 삭제 API 404 Error 추가

- [ ] Phase 3: 중 우선순위 항목 완료
  - [ ] POST API Request Example 추가
  - [ ] PATCH API Field Table + Request Example 추가
  - [ ] PUT API Field Table + Request Example 추가
  - [ ] DELETE API Request Example 추가
  - [ ] GET 목록 API Request Example 추가

---

## 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|-----|------|--------|----------|
| 1.0 | 2026-01-12 | AI Assistant | 초안 작성 |
