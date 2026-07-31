"""
Thumbnail model: 카메라 썸네일 이미지 메타데이터 저장

PRD: PRD_Thumbnail_Image.md v1.1
- file_name: 클라이언트 지정 파일명 (UNIQUE)
- 파일 저장 경로: {THUMBNAIL_STORAGE_PATH}/{YYYY-MM-DD}/{client_file_name}
- DetectionEvent와 FK 없이 연결 (detail.thumbnail URL 참조)
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime as dt

from app.database import Base
from app.models.types import UtcDateTime
from app.config import settings


class Thumbnail(Base):
    __tablename__ = "thumbnails"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_path = Column(String(500), nullable=False, doc="파일 시스템 경로")
    file_name = Column(String(200), nullable=False, unique=True, index=True, doc="클라이언트 지정 파일명")
    file_size = Column(Integer, nullable=False, doc="파일 크기 (bytes)")
    mime_type = Column(String(50), nullable=False, doc="MIME 타입")
    width = Column(Integer, nullable=True, doc="이미지 너비 (px)")
    height = Column(Integer, nullable=True, doc="이미지 높이 (px)")
    created_at = Column(
        UtcDateTime,
        default=lambda: dt.now(settings.tz).replace(tzinfo=None),
        nullable=False,
        index=True,
        doc="생성 시간"
    )

    def __repr__(self):
        return (
            f"<Thumbnail(id={self.id}, "
            f"file_name='{self.file_name}')>"
        )
