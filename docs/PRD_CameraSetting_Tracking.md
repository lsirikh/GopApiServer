# PRD: CameraSetting 필드 변경 — pan_tilt_speed/zoom_speed 삭제 및 tracking 추가

**작성일**: 2026-02-09
**변경 유형**: 구조 변경 (Structural) + 동작 변경 (Behavioral)

---

## 1. 배경 및 목적

### 1.1 삭제 대상: pan_tilt_speed, zoom_speed

현재 CameraSetting에 `pan_tilt_speed`(Integer, 0~100, 기본값 50)와 `zoom_speed`(Integer, 0~100, 기본값 50) 필드가 있다.
해당 필드를 **삭제**한다.

### 1.2 추가 대상: tracking

PTZ 카메라의 자동 추적(Auto Tracking) 상태를 관리하기 위한 `tracking` 필드를 추가한다.

| 상태 | 설명 |
|------|------|
| `ACTIVE` | 타겟 추적 중 (target 정보 포함) |
| `LOST` | 타겟 놓침 (마지막 위치 전송 후 idle로 전환) |
| `IDLE` | 추적 비활성 (TRACKING_SET off 시) |

---

## 2. 신규 Enum 정의 (1개)

파일: `app/utils/enums.py`

| Enum 클래스 | 값 | 용도 |
|---|---|---|
| `EnumTrackingStatus` | `ACTIVE`, `LOST`, `IDLE` | 카메라 추적 상태 |

```python
class EnumTrackingStatus(str, Enum):
    """카메라 자동 추적 상태"""
    ACTIVE = "ACTIVE"   # 타겟 추적 중
    LOST = "LOST"       # 타겟 놓침
    IDLE = "IDLE"       # 추적 비활성
```

---

## 3. CameraSetting 모델 변경

파일: `app/models/device_setting.py`

### 3.1 삭제 컬럼

| 컬럼 | 현재 타입 | 현재 기본값 |
|------|----------|-----------|
| `pan_tilt_speed` | Integer, NOT NULL | 50 |
| `zoom_speed` | Integer, NOT NULL | 50 |

### 3.2 추가 컬럼

| 컬럼 | 타입 | Nullable | 기본값 | 비고 |
|------|------|----------|--------|------|
| `tracking` | Enum(EnumTrackingStatus) | NO | IDLE | 자동 추적 상태 |

### 3.3 변경 후 컬럼 목록 (14개)

| # | 컬럼 | 타입 | Nullable | 기본값 |
|---|------|------|----------|--------|
| 1 | id | Integer PK | NO | AUTO |
| 2 | camera_id | Integer FK | NO | - |
| 3 | weather_mode | Enum(EnumWeatherMode) | NO | NORMAL |
| 4 | camera_mode | Enum(EnumCameraVideoMode) | NO | NORMAL |
| 5 | heater | Enum(EnumOnOff) | NO | off |
| 6 | fan | Enum(EnumOnOff) | NO | off |
| 7 | headlight | Enum(EnumOnOff) | NO | off |
| 8 | day_night_mode | Enum(EnumDayNightMode) | NO | AUTO |
| 9 | focus_mode | Enum(EnumFocusMode) | NO | AUTO |
| 10 | iris_mode | Enum(EnumIrisMode) | NO | AUTO |
| 11 | **tracking** | **Enum(EnumTrackingStatus)** | **NO** | **IDLE** |
| 12 | palette | Enum(EnumPalette) | YES | NULL |
| 13 | created_at | DateTime | NO | now() |
| 14 | updated_at | DateTime | NO | now() |

---

## 4. Schema 변경

파일: `app/schemas/device_setting.py`

### 4.1 CameraSettingCreate (PUT용, 모든 필드 required)

| 변경 | 필드 | 타입 | 비고 |
|------|------|------|------|
| 삭제 | ~~pan_tilt_speed~~ | ~~int, ge=0, le=100~~ | |
| 삭제 | ~~zoom_speed~~ | ~~int, ge=0, le=100~~ | |
| 추가 | tracking | EnumTrackingStatus | required |

### 4.2 CameraSettingUpdate (PATCH용, 모든 필드 Optional)

| 변경 | 필드 | 타입 | 비고 |
|------|------|------|------|
| 삭제 | ~~pan_tilt_speed~~ | ~~Optional[int]~~ | |
| 삭제 | ~~zoom_speed~~ | ~~Optional[int]~~ | |
| 추가 | tracking | Optional[EnumTrackingStatus] | |

### 4.3 CameraSettingResponse

| 변경 | 필드 | 타입 | 비고 |
|------|------|------|------|
| 삭제 | ~~pan_tilt_speed~~ | ~~int~~ | |
| 삭제 | ~~zoom_speed~~ | ~~int~~ | |
| 추가 | tracking | EnumTrackingStatus | |

---

## 5. API 동작 변경

### 5.1 GET /api/devices/cameras/{camera_id}/settings

