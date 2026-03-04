"""
Thumbnail schemas: ThumbnailResponse

PRD: PRD_Thumbnail_Image.md v1.1
"""
from pydantic import BaseModel, ConfigDict, computed_field
from datetime import datetime
from app.schemas.common import KSTDatetime
from typing import Optional


class ThumbnailResponse(BaseModel):
    """Thumbnail metadata response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: KSTDatetime

    @computed_field
    @property
    def image_url(self) -> str:
        return f"/api/thumbnails/images/{self.file_name}"
