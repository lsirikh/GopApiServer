# GOP API Server - TDD Implementation Plan

**Project**: GOP RESTful API Server (FastAPI)
**Methodology**: Test-Driven Development (TDD)
**Reference Documents**:
- PRD.md
- Docs/GOP_Restful_Api_연동설계.md
- Claude.md (TDD principles)

---

## TDD Cycle Rules
- ❌ RED: Write a failing test first
- ✅ GREEN: Implement minimum code to pass the test
- ♻️ REFACTOR: Improve code structure while keeping tests green
- 📝 COMMIT: Only commit when all tests pass

---

## Phase 1: Project Setup & Infrastructure

### 1.1 프로젝트 구조 생성
- [ ] Test: 프로젝트 디렉토리 구조 검증
- [ ] Impl: 기본 디렉토리 구조 생성 (app/, tests/, data/, logs/)
- [ ] Test: requirements.txt 파일 존재 검증
- [ ] Impl: requirements.txt 생성 (fastapi, uvicorn, sqlalchemy, pydantic, etc.)
- [ ] Test: __init__.py 파일들 존재 검증
- [ ] Impl: 필요한 모든 __init__.py 파일 생성

### 1.2 환경 설정
- [ ] Test: .env.example 파일 존재 및 필수 변수 검증
- [ ] Impl: .env.example 파일 생성
- [ ] Test: config.py가 환경 변수를 올바르게 로드하는지 검증
- [ ] Impl: app/config.py 생성 (Pydantic Settings 사용)
- [ ] Test: 환경 변수 기본값 검증
- [ ] Impl: 기본값 설정 추가

### 1.3 데이터베이스 연결
- [ ] Test: database.py가 SQLite 연결을 생성하는지 검증
- [ ] Impl: app/database.py 생성 (SQLAlchemy engine, SessionLocal)
- [ ] Test: 데이터베이스 파일이 생성되는지 검증
- [ ] Impl: 데이터베이스 초기화 로직 추가
- [ ] Test: get_db() 의존성이 세션을 반환하는지 검증
- [ ] Impl: app/dependencies.py에 get_db() 구현

---

## Phase 2: Enum 및 공통 스키마

### 2.1 Enum 정의
- [ ] Test: EnumDeviceType이 모든 값을 포함하는지 검증
- [ ] Impl: app/utils/enums.py에 EnumDeviceType 생성
- [ ] Test: EnumDeviceStatus가 올바른 값을 가지는지 검증
- [ ] Impl: EnumDeviceStatus 추가
- [ ] Test: EnumCameraMode, EnumCameraType 검증
- [ ] Impl: EnumCameraMode, EnumCameraType 추가
- [ ] Test: EnumEventType, EnumDetectionType 검증
- [ ] Impl: EnumEventType, EnumDetectionType 추가
- [ ] Test: EnumFaultType, EnumTrueFalse 검증
- [ ] Impl: EnumFaultType, EnumTrueFalse 추가

### 2.2 공통 응답 스키마
- [ ] Test: ApiResponse 스키마가 success, message, data 필드를 가지는지 검증
- [ ] Impl: app/schemas/common.py에 ApiResponse 생성
- [ ] Test: ApiErrorResponse 스키마 검증
- [ ] Impl: ApiErrorResponse 추가
- [ ] Test: PaginationMeta 스키마 검증
- [ ] Impl: PaginationMeta 추가
- [ ] Test: ResponseMeta 스키마 검증 (timestamp, request_id)
- [ ] Impl: ResponseMeta 추가

---

## Phase 3: Request/Response 추적 및 로깅 시스템

### 3.1 Request ID 미들웨어
- [ ] Test: Request에 X-Request-ID 헤더가 없으면 자동 생성되는지 검증
- [ ] Impl: app/middleware/request_id.py 생성
- [ ] Test: X-Request-ID가 이미 있으면 그대로 사용하는지 검증
- [ ] Impl: 조건부 UUID 생성 로직 추가
- [ ] Test: Response에 X-Request-ID 헤더가 포함되는지 검증
- [ ] Impl: Response 헤더 추가 로직