**Response 변경**:
```json
{
  "success": true,
  "message": "Camera settings retrieved successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "weather_mode": "NORMAL",
    "camera_mode": "NORMAL",
    "heater": "off",
    "fan": "off",
    "headlight": "off",
    "day_night_mode": "AUTO",
    "focus_mode": "AUTO",
    "iris_mode": "AUTO",
    "tracking": "IDLE",
    "palette": null,
    "created_at": "2026-02-09T12:00:00.000Z",
    "updated_at": "2026-02-09T12:00:00.000Z"
  }
}
```

- ~~pan_tilt_speed~~ 삭제
- ~~zoom_speed~~ 삭제
- `tracking` 추가 (기본값 `"IDLE"`)

### 5.2 PATCH /api/devices/cameras/{camera_id}/settings

**Request Body 변경**:

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| weather_mode | string | N | "NORMAL" | 기상 모드 (EnumWeatherMode) |
| camera_mode | string | N | "NORMAL" | 카메라 영상 모드 (EnumCameraVideoMode) |
| heater | string | N | "off" | 히터 ON/OFF (EnumOnOff) |
| fan | string | N | "off" | 팬 ON/OFF (EnumOnOff) |
| headlight | string | N | "off" | 전조등 ON/OFF (EnumOnOff) |
| day_night_mode | string | N | "AUTO" | 주야간 모드 (EnumDayNightMode) |
| focus_mode | string | N | "AUTO" | 초점 모드 (EnumFocusMode) |
| iris_mode | string | N | "AUTO" | 조리개 모드 (EnumIrisMode) |
| **tracking** | **string** | **N** | **"IDLE"** | **추적 상태 (EnumTrackingStatus)** |
| palette | string | N | null | 열화상 팔레트 (EnumPalette, nullable) |

- ~~pan_tilt_speed~~ 삭제
- ~~zoom_speed~~ 삭제

### 5.3 PUT /api/devices/cameras/{camera_id}/settings

**Request Body 변경**:

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
| **tracking** | **string** | **Y** | **추적 상태 (EnumTrackingStatus)** |
| palette | string | N | 열화상 팔레트 (EnumPalette, nullable) |

- ~~pan_tilt_speed~~ 삭제
- ~~zoom_speed~~ 삭제

---

## 6. 샘플 데이터 변경

파일: `app/utils/init_sample_data.py` → `_create_camera_settings()`

모든 preset에서 `pan_tilt_speed`, `zoom_speed` 제거하고 `tracking` 추가.

---

## 7. 문서 업데이트

### 7.1 GOP_스키마_전체.md (v2.9 유지 — 같은 날 변경 통합)

| 위치 | 작업 |
|------|------|
| 버전/날짜 | v2.9 유지 (2026-02-09) |
| Section 2.9 camera_settings DDL | `pan_tilt_speed`, `zoom_speed` 컬럼 삭제, `tracking` 컬럼 추가, `enum_tracking_status` 타입 추가 |
| Section 2.9 필드 정의 테이블 | `pan_tilt_speed`, `zoom_speed` 행 삭제, `tracking` 행 추가 |
| Section 9 Enum | 9.39 `EnumTrackingStatus` 섹션 추가 (ACTIVE, LOST, IDLE) |
| TOC | 9.39 추가 |
| Section 13 변경 이력 | v2.9 엔트리에 tracking 변경 내용 추가 |

### 7.2 GOP_Restful_Api_연동설계.md (v3.7 유지 — 같은 날 변경 통합)

| 위치 | 작업 |
|------|------|
| 버전/날짜 | v3.7 유지 (2026-02-09) |
| Section 4.9 Enum 정의 | `EnumTrackingStatus` 추가 |
| Section 5.3.7 GET 응답 | `pan_tilt_speed`, `zoom_speed` 삭제, `tracking` 추가 |
| Section 5.3.8 PATCH 요청/응답 | `pan_tilt_speed`, `zoom_speed` 삭제, `tracking` 추가 |
| Section 5.3.9 PUT 요청/응답 | `pan_tilt_speed`, `zoom_speed` 삭제, `tracking` 추가 |
| 부록 변경이력 | v3.7 엔트리에 tracking 변경 내용 추가 |

> **문서 규칙**:
> - 해당하는 항목 위치의 내용을 업데이트 또는 추가
> - 삭제된 필드는 문서에서도 삭제
> - 문서 초반 날짜/버전 갱신
> - 부록 변경이력에 동일 날짜·동일 버전으로 묶어 정리
> - PRD 참조 문구 제외

---

## 8. 수정 대상 파일 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| **수정** | `app/utils/enums.py` | `EnumTrackingStatus` 추가 |
| **수정** | `app/models/device_setting.py` | `pan_tilt_speed`, `zoom_speed` 삭제, `tracking` 추가 |
| **수정** | `app/schemas/device_setting.py` | Create/Update/Response 3개 스키마 필드 변경 |
| **수정** | `app/utils/init_sample_data.py` | 샘플 데이터 preset 수정 |
| **수정** | `tests/test_device_setting_model.py` | 모델 테스트 (컬럼 수 15→14, 필드 검증) |
| **수정** | `tests/test_device_setting_schema.py` | 스키마 테스트 (speed 범위 → tracking Enum) |
| **수정** | `tests/test_camera_settings_router.py` | 라우터 테스트 (GET/PATCH/PUT 응답 필드) |
| **수정** | `docs/GOP_스키마_전체.md` | v2.9 통합: DDL, 필드, Enum, 변경이력 |
| **수정** | `docs/GOP_Restful_Api_연동설계.md` | v3.7 통합: Enum, API 3개 섹션, 변경이력 |

