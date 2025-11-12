"""
Device schemas: Controller, Sensor, Camera
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ControllerCreate(BaseModel):
    """Schema for creating a new Controller"""
    number_device: int
    group_device: int
    name_device: str
    type_device: str  # EnumDeviceType value as string
    version: str
    status: str  # EnumDeviceStatus value as string
    ip_address: str
    ip_port: int


class ControllerResponse(BaseModel):
    """Schema for Controller response (includes all fields)"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str  # EnumDeviceType value as string
    version: str
    status: str  # EnumDeviceStatus value as string
    ip_address: str
    ip_port: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ControllerUpdate(BaseModel):
    """Schema for updating a Controller (all fields optional for PATCH)"""
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    type_device: Optional[str] = None  # EnumDeviceType value as string
    version: Optional[str] = None
    status: Optional[str] = None  # EnumDeviceStatus value as string
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None


class SensorCreate(BaseModel):
    """Schema for creating a new Sensor"""
    number_device: int
    group_device: int
    name_device: str
    type_device: str  # EnumDeviceType value as string
    version: str
    status: str  # EnumDeviceStatus value as string
    controller_id: int


class SensorResponse(BaseModel):
    """Schema for Sensor response (includes all fields)"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str  # EnumDeviceType value as string
    version: str
    status: str  # EnumDeviceStatus value as string
    controller_id: int
    created_at: datetime
    updated_at: datetime
    controller: Optional['ControllerResponse'] = None  # Optional nested controller info

    model_config = ConfigDict(from_attributes=True)


class SensorUpdate(BaseModel):
    """Schema for updating a Sensor (all fields optional for PATCH)"""
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    type_device: Optional[str] = None  # EnumDeviceType value as string
    version: Optional[str] = None
    status: Optional[str] = None  # EnumDeviceStatus value as string
    controller_id: Optional[int] = None


class CameraCreate(BaseModel):
    """Schema for creating a new Camera"""
    number_device: int
    group_device: int
    name_device: str
    type_device: str  # EnumDeviceType value as string
    version: str
    status: str  # EnumDeviceStatus value as string
    ip_address: str
    ip_port: int
    user_name: str
    user_password: str
    rtsp_uri: str
    rtsp_port: int
    mode: str  # EnumCameraMode value as string
    category: str  # EnumCameraType value as string


class CameraResponse(BaseModel):
    """Schema for Camera response (includes all fields)"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str  # EnumDeviceType value as string
    version: str
    status: str  # EnumDeviceStatus value as string
    ip_address: str
    ip_port: int
    user_name: str
    user_password: str
    rtsp_uri: str
    rtsp_port: int
    mode: str  # EnumCameraMode value as string
    category: str  # EnumCameraType value as string
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraUpdate(BaseModel):
    """Schema for updating a Camera (all fields optional for PATCH)"""
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    type_device: Optional[str] = None  # EnumDeviceType value as string
    version: Optional[str] = None
    status: Optional[str] = None  # EnumDeviceStatus value as string
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    rtsp_uri: Optional[str] = None
    rtsp_port: Optional[int] = None
    mode: Optional[str] = None  # EnumCameraMode value as string
    category: Optional[str] = None  # EnumCameraType value as string
