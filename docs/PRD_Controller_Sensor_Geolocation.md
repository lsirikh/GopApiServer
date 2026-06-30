# PRD: Controller/Sensor Geolocation 추가

**버전**: v1.0
**작성일**: 2026-01-08
**상태**: Draft

---

## 1. 개요

### 1.1 목적
Controller와 Sensor 장비에 위치 정보(geolocation)를 저장할 수 있도록 JSONB 필드를 추가한다.

### 1.2 배경
- 현재 Camera 모델에만 geolocation JSONB 필드가 존재
- Controller와 Sensor도 물리적 설치 위치 관리가 필요
- 기존 Geolocation 스키마 재사용으로 일관성 유지

### 1.3 범위
| 항목 | 포함 여부 |
|------|----------|
| Controller 모델/스키마/라우터 | O |
| Sensor 모델/스키마/라우터 | O |
| 데이터베이스 스키마 문서 | O |
| API 연동 설계 문서 | O |
| Swagger/ReDoc 자동 업데이트 | O |

---

## 2. 기능 요구사항

### 2.1 Geolocation 스키마 (기존 재사용)

```python
class Geolocation(BaseModel):
    location: Optional[str] = Field(None, max_length=500, description="설치 위치")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="위도")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="경도")
    altitude: Optional[float] = Field(None, description="고도 (미터)")
```

### 2.2 Controller Geolocation
- `controllers` 테이블에 `geolocation` JSONB 컬럼 추가
- Create/Update/Response 스키마에 geolocation 필드 추가
- API 엔드포인트에서 geolocation 처리

### 2.3 Sensor Geolocation
- `sensors` 테이블에 `geolocation` JSONB 컬럼 추가
- Create/Update/Response 스키마에 geolocation 필드 추가
- API 엔드포인트에서 geolocation 처리

---

## 3. 데이터베이스 스키마 변경

### 3.1 controllers 테이블

**변경 전:**
```sql
CREATE TABLE controllers (
    id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    ip_port INTEGER
);
```

**변경 후:**
```sql
CREATE TABLE controllers (
    id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    ip_port INTEGER,
    geolocation JSONB DEFAULT NULL  -- 신규 추가
);
```

### 3.2 sensors 테이블

**변경 전:**
```sql
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
    controller_id INTEGER REFERENCES controllers(id) ON DELETE SET NULL
);
```

**변경 후:**
```sql
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
    controller_id INTEGER REFERENCES controllers(id) ON DELETE SET NULL,
    geolocation JSONB DEFAULT NULL  -- 신규 추가
);
```

### 3.3 Geolocation JSONB 구조

```json
{
  "location": "GOP 3초소 정문",
  "latitude": 38.1234,
  "longitude": 127.5678,
  "altitude": 150.0
}
```

---

## 4. API 스키마 변경

### 4.1 Controller 스키마 변경

#### ControllerCreate
```python
class ControllerCreate(BaseModel):
    number_device: int
    group_device: Optional[int] = None
    name_device: str
    type_device: EnumDeviceType = EnumDeviceType.IoController
    version: Optional[str] = None
    status: EnumDeviceStatus = EnumDeviceStatus.ACTIVATED
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None
    geolocation: Optional[Geolocation] = None  # 신규 추가
```

#### ControllerUpdate
```python
class ControllerUpdate(BaseModel):
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    type_device: Optional[EnumDeviceType] = None
    version: Optional[str] = None
    status: Optional[EnumDeviceStatus] = None
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None
    geolocation: Optional[Geolocation] = None  # 신규 추가
```

#### ControllerResponse
```python
class ControllerResponse(BaseModel):
    id: int
    number_device: int
    group_device: Optional[int]
    name_device: str
    type_device: str
    version: Optional[str]
    status: EnumDeviceStatus
    ip_address: Optional[str]
    ip_port: Optional[int]
    geolocation: Optional[Geolocation] = None  # 신규 추가
    created_at: datetime
    updated_at: datetime
```

#### ControllerNestedResponse
```python
class ControllerNestedResponse(BaseModel):
    id: int
    number_device: int
    group_device: Optional[int]
    name_device: str
    type_device: str
    version: Optional[str]
    status: EnumDeviceStatus
    ip_address: Optional[str]
    ip_port: Optional[int]
    geolocation: Optional[Geolocation] = None  # 신규 추가
```

### 4.2 Sensor 스키마 변경

#### SensorCreate
```python
class SensorCreate(BaseModel):
    number_device: int
    group_device: Optional[int] = None
    name_device: str
    type_device: EnumDeviceType = EnumDeviceType.Sensor
    version: Optional[str] = None
    status: EnumDeviceStatus = EnumDeviceStatus.ACTIVATED
    controller_id: Optional[int] = None
    geolocation: Optional[Geolocation] = None  # 신규 추가
```

