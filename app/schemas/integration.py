"""
Integration schemas: EventMapping
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class EventMappingCreate(BaseModel):
    """Schema for creating a new EventMapping"""
    name_event: str
    group_event: str
    category_event: str
    description: Optional[str] = None
    status: bool = True


class EventMappingResponse(BaseModel):
    """Schema for EventMapping response"""
    id: int
    name_event: str
    group_event: str
    category_event: str
    description: Optional[str]
    status: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMappingUpdate(BaseModel):
    """Schema for updating an EventMapping (all fields optional for PATCH)"""
    name_event: Optional[str] = None
    group_event: Optional[str] = None
    category_event: Optional[str] = None
    description: Optional[str] = None
    status: Optional[bool] = None
