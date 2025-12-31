"""
DeviceGroup models: DeviceGroup, DeviceGroupMapping (Junction Table)
Based on PRD_Device_Structure_Refactoring.md - Section 3.1
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumDeviceCategory


class DeviceGroup(Base):
    """
    DeviceGroup model for managing device groups with metadata.

    Attributes:
        id: Primary key
        name: Group name (unique)
        description: Group description (optional)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        device_mappings: Relationship to DeviceGroupMapping (N:N via Junction Table)
    """
    __tablename__ = "device_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz), onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Relationship to DeviceGroupMapping (Junction Table)
    device_mappings = relationship(
        "DeviceGroupMapping",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<DeviceGroup(id={self.id}, name='{self.name}')>"

    @property
    def device_count(self):
        """Return the count of devices in this group"""
        return self.device_mappings.count() if self.device_mappings else 0


class DeviceGroupMapping(Base):
    """
    DeviceGroupMapping model - Junction Table for Device-Group N:N relationship.

    Attributes:
        id: Primary key
        device_id: Device's ID (controller_id, sensor_id, or camera_id)
        category_device: Type of device ('controller', 'sensor', 'camera')
        group_id: Foreign key to device_groups.id
        created_at: Mapping creation timestamp

    Constraints:
        - UNIQUE(device_id, category_device, group_id): Prevent duplicate device-group combinations
        - ON DELETE CASCADE: Automatically delete mappings when group is deleted
    """
    __tablename__ = "device_group_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(
        Integer,
        nullable=False,
        index=True
    )
    category_device = Column(
        SQLEnum(EnumDeviceCategory),
        nullable=False,
        index=True,
        comment="Device category: EnumDeviceCategory (CONTROLLER, SENSOR, CAMERA)"
    )
    group_id = Column(
        Integer,
        ForeignKey("device_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)

    # Unique constraint: prevent duplicate device-group combinations (including category_device)
    __table_args__ = (
        UniqueConstraint('device_id', 'category_device', 'group_id', name='uq_device_category_group'),
    )

    # Relationships
    group = relationship("DeviceGroup", back_populates="device_mappings")
    # Note: device relationship will be added when Device Base model is implemented

    def __repr__(self):
        return f"<DeviceGroupMapping(device_id={self.device_id}, category_device='{self.category_device}', group_id={self.group_id})>"
