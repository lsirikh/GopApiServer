# PRD: 함체관리장비 (Enclosure Device)

**버전**: v1.1
**작성일**: 2026-01-08
**상태**: Draft

---

## 1. 개요

### 1.1 목적
GOP(일반전초) 경계시스템의 옥외 함체(Enclosure)를 관리하기 위한 디바이스 타입 추가. 함체 내부의 환경 상태(온도, 습도), 전원 상태(전류, 전압), 물리적 상태(진동, 도어 상태)를 모니터링하고 제어한다.

### 1.2 배경
- GOP 경계시스템은 옥외에 설치된 다수의 장비함체를 운용
- 함체 내부 환경(온도, 습도) 모니터링 및 히터/팬 자동 제어 필요
- 전원 상태 감시 및 UPS 연동 필요
- 함체 도어 개폐 상태 및 진동 감지 필요
- NMS(통합관제시스템) 연동을 통한 원격 모니터링 필요

### 1.3 범위
- Enclosure 모델 및 스키마 정의
- Enclosure CRUD API 구현
- Device 다형성 상속 구조 적용
- 환경 모니터링 데이터 JSONB 저장

---

## 2. 요구사항 분석

### 2.1 하드웨어 요구사항 (GOP 기준)

| 항목 | 요구사항 |
|------|----------|
| 함체 구조 | 19인치 랙 마운트, 내후성 스틸/알루미늄 |
| 도어 잠금 | 전자식 잠금장치, 개폐 센서 |
| 환경 보호 | IP65 이상, -30°C ~ +50°C 동작 |
| 전원 | AC 220V, UPS 연동, 과전류 차단기 |
| 발열 관리 | 히터(동절기), 팬(하절기) 자동 제어 |
| 진동 감지 | 외부 충격/진동 감지 센서 |

### 2.2 소프트웨어 요구사항

#### 2.2.1 모니터링 항목
- **온도**: 함체 내부 온도 (°C)
- **습도**: 함체 내부 습도 (%)
- **전류**: 입력 전류 (A)
- **전압**: 입력 전압 (V)
- **진동**: 진동 감지 레벨 (0-100)
- **UPS 상태**: 배터리 잔량, 충전 상태

#### 2.2.2 제어 항목
- **도어 상태**: CLOSED(닫힘), OPEN(열림) - 센서로 물리적 상태 감지
- **장비 상태**: Device.status (EnumDeviceStatus) - ACTIVATED/DEACTIVATED/ERROR
- **히터 제어**: ON/OFF (온도 기반 자동)
- **팬 제어**: ON/OFF (온도 기반 자동)

#### 2.2.3 알람 조건
- 온도 임계값 초과/미달
- 습도 임계값 초과
- 과전류/저전압 감지
- 진동 임계값 초과 (침입/파손 의심)
- 비정상 도어 개방 (status=ACTIVATED 상태에서 door_status=OPEN)

---

## 3. 데이터 모델

### 3.1 Enum 정의

#### 3.1.1 EnumDoorStatus (신규)
```python
class EnumDoorStatus(str, Enum):
    """함체 도어 물리적 상태 (센서 감지)"""
    CLOSED = "CLOSED"      # 도어 닫힘
    OPEN = "OPEN"          # 도어 열림
```

#### 3.1.2 EnumDeviceStatus (기존 - Device 상속)
```python
class EnumDeviceStatus(str, Enum):
    """장비 운영 상태 (Device에서 상속)"""
    ACTIVATED = "ACTIVATED"        # 활성화 (정상 운영)
    DEACTIVATED = "DEACTIVATED"    # 비활성화 (점검/유지보수 모드)
    ERROR = "ERROR"                # 오류 상태
```

**운영 로직:**
- `status=ACTIVATED` + `door_status=OPEN` → 비정상 개방 알람 발생
- `status=DEACTIVATED` + `door_status=OPEN` → 점검 중이므로 알람 무시
- `status=ERROR` → 함체 이상 상태 (통신 불가 등)

#### 3.1.3 EnumDeviceCategory 확장
```python
class EnumDeviceCategory(str, Enum):
    # 기존 값들...
    CONTROLLER = "CONTROLLER"
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"
    SPEAKER = "SPEAKER"
    ENCLOSURE = "ENCLOSURE"  # 신규 추가
```

### 3.2 테이블 스키마

