# PRD: Speaker Geolocation 추가

**버전**: v1.0
**작성일**: 2026-01-09
**상태**: Draft

---

## 1. 개요

### 1.1 목적

Speaker 장비에 `geolocation` JSONB 필드를 추가하여 Controller, Sensor, Camera, Enclosure와 동일한 위치 정보 관리 체계를 갖추도록 한다.

### 1.2 배경

현재 Device 계층 구조에서 위치 정보(geolocation) 지원 현황:

| Device Type | geolocation 지원 |
|-------------|------------------|
| Controller | ✅ (v2.4 추가) |
| Sensor | ✅ (v2.4 추가) |
| Camera | ✅ (기존) |
| Enclosure | ✅ (v2.4 추가) |
| **Speaker** | ❌ **미지원** |

Speaker도 GOP 현장에 물리적으로 설치되는 장비이므로 위치 정보 관리가 필요하다.

### 1.3 변경 범위

1. **코드 변경**
   - `app/models/device.py`: Speaker 모델에 geolocation 컬럼 추가
   - `app/schemas/device.py`: SpeakerCreate, SpeakerUpdate, SpeakerResponse에 geolocation 필드 추가
   - `app/routers/speakers.py`: geolocation 처리 로직 추가

2. **문서 변경**
   - `docs/GOP_스키마_전체.md`: speakers 테이블에 geolocation 컬럼 추가
   - `GOP_Restful_Api_연동설계.md`: Speaker API 섹션에 geolocation 필드 추가

---

## 2. 기술 명세

### 2.1 Geolocation JSON 구조

기존 Controller/Sensor/Camera/Enclosure와 동일한 구조 사용:

```json
{
  "location": "GOP 3초소 방송실",
  "latitude": 38.1234,
  "longitude": 127.5678,
  "altitude": 245.5
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| location | string | N | 설치 위치 (최대 500자) |
| latitude | float | N | 위도 (-90.0 ~ 90.0) |
| longitude | float | N | 경도 (-180.0 ~ 180.0) |
| altitude | float | N | 고도 (미터) |

### 2.2 DB 스키마 변경

```sql
-- speakers 테이블에 geolocation 컬럼 추가
ALTER TABLE speakers ADD COLUMN geolocation JSONB;
```

---

## 3. 코드 변경 상세

### 3.1 Model 변경 (`app/models/device.py`)

**Speaker 클래스에 geolocation 컬럼 추가**:

```python
class Speaker(Device):
    __tablename__ = "speakers"

    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    speaker_type = Column(SQLEnum(EnumSpeakerType), nullable=False, default=EnumSpeakerType.NORMAL)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    geolocation = Column(JSON, nullable=True, default=None)  # 신규 추가
```

### 3.2 Schema 변경 (`app/schemas/device.py`)

**SpeakerCreate에 geolocation 필드 추가**:

```python
class SpeakerCreate(BaseModel):
    # 기존 필드들...
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
```

**SpeakerUpdate에 geolocation 필드 추가**:

```python
class SpeakerUpdate(BaseModel):
    # 기존 필드들...
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보 (JSON)")
```

**SpeakerResponse에 geolocation 필드 추가**:

```python
class SpeakerResponse(BaseModel):
    # 기존 필드들...
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보")
```

**SpeakerNestedResponse에 geolocation 필드 추가**:

```python
class SpeakerNestedResponse(BaseModel):
    # 기존 필드들...
    geolocation: Optional[Geolocation] = Field(None, description="좌표/위치 정보")
```

### 3.3 Router 변경 (`app/routers/speakers.py`)

**_speaker_to_response 함수에 geolocation 처리 추가**:

```python
def _speaker_to_response(speaker: Speaker, db: Session) -> SpeakerResponse:
    # 기존 로직...
    return SpeakerResponse(
        # 기존 필드들...
        geolocation=speaker.geolocation  # 신규 추가
    )