#### SensorUpdate
```python
class SensorUpdate(BaseModel):
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    type_device: Optional[EnumDeviceType] = None
    version: Optional[str] = None
    status: Optional[EnumDeviceStatus] = None
    controller_id: Optional[int] = None
    geolocation: Optional[Geolocation] = None  # 신규 추가
```

#### SensorResponse
```python
class SensorResponse(BaseModel):
    id: int
    number_device: int
    group_device: Optional[int]
    name_device: str
    type_device: str
    version: Optional[str]
    status: EnumDeviceStatus
    controller_id: Optional[int]
    controller: Optional[ControllerNestedResponse]
    geolocation: Optional[Geolocation] = None  # 신규 추가
    created_at: datetime
    updated_at: datetime
```

#### SensorNestedResponse
```python
class SensorNestedResponse(BaseModel):
    id: int
    number_device: int
    group_device: Optional[int]
    name_device: str
    type_device: str
    version: Optional[str]
    status: EnumDeviceStatus
    controller_id: Optional[int]
    geolocation: Optional[Geolocation] = None  # 신규 추가
```

---

## 5. API 엔드포인트 변경

### 5.1 Controller API

| Method | Endpoint | 변경 내용 |
|--------|----------|----------|
| POST | /api/devices/controllers | geolocation 필드 처리 추가 |
| PATCH | /api/devices/controllers/{id} | geolocation 필드 처리 추가 |
| PUT | /api/devices/controllers/{id} | geolocation 필드 처리 추가 |
| GET | /api/devices/controllers | geolocation 응답에 포함 |
| GET | /api/devices/controllers/{id} | geolocation 응답에 포함 |

### 5.2 Sensor API

| Method | Endpoint | 변경 내용 |
|--------|----------|----------|
| POST | /api/devices/sensors | geolocation 필드 처리 추가 |
| PATCH | /api/devices/sensors/{id} | geolocation 필드 처리 추가 |
| PUT | /api/devices/sensors/{id} | geolocation 필드 처리 추가 |
| GET | /api/devices/sensors | geolocation 응답에 포함 |
| GET | /api/devices/sensors/{id} | geolocation 응답에 포함 |

---

## 6. 구현 계획

### Phase 1: 모델 변경 (app/models/device.py)

#### ActionItem 1.1: Controller 모델에 geolocation 추가
- [ ] 테스트: Controller 모델에 geolocation 컬럼이 존재하는지 확인
- [ ] 구현: `geolocation = Column(JSON, nullable=True, default=None)` 추가

#### ActionItem 1.2: Sensor 모델에 geolocation 추가
- [ ] 테스트: Sensor 모델에 geolocation 컬럼이 존재하는지 확인
- [ ] 구현: `geolocation = Column(JSON, nullable=True, default=None)` 추가

### Phase 2: 스키마 변경 (app/schemas/device.py)

#### ActionItem 2.1: Controller 스키마 업데이트
- [ ] 테스트: ControllerCreate에 geolocation 필드 존재 확인
- [ ] 테스트: ControllerUpdate에 geolocation 필드 존재 확인
- [ ] 테스트: ControllerResponse에 geolocation 필드 존재 확인
- [ ] 테스트: ControllerNestedResponse에 geolocation 필드 존재 확인
- [ ] 구현: 4개 스키마에 geolocation 필드 추가

#### ActionItem 2.2: Sensor 스키마 업데이트
- [ ] 테스트: SensorCreate에 geolocation 필드 존재 확인
- [ ] 테스트: SensorUpdate에 geolocation 필드 존재 확인
- [ ] 테스트: SensorResponse에 geolocation 필드 존재 확인
- [ ] 테스트: SensorNestedResponse에 geolocation 필드 존재 확인
- [ ] 구현: 4개 스키마에 geolocation 필드 추가

### Phase 3: 라우터 변경

#### ActionItem 3.1: Controller 라우터 업데이트 (app/routers/controllers.py)
- [ ] 테스트: POST /api/devices/controllers geolocation 저장 확인
- [ ] 테스트: PATCH /api/devices/controllers/{id} geolocation 업데이트 확인
- [ ] 테스트: PUT /api/devices/controllers/{id} geolocation 교체 확인
- [ ] 테스트: GET /api/devices/controllers geolocation 응답 확인
- [ ] 테스트: GET /api/devices/controllers/{id} geolocation 응답 확인
- [ ] 구현: create/update 함수에 geolocation 처리 로직 추가
- [ ] 구현: _controller_to_response 함수에 geolocation 변환 추가

