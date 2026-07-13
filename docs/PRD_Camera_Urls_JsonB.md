# PRD: Camera URLs JSONB 통합

**문서 버전**: v1.0
**작성일**: 2026-01-07
**작성자**: Claude AI
**상태**: Draft
**기준 API 버전**: v2.3

---

## 1. 개요

### 1.1 목적

Camera 모델의 `rtsp_uri`, `rtsp_port` 필드를 `urls` JSONB 컬럼으로 통합하여, 다양한 스트리밍 프로토콜(RTSP, WebRTC, HLS 등)과 접속 정보를 유연하게 관리할 수 있도록 합니다.

### 1.2 배경

#### 현재 구조의 한계

| 문제점 | 설명 |
|--------|------|
| **단일 RTSP만 지원** | `rtsp_uri` 하나로 main/sub 스트림 구분 불가 |
| **프로토콜 제한** | WebRTC, HLS, RTMP 등 다른 프로토콜 지원 불가 |
| **접속 정보 분산** | 카메라 homepage, ONVIF endpoint 등 별도 관리 필요 |
| **스냅샷 URL 부재** | 정지 이미지 캡처 URL 저장 공간 없음 |
| **확장성 부족** | 새로운 URL 타입 추가 시 스키마 변경 필요 |

#### 목표 구조

```json
{
  "homepage": { "url": "https://192.168.0.10/" },
  "onvif": { "device_service": "http://192.168.0.10:8000/onvif/device_service" },
  "streams": {
    "rtsp": {
      "main": "rtsp://192.168.0.10:554/Streaming/Channels/101",
      "sub":  "rtsp://192.168.0.10:554/Streaming/Channels/102"
    },
    "webrtc": {
      "main": "https://192.168.0.10/webrtc/main"
    },
    "hls": {
      "main": "https://192.168.0.10/hls/live.m3u8"
    }
  },
  "snapshot": {
    "ch1": "http://192.168.0.10/cgi-bin/snapshot.cgi"
  }
}
```

---

## 2. 영향 범위 분석

### 2.1 수정 대상 파일

#### Models (1개)

| 파일 | 변경 내용 |
|------|-----------|
| `app/models/device.py` | Camera 모델: `rtsp_uri`, `rtsp_port` 제거, `urls` JSONB 추가 |

#### Schemas (2개)

| 파일 | 변경 내용 |
|------|-----------|
| `app/schemas/device.py` | CameraUrls 스키마 추가, Camera 관련 스키마 수정 |
| `app/schemas/event.py` | 변경 없음 (device polymorphic은 스키마 참조) |

#### Routers (7개)

| 파일 | 변경 내용 |
|------|-----------|
| `app/routers/cameras.py` | CRUD 엔드포인트: urls 필드 처리 |
| `app/routers/detections.py` | `_build_device_nested_response()` 수정 |
| `app/routers/connections.py` | `_build_device_nested_response()` 수정 |
| `app/routers/malfunctions.py` | `_build_device_nested_response()` 수정 |
| `app/routers/actions.py` | `_build_device_nested_response()` 수정 |
| `app/routers/device_groups.py` | Camera 조회 시 urls 포함 |
| `app/routers/sensors.py` | 변경 없음 (Camera 미참조) |

### 2.2 영향받는 API 엔드포인트

#### Device API (직접 영향)

| Method | Endpoint | 영향 |
|--------|----------|------|
| GET | `/api/cameras` | Response에 urls 포함 |
| GET | `/api/cameras/{id}` | Response에 urls 포함 |
| POST | `/api/cameras` | Request에서 urls 받음 |
| PATCH | `/api/cameras/{id}` | urls 부분 업데이트 |
| PUT | `/api/cameras/{id}` | urls 전체 교체 |

#### Event API (간접 영향 - Nested Response)

| Method | Endpoint | 영향 |
|--------|----------|------|
| GET | `/api/detections` | device.urls 포함 |
| GET | `/api/detections/{id}` | device.urls 포함 |
| GET | `/api/malfunctions` | device.urls 포함 |
| GET | `/api/malfunctions/{id}` | device.urls 포함 |
| GET | `/api/connections` | device.urls 포함 |
| GET | `/api/connections/{id}` | device.urls 포함 |
| GET | `/api/actions` | device.urls 포함 |
| GET | `/api/actions/{id}` | device.urls 포함 |

#### DeviceGroup API (간접 영향)