### 3.2 Client UUID 추적
- [ ] Test: X-Client-UUID 헤더를 읽을 수 있는지 검증
- [ ] Impl: 헤더 추출 유틸리티 함수 생성
- [ ] Test: Client UUID가 로그에 포함되는지 검증
- [ ] Impl: 로깅 컨텍스트에 Client UUID 추가

### 3.3 API 로깅 시스템
- [ ] Test: API 요청이 로그 DB에 기록되는지 검증
- [ ] Impl: app/models/log.py에 ApiLog 모델 생성
- [ ] Test: 로그 포맷이 올바른지 검증 (ISO 8601: yyyy-MM-ddTHH:mm:ss.fff)
- [ ] Impl: datetime 필드 추가
- [ ] Test: 로그에 resource, method, client_uuid, request_id가 저장되는지 검증
- [ ] Impl: 로그 모델 필드 완성
- [ ] Test: 로그에 상세 작업 설명이 포함되는지 검증 (예: "제어기 생성")
- [ ] Impl: description 필드 및 생성 로직 추가
- [ ] Test: 로깅 미들웨어가 모든 요청을 기록하는지 검증
- [ ] Impl: app/middleware/logging.py 생성

### 3.4 로그 조회 API
- [ ] Test: GET /api/logs 엔드포인트가 존재하는지 검증
- [ ] Impl: app/routers/logs.py 생성
- [ ] Test: 로그 목록이 페이징되어 반환되는지 검증
- [ ] Impl: 페이징 로직 추가
- [ ] Test: 날짜 범위로 로그 필터링이 가능한지 검증 (start_date, end_date)
- [ ] Impl: 날짜 필터링 로직 추가
- [ ] Test: Method로 로그 필터링이 가능한지 검증 (GET, POST, etc.)
- [ ] Impl: method 필터링 추가
- [ ] Test: Resource로 로그 필터링이 가능한지 검증 (controllers, sensors, etc.)
- [ ] Impl: resource 필터링 추가
- [ ] Test: Client UUID로 로그 검색이 가능한지 검증
- [ ] Impl: client_uuid 필터링 추가

---

## Phase 4: 인증 시스템

### 4.1 User 모델
- [ ] Test: User 모델이 username, hashed_password, role 필드를 가지는지 검증
- [ ] Impl: app/models/user.py 생성
- [ ] Test: User 테이블이 데이터베이스에 생성되는지 검증
- [ ] Impl: SQLAlchemy 모델 정의 완성

### 4.2 User 스키마
- [ ] Test: UserCreate 스키마가 username, password를 받는지 검증
- [ ] Impl: app/schemas/user.py에 UserCreate 생성
- [ ] Test: UserResponse 스키마가 비밀번호를 포함하지 않는지 검증
- [ ] Impl: UserResponse 스키마 생성
- [ ] Test: Token 스키마 검증
- [ ] Impl: Token, TokenData 스키마 추가

### 4.3 비밀번호 해싱
- [ ] Test: 비밀번호가 bcrypt로 해싱되는지 검증
- [ ] Impl: app/utils/auth.py에 hash_password() 함수 추가
- [ ] Test: 해싱된 비밀번호 검증이 동작하는지 검증
- [ ] Impl: verify_password() 함수 추가

### 4.4 JWT 토큰 생성
- [ ] Test: JWT 토큰이 생성되는지 검증
- [ ] Impl: create_access_token() 함수 추가
- [ ] Test: 토큰에 username과 만료시간이 포함되는지 검증
- [ ] Impl: JWT payload 설정
- [ ] Test: 토큰 디코딩이 동작하는지 검증
- [ ] Impl: decode_token() 함수 추가
- [ ] Test: 만료된 토큰이 거부되는지 검증
- [ ] Impl: 토큰 만료 검증 로직 추가

