# PRD: 하위 테이블 SYNC 트리거 추가

**문서 버전**: v1.0
**작성일**: 2026-03-07
**상태**: Draft
**참조 문서**: `Gop_Message_Broker_연동설계.md` v1.3 (Section 9.5, 9.6, 9.7)
**관련 코드**: `app/db_triggers.py`

---

## 1. 개요

### 1.1 문제

`Gop_Message_Broker_연동설계.md`에서 다음과 같이 명시하고 있으나, 현재 하위 테이블에 대한 pg_notify 트리거가 누락되어 있다:

- **Section 9.5**: "DeviceGroup CRUD 발생 시 **또는 장비 할당/제거 시**" → `device_group_mappings` 트리거 없음
- **Section 9.6**: "EventMapping CRUD 발생 시 **또는 Camera/Speaker/Lamp 매핑 변경 시**" → `event_mapping_cameras`, `event_mapping_speakers`, `event_mapping_lamps` 트리거 없음
- **Section 9.7**: "CameraPreset CRUD 발생 시 **또는 ROI 변경 시**" → `rois` 트리거 없음

### 1.2 결과

하위 테이블만 변경될 때(예: 이벤트 매핑에 카메라 추가/삭제) NATS 알림이 발행되지 않아, 서브시스템 캐시가 갱신되지 않는다.

### 1.3 해결 방법

하위 테이블 변경 시 **부모 리소스의 SYNC cmd**를 발행한다. 별도 cmd를 추가하지 않고, 부모의 `resource_id`를 payload에 포함하여 기존 설계와 일관성을 유지한다.

---

## 2. 변경 대상

### 2.1 추가할 트리거 목록

| 하위 테이블 | FK 컬럼 | 발행할 cmd | resource_id 출처 | 비고 |
|---|---|---|---|---|
| `event_mapping_cameras` | `event_mapping_id` | `SYNC_EVENT_MAPPING` | `event_mapping_id` | 카메라 연동 추가/수정/삭제 |
| `event_mapping_speakers` | `event_mapping_id` | `SYNC_EVENT_MAPPING` | `event_mapping_id` | 스피커 연동 추가/수정/삭제 |
| `event_mapping_lamps` | `event_mapping_id` | `SYNC_EVENT_MAPPING` | `event_mapping_id` | 램프 연동 추가/수정/삭제 |
| `device_group_mappings` | `group_id` | `SYNC_DEVICE_GROUP` | `group_id` | 장비↔그룹 할당/제거 |
| `rois` | `preset_id` | `SYNC_PRESET` | `preset_id` | ROI 추가/수정/삭제 |

### 2.2 설계 핵심

- 하위 테이블의 `id`가 아닌 **부모 FK 컬럼 값**을 `resource_id`로 사용
- 서브시스템은 기존 SYNC 메시지와 동일하게 부모 리소스를 REST API로 재조회
- 별도 cmd/Subject 추가 없음 — 기존 인프라 변경 불필요

---

## 3. 트리거 함수 변경

### 3.1 fn_notify_gop_sync() 분기 추가

현재 함수의 `ELSIF` 체인에 하위 테이블 분기를 추가한다. 하위 테이블은 자신의 `id`가 아닌 부모 FK 값을 `resource_id`로 사용해야 하므로, 별도 분기가 필요하다.

```sql
-- event_mapping 하위 테이블 (cameras, speakers, lamps)
ELSIF TG_TABLE_NAME IN ('event_mapping_cameras', 'event_mapping_speakers', 'event_mapping_lamps') THEN
    IF TG_OP = 'DELETE' THEN
        resource_id := OLD.event_mapping_id;
    ELSE
        resource_id := NEW.event_mapping_id;
    END IF;
    payload := jsonb_build_object(
        'cmd', 'SYNC_EVENT_MAPPING',
        'action', 'UPDATED',
        'resource_id', resource_id
    );

-- device_group_mappings (장비↔그룹 할당)
ELSIF TG_TABLE_NAME = 'device_group_mappings' THEN
    IF TG_OP = 'DELETE' THEN
        resource_id := OLD.group_id;
    ELSE
        resource_id := NEW.group_id;
    END IF;
    payload := jsonb_build_object(
        'cmd', 'SYNC_DEVICE_GROUP',
        'action', 'UPDATED',
        'resource_id', resource_id
    );

-- rois (카메라 프리셋 ROI)
ELSIF TG_TABLE_NAME = 'rois' THEN
    IF TG_OP = 'DELETE' THEN
        resource_id := OLD.preset_id;
    ELSE
        resource_id := NEW.preset_id;
    END IF;
    payload := jsonb_build_object(
        'cmd', 'SYNC_PRESET',
        'action', 'UPDATED',
        'resource_id', resource_id
    );
```

> **action은 항상 `UPDATED`**: 하위 테이블의 INSERT/DELETE는 부모 리소스 관점에서 "내용 변경(UPDATED)"이므로, 서브시스템은 부모를 다시 조회하면 된다.

### 3.2 트리거 등록 SQL 추가

