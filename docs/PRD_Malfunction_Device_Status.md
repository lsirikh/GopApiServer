# PRD: 이벤트 기반 장비 상태 자동 변경

**Version**: v1.1
**Date**: 2026-03-07
**Status**: Draft

---

## 1. 개요

이벤트 유형에 따라 해당 장비(Device)의 `status`를 자동으로 변경한다.

| 이벤트 | Device.status 변경 |
|--------|-------------------|
| POST Malfunction (장애) | → `ERROR` |
| POST Detection (탐지) | → `ACTIVATED` |
| POST Action (조치) | → `ACTIVATED` |

현재는 이벤트만 기록하고 장비 상태는 그대로 유지되어, 모니터링 화면과 실제 장비 상태가 불일치하는 문제가 있다.

## 2. 현재 동작 (AS-IS)

```
POST /api/events/malfunctions  → MalfunctionEvent 생성, Device.status 변경 없음
POST /api/events/detections    → DetectionEvent 생성, Device.status 변경 없음
POST /api/events/actions       → ActionEvent 생성, Device.status 변경 없음
```

## 3. 변경 후 동작 (TO-BE)

### 3.1 POST /api/events/malfunctions

```
1. device_id로 Device 조회
2. Device.status를 ERROR로 변경
3. MalfunctionEvent 생성 및 DB 저장
4. 단일 트랜잭션으로 commit
5. Response 반환 (device.status = ERROR 반영)
```

### 3.2 POST /api/events/detections

```
1. device_id로 Device 조회
2. Device.status를 ACTIVATED로 변경
3. DetectionEvent 생성 및 DB 저장
4. 단일 트랜잭션으로 commit
5. Response 반환 (device.status = ACTIVATED 반영)
```

탐지 이벤트가 발생했다는 것은 장비가 정상 작동 중이라는 의미이므로 ACTIVATED로 전환한다.

### 3.3 POST /api/events/actions

```
1. from_event_id로 원본 Event 조회
2. 원본 Event의 device_id로 Device 조회
3. Device.status를 ACTIVATED로 변경
4. ActionEvent 생성 및 DB 저장
5. 단일 트랜잭션으로 commit
6. Response 반환 (device.status = ACTIVATED 반영)
```

조치 완료는 장애 해소를 의미하므로 ACTIVATED로 복구한다.
ActionEvent는 `device_id`가 없고 `from_event_id`로 원본 이벤트를 참조하므로, 원본 이벤트의 device_id를 통해 장비를 조회한다.

### 3.4 트랜잭션 원자성

- Device 상태 변경과 이벤트 생성은 **하나의 트랜잭션**으로 처리한다.
- 둘 중 하나라도 실패하면 전체 롤백한다.

## 4. 영향 범위

### 4.1 변경 대상 파일

| 파일 | 변경 내용 |
|------|-----------|
| `app/routers/malfunctions.py` | `create_malfunction_event()` — Device.status = ERROR |
| `app/routers/detections.py` | `create_detection_event()` — Device.status = ACTIVATED |
| `app/routers/actions.py` | `create_action_event()` — 원본 이벤트의 Device.status = ACTIVATED |

### 4.2 변경하지 않는 것

| 항목 | 이유 |
|------|------|
| Device 모델 | `EnumDeviceStatus.ERROR`, `ACTIVATED` 이미 존재 |
| 이벤트 스키마 | 요청/응답 필드 변경 없음 |
| ConnectionEvent 라우터 | 이 PRD 범위 외 (별도 PRD로 확장 가능) |

## 5. 상세 로직

### 5.1 Malfunction — Device.status → ERROR

```python
device = db.query(Device).filter(Device.id == event_data.device_id).first()
if not device:
    raise HTTPException(400, ...)

# 추가
device.status = EnumDeviceStatus.ERROR

new_event = MalfunctionEvent(...)
db.add(new_event)
db.commit()  # Device 상태 변경 + 이벤트 생성 동시 커밋
```

### 5.2 Detection — Device.status → ACTIVATED

```python
device = db.query(Device).filter(Device.id == event_data.device_id).first()
if not device:
    raise HTTPException(400, ...)

# 추가
device.status = EnumDeviceStatus.ACTIVATED

new_event = DetectionEvent(...)
db.add(new_event)
db.commit()
```

### 5.3 Action — 원본 이벤트의 Device.status → ACTIVATED

