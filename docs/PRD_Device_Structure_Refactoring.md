# PRD: Device 구조 리팩토링

**문서 버전**: v1.0
**작성일**: 2025-12-30
**상태**: Draft

---

## 1. 개요

### 1.1 배경
현재 GOP API 서버의 Device 관련 모델(Controller, Sensor, Camera)은 각각 독립된 테이블로 구성되어 있으며, 공통 필드가 중복 정의되어 있다. 또한 `group_device` 필드가 단순 정수값으로 관리되어 그룹에 대한 메타데이터 관리가 불가능하다.

### 1.2 목적
- Device 모델을 상속 구조로 리팩토링하여 공통 필드 중복 제거
- DeviceGroup 테이블을 신규 생성하여 그룹 관리 기능 추가
- Camera 모델에 하드웨어 스펙, 좌표 정보 등 신규 필드 추가
- 타입 안전성 확보 및 확장성 향상

### 1.3 범위
- Device Base 모델 및 상속 구조 설계
- DeviceGroup 모델 신규 생성
- Camera 모델 필드 확장
- 관련 API 엔드포인트 수정
- 기존 데이터 마이그레이션

---

## 2. 현재 상태 분석

### 2.1 현재 테이블 구조

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   controllers   │  │     sensors     │  │     cameras     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id              │  │ id              │  │ id              │
│ number_device   │  │ number_device   │  │ number_device   │
│ group_device    │  │ group_device    │  │ group_device    │
│ name_device     │  │ name_device     │  │ name_device     │
│ type_device     │  │ type_device     │  │ type_device     │
│ version         │  │ version         │  │ version         │
│ status          │  │ status          │  │ status          │
│ ip_address      │  │ controller_id   │  │ ip_address      │
│ ip_port         │  │ created_at      │  │ ip_port         │
│ created_at      │  │ updated_at      │  │ user_name       │
│ updated_at      │  │                 │  │ user_password   │
│                 │  │                 │  │ rtsp_uri        │
│                 │  │                 │  │ rtsp_port       │
│                 │  │                 │  │ mode            │
│                 │  │                 │  │ category        │
│                 │  │                 │  │ created_at      │
│                 │  │                 │  │ updated_at      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 현재 문제점

| 문제 | 설명 | 영향도 |
|------|------|--------|
| **필드 중복** | 7개 공통 필드가 3개 테이블에 중복 정의 | 유지보수 어려움 |
| **그룹 관리 불가** | `group_device`가 단순 int, 메타데이터 없음 | 기능 제한 |
| **타입 혼재 위험** | 그룹 내 디바이스 타입 제약 없음 | 데이터 무결성 |
| **확장성 부족** | 새 디바이스 타입 추가 시 전체 구조 복제 필요 | 개발 비용 |
| **Camera 필드 부족** | 하드웨어 스펙, 좌표 정보 등 미지원 | 요구사항 미충족 |

---

## 3. 목표 상태 설계

### 3.1 목표 테이블 구조

**N:N 관계 (Junction Table 방식)**

하나의 디바이스가 여러 그룹에 소속될 수 있고, 하나의 그룹이 여러 디바이스를 포함할 수 있다.