### 4.5 로그인 API
- [ ] Test: POST /api/auth/login 엔드포인트가 존재하는지 검증
- [ ] Impl: app/routers/auth.py 생성 및 라우터 등록
- [ ] Test: 올바른 자격증명으로 로그인 시 토큰을 반환하는지 검증
- [ ] Impl: 로그인 로직 구현
- [ ] Test: 잘못된 자격증명으로 401을 반환하는지 검증
- [ ] Impl: 에러 처리 추가
- [ ] Test: 응답 형식이 {access_token, token_type}인지 검증
- [ ] Impl: 응답 스키마 설정

### 4.6 현재 사용자 조회 API
- [ ] Test: GET /api/auth/me가 인증된 사용자 정보를 반환하는지 검증
- [ ] Impl: get_current_user 의존성 및 엔드포인트 추가
- [ ] Test: 토큰 없이 접근 시 401을 반환하는지 검증
- [ ] Impl: 인증 검증 로직 추가

### 4.7 초기 관리자 계정
- [ ] Test: 서버 시작 시 admin 계정이 없으면 생성되는지 검증
- [ ] Impl: app/utils/init_db.py에 초기화 스크립트 추가
- [ ] Test: admin 계정으로 로그인이 가능한지 검증
- [ ] Impl: 초기 비밀번호 설정 (admin123)

### 4.8 인증 모드 전환
- [ ] Test: AUTH_MODE=token일 때 인증이 필수인지 검증
- [ ] Impl: get_current_user_optional() 의존성 함수 추가
- [ ] Test: AUTH_MODE=public일 때 인증 없이 접근 가능한지 검증
- [ ] Impl: 조건부 인증 로직 추가 (config 기반)

---

## Phase 5: Device API - Controller

### 5.1 Controller 모델
- [ ] Test: Controller 모델이 필수 필드를 가지는지 검증
- [ ] Impl: app/models/device.py에 Controller 모델 생성
- [ ] Test: created_at, updated_at이 자동 설정되는지 검증
- [ ] Impl: timestamp 필드 추가 (default, onupdate)
- [ ] Test: 테이블 이름이 'controllers'인지 검증
- [ ] Impl: __tablename__ 설정

### 5.2 Controller 스키마
- [ ] Test: ControllerCreate 스키마가 필수 필드를 요구하는지 검증
- [ ] Impl: app/schemas/device.py에 ControllerCreate 생성
- [ ] Test: ControllerResponse 스키마가 모든 필드를 포함하는지 검증
- [ ] Impl: ControllerResponse 추가
- [ ] Test: ControllerUpdate 스키마의 모든 필드가 Optional인지 검증
- [ ] Impl: ControllerUpdate 추가 (PATCH용)
- [ ] Test: Enum 필드가 문자열로 직렬화되는지 검증
- [ ] Impl: Enum 직렬화 설정

### 5.3 Controller Repository
- [ ] Test: create_controller()가 컨트롤러를 저장하고 반환하는지 검증
- [ ] Impl: app/repositories/device_repository.py 생성
- [ ] Test: get_controller_by_id()가 컨트롤러를 반환하는지 검증
- [ ] Impl: get_controller_by_id() 추가
- [ ] Test: get_controller_by_id()가 없는 ID에 대해 None을 반환하는지 검증
- [ ] Impl: 조회 로직 완성
- [ ] Test: get_controllers()가 목록을 반환하는지 검증
- [ ] Impl: get_controllers() 추가
- [ ] Test: 페이징이 동작하는지 검증 (skip, limit)
- [ ] Impl: 페이징 로직 추가
- [ ] Test: group_device 필터가 동작하는지 검증
- [ ] Impl: 필터링 로직 추가
- [ ] Test: status 필터가 동작하는지 검증
- [ ] Impl: status 필터링 추가
- [ ] Test: update_controller()가 수정하는지 검증
- [ ] Impl: update_controller() 추가
- [ ] Test: delete_controller()가 삭제하는지 검증
- [ ] Impl: delete_controller() 추가
- [ ] Test: count_controllers()가 총 개수를 반환하는지 검증
- [ ] Impl: count 쿼리 추가

