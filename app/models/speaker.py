"""
Speaker model: Device Polymorphic child for IP Speaker devices
PRD: PRD_Speaker_Device.md - Section 4.1, 4.2

Speaker inherits from Device using Joined Table Inheritance.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.device import Device
from app.utils.enums import EnumDeviceCategory, EnumSpeakerType


class Speaker(Device):
    """
    Speaker model for managing IP Speaker devices.
    Inherits from Device using Joined Table Inheritance.

    Additional Attributes:
        speaker_type: Speaker type (EnumSpeakerType: NORMAL, ADMIN, MONITOR, DEV)
        server_id: FK to Server (SPEAKER_API type), SET NULL on delete
        description: Description text
    """
    __tablename__ = "speakers"

    # Foreign key to devices table (Joined Table Inheritance)
    id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)

    # Speaker-specific fields
    speaker_type = Column(
        SQLEnum(EnumSpeakerType),
        nullable=False,
        default=EnumSpeakerType.NORMAL
    )
    server_id = Column(
        Integer,
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    description = Column(String(500), nullable=True)

    # Polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": EnumDeviceCategory.SPEAKER
    }

    # Relationship to Server
    server = relationship("Server", foreign_keys=[server_id])

    def __repr__(self):
        return (
            f"<Speaker(id={self.id}, number_device={self.number_device}, "
            f"name_device='{self.name_device}', status='{self.status.value}', "
            f"speaker_type='{self.speaker_type.value}', server_id={self.server_id})>"
        )