```
┌─────────────────────────────────────────────────────────────┐
│                       device_groups                          │
├─────────────────────────────────────────────────────────────┤
│ id              : Integer, PK, Auto Increment                │
│ name            : String(200), NOT NULL, UNIQUE              │
│ description     : String(500), NULL                          │
│ created_at      : DateTime, NOT NULL                         │
│ updated_at      : DateTime, NOT NULL                         │
└─────────────────────────────────────────────────────────────┘
          │
          │ N:N (via Junction Table)
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   device_group_mappings                      │
│                      (Junction Table)                        │
├─────────────────────────────────────────────────────────────┤
│ id              : Integer, PK, Auto Increment                │
│ device_id       : Integer, FK → devices.id, NOT NULL         │
│ group_id        : Integer, FK → device_groups.id, NOT NULL   │
│ created_at      : DateTime, NOT NULL                         │
├─────────────────────────────────────────────────────────────┤
│ Constraints:                                                 │
│   - UNIQUE(device_id, group_id) : 중복 할당 방지             │
│   - ON DELETE CASCADE : 그룹/디바이스 삭제 시 매핑도 삭제    │
└─────────────────────────────────────────────────────────────┘
          │
          │ N:N (via Junction Table)
          ▼
┌─────────────────────────────────────────────────────────────┐
│                         devices                              │
│                    (Base Table - Polymorphic)                │
├─────────────────────────────────────────────────────────────┤
│ id              : Integer, PK, Auto Increment                │
│ device_type     : String(50), NOT NULL (Discriminator)       │
│ number_device   : Integer, NOT NULL, UNIQUE                  │
│ name_device     : String(200), NOT NULL                      │
│ group_device    : Integer, NOT NULL (Deprecated, 호환성 유지) │
│ type_device     : Enum(EnumDeviceType), NOT NULL             │
│ version         : String(50), NOT NULL                       │
│ status          : Enum(EnumDeviceStatus), NOT NULL           │
│ created_at      : DateTime, NOT NULL                         │
│ updated_at      : DateTime, NOT NULL                         │
├─────────────────────────────────────────────────────────────┤
│ Discriminator Values:                                        │
│   - "controller" → Controller                                │
│   - "sensor"     → Sensor                                    │
│   - "camera"     → Camera                                    │
│                                                              │
│ Note: group_id FK 제거됨 → Junction Table로 관리             │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   controllers   │  │     sensors     │  │     cameras     │
│   (Inherited)   │  │   (Inherited)   │  │   (Inherited)   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id (FK→devices) │  │ id (FK→devices) │  │ id (FK→devices) │
│ ip_address      │  │ controller_id   │  │ ip_address      │
│ ip_port         │  │                 │  │ ip_port         │
│                 │  │                 │  │ user_name       │
│                 │  │                 │  │ user_password   │
│                 │  │                 │  │ rtsp_uri        │
│                 │  │                 │  │ rtsp_port       │
│                 │  │                 │  │ mode            │
│                 │  │                 │  │ category        │
│                 │  │                 │  │ is_record       │
│                 │  │                 │  │ hardware_spec   │ ← JSON (HardwareSpec)
│                 │  │                 │  │ geolocation     │ ← JSON (Geolocation)
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 3.1.1 N:N 관계의 장점

| 장점 | 설명 |
|------|------|
| **다중 그룹 소속** | 디바이스가 여러 그룹에 동시 소속 가능 (예: "GOP 1구역" + "야간 감시") |
| **Device 스키마 단순화** | Device 테이블에 group_id FK 불필요, 관심사 분리 |
| **유연한 그룹 관리** | 그룹 할당/해제가 Device 수정 없이 가능 |
| **하위 호환성** | `group_device` 필드는 기존 호환성 유지용으로 유지 |

### 3.1.2 Junction Table 설계

```python
class DeviceGroupMapping(Base):
    """Device-Group N:N 매핑 테이블"""
    __tablename__ = "device_group_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("device_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)

    # Unique constraint: 동일 디바이스-그룹 조합 중복 방지
    __table_args__ = (
        UniqueConstraint('device_id', 'group_id', name='uq_device_group'),
    )

    # Relationships
    device = relationship("Device", back_populates="group_mappings")
    group = relationship("DeviceGroup", back_populates="device_mappings")
```

### 3.2 Camera 신규 필드 상세

#### 3.2.1 Composite Type 설계

Camera 모델의 확장 필드는 **Composite Type (복합 타입)**으로 구성하여 관심사를 분리한다.

```
┌─────────────────────────────────────────────────────────────┐
│                         Camera                               │
├─────────────────────────────────────────────────────────────┤
│ ... (기존 필드들)                                            │
│                                                              │
│ hardware_spec  : HardwareSpec (Embedded/Composite Type)     │
│ geolocation    : Geolocation (Embedded/Composite Type)      │
│ is_record      : Boolean                                     │
└─────────────────────────────────────────────────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│     HardwareSpec        │  │      Geolocation        │
├─────────────────────────┤  ├─────────────────────────┤
│ name          : String  │  │ latitude   : Float      │
│ location      : String  │  │ longitude  : Float      │
│ manufacturer  : String  │  │ altitude   : Float      │
│ model         : String  │  └─────────────────────────┘
│ hardware      : String  │
│ firmware      : String  │
│ device_id     : String  │
│ mac_address   : String  │
│ onvif_version : String  │
└─────────────────────────┘
```

#### 3.2.2 HardwareSpec 클래스

```python
class HardwareSpec(BaseModel):
    """카메라 하드웨어 스펙 정보"""
    name: Optional[str] = Field(None, max_length=200, description="하드웨어 이름")
    location: Optional[str] = Field(None, max_length=500, description="설치 위치")
    manufacturer: Optional[str] = Field(None, max_length=200, description="제조사")
    model: Optional[str] = Field(None, max_length=200, description="모델명")
    hardware: Optional[str] = Field(None, max_length=200, description="하드웨어 정보")
    firmware: Optional[str] = Field(None, max_length=100, description="펌웨어 버전")
    device_id: Optional[str] = Field(None, max_length=200, description="장치 ID")
    mac_address: Optional[str] = Field(None, max_length=17, description="MAC 주소 (XX:XX:XX:XX:XX:XX)")
    onvif_version: Optional[str] = Field(None, max_length=50, description="ONVIF 버전")
```

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `name` | String(200) | N | 하드웨어 이름 |
| `location` | String(500) | N | 설치 위치 |
| `manufacturer` | String(200) | N | 제조사 |
| `model` | String(200) | N | 모델명 |
| `hardware` | String(200) | N | 하드웨어 정보 |
| `firmware` | String(100) | N | 펌웨어 버전 |
| `device_id` | String(200) | N | 장치 ID |
| `mac_address` | String(17) | N | MAC 주소 (XX:XX:XX:XX:XX:XX) |
| `onvif_version` | String(50) | N | ONVIF 버전 |

#### 3.2.3 Geolocation 클래스

```python
class Geolocation(BaseModel):
    """좌표 정보"""
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="위도")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="경도")
    altitude: Optional[float] = Field(None, description="고도 (미터)")
