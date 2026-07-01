# PRD: EventMappingSpeaker API 수정

**문서 버전**: v1.1
**작성일**: 2026-01-14
**상태**: Draft
**관련 문서**:
- GOP_Restful_Api_연동설계.md (Section 7.4)
- PRD_EventMappingSpeaker.md v1.0

---

## 1. 개요

### 1.1 목적

본 문서는 GOP_Restful_Api_연동설계.md (Section 7.4)와 현재 구현된 EventMappingSpeaker API 코드 간의 차이점을 분석하고, 문서 사양에 맞게 코드를 수정하기 위한 상세 요구사항을 정의합니다.

### 1.2 문서 vs 구현 비교 분석 요약

| 항목 | 문서 사양 (7.4) | 현재 구현 | 일치 여부 | 우선순위 |
|------|-----------------|-----------|----------|---------|
| Endpoint Path | `/api/integrations/event-mappings/{mapping_id}/speakers` | O | **일치** | - |
| 목록 조회 페이지네이션 | page, limit 파라미터 | X | **불일치** | HIGH |
| PATCH speaker_id 검증 | 변경 시 존재 확인 필요 | X | **불일치** | HIGH |
| PATCH file_group_id 검증 | 변경 시 존재 확인 필요 | X | **불일치** | HIGH |
| PUT speaker_id 검증 | 변경 시 존재 확인 필요 | X | **불일치** | HIGH |
| PUT file_group_id 검증 | 변경 시 존재 확인 필요 | X | **불일치** | HIGH |
| 코드 주석 | `/api/integrations/...` | 잘못된 경로 | **불일치** | LOW |
| Nested Response 형식 | speaker, file_group 포함 | O | **일치** | - |
| FK CASCADE 동작 | 문서 명세 | O | **일치** | - |

---

## 2. 수정 요구사항

### 2.1 목록 조회 페이지네이션 추가 [HIGH]

**현재 상태**:
- `GET /{mapping_id}/speakers`는 모든 항목을 한 번에 반환
- 페이지네이션 파라미터 없음

**문서 사양** (7.4.1):
```
Query Parameters:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
```

**수정 요구사항**:

1. Query Parameters 추가:
   - `page: int = Query(1, ge=1, description="페이지 번호")`
   - `limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수")`

2. 페이지네이션 로직 구현:
   ```python
   offset = (page - 1) * limit
   query = db.query(EventMappingSpeaker).filter(
       EventMappingSpeaker.event_mapping_id == mapping_id
   )
   total = query.count()
   speakers = query.offset(offset).limit(limit).all()
   ```

3. Response 형식 (문서와 동일):
   ```json
   {
     "success": true,
     "message": "Event mapping speakers retrieved successfully",
     "data": {
       "items": [...],
       "total": 10
     }
   }
   ```

**영향 범위**:
- `app/routers/event_mapping_speakers.py` - `list_event_mapping_speakers()` 함수

---

### 2.2 PATCH API speaker_id/file_group_id 검증 추가 [HIGH]

**현재 상태**:
```python
def update_event_mapping_speaker(...):
    # Update only provided fields
    update_data = speaker_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ems, field, value)  # 검증 없이 바로 설정
```

**문서 사양** (7.4.4):
- speaker_id 변경 시 해당 Speaker 존재 확인 필요
- file_group_id 변경 시 해당 FileGroup 존재 확인 필요

**수정 요구사항**:

```python
def update_event_mapping_speaker(
    mapping_id: int,
    config_id: int,
    speaker_data: EventMappingSpeakerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    # ... (기존 EventMapping, EventMappingSpeaker 존재 확인 로직)

    update_data = speaker_data.model_dump(exclude_unset=True)

    # speaker_id 변경 시 존재 확인
    if 'speaker_id' in update_data and update_data['speaker_id'] is not None:
        speaker = db.query(Speaker).filter(Speaker.id == update_data['speaker_id']).first()
        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Speaker with id {update_data['speaker_id']} not found"
            )

    # file_group_id 변경 시 존재 확인
    if 'file_group_id' in update_data and update_data['file_group_id'] is not None:
        file_group = db.query(FileGroup).filter(FileGroup.id == update_data['file_group_id']).first()
        if not file_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FileGroup with id {update_data['file_group_id']} not found"
            )

    for field, value in update_data.items():
        setattr(ems, field, value)

    # ... (나머지 로직)
```

**영향 범위**:
- `app/routers/event_mapping_speakers.py` - `update_event_mapping_speaker()` 함수

---

### 2.3 PUT API speaker_id/file_group_id 검증 추가 [HIGH]

**현재 상태**:
```python
def replace_event_mapping_speaker(...):
    # Replace all fields - 검증 없이 바로 설정
    ems.speaker_id = speaker_data.speaker_id
    ems.file_group_id = speaker_data.file_group_id
    # ...
```

**문서 사양** (7.4.5):
- speaker_id (필수) 존재 확인 필요
- file_group_id (선택) 존재 확인 필요

**수정 요구사항**:

```python
def replace_event_mapping_speaker(
    mapping_id: int,
    config_id: int,
    speaker_data: EventMappingSpeakerReplace,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    # ... (기존 EventMapping, EventMappingSpeaker 존재 확인 로직)

    # speaker_id 존재 확인 (필수 필드)
    speaker = db.query(Speaker).filter(Speaker.id == speaker_data.speaker_id).first()
    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_data.speaker_id} not found"
        )

    # file_group_id 존재 확인 (선택 필드)
    if speaker_data.file_group_id is not None:
        file_group = db.query(FileGroup).filter(FileGroup.id == speaker_data.file_group_id).first()
        if not file_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FileGroup with id {speaker_data.file_group_id} not found"
            )

    # Replace all fields
    ems.speaker_id = speaker_data.speaker_id
    ems.file_group_id = speaker_data.file_group_id
    # ...
```

**영향 범위**:
- `app/routers/event_mapping_speakers.py` - `replace_event_mapping_speaker()` 함수

---

### 2.4 코드 주석 수정 [LOW]

**현재 상태**:
```python
"""
EventMappingSpeaker Router

PRD: PRD_EventMappingSpeaker.md v1.0

Endpoints: /api/event-mappings/{mapping_id}/speakers  # 잘못됨
"""
```

**수정 요구사항**:
```python
"""
EventMappingSpeaker Router

PRD: PRD_EventMappingSpeaker.md v1.0

Endpoints: /api/integrations/event-mappings/{mapping_id}/speakers
"""
```

**영향 범위**:
- `app/routers/event_mapping_speakers.py` - 파일 헤더 주석

---

## 3. 테스트 요구사항

### 3.1 신규 테스트 케이스

| 테스트 ID | API | 시나리오 | 예상 결과 |
|----------|-----|----------|----------|
| TC-LIST-001 | GET List | page=2, limit=5 파라미터 사용 | 페이지네이션 적용된 결과 반환 |
| TC-LIST-002 | GET List | page=0 (유효하지 않은 값) | 422 Validation Error |
| TC-LIST-003 | GET List | limit=101 (최대값 초과) | 422 Validation Error |
| TC-PATCH-001 | PATCH | 존재하지 않는 speaker_id로 변경 | 404 Not Found |
| TC-PATCH-002 | PATCH | 존재하지 않는 file_group_id로 변경 | 404 Not Found |
| TC-PATCH-003 | PATCH | 유효한 speaker_id로 변경 | 200 OK, 변경된 데이터 반환 |
| TC-PUT-001 | PUT | 존재하지 않는 speaker_id | 404 Not Found |
| TC-PUT-002 | PUT | 존재하지 않는 file_group_id | 404 Not Found |
| TC-PUT-003 | PUT | 유효한 speaker_id, file_group_id | 200 OK |

### 3.2 기존 테스트 영향

- `tests/test_event_mapping_speaker_router.py`의 기존 66개 테스트는 유지
- 페이지네이션 관련 목록 조회 테스트 수정 필요 (파라미터 없는 기본 동작 테스트)

---

## 4. 구현 계획

### 4.1 Phase 1: 코드 수정 (TDD)

| 단계 | 작업 | 예상 파일 |
|------|------|----------|
| 1.1 | 페이지네이션 테스트 작성 | test_event_mapping_speaker_router.py |
| 1.2 | 목록 조회 페이지네이션 구현 | event_mapping_speakers.py |
| 1.3 | PATCH 검증 테스트 작성 | test_event_mapping_speaker_router.py |
| 1.4 | PATCH speaker_id/file_group_id 검증 구현 | event_mapping_speakers.py |
| 1.5 | PUT 검증 테스트 작성 | test_event_mapping_speaker_router.py |
| 1.6 | PUT speaker_id/file_group_id 검증 구현 | event_mapping_speakers.py |
| 1.7 | 코드 주석 수정 | event_mapping_speakers.py |

### 4.2 Phase 2: 문서 업데이트

| 단계 | 작업 | 파일 |
|------|------|------|
| 2.1 | 스키마 문서 업데이트 (페이지네이션 추가) | GOP_스키마_전체.md |
| 2.2 | PRD 버전 업데이트 | PRD_EventMappingSpeaker.md → v1.1 |

---

## 5. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2026-01-12 | - | 최초 작성 (EventMappingSpeaker API 구현) |
| v1.1 | 2026-01-14 | - | 문서 vs 구현 차이점 분석 및 수정 요구사항 정의 |

---

## 6. 부록: 문서 vs 구현 상세 비교

### 6.1 목록 조회 (7.4.1)

**문서**:
```http
GET /api/integrations/event-mappings/10/speakers?page=1&limit=20 HTTP/1.1
```

**현재 구현**:
```python
@router.get("/{mapping_id}/speakers", ...)
def list_event_mapping_speakers(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    # page, limit 파라미터 없음
```

### 6.2 PATCH (7.4.4)

**문서 예시**: speaker_id를 301에서 302로 변경 가능

**현재 구현**: speaker_id 변경 시 존재 검증 없음

### 6.3 PUT (7.4.5)

**문서 예시**: speaker_id를 302로 변경

**현재 구현**: speaker_id 존재 검증 없음
