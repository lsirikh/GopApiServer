"""
User Pydantic schemas
PRD: PRD_Account_Design.md Section 4
"""
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.common import KSTDatetime

from app.utils.enums import (
    EnumUserRole, EnumLogoutReason,
    EnumLoginAction, EnumLoginResult, EnumLoginFailureReason,
    EnumPermissionModule, EnumPermissionVerb,
)


# ============================================================
# UserGroup Schemas (AC-2.3)
# ============================================================

# NOTE: 과거 List[str] modules 의 PermissionsSchema(v4.x) 는 v4.9 Phase 3 에서
# 강타입 Dict 구조(아래 PermissionsSchema)로 대체됨. 죽은 중복 정의 제거(R4, WS-B 2026-06-30).


class ModulePermission(BaseModel):
    """RBAC 모듈 권한 — PRD v4.9 Phase 3 (A-2.2/A-2.3/A-2.5)

    - extra="forbid": 미정의 verb (destroy/admin/... ) 전송 시 422 자동 거부
    - StrictBool: "yes"/1/"true" 문자열 truthy 차단 — 명시적 true/false만 허용
    - control: CAMERAS 모듈 전용 (PTZ/녹화 등)
    """
    model_config = ConfigDict(extra="forbid")

    view: Optional[StrictBool] = Field(None, description="조회 권한")
    edit: Optional[StrictBool] = Field(None, description="생성/수정 권한")
    delete: Optional[StrictBool] = Field(None, description="삭제 권한")
    control: Optional[StrictBool] = Field(None, description="제어 권한 (cameras 전용)")


class PermissionsSchema(BaseModel):
    """RBAC 권한 전체 구조 — PRD v4.9 Phase 3 (A-2.1)

    - modules: Dict[EnumPermissionModule, ModulePermission] — 미정의 모듈 키 422 차단
    - device_groups: 접근 가능 그룹 ID
    - time_restriction: 시간대 제한 (v5.0 권고)
    """
    model_config = ConfigDict(extra="forbid")

    modules: Optional[Dict[EnumPermissionModule, ModulePermission]] = Field(
        None, description="모듈별 권한 (devices/events/reports/cameras/users/user_groups/audit_logs/servers)"
    )
    # P1-03 (2026-07-09): 아래 두 필드는 **서버측 미집행(UI 메타데이터)**. 저장/노출만 되고
    # 실제 인가(row-level scope / 시간대 차단)에는 반영되지 않는다. 보안 기능으로 오인 금지.
    # (집행 구현은 별도 PRD — 매 요청 device scope 필터 / time_restriction 게이트.)
    device_groups: Optional[List[int]] = Field(None, description="접근 가능한 디바이스 그룹 ID 목록 (⚠ 서버 미집행 — UI 메타데이터)")
    time_restriction: Optional[Dict[str, Any]] = Field(None, description="시간대 제한 (v5.0) (⚠ 서버 미집행 — UI 메타데이터)")


