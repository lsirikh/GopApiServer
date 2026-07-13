"""
User Model for authentication
PRD: PRD_Account_Design.md Section 4
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.config import settings


class UserGroup(Base):
    """
    UserGroup model for user permission groups
    PRD: PRD_Account_Design.md Section 4.1
    """
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Audit fields (FK to User - defined later via Integer for now)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationship to users
    users = relationship("AccountUser", back_populates="group")
    # FR-01: 시간기반 부여(grant) — 그룹 삭제 시 부여도 정리
    grants = relationship("UserGroupGrant", back_populates="group", cascade="all, delete-orphan")


class AccountUser(Base):
    """
    Account User model (PRD_Account_Design.md compliant)
    PRD: PRD_Account_Design.md Section 4.2
    """
    __tablename__ = "account_users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Login credentials
    login_id = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Personal info
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employee_number = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)

    # Role and Group
    # v6.0-role_seed_normalize (2026-07-07): default VIEWER → USER (v5.3 role 2종 축소 정합).
    # VIEWER 는 v5.3 Phase 2 에서 폐지된 레거시 값 — 미지정 생성 시 옛 값이 들어가던 지뢰.
    role = Column(String(20), default="USER", nullable=False)
    group_id = Column(Integer, ForeignKey("user_groups.id", ondelete="SET NULL"), nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    lock_reason = Column(String(255), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    locked_by = Column(Integer, nullable=True)

    # Password policy fields
    password_changed_at = Column(DateTime, nullable=True)
    password_expires_at = Column(DateTime, nullable=True)
    failed_login_count = Column(Integer, default=0, nullable=False)

    # Last login fields
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 length

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Audit fields
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationships
    group = relationship("UserGroup", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    login_logs = relationship("UserLoginLog", back_populates="user")
    # FR-01: 시간기반 권한그룹 부여 — 사용자 삭제 시 부여도 CASCADE
    grants = relationship("UserGroupGrant", back_populates="user", cascade="all, delete-orphan")

    # Report System relationships (PRD: PRD_Report_System.md)
    report_templates = relationship("ReportTemplate", back_populates="owner")
    report_generations = relationship("ReportGeneration", back_populates="generator")

    def __repr__(self):
        return f"<AccountUser(login_id='{self.login_id}', role='{self.role}')>"


class UserGroupGrant(Base):
    """
    UserGroupGrant — 사용자에게 권한그룹을 기간을 정해 부여(시간기반 스케쥴링)
    PRD: PRD_Permission_Group_Scheduling.md §3.3 (FR-01)

    설계 원칙:
    - 스케쥴은 "그룹 정의"가 아니라 "부여(assignment)"에 건다(등급그룹 전체 만료 방지).
    - 권위 판정은 요청 시점 계산(valid_from <= now < valid_until). is_active 는 sweep 비정규화(표시·통지용).
    - valid_until = NULL → 상시(무기한). revoked_at = soft 회수(물리삭제 금지).
    """
    __tablename__ = "user_group_grants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 부여 대상 사용자 / 부여 그룹 (둘 다 삭제 시 CASCADE)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False, index=True)

    # 유효 기간 — valid_until NULL = 상시
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)

    # sweep 비정규화 플래그(표시/통지용). 인가 권위는 valid_until > now 계산이 담당.
    is_active = Column(Boolean, default=True, nullable=False)

    # 감사 — 부여한 ADMIN / soft 회수 시각
    granted_by = Column(Integer, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationships
    user = relationship("AccountUser", back_populates="grants")
    group = relationship("UserGroup", back_populates="grants")

    def __repr__(self):
        return f"<UserGroupGrant(user_id={self.user_id}, group_id={self.group_id}, valid_until={self.valid_until})>"


class UserSession(Base):
    """
    User Session model for tracking active sessions
    PRD: PRD_Account_Design.md Section 4.3
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User FK (CASCADE delete)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token fields (E1/P1-10, 2026-07-10): 원문 JWT 대신 **jti**(식별자) 저장.
    # jti 는 서명 없는 비-크리덴셜이라 DB 열람만으로 토큰 위조 불가 → 원문 노출 제거.
    # token=access jti, refresh_token=refresh jti. revoke/force_logout 은 이 값을 직접 블랙리스트.
    token = Column(String(500), unique=True, nullable=False, index=True)          # access jti
    refresh_token = Column(String(500), unique=True, nullable=True)               # refresh jti

    # Connection info
    ip_address = Column(String(45), nullable=True)  # IPv6 length
    user_agent = Column(String(500), nullable=True)

    # Time fields
    expires_at = Column(DateTime, nullable=False)                    # access token 만료(블랙리스트 TTL 원천)
    refresh_expires_at = Column(DateTime, nullable=True)             # E1: refresh 만료(블랙리스트 TTL)
    logged_out_at = Column(DateTime, nullable=True)

    # Standard timestamps (PRD_UserSession_Improvement.md v1.2)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)  # was: login_at
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=True)   # was: last_activity

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    logout_reason = Column(String(50), nullable=True)  # EnumLogoutReason value
    forced_by = Column(Integer, nullable=True)  # User ID who forced logout

    # Relationships
    user = relationship("AccountUser", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, is_active={self.is_active})>"


class UserLoginLog(Base):
    """
    User Login Log model for audit logging
    PRD: PRD_Account_Design.md Section 4.4
    """
    __tablename__ = "user_login_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User FK (SET NULL on delete - preserve logs even after user deletion)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Login ID preserved for audit (even if user is deleted)
    login_id = Column(String(50), nullable=False, index=True)

    # Action and result
    action = Column(String(20), nullable=False)  # EnumLoginAction value
    result = Column(String(20), nullable=False)  # EnumLoginResult value
    failure_reason = Column(String(50), nullable=True)  # EnumLoginFailureReason value

    # Connection info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False, index=True)

    # Relationships
    user = relationship("AccountUser", back_populates="login_logs")

    def __repr__(self):
        return f"<UserLoginLog(login_id='{self.login_id}', action='{self.action}', result='{self.result}')>"


# v5.3 (2026-07-02): Legacy User 모델 삭제 (GIS 팀 요청 대응, PRD_Legacy_User_Removal)
# → AccountUser (account_users 테이블)로 완전 통일. FK 참조 0건 확인 후 DB DROP TABLE users.