```

| 필드명 | 타입 | 필수 | 설명 | 범위 |
|--------|------|------|------|------|
| `latitude` | Float | N | 위도 | -90.0 ~ 90.0 |
| `longitude` | Float | N | 경도 | -180.0 ~ 180.0 |
| `altitude` | Float | N | 고도 (미터) | - |

#### 3.2.4 녹화 설정

| 필드명 | 타입 | 필수 | 기본값 | 설명 |
|--------|------|------|--------|------|
| `is_record` | Boolean | N | False | 녹화 여부 |

#### 3.2.5 SQLAlchemy 구현 방식

SQLite는 JSON 타입을 지원하므로, Composite Type을 JSON 컬럼으로 저장한다.

```python
from sqlalchemy import Column, JSON

class Camera(Device):
    __tablename__ = "cameras"

    # ... 기존 필드들

    # Composite Types as JSON
    hardware_spec = Column(JSON, nullable=True, default=None)
    geolocation = Column(JSON, nullable=True, default=None)
    is_record = Column(Boolean, nullable=False, default=False)
```

**장점**:
- 관심사 분리로 코드 가독성 향상
- 개별 타입에 대한 검증 로직 캡슐화
- 향후 필드 추가/변경 시 유연성 확보
- API 응답에서 구조화된 데이터 제공

### 3.3 Enum 변경 사항

#### 3.3.1 EnumCameraMode (변경 없음)
```python
class EnumCameraMode(str, Enum):
    NONE = "NONE"
    ONVIF = "ONVIF"
    EMSTONE_API = "EMSTONE_API"
    INNODEP_API = "INNODEP_API"
    ETC = "ETC"
```

#### 3.3.2 EnumCameraType (변경 없음)
```python
class EnumCameraType(str, Enum):
    NONE = "NONE"
    FIXED = "FIXED"
    PTZ = "PTZ"
```

#### 3.3.3 EnumDeviceStatus (변경 없음)
```python
class EnumDeviceStatus(str, Enum):
    ACTIVATED = "ACTIVATED"
    ERROR = "ERROR"
    DEACTIVATED = "DEACTIVATED"
```

---

## 4. API 변경 사항

### 4.1 신규 API: DeviceGroup

#### 4.1.1 엔드포인트 요약

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/api/devices/groups` | 디바이스 그룹 목록 조회 | Optional |
| GET | `/api/devices/groups/{group_id}` | 디바이스 그룹 단건 조회 | Optional |
| POST | `/api/devices/groups` | 디바이스 그룹 생성 | Optional |
| PATCH | `/api/devices/groups/{group_id}` | 디바이스 그룹 부분 수정 | Optional |
| PUT | `/api/devices/groups/{group_id}` | 디바이스 그룹 전체 수정 | Optional |
| DELETE | `/api/devices/groups/{group_id}` | 디바이스 그룹 삭제 | Optional |
| POST | `/api/devices/groups/{group_id}/devices` | 그룹에 디바이스 할당 | Optional |
| DELETE | `/api/devices/groups/{group_id}/devices/{device_id}` | 그룹에서 디바이스 제거 | Optional |

---

#### 4.1.2 GET `/api/devices/groups` - 목록 조회

디바이스 그룹 목록을 페이지네이션하여 조회합니다.

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `page` | Integer | N | 1 | 페이지 번호 (1부터 시작) |
| `limit` | Integer | N | 20 | 페이지당 항목 수 (최대 100) |
| `name` | String | N | - | 그룹명으로 필터링 (부분 일치) |
| `include_devices` | Boolean | N | false | 디바이스 목록 포함 여부 |
| `include_count` | Boolean | N | true | 디바이스 수 포함 여부 |

**Response (200 OK)**
```json
{
  "success": true,
  "message": "Device groups retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "GOP 1구역",
      "description": "1구역 전방 감시 장비 그룹",
      "device_count": 15,
      "created_at": "2025-12-30T10:00:00",
      "updated_at": "2025-12-30T10:00:00"
    },
    {
      "id": 2,
      "name": "GOP 2구역",
      "description": "2구역 후방 감시 장비 그룹",
      "device_count": 8,
      "created_at": "2025-12-30T11:00:00",
      "updated_at": "2025-12-30T11:00:00"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_pages": 1,
    "total_items": 2
  }
}
```

**Response with `include_devices=true` (200 OK)**

> **Note**: N:N 관계이므로 각 디바이스는 `device_groups` 배열을 가지며, 현재 그룹 외 다른 그룹에도 소속될 수 있음