| Method | Endpoint | 영향 |
|--------|----------|------|
| GET | `/api/device-groups/{id}` | cameras[].urls 포함 |

#### EventMapping API (간접 영향)

| Method | Endpoint | 영향 |
|--------|----------|------|
| GET | `/api/event-mappings/{id}/cameras` | camera.urls 포함 |

---

## 3. 스키마 설계

### 3.1 CameraUrls JSONB 구조

```python
# app/schemas/device.py

from pydantic import BaseModel, Field
from typing import Optional, Dict


class StreamUrls(BaseModel):
    """스트림 URL (main/sub 등)"""
    main: Optional[str] = Field(None, description="메인 스트림 URL")
    sub: Optional[str] = Field(None, description="서브 스트림 URL")

    model_config = ConfigDict(extra="allow")  # 추가 채널 허용


class HomepageUrl(BaseModel):
    """카메라 웹 인터페이스"""
    url: Optional[str] = Field(None, description="카메라 관리 페이지 URL")


class OnvifUrl(BaseModel):
    """ONVIF 서비스 URL"""
    device_service: Optional[str] = Field(None, description="ONVIF Device Service URL")
    media_service: Optional[str] = Field(None, description="ONVIF Media Service URL")
    ptz_service: Optional[str] = Field(None, description="ONVIF PTZ Service URL")


class CameraUrls(BaseModel):
    """
    카메라 URL 통합 스키마 (JSONB)

    다양한 프로토콜과 접속 정보를 유연하게 관리합니다.
    """
    homepage: Optional[HomepageUrl] = Field(None, description="카메라 웹 인터페이스")
    onvif: Optional[OnvifUrl] = Field(None, description="ONVIF 서비스 URL")
    streams: Optional[Dict[str, StreamUrls]] = Field(
        None,
        description="스트리밍 URL (rtsp, webrtc, hls, rtmp 등)"
    )
    snapshot: Optional[Dict[str, str]] = Field(
        None,
        description="스냅샷 URL (채널별)"
    )

    model_config = ConfigDict(from_attributes=True, extra="allow")
```

### 3.2 Camera 스키마 수정

#### CameraCreate (수정)

```python
class CameraCreate(BaseModel):
    """카메라 생성 스키마"""
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: str
    status: str
    ip_address: str
    ip_port: int
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    mode: str
    category: str
    is_record: bool = False
    hardware_spec: Optional[HardwareSpec] = None
    geolocation: Optional[Geolocation] = None
    urls: Optional[CameraUrls] = None  # ✅ 신규: JSONB URLs
    group_ids: Optional[List[int]] = None

    # ❌ 제거: rtsp_uri, rtsp_port
```

#### CameraResponse (수정)

```python
class CameraResponse(BaseModel):
    """카메라 응답 스키마"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: str
    status: str
    ip_address: str
    ip_port: int
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    mode: str
    category: str
    is_record: bool
    hardware_spec: Optional[HardwareSpec] = None
    geolocation: Optional[Geolocation] = None
    urls: Optional[CameraUrls] = None  # ✅ 신규: JSONB URLs
    created_at: datetime
    updated_at: datetime
    device_groups: List[DeviceGroupNestedResponse] = []

    # ❌ 제거: rtsp_uri, rtsp_port

    model_config = ConfigDict(from_attributes=True)
```

#### CameraNestedResponse (수정)

```python
class CameraNestedResponse(BaseModel):
    """카메라 Nested response 스키마 (Event/EventMapping에서 사용)"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str
    ip_address: str
    ip_port: int
    mode: str
    category: str
    is_record: bool
    hardware_spec: Optional[HardwareSpec] = None
    geolocation: Optional[Geolocation] = None
    urls: Optional[CameraUrls] = None  # ✅ 신규: JSONB URLs
    device_groups: List[DeviceGroupNestedResponse] = []

    # ❌ 제거: rtsp_uri, rtsp_port

    model_config = ConfigDict(from_attributes=True)
```

#### DeviceNestedResponse (수정)

```python
class DeviceNestedResponse(BaseModel):
    """폴리모픽 Device nested response 스키마"""
    # 공통 필드
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    status: str
    version: Optional[str] = None

    # Controller/Camera 공유 필드
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None

    # Sensor 전용 필드
    controller_id: Optional[int] = None

    # Camera 전용 필드 (변경)
    mode: Optional[str] = None
    category: Optional[str] = None
    is_record: Optional[bool] = None
    urls: Optional[CameraUrls] = None  # ✅ 신규: JSONB URLs

    # ❌ 제거: rtsp_uri, rtsp_port

    # 공통
    device_groups: List[DeviceGroupNestedResponse] = []

    model_config = ConfigDict(from_attributes=True)
```