#### ActionItem 3.2: Sensor 라우터 업데이트 (app/routers/sensors.py)
- [ ] 테스트: POST /api/devices/sensors geolocation 저장 확인
- [ ] 테스트: PATCH /api/devices/sensors/{id} geolocation 업데이트 확인
- [ ] 테스트: PUT /api/devices/sensors/{id} geolocation 교체 확인
- [ ] 테스트: GET /api/devices/sensors geolocation 응답 확인
- [ ] 테스트: GET /api/devices/sensors/{id} geolocation 응답 확인
- [ ] 구현: create/update 함수에 geolocation 처리 로직 추가
- [ ] 구현: _sensor_to_response 함수에 geolocation 변환 추가

### Phase 4: 문서 업데이트

#### ActionItem 4.1: GOP_스키마_전체.md 업데이트
- [ ] Section 2.2 controllers 테이블에 geolocation 컬럼 추가
- [ ] Section 2.3 sensors 테이블에 geolocation 컬럼 추가
- [ ] 변경 이력 업데이트

#### ActionItem 4.2: GOP_Restful_Api_연동설계.md 업데이트
- [ ] Section 5.1 Controller API 스키마에 geolocation 추가
- [ ] Section 5.2 Sensor API 스키마에 geolocation 추가
- [ ] 예제 JSON 업데이트

### Phase 5: Swagger/ReDoc 검증

#### ActionItem 5.1: API 문서 자동 생성 검증
- [ ] localhost:8000/docs (Swagger UI) 확인
- [ ] localhost:8000/redoc (ReDoc) 확인
- [ ] Controller/Sensor 스키마에 geolocation 필드 표시 확인

---

## 7. 테스트 파일

| 파일명 | 테스트 범위 |
|--------|------------|
| tests/test_controller_geolocation.py | Controller geolocation 모델/스키마/API 테스트 |
| tests/test_sensor_geolocation.py | Sensor geolocation 모델/스키마/API 테스트 |

---

## 8. 예상 API 사용 예시

### 8.1 Controller 생성 (with geolocation)

**Request:**
```http
POST /api/devices/controllers
Content-Type: application/json

{
  "number_device": 1,
  "name_device": "GOP 3초소 컨트롤러",
  "ip_address": "192.168.1.100",
  "ip_port": 8080,
  "geolocation": {
    "location": "GOP 3초소 정문",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 150.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Controller created successfully",
  "data": {
    "id": 1,
    "number_device": 1,
    "name_device": "GOP 3초소 컨트롤러",
    "type_device": "IoController",
    "status": "ACTIVATED",
    "ip_address": "192.168.1.100",
    "ip_port": 8080,
    "geolocation": {
      "location": "GOP 3초소 정문",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 150.0
    },
    "created_at": "2026-01-08T10:00:00",
    "updated_at": "2026-01-08T10:00:00"
  }
}
```

### 8.2 Sensor 생성 (with geolocation)

**Request:**
```http
POST /api/devices/sensors
Content-Type: application/json

{
  "number_device": 101,
  "name_device": "3초소 진동 센서",
  "controller_id": 1,
  "geolocation": {
    "location": "GOP 3초소 철책 구간 A",
    "latitude": 38.1235,
    "longitude": 127.5680,
    "altitude": 148.5
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sensor created successfully",
  "data": {
    "id": 101,
    "number_device": 101,
    "name_device": "3초소 진동 센서",
    "type_device": "Sensor",
    "status": "ACTIVATED",
    "controller_id": 1,
    "controller": {
      "id": 1,
      "name_device": "GOP 3초소 컨트롤러",
      "geolocation": {
        "location": "GOP 3초소 정문",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 150.0
      }
    },
    "geolocation": {
      "location": "GOP 3초소 철책 구간 A",
      "latitude": 38.1235,
      "longitude": 127.5680,
      "altitude": 148.5
    },
    "created_at": "2026-01-08T10:05:00",
    "updated_at": "2026-01-08T10:05:00"
  }
}
```

---

## 9. 기존 데이터 호환성

### 9.1 마이그레이션 전략
- geolocation 컬럼은 `nullable=True, default=None`으로 설정
- 기존 데이터는 geolocation이 null로 유지
- 신규 생성/업데이트 시에만 geolocation 설정

### 9.2 하위 호환성
- 기존 API 요청은 geolocation 없이 계속 동작
- geolocation 미포함 요청 시 null로 저장

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| v1.0 | 2026-01-08 | 초안 작성 | Claude |

---

## 11. 참고 문서

- [GOP_스키마_전체.md](GOP_스키마_전체.md) - 데이터베이스 스키마 정의
- [GOP_Restful_Api_연동설계.md](GOP_Restful_Api_연동설계.md) - API 연동 설계
- [PRD_Enclosure_Device.md](PRD_Enclosure_Device.md) - Enclosure geolocation 구현 참고
