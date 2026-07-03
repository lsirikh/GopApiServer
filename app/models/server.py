"""
Server models: ServerCategory, Server
Based on GOP_서버모니터링_스키마.md
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
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
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

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
        threshold_config: 임계치 설정 (JSONB)
        created_at: 생성 시간
        updated_at: 수정 시간
        category: Relationship to ServerCategory
        metrics: Relationship to ServerMetrics (1:N)
    """
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("server_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status = Column(SQLEnum(EnumServerStatus), nullable=False, default=EnumServerStatus.NORMAL)
    ip_address = Column(String(45), nullable=False)  # IPv4/IPv6 지원
    port = Column(Integer, nullable=False)
    hostname = Column(String(100), nullable=True)

    # ===== 인증 정보 =====
    user_name = Column(String(100), nullable=True)
    user_password = Column(String(200), nullable=True)

    # 임계치 설정 (JSONB)
    threshold_config = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationship to category
    category = relationship("ServerCategory", back_populates="servers")

    # Relationship to metrics (1:N)
    # v6.0 hotfix: passive_deletes=True → DB CASCADE 위임 (ORM이 UPDATE server_id=NULL 시도 방지)
    metrics = relationship("ServerMetrics", back_populates="server", cascade="all, delete-orphan", passive_deletes=True)

    # Relationship to system_events (1:N, SET NULL on delete)
    # v6.0 hotfix: passive_deletes=True → DB ondelete=SET NULL 위임
    system_events = relationship("SystemEvent", back_populates="server", passive_deletes=True)

    def __repr__(self):
        return (
            f"<Server(id={self.id}, name='{self.name}', "
            f"status='{self.status.value}', ip_address='{self.ip_address}', "
            f"port={self.port}, category_id={self.category_id})>"
        )


class ServerMetrics(Base):
    """
    Server Metrics model (서버 리소스 모니터링 이력)

    Attributes:
        id: Primary key
        server_id: Foreign key to Server (CASCADE)
        cpu_usage: CPU 사용률 (%)
        ram_usage: RAM 사용률 (%)
        ram_total_gb: RAM 전체 크기 (GB)
        ram_used_gb: RAM 사용 크기 (GB)
        disk_usage: Disk 사용률 (%)
        disk_total_gb: Disk 전체 크기 (GB)
        disk_used_gb: Disk 사용 크기 (GB)
        network_in_mbps: 네트워크 수신 속도 (Mbps)
        network_out_mbps: 네트워크 송신 속도 (Mbps)
        process_count: 프로세스 수
        detail: 추가 상세 정보 (JSONB)
        collected_at: 수집 시간
        created_at: 생성 시간

    PRD Reference: PRD_System_Event.md Section 2.4
    """
    __tablename__ = "server_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)

    # 리소스 메트릭
    cpu_usage = Column(Float, nullable=True)  # CPU 사용률 (%)
    ram_usage = Column(Float, nullable=True)  # RAM 사용률 (%)
    ram_total_gb = Column(Float, nullable=True)  # RAM 전체 크기 (GB)
    ram_used_gb = Column(Float, nullable=True)  # RAM 사용 크기 (GB)
    disk_usage = Column(Float, nullable=True)  # Disk 사용률 (%)
    disk_total_gb = Column(Float, nullable=True)  # Disk 전체 크기 (GB)
    disk_used_gb = Column(Float, nullable=True)  # Disk 사용 크기 (GB)
    network_in_mbps = Column(Float, nullable=True)  # 네트워크 수신 속도 (Mbps)
    network_out_mbps = Column(Float, nullable=True)  # 네트워크 송신 속도 (Mbps)
    process_count = Column(Integer, nullable=True)  # 프로세스 수

    # 추가 상세 정보 (JSONB)
    detail = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    # 타임스탬프
    collected_at = Column(DateTime, nullable=True)  # 수집 시간
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationship to server
    server = relationship("Server", back_populates="metrics")

    def __repr__(self):
        return (
            f"<ServerMetrics(id={self.id}, server_id={self.server_id}, "
            f"cpu_usage={self.cpu_usage}, ram_usage={self.ram_usage})>"
        )