---

## 9. TDD 실행 계획

### Phase 1: EnumTrackingStatus 추가 (Structural)

- [ ] 1.1 TEST: EnumTrackingStatus — ACTIVE, LOST, IDLE 3개 값 확인
- [ ] 1.2 IMPL: enums.py에 EnumTrackingStatus 추가
- [ ] 1.3 VERIFY: Enum 테스트 통과

### Phase 2: CameraSetting 모델 변경 (Structural)

- [ ] 2.1 TEST: CameraSetting 모델에서 pan_tilt_speed, zoom_speed 컬럼 없음 확인
- [ ] 2.2 TEST: CameraSetting 모델에 tracking 컬럼 존재, 기본값 IDLE 확인
- [ ] 2.3 TEST: CameraSetting 총 컬럼 수 14개 확인
- [ ] 2.4 IMPL: device_setting.py에서 pan_tilt_speed, zoom_speed 삭제, tracking 추가
- [ ] 2.5 VERIFY: 모델 테스트 통과

### Phase 3: Schema 변경 (Structural)

- [ ] 3.1 TEST: CameraSettingCreate에 tracking(EnumTrackingStatus) required 필드 확인
- [ ] 3.2 TEST: CameraSettingCreate에 pan_tilt_speed, zoom_speed 필드 없음 확인
- [ ] 3.3 TEST: CameraSettingUpdate에 tracking Optional 필드 확인
- [ ] 3.4 TEST: CameraSettingResponse에 tracking 필드, pan_tilt_speed/zoom_speed 없음 확인
- [ ] 3.5 IMPL: device_setting.py 스키마 3개 수정
- [ ] 3.6 VERIFY: 스키마 테스트 통과

### Phase 4: 라우터 테스트 업데이트 (Behavioral)

- [ ] 4.1 TEST: GET 기본값에 tracking="IDLE" 포함, pan_tilt_speed/zoom_speed 없음
- [ ] 4.2 TEST: PATCH tracking="ACTIVE" 부분 수정 확인
- [ ] 4.3 TEST: PATCH 잘못된 tracking 값 → 422 Validation Error
- [ ] 4.4 TEST: PUT 전체 교체 시 tracking 포함 확인
- [ ] 4.5 TEST: PUT tracking 누락 → 422
- [ ] 4.6 IMPL: 기존 테스트 업데이트 (speed 관련 assert 제거, tracking assert 추가)
- [ ] 4.7 VERIFY: 전체 라우터 테스트 통과

### Phase 5: 샘플 데이터 업데이트 (Behavioral)

- [ ] 5.1 IMPL: init_sample_data.py preset에서 speed 제거, tracking 추가
- [ ] 5.2 VERIFY: Import OK

### Phase 6: GOP_스키마_전체.md 업데이트 (v2.9 통합)

- [ ] 6.1 IMPL: Section 2.9 DDL에서 pan_tilt_speed, zoom_speed 삭제, tracking 추가, enum_tracking_status 타입 추가
- [ ] 6.2 IMPL: Section 2.9 필드 정의 테이블 업데이트
- [ ] 6.3 IMPL: Section 9.39 EnumTrackingStatus 추가
- [ ] 6.4 IMPL: TOC에 9.39 추가
- [ ] 6.5 IMPL: Section 13 변경 이력 v2.9 엔트리에 tracking 내용 추가

### Phase 7: GOP_Restful_Api_연동설계.md 업데이트 (v3.7 통합)

- [ ] 7.1 IMPL: Section 4.9에 EnumTrackingStatus 추가
- [ ] 7.2 IMPL: Section 5.3.7 GET 응답에서 speed 삭제, tracking 추가
- [ ] 7.3 IMPL: Section 5.3.8 PATCH 요청/응답에서 speed 삭제, tracking 추가
- [ ] 7.4 IMPL: Section 5.3.9 PUT 요청/응답에서 speed 삭제, tracking 추가
- [ ] 7.5 IMPL: 부록 변경이력 v3.7 엔트리에 tracking 내용 추가

### Phase 8: 최종 검증 및 커밋

- [ ] 8.1 VERIFY: 전체 테스트 수트 통과
- [ ] 8.2 VERIFY: 서버 기동 + Swagger UI에서 tracking Enum 값 확인
- [ ] 8.3 COMMIT (structural): EnumTrackingStatus + CameraSetting 모델/스키마 필드 변경
- [ ] 8.4 COMMIT (behavioral): 라우터 테스트 + 샘플 데이터 업데이트
- [ ] 8.5 COMMIT (docs): 스키마 문서 v2.9 + API 문서 v3.7 통합 업데이트
