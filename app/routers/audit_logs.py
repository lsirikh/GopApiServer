"""
Audit Log API endpoints
PRD: PRD_Audit_Log.md v1.0
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async
from app.models.audit_log import AuditLog
from app.schemas.audit_log import (
    AuditLogResponse,
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta, ValidationErrorResponse

router = APIRouter(tags=["Audit Logs"])


@router.get(
    "",
    response_model=ApiResponse[List[AuditLogResponse]],
    responses={
        200: {
            "description": "감사 로그 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": 100,
                                "action_type": "USER_CREATED",
                                "action_status": "SUCCESS",
                                "resource_type": "USER",
                                "resource_id": 5,
                                "resource_name": "홍길동 (operator01)",
                                "actor_id": 1,
                                "actor_login_id": "admin",
                                "actor_name": "관리자",
                                "actor_role": "ADMIN",
                                "changes": {
                                    "after": {
                                        "login_id": "operator01",
                                        "name": "홍길동",
                                        "role": "OPERATOR"
                                    }
                                },
                                "description": "사용자 생성: operator01",
                                "ip_address": "192.168.1.100",
                                "user_agent": None,
                                "error_message": None,
                                "created_at": "2026-01-19T10:30:00+09:00"
                            }
                        ],
                        "pagination": {
                            "page": 1,
                            "limit": 20,
                            "total": 1250,
                            "total_pages": 63
                        }
                    }
                }
            }
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error - 잘못된 쿼리 파라미터"
        }
    }
)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    action_type: Optional[str] = Query(None, description="행위 유형 필터 (EnumAuditActionType)"),
    resource_type: Optional[str] = Query(None, description="리소스 유형 필터 (EnumAuditResourceType)"),
    resource_id: Optional[int] = Query(None, description="리소스 ID 필터"),
    actor_login_id: Optional[str] = Query(None, description="행위자 로그인 ID 필터"),
    action_status: Optional[str] = Query(None, description="행위 결과 필터 (SUCCESS, FAILURE)"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜 필터"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜 필터"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    감사 로그 목록 조회 (페이지네이션)

    사용자 활동 감사 로그 목록을 페이지네이션하여 조회합니다.
    다양한 필터를 적용할 수 있습니다.

    **Query Parameters**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **action_type**: 행위 유형으로 필터링
    - **resource_type**: 리소스 유형으로 필터링
    - **resource_id**: 리소스 ID로 필터링
    - **actor_login_id**: 행위자 로그인 ID로 필터링
    - **action_status**: 행위 결과로 필터링
    - **start_date**: 시작 날짜 (이 날짜 이후의 로그만 조회)
    - **end_date**: 종료 날짜 (이 날짜 이전의 로그만 조회)

    **Response**: 감사 로그 목록 및 페이지네이션 정보
    """
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    # 필터 적용
    if action_type:
        stmt = stmt.where(AuditLog.action_type == action_type)
        count_stmt = count_stmt.where(AuditLog.action_type == action_type)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
        count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)
        count_stmt = count_stmt.where(AuditLog.resource_id == resource_id)
    if actor_login_id:
        stmt = stmt.where(AuditLog.actor_login_id == actor_login_id)
        count_stmt = count_stmt.where(AuditLog.actor_login_id == actor_login_id)
    if action_status:
        stmt = stmt.where(AuditLog.action_status == action_status)
        count_stmt = count_stmt.where(AuditLog.action_status == action_status)
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= start_date)
        count_stmt = count_stmt.where(AuditLog.created_at >= start_date)
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= end_date)
        count_stmt = count_stmt.where(AuditLog.created_at <= end_date)

    total = (await db.execute(count_stmt)).scalar() or 0
    skip = (page - 1) * limit
    audit_logs = (
        await db.execute(
            stmt.order_by(AuditLog.id.desc()).offset(skip).limit(limit)
        )
    ).scalars().all()

    total_pages = math.ceil(total / limit) if total > 0 else 1

    # v6.0-clone_deploy_bugfix (#2): 목록 fault tolerance — 한 행의 스키마 위반이
    # 목록 전체를 500 으로 만들지 않도록 skip + WARN.
    _data = []
    for log in audit_logs:
        try:
            _data.append(AuditLogResponse.model_validate(log))
        except Exception as exc:
            logger.warning(
                "[audit_logs.list] response 직렬화 실패 → skip: id=%s actor_role=%r reason=%s",
                getattr(log, "id", "?"), getattr(log, "actor_role", "?"), exc,
            )

    return ApiResponse(
        success=True,
        message="감사 로그 목록 조회 성공",
        data=_data,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages
        )
    )


@router.get(
    "/{audit_log_id}",
    response_model=ApiSingleResponse[AuditLogResponse],
    responses={
        200: {
            "description": "감사 로그 상세 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "id": 100,
                            "action_type": "ROLE_CHANGED",
                            "action_status": "SUCCESS",
                            "resource_type": "USER",
                            "resource_id": 5,
                            "resource_name": "홍길동 (operator01)",
                            "actor_id": 1,
                            "actor_login_id": "admin",
                            "actor_name": "관리자",
                            "actor_role": "ADMIN",
                            "changes": {
                                "before": {"role": "VIEWER"},
                                "after": {"role": "OPERATOR"}
                            },
                            "description": "역할 변경: VIEWER → OPERATOR",
                            "ip_address": "192.168.1.100",
                            "user_agent": "Mozilla/5.0...",
                            "error_message": None,
                            "created_at": "2026-01-19T10:30:00+09:00"
                        }
                    }
                }
            }
        },
        404: {
            "description": "감사 로그를 찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Audit log not found"
                        }
                    }
                }
            }
        }
    }
)
async def get_audit_log_detail(
    audit_log_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    감사 로그 상세 조회

    특정 감사 로그의 상세 정보를 조회합니다.

    **Path Parameters**:
    - **audit_log_id**: 감사 로그 ID

    **Response**: 감사 로그 상세 정보
    """
    audit_log = (
        await db.execute(select(AuditLog).where(AuditLog.id == audit_log_id))
    ).scalars().first()

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with id {audit_log_id} not found"
        )

    return ApiSingleResponse(
        success=True,
        message="감사 로그 상세 조회 성공",
        data=AuditLogResponse.model_validate(audit_log)
    )
