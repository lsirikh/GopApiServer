"""
Database initialization utilities
"""
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
# v5.3 (2026-07-02): Legacy User 삭제. AccountUser (account_users)로 완전 통일.
from app.models.user import AccountUser, UserGroup
from app.models.log import ApiLog
from app.utils.auth import hash_password
from app.utils.init_server_data import initialize_server_data
from app.utils.init_report_data import initialize_report_data
from app.utils.init_sample_data import initialize_sample_data
from app.config import settings


def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")


def create_admin_account_user(db: Session):
    """
    Create initial AccountUser admin if not exists

    Args:
        db: Database session
    """
    # Check if admin AccountUser already exists
    existing_admin = db.query(AccountUser).filter(AccountUser.login_id == "admin").first()

    if existing_admin:
        print("[OK] AccountUser admin already exists")
        return

    # Create admin AccountUser
    admin_account = AccountUser(
        login_id="admin",
        password_hash=hash_password("admin123"),
        name="시스템 관리자",
        role="ADMIN",
        is_active=True,
        is_locked=False
    )

    db.add(admin_account)
    db.commit()
    db.refresh(admin_account)

    print("[OK] AccountUser admin created (login_id: admin, password: admin123)")


def ensure_role_permission_groups(db: Session):
    """역할(등급) = 권한 단위 모델 (PRD-GOP-01 OQ-PG-01 = Option A).

    5개 역할명 등급 그룹(ADMIN/MAINTAINER/OPERATOR/VIEWER/GUEST)을 idempotent 보장한다.
    - 없으면 PRD §6-1 기반 기본 매트릭스(8모듈×4동작)로 생성, 있으면 유지(ADMIN 편집분 보존).
    - 로그인은 user.role 명으로 이 그룹의 매트릭스를 사용(auth.py). 기존 임의 팀그룹은 건드리지 않음(비파괴).
    - audit_logs 는 append-only → delete 항상 false.
    """
    FULL = {"view": True,  "edit": True,  "delete": True,  "control": True}
    RWC  = {"view": True,  "edit": True,  "delete": False, "control": True}
    RC   = {"view": True,  "edit": False, "delete": False, "control": True}
    RW   = {"view": True,  "edit": True,  "delete": False, "control": False}
    R    = {"view": True,  "edit": False, "delete": False, "control": False}
    NO   = {"view": False, "edit": False, "delete": False, "control": False}
    AUDIT_ADMIN = {"view": True, "edit": True,  "delete": False, "control": True}   # append-only(삭제 금지)
    AUDIT_VIEW  = {"view": True, "edit": False, "delete": False, "control": False}

    # 8 modules: devices, events, reports, cameras, users, user_groups, audit_logs, servers
    role_perms = {
        "ADMIN":      {"devices": FULL, "events": FULL, "reports": FULL, "cameras": FULL,
                       "users": FULL, "user_groups": FULL, "audit_logs": AUDIT_ADMIN, "servers": FULL},
        "MAINTAINER": {"devices": FULL, "events": FULL, "reports": RW,   "cameras": FULL,
                       "users": NO,   "user_groups": NO,   "audit_logs": AUDIT_VIEW,  "servers": NO},
        "OPERATOR":   {"devices": R,    "events": RC,   "reports": RW,   "cameras": RC,
                       "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
        "VIEWER":     {"devices": R,    "events": R,    "reports": R,    "cameras": R,
                       "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
        "GUEST":      {"devices": NO,   "events": NO,   "reports": NO,   "cameras": R,
                       "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
    }
    desc = {"ADMIN": "관리자(전체)", "MAINTAINER": "유지보수자", "OPERATOR": "운영자",
            "VIEWER": "조회자", "GUEST": "게스트"}

    created = 0
    for role, mods in role_perms.items():
        if db.query(UserGroup).filter(UserGroup.name == role).first():
            continue  # 이미 존재 → 유지(편집분 보존)
        db.add(UserGroup(name=role, description=f"권한 등급 — {desc[role]}",
                         permissions={"modules": mods}, is_active=True))
        created += 1
    if created:
        db.commit()
    print(f"[OK] Role permission groups ensured (created {created}/5)")

    # R10③ (ADR_Permission_Model_v5.2): admin 사용자를 ADMIN 그룹에 배정.
    # name==role 폐기(R10①) 후 권한 원천 = group_id. 미배정 admin 은 로그인 payload permissions 빈값
    # (서버 ADMIN bypass 는 정상이라 기능 무영향 — 클라 UI 표시 일관성 위해 배정). 멱등.
    admin_group = db.query(UserGroup).filter(UserGroup.name == "ADMIN").first()
    admin_user = db.query(AccountUser).filter(AccountUser.login_id == "admin").first()
    if admin_group and admin_user and admin_user.group_id is None:
        admin_user.group_id = admin_group.id
        db.commit()
        print(f"[OK] admin user assigned to ADMIN group (id={admin_group.id})")


def initialize_database():
    """
    Initialize database: create tables and admin user
    """
    print("Initializing database...")

    # Create tables
    create_tables()

    # Create admin user and initialize server data
    db = SessionLocal()
    try:
        create_admin_account_user(db)
        ensure_role_permission_groups(db)
        initialize_server_data(db)
        initialize_report_data(db)
        if settings.INIT_SAMPLE_DATA:
            initialize_sample_data(db)
        else:
            print("[SKIP] Sample data (INIT_SAMPLE_DATA=false)")
    finally:
        db.close()

    print("[OK] Database initialization complete")