#### 3.2.1 enclosures 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INTEGER | PK, FK(devices.id) CASCADE | Device FK |
| door_status | ENUM(EnumDoorStatus) | NOT NULL, DEFAULT 'CLOSED' | 도어 물리적 상태 |
| detail_info | JSONB | NULLABLE | 환경 모니터링 데이터 |
| geolocation | JSONB | NULLABLE | 위치 정보 |
| threshold_config | JSONB | NULLABLE | 알람 임계값 설정 |
| heater_enabled | BOOLEAN | DEFAULT FALSE | 히터 활성화 |
| fan_enabled | BOOLEAN | DEFAULT FALSE | 팬 활성화 |

**Note:** `status` 필드는 Device 부모 테이블에서 상속 (EnumDeviceStatus)

### 3.3 JSONB 스키마

#### 3.3.1 detail_info (환경 모니터링)
```json
{
  "temperature": 25.5,        // 온도 (°C)
  "humidity": 45.0,           // 습도 (%)
  "current": 2.5,             // 전류 (A)
  "voltage": 220.0,           // 전압 (V)
  "vibration": 5,             // 진동 레벨 (0-100)
  "ups_battery_level": 100,   // UPS 배터리 (%)
  "ups_charging": true,       // UPS 충전 중 여부
  "last_updated": "2026-01-08T10:30:00Z"
}
```

#### 3.3.2 geolocation (위치 정보)
```json
{
  "location": "GOP 3초소 함체 A",
  "latitude": 38.1234,
  "longitude": 127.5678,
  "altitude": 150.0
}
```

#### 3.3.3 threshold_config (알람 임계값)
```json
{
  "temp_high": 40.0,          // 고온 경보 (°C)
  "temp_low": -10.0,          // 저온 경보 (°C)
  "humidity_high": 80.0,      // 고습도 경보 (%)
  "current_high": 10.0,       // 과전류 경보 (A)
  "voltage_low": 200.0,       // 저전압 경보 (V)
  "vibration_high": 70        // 진동 경보 레벨
}
```

---

## 4. 모델 구현

### 4.1 SQLAlchemy 모델 (app/models/device.py)

```python
class Enclosure(Device):
    """
    함체관리장비 모델

    PRD: PRD_Enclosure_Device.md v1.1
    Device 다형성 상속 (Joined Table Inheritance)

    - status: Device에서 상속 (EnumDeviceStatus: ACTIVATED/DEACTIVATED/ERROR)
    - door_status: 도어 물리적 상태 (EnumDoorStatus: CLOSED/OPEN)
    """
    __tablename__ = "enclosures"

    id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True
    )
    door_status = Column(
        SQLEnum(EnumDoorStatus),
        nullable=False,
        default=EnumDoorStatus.CLOSED,
        comment="도어 물리적 상태 (CLOSED/OPEN) - 센서 감지"
    )
    detail_info = Column(
        JSON,
        nullable=True,
        default=None,
        comment="환경 모니터링 데이터 (temperature, humidity, current, voltage, vibration)"
    )
    geolocation = Column(
        JSON,
        nullable=True,
        default=None,
        comment="위치 정보 (location, latitude, longitude, altitude)"
    )
    threshold_config = Column(
        JSON,
        nullable=True,
        default=None,
        comment="알람 임계값 설정"
    )
    heater_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="히터 활성화 상태"
    )
    fan_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="팬 활성화 상태"
    )

    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.ENCLOSURE
    }
```

### 4.2 Pydantic 스키마 (app/schemas/enclosure.py)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.utils.enums import EnumDoorStatus, EnumDeviceStatus
from app.schemas.device import Geolocation