class UserGroupCreate(BaseModel):
    """Schema for creating a new user group

    PRD v4.9 Phase 3 (A-2): permissions 강타입 PermissionsSchema 적용
    - 미정의 모듈 키 (super_admin/system 등) → 422
    - 미정의 verb (destroy/admin) → 422
    - StrictBool 강제 → "yes"/1 등 truthy 차단
    """
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ..., min_length=1, max_length=100,
        description="그룹 이름",
        json_schema_extra={"example": "1중대 운영팀"}
    )
    description: Optional[str] = Field(
        None, description="그룹 설명",
        json_schema_extra={"example": "1중대 경계 시스템 운영 담당"}
    )
    permissions: Optional[PermissionsSchema] = Field(
        None, description="권한 설정 (PermissionsSchema 강타입)",
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
    """Schema for updating a user group (all fields optional)

    PRD v4.8 Phase 12-7a (RBAC permissions immutability — P0):
    - permissions 필드 제거 — 일반 PATCH로 권한 변경 차단 (권한 상승 공격 차단)
    - extra="forbid": permissions 전송 시 422 자동 거부
    - 권한 변경은 향후 전용 admin 엔드포인트(POST /user-groups/{id}/permissions)로만 허용 권고 (v5.0)
    """
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
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
        ..., min_length=8,
        description="비밀번호 (P2-01: 최소 8자)",
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
    role: Optional[EnumUserRole] = Field(
        EnumUserRole.USER,
        description="사용자 역할 (v5.3 Phase 2: ADMIN | USER 2종만 허용)",
        json_schema_extra={"example": "USER"}
    )
    group_id: Optional[int] = Field(
        None, description="소속 그룹 ID (USER role일 때 UserGroupGrant로 permission 결정)",
        json_schema_extra={"example": 1}
    )


class AccountUserSelfUpdate(BaseModel):
    """Schema for self-update via PUT /users/me (PRD v4.8 Phase 12-7c)

    - role/group_id/is_active/is_locked 등 권한 상승 가능 필드 제거
    - extra="forbid": 권한 필드 전송 시 422 자동 거부
    - 본 스키마는 /me 경로 전용. /users/{id} (admin 경로)는 AccountUserUpdate 사용
    """
    model_config = ConfigDict(extra="forbid")

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
    photo_url: Optional[str] = Field(
        None, description="프로필 사진 URL"
    )
    phone: Optional[str] = Field(
        None, description="전화번호",
        json_schema_extra={"example": "010-1234-5678"}
    )

    @field_validator("photo_url")
    @classmethod
    def validate_photo_url_scheme(cls, v):
        """PRD v4.9 Phase 4 (A-1.2): photo_url XSS validator

        허용: http:// / https:// / /api/users/photo/* (서버 자체 서빙 경로) / None
        차단: javascript: / data: / vbscript: / file: / about: / 기타 스킴 → 422

        v6.3-profile_photo_crud (2026-07-13): 허용 상대경로를 실제 서빙 경로(/api/users/photo/)로
        정정. 종전 /static/profiles/ 는 실존하지 않는 경로(StaticFiles 미마운트)여서, 서버가 응답에
        채우는 default(/api/users/photo/default.png)를 클라가 되받아 PUT /me 로 보낼 때 422 로 거부되던
        버그를 유발했다(서버가 emit 하는 값을 서버가 되받지 못함).
        """
        if v is None or v == "":
            return v
        v_lower = v.strip().lower()
        # 명시적 차단 스킴
        for forbidden in ("javascript:", "data:", "vbscript:", "file:", "about:"):
            if v_lower.startswith(forbidden):
                raise ValueError(f"photo_url scheme '{forbidden[:-1]}' is not allowed (XSS prevention)")
        # 허용 패턴: http(s):// 또는 실제 서빙 경로 /api/users/photo/ 시작
        if not (v_lower.startswith("http://") or v_lower.startswith("https://") or v_lower.startswith("/api/users/photo/")):
            raise ValueError("photo_url must start with http://, https://, or /api/users/photo/")
        return v


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
    role: Optional[EnumUserRole] = Field(
        None,
        description="사용자 역할 (v5.3 Phase 2: ADMIN | USER 2종만 허용)",
        json_schema_extra={"example": "USER"}
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
    # v6.0-users_role_response_relax (2026-07-06): EnumUserRole → str 완화.
    # v5.3 Phase 2에서 EnumUserRole 축소(5종 → ADMIN/USER)했으나 DB에 옛 값(OPERATOR/MAINTAINER/VIEWER/GUEST)
    # 남은 사이트가 있어 목록 응답 시 pydantic 검증 실패로 500 발생. 응답 관대 원칙(Postel's Law).
    role: str = Field(..., description="사용자 역할 (ADMIN/USER, 옛 데이터는 OPERATOR/MAINTAINER/VIEWER/GUEST 가능)", json_schema_extra={"example": "USER"})
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

    @model_validator(mode="after")
    def _fill_default_photo(self) -> "AccountUserResponse":
        # v6.0-default_profile_image (2026-07-07): 사진 미설정 계정은 default 이미지 URL 제공.
        # 상대 경로 → 클라가 base_url 과 조합. 서빙 엔드포인트가 default.png 를 반환(startup 자동 생성).
        if not self.photo_url:
            self.photo_url = "/api/users/photo/default.png"
        return self


class AccountUserNestedResponse(BaseModel):
    """Schema for nested user reference (minimal fields for session/group)

    v6.0-users_role_response_relax (2026-07-06): role Enum → str (AccountUserResponse와 동일 이유).
    """
    id: int
    login_id: str
    name: str
    role: str

    model_config = {"from_attributes": True}


# ============================================================
# UserSession Schemas (AC-4.3)
# ============================================================

class UserSessionResponse(BaseModel):
    """Schema for user session response (PRD_UserSession_Improvement.md v1.2)

    v6.0-users_role_response_relax (2026-07-06): role Enum → str (동일 완화).
    """
    id: int
    user_id: int
    # JOIN fields (US-3: AccountUser lookup for better response)
    login_id: Optional[str] = None
    role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: KSTDatetime
    is_active: bool
    logout_reason: Optional[str] = None  # v6.0-response_schema_audit: Enum→str (String 컬럼 지뢰)
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
    """Schema for user login log response

    v6.0-response_schema_audit (2026-07-07): action/result/failure_reason Enum→str.
    user_login_logs 컬럼이 String 이라 옛/임의 값 저장 가능 → strict Enum 응답이면 목록 500.
    """
    id: int
    user_id: Optional[int] = None
    login_id: str
    action: str
    result: str
    failure_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: KSTDatetime

    model_config = {"from_attributes": True}


# v5.3 (2026-07-02): Legacy UserCreate / UserResponse 삭제 (users 테이블 폐기)
# → AccountUserCreate / AccountUserResponse 사용


class Token(BaseModel):
    """Schema for JWT token response (access_token + token_type)"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token payload data

    PRD v4.9 Phase 2-A4: jti + token_type 추가 (블랙리스트 + refresh 가드)
    PRD Force_Logout FR-SVF-02: sid 추가 (세션 식별자 = UserSession.id, refresh 시 불변)
    """
    username: Optional[str] = None
    jti: Optional[str] = None  # JWT ID (블랙리스트 키)
    token_type: Optional[str] = None  # "refresh" or None (access)
    sid: Optional[str] = None  # session id (== UserSession.id), refresh로 회전하지 않음


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
        ..., min_length=8, max_length=100,
        description="새 비밀번호 (P2-01: 최소 8자)",
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
        ..., min_length=8, max_length=100,
        description="새 비밀번호 (P2-01: 최소 8자)",
        json_schema_extra={"example": "NewSecureP@ss123!"}
    )