```sql
DROP TRIGGER IF EXISTS trg_sync_event_mapping_cameras ON event_mapping_cameras;
CREATE TRIGGER trg_sync_event_mapping_cameras
    AFTER INSERT OR UPDATE OR DELETE ON event_mapping_cameras
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

DROP TRIGGER IF EXISTS trg_sync_event_mapping_speakers ON event_mapping_speakers;
CREATE TRIGGER trg_sync_event_mapping_speakers
    AFTER INSERT OR UPDATE OR DELETE ON event_mapping_speakers
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

DROP TRIGGER IF EXISTS trg_sync_event_mapping_lamps ON event_mapping_lamps;
CREATE TRIGGER trg_sync_event_mapping_lamps
    AFTER INSERT OR UPDATE OR DELETE ON event_mapping_lamps
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

DROP TRIGGER IF EXISTS trg_sync_device_group_mappings ON device_group_mappings;
CREATE TRIGGER trg_sync_device_group_mappings
    AFTER INSERT OR UPDATE OR DELETE ON device_group_mappings
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

DROP TRIGGER IF EXISTS trg_sync_rois ON rois;
CREATE TRIGGER trg_sync_rois
    AFTER INSERT OR UPDATE OR DELETE ON rois
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
```

---

## 4. 영향 범위

### 4.1 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/db_triggers.py` | `fn_notify_gop_sync()` 분기 추가 + 트리거 등록 SQL 5개 추가 |

### 4.2 변경하지 않는 것

| 항목 | 이유 |
|------|------|
| `db_monitor/main.py` | 기존 `CMD_TO_SUBJECT` 매핑으로 이미 처리됨 (새 cmd 없음) |
| NATS Subject | 기존 Subject 그대로 사용 |
| 서브시스템 | 기존 SYNC 구독/처리 로직 변경 불필요 |
| `Gop_Message_Broker_연동설계.md` | 설계 문서는 이미 하위 테이블 변경을 포함하고 있음 |

---

## 5. NATS 메시지 예시

### 5.1 이벤트 매핑에 카메라 추가 시

```
API: POST /api/integrations/event-mappings/5/cameras
DB: INSERT INTO event_mapping_cameras (event_mapping_id=5, camera_id=201, ...)
pg_notify: {"cmd": "SYNC_EVENT_MAPPING", "action": "UPDATED", "resource_id": 5}
NATS: sensorway.unit001.all.sync.event-mapping
서브시스템: GET /api/integrations/event-mappings/5 → 캐시 갱신
```

### 5.2 장비 그룹에서 장비 제거 시

```
API: DELETE /api/devices/groups/3/devices/102
DB: DELETE FROM device_group_mappings WHERE group_id=3 AND device_id=102
pg_notify: {"cmd": "SYNC_DEVICE_GROUP", "action": "UPDATED", "resource_id": 3}
NATS: sensorway.unit001.all.sync.device-group
서브시스템: GET /api/devices/groups/3 → 캐시 갱신
```

### 5.3 프리셋 ROI 수정 시

```
API: PATCH /api/devices/cameras/201/presets/1/rois/10
DB: UPDATE rois SET ... WHERE id=10 (preset_id=1)
pg_notify: {"cmd": "SYNC_PRESET", "action": "UPDATED", "resource_id": 1}
NATS: sensorway.unit001.all.sync.preset
서브시스템: GET /api/devices/cameras/201/presets/1 → 캐시 갱신
```

---

## 6. 구현 계획 (TDD)

### Phase 1: 트리거 함수 확장

- [ ] 1.1 TEST: `event_mapping_cameras` INSERT 시 `SYNC_EVENT_MAPPING` pg_notify 발행 확인
- [ ] 1.2 TEST: `event_mapping_cameras` DELETE 시 부모 `event_mapping_id`가 `resource_id`로 전달되는지 확인
- [ ] 1.3 IMPL: `fn_notify_gop_sync()`에 하위 테이블 5개 분기 추가
- [ ] 1.4 IMPL: 트리거 등록 SQL 5개 추가
- [ ] 1.5 TEST: 전체 트리거 함수 SQL에 5개 테이블명 포함 확인

### Phase 2: 통합 검증

- [ ] 2.1 VERIFY: 이벤트 매핑 카메라 추가 → NATS `SYNC_EVENT_MAPPING` 수신
- [ ] 2.2 VERIFY: 장비 그룹 할당 → NATS `SYNC_DEVICE_GROUP` 수신
- [ ] 2.3 VERIFY: ROI 수정 → NATS `SYNC_PRESET` 수신

---

## 7. 트리거 등록 완료 후 전체 목록

| # | 테이블 | 트리거명 | cmd |
|---|--------|---------|-----|
| 1 | `devices` | `trg_sync_devices` | `SYNC_DEVICE` |
| 2 | `servers` | `trg_sync_servers` | `SYNC_SERVER` |
| 3 | `server_categories` | `trg_sync_server_categories` | `SYNC_CATEGORY` |
| 4 | `device_groups` | `trg_sync_device_groups` | `SYNC_DEVICE_GROUP` |
| 5 | `event_mappings` | `trg_sync_event_mappings` | `SYNC_EVENT_MAPPING` |
| 6 | `camera_presets` | `trg_sync_camera_presets` | `SYNC_PRESET` |
| 7 | `file_groups` | `trg_sync_file_groups` | `SYNC_FILE_GROUP` |
| 8 | `camera_settings` | `trg_sync_camera_settings` | `SYNC_CAMERA_SETTING` |
| 9 | `proxy_settings` | `trg_sync_proxy_settings` | `SYNC_PROXY_SETTING` |
| 10 | `event_mapping_cameras` | `trg_sync_event_mapping_cameras` | `SYNC_EVENT_MAPPING` |
| 11 | `event_mapping_speakers` | `trg_sync_event_mapping_speakers` | `SYNC_EVENT_MAPPING` |
| 12 | `event_mapping_lamps` | `trg_sync_event_mapping_lamps` | `SYNC_EVENT_MAPPING` |
| 13 | `device_group_mappings` | `trg_sync_device_group_mappings` | `SYNC_DEVICE_GROUP` |
| 14 | `rois` | `trg_sync_rois` | `SYNC_PRESET` |
