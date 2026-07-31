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


# ============================================================
# v6.0-clone_deploy_bugfix (#5·#6): startup 스키마 보정 마이그레이션
# ============================================================
# 문제: create_all() 은 "이미 존재하는 테이블"에 새 컬럼을 추가하지 않는다.
#   → 기존 볼륨을 가진 PC(또는 옛 스키마로 만들어진 DB)에서 코드만 git pull 하면
#     모델엔 progress_pct 등이 있지만 DB엔 없어 UndefinedColumnError(500) 발생.
# 해결: startup 에 화이트리스트 idempotent 마이그레이션을 실행한다.
#   ★ 파괴적 마이그레이션(v56_drop_users 등)은 절대 넣지 않는다.
#   ★ 각 SQL 은 IF NOT EXISTS / IF EXISTS 로 재실행 안전해야 한다.
IDEMPOTENT_MIGRATIONS = [
    "v61_report_generation_progress.sql",   # progress_pct/stage/updated_at (ADD COLUMN IF NOT EXISTS)
    "v62_role_normalize.sql",               # account_users.role 옛값(OPERATOR 등) → USER 정규화
    "v63_redact_sensitive_api_log_bodies.sql",  # SEC-01: 과거 api_logs.body 평문 비밀번호/토큰 정리
    "v64_session_token_jti.sql",                # E1/P1-10: refresh_expires_at 추가 + 원문토큰 세션 무효화
    "v65_add_settings_config_enum.sql",         # config enum 에 SETTINGS 보강 (세션설정 변경 500 자가치유, clone 옛볼륨)
    "v66_datetime_to_utc.sql",                  # datetime-unification: naive→timestamptz(UTC 저장). 조건부멱등(naive만 대상), api_logs 제외(v67 재생성)
    "v68_session_client_id.sql",                # session_concurrency: user_sessions.client_id + SSO 예약컬럼(auth_source/idp_subject/idp_session_id)
]