```json
{
  "success": true,
  "message": "Device groups retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "GOP 1구역",
      "description": "1구역 전방 감시 장비 그룹",
      "device_count": 3,
      "device_summary": {
        "controllers": 1,
        "sensors": 1,
        "cameras": 1
      },
      "devices": [
        {
          "id": 1,
          "device_type": "controller",
          "number_device": 101,
          "group_device": 1,
          "device_groups": [
            {"id": 1, "name": "GOP 1구역"}
          ],
          "name_device": "CTL-001",
          "type_device": "Controller",
          "version": "1.0.0",
          "status": "ACTIVATED",
          "ip_address": "192.168.1.10",
          "ip_port": 8080,
          "created_at": "2025-12-30T10:00:00",
          "updated_at": "2025-12-30T10:00:00"
        },
        {
          "id": 2,
          "device_type": "sensor",
          "number_device": 201,
          "group_device": 1,
          "device_groups": [
            {"id": 1, "name": "GOP 1구역"},
            {"id": 3, "name": "야간 감시"}
          ],
          "name_device": "SNS-001",
          "type_device": "Fence",
          "version": "2.1.0",
          "status": "ACTIVATED",
          "controller_id": 1,
          "created_at": "2025-12-30T10:00:00",
          "updated_at": "2025-12-30T10:00:00"
        },
        {
          "id": 3,
          "device_type": "camera",
          "number_device": 301,
          "group_device": 1,
          "device_groups": [
            {"id": 1, "name": "GOP 1구역"},
            {"id": 2, "name": "VIP 감시"}
          ],
          "name_device": "CAM-001",
          "type_device": "IpCamera",
          "version": "3.0.0",
          "status": "ACTIVATED",
          "ip_address": "192.168.1.100",
          "ip_port": 80,
          "user_name": "admin",
          "user_password": "********",
          "rtsp_uri": "/stream1",
          "rtsp_port": 554,
          "mode": "ONVIF",
          "category": "PTZ",
          "is_record": true,
          "hardware_spec": {
            "name": "Axis P3245-V",
            "location": "GOP 1구역 전방 초소",
            "manufacturer": "Axis Communications",
            "model": "P3245-V",
            "hardware": "ARTPEC-7",
            "firmware": "10.12.114",
            "device_id": "ACCC8E123456",
            "mac_address": "AC:CC:8E:12:34:56",
            "onvif_version": "21.06"
          },
          "geolocation": {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "altitude": 50.0
          },
          "created_at": "2025-12-30T10:00:00",
          "updated_at": "2025-12-30T10:00:00"
        }
      ],
      "created_at": "2025-12-30T10:00:00",
      "updated_at": "2025-12-30T10:00:00"
    }
  ],
  "pagination": { ... }
}
```

> **Note**: `user_password`는 보안상 마스킹 처리하여 반환 (`********`)
> **Note**: `device_groups` 배열은 해당 디바이스가 소속된 모든 그룹을 반환 (N:N 관계)

---

#### 4.1.3 GET `/api/devices/groups/{group_id}` - 단건 조회

특정 디바이스 그룹의 상세 정보를 조회합니다.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `group_id` | Integer | Y | 그룹 ID |

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `include_devices` | Boolean | N | true | 디바이스 목록 포함 여부 |

**Response (200 OK)**
```json
{
  "success": true,
  "message": "Device group retrieved successfully",
  "data": {
    "id": 1,
    "name": "GOP 1구역",
    "description": "1구역 전방 감시 장비 그룹",
    "device_count": 15,
    "device_summary": {
      "controllers": 2,
      "sensors": 10,
      "cameras": 3
    },
    "devices": [
      {
        "id": 1,
        "device_type": "controller",
        "number_device": 101,
        "group_device": 1,
        "device_groups": [
          {"id": 1, "name": "GOP 1구역"}
        ],
        "name_device": "CTL-001",
        "type_device": "Controller",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.10",
        "ip_port": 8080,
        "created_at": "2025-12-30T10:00:00",
        "updated_at": "2025-12-30T10:00:00"
      },
      {
        "id": 2,
        "device_type": "sensor",
        "number_device": 201,
        "group_device": 1,
        "device_groups": [
          {"id": 1, "name": "GOP 1구역"},
          {"id": 3, "name": "야간 감시"}
        ],
        "name_device": "SNS-001",
        "type_device": "Fence",
        "version": "2.1.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "created_at": "2025-12-30T10:00:00",
        "updated_at": "2025-12-30T10:00:00"
      },
      {
        "id": 3,
        "device_type": "camera",
        "number_device": 301,
        "group_device": 1,
        "device_groups": [
          {"id": 1, "name": "GOP 1구역"},
          {"id": 2, "name": "VIP 감시"}
        ],
        "name_device": "CAM-001",
        "type_device": "IpCamera",
        "version": "3.0.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.100",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "********",
        "rtsp_uri": "/stream1",
        "rtsp_port": 554,
        "mode": "ONVIF",
        "category": "PTZ",
        "is_record": true,
        "hardware_spec": {
          "name": "Axis P3245-V",
          "location": "GOP 1구역 전방 초소",
          "manufacturer": "Axis Communications",
          "model": "P3245-V",
          "hardware": "ARTPEC-7",
          "firmware": "10.12.114",
          "device_id": "ACCC8E123456",
          "mac_address": "AC:CC:8E:12:34:56",
          "onvif_version": "21.06"
        },
        "geolocation": {
          "latitude": 37.5665,
          "longitude": 126.9780,
          "altitude": 50.0
        },
        "created_at": "2025-12-30T10:00:00",
        "updated_at": "2025-12-30T10:00:00"
      }
    ],
    "created_at": "2025-12-30T10:00:00",
    "updated_at": "2025-12-30T10:00:00"
  }
}
```

> **Note**: `user_password`는 보안상 마스킹 처리하여 반환 (`********`)
> **Note**: `device_groups` 배열은 해당 디바이스가 소속된 모든 그룹을 반환 (N:N 관계)

> **구현 방식**: Pydantic의 `Union` 타입과 `Discriminator`를 사용하여 `device_type` 필드 값에 따라 각 타입별 스키마를 자동 선택합니다.
> ```python
> from typing import Union, Annotated
> from pydantic import Discriminator
>
> DeviceResponse = Annotated[
>     Union[ControllerResponse, SensorResponse, CameraResponse],
>     Discriminator("device_type")
> ]
> ```