---

## 4. 모델 설계

### 4.1 Camera 모델 수정

```python
# app/models/device.py

class Camera(Device):
    """
    카메라 모델

    PRD: PRD_Camera_Urls_JsonB.md
    - rtsp_uri, rtsp_port 제거
    - urls JSONB 필드 추가
    """
    __tablename__ = 'cameras'

    id = Column(Integer, ForeignKey('devices.id'), primary_key=True)
    ip_address = Column(String(100), nullable=False)
    ip_port = Column(Integer, nullable=False)
    user_name = Column(String(100), nullable=True)
    user_password = Column(String(200), nullable=True)
    mode = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    is_record = Column(Boolean, default=False, nullable=False)
    hardware_spec = Column(JSON, nullable=True)
    geolocation = Column(JSON, nullable=True)

    # ✅ 신규: URLs JSONB
    urls = Column(JSON, nullable=True, doc="카메라 URL 정보 (JSONB)")
    """
    {
        "homepage": { "url": "https://192.168.0.10/" },
        "onvif": { "device_service": "http://192.168.0.10:8000/onvif/device_service" },
        "streams": {
            "rtsp": { "main": "rtsp://...", "sub": "rtsp://..." },
            "webrtc": { "main": "https://..." }
        },
        "snapshot": { "ch1": "http://..." }
    }
    """

    # ❌ 제거
    # rtsp_uri = Column(String(500), nullable=True)
    # rtsp_port = Column(Integer, nullable=False, default=554)

    __mapper_args__ = {
        'polymorphic_identity': 'Camera'
    }
```

---

## 5. API Response 예시

### 5.1 Camera 단건 조회

**Endpoint**: `GET /api/cameras/{id}`

```json
{
  "success": true,
  "message": "Camera retrieved successfully",
  "data": {
    "id": 201,
    "number_device": 1,
    "group_device": 1,
    "name_device": "PTZ-Camera-01",
    "type_device": "IpCamera",
    "version": "1.0.0",
    "status": "ACTIVATED",
    "ip_address": "192.168.0.10",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "****",
    "mode": "ONVIF",
    "category": "PTZ",
    "is_record": true,
    "hardware_spec": {
      "name": "AXIS P5655-E",
      "manufacturer": "Axis Communications",
      "model": "P5655-E",
      "firmware": "10.12.114"
    },
    "geolocation": {
      "location": "GOP 1구역 전방 초소",
      "latitude": 37.123456,
      "longitude": 127.123456
    },
    "urls": {
      "homepage": {
        "url": "https://192.168.0.10/"
      },
      "onvif": {
        "device_service": "http://192.168.0.10:8000/onvif/device_service"
      },
      "streams": {
        "rtsp": {
          "main": "rtsp://192.168.0.10:554/Streaming/Channels/101",
          "sub": "rtsp://192.168.0.10:554/Streaming/Channels/102"
        },
        "webrtc": {
          "main": "https://192.168.0.10/webrtc/main"
        }
      },
      "snapshot": {
        "ch1": "http://192.168.0.10/cgi-bin/snapshot.cgi"
      }
    },
    "created_at": "2026-01-01T00:00:00.000+09:00",
    "updated_at": "2026-01-07T10:00:00.000+09:00",
    "device_groups": [
      { "id": 1, "name": "1구역 센서 그룹", "description": "1구역 감시 장비", "device_count": 5 }
    ]
  }
}
```

### 5.2 Detection Event 조회 (Nested Camera)

**Endpoint**: `GET /api/detections/{id}`

```json
{
  "success": true,
  "message": "Detection event retrieved successfully",
  "data": {
    "id": 1001,
    "event_time": "2026-01-07T10:30:00.000+09:00",
    "category_event": "intrusion",
    "status_event": "pending",
    "device": {
      "id": 201,
      "number_device": 1,
      "group_device": 1,
      "name_device": "PTZ-Camera-01",
      "type_device": "IpCamera",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "ip_address": "192.168.0.10",
      "ip_port": 80,
      "mode": "ONVIF",
      "category": "PTZ",
      "is_record": true,
      "hardware_spec": {
        "name": "AXIS P5655-E",
        "manufacturer": "Axis Communications"
      },
      "geolocation": {
        "location": "GOP 1구역 전방 초소",
        "latitude": 37.123456,
        "longitude": 127.123456
      },
      "urls": {
        "streams": {
          "rtsp": {
            "main": "rtsp://192.168.0.10:554/Streaming/Channels/101"
          }
        }
      },
      "device_groups": [
        { "id": 1, "name": "1구역 센서 그룹", "description": "1구역 감시 장비", "device_count": 5 }
      ]
    },
    "created_at": "2026-01-07T10:30:00.000+09:00",
    "updated_at": "2026-01-07T10:30:00.000+09:00"
  }
}
```