def apply_idempotent_migrations(engine_) -> None:
    """화이트리스트 idempotent 마이그레이션을 **추적 + fail-fast** 로 실행 (PostgreSQL only).

    DB-01 (2026-07-10, 최소 마이그레이션 체계):
    - `schema_migrations` 추적 테이블에 적용 이력(filename·checksum·applied_at) 기록 → 적용 상태 감사 가능.
    - checksum 일치 시 skip(재실행 비용 절감), 파일 변경(checksum 상이) 시 재적용.
    - **fail-fast**: 마이그레이션 실패를 무시하지 않고 예외 전파 → 스키마 드리프트로 조용히 기동하지 않음.
      (본 화이트리스트는 전부 idempotent — IF NOT EXISTS / WHERE 조건부 → 재실행 안전, 실패는 실제 문제.)

    각 파일의 `BEGIN;/COMMIT;` 단독 라인은 psycopg2 자동 트랜잭션과 충돌하므로 제거 후 실행.
    """
    if engine_.dialect.name != "postgresql":
        return
    import os
    import re
    import hashlib
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "migrations")

    # 1) 추적 테이블 보장 + 기적용 목록 로드
    raw = engine_.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "  filename VARCHAR(255) PRIMARY KEY,"
            "  checksum VARCHAR(64) NOT NULL,"
            "  applied_at TIMESTAMP NOT NULL DEFAULT now())"
        )
        raw.commit()
        cur.execute("SELECT filename, checksum FROM schema_migrations")
        applied = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
    finally:
        raw.close()

    for fname in IDEMPOTENT_MIGRATIONS:
        path = os.path.join(migrations_dir, fname)
        if not os.path.exists(path):
            print(f"[WARN] idempotent migration 파일 없음: {fname}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            sql_raw = f.read()
        checksum = hashlib.sha256(sql_raw.encode("utf-8")).hexdigest()
        if applied.get(fname) == checksum:
            print(f"[skip] migration already applied: {fname}")
            continue
        sql = re.sub(r"(?im)^\s*(BEGIN|COMMIT)\s*;\s*$", "", sql_raw)
        if not sql.strip():
            continue
        raw = engine_.raw_connection()
        try:
            cur = raw.cursor()
            cur.execute(sql)  # psycopg2 multi-statement (ADD COLUMN IF NOT EXISTS 등)
            cur.execute(
                "INSERT INTO schema_migrations (filename, checksum) VALUES (%s, %s) "
                "ON CONFLICT (filename) DO UPDATE SET checksum=EXCLUDED.checksum, applied_at=now()",
                (fname, checksum),
            )
            raw.commit()
            cur.close()
            print(f"[OK] migration applied+recorded: {fname}")
        except Exception as e:
            raw.rollback()
            raw.close()
            # DB-01 fail-fast: 조용히 무시하지 않고 기동 중단(스키마 드리프트 방지).
            raise RuntimeError(f"[FATAL] 필수 마이그레이션 실패: {fname}: {e}") from e
        finally:
            try:
                raw.close()
            except Exception:
                pass


# v6.2 (2026-07-05): 기본 관리자 계정 Static seed 정책 승격
# admin(admin123) 외에 팀 매니저 3종 자동 시드. bcrypt 해시로 저장, group_id=NULL(ADMIN bypass).
# password는 dev/시연 기본값 — 프로덕션 배포 시 최초 로그인 후 변경 권장.
DEFAULT_ADMIN_ACCOUNTS = [
    {"login_id": "admin",               "password": "admin123",   "name": "시스템 관리자"},
    # v6.2 (2026-07-05): 팀 매니저 3종
    {"login_id": "m_manager",           "password": "sensorway1", "name": "M 매니저"},
    {"login_id": "vms_manager",         "password": "sensorway1", "name": "VMS 매니저"},
    {"login_id": "popup_manager",       "password": "sensorway1", "name": "팝업 매니저"},
    # v6.0-account_managers_expand (2026-07-06): 장비 도메인별 매니저 5종
    {"login_id": "CameraManager",       "password": "sensorway1", "name": "Camera 매니저"},
    {"login_id": "BroadcastingManager", "password": "sensorway1", "name": "Broadcasting 매니저"},
    {"login_id": "QLiteLampManager",    "password": "sensorway1", "name": "QLiteLamp 매니저"},
    {"login_id": "NVRManager",          "password": "sensorway1", "name": "NVR 매니저"},
    {"login_id": "EnclosureManager",    "password": "sensorway1", "name": "Enclosure 매니저"},
]


def create_admin_account_user(db: Session):
    """기본 ADMIN 계정 Static seed (idempotent).

    - login_id 존재 시 스킵 (편집분 보존)
    - role=ADMIN, group_id=NULL(bypass), is_active=True
    - password는 bcrypt로 해시 저장
    """
    created = 0
    for spec in DEFAULT_ADMIN_ACCOUNTS:
        existing = db.query(AccountUser).filter(AccountUser.login_id == spec["login_id"]).first()
        if existing:
            print(f"[OK] AccountUser {spec['login_id']} already exists")
            continue
        db.add(AccountUser(
            login_id=spec["login_id"],
            password_hash=hash_password(spec["password"]),
            name=spec["name"],
            role="ADMIN",
            is_active=True,
            is_locked=False,
        ))
        created += 1
        print(f"[OK] AccountUser {spec['login_id']} created (role: ADMIN)")
    if created:
        db.commit()


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
    """Async 병존: 기본 ADMIN 계정 Static seed (idempotent).

    sync `create_admin_account_user` 와 동일 계약 — DEFAULT_ADMIN_ACCOUNTS 순회.
    """
    created = 0
    for spec in DEFAULT_ADMIN_ACCOUNTS:
        result = await db.execute(
            select(AccountUser).where(AccountUser.login_id == spec["login_id"])
        )
        if result.scalars().first():
            print(f"[OK] AccountUser {spec['login_id']} already exists")
            continue
        db.add(AccountUser(
            login_id=spec["login_id"],
            password_hash=hash_password(spec["password"]),
            name=spec["name"],
            role="ADMIN",
            is_active=True,
            is_locked=False,
        ))
        created += 1
        print(f"[OK] AccountUser {spec['login_id']} created (role: ADMIN)")
    if created:
        await db.commit()


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