**Error Responses**

| 코드 | 상황 | 응답 |
|------|------|------|
| 404 | 그룹을 찾을 수 없음 | `{"success": false, "message": "Device group with id {group_id} not found"}` |

---

#### 4.1.4 POST `/api/devices/groups` - 생성

새로운 디바이스 그룹을 생성합니다.

**Request Body (DeviceGroupCreate)**

| 필드 | 타입 | 필수 | 제약조건 | 설명 |
|------|------|------|----------|------|
| `name` | String | Y | 1-200자, 유니크 | 그룹명 |
| `description` | String | N | 최대 500자 | 그룹 설명 |

```json
{
  "name": "GOP 1구역",
  "description": "1구역 전방 감시 장비 그룹"
}
```

**Response (201 Created)**
```json
{
  "success": true,
  "message": "Device group created successfully",
  "data": {
    "id": 1,
    "name": "GOP 1구역",
    "description": "1구역 전방 감시 장비 그룹",
    "device_count": 0,
    "devices": [],
    "created_at": "2025-12-30T10:00:00",
    "updated_at": "2025-12-30T10:00:00"
  }
}
```

**Error Responses**

| 코드 | 상황 | 응답 |
|------|------|------|
| 409 | 동일한 이름의 그룹 존재 | `{"success": false, "message": "Device group with name 'GOP 1구역' already exists"}` |
| 422 | 유효성 검사 실패 | `{"success": false, "message": "Validation error", "detail": [...]}` |

---

#### 4.1.5 PATCH `/api/devices/groups/{group_id}` - 부분 수정

디바이스 그룹의 일부 필드만 수정합니다.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `group_id` | Integer | Y | 그룹 ID |

**Request Body (DeviceGroupUpdate)**

| 필드 | 타입 | 필수 | 제약조건 | 설명 |
|------|------|------|----------|------|
| `name` | String | N | 1-200자, 유니크 | 그룹명 |
| `description` | String | N | 최대 500자 | 그룹 설명 |

```json
{
  "description": "1구역 전방 감시 장비 그룹 (수정됨)"
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "Device group updated successfully",
  "data": {
    "id": 1,
    "name": "GOP 1구역",
    "description": "1구역 전방 감시 장비 그룹 (수정됨)",
    "device_count": 15,
    "created_at": "2025-12-30T10:00:00",
    "updated_at": "2025-12-30T12:00:00"
  }
}
```

**Error Responses**

| 코드 | 상황 | 응답 |
|------|------|------|
| 404 | 그룹을 찾을 수 없음 | `{"success": false, "message": "Device group with id {group_id} not found"}` |
| 409 | 동일한 이름의 다른 그룹 존재 | `{"success": false, "message": "Device group with name '...' already exists"}` |

---

#### 4.1.6 PUT `/api/devices/groups/{group_id}` - 전체 수정

디바이스 그룹의 모든 필드를 교체합니다.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `group_id` | Integer | Y | 그룹 ID |

**Request Body (DeviceGroupCreate)**

| 필드 | 타입 | 필수 | 제약조건 | 설명 |
|------|------|------|----------|------|
| `name` | String | Y | 1-200자, 유니크 | 그룹명 |
| `description` | String | N | 최대 500자 | 그룹 설명 |

```json
{
  "name": "GOP 1구역 (변경)",
  "description": "전방 초소 감시 장비"
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "Device group replaced successfully",
  "data": {
    "id": 1,
    "name": "GOP 1구역 (변경)",
    "description": "전방 초소 감시 장비",
    "device_count": 15,
    "created_at": "2025-12-30T10:00:00",
    "updated_at": "2025-12-30T12:30:00"
  }
}
```

---

#### 4.1.7 DELETE `/api/devices/groups/{group_id}` - 삭제

디바이스 그룹을 삭제합니다.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `group_id` | Integer | Y | 그룹 ID |

**Query Parameters**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `force` | Boolean | N | false | 디바이스가 있어도 강제 삭제 |

**삭제 동작**

| `force` | 디바이스 존재 | 동작 |
|---------|--------------|------|
| false | 있음 | 삭제 거부 (409) |
| false | 없음 | 삭제 수행 |
| true | 있음 | 그룹 삭제, 디바이스의 `group_id`는 NULL로 설정 |
| true | 없음 | 삭제 수행 |

**Response (200 OK)**
```json
{
  "success": true,
  "message": "Device group deleted successfully",
  "data": {
    "id": 1,
    "affected_devices": 0
  }
}
```

**Response with `force=true` (200 OK)**
```json
{
  "success": true,
  "message": "Device group deleted successfully. 15 devices were unassigned.",
  "data": {
    "id": 1,
    "affected_devices": 15
  }
}
```

**Error Responses**

| 코드 | 상황 | 응답 |
|------|------|------|
| 404 | 그룹을 찾을 수 없음 | `{"success": false, "message": "Device group with id {group_id} not found"}` |
| 409 | 디바이스가 있는데 force=false | `{"success": false, "message": "Cannot delete group with 15 assigned devices. Use force=true to unassign and delete."}` |

---

