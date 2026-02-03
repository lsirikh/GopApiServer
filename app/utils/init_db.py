"""
Database initialization utilities
"""
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
# NOTE: User는 레거시 모델 (users 테이블). 신규 코드는 AccountUser (account_users 테이블) 사용할 것.
from app.models.user import User, AccountUser
from app.models.log import ApiLog
from app.utils.auth import hash_password
from app.utils.init_server_data import initialize_server_data
from app.utils.init_report_data import initialize_report_data
from app.utils.init_sample_data import initialize_sample_data


def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")


def create_admin_user(db: Session):
    """
    [LEGACY] Create initial admin user if not exists (Legacy User / users 테이블)
    → 신규 admin은 create_admin_account_user()에서 생성 (AccountUser / account_users 테이블)

    Args:
        db: Database session
    """
    # Check if admin user already exists
    existing_admin = db.query(User).filter(User.username == "admin").first()

    if existing_admin:
        print("[OK] Admin user already exists")
        return

    # Create admin user
    admin_user = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        role="admin"
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    print("[OK] Admin user created (username: admin, password: admin123)")


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
        create_admin_user(db)
        create_admin_account_user(db)
        initialize_server_data(db)
        initialize_report_data(db)
        initialize_sample_data(db)
    finally:
        db.close()

    print("[OK] Database initialization complete")