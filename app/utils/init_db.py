"""
Database initialization utilities
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, AsyncSessionLocal, Base
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
    """Preset 권한 그룹(3건) idempotent 보장 — v5.3 Phase 2 (Role 축소).

    v5.3 Phase 2 변경 (PRD_Role_Simplification):
    - EnumUserRole 축소 (5종 → 2종: ADMIN/USER).
    - 등급 그룹 5건 → Preset 그룹 3건 + ADMIN/GUEST 삭제.
    - 신규 생성 이름: "Preset - 유지보수자/운영자/조회자" (v5.2 R10① name==role 폐기 반영).
    - admin 사용자는 group_id=NULL (bypass라 그룹 매트릭스 무관).
    - 팀 그룹(운영팀/관제팀/유지보수팀)은 별도 시드에서 관리.
    - audit_logs 는 append-only → delete 항상 false.

    ★ 신규 down -v 후 재시드 시에도 v5.4 이름/매트릭스로 생성 보장.
    ★ 기존 그룹(v5.3 이전 이름)이 있으면 유지(편집분 보존, 마이그레이션 v57에서 rename 처리).
    """
    FULL = {"view": True,  "edit": True,  "delete": True,  "control": True}
    RC   = {"view": True,  "edit": False, "delete": False, "control": True}
    RW   = {"view": True,  "edit": True,  "delete": False, "control": False}
    R    = {"view": True,  "edit": False, "delete": False, "control": False}
    NO   = {"view": False, "edit": False, "delete": False, "control": False}
    AUDIT_VIEW  = {"view": True, "edit": False, "delete": False, "control": False}

    # v5.3 Phase 2: Preset 3건 (팀 그룹은 별도 시드)
    preset_perms = {
        "Preset - 유지보수자": {"devices": FULL, "events": FULL, "reports": RW,   "cameras": FULL,
                                "users": NO,   "user_groups": NO,   "audit_logs": AUDIT_VIEW,  "servers": NO},
        "Preset - 운영자":     {"devices": R,    "events": RC,   "reports": RW,   "cameras": RC,
                                "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
        "Preset - 조회자":     {"devices": R,    "events": R,    "reports": R,    "cameras": R,
                                "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
    }
    desc = {
        "Preset - 유지보수자": "표준 프리셋 — 유지보수자 권한 매트릭스 (참고 배정용)",
        "Preset - 운영자":     "표준 프리셋 — 운영자 권한 매트릭스 (참고 배정용)",
        "Preset - 조회자":     "표준 프리셋 — 조회자 권한 매트릭스 (참고 배정용)",
    }

    created = 0
    for name, mods in preset_perms.items():
        if db.query(UserGroup).filter(UserGroup.name == name).first():
            continue  # 이미 존재 → 유지 (편집분 보존)
        db.add(UserGroup(name=name, description=desc[name],
                         permissions={"modules": mods}, is_active=True))
        created += 1
    if created:
        db.commit()
    print(f"[OK] Preset permission groups ensured (created {created}/3)")

    # v5.3 Phase 2: ADMIN 사용자는 group_id=NULL (bypass라 매트릭스 무관).
    # v5.3 Phase 1까지 admin.group_id=10(ADMIN 그룹)이었으나 v5.3 Phase 2에서 ADMIN 등급 그룹 삭제 → NULL.
    # 마이그레이션 v57에서 이미 처리하지만 idempotent 보장.
    admin_user = db.query(AccountUser).filter(AccountUser.login_id == "admin").first()
    if admin_user and admin_user.group_id is not None:
        # ADMIN 등급 그룹(id=10)이 이미 삭제된 상태라면 group_id 참조 무효 → NULL
        if not db.query(UserGroup).filter(UserGroup.id == admin_user.group_id).first():
            admin_user.group_id = None
            db.commit()
            print(f"[OK] admin user group_id set to NULL (ADMIN bypass, no group needed)")


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


# ============================================================
# v6.0 P8 후속 Phase 2 — Async 병존 함수 (Dual-stack)
# ============================================================
# 원칙:
# - sync 함수는 유지 (테스트 등 caller 호환)
# - 아래 _async 접미사 함수는 신규 async 경로 (FastAPI startup 등에서 사용)
# - Base.metadata.create_all / downstream sync seed(init_server/report/sample) 는
#   sync SessionLocal 을 그대로 유지 (해당 파일들은 아직 sync 전용)
# ============================================================


async def create_admin_account_user_async(db: AsyncSession) -> None:
    """Async 병존: 초기 AccountUser admin 생성 (idempotent).

    Args:
        db: AsyncSession
    """
    # Check if admin AccountUser already exists
    result = await db.execute(
        select(AccountUser).where(AccountUser.login_id == "admin")
    )
    existing_admin = result.scalars().first()

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
        is_locked=False,
    )

    db.add(admin_account)
    await db.commit()
    await db.refresh(admin_account)

    print("[OK] AccountUser admin created (login_id: admin, password: admin123)")


async def ensure_role_permission_groups_async(db: AsyncSession) -> None:
    """Async 병존: Preset 권한 그룹(3건) idempotent 보장.

    sync `ensure_role_permission_groups` 와 동일한 매트릭스/시맨틱.
    """
    FULL = {"view": True,  "edit": True,  "delete": True,  "control": True}
    RC   = {"view": True,  "edit": False, "delete": False, "control": True}
    RW   = {"view": True,  "edit": True,  "delete": False, "control": False}
    R    = {"view": True,  "edit": False, "delete": False, "control": False}
    NO   = {"view": False, "edit": False, "delete": False, "control": False}
    AUDIT_VIEW = {"view": True, "edit": False, "delete": False, "control": False}

    preset_perms = {
        "Preset - 유지보수자": {"devices": FULL, "events": FULL, "reports": RW,   "cameras": FULL,
                                "users": NO,   "user_groups": NO,   "audit_logs": AUDIT_VIEW,  "servers": NO},
        "Preset - 운영자":     {"devices": R,    "events": RC,   "reports": RW,   "cameras": RC,
                                "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
        "Preset - 조회자":     {"devices": R,    "events": R,    "reports": R,    "cameras": R,
                                "users": NO,   "user_groups": NO,   "audit_logs": NO,          "servers": NO},
    }
    desc = {
        "Preset - 유지보수자": "표준 프리셋 — 유지보수자 권한 매트릭스 (참고 배정용)",
        "Preset - 운영자":     "표준 프리셋 — 운영자 권한 매트릭스 (참고 배정용)",
        "Preset - 조회자":     "표준 프리셋 — 조회자 권한 매트릭스 (참고 배정용)",
    }

    created = 0
    for name, mods in preset_perms.items():
        existing = (
            await db.execute(select(UserGroup).where(UserGroup.name == name))
        ).scalars().first()
        if existing:
            continue  # 이미 존재 → 유지 (편집분 보존)
        db.add(UserGroup(
            name=name,
            description=desc[name],
            permissions={"modules": mods},
            is_active=True,
        ))
        created += 1
    if created:
        await db.commit()
    print(f"[OK] Preset permission groups ensured (created {created}/3)")

    # v5.3 Phase 2: ADMIN 사용자는 group_id=NULL (bypass) 보장
    admin_user = (
        await db.execute(select(AccountUser).where(AccountUser.login_id == "admin"))
    ).scalars().first()
    if admin_user and admin_user.group_id is not None:
        exists_group = (
            await db.execute(select(UserGroup).where(UserGroup.id == admin_user.group_id))
        ).scalars().first()
        if not exists_group:
            admin_user.group_id = None
            await db.commit()
            print("[OK] admin user group_id set to NULL (ADMIN bypass, no group needed)")


async def initialize_database_async() -> None:
    """Async 병존: 테이블 생성 + admin seed + preset groups.

    Notes:
        - Base.metadata.create_all 은 sync engine 유지 (DDL은 async 불필요).
        - 하위 시드(init_server_data / init_report_data / init_sample_data) 는
          아직 sync 전용 → sync SessionLocal 로 실행 (병행 dual-stack).
        - admin / preset groups 만 AsyncSessionLocal 기반으로 실행.
    """
    print("Initializing database (async)...")

    # Create tables (sync — DDL)
    create_tables()

    # Async path: admin + preset groups
    async with AsyncSessionLocal() as adb:
        await create_admin_account_user_async(adb)
        await ensure_role_permission_groups_async(adb)

    # Sync path: downstream seeds (아직 sync 전용)
    db = SessionLocal()
    try:
        initialize_server_data(db)
        initialize_report_data(db)
        if settings.INIT_SAMPLE_DATA:
            initialize_sample_data(db)
        else:
            print("[SKIP] Sample data (INIT_SAMPLE_DATA=false)")
    finally:
        db.close()

    print("[OK] Database initialization complete (async)")