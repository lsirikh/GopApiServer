# PRD: ActionEvent 1:N 관계 리팩토링

**작성일**: 2026-02-09
**최종 수정일**: 2026-02-27
**버전**: v2.0
**기반**: PRD_Event_ActionEvent_Refactoring.md v2.1
**변경 유형**: 동작 변경 (Behavioral Change)

---

## 1. 배경 및 목적

### 1.1 현재 구조 (1:1)

현재 ActionEvent와 원본 이벤트(Detection/Malfunction)는 **암묵적 1:1 관계**로 운용된다.

- `from_event_id` FK에 UNIQUE 제약조건이 **없으므로** DB 스키마상 1:N이 가능하지만,
  비즈니스 로직이 1:1을 전제로 구현되어 있다.
- ActionEvent **생성** 시 → 원본 이벤트의 `action_reported = "True"` (무조건)
- ActionEvent **삭제** 시 → 원본 이벤트의 `action_reported = "False"` (무조건)

### 1.2 문제점

하나의 탐지/장애 이벤트에 대해 **여러 명이 각기 다른 조치**를 취할 수 있다.
예: 침입 탐지 → 1차 확인 조치(operator1) + 2차 경비 출동(operator2) + 3차 보고서 작성(admin)

현재 구조에서는:
- 두 번째 ActionEvent 생성 시 `action_reported`는 이미 "True"이므로 문제 없음
- 그러나 **첫 번째 ActionEvent만 삭제**해도 `action_reported = "False"`로 리셋됨
- 두 번째 ActionEvent가 아직 존재하는데도 "미조치" 상태가 되는 **데이터 불일치** 발생
- `GET /{event_id}/action` 엔드포인트가 `.first()`로 **1건만 반환** — 나머지 조치 조회 불가
- DetectionLog의 `_build_action_nested()`가 `actions[0]`만 사용 — 나머지 무시

### 1.3 목표

- ActionEvent → Detection/Malfunction 관계를 **명시적 1:N**으로 전환
- `action_reported` 필드를 **액션 존재 여부 기반**으로 동적 관리
  - 해당 이벤트에 ActionEvent가 **1개 이상 존재** → `"True"`
  - 해당 이벤트에 ActionEvent가 **0개** → `"False"`
- 이벤트별 조치 조회 API를 **리스트 반환**으로 변경
- DetectionLog의 조치 정보를 **리스트**로 확장

---

## 2. 변경 범위

### 2.1 변경 없음 (DB 스키마)

| 항목 | 현재 상태 | 변경 여부 |
|------|----------|----------|
| `action_events.from_event_id` FK | UNIQUE 없음 | 변경 없음 |
| `detection_events.action_reported` | String(10), default="False" | 변경 없음 |
| `malfunction_events.action_reported` | String(10), default="False" | 변경 없음 |
| `Event.actions` relationship | `back_populates="source_event"` (list) | 변경 없음 |

> DB 스키마가 이미 1:N을 허용하므로 마이그레이션 불필요.

### 2.2 변경 대상 (비즈니스 로직)

| 파일 | 함수/엔드포인트 | 현재 동작 | 변경 후 |
|------|----------------|----------|--------|
| `app/routers/actions.py` | `reset_source_action_reported()` | 무조건 `"False"` 설정 | **남은 ActionEvent 수 확인** 후 0이면 `"False"`, 1이상이면 유지 |
| `app/routers/actions.py` | `update_source_action_reported()` | 무조건 `"True"` 설정 | 변경 없음 (1개 이상이면 True — 생성 시 항상 True) |
| `app/routers/detections.py` | `GET /{event_id}/action` | `.first()`로 단건 반환 | `.all()`로 **리스트 반환** |
| `app/routers/malfunctions.py` | `GET /{event_id}/action` | `.first()`로 단건 반환 | `.all()`로 **리스트 반환** |
| `app/routers/detection_logs.py` | `_build_action_nested()` | `actions[0]` 1건만 사용 | **전체 리스트** 변환 |
| `app/schemas/event.py` | `DetectionLogResponse.action` | `Optional[ActionNested]` 단건 | `List[ActionNested]` **리스트** |