### 5.4 Controller Service
- [ ] Test: Service가 Repository를 호출하는지 검증
- [ ] Impl: app/services/device_service.py 생성
- [ ] Test: 중복 number_device 체크가 동작하는지 검증
- [ ] Impl: 비즈니스 로직 추가

### 5.5 Controller API - 목록 조회
- [ ] Test: GET /api/devices/controllers가 빈 배열을 반환하는지 검증
- [ ] Impl: app/routers/controllers.py 생성 및 엔드포인트 추가
- [ ] Test: 페이징 파라미터가 동작하는지 검증 (page=1, limit=20)
- [ ] Impl: 페이징 로직 추가
- [ ] Test: 응답에 pagination 객체가 포함되는지 검증
- [ ] Impl: PaginationMeta 응답 추가
- [ ] Test: 필터링 파라미터가 동작하는지 검증 (group_device, status)
- [ ] Impl: 필터링 로직 추가
- [ ] Test: include_sensors=true일 때 센서 목록이 포함되는지 검증
- [ ] Impl: 센서 목록 포함 로직 추가 (일단 빈 배열)
- [ ] Test: 응답 형식이 ApiResponse 형태인지 검증
- [ ] Impl: 응답 래핑

### 5.6 Controller API - 단일 조회
- [ ] Test: GET /api/devices/controllers/{id}가 404를 반환하는지 검증 (존재하지 않는 경우)
- [ ] Impl: get_controller 엔드포인트 추가
- [ ] Test: 존재하는 컨트롤러가 반환되는지 검증
- [ ] Impl: 조회 로직 추가
- [ ] Test: include_sensors 파라미터가 동작하는지 검증
- [ ] Impl: 센서 포함 로직 추가

### 5.7 Controller API - 생성
- [ ] Test: POST /api/devices/controllers가 201을 반환하는지 검증
- [ ] Impl: create_controller 엔드포인트 추가
- [ ] Test: 생성된 데이터가 올바른지 검증 (id, created_at 포함)
- [ ] Impl: 생성 로직 완성
- [ ] Test: 유효하지 않은 데이터로 422를 반환하는지 검증
- [ ] Impl: Pydantic 검증 활용
- [ ] Test: 중복 number_device로 409를 반환하는지 검증
- [ ] Impl: 중복 체크 로직 추가

### 5.8 Controller API - 부분 수정
- [ ] Test: PATCH /api/devices/controllers/{id}가 200을 반환하는지 검증
- [ ] Impl: update_controller 엔드포인트 추가
- [ ] Test: 일부 필드만 수정되는지 검증
- [ ] Impl: 부분 업데이트 로직 추가 (exclude_unset=True)
- [ ] Test: 존재하지 않는 ID로 404를 반환하는지 검증
- [ ] Impl: 에러 처리 추가

### 5.9 Controller API - 전체 수정
- [ ] Test: PUT /api/devices/controllers/{id}가 200을 반환하는지 검증
- [ ] Impl: replace_controller 엔드포인트 추가
- [ ] Test: 모든 필드가 교체되는지 검증
- [ ] Impl: 전체 업데이트 로직 추가

### 5.10 Controller API - 삭제
- [ ] Test: DELETE /api/devices/controllers/{id}가 200을 반환하는지 검증
- [ ] Impl: delete_controller 엔드포인트 추가
- [ ] Test: 삭제 후 조회 시 404를 반환하는지 검증
- [ ] Impl: 삭제 로직 완성
- [ ] Test: 응답에 deleted: true, id가 포함되는지 검증
- [ ] Impl: 응답 형식 설정

---

## Phase 6: Device API - Sensor

