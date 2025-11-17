"""
Integration models: EventMapping
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class EventMapping(Base):
    """EventMapping model for integration settings"""
    __tablename__ = "event_mappings"

    id = Column(Integer, primary_key=True, index=True)
    name_event = Column(String, nullable=False)
    group_event = Column(String, nullable=False)
    category_event = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