---

## 3. 상세 설계

### 3.1 `reset_source_action_reported()` 변경

**현재 코드** (`app/routers/actions.py:106-129`):
```python
def reset_source_action_reported(db: Session, source_event: Event) -> None:
    if source_event is None:
        return
    if isinstance(source_event, (DetectionEvent, MalfunctionEvent)):
        source_event.action_reported = "False"
```

**변경 후**:
```python
def reset_source_action_reported(db: Session, source_event: Event, excluding_action_id: int) -> None:
    if source_event is None:
        return
    if isinstance(source_event, (DetectionEvent, MalfunctionEvent)):
        remaining_count = db.query(ActionEvent).filter(
            ActionEvent.from_event_id == source_event.id,
            ActionEvent.id != excluding_action_id
        ).count()
        if remaining_count == 0:
            source_event.action_reported = "False"
```

**변경 사항**:
- `excluding_action_id` 파라미터 추가: 삭제 대상 ActionEvent ID를 제외하고 카운트
- 남은 ActionEvent가 0개일 때만 `"False"` 설정
- 1개 이상 남아있으면 `action_reported` 유지 (`"True"`)

### 3.2 `delete_action_event()` 호출부 변경

**현재 코드** (`app/routers/actions.py:636`):
```python
reset_source_action_reported(db, event.source_event)
```

**변경 후**:
```python
reset_source_action_reported(db, event.source_event, excluding_action_id=event.id)
```

### 3.3 `GET /{event_id}/action` → `GET /{event_id}/actions` (복수형)

#### 3.3.1 detections.py 변경

**현재** (`app/routers/detections.py:684`):
```python
@router.get("/{event_id}/action", response_model=ApiSingleResponse[ActionEventResponse])
async def get_action_event_for_detection(...):
    action = db.query(ActionEvent).filter(
        ActionEvent.from_event_id == event_id
    ).first()
    # 단건 반환
```

**변경 후**:
```python
@router.get("/{event_id}/actions", response_model=ApiResponse[list[ActionEventResponse]])
async def get_action_events_for_detection(...):
    actions = db.query(ActionEvent).filter(
        ActionEvent.from_event_id == event_id
    ).order_by(ActionEvent.created_at.desc()).all()
    # 리스트 반환 (빈 리스트 허용 — 404 대신)
```

**응답 변경**:
- `ApiSingleResponse[ActionEventResponse]` → `ApiResponse[list[ActionEventResponse]]`
- 조치가 없으면 404 대신 **빈 리스트** 반환 (`"items": [], "total": 0`)
- URL 경로: `/action` → `/actions` (복수형으로 변경)

#### 3.3.2 malfunctions.py 변경

detections.py와 동일한 패턴 적용.

### 3.4 DetectionLog 조치 정보 리스트화

#### 3.4.1 `_build_action_nested()` → `_build_actions_nested()`

**현재** (`app/routers/detection_logs.py:152`):
```python
def _build_action_nested(actions) -> Optional[ActionNested]:
    """Event.actions 리스트에서 첫 번째 ActionEvent를 ActionNested로 변환"""
    if not actions:
        return None
    action = actions[0] if isinstance(actions, list) else None
    if action is None:
        return None
    return ActionNested(...)
```

**변경 후**:
```python
def _build_actions_nested(actions) -> list[ActionNested]:
    """Event.actions 리스트를 ActionNested 리스트로 변환"""
    if not actions:
        return []
    return [
        ActionNested(
            id=action.id,
            content=action.content,
            user=action.user,
            created_at=action.created_at,
            updated_at=action.updated_at
        )
        for action in actions
    ]
```

#### 3.4.2 호출부 변경

```python
# 변경 전
action=_build_action_nested(e.actions),

# 변경 후
actions=_build_actions_nested(e.actions),
```

#### 3.4.3 `DetectionLogResponse` 스키마 변경