### 6.1 Sensor 모델
- [ ] Test: Sensor 모델이 controller_id FK를 가지는지 검증
- [ ] Impl: app/models/device.py에 Sensor 모델 추가
- [ ] Test: Controller와의 관계가 설정되는지 검증 (relationship)
- [ ] Impl: SQLAlchemy relationship 추가

### 6.2 Sensor 스키마
- [ ] Test: SensorCreate 스키마가 controller_id를 요구하는지 검증
- [ ] Impl: app/schemas/device.py에 Sensor 스키마 추가
- [ ] Test: SensorResponse가 controller 정보를 포함할 수 있는지 검증
- [ ] Impl: nested ControllerResponse 추가 (optional)

### 6.3 Sensor Repository
- [ ] Test: create_sensor()가 센서를 저장하는지 검증
- [ ] Impl: device_repository.py에 Sensor CRUD 추가
- [ ] Test: get_sensors_by_controller()가 특정 컨트롤러의 센서를 반환하는지 검증
- [ ] Impl: 컨트롤러별 센서 조회 로직 추가
- [ ] Test: 유효하지 않은 controller_id로 센서 생성 시 에러 검증
- [ ] Impl: FK 제약 조건 처리

### 6.4 Sensor API - 목록 조회
- [ ] Test: GET /api/devices/sensors가 빈 배열을 반환하는지 검증
- [ ] Impl: app/routers/sensors.py 생성
- [ ] Test: controller_id 필터링이 동작하는지 검증
- [ ] Impl: 필터링 파라미터 추가
- [ ] Test: type_device 필터링이 동작하는지 검증
- [ ] Impl: 타입 필터링 추가
- [ ] Test: include_controller=true일 때 컨트롤러 정보가 포함되는지 검증
- [ ] Impl: 컨트롤러 정보 포함 로직 추가

### 6.5 Sensor API - 나머지 CRUD
- [ ] Test: GET /api/devices/sensors/{id} 검증
- [ ] Impl: 단일 조회 추가
- [ ] Test: POST /api/devices/sensors 검증
- [ ] Impl: 생성 로직 추가
- [ ] Test: PATCH /api/devices/sensors/{id} 검증
- [ ] Impl: 수정 로직 추가
- [ ] Test: PUT /api/devices/sensors/{id} 검증
- [ ] Impl: 전체 수정 추가
- [ ] Test: DELETE /api/devices/sensors/{id} 검증
- [ ] Impl: 삭제 로직 추가

---

## Phase 7: Device API - Camera

### 7.1 Camera 모델
- [ ] Test: Camera 모델이 카메라 전용 필드를 가지는지 검증 (rtsp_uri, mode, category)
- [ ] Impl: app/models/device.py에 Camera 모델 추가
- [ ] Test: user_password 필드가 존재하는지 검증
- [ ] Impl: 필드 추가 완료

### 7.2 Camera 스키마
- [ ] Test: CameraCreate 스키마가 카메라 필수 필드를 요구하는지 검증
- [ ] Impl: app/schemas/device.py에 Camera 스키마 추가
- [ ] Test: CameraListResponse에서 비밀번호가 마스킹되는지 검증 (*******)
- [ ] Impl: password 마스킹 로직 추가 (validator)
- [ ] Test: CameraDetailResponse에서 비밀번호가 평문으로 반환되는지 검증
- [ ] Impl: 상세 조회용 스키마 분리

### 7.3 Camera Repository
- [ ] Test: create_camera() 검증
- [ ] Impl: device_repository.py에 Camera CRUD 추가
- [ ] Test: mode, category 필터링 검증
- [ ] Impl: 필터링 로직 추가

### 7.4 Camera API - 전체 CRUD
- [ ] Test: GET /api/devices/cameras 검증 (비밀번호 마스킹)
- [ ] Impl: app/routers/cameras.py 생성
- [ ] Test: GET /api/devices/cameras/{id} 검증 (비밀번호 평문)
- [ ] Impl: 단일 조회 (비밀번호 포함)
- [ ] Test: POST /api/devices/cameras 검증
- [ ] Impl: 생성 로직
- [ ] Test: PATCH /api/devices/cameras/{id} 검증
- [ ] Impl: 수정 로직
- [ ] Test: PUT /api/devices/cameras/{id} 검증
- [ ] Impl: 전체 수정
- [ ] Test: DELETE /api/devices/cameras/{id} 검증
- [ ] Impl: 삭제 로직