### 5.3 EventMappingCamera 조회 (Nested Camera)

**Endpoint**: `GET /api/event-mappings/{id}/cameras`

```json
{
  "success": true,
  "message": "Event mapping cameras retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "event_mapping_id": 10,
        "camera": {
          "id": 201,
          "number_device": 1,
          "group_device": 1,
          "name_device": "PTZ-Camera-01",
          "type_device": "IpCamera",
          "version": "1.0.0",
          "status": "ACTIVATED",
          "ip_address": "192.168.0.10",
          "ip_port": 80,
          "mode": "ONVIF",
          "category": "PTZ",
          "is_record": true,
          "hardware_spec": {
            "name": "AXIS P5655-E",
            "manufacturer": "Axis Communications"
          },
          "geolocation": {
            "location": "GOP 1구역 전방 초소",
            "latitude": 37.123456,
            "longitude": 127.123456
          },
          "urls": {
            "homepage": { "url": "https://192.168.0.10/" },
            "onvif": { "device_service": "http://192.168.0.10:8000/onvif/device_service" },
            "streams": {
              "rtsp": {
                "main": "rtsp://192.168.0.10:554/Streaming/Channels/101",
                "sub": "rtsp://192.168.0.10:554/Streaming/Channels/102"
              },
              "webrtc": { "main": "https://192.168.0.10/webrtc/main" }
            },
            "snapshot": { "ch1": "http://192.168.0.10/cgi-bin/snapshot.cgi" }
          },
          "device_groups": [
            { "id": 1, "name": "1구역 센서 그룹", "description": "1구역 감시 장비", "device_count": 5 }
          ]
        },
        "target_preset": {
          "id": 5,
          "camera_id": 201,
          "camera_name": "PTZ-Camera-01",
          "preset_index": 1,
          "preset_name": "입구 정면",
          "touring_time": 10
        },
        "home_preset": {
          "id": 6,
          "camera_id": 201,
          "camera_name": "PTZ-Camera-01",
          "preset_index": 0,
          "preset_name": "Home",
          "touring_time": 0
        },
        "delay_time": 30,
        "is_enable": true,
        "priority": 1,
        "created_at": "2026-01-07T10:00:00.000+09:00",
        "updated_at": "2026-01-07T10:00:00.000+09:00"
      }
    ],
    "total": 1
  }
}
```

---

## 6. 마이그레이션 계획

### 6.1 데이터 마이그레이션

```sql
-- Phase 1: urls 컬럼 추가
ALTER TABLE cameras ADD COLUMN urls JSONB;

-- Phase 2: 기존 rtsp_uri, rtsp_port 데이터를 urls로 마이그레이션
UPDATE cameras
SET urls = jsonb_build_object(
    'streams', jsonb_build_object(
        'rtsp', jsonb_build_object(
            'main', rtsp_uri
        )
    )
)
WHERE rtsp_uri IS NOT NULL;

-- Phase 3: 하위 호환성 검증 후 기존 컬럼 제거
-- ALTER TABLE cameras DROP COLUMN rtsp_uri;
-- ALTER TABLE cameras DROP COLUMN rtsp_port;
```

### 6.2 하위 호환성

#### Deprecation 기간 (옵션)

기존 클라이언트 호환을 위해 일정 기간 동안 두 필드 모두 지원:

```python
class CameraResponse(BaseModel):
    # 신규 필드
    urls: Optional[CameraUrls] = None

    # Deprecated 필드 (읽기 전용, 계산됨)
    rtsp_uri: Optional[str] = Field(None, deprecated=True)
    rtsp_port: Optional[int] = Field(None, deprecated=True)

    @computed_field
    @property
    def rtsp_uri(self) -> Optional[str]:
        """Deprecated: urls.streams.rtsp.main 사용 권장"""
        if self.urls and self.urls.streams and 'rtsp' in self.urls.streams:
            return self.urls.streams['rtsp'].main
        return None
```

