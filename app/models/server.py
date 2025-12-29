"""
Server models: ServerCategory, Server
Based on GOP_서버모니터링_스키마.md
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumServerType, EnumServerStatus


class ServerCategory(Base):
    """
    Server Category model (서버 카테고리 - 상위 그룹)

    Attributes:
        id: Primary key
        name: 카테고리 표시명 (예: "VMS 서버")
        type_server: 서버 유형 (EnumServerType), UNIQUE
        description: 설명 (옵션)
        sort_order: 정렬 순서
        created_at: 생성 시간
        updated_at: 수정 시간
        servers: Relationship to Server models (1:N)
    """
    __tablename__ = "server_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type_server = Column(SQLEnum(EnumServerType), nullable=False, unique=True)
    description = Column(String(200), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Relationship to servers (1:N)
    servers = relationship("Server", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<ServerCategory(id={self.id}, name='{self.name}', "
            f"type_server='{self.type_server.value}', sort_order={self.sort_order})>"
        )


class Server(Base):
    """
    Server model (서버 인스턴스 - 하위 개별 서버)

    Attributes:
        id: Primary key
        category_id: Foreign key to ServerCategory
        name: 서버 인스턴스명 (예: "VMS-ab1120")
        status: 서버 상태 (EnumServerStatus)
        ip_address: IP 주소 (IPv4/IPv6)
        port: 포트 번호
        hostname: 호스트명 (옵션)
        cpu_usage: CPU 사용률 (%)
        ram_usage: RAM 사용률 (%)
        disk_usage: DISK 사용률 (%)
        network_throughput: 네트워크 처리량 (예: "125MB/s")
        created_at: 생성 시간
        updated_at: 수정 시간
        category: Relationship to ServerCategory
    """
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("server_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status = Column(SQLEnum(EnumServerStatus), nullable=False, default=EnumServerStatus.NORMAL)
    ip_address = Column(String(45), nullable=False)  # IPv4/IPv6 지원
    port = Column(Integer, nullable=False)
    hostname = Column(String(100), nullable=True)

    # 메트릭
    cpu_usage = Column(Float, nullable=True)
    ram_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    network_throughput = Column(String(20), nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Relationship to category
    category = relationship("ServerCategory", back_populates="servers")

    def __repr__(self):
        return (
            f"<Server(id={self.id}, name='{self.name}', "
            f"status='{self.status.value}', ip_address='{self.ip_address}', "
            f"port={self.port}, category_id={self.category_id})>"
        )