---

## Phase 8: Event API - Detection Event

### 8.1 Detection Event 모델
- [ ] Test: DetectionEvent 모델이 필수 필드를 가지는지 검증
- [ ] Impl: app/models/event.py 생성 및 DetectionEvent 추가
- [ ] Test: device_id FK가 설정되는지 검증
- [ ] Impl: Device와의 관계 설정
- [ ] Test: result 필드가 EnumDetectionType인지 검증
- [ ] Impl: Enum 필드 추가

### 8.2 Detection Event 스키마
- [ ] Test: DetectionEventCreate 스키마 검증
- [ ] Impl: app/schemas/event.py 생성
- [ ] Test: DetectionEventResponse가 device 정보를 포함할 수 있는지 검증
- [ ] Impl: nested device 스키마 추가

### 8.3 Detection Event Repository
- [ ] Test: create_detection_event() 검증
- [ ] Impl: app/repositories/event_repository.py 생성
- [ ] Test: get_detection_events()가 목록을 반환하는지 검증
- [ ] Impl: 목록 조회 추가
- [ ] Test: 날짜 범위 조회가 동작하는지 검증 (start_date, end_date)
- [ ] Impl: 날짜 필터링 로직 추가
- [ ] Test: status 필터링 검증
- [ ] Impl: status 필터링 추가

### 8.4 Detection Event API
- [ ] Test: GET /api/events/detections 검증
- [ ] Impl: app/routers/detections.py 생성
- [ ] Test: POST /api/events/detections 검증
- [ ] Impl: 생성 로직
- [ ] Test: GET /api/events/detections/{id} 검증
- [ ] Impl: 단일 조회
- [ ] Test: PATCH /api/events/detections/{id} 검증
- [ ] Impl: 수정 로직
- [ ] Test: DELETE /api/events/detections/{id} 검증
- [ ] Impl: 삭제 로직

---

## Phase 9: Event API - Malfunction Event

### 9.1 Malfunction Event 모델
- [ ] Test: MalfunctionEvent 모델이 장애 전용 필드를 가지는지 검증 (reason, first_start, etc.)
- [ ] Impl: app/models/event.py에 MalfunctionEvent 추가

### 9.2 Malfunction Event 스키마
- [ ] Test: MalfunctionEventCreate 스키마 검증
- [ ] Impl: app/schemas/event.py에 추가

### 9.3 Malfunction Event API
- [ ] Test: GET /api/events/malfunctions 검증
- [ ] Impl: app/routers/malfunctions.py 생성
- [ ] Test: POST /api/events/malfunctions 검증
- [ ] Impl: CRUD 구현
- [ ] Test: reason 필터링 검증
- [ ] Impl: 필터링 추가

---

## Phase 10: Event API - Connection Event

### 10.1 Connection Event 모델
- [ ] Test: ConnectionEvent 모델 검증
- [ ] Impl: app/models/event.py에 ConnectionEvent 추가

### 10.2 Connection Event 스키마
- [ ] Test: ConnectionEventCreate 스키마 검증
- [ ] Impl: app/schemas/event.py에 추가

### 10.3 Connection Event API
- [ ] Test: GET /api/events/connections 검증
- [ ] Impl: app/routers/connections.py 생성
- [ ] Test: POST /api/events/connections 검증
- [ ] Impl: CRUD 구현

---

## Phase 11: Event API - Action Event

### 11.1 Action Event 모델
- [ ] Test: ActionEvent 모델이 content, user 필드를 가지는지 검증
- [ ] Impl: app/models/event.py에 ActionEvent 추가
- [ ] Test: from_event_id, from_event_type 필드 검증 (다형성 참조)
- [ ] Impl: 원본 이벤트 참조 필드 추가