class EnclosureDetailInfo(BaseModel):
    """함체 환경 모니터링 데이터"""
    model_config = ConfigDict(from_attributes=True)

    temperature: Optional[float] = Field(None, description="온도 (°C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="습도 (%)")
    current: Optional[float] = Field(None, ge=0, description="전류 (A)")
    voltage: Optional[float] = Field(None, ge=0, description="전압 (V)")
    vibration: Optional[int] = Field(None, ge=0, le=100, description="진동 레벨")
    ups_battery_level: Optional[int] = Field(None, ge=0, le=100, description="UPS 배터리 (%)")
    ups_charging: Optional[bool] = Field(None, description="UPS 충전 중")
    last_updated: Optional[datetime] = Field(None, description="마지막 업데이트 시각")

class EnclosureThresholdConfig(BaseModel):
    """함체 알람 임계값 설정"""
    model_config = ConfigDict(from_attributes=True)

    temp_high: Optional[float] = Field(40.0, description="고온 경보 (°C)")
    temp_low: Optional[float] = Field(-10.0, description="저온 경보 (°C)")
    humidity_high: Optional[float] = Field(80.0, description="고습도 경보 (%)")
    current_high: Optional[float] = Field(10.0, description="과전류 경보 (A)")
    voltage_low: Optional[float] = Field(200.0, description="저전압 경보 (V)")
    vibration_high: Optional[int] = Field(70, description="진동 경보 레벨")

class EnclosureCreate(BaseModel):
    """함체 생성 스키마"""
    model_config = ConfigDict(from_attributes=True)

    # Device 기본 필드
    number_device: int = Field(..., description="장비 번호")
    name_device: str = Field(..., max_length=200, description="장비 이름")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP 주소")
    description: Optional[str] = Field(None, description="설명")
    status: EnumDeviceStatus = Field(EnumDeviceStatus.ACTIVATED, description="장비 상태")

    # Enclosure 전용 필드
    door_status: EnumDoorStatus = Field(
        EnumDoorStatus.CLOSED,
        description="도어 물리적 상태 (센서 감지)"
    )
    detail_info: Optional[EnclosureDetailInfo] = Field(None, description="환경 모니터링 데이터")
    geolocation: Optional[Geolocation] = Field(None, description="위치 정보")
    threshold_config: Optional[EnclosureThresholdConfig] = Field(None, description="알람 임계값")
    heater_enabled: bool = Field(False, description="히터 활성화")
    fan_enabled: bool = Field(False, description="팬 활성화")

class EnclosureUpdate(BaseModel):
    """함체 수정 스키마 (PATCH)"""
    model_config = ConfigDict(from_attributes=True)

    name_device: Optional[str] = Field(None, max_length=200)
    ip_address: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    status: Optional[EnumDeviceStatus] = None
    door_status: Optional[EnumDoorStatus] = None
    detail_info: Optional[EnclosureDetailInfo] = None
    geolocation: Optional[Geolocation] = None
    threshold_config: Optional[EnclosureThresholdConfig] = None
    heater_enabled: Optional[bool] = None
    fan_enabled: Optional[bool] = None

class EnclosureResponse(BaseModel):
    """함체 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    number_device: int
    name_device: str
    type_device: str  # "ENCLOSURE"
    ip_address: Optional[str]
    description: Optional[str]
    status: EnumDeviceStatus  # Device에서 상속 (ACTIVATED/DEACTIVATED/ERROR)
    door_status: EnumDoorStatus  # 도어 물리적 상태 (CLOSED/OPEN)
    detail_info: Optional[EnclosureDetailInfo]
    geolocation: Optional[Geolocation]
    threshold_config: Optional[EnclosureThresholdConfig]
    heater_enabled: bool
    fan_enabled: bool
    created_at: datetime
    updated_at: datetime
```

---

## 5. API 설계

### 5.1 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/devices/enclosures | 함체 목록 조회 |
| GET | /api/devices/enclosures/{id} | 함체 단건 조회 |
| POST | /api/devices/enclosures | 함체 생성 |
| PATCH | /api/devices/enclosures/{id} | 함체 부분 수정 |
| PUT | /api/devices/enclosures/{id} | 함체 전체 수정 |
| DELETE | /api/devices/enclosures/{id} | 함체 삭제 |
| PATCH | /api/devices/enclosures/{id}/status | 환경 데이터 업데이트 |
| POST | /api/devices/enclosures/{id}/control | 히터/팬 제어 |

### 5.2 Query Parameters (GET 목록)

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| page | int | 페이지 번호 (기본: 1) |
| limit | int | 페이지당 항목 수 (기본: 20) |
| door_status | EnumDoorStatus | 도어 상태 필터 (CLOSED/OPEN) |
| status | EnumDeviceStatus | 장비 상태 필터 (ACTIVATED/DEACTIVATED/ERROR) |
| name_device | str | 장비명 검색 |

### 5.3 요청/응답 예시

#### 5.3.1 POST /api/devices/enclosures
**Request:**
```json
{
  "number_device": 101,
  "name_device": "GOP 3초소 함체 A",
  "ip_address": "192.168.1.101",
  "description": "3초소 메인 통신함체",
  "status": "ACTIVATED",
  "door_status": "CLOSED",
  "geolocation": {
    "location": "GOP 3초소",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 150.0
  },
  "threshold_config": {
    "temp_high": 45.0,
    "temp_low": -20.0,
    "humidity_high": 85.0
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Enclosure created successfully",
  "data": {
    "id": 1,
    "number_device": 101,
    "name_device": "GOP 3초소 함체 A",
    "type_device": "ENCLOSURE",
    "ip_address": "192.168.1.101",
    "description": "3초소 메인 통신함체",
    "status": "ACTIVATED",
    "door_status": "CLOSED",
    "detail_info": null,
    "geolocation": {
      "location": "GOP 3초소",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 150.0
    },
    "threshold_config": {
      "temp_high": 45.0,
      "temp_low": -20.0,
      "humidity_high": 85.0,
      "current_high": 10.0,
      "voltage_low": 200.0,
      "vibration_high": 70
    },
    "heater_enabled": false,
    "fan_enabled": false,
    "created_at": "2026-01-08T10:00:00Z",
    "updated_at": "2026-01-08T10:00:00Z"
  }
}
```

#### 5.3.2 PATCH /api/devices/enclosures/{id}/status
**Request (환경 데이터 업데이트):**
```json
{
  "detail_info": {
    "temperature": 28.5,
    "humidity": 55.0,
    "current": 3.2,
    "voltage": 218.5,
    "vibration": 2,
    "ups_battery_level": 95,
    "ups_charging": false,
    "last_updated": "2026-01-08T10:30:00Z"
  }
}
```

#### 5.3.3 POST /api/devices/enclosures/{id}/control
**Request (히터/팬 제어):**
```json
{
  "heater_enabled": true,
  "fan_enabled": false
}
```

---

## 6. 구현 계획 (TDD)

### Phase 1: Enum 정의
- [ ] 테스트: EnumDoorStatus 존재 확인
- [ ] 구현: EnumDoorStatus 추가 (app/utils/enums.py)
- [ ] 테스트: EnumDeviceCategory.ENCLOSURE 존재 확인
- [ ] 구현: EnumDeviceCategory 확장

### Phase 2: 모델 정의
- [ ] 테스트: Enclosure 모델 존재 및 Device 상속 확인
- [ ] 구현: Enclosure 모델 (app/models/device.py)
- [ ] 테스트: Enclosure 테이블 컬럼 검증
- [ ] 구현: 마이그레이션 생성 및 적용

### Phase 3: 스키마 정의
- [ ] 테스트: EnclosureDetailInfo 스키마 필드 검증
- [ ] 테스트: EnclosureCreate/Update/Response 스키마 검증
- [ ] 구현: Enclosure 스키마 (app/schemas/enclosure.py)

### Phase 4: 라우터 구현
- [ ] 테스트: GET /api/devices/enclosures 목록 조회
- [ ] 테스트: GET /api/devices/enclosures/{id} 단건 조회
- [ ] 테스트: POST /api/devices/enclosures 생성
- [ ] 테스트: PATCH /api/devices/enclosures/{id} 부분 수정
- [ ] 테스트: PUT /api/devices/enclosures/{id} 전체 수정
- [ ] 테스트: DELETE /api/devices/enclosures/{id} 삭제
- [ ] 구현: enclosures 라우터 (app/routers/enclosures.py)

### Phase 5: 특수 기능
- [ ] 테스트: 환경 데이터 업데이트 API
- [ ] 테스트: 히터/팬 제어 API
- [ ] 구현: 특수 엔드포인트 추가

### Phase 6: 문서 업데이트
- [ ] GOP_Restful_Api_연동설계.md 업데이트
- [ ] GOP_스키마_전체.md 업데이트

---

## 7. 연관 문서

- GOP_Restful_Api_연동설계.md - Section 5: 디바이스 스키마
- GOP_스키마_전체.md - Section 4: devices 테이블
- app/models/device.py - Device 다형성 상속 구조
- app/schemas/device.py - Geolocation 스키마 참조

---

## 8. 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| v1.0 | 2026-01-08 | 최초 작성 | Claude |
| v1.1 | 2026-01-08 | EnumEnclosureOperationMode → EnumDoorStatus + Device.status 분리 | Claude |
