# PRD: Device Setting (ProxySetting & CameraSetting)

**작성일**: 2026-02-06
**소스**: docs/Device_Setting_Schema.md

---

## 1. 개요

NATS 제어 메시지로 변경되는 장비 설정(열선, 팬, 영상 모드 등)을 DB에 저장하기 위한 `proxy_settings`, `camera_settings` 테이블 및 REST API를 구현한다.

- **ProxySetting**: Server와 1:1 관계. PidsProxy 서버 운용 설정 (operation_mode, windy_mode)
- **CameraSetting**: Camera와 1:1 관계. 카메라 기능 설정 (악천후 모드, 영상 모드, 열선/팬/전조등, PTZ 속도, 팔레트 등)
- **초기화 방식**: GET 시 Lazy 생성 (설정 없으면 기본값으로 자동 생성)
- **삭제**: CASCADE DELETE (부모 삭제 시 자동 삭제, 별도 DELETE API 없음)

---

## 2. 신규 Enum 정의 (7개)

파일: `app/utils/enums.py`

| Enum 클래스 | 값 | 용도 |
|---|---|---|
| `EnumOperationMode` | `NORMAL`, `REGISTER` | Proxy 운용 모드 |
| `EnumWindyMode` | `wind0`, `wind1`, `wind2`, `wind3` | 풍량 모드 |
| `EnumWeatherMode` | `NORMAL`, `FOG`, `SEA_FOG`, `YELLOW_DUST`, `RAIN`, `SNOW`, `HEAT_HAZE` | 악천후 모드 |
| `EnumCameraVideoMode` | `NORMAL`, `STABILIZATION`, `BLC`, `NIGHT_ENHANCE` | 카메라 영상 모드 (기존 EnumCameraMode와 충돌 방지) |
| `EnumOnOff` | `on`, `off` | 열선/팬/전조등 상태 |
| `EnumDayNightMode` | `AUTO`, `DAY`, `NIGHT` | 주/야간 모드 |
| `EnumPalette` | `WHITE_HOT`, `BLACK_HOT`, `RAINBOW`, `IRONBOW` | 열화상 팔레트 (nullable) |

---

## 3. 신규 Model 정의

파일: `app/models/device_setting.py` (신규)

### 3.1 ProxySetting

| 컬럼 | 타입 | Nullable | 기본값 | 비고 |
|---|---|---|---|---|
| `id` | Integer PK | NO | AUTO | |
| `server_id` | Integer FK(servers.id) | NO | - | UNIQUE, CASCADE DELETE |
| `operation_mode` | Enum(EnumOperationMode) | NO | NORMAL | |
| `windy_mode` | Enum(EnumWindyMode) | NO | wind0 | |
| `created_at` | DateTime | NO | now() | |
| `updated_at` | DateTime | NO | now() | onupdate |

### 3.2 CameraSetting

| 컬럼 | 타입 | Nullable | 기본값 | 비고 |
|---|---|---|---|---|
| `id` | Integer PK | NO | AUTO | |
| `camera_id` | Integer FK(cameras.id) | NO | - | UNIQUE, CASCADE DELETE |
| `weather_mode` | Enum(EnumWeatherMode) | NO | NORMAL | |
| `camera_mode` | Enum(EnumCameraVideoMode) | NO | NORMAL | |
| `heater` | Enum(EnumOnOff) | NO | off | |
| `fan` | Enum(EnumOnOff) | NO | off | |
| `headlight` | Enum(EnumOnOff) | NO | off | |
| `day_night_mode` | Enum(EnumDayNightMode) | NO | AUTO | |
| `pan_tilt_speed` | Integer | NO | 50 | 0~100 |
| `zoom_speed` | Integer | NO | 50 | 0~100 |
| `palette` | Enum(EnumPalette) | YES | NULL | 열화상 전용 |
| `created_at` | DateTime | NO | now() | |
| `updated_at` | DateTime | NO | now() | onupdate |

