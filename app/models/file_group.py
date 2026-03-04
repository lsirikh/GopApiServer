"""
FileGroup model: 방송음원 파일풀 관리
PRD: PRD_Speaker_Device.md - Section 4.4, 4.5

FileGroup stores broadcast audio file pools for Speaker servers.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings


class FileGroup(Base):
    """
    FileGroup model for managing broadcast audio file pools.

    Attributes:
        id: Primary key
        server_id: FK to Server (SPEAKER_API type), CASCADE on delete
        group_id: File group ID from broadcast server
        group_name: File group name (e.g., "화재경보")
        files: JSONB array of file names (e.g., ["music01.mp3", "music02.mp3"])
        created_at: Creation timestamp
        updated_at: Last update timestamp

    Constraints:
        - UNIQUE(server_id, group_id)
    """
    __tablename__ = "file_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    server_id = Column(
        Integer,
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    group_id = Column(Integer, nullable=False)
    group_name = Column(String(100), nullable=False)
    files = Column(JSON, nullable=True)  # JSONB array: ["file1.mp3", "file2.mp3"]

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Unique constraint: (server_id, group_id)
    __table_args__ = (
        UniqueConstraint('server_id', 'group_id', name='uq_file_groups_server_group'),
    )

    # Relationship to Server
    server = relationship("Server", foreign_keys=[server_id])

    # Relationship to EventMappingSpeaker (PRD: PRD_EventMappingSpeaker.md v1.0)
    event_mapping_speakers = relationship("EventMappingSpeaker", back_populates="file_group")

    def __repr__(self):
        return (
            f"<FileGroup(id={self.id}, server_id={self.server_id}, "
            f"group_id={self.group_id}, group_name='{self.group_name}')>"
        )
