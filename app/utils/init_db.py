"""
Database initialization utilities
"""
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.log import ApiLog
from app.utils.auth import hash_password


def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")


def create_admin_user(db: Session):
    """
    Create initial admin user if not exists

    Args:
        db: Database session
    """
    # Check if admin user already exists
    existing_admin = db.query(User).filter(User.username == "admin").first()

    if existing_admin:
        print("✓ Admin user already exists")
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

    print("✓ Admin user created (username: admin, password: admin123)")


def initialize_database():
    """
    Initialize database: create tables and admin user
    """
    print("Initializing database...")

    # Create tables
    create_tables()

    # Create admin user
    db = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()

    print("✓ Database initialization complete")