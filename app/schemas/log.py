"""
API Log Schemas
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ApiLogResponse(BaseModel):
    """
    API Log response schema
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    resource: str
    method: str
    client_uuid: Optional[str] = None
    request_id: Optional[str] = None
    description: str
    status_code: Optional[int] = None
    user_id: Optional[int] = None
