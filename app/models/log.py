"""
API Log Model for tracking all API requests
"""
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime


class ApiLog(Base):
    """
    API Log model for storing request logs
    Format: yyyy-MM-ddTHH:mm:ss.fff, Resource, Method, Client UUID, Request ID, Description
    """
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)  # e.g., "devices/controllers"
    method = Column(String(10), nullable=False, index=True)  # GET, POST, PATCH, DELETE, etc.
    client_uuid = Column(String(100), nullable=True, index=True)  # X-Client-UUID header
    request_id = Column(String(100), nullable=True, index=True)  # X-Request-ID
    description = Column(String(500), nullable=False)  # e.g., "Create new controller"
    status_code = Column(Integer, nullable=True)  # HTTP status code
    user_id = Column(Integer, nullable=True)  # User ID if authenticated

    def __repr__(self):
        return (
            f"<ApiLog(timestamp='{self.timestamp.isoformat()}', "
            f"resource='{self.resource}', method='{self.method}', "
            f"description='{self.description}')>"
        )

    def to_csv_format(self) -> str:
        """
        Return log in CSV format:
        yyyy-MM-ddTHH:mm:ss.fff,Resource,Method,ClientUUID,RequestID,Description
        """
        client_uuid_str = self.client_uuid if self.client_uuid else ""
        request_id_str = self.request_id if self.request_id else ""

        return (
            f"{self.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]},"
            f"{self.resource},"
            f"{self.method},"
            f"{client_uuid_str},"
            f"{request_id_str},"
            f"{self.description}"
        )