### 11.2 Action Event 스키마
- [ ] Test: ActionEventCreate 스키마 검증 (content, user, from_event_id)
- [ ] Impl: app/schemas/event.py에 추가

### 11.3 Action Event API
- [ ] Test: GET /api/events/actions 검증
- [ ] Impl: app/routers/actions.py 생성
- [ ] Test: POST /api/events/actions 검증
- [ ] Impl: CRUD 구현
- [ ] Test: from_event_id로 원본 이벤트 연결 검증
- [ ] Impl: 이벤트 연결 로직

---

## Phase 12: Main Application 통합

### 12.1 FastAPI 앱 생성
- [ ] Test: FastAPI 앱이 생성되는지 검증
- [ ] Impl: app/main.py 생성
- [ ] Test: 앱 title, description, version이 설정되는지 검증
- [ ] Impl: OpenAPI 메타데이터 설정
- [ ] Test: CORS 미들웨어가 설정되는지 검증
- [ ] Impl: CORS 설정 추가
- [ ] Test: 모든 라우터가 등록되는지 검증
- [ ] Impl: include_router() 호출 (auth, controllers, sensors, etc.)

### 12.2 미들웨어 등록
- [ ] Test: Request ID 미들웨어가 동작하는지 검증
- [ ] Impl: app.add_middleware() 추가
- [ ] Test: 로깅 미들웨어가 동작하는지 검증
- [ ] Impl: 로깅 미들웨어 등록
- [ ] Test: 미들웨어 순서가 올바른지 검증
- [ ] Impl: 미들웨어 순서 조정

### 12.3 시작 및 종료 이벤트
- [ ] Test: 시작 시 데이터베이스 테이블이 생성되는지 검증
- [ ] Impl: @app.on_event("startup") 추가
- [ ] Test: 시작 시 초기 admin 계정이 생성되는지 검증
- [ ] Impl: init_db() 호출
- [ ] Test: 종료 시 리소스가 정리되는지 검증
- [ ] Impl: @app.on_event("shutdown") 추가

### 12.4 Health Check
- [ ] Test: GET /health가 200을 반환하는지 검증
- [ ] Impl: health check 엔드포인트 추가
- [ ] Test: GET /api/health가 DB 연결 상태를 반환하는지 검증
- [ ] Impl: DB health check 추가

### 12.5 OpenAPI 문서화
- [ ] Test: GET /docs가 접근 가능한지 검증
- [ ] Impl: Swagger UI 확인
- [ ] Test: GET /redoc이 접근 가능한지 검증
- [ ] Impl: ReDoc 확인
- [ ] Test: GET /openapi.json이 스펙을 반환하는지 검증
- [ ] Impl: OpenAPI 스펙 확인
- [ ] Test: 각 엔드포인트에 설명이 있는지 검증
- [ ] Impl: docstring 및 description 추가

---

## Phase 13: Docker 배포

### 13.1 Dockerfile
- [ ] Test: Dockerfile이 존재하는지 검증
- [ ] Impl: Dockerfile 생성
- [ ] Test: 이미지가 빌드되는지 검증
- [ ] Impl: docker build 테스트
- [ ] Test: 컨테이너가 실행되는지 검증
- [ ] Impl: docker run 테스트

### 13.2 Docker Compose
- [ ] Test: docker-compose.yml이 존재하는지 검증
- [ ] Impl: docker-compose.yml 생성
- [ ] Test: docker-compose up이 동작하는지 검증
- [ ] Impl: 서비스 설정 완료
- [ ] Test: 포트 8000이 매핑되는지 검증
- [ ] Impl: ports 설정 확인
- [ ] Test: 볼륨 마운트가 동작하는지 검증 (data, logs)
- [ ] Impl: volumes 설정 확인
- [ ] Test: 환경 변수가 전달되는지 검증
- [ ] Impl: environment 설정