#### 4.1.8 POST `/api/devices/groups/{group_id}/devices` - 디바이스 할당

그룹에 디바이스를 할당합니다. (벌크 지원)

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `group_id` | Integer | Y | 그룹 ID |

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `device_ids` | Array[Integer] | Y | 할당할 디바이스 ID 목록 |

```json
{
  "device_ids": [1, 2, 3, 4, 5]
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "message": "5 devices assigned to group successfully",
  "data": {
    "group_id": 1,
    "assigned_count": 5,
    "assigned_devices": [1, 2, 3, 4, 5]
  }
}
```

**Error Responses**

| 코드 | 상황 | 응답 |
|------|------|------|
| 404 | 그룹을 찾을 수 없음 | `{"success": false, "message": "Device group with id {group_id} not found"}` |
| 404 | 디바이스를 찾을 수 없음 | `{"success": false, "message": "Devices not found: [99, 100]"}` |
| 409 | 이미 다른 그룹에 할당됨 | `{"success": false, "message": "Devices already assigned to other groups: [3, 4]"}` |

---

#### 4.1.9 DELETE `/api/devices/groups/{group_id}/devices/{device_id}` - 디바이스 제거

그룹에서 특정 디바이스를 제거합니다.

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `group_id` | Integer | Y | 그룹 ID |
| `device_id` | Integer | Y | 디바이스 ID |

**Response (200 OK)**
```json
{
  "success": true,
  "message": "Device removed from group successfully",
  "data": {
    "group_id": 1,
    "device_id": 5
  }
}
```

**Error Responses**

| 코드 | 상황 | 응답 |
|------|------|------|
| 404 | 그룹을 찾을 수 없음 | `{"success": false, "message": "Device group with id {group_id} not found"}` |
| 404 | 디바이스를 찾을 수 없음 | `{"success": false, "message": "Device with id {device_id} not found"}` |
| 404 | 디바이스가 해당 그룹에 없음 | `{"success": false, "message": "Device {device_id} is not assigned to group {group_id}"}` |

---

#### 4.1.10 Pydantic Schema 정의

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    """디바이스 타입 구분"""
    CONTROLLER = "controller"
    SENSOR = "sensor"
    CAMERA = "camera"


class DeviceSummary(BaseModel):
    """디바이스 요약 정보 (그룹 내 디바이스 간략 정보)"""
    id: int
    device_type: DeviceType
    number_device: int
    name_device: str
    status: str

    class Config:
        from_attributes = True


class DeviceCountSummary(BaseModel):
    """디바이스 타입별 수량"""
    controllers: int = 0
    sensors: int = 0
    cameras: int = 0


class DeviceGroupBase(BaseModel):
    """DeviceGroup 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=200, description="그룹명")
    description: Optional[str] = Field(None, max_length=500, description="그룹 설명")


class DeviceGroupCreate(DeviceGroupBase):
    """DeviceGroup 생성 스키마"""
    pass


class DeviceGroupUpdate(BaseModel):
    """DeviceGroup 수정 스키마 (PATCH)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="그룹명")
    description: Optional[str] = Field(None, max_length=500, description="그룹 설명")