```

**POST/PATCH/PUT 핸들러에 geolocation 처리 로직 추가**.

---

## 4. API 변경 상세

### 4.1 Request Body 변경

**POST /api/devices/speakers** (생성):

```json
{
  "number_device": 2401,
  "group_device": 0,
  "name_device": "VCS_2401",
  "type_device": "IpSpeaker",
  "status": "ACTIVATED",
  "speaker_type": "NORMAL",
  "server_id": 1,
  "description": "1구역 스피커",
  "geolocation": {
    "location": "GOP 3초소 방송실",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5
  }
}
```

**PATCH /api/devices/speakers/{id}** (부분 수정):

```json
{
  "geolocation": {
    "location": "GOP 3초소 방송실 (변경)",
    "latitude": 38.1235,
    "longitude": 127.5679
  }
}
```

### 4.2 Response Body 변경

**GET /api/devices/speakers** 및 **GET /api/devices/speakers/{id}**:

```json
{
  "success": true,
  "message": "Speakers retrieved successfully",
  "data": [
    {
      "id": 101,
      "category_device": "speaker",
      "number_device": 2401,
      "group_device": 0,
      "name_device": "VCS_2401",
      "type_device": "IpSpeaker",
      "version": null,
      "status": "ACTIVATED",
      "created_at": "2026-01-07T10:00:00.000000",
      "updated_at": "2026-01-07T10:00:00.000000",
      "speaker_type": "NORMAL",
      "description": "1구역 스피커",
      "geolocation": {
        "location": "GOP 3초소 방송실",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 245.5
      },
      "server": {
        "id": 1,
        "category_id": 10,
        "name": "방송서버-01",
        "status": "NORMAL",
        "ip_address": "192.168.1.100",
        "port": 8080,
        "hostname": "bcast-srv-01",
        "user_name": "admin",
        "user_password": "password123",
        "cpu_usage": 25.5,
        "ram_usage": 40.2,
        "disk_usage": 55.0,
        "network_throughput": "50MB/s"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 35,
    "total_pages": 2
  }
}
```

### 4.3 필드 정의 업데이트

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| number_device | integer | Y | 단말 번호 (NATS device_no 통합) |
| group_device | integer | N | 그룹 번호 (기본값: 0) |
| name_device | string | Y | 장비명 |
| type_device | string | N | EnumDeviceType (기본값: IpSpeaker) |
| status | string | N | EnumDeviceStatus (기본값: ACTIVATED) |
| speaker_type | string | N | EnumSpeakerType (기본값: NORMAL) |
| server_id | integer | N | 방송서버 ID (FK) |
| description | string | N | 설명 |
| **geolocation** | **object** | **N** | **좌표/위치 정보 (JSON, v2.6 신규)** |

---

## 5. 문서 변경 상세

### 5.1 GOP_스키마_전체.md 변경

**2.5 speakers 테이블 섹션 수정**:

1. 변경사항 주석 추가:
   > **v1.9 변경사항**: `geolocation` JSONB 컬럼 추가

2. CREATE TABLE 문에 geolocation 컬럼 추가:
   ```sql
   CREATE TABLE speakers (
       id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,
       speaker_type enum_speaker_type NOT NULL DEFAULT 'NORMAL',
       server_id INTEGER REFERENCES servers(id) ON DELETE SET NULL,
       description VARCHAR(500),
       geolocation JSONB                    -- v1.9: 위치 정보
   );
   ```

3. 필드 정의 테이블에 geolocation 행 추가

4. geolocation JSON 구조 섹션 추가 (Controller/Sensor와 동일)

5. ERD 다이어그램 업데이트 (speakers 박스에 geolocation 추가)

6. 변경 이력에 v1.9 추가

### 5.2 GOP_Restful_Api_연동설계.md 변경

**문서 헤더 업데이트**:
- 최종 수정일: 2026-01-09
- 버전: v2.6

**5.4 Speaker API 섹션 수정**:

1. Response Example에 geolocation 필드 추가

2. Request Body Example에 geolocation 필드 추가

3. 필드 정의 테이블에 geolocation 행 추가

**변경 이력에 v2.6 추가**:

```
| v2.6 | 2026-01-09 | **Speaker Geolocation 추가**<br>- **speakers.geolocation JSONB 추가**: Speaker 장비 위치 정보<br>- **API 변경**: POST/PATCH/PUT Request에 geolocation 필드 추가<br>- **Response 변경**: GET 응답에 geolocation 필드 포함<br>- **Swagger/Docs 업데이트**: SpeakerCreate, SpeakerUpdate, SpeakerResponse 스키마에 geolocation 필드 추가 |
```

---

## 6. Swagger/Docs 자동 반영

FastAPI의 Pydantic 스키마 기반 자동 문서화로 인해, 코드 변경 시 다음 문서가 자동 업데이트됨:

- **Swagger UI** (`/docs`): SpeakerCreate, SpeakerUpdate, SpeakerResponse 스키마에 geolocation 필드 표시
- **ReDoc** (`/redoc`): 동일하게 geolocation 필드 반영
- **OpenAPI JSON** (`/openapi.json`): geolocation 스키마 정의 포함

---

## 7. 구현 체크리스트

### 7.1 코드 변경
- [ ] `app/models/device.py`: Speaker.geolocation 컬럼 추가
- [ ] `app/schemas/device.py`: SpeakerCreate.geolocation 필드 추가
- [ ] `app/schemas/device.py`: SpeakerUpdate.geolocation 필드 추가
- [ ] `app/schemas/device.py`: SpeakerResponse.geolocation 필드 추가
- [ ] `app/schemas/device.py`: SpeakerNestedResponse.geolocation 필드 추가
- [ ] `app/routers/speakers.py`: _speaker_to_response에 geolocation 추가
- [ ] `app/routers/speakers.py`: create_speaker에 geolocation 처리 추가
- [ ] `app/routers/speakers.py`: update_speaker에 geolocation 처리 추가
- [ ] `app/routers/speakers.py`: replace_speaker에 geolocation 처리 추가

### 7.2 문서 변경
- [ ] `docs/GOP_스키마_전체.md`: speakers 테이블 스키마 업데이트
- [ ] `docs/GOP_스키마_전체.md`: geolocation JSON 구조 섹션 추가
- [ ] `docs/GOP_스키마_전체.md`: ERD 다이어그램 업데이트
- [ ] `docs/GOP_스키마_전체.md`: 변경 이력 v1.9 추가
- [ ] `GOP_Restful_Api_연동설계.md`: 문서 버전/날짜 업데이트
- [ ] `GOP_Restful_Api_연동설계.md`: 5.4 Speaker API Response Example 업데이트
- [ ] `GOP_Restful_Api_연동설계.md`: 5.4 Speaker API Request Body 업데이트
- [ ] `GOP_Restful_Api_연동설계.md`: 5.4 Speaker API 필드 정의 테이블 업데이트
- [ ] `GOP_Restful_Api_연동설계.md`: 변경 이력 v2.6 추가

### 7.3 테스트
- [ ] Speaker 생성 테스트 (geolocation 포함)
- [ ] Speaker 수정 테스트 (geolocation 업데이트)
- [ ] Speaker 조회 테스트 (geolocation 반환 확인)
- [ ] Swagger UI 확인 (geolocation 필드 표시)

---

## 8. 예상 영향도

### 8.1 하위 호환성

- **Breaking Change 없음**: geolocation은 Optional 필드이므로 기존 API 호출에 영향 없음
- **기존 데이터**: 기존 Speaker 레코드의 geolocation은 NULL

### 8.2 관련 API

Speaker가 Response에 포함되는 다른 API는 현재 없음 (Speaker는 독립적인 Device).
만약 향후 Event Response에 Speaker가 포함된다면, SpeakerNestedResponse에도 geolocation이 포함됨.

---

**문서 종료**