---

## 4. 신규 Schema 정의

파일: `app/schemas/device_setting.py` (신규)

### 4.1 ProxySetting

- **ProxySettingUpdate**: `operation_mode?(EnumOperationMode)`, `windy_mode?(EnumWindyMode)` — 모두 Optional
- **ProxySettingResponse**: `id`, `server_id`, `operation_mode(str)`, `windy_mode(str)`, `created_at`, `updated_at` — ConfigDict(from_attributes=True)

### 4.2 CameraSetting

- **CameraSettingUpdate**: 모든 필드 Optional. `pan_tilt_speed`, `zoom_speed`는 `Field(ge=0, le=100)`
- **CameraSettingResponse**: 전체 12필드 + created_at/updated_at, palette는 `Optional[str]`

---

## 5. REST API 엔드포인트 (4개)

### 5.1 Proxy Settings

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/servers/{server_id}/proxy-settings` | 조회 (없으면 기본값 Lazy 생성) |
| PATCH | `/api/servers/{server_id}/proxy-settings` | 부분 수정 (없으면 Upsert) |

Router: `app/routers/proxy_settings.py` → `main.py`에서 `prefix="/api/servers"` 등록

### 5.2 Camera Settings

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/devices/cameras/{camera_id}/settings` | 조회 (없으면 기본값 Lazy 생성) |
| PATCH | `/api/devices/cameras/{camera_id}/settings` | 부분 수정 (없으면 Upsert) |

Router: `app/routers/camera_settings.py` → `main.py`에서 `prefix="/api/devices/cameras"` 등록

### 5.3 공통 로직

- **GET**: 부모 존재 확인(404) → 설정 조회 → 없으면 기본값 생성 → ApiResponse 반환
- **PATCH**: 부모 존재 확인(404) → 설정 조회 → 없으면 생성+적용, 있으면 `exclude_unset` 부분 업데이트 → ApiResponse 반환

---

## 6. 문서 업데이트

### 6.1 GOP_스키마_전체.md (v2.7 → v2.8)

- 버전/날짜 업데이트: v2.8 / 2026-02-06
- **Section 2.9**: `camera_settings` 테이블 추가 (cameras 다음)
- **Section 7.6**: `proxy_settings` 테이블 추가 (servers 다음)
- **Section 9.30~9.36**: 신규 Enum 7개 추가
- TOC 업데이트

### 6.2 GOP_Restful_Api_연동설계.md (v3.5 → v3.6)

- 버전/날짜 업데이트: v3.6 / 2026-02-06
- **Section 4**: 신규 Enum 정의 추가
- **Section 5.3.7~5.3.8**: Camera Setting 조회/수정 API (Camera API 하위)
- **Section 8.8**: Proxy Setting API (Server Monitoring 하위)
- TOC 업데이트
- **부록 변경이력**: v3.6 엔트리 추가 (금일 변경 내용 묶음)

---

## 7. 수정 대상 파일 목록

| 구분 | 파일 | 작업 |
|---|---|---|
| **신규** | `app/models/device_setting.py` | ProxySetting, CameraSetting 모델 |
| **신규** | `app/schemas/device_setting.py` | Update/Response 스키마 |
| **신규** | `app/routers/proxy_settings.py` | GET/PATCH 엔드포인트 |
| **신규** | `app/routers/camera_settings.py` | GET/PATCH 엔드포인트 |
| **수정** | `app/utils/enums.py` | 7개 Enum 추가 |
| **수정** | `app/main.py` | 라우터 등록, tags_metadata |
| **수정** | `app/utils/init_sample_data.py` | 샘플 데이터 추가 |
| **수정** | `docs/GOP_스키마_전체.md` | v2.8 테이블/Enum 추가 |
| **수정** | `GOP_Restful_Api_연동설계.md` | v3.6 API 섹션 추가 |
