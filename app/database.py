"""
Database connection setup using SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,        # 기본 커넥션 수 (기존 SQLite 기본값 5에서 확장)
    max_overflow=20,     # 최대 초과 커넥션 수 (총 30커넥션)
    pool_timeout=30,     # 커넥션 대기 타임아웃 (초)
    pool_pre_ping=True,  # 커넥션 유효성 사전 확인 (stale connection 방지)
    pool_recycle=1800,   # 30분마다 커넥션 재생성 (idle 커넥션 정리)
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()