---

## 7. 코드 변경 상세

### 7.1 Router 수정 (cameras.py)

```python
# _camera_to_response() 함수 수정

def _camera_to_response(camera: Camera, device_groups: List) -> CameraResponse:
    return CameraResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device,
        version=camera.version,
        status=camera.status,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        user_name=camera.user_name,
        user_password=camera.user_password,
        mode=camera.mode,
        category=camera.category,
        is_record=camera.is_record,
        hardware_spec=camera.hardware_spec,
        geolocation=camera.geolocation,
        urls=camera.urls,  # ✅ 신규
        # ❌ 제거: rtsp_uri, rtsp_port
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        device_groups=device_groups
    )
```

### 7.2 Event Router 수정 (공통 패턴)

```python
# detections.py, connections.py, malfunctions.py, actions.py

def _build_device_nested_response(device) -> DeviceNestedResponse:
    """Device polymorphic nested response 생성"""

    # Camera 타입일 때
    if isinstance(device, Camera):
        return CameraNestedResponse(
            id=device.id,
            number_device=device.number_device,
            group_device=device.group_device,
            name_device=device.name_device,
            type_device=device.type_device,
            version=device.version,
            status=device.status,
            ip_address=device.ip_address,
            ip_port=device.ip_port,
            mode=device.mode,
            category=device.category,
            is_record=device.is_record,
            hardware_spec=device.hardware_spec,
            geolocation=device.geolocation,
            urls=device.urls,  # ✅ 신규
            # ❌ 제거: rtsp_uri, rtsp_port
            device_groups=[...]
        )

    # Sensor, Controller 처리...
```

---

## 8. 구현 순서

### Phase 1: 스키마 및 모델 (0.5일)

1. `app/schemas/device.py`에 CameraUrls 스키마 추가
2. Camera 관련 스키마 수정 (Create, Response, Update, Nested)
3. DeviceNestedResponse 수정
4. `app/models/device.py` Camera 모델 수정

### Phase 2: Router 수정 (1일)

1. `app/routers/cameras.py` CRUD 엔드포인트 수정
2. Event routers 수정 (detections, connections, malfunctions, actions)
3. `app/routers/device_groups.py` Camera 조회 수정

### Phase 3: 마이그레이션 (0.5일)

1. DB 마이그레이션 스크립트 작성
2. 기존 데이터 변환
3. 테스트

### Phase 4: 정리 (선택)

1. 하위 호환 필드 Deprecation 경고
2. 기존 컬럼 제거 (충분한 마이그레이션 기간 후)

---

## 9. 고려사항

### 9.1 JSONB 쿼리 성능

```sql
-- streams.rtsp.main으로 검색이 필요한 경우 인덱스 추가
CREATE INDEX idx_cameras_urls_rtsp_main
ON cameras ((urls->'streams'->'rtsp'->>'main'));
```

### 9.2 Validation

```python
class CameraUrls(BaseModel):
    """URL 유효성 검사"""

    @field_validator('streams')
    @classmethod
    def validate_stream_urls(cls, v):
        if v:
            for protocol, urls in v.items():
                if urls.main and not urls.main.startswith(('rtsp://', 'https://', 'http://')):
                    raise ValueError(f"Invalid {protocol} main URL format")
        return v
```

### 9.3 Null 처리

```python
# urls가 null인 경우 기본값
urls: Optional[CameraUrls] = Field(default_factory=lambda: CameraUrls())
```

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| **v1.0** | 2026-01-07 | 초안 작성 - Camera URLs JSONB 통합 PRD |

---

## 11. 핵심 요약

### 제거 필드

```python
# ❌ 제거
rtsp_uri: Optional[str]
rtsp_port: int
```

### 신규 필드

```python
# ✅ 신규
urls: Optional[CameraUrls]  # JSONB
```

### urls 구조

```json
{
  "homepage": { "url": "..." },
  "onvif": { "device_service": "..." },
  "streams": {
    "rtsp": { "main": "...", "sub": "..." },
    "webrtc": { "main": "..." },
    "hls": { "main": "..." }
  },
  "snapshot": { "ch1": "..." }
}
```

### 영향받는 Response

1. **CameraResponse** - Camera CRUD
2. **CameraNestedResponse** - Event/EventMapping에서 Camera nested
3. **DeviceNestedResponse** - Event polymorphic device

---

**문서 끝**
