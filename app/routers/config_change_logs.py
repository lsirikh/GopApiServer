"""
Config Change Log API Router
Based on PRD_ConfigChangeLog.md v1.2

Endpoints:
- GET /api/config-change-logs - 목록 조회 (필터링, 페이지네이션)
- GET /api/config-change-logs/{id} - 단건 조회

JSONB 정규화 규칙 (v1.1):
- CREATED: after_state = {id, name} (식별 정보만)
- UPDATED: before_state/after_state = {변경된 필드만}
- DELETED: before_state = {id, name} (식별 정보만)
- STATUS_CHANGED: {status} 필드만
- ASSIGNED: after_state = {target_id, target_name}
- UNASSIGNED: before_state = {target_id, target_name}

Note: SERVER, SERVER_CATEGORY는 SystemEvent에서 관리
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.models.config_change_log import ConfigChangeLog
from app.schemas.config_change_log import ConfigChangeLogResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

router = APIRouter()


# ==============================================================================
# Helper Functions
# ==============================================================================

def _config_change_log_to_response(log: ConfigChangeLog) -> ConfigChangeLogResponse:
    """ConfigChangeLog 모델을 ConfigChangeLogResponse 스키마로 변환"""
    return ConfigChangeLogResponse(
        id=log.id,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        resource_name=log.resource_name,
        action=log.action,
        before_state=log.before_state,
        after_state=log.after_state,
        actor_id=log.actor_id,
        actor_name=log.actor_name,
        actor_ip=log.actor_ip,
        description=log.description,
        created_at=log.created_at
    )


# ==============================================================================
# GET Endpoints
# ==============================================================================

@router.get("", response_model=ApiResponse[list[ConfigChangeLogResponse]])
async def get_config_change_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    resource_type: Optional[str] = Query(None, description="리소스 유형 필터"),
    resource_id: Optional[int] = Query(None, description="리소스 ID 필터"),
    action: Optional[str] = Query(None, description="액션 유형 필터"),
    actor_id: Optional[int] = Query(None, description="액터 ID 필터"),
    start_date: Optional[datetime] = Query(None, description="시작 일시"),
    end_date: Optional[datetime] = Query(None, description="종료 일시"),
    db: Session = Depends(get_db)
):
    """
    설정 변경 로그 목록 조회

    **파라미터**:
    - **page**: 페이지 번호 (default: 1)
    - **limit**: 페이지당 항목 수 (default: 20, max: 100)
    - **resource_type**: 리소스 유형 필터 (CAMERA, SENSOR, DEVICE_GROUP 등)
    - **resource_id**: 리소스 ID 필터
    - **action**: 액션 유형 필터 (CREATED, UPDATED, DELETED 등)
    - **actor_id**: 액터(사용자) ID 필터
    - **start_date**: 시작 일시 필터
    - **end_date**: 종료 일시 필터

    **JSONB 정규화 규칙 (v1.1)**:

    | Action | before_state | after_state |
    |--------|--------------|-------------|
    | CREATED | null | {id, name} |
    | UPDATED | {변경된 필드만} | {변경된 필드만} |
    | DELETED | {id, name} | null |
    | STATUS_CHANGED | {status} | {status} |
    | ASSIGNED | null | {target_id, target_name} |
    | UNASSIGNED | {target_id, target_name} | null |

    **응답 예시**:
    ```json
    {
      "success": true,
      "message": "Config change logs retrieved successfully",
      "data": {
        "logs": [
          {
            "id": 1,
            "resource_type": "CAMERA",
            "resource_id": 201,
            "action": "CREATED",
            "before_state": null,
            "after_state": {"id": 201, "name": "정문 CCTV"}
          },
          {
            "id": 2,
            "resource_type": "CAMERA",
            "resource_id": 201,
            "action": "UPDATED",
            "before_state": {"name": "정문 CCTV"},
            "after_state": {"name": "정문 CCTV (수정)"}
          },
          {
            "id": 3,
            "resource_type": "CAMERA",
            "resource_id": 202,
            "action": "DELETED",
            "before_state": {"id": 202, "name": "후문 CCTV"},
            "after_state": null
          }
        ],
        "total": 150,
        "page": 1,
        "limit": 20
      }
    }
    ```

    PRD Reference: PRD_ConfigChangeLog.md v1.2
    """
    query = db.query(ConfigChangeLog)

    # 필터 적용
    if resource_type:
        try:
            type_enum = EnumConfigResourceType(resource_type)
            query = query.filter(ConfigChangeLog.resource_type == type_enum)
        except ValueError:
            pass  # 유효하지 않은 값은 무시

    if resource_id is not None:
        query = query.filter(ConfigChangeLog.resource_id == resource_id)

    if action:
        try:
            action_enum = EnumConfigActionType(action)
            query = query.filter(ConfigChangeLog.action == action_enum)
        except ValueError:
            pass

    if actor_id is not None:
        query = query.filter(ConfigChangeLog.actor_id == actor_id)

    if start_date:
        query = query.filter(ConfigChangeLog.created_at >= start_date)

    if end_date:
        query = query.filter(ConfigChangeLog.created_at <= end_date)

    # 전체 카운트
    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # 정렬 및 페이지네이션
    query = query.order_by(ConfigChangeLog.created_at.desc())
    skip = (page - 1) * limit
    logs = query.offset(skip).limit(limit).all()

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Config change logs retrieved successfully",
        data=[_config_change_log_to_response(log) for log in logs],
        pagination=pagination
    )


@router.get("/{log_id}", response_model=ApiSingleResponse[ConfigChangeLogResponse])
async def get_config_change_log(log_id: int, db: Session = Depends(get_db)):
    """
    설정 변경 로그 단건 조회

    **파라미터**:
    - **log_id**: 로그 ID

    **응답 예시 (UPDATED)**:
    ```json
    {
      "success": true,
      "message": "Config change log retrieved successfully",
      "data": {
        "id": 1,
        "resource_type": "CAMERA",
        "resource_id": 201,
        "resource_name": "Camera-201 (정문 CCTV)",
        "action": "UPDATED",
        "before_state": {"name": "정문 CCTV"},
        "after_state": {"name": "정문 CCTV (수정)"},
        "actor_id": 1,
        "actor_name": "admin",
        "actor_ip": "192.168.1.100",
        "description": "Camera 정보 수정",
        "created_at": "2026-01-20T10:30:00+09:00"
      }
    }
    ```

    PRD Reference: PRD_ConfigChangeLog.md v1.2
    """
    log = db.query(ConfigChangeLog).filter(ConfigChangeLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"ConfigChangeLog with id {log_id} not found")

    return ApiSingleResponse(
        success=True,
        message="Config change log retrieved successfully",
        data=_config_change_log_to_response(log)
    )