```python
source_event = db.query(Event).filter(Event.id == event_data.from_event_id).first()
if not source_event:
    raise HTTPException(404, ...)

# 추가: 원본 이벤트의 장비 상태 복구
if source_event.device_id:
    device = db.query(Device).filter(Device.id == source_event.device_id).first()
    if device:
        device.status = EnumDeviceStatus.ACTIVATED

new_event = ActionEvent(...)
db.add(new_event)
db.commit()
```

**주의**: ActionEvent의 원본이 반드시 MalfunctionEvent인 것은 아니다 (DetectionEvent일 수도 있음). 어떤 원본이든 조치 완료 시 장비를 ACTIVATED로 복구한다.

### 5.4 상태 전이 요약

```
ACTIVATED ──(Malfunction)──→ ERROR
ERROR     ──(Detection)───→ ACTIVATED
ERROR     ──(Action)──────→ ACTIVATED
DEACTIVATED ──(Malfunction)──→ ERROR
DEACTIVATED ──(Detection)───→ ACTIVATED
```

### 5.5 NATS Sync 연동 (자동)

- Device.status 변경 시 `devices` 테이블 UPDATE 발생
- 기존 `trg_sync_devices` 트리거가 자동으로 `pg_notify` → NATS `SYNC_DEVICE` 메시지 발행
- **추가 코드 불필요**

## 6. 고려사항

### 6.1 DEACTIVATED 장비 처리

`DEACTIVATED`(관리자가 의도적으로 비활성화)한 장비에 이벤트가 오면:
- Malfunction → ERROR로 변경 (장애는 비활성 상태에서도 기록)
- Detection → ACTIVATED로 변경 (탐지가 발생했으면 장비가 작동 중)

관리자가 의도적으로 비활성화한 장비는 이벤트 자체가 발생하지 않아야 하므로, 이벤트가 온 시점에서는 상태 변경이 적절하다.

### 6.2 ConnectionEvent 확장 (향후)

| 이벤트 | 상태 변경 | 비고 |
|--------|-----------|------|
| `CONNECTION_LOST` | → ERROR | 연결 끊김 = 장애 |
| `CONNECTION_RESTORED` | → ACTIVATED | 연결 복구 = 정상 |

이 PRD 범위에 포함하지 않는다. 필요 시 `PRD_Connection_Device_Status.md`로 확장.

### 6.3 응답 데이터

이벤트 Response에 포함된 `device` nested 객체에 변경된 status가 자동 반영된다.
`db.commit()` → `db.refresh()` 이후 device를 읽으므로 별도 처리 불필요.

## 7. 테스트 계획

### Malfunction → ERROR

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | ACTIVATED 장비에 장애 POST | Device.status == ERROR |
| 2 | DEACTIVATED 장비에 장애 POST | Device.status == ERROR |
| 3 | 이미 ERROR 장비에 장애 POST | ERROR 유지, 이벤트 정상 생성 |
| 4 | 응답 device.status 확인 | Response 내 device.status == "ERROR" |

### Detection → ACTIVATED

| # | 테스트 | 검증 |
|---|--------|------|
| 5 | ERROR 장비에 탐지 POST | Device.status == ACTIVATED |
| 6 | DEACTIVATED 장비에 탐지 POST | Device.status == ACTIVATED |
| 7 | 이미 ACTIVATED 장비에 탐지 POST | ACTIVATED 유지, 이벤트 정상 생성 |
| 8 | 응답 device.status 확인 | Response 내 device.status == "ACTIVATED" |

### Action → ACTIVATED (원본 장비)

| # | 테스트 | 검증 |
|---|--------|------|
| 9 | ERROR 장비의 장애이벤트에 조치 POST | 원본 Device.status == ACTIVATED |
| 10 | 원본 이벤트에 device_id 없는 경우 | 상태 변경 없이 ActionEvent 정상 생성 |

### 통합 시나리오

| # | 시나리오 | 검증 |
|---|----------|------|
| 11 | Malfunction → Action 순서 | ACTIVATED → ERROR → ACTIVATED |
| 12 | NATS SYNC_DEVICE 발행 | Device UPDATE 트리거 발화 확인 |

## 8. 변경이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-03-07 | v1.0 | 초안 — Malfunction → ERROR만 |
| 2026-03-07 | v1.1 | Detection → ACTIVATED, Action → ACTIVATED 추가 |
