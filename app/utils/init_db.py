"""
Database initialization utilities
"""
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.log import ApiLog
from app.utils.auth import hash_password
from app.utils.init_server_data import initialize_server_data


def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")


def create_admin_user(db: Session):
    """
    Create initial admin user if not exists

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
        initialize_server_data(db)
    finally:
        db.close()

    print("[OK] Database initialization complete")