"""
FileGroup schemas: FileGroupCreate, FileGroupUpdate, FileGroupResponse
PRD: PRD_Speaker_Device.md - Section 5.2
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class FileGroupCreate(BaseModel):
    """Schema for creating a new FileGroup"""
    server_id: int
    group_id: int
    group_name: str
    files: Optional[List[str]] = None  # JSONB: ["file1.mp3", "file2.mp3"]


class FileGroupUpdate(BaseModel):
    """Schema for updating a FileGroup (PATCH - all fields optional)"""
    group_name: Optional[str] = None
    files: Optional[List[str]] = None


class FileGroupResponse(BaseModel):
    """Schema for FileGroup response"""
    id: int
    server_id: int
    group_id: int
    group_name: str
    files: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
