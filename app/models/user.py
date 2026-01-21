"""
User Model for authentication
PRD: PRD_Account_Design.md Section 4
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
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
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Audit fields (FK to User - defined later via Integer for now)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationship to users
    users = relationship("AccountUser", back_populates="group")


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
    role = Column(String(20), default="VIEWER", nullable=False)
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
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Audit fields
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationships
    group = relationship("UserGroup", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    login_logs = relationship("UserLoginLog", back_populates="user")

    def __repr__(self):
        return f"<AccountUser(login_id='{self.login_id}', role='{self.role}')>"


class UserSession(Base):
    """
    User Session model for tracking active sessions
    PRD: PRD_Account_Design.md Section 4.3
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User FK (CASCADE delete)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token fields
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True)

    # Connection info
    ip_address = Column(String(45), nullable=True)  # IPv6 length
    user_agent = Column(String(500), nullable=True)

    # Time fields
    expires_at = Column(DateTime, nullable=False)
    logged_out_at = Column(DateTime, nullable=True)

    # Standard timestamps (PRD_UserSession_Improvement.md v1.2)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)  # was: login_at
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=True)   # was: last_activity

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
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False, index=True)

    # Relationships
    user = relationship("AccountUser", back_populates="login_logs")

    def __repr__(self):
        return f"<UserLoginLog(login_id='{self.login_id}', action='{self.action}', result='{self.result}')>"


# Legacy User model (to be deprecated - will be replaced by AccountUser)
class User(Base):
    """
    Legacy User model for authentication.
    TODO: Migrate to AccountUser and remove this class.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # "admin" or "user"
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