**현재** (`app/schemas/event.py:405`):
```python
action: Optional[ActionNested] = Field(None, description="조치보고 정보 (없으면 null)")
```

**변경 후**:
```python
actions: list[ActionNested] = Field(default_factory=list, description="조치보고 목록 (없으면 빈 리스트)")
```

---

## 4. API 동작 변경

### 4.1 POST /api/events/actions (ActionEvent 생성)

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 동일 이벤트에 2번째 Action 생성 | 동작하지만 의미 불명확 | **정상 동작** (1:N 허용) |
| `action_reported` 업데이트 | 무조건 `"True"` | 무조건 `"True"` (동일) |

### 4.2 DELETE /api/events/actions/{event_id} (ActionEvent 삭제)

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| Action 삭제 시 `action_reported` | 무조건 `"False"` | **남은 Action 수 확인**: 0이면 `"False"`, 1+이면 유지 |
| 마지막 Action 삭제 | `"False"` | `"False"` (동일) |
| 2개 중 1개 삭제 | `"False"` (버그) | `"True"` (정상 유지) |

### 4.3 GET /api/events/detection/{id}/actions (조치 목록 조회) — Breaking Change

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| URL | `GET /{event_id}/action` | `GET /{event_id}/actions` |
| 응답 타입 | `ApiSingleResponse[ActionEventResponse]` | `ApiResponse[list[ActionEventResponse]]` |
| 조치 없음 | 404 에러 | **빈 리스트** (`items: [], total: 0`) |
| 조치 1건 | 단건 객체 | 리스트 (`items: [...]`, `total: 1`) |
| 조치 N건 | 첫 번째만 반환 | **전체 리스트** (`items: [...]`, `total: N`) |

### 4.4 GET /api/events/malfunction/{id}/actions (조치 목록 조회) — Breaking Change

4.3과 동일한 패턴 적용.

### 4.5 GET /api/events/detection-logs (탐지 로그)

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 응답 필드명 | `action` (단건) | `actions` (리스트) |
| 조치 없음 | `action: null` | `actions: []` |
| 조치 1건 | `action: {...}` | `actions: [{...}]` |
| 조치 N건 | `action: {첫 번째만}` | `actions: [{...}, {...}, ...]` |

### 4.6 기타 API — 변경 없음

| API | 영향 |
|-----|------|
| GET /api/events/actions | `from_event_id` 필터로 N건 반환 가능 (기존에도 list API) |
| GET /api/events/actions/{id} | 변경 없음 |
| PATCH /api/events/actions/{id} | 변경 없음 |
| PUT /api/events/actions/{id} | 변경 없음 |
| GET /api/events/detection | `action_reported` 값이 정확해짐 |
| GET /api/events/malfunction | `action_reported` 값이 정확해짐 |

---

## 5. Breaking Changes 정리

| 변경 | 영향 | 클라이언트 대응 |
|------|------|----------------|
| `/{event_id}/action` → `/{event_id}/actions` | URL 경로 변경 | 엔드포인트 URL 수정 |
| `ApiSingleResponse` → `ApiResponse[list]` | 응답 구조 변경 (`data` → `data.items`) | 응답 파싱 로직 수정 |
| 조치 없음 시 404 → 200 빈 리스트 | 에러 핸들링 불필요 | 404 핸들링 제거, 빈 리스트 처리 |
| `DetectionLogResponse.action` → `actions` | 필드명 변경 (단수 → 복수) | 필드명 수정 |

---

## 6. 수정 대상 파일 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| **수정** | `app/routers/actions.py` | `reset_source_action_reported()` 로직 변경, 호출부 수정 |
| **수정** | `app/routers/detections.py` | `GET /{event_id}/actions` 리스트 반환으로 변경 |
| **수정** | `app/routers/malfunctions.py` | `GET /{event_id}/actions` 리스트 반환으로 변경 |
| **수정** | `app/routers/detection_logs.py` | `_build_actions_nested()` 리스트 변환, 호출부 수정 |
| **수정** | `app/schemas/event.py` | `DetectionLogResponse.action` → `actions: list[ActionNested]` |
| **신규** | `tests/test_action_event_1n.py` | 1:N 시나리오 테스트 |

