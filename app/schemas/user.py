"""
User Pydantic schemas
PRD: PRD_Account_Design.md Section 4
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.common import KSTDatetime

from app.utils.enums import (
    EnumUserRole, EnumLogoutReason,
    EnumLoginAction, EnumLoginResult, EnumLoginFailureReason,
)


# ============================================================
# UserGroup Schemas (AC-2.3)
# ============================================================

class PermissionsSchema(BaseModel):
    """
    Permissions structure for UserGroup
    PRD: PRD_Account_Design.md Section 4.1
    """
    modules: Optional[List[str]] = None
    device_groups: Optional[List[int]] = None
    time_restriction: Optional[Dict[str, Any]] = None


class UserGroupCreate(BaseModel):
    """Schema for creating a new user group"""
    name: str = Field(
        ..., min_length=1, max_length=100,
        description="그룹 이름",
        json_schema_extra={"example": "1중대 운영팀"}
    )
    description: Optional[str] = Field(
        None, description="그룹 설명",
        json_schema_extra={"example": "1중대 경계 시스템 운영 담당"}
    )
    permissions: Optional[Dict[str, Any]] = Field(
        None, description="권한 설정",
        json_schema_extra={"example": {
            "modules": {"events": {"view": True, "edit": True}, "cameras": {"view": True, "control": True}},
            "device_groups": [1, 2, 3]
        }}
    )
    is_active: Optional[bool] = Field(
        True, description="활성 상태",
        json_schema_extra={"example": True}
    )


class UserGroupUpdate(BaseModel):
    """Schema for updating a user group (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class UserGroupResponse(BaseModel):
    """Schema for user group response"""
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: bool
    user_count: Optional[int] = None
    created_at: KSTDatetime
    updated_at: KSTDatetime

    model_config = {"from_attributes": True}


# ============================================================
# AccountUser Schemas (AC-3.3 - PRD_Account_Design.md compliant)
# ============================================================

class AccountUserCreate(BaseModel):
    """Schema for creating a new account user (PRD compliant)"""
    login_id: str = Field(
        ..., min_length=3, max_length=50,
        description="로그인 ID",
        json_schema_extra={"example": "operator01"}
    )
    password: str = Field(
        ..., min_length=6,
        description="비밀번호",
        json_schema_extra={"example": "SecureP@ss123!"}
    )
    name: str = Field(
        ..., min_length=1, max_length=100,
        description="사용자 이름",
        json_schema_extra={"example": "홍길동"}
    )
    email: Optional[str] = Field(
        None, description="이메일",
        json_schema_extra={"example": "operator01@gop.mil.kr"}
    )
    department: Optional[str] = Field(
        None, description="부서",
        json_schema_extra={"example": "경계부대 1중대"}
    )
    position: Optional[str] = Field(
        None, description="직책",
        json_schema_extra={"example": "상병"}
    )
    employee_number: Optional[str] = Field(
        None, description="군번/사번",
        json_schema_extra={"example": "21-12345678"}
    )
    photo_url: Optional[str] = Field(
        None, description="프로필 사진 URL"
    )
    phone: Optional[str] = Field(
        None, description="전화번호",
        json_schema_extra={"example": "010-1234-5678"}
    )
    role: Optional[str] = Field(
        "VIEWER", description="사용자 역할 (ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST)",
        json_schema_extra={"example": "OPERATOR"}
    )
    group_id: Optional[int] = Field(
        None, description="소속 그룹 ID",
        json_schema_extra={"example": 1}
    )


class AccountUserUpdate(BaseModel):
    """Schema for updating an account user (all fields optional)"""
    name: Optional[str] = Field(
        None, min_length=1, max_length=100,
        description="사용자 이름",
        json_schema_extra={"example": "홍길동"}
    )
    email: Optional[str] = Field(
        None, description="이메일",
        json_schema_extra={"example": "operator01@gop.mil.kr"}
    )
    department: Optional[str] = Field(
        None, description="부서",
        json_schema_extra={"example": "경계부대 1중대"}
    )
    position: Optional[str] = Field(
        None, description="직책",
        json_schema_extra={"example": "병장"}
    )
    employee_number: Optional[str] = Field(
        None, description="군번/사번",
        json_schema_extra={"example": "21-12345678"}
    )
    photo_url: Optional[str] = Field(
        None, description="프로필 사진 URL"
    )
    phone: Optional[str] = Field(
        None, description="전화번호",
        json_schema_extra={"example": "010-1234-5678"}
    )
    role: Optional[str] = Field(
        None, description="사용자 역할",
        json_schema_extra={"example": "OPERATOR"}
    )
    group_id: Optional[int] = Field(
        None, description="소속 그룹 ID",
        json_schema_extra={"example": 1}
    )
    is_active: Optional[bool] = Field(
        None, description="활성 상태",
        json_schema_extra={"example": True}
    )


class AccountUserResponse(BaseModel):
    """Schema for account user response (excludes password_hash)"""
    id: int = Field(..., description="사용자 ID", json_schema_extra={"example": 1})
    login_id: str = Field(..., description="로그인 ID", json_schema_extra={"example": "operator01"})
    name: str = Field(..., description="사용자 이름", json_schema_extra={"example": "홍길동"})
    email: Optional[str] = Field(None, description="이메일", json_schema_extra={"example": "operator01@gop.mil.kr"})
    department: Optional[str] = Field(None, description="부서", json_schema_extra={"example": "경계부대 1중대"})
    position: Optional[str] = Field(None, description="직책", json_schema_extra={"example": "상병"})
    employee_number: Optional[str] = Field(None, description="군번/사번", json_schema_extra={"example": "21-12345678"})
    photo_url: Optional[str] = Field(None, description="프로필 사진 URL")
    phone: Optional[str] = Field(None, description="전화번호", json_schema_extra={"example": "010-1234-5678"})
    role: EnumUserRole = Field(..., description="사용자 역할", json_schema_extra={"example": "OPERATOR"})
    group_id: Optional[int] = Field(None, description="소속 그룹 ID", json_schema_extra={"example": 1})
    is_active: bool = Field(..., description="활성 상태", json_schema_extra={"example": True})
    is_locked: bool = Field(..., description="잠금 상태", json_schema_extra={"example": False})
    lock_reason: Optional[str] = Field(None, description="잠금 사유")
    locked_at: Optional[KSTDatetime] = Field(None, description="잠금 시간")
    last_login_at: Optional[KSTDatetime] = Field(None, description="마지막 로그인 시간", json_schema_extra={"example": "2026-01-01T09:00:00+09:00"})
    last_login_ip: Optional[str] = Field(None, description="마지막 로그인 IP", json_schema_extra={"example": "192.168.1.100"})
    created_at: KSTDatetime = Field(..., description="생성 시간", json_schema_extra={"example": "2026-01-01T09:00:00+09:00"})
    updated_at: KSTDatetime = Field(..., description="수정 시간", json_schema_extra={"example": "2026-01-01T09:00:00+09:00"})

    model_config = {"from_attributes": True}


class AccountUserNestedResponse(BaseModel):
    """Schema for nested user reference (minimal fields for session/group)"""
    id: int
    login_id: str
    name: str
    role: EnumUserRole

    model_config = {"from_attributes": True}


# ============================================================
# UserSession Schemas (AC-4.3)
# ============================================================

class UserSessionResponse(BaseModel):
    """Schema for user session response (PRD_UserSession_Improvement.md v1.2)"""
    id: int
    user_id: int
    # JOIN fields (US-3: AccountUser lookup for better response)
    login_id: Optional[str] = None
    role: Optional[EnumUserRole] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: KSTDatetime
    is_active: bool
    logout_reason: Optional[EnumLogoutReason] = None
    logged_out_at: Optional[KSTDatetime] = None
    # Standard timestamps (renamed from login_at, last_activity)
    created_at: KSTDatetime
    updated_at: Optional[KSTDatetime] = None

    model_config = {"from_attributes": True}


class UserSessionListResponse(BaseModel):
    """Schema for user session list response"""
    sessions: List["UserSessionResponse"]
    total: int


# ============================================================
# UserLoginLog Schemas (AC-5.3)
# ============================================================

class UserLoginLogResponse(BaseModel):
    """Schema for user login log response"""
    id: int
    user_id: Optional[int] = None
    login_id: str
    action: EnumLoginAction
    result: EnumLoginResult
    failure_reason: Optional[EnumLoginFailureReason] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: KSTDatetime

    model_config = {"from_attributes": True}


# ============================================================
# [LEGACY] Legacy User Schemas (users 테이블용 — Deprecated 예정)
# → 신규 코드는 AccountUser 스키마 사용 (AccountUserCreate, AccountUserResponse 등)
# ============================================================

class UserCreate(BaseModel):
    """[LEGACY] Schema for creating a legacy User (users 테이블)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Optional[str] = "user"


class UserResponse(BaseModel):
    """[LEGACY] Schema for legacy User response (users 테이블, excludes password)"""
    id: int
    username: str
    role: EnumUserRole
    created_at: Optional[KSTDatetime] = None
    updated_at: Optional[KSTDatetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """[LEGACY] Schema for JWT token response (Legacy OAuth2 로그인용)"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """[LEGACY] Schema for token payload data (Legacy User의 username 기반)"""
    username: Optional[str] = None


# ============================================================
# Account Auth Schemas (AC-6)
# ============================================================

class AccountLoginRequest(BaseModel):
    """Schema for Account login request (JSON body)"""
    login_id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="로그인 ID",
        json_schema_extra={"example": "admin"}
    )
    password: str = Field(
        ...,
        min_length=1,
        description="비밀번호",
        json_schema_extra={"example": "admin123"}
    )


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request (JSON body)"""
    refresh_token: str = Field(
        ...,
        min_length=1,
        description="리프레시 토큰",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )


class PasswordResetRequest(BaseModel):
    """Schema for admin password reset request"""
    new_password: str = Field(
        ..., min_length=6, max_length=100,
        description="새 비밀번호",
        json_schema_extra={"example": "NewSecureP@ss123!"}
    )


class PasswordChangeRequest(BaseModel):
    """Schema for user password change request"""
    current_password: str = Field(
        ..., min_length=1,
        description="현재 비밀번호",
        json_schema_extra={"example": "OldP@ss123!"}
    )
    new_password: str = Field(
        ..., min_length=6, max_length=100,
        description="새 비밀번호",
        json_schema_extra={"example": "NewSecureP@ss123!"}
    )