### 13.3 .dockerignore
- [ ] Test: .dockerignore 파일이 존재하는지 검증
- [ ] Impl: .dockerignore 생성 (__pycache__, .env, etc.)

---

## Phase 14: 통합 테스트

### 14.1 인증 플로우 테스트
- [ ] Test: 로그인 → 토큰 발급 → API 호출 전체 플로우 검증
- [ ] Impl: tests/integration/test_auth_flow.py 작성

### 14.2 Device CRUD 플로우 테스트
- [ ] Test: Controller 생성 → Sensor 생성 → 연결 검증 → 조회
- [ ] Impl: tests/integration/test_device_flow.py 작성

### 14.3 Event 플로우 테스트
- [ ] Test: Detection 이벤트 생성 → Action 이벤트 생성 → 연결 검증
- [ ] Impl: tests/integration/test_event_flow.py 작성

### 14.4 로깅 플로우 테스트
- [ ] Test: API 호출 → 로그 생성 → 로그 조회 검증
- [ ] Impl: tests/integration/test_logging_flow.py 작성

### 14.5 인증 모드 전환 테스트
- [ ] Test: AUTH_MODE=public일 때 인증 없이 접근 가능한지 검증
- [ ] Impl: 환경 변수 변경 테스트
- [ ] Test: AUTH_MODE=token일 때 인증 필수인지 검증
- [ ] Impl: 인증 모드 테스트

---

## Phase 15: 문서화 및 배포 준비

### 15.1 README.md
- [ ] Test: README.md가 프로젝트 설명을 포함하는지 검증
- [ ] Impl: README.md 작성
- [ ] Test: 설치 방법이 명확한지 검증
- [ ] Impl: Installation 섹션 추가
- [ ] Test: 실행 방법이 포함되는지 검증
- [ ] Impl: Usage 섹션 추가

### 15.2 API 사용 예제
- [ ] Test: examples/ 디렉토리가 존재하는지 검증
- [ ] Impl: examples/ 디렉토리 생성
- [ ] Test: curl 예제가 포함되는지 검증
- [ ] Impl: curl_examples.md 작성
- [ ] Test: Python 클라이언트 예제가 있는지 검증
- [ ] Impl: python_client_example.py 작성

### 15.3 배포 가이드
- [ ] Test: DEPLOYMENT.md가 존재하는지 검증
- [ ] Impl: 배포 문서 작성
- [ ] Test: 환경 변수 설명이 포함되는지 검증
- [ ] Impl: 환경 변수 테이블 추가
- [ ] Test: Docker 배포 가이드가 명확한지 검증
- [ ] Impl: Docker 배포 스텝 작성

---

## Commit Strategy

### Structural Changes (구조적 변경)
```
refactor: extract method for [function]
refactor: rename [old] to [new]
refactor: move [component] to [new location]
```

### Behavioral Changes (기능 변경)
```
test: add test for [feature]
feat: implement [feature]
fix: resolve [issue]
```

### Commit Timing
- 테스트 작성 후 커밋
- 구현 완료 후 커밋
- 리팩토링 후 커밋 (별도 커밋)
- 항상 모든 테스트가 통과한 상태에서만 커밋

---

## Progress Tracking

**Current Phase**: Phase 1 - Project Setup
**Next Test**: 프로젝트 디렉토리 구조 검증
**Status**: 🔴 Ready to start

---

## Notes

- 각 테스트는 독립적으로 실행 가능해야 함
- 테스트 실패 시 다음 단계로 넘어가지 않음
- 리팩토링은 모든 테스트가 통과한 후에만 수행
- 커밋은 항상 Green 상태에서만 수행
- Long-running 테스트는 별도 마킹하여 일반 테스트 실행 시 제외

---

**Remember**: Red → Green → Refactor → Commit

**When I say "go"**: Find the next unmarked test in this plan, implement the test, then implement only enough code to make that test pass.