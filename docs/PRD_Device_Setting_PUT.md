# PRD: Device Setting v1.1 - PUT API 추가 및 CameraSetting 필드 확장

**작성일**: 2026-02-09
**기반**: PRD_Device_Setting.md v1.0
**변경 유형**: 기능 추가 (Behavioral Change)

---

## 1. 배경 및 목적

### 1.1 PUT API 추가

현재 ProxySetting, CameraSetting은 PATCH(부분 수정)만 제공한다.
C#, Java 등 정적 타입 클라이언트는 전체 모델 객체를 보유하고 있으므로,
**PUT(전체 교체)** API를 함께 제공하여 클라이언트가 상황에 맞게 선택할 수 있도록 한다.

#### PUT vs PATCH 비교

| 구분 | PUT (전체 교체) | PATCH (부분 수정) |
|------|----------------|-------------------|
| 필드 | **모든 필드 필수** | 변경할 필드만 |
| 의미 | 현재 상태의 전체 스냅샷 저장 | 일부 필드만 변경 |
| 누락 필드 | **422 Validation Error** | 현재 값 유지 |
| 적합 클라이언트 | C#, Java (정형 모델) | JS, Python (동적) |
| Upsert | 없으면 생성 | 없으면 생성 |

### 1.2 CameraSetting 필드 확장

PTZ 카메라의 3대 광학 제어(Pan/Tilt, Zoom, **Focus**)에서 Focus 관련 설정이 누락되어 있다.
ONVIF ImagingSettings 기반으로 **focus_mode**, **iris_mode** 2개 필드를 추가한다.

#### ONVIF ImagingSettings 매핑

| ONVIF 속성 | CameraSetting 필드 | 비고 |
|------------|-------------------|------|
| Focus.AutoFocusMode | `focus_mode` | AUTO / MANUAL |
| Exposure.Mode (Iris) | `iris_mode` | AUTO / MANUAL |
| IrCutFilter | `day_night_mode` | 기존 구현 완료 |
| WhiteBalance.Mode | - | 향후 필요 시 추가 |

---

## 2. 신규 Enum 정의 (2개)

파일: `app/utils/enums.py`

| Enum 클래스 | 값 | 용도 |
|---|---|---|
| `EnumFocusMode` | `AUTO`, `MANUAL` | 카메라 초점 모드 |
| `EnumIrisMode` | `AUTO`, `MANUAL` | 카메라 조리개 모드 |

---

## 3. CameraSetting 모델 변경

파일: `app/models/device_setting.py`

### 3.1 추가 컬럼 (2개)

| 컬럼 | 타입 | Nullable | 기본값 | 비고 |
|------|------|----------|--------|------|
| `focus_mode` | Enum(EnumFocusMode) | NO | AUTO | ONVIF Focus.AutoFocusMode |
| `iris_mode` | Enum(EnumIrisMode) | NO | AUTO | ONVIF Exposure.Mode |

### 3.2 변경 후 CameraSetting 전체 컬럼

| 컬럼 | 타입 | Nullable | 기본값 | 비고 |
|------|------|----------|--------|------|
| `id` | Integer PK | NO | AUTO | |
| `camera_id` | Integer FK(cameras.id) | NO | - | UNIQUE, CASCADE DELETE |
| `weather_mode` | Enum(EnumWeatherMode) | NO | NORMAL | 악천후 모드 |
| `camera_mode` | Enum(EnumCameraVideoMode) | NO | NORMAL | 영상 모드 |
| `heater` | Enum(EnumOnOff) | NO | off | 열선 |
| `fan` | Enum(EnumOnOff) | NO | off | 냉각팬 |
| `headlight` | Enum(EnumOnOff) | NO | off | 전조등 |
| `day_night_mode` | Enum(EnumDayNightMode) | NO | AUTO | 주/야간 모드 |
| `focus_mode` | Enum(EnumFocusMode) | NO | AUTO | **신규** - 초점 모드 |
| `iris_mode` | Enum(EnumIrisMode) | NO | AUTO | **신규** - 조리개 모드 |
| `pan_tilt_speed` | Integer | NO | 50 | 0~100 |
| `zoom_speed` | Integer | NO | 50 | 0~100 |
| `palette` | Enum(EnumPalette) | YES | NULL | 열화상 전용 |
| `created_at` | DateTime | NO | now() | |
| `updated_at` | DateTime | NO | now() | onupdate |

---

## 4. Schema 변경

파일: `app/schemas/device_setting.py`

### 4.1 ProxySettingCreate (PUT용, 신규)

모든 필드 필수.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| operation_mode | EnumOperationMode | **Y** | 운용 모드 |
| windy_mode | EnumWindyMode | **Y** | 풍량 모드 |

### 4.2 CameraSettingUpdate (기존 수정)

focus_mode, iris_mode 필드 추가 (Optional).

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| weather_mode | EnumWeatherMode | N | 현재 값 유지 | 악천후 모드 |
| camera_mode | EnumCameraVideoMode | N | 현재 값 유지 | 영상 모드 |
| heater | EnumOnOff | N | 현재 값 유지 | 열선 |
| fan | EnumOnOff | N | 현재 값 유지 | 냉각팬 |
| headlight | EnumOnOff | N | 현재 값 유지 | 전조등 |
| day_night_mode | EnumDayNightMode | N | 현재 값 유지 | 주/야간 모드 |
| focus_mode | EnumFocusMode | N | 현재 값 유지 | **신규** - 초점 모드 |
| iris_mode | EnumIrisMode | N | 현재 값 유지 | **신규** - 조리개 모드 |
| pan_tilt_speed | integer (0-100) | N | 현재 값 유지 | 팬/틸트 속도 |
| zoom_speed | integer (0-100) | N | 현재 값 유지 | 줌 속도 |
| palette | EnumPalette | N | 현재 값 유지 | 열화상 팔레트 |

### 4.3 CameraSettingCreate (PUT용, 신규)

모든 필드 필수 (palette 제외).

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| weather_mode | EnumWeatherMode | **Y** | 악천후 모드 |
| camera_mode | EnumCameraVideoMode | **Y** | 영상 모드 |
| heater | EnumOnOff | **Y** | 열선 |
| fan | EnumOnOff | **Y** | 냉각팬 |
| headlight | EnumOnOff | **Y** | 전조등 |
| day_night_mode | EnumDayNightMode | **Y** | 주/야간 모드 |
| focus_mode | EnumFocusMode | **Y** | **신규** - 초점 모드 |
| iris_mode | EnumIrisMode | **Y** | **신규** - 조리개 모드 |
| pan_tilt_speed | integer (0-100) | **Y** | 팬/틸트 속도 |
| zoom_speed | integer (0-100) | **Y** | 줌 속도 |
| palette | EnumPalette | **N** | 열화상 팔레트 (nullable) |

### 4.4 CameraSettingResponse (기존 수정)

focus_mode, iris_mode 필드 추가.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int | 설정 ID |
| camera_id | int | 카메라 ID |
| weather_mode | EnumWeatherMode | 악천후 모드 |
| camera_mode | EnumCameraVideoMode | 영상 모드 |
| heater | EnumOnOff | 열선 |
| fan | EnumOnOff | 냉각팬 |
| headlight | EnumOnOff | 전조등 |
| day_night_mode | EnumDayNightMode | 주/야간 모드 |
| focus_mode | EnumFocusMode | **신규** - 초점 모드 |
| iris_mode | EnumIrisMode | **신규** - 조리개 모드 |
| pan_tilt_speed | int | 팬/틸트 속도 |
| zoom_speed | int | 줌 속도 |
| palette | EnumPalette? | 열화상 팔레트 (nullable) |
| created_at | datetime | 생성 일시 |
| updated_at | datetime | 수정 일시 |

---

## 5. 신규 API 엔드포인트 (2개)

| Method | Path | 설명 |
|--------|------|------|
| PUT | `/api/servers/{server_id}/proxy-settings` | 프록시 설정 전체 교체 (없으면 Upsert) |
| PUT | `/api/devices/cameras/{camera_id}/settings` | 카메라 설정 전체 교체 (없으면 Upsert) |

---

## 6. API 상세 명세

### 6.1 프록시 설정 전체 수정 (PUT)

**Endpoint**: `PUT /api/servers/{server_id}/proxy-settings`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | Server ID |

> **Note**: PUT은 전체 교체이므로 **모든 필드를 반드시 포함**합니다. 설정이 존재하지 않으면 Upsert (자동 생성).

**Request Example**:
```http
PUT /api/servers/1/proxy-settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "operation_mode": "REGISTER",
  "windy_mode": "wind2"
}
```

**Request Body** (전체 교체 - 모든 필드 필수):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| operation_mode | string | **Y** | 운용 모드 (EnumOperationMode) |
| windy_mode | string | **Y** | 풍량 모드 (EnumWindyMode) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Proxy settings replaced successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "operation_mode": "REGISTER",
    "windy_mode": "wind2",
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-09T14:30:00.150Z"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

### 6.2 카메라 설정 전체 수정 (PUT)

**Endpoint**: `PUT /api/devices/cameras/{camera_id}/settings`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | Camera ID |

> **Note**: PUT은 전체 교체이므로 **모든 필드를 반드시 포함**합니다 (palette 제외). 설정이 존재하지 않으면 Upsert (자동 생성).

**Request Example**:
```http
PUT /api/devices/cameras/201/settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "weather_mode": "FOG",
  "camera_mode": "STABILIZATION",
  "heater": "on",
  "fan": "on",
  "headlight": "off",
  "day_night_mode": "NIGHT",
  "focus_mode": "MANUAL",
  "iris_mode": "AUTO",
  "pan_tilt_speed": 80,
  "zoom_speed": 60,
  "palette": null
}
```

**Request Body** (전체 교체 - palette 외 모든 필드 필수):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| weather_mode | string | **Y** | 기상 모드 (EnumWeatherMode) |
| camera_mode | string | **Y** | 카메라 영상 모드 (EnumCameraVideoMode) |
| heater | string | **Y** | 히터 ON/OFF (EnumOnOff) |
| fan | string | **Y** | 팬 ON/OFF (EnumOnOff) |
| headlight | string | **Y** | 전조등 ON/OFF (EnumOnOff) |
| day_night_mode | string | **Y** | 주야간 모드 (EnumDayNightMode) |
| focus_mode | string | **Y** | 초점 모드 (EnumFocusMode) |
| iris_mode | string | **Y** | 조리개 모드 (EnumIrisMode) |
| pan_tilt_speed | integer | **Y** | 팬틸트 속도 (0~100) |
| zoom_speed | integer | **Y** | 줌 속도 (0~100) |
| palette | string | N | 열화상 팔레트 (EnumPalette, nullable) |

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera settings replaced successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "weather_mode": "FOG",
    "camera_mode": "STABILIZATION",
    "heater": "on",
    "fan": "on",
    "headlight": "off",
    "day_night_mode": "NIGHT",
    "focus_mode": "MANUAL",
    "iris_mode": "AUTO",
    "pan_tilt_speed": 80,
    "zoom_speed": 60,
    "palette": null,
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-09T14:30:00.150Z"
  },
  "meta": {
    "timestamp": "2026-02-09T14:30:00.200Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Camera with id 999 not found",
    "details": "No camera exists with the specified ID"
  },
  "meta": {
    "timestamp": "2026-02-09T14:30:00.200Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

---

## 7. PUT과 PATCH 동작 차이

### 7.1 ProxySetting 예시

현재 DB 상태: `operation_mode="REGISTER", windy_mode="wind3"`

| 요청 | PUT 결과 | PATCH 결과 |
|------|----------|------------|
| `{"operation_mode": "NORMAL", "windy_mode": "wind0"}` | NORMAL, wind0 | NORMAL, wind0 |
| `{"operation_mode": "NORMAL"}` | **422 Validation Error** (windy_mode 누락) | NORMAL, **wind3** (유지) |

### 7.2 CameraSetting 예시

현재 DB 상태: `heater="on", fan="on", focus_mode="AUTO", ...`

| 요청 | PUT 결과 | PATCH 결과 |
|------|----------|------------|
| 전체 필드 포함 | 요청값으로 전체 교체 | 요청값으로 전체 교체 |
| `{"heater": "off"}` 만 | **422 Validation Error** (필수 필드 누락) | heater만 off, 나머지 유지 |
| `{"focus_mode": "MANUAL"}` 만 | **422 Validation Error** | focus_mode만 MANUAL, 나머지 유지 |

---

## 8. CameraSetting 필드 분류 (변경 후)

| 분류 | 필드 | ONVIF 대응 |
|------|------|-----------|
| **환경 대응** | weather_mode, heater, fan, headlight, day_night_mode | IrCutFilter |
| **영상 모드** | camera_mode | VideoSourceConfiguration |
| **광학 제어** | focus_mode, iris_mode | ImagingSettings |
| **PTZ 제어** | pan_tilt_speed, zoom_speed | PTZ.ContinuousMove |
| **열화상** | palette | Thermal Extension |

---

## 9. 코드 수정 상세

### 9.1 `app/utils/enums.py` — Enum 2개 추가

```python
class EnumFocusMode(str, Enum):
    """카메라 초점 모드"""
    AUTO = "AUTO"
    MANUAL = "MANUAL"

class EnumIrisMode(str, Enum):
    """카메라 조리개 모드"""
    AUTO = "AUTO"
    MANUAL = "MANUAL"
```

### 9.2 `app/models/device_setting.py` — CameraSetting 컬럼 추가

`day_night_mode` 다음, `pan_tilt_speed` 앞에 추가:

```python
focus_mode = Column(SAEnum(EnumFocusMode), nullable=False, default=EnumFocusMode.AUTO)
iris_mode = Column(SAEnum(EnumIrisMode), nullable=False, default=EnumIrisMode.AUTO)
```

### 9.3 `app/schemas/device_setting.py` — Schema 변경

**추가할 Schema:**
- `ProxySettingCreate`: 모든 필드 required (PUT용)
- `CameraSettingCreate`: palette 외 모든 필드 required (PUT용)

**수정할 Schema:**
- `CameraSettingUpdate`: focus_mode, iris_mode Optional 필드 추가
- `CameraSettingResponse`: focus_mode, iris_mode 필드 추가

### 9.4 `app/routers/proxy_settings.py` — PUT 엔드포인트 추가

```python
@router.put("/{server_id}/proxy-settings")
async def replace_proxy_settings(server_id, create_data: ProxySettingCreate, ...):
    # Server 존재 확인 (404)
    # ProxySetting 조회 → 없으면 생성 (Upsert)
    # 모든 필드를 create_data 값으로 교체
    # message: "Proxy settings replaced successfully"
```

### 9.5 `app/routers/camera_settings.py` — PUT 엔드포인트 추가

```python
@router.put("/{camera_id}/settings")
async def replace_camera_settings(camera_id, create_data: CameraSettingCreate, ...):
    # Camera 존재 확인 (404)
    # CameraSetting 조회 → 없으면 생성 (Upsert)
    # 모든 필드를 create_data 값으로 교체
    # message: "Camera settings replaced successfully"
```

### 9.6 `app/utils/init_sample_data.py` — 샘플 데이터 반영

`_create_camera_settings()` 함수의 presets에 `focus_mode`, `iris_mode` 필드 추가.

---

## 10. GOP_스키마_전체.md 업데이트 (v2.8 → v2.9)

### 10.1 버전/날짜 변경 (Line 3-5)

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| 문서 버전 | v2.8 | **v2.9** |
| 최종 업데이트 | 2026-02-06 | **2026-02-09** |
| 기준 API 버전 | v3.6 | **v3.7** |

### 10.2 camera_settings 테이블 수정 (Section 2.9, Line 686~)

**SQL DDL에 Enum 타입 추가** (기존 enum_palette 다음):
```sql
CREATE TYPE enum_focus_mode AS ENUM ('AUTO', 'MANUAL');
CREATE TYPE enum_iris_mode AS ENUM ('AUTO', 'MANUAL');
```

**CREATE TABLE에 컬럼 추가** (day_night_mode 다음, pan_tilt_speed 앞):
```sql
focus_mode enum_focus_mode NOT NULL DEFAULT 'AUTO',
iris_mode enum_iris_mode NOT NULL DEFAULT 'AUTO',
```

**필드 정의 테이블에 행 추가** (day_night_mode 다음):

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| focus_mode | ENUM | NO | AUTO | 초점 모드 (EnumFocusMode) |
| iris_mode | ENUM | NO | AUTO | 조리개 모드 (EnumIrisMode) |

### 10.3 Enum 정의 추가 (Section 9.37~9.38, Line 2654~ 기존 9.36 다음)

**9.37 EnumFocusMode (v2.9 신규)**

카메라 초점 모드 — 2종

| 값 | 설명 |
|-----|------|
| AUTO | 자동 초점 |
| MANUAL | 수동 초점 |

**9.38 EnumIrisMode (v2.9 신규)**

카메라 조리개 모드 — 2종

| 값 | 설명 |
|-----|------|
| AUTO | 자동 조리개 |
| MANUAL | 수동 조리개 |

### 10.4 TOC 업데이트 (Line 91~98)

Settings Enum 범위 변경: `9.30~9.36` → `9.30~9.38`

추가:
```markdown
  - 9.37 [EnumFocusMode](#937-enumfocusmode-v29-신규)
  - 9.38 [EnumIrisMode](#938-enumirismode-v29-신규)
```

### 10.5 변경 이력 추가 (Section 13, Line 3510~)

v2.8 앞에 v2.9 엔트리 삽입:

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| **v2.9** | 2026-02-09 | **CameraSetting 필드 확장 (focus_mode, iris_mode)**<br>1. camera_settings 테이블 변경 (2.9): focus_mode, iris_mode 컬럼 추가<br>2. Settings Enum 추가 (9.37~9.38): EnumFocusMode (2종), EnumIrisMode (2종) |

---

## 11. GOP_Restful_Api_연동설계.md 업데이트 (v3.6 → v3.7)

### 11.1 버전/날짜 변경 (Line 4-5)

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| 최종 수정일 | 2026-02-06 | **2026-02-09** |
| 버전 | v3.6 | **v3.7** |

### 11.2 TOC 업데이트

**Camera API 하위 (Line 22~24)** — 5.3.9 추가, 기존 태그 수정:
```
     - 5.3.7 [카메라 설정 조회](#537-카메라-설정-조회) *(v3.7 수정)*
     - 5.3.8 [카메라 설정 수정 (부분)](#538-카메라-설정-수정-부분) *(v3.7 수정)*
     - 5.3.9 [카메라 설정 수정 (전체)](#539-카메라-설정-수정-전체) *(v3.7 신규)*
```

**Server Monitoring API 하위 (Line 51)** — 8.8.3 추가:
```
  - 8.8 [프록시 설정 API](#88-프록시-설정-api) *(v3.7 수정)*
    - 8.8.1 프록시 설정 조회
    - 8.8.2 프록시 설정 수정 (부분) *(v3.7 제목 변경)*
    - 8.8.3 프록시 설정 수정 (전체) *(v3.7 신규)*
```

### 11.3 Enum 정의 추가 (Section 4.9, Line 974~ EnumPalette 사용처 다음)

기존 EnumPalette 블록 다음에 추가:

```markdown
#### EnumFocusMode (카메라 초점 모드 - 2종)

​```python
# Python 정의 - app/utils/enums.py
class EnumFocusMode(str, Enum):
    """카메라 초점 모드 (ONVIF Focus.AutoFocusMode)"""
    AUTO = "AUTO"       # 자동 초점
    MANUAL = "MANUAL"   # 수동 초점
​```

**사용처**:
- `CameraSetting.focus_mode`: 카메라 초점 모드

#### EnumIrisMode (카메라 조리개 모드 - 2종)

​```python
# Python 정의 - app/utils/enums.py
class EnumIrisMode(str, Enum):
    """카메라 조리개 모드 (ONVIF Exposure.Mode)"""
    AUTO = "AUTO"       # 자동 조리개
    MANUAL = "MANUAL"   # 수동 조리개
​```

**사용처**:
- `CameraSetting.iris_mode`: 카메라 조리개 모드
```

### 11.4 Section 5.3.7 카메라 설정 조회 수정 (Line 3085~)

**Response Example의 `data` 객체에 focus_mode, iris_mode 추가** (day_night_mode 다음, pan_tilt_speed 앞):
```json
    "focus_mode": "AUTO",             //(EnumFocusMode)
    "iris_mode": "AUTO",              //(EnumIrisMode)
```

### 11.5 Section 5.3.8 카메라 설정 수정 (부분) 수정 (Line 3147~)

**Request Body 필드 테이블에 행 추가** (day_night_mode 다음, pan_tilt_speed 앞):

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| focus_mode | string | N | "AUTO" | 초점 모드 (EnumFocusMode) (현재 값 유지) |
| iris_mode | string | N | "AUTO" | 조리개 모드 (EnumIrisMode) (현재 값 유지) |

**Response Example의 `data` 객체에 focus_mode, iris_mode 추가** (day_night_mode 다음).

### 11.6 Section 5.3.9 카메라 설정 수정 (전체) 신규 삽입

**삽입 위치**: 5.3.8 다음, 5.4 (Speaker API) 앞

```markdown
#### 5.3.9 카메라 설정 수정 (전체)

**Endpoint**: `PUT /api/devices/cameras/{camera_id}/settings`
```

내용: 본 PRD Section 6.2의 전체 명세를 해당 문서 포맷으로 작성.
포함 항목: Path Parameters, Note, Request Example, Request Body 테이블, Response Example (200 OK), Error Response (404).

### 11.7 Section 8.8.2 프록시 설정 수정 제목 변경 (Line 12072)

| 변경 전 | 변경 후 |
|---------|---------|
| `#### 8.8.2 프록시 설정 수정` | `#### 8.8.2 프록시 설정 수정 (부분)` |

### 11.8 Section 8.8.3 프록시 설정 수정 (전체) 신규 삽입

**삽입 위치**: 8.8.2 다음, Section 9 (Account API) 앞

```markdown
#### 8.8.3 프록시 설정 수정 (전체)

​```http
PUT /api/servers/{server_id}/proxy-settings
​```
```

내용: 본 PRD Section 6.1의 전체 명세를 해당 문서 포맷으로 작성.
포함 항목: Path Parameters, Note, Request Example, Request Body 테이블, Response Example (200 OK), Error Response (404).

### 11.9 삭제 항목

- 기존 5.3.7, 5.3.8의 CameraSetting Response에서 focus_mode/iris_mode가 없는 구버전 JSON 예시 삭제 → 신규 필드 포함 형태로 교체

### 11.10 변경 이력 추가 (Line 13812~, v3.6 앞에 삽입)

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| **v3.7** | 2026-02-09 | **Device Setting PUT API 추가, CameraSetting focus_mode/iris_mode 필드 확장, Enum 2종 추가**<br><br>**[1. Device Setting Enum 추가 (4.9)]**<br>- **EnumFocusMode (2종)**: AUTO, MANUAL<br>- **EnumIrisMode (2종)**: AUTO, MANUAL<br><br>**[2. Camera Settings API 변경 (5.3.7~5.3.9)]**<br>- **5.3.7 GET 응답 변경**: focus_mode, iris_mode 필드 추가<br>- **5.3.8 PATCH 요청/응답 변경**: focus_mode, iris_mode 필드 추가<br>- **5.3.9 PUT /api/devices/cameras/{camera_id}/settings 신규**: 전체 교체 (Upsert)<br><br>**[3. Proxy Settings API 변경 (8.8.2~8.8.3)]**<br>- **8.8.2 제목 변경**: "프록시 설정 수정" → "프록시 설정 수정 (부분)"<br>- **8.8.3 PUT /api/servers/{server_id}/proxy-settings 신규**: 전체 교체 (Upsert) |

### 11.11 영향 범위 확인 — CameraSetting Response Nested 여부

CameraSetting Response는 **독립 1:1 설정 리소스**로, 다른 API의 Response에 nested로 포함되지 않음.
따라서 다른 API의 Response 구조에는 **변경 불필요**.

| API | CameraSetting 포함 여부 | 변경 필요 |
|-----|----------------------|----------|
| Camera API (5.3) | Camera 응답에 settings 미포함 | **없음** |
| Integration API (7절) | CameraNestedResponseIntegration에 settings 미포함 | **없음** |
| DeviceGroup API (5.6) | CameraSummary에 settings 미포함 | **없음** |
| Event API (6절) | CameraNestedResponse에 settings 미포함 | **없음** |
| **CameraSetting API (5.3.7~5.3.9)** | **직접 반환** | **수정 대상** |

---

## 12. Swagger / Docs / Redoc 자동 반영

FastAPI의 OpenAPI 자동 생성으로, 코드 변경 시 서버 재시작만으로 Swagger/Redoc에 자동 반영됨:

| 항목 | 자동 반영 | 비고 |
|------|----------|------|
| PUT 엔드포인트 표시 | O | `@router.put()` 데코레이터 |
| Request Body 스키마 | O | `ProxySettingCreate`, `CameraSettingCreate` Pydantic 모델 |
| Response 스키마 | O | 기존 `ProxySettingResponse`, `CameraSettingResponse` 재사용 |
| Enum 드롭다운 | O | `EnumFocusMode`, `EnumIrisMode` 타입 사용 시 |
| focus_mode, iris_mode 필드 | O | Schema에 추가하면 자동 노출 |
| API Tags 그룹핑 | O | 기존 "Proxy Settings", "Camera Settings" 태그 사용 |

**별도 문서 수정 불필요. 서버 재시작 후 자동 반영.**

---

## 13. 수정 대상 파일 전체 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| **코드** | `app/utils/enums.py` | EnumFocusMode, EnumIrisMode 추가 |
| **코드** | `app/models/device_setting.py` | CameraSetting에 focus_mode, iris_mode 컬럼 추가 |
| **코드** | `app/schemas/device_setting.py` | ProxySettingCreate, CameraSettingCreate 신규 + Update/Response 수정 |
| **코드** | `app/routers/proxy_settings.py` | PUT 엔드포인트 추가 |
| **코드** | `app/routers/camera_settings.py` | PUT 엔드포인트 추가 |
| **코드** | `app/utils/init_sample_data.py` | 샘플 데이터에 focus_mode, iris_mode 반영 |
| **문서** | `GOP_Restful_Api_연동설계.md` | v3.7: Enum 2개, 5.3.7~5.3.9, 8.8.2~8.8.3, TOC, 변경이력 |
| **문서** | `docs/GOP_스키마_전체.md` | v2.9: camera_settings 컬럼, Enum 9.37~9.38, TOC, 변경이력 |

---

## 14. 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-02-06 | v1.0 | 초기 작성 (GET/PATCH) |
| 2026-02-09 | v1.1 | PUT API 추가, CameraSetting에 focus_mode/iris_mode 필드 추가 |