---

## 7. TDD 실행 계획

### Phase 1: 1:N 관계 동작 확인 (Behavioral)

- [ ] 1.1 TEST: 동일 이벤트에 ActionEvent 2개 생성 가능 확인
- [ ] 1.2 IMPL: 확인 (DB 스키마 이미 지원)
- [ ] 1.3 VERIFY: 테스트 통과

### Phase 2: action_reported 카운트 기반 로직 (Behavioral)

- [ ] 2.1 TEST: ActionEvent 1개 생성 → action_reported = "True"
- [ ] 2.2 IMPL: 확인 (기존 로직 동일)
- [ ] 2.3 TEST: ActionEvent 2개 생성 → action_reported = "True"
- [ ] 2.4 IMPL: 확인
- [ ] 2.5 TEST: 2개 중 1개 삭제 → action_reported = "True" 유지
- [ ] 2.6 IMPL: `reset_source_action_reported()` 변경 — 남은 카운트 확인
- [ ] 2.7 TEST: 마지막 1개 삭제 → action_reported = "False"
- [ ] 2.8 IMPL: 확인
- [ ] 2.9 VERIFY: 전체 테스트 통과

### Phase 3: 이벤트별 조치 목록 API (Behavioral)

- [ ] 3.1 TEST: `GET /api/events/detection/{id}/actions` 빈 리스트 반환 (조치 없음)
- [ ] 3.2 IMPL: detections.py 엔드포인트 리스트 반환으로 변경
- [ ] 3.3 TEST: `GET /api/events/detection/{id}/actions` N건 반환 (조치 존재)
- [ ] 3.4 IMPL: 확인
- [ ] 3.5 TEST: `GET /api/events/malfunction/{id}/actions` 빈 리스트 반환
- [ ] 3.6 IMPL: malfunctions.py 엔드포인트 리스트 반환으로 변경
- [ ] 3.7 TEST: `GET /api/events/malfunction/{id}/actions` N건 반환
- [ ] 3.8 IMPL: 확인
- [ ] 3.9 VERIFY: 전체 테스트 통과

### Phase 4: DetectionLog 조치 리스트화 (Behavioral)

- [ ] 4.1 TEST: DetectionLog 응답에 `actions` 필드가 리스트로 반환됨
- [ ] 4.2 IMPL: 스키마 변경 (`action` → `actions: list`) + `_build_actions_nested()` 변경
- [ ] 4.3 TEST: 조치 없는 DetectionLog → `actions: []`
- [ ] 4.4 TEST: 조치 N건 DetectionLog → `actions: [{...}, {...}]`
- [ ] 4.5 VERIFY: 전체 테스트 통과

### Phase 5: 엣지 케이스 (Behavioral)

- [ ] 5.1 TEST: ConnectionEvent에 ActionEvent 생성 → action_reported 무관 (ConnectionEvent에는 action_reported 없음)
- [ ] 5.2 IMPL: 확인 (기존 isinstance 체크로 자동 스킵)
- [ ] 5.3 TEST: source_event가 NULL인 ActionEvent 삭제 → 에러 없음
- [ ] 5.4 IMPL: 확인 (기존 None 체크)
- [ ] 5.5 VERIFY: 전체 테스트 통과

### Phase 6: 기존 테스트 호환성 확인

- [ ] 6.1 VERIFY: 기존 ActionEvent 테스트 전체 통과 (regression 없음)
- [ ] 6.2 VERIFY: 기존 DetectionEvent, MalfunctionEvent 테스트 통과
- [ ] 6.3 VERIFY: 기존 DetectionLog 테스트 통과 (스키마 필드명 변경 반영)

### Phase 7: 최종 검증 및 커밋

- [ ] 7.1 VERIFY: 전체 테스트 수트 통과
- [ ] 7.2 COMMIT (behavioral): ActionEvent 1:N 리팩토링 — action_reported 카운트 기반 + API 리스트 반환