class DeviceGroupResponse(DeviceGroupBase):
    """DeviceGroup 응답 스키마"""
    id: int
    device_count: int = 0
    device_summary: Optional[DeviceCountSummary] = None
    devices: Optional[List[DeviceSummary]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceGroupListResponse(DeviceGroupBase):
    """DeviceGroup 목록 조회용 응답 스키마 (devices 제외)"""
    id: int
    device_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceAssignRequest(BaseModel):
    """디바이스 할당 요청 스키마"""
    device_ids: List[int] = Field(..., min_items=1, description="할당할 디바이스 ID 목록")


class DeviceAssignResponse(BaseModel):
    """디바이스 할당 응답 스키마"""
    group_id: int
    assigned_count: int
    assigned_devices: List[int]
```

### 4.2 기존 API 변경: Controller, Sensor, Camera

#### 4.2.1 하위 호환성 전략 (N:N 구조)

N:N 관계로 변경되면서, 디바이스는 여러 그룹에 소속될 수 있다. 기존 `group_device` 필드는 호환성을 위해 유지한다.

| 필드 | 상태 | 설명 |
|------|------|------|
| `group_device` | **유지 (Deprecated)** | 기존 호환성 유지, 첫 번째 그룹 ID 반환 |
| `device_groups` | **신규 추가** | 소속 그룹 배열 (N:N), 권장 사용 필드 |

#### 4.2.2 Request 변경

**기존 (계속 지원)** - 단일 그룹 할당
```json
{
  "group_device": 1,
  ...
}
```
> 내부적으로 `device_group_mappings` 테이블에 매핑 생성

**신규 (권장)** - 다중 그룹 할당
```json
{
  "group_ids": [1, 3],
  ...
}
```

**둘 다 지원** - 우선순위: `group_ids` > `group_device`
```json
{
  "group_device": 1,
  "group_ids": [2, 3],
  ...
}
// group_ids=[2, 3]이 적용됨
```

#### 4.2.3 Response 변경

**변경 후** (N:N 구조 반영)
```json
{
  "id": 1,
  "group_device": 1,
  "device_groups": [
    {"id": 1, "name": "GOP 1구역"},
    {"id": 3, "name": "야간 감시"}
  ],
  ...
}
```

> **Note**: `group_device`는 `device_groups` 배열의 첫 번째 그룹 ID를 반환 (호환성 유지)
> 그룹이 없는 경우 `group_device`는 기존 값 유지, `device_groups`는 빈 배열

#### 4.2.4 Deprecation 계획

```
Phase 1 (현재): group_device 유지 + device_groups 배열 추가 (N:N)
Phase 2 (v2.1): group_device에 @deprecated 경고 추가
Phase 3 (v3.0): group_device 제거, device_groups만 사용
```

#### 4.2.5 그룹 관리 방식 비교

| 방식 | 설명 | 사용 시나리오 |
|------|------|--------------|
| Device API에서 `group_ids` 지정 | 디바이스 생성/수정 시 그룹 할당 | 개별 디바이스 관리 |
| DeviceGroup API에서 디바이스 할당 | 그룹에 벌크로 디바이스 추가 | 그룹 중심 관리 |

두 방식 모두 동일한 `device_group_mappings` 테이블을 사용하며, 결과는 동일함.

### 4.3 Camera API 확장

#### 4.3.1 CameraCreate 신규 필드

```json
{
  "number_device": 1,
  "name_device": "CAM-001",
  "group_device": 1,
  "group_ids": [1, 2],
  "type_device": "IpCamera",
  "version": "1.0.0",
  "status": "ACTIVATED",
  "ip_address": "192.168.1.100",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "password123",
  "rtsp_uri": "/stream1",
  "rtsp_port": 554,
  "mode": "ONVIF",
  "category": "PTZ",
  "is_record": true,
  "hardware_spec": {
    "name": "Axis P3245-V",
    "location": "GOP 1구역 전방 초소",
    "manufacturer": "Axis Communications",
    "model": "P3245-V",
    "hardware": "ARTPEC-7",
    "firmware": "10.12.114",
    "device_id": "ACCC8E123456",
    "mac_address": "AC:CC:8E:12:34:56",
    "onvif_version": "21.06"
  },
  "geolocation": {
    "latitude": 37.5665,
    "longitude": 126.9780,
    "altitude": 50.0
  }
}
```

> **Note**: `group_ids`는 다중 그룹 할당용 (N:N), `group_device`는 호환성 유지용 (단일)

---

## 5. 데이터베이스 마이그레이션

### 5.1 마이그레이션 전략

```
Phase 1: 신규 테이블 생성
├── device_groups 테이블 생성
├── device_group_mappings 테이블 생성 (Junction Table)
├── devices 테이블 생성 (Base)
└── cameras 테이블에 신규 컬럼 추가

Phase 2: 데이터 마이그레이션
├── 기존 group_device 값으로 device_groups 레코드 생성 (DISTINCT)
├── 기존 controllers 데이터 → devices + controllers 분리
├── 기존 sensors 데이터 → devices + sensors 분리
├── 기존 cameras 데이터 → devices + cameras 분리
└── group_device 값으로 device_group_mappings 매핑 생성

Phase 3: 기존 테이블 정리
├── 구 테이블 백업
├── 공통 컬럼 삭제 (controllers, sensors, cameras)
└── 인덱스 및 제약조건 최적화

Phase 4: 검증
├── 데이터 무결성 검증 (N:N 매핑 확인)
├── API 테스트
└── 롤백 플랜 확인
```

### 5.1.1 Junction Table 마이그레이션 SQL

```sql
-- 1. device_groups 테이블 생성 (기존 group_device 값에서 DISTINCT)
INSERT INTO device_groups (id, name, description, created_at, updated_at)
SELECT DISTINCT
    group_device as id,
    'Group ' || group_device as name,
    NULL as description,
    datetime('now') as created_at,
    datetime('now') as updated_at
FROM (
    SELECT group_device FROM controllers
    UNION
    SELECT group_device FROM sensors
    UNION
    SELECT group_device FROM cameras
);

-- 2. device_group_mappings 생성 (기존 1:N → N:N 변환)
INSERT INTO device_group_mappings (device_id, group_id, created_at)
SELECT
    d.id as device_id,
    d.group_device as group_id,
    datetime('now') as created_at
FROM devices d
WHERE d.group_device IS NOT NULL;
```

### 5.2 롤백 플랜

- Phase 별 백업 테이블 유지
- 마이그레이션 스크립트에 롤백 함수 포함
- 문제 발생 시 백업 테이블에서 복원

### 5.3 예상 다운타임

| 데이터 규모 | 예상 시간 |
|-------------|----------|
| 1,000건 미만 | 1분 이내 |
| 10,000건 | 5분 이내 |
| 100,000건 | 30분 이내 |

---

## 6. 영향 범위

### 6.1 수정 대상 파일

| 구분 | 파일 | 변경 내용 |
|------|------|----------|
| **Models** | `app/models/device.py` | 전면 재작성 (상속 구조) |
| **Models** | `app/models/device_group.py` | 신규 생성 (DeviceGroup + DeviceGroupMapping) |
| **Schemas** | `app/schemas/device.py` | 전면 재작성, `device_groups` 배열 추가 |
| **Schemas** | `app/schemas/device_group.py` | 신규 생성 |
| **Routers** | `app/routers/controllers.py` | `group_ids` 지원, `device_groups` 응답 |
| **Routers** | `app/routers/sensors.py` | `group_ids` 지원, `device_groups` 응답 |
| **Routers** | `app/routers/cameras.py` | `group_ids` + 신규 필드, `device_groups` 응답 |
| **Routers** | `app/routers/device_groups.py` | 신규 생성 |
| **Routers** | `app/routers/__init__.py` | export 추가 |
| **Main** | `app/main.py` | 라우터 등록 |
| **Utils** | `app/utils/init_db.py` | 초기화 로직 수정 |
| **Tests** | `tests/test_*.py` | 테스트 케이스 수정 |

### 6.2 영향 받는 기존 API

| API | 영향 내용 |
|-----|----------|
| Event Mappings | `device_groups` 배열 추가, `group_device` 유지 |
| Camera Event Mappings | Camera 필드 확장 반영 |
| Detection Events | Device 조회 방식 변경 (Junction Table JOIN) |

### 6.3 하위 호환성 (N:N 구조)

| 항목 | 호환성 | 대응 방안 |
|------|--------|----------|
| `group_device` Request 파라미터 | ✅ 완전 호환 | 단일 그룹 할당으로 매핑 생성 |
| `group_ids` Request 파라미터 | ✅ 신규 추가 | 다중 그룹 할당 (권장) |
| `group_device` Response 필드 | ✅ 완전 호환 | 첫 번째 그룹 ID 반환 |
| `device_groups` Response 필드 | ✅ 신규 추가 | 소속 그룹 배열 (권장) |
| Camera 신규 필드 | ✅ 호환 | Optional 필드로 추가 |

---

## 7. 구현 계획

### 7.1 작업 단계

| 단계 | 작업 | 예상 소요 |
|------|------|----------|
| 1 | Models 재작성 (Device, DeviceGroup, DeviceGroupMapping) | 2시간 |
| 2 | Schemas 재작성 (`device_groups` 배열, `group_ids` 지원) | 1시간 |
| 3 | DeviceGroup Router 신규 개발 | 1시간 |
| 4 | Controllers Router 수정 (N:N 지원) | 30분 |
| 5 | Sensors Router 수정 (N:N 지원) | 30분 |
| 6 | Cameras Router 수정 + 신규 필드 (N:N 지원) | 1시간 |
| 7 | DB 마이그레이션 스크립트 작성 (Junction Table 포함) | 1시간 |
| 8 | 테스트 케이스 수정 | 1시간 |
| 9 | 통합 테스트 및 검증 | 1시간 |
| 10 | 문서 업데이트 | 30분 |
| **합계** | | **약 9시간** |

### 7.2 우선순위

```
[P0] 필수 - 기능 동작에 필수
├── Device Base 모델 구현
├── DeviceGroup + DeviceGroupMapping 모델 구현 (N:N)
├── 기존 Router 수정 (device_groups 배열 지원)
└── 마이그레이션 스크립트 (Junction Table 포함)

[P1] 중요 - 완성도에 중요
├── Camera 신규 필드 추가
├── API 문서 업데이트
└── 테스트 케이스

[P2] 개선 - 향후 개선 가능
├── 그룹별 통계 API
├── 대시보드 연동
└── 벌크 그룹 할당/해제 API
```

---

## 8. 테스트 계획

### 8.1 단위 테스트

| 테스트 대상 | 테스트 케이스 |
|------------|--------------|
| DeviceGroup CRUD | 생성, 조회, 수정, 삭제 |
| Device 상속 | Controller/Sensor/Camera 생성 시 devices 테이블 연동 |
| Group 할당 | Device에 Group 할당/해제 |
| Camera 신규 필드 | 하드웨어 스펙, 좌표 정보 저장/조회 |

### 8.2 통합 테스트

| 시나리오 | 검증 항목 |
|----------|----------|
| 그룹 생성 → 디바이스 할당 | FK 관계 정상 동작 |
| 그룹 삭제 시 디바이스 처리 | CASCADE or SET NULL 확인 |
| 디바이스 타입별 조회 | Polymorphic 쿼리 정상 동작 |
| API 필터링 | group_id 필터 정상 동작 |

### 8.3 성능 테스트

| 테스트 | 기준 |
|--------|------|
| 디바이스 1000건 조회 | < 500ms |
| 그룹별 디바이스 조회 | < 200ms |
| JOIN 쿼리 성능 | 기존 대비 10% 이내 저하 |

---

## 9. 위험 요소 및 대응

| 위험 | 영향도 | 발생 확률 | 대응 방안 |
|------|--------|----------|----------|
| 마이그레이션 실패 | 높음 | 낮음 | 롤백 스크립트 준비, 백업 유지 |
| API 하위 호환성 | 중간 | 높음 | 버전 관리, 클라이언트 업데이트 가이드 |
| 성능 저하 | 중간 | 중간 | 인덱스 최적화, 쿼리 튜닝 |
| 테스트 누락 | 낮음 | 중간 | 테스트 커버리지 확인 |

---

## 10. 승인

| 역할 | 이름 | 승인일 | 서명 |
|------|------|--------|------|
| 기획 | | | |
| 개발 | | | |
| QA | | | |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| v1.0 | 2025-12-30 | 초안 작성 | Claude |
