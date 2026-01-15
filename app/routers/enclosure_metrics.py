"""
EnclosureMetric Router

PRD: PRD_Enclosure_Metrics_Separation.md v1.0

Endpoints: /api/devices/enclosures/{enclosure_id}/metrics
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Enclosure, EnclosureMetric
from app.schemas.device import EnclosureMetricCreate, EnclosureMetricResponse

router = APIRouter(tags=["Enclosure Metrics"])


def _metric_to_response(metric: EnclosureMetric) -> dict:
    """Convert EnclosureMetric model to response dict"""
    return {
        "id": metric.id,
        "enclosure_id": metric.enclosure_id,
        "collected_at": metric.collected_at.isoformat() if metric.collected_at else None,
        "temperature": metric.temperature,
        "humidity": metric.humidity,
        "current": metric.current,
        "voltage": metric.voltage,
        "vibration": metric.vibration,
        "ups_battery_level": metric.ups_battery_level,
        "ups_charging": metric.ups_charging,
        "detail": metric.detail,
        "created_at": metric.created_at.isoformat() if metric.created_at else None,
    }


@router.post(
    "/{enclosure_id}/metrics",
    status_code=status.HTTP_201_CREATED,
    summary="Enclosure 메트릭 저장",
    description="함체의 환경 모니터링 메트릭 데이터를 저장합니다."
)
def create_enclosure_metric(
    enclosure_id: int,
    metric_data: EnclosureMetricCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    POST /api/devices/enclosures/{enclosure_id}/metrics

    함체의 환경 모니터링 메트릭을 저장합니다.

    **파라미터**:
    - **enclosure_id**: Enclosure ID (path parameter)
    - **metric_data**: EnclosureMetricCreate 스키마

    **반환**:
    - 저장된 메트릭 데이터 및 임계치 초과 정보
    """
    # Enclosure 존재 확인
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # Create metric
    metric = EnclosureMetric(
        enclosure_id=enclosure_id,
        collected_at=metric_data.collected_at,
        temperature=str(metric_data.temperature) if metric_data.temperature is not None else None,
        humidity=str(metric_data.humidity) if metric_data.humidity is not None else None,
        current=str(metric_data.current) if metric_data.current is not None else None,
        voltage=str(metric_data.voltage) if metric_data.voltage is not None else None,
        vibration=metric_data.vibration,
        ups_battery_level=metric_data.ups_battery_level,
        ups_charging=metric_data.ups_charging,
        detail=metric_data.detail,
    )

    db.add(metric)
    db.commit()
    db.refresh(metric)

    # Check thresholds
    threshold_exceeded = _check_thresholds(enclosure, metric_data)

    return {
        "success": True,
        "message": "Enclosure metric saved successfully",
        "data": _metric_to_response(metric),
        "threshold_exceeded": threshold_exceeded
    }


def _check_thresholds(enclosure: Enclosure, metric_data: EnclosureMetricCreate) -> List[dict]:
    """
    임계치 초과 여부 확인

    Returns:
        List of exceeded thresholds with field name and values
    """
    exceeded = []

    if not enclosure.threshold_config:
        return exceeded

    config = enclosure.threshold_config

    # Temperature check
    if metric_data.temperature is not None:
        if config.get("temp_high") and metric_data.temperature > config["temp_high"]:
            exceeded.append({
                "field": "temperature",
                "value": metric_data.temperature,
                "threshold": config["temp_high"],
                "type": "HIGH"
            })
        if config.get("temp_low") and metric_data.temperature < config["temp_low"]:
            exceeded.append({
                "field": "temperature",
                "value": metric_data.temperature,
                "threshold": config["temp_low"],
                "type": "LOW"
            })

    # Humidity check
    if metric_data.humidity is not None:
        if config.get("humidity_high") and metric_data.humidity > config["humidity_high"]:
            exceeded.append({
                "field": "humidity",
                "value": metric_data.humidity,
                "threshold": config["humidity_high"],
                "type": "HIGH"
            })

    # Current check
    if metric_data.current is not None:
        if config.get("current_high") and metric_data.current > config["current_high"]:
            exceeded.append({
                "field": "current",
                "value": metric_data.current,
                "threshold": config["current_high"],
                "type": "HIGH"
            })

    # Voltage check
    if metric_data.voltage is not None:
        if config.get("voltage_low") and metric_data.voltage < config["voltage_low"]:
            exceeded.append({
                "field": "voltage",
                "value": metric_data.voltage,
                "threshold": config["voltage_low"],
                "type": "LOW"
            })

    # Vibration check
    if metric_data.vibration is not None:
        if config.get("vibration_high") and metric_data.vibration > config["vibration_high"]:
            exceeded.append({
                "field": "vibration",
                "value": metric_data.vibration,
                "threshold": config["vibration_high"],
                "type": "HIGH"
            })

    return exceeded


@router.get(
    "/{enclosure_id}/metrics",
    summary="Enclosure 메트릭 목록 조회",
    description="함체의 환경 모니터링 메트릭 이력을 조회합니다."
)
def get_enclosure_metrics(
    enclosure_id: int,
    limit: int = Query(100, ge=1, le=1000, description="조회할 최대 개수"),
    start_time: Optional[datetime] = Query(None, description="시작 시간 필터"),
    end_time: Optional[datetime] = Query(None, description="종료 시간 필터"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    GET /api/devices/enclosures/{enclosure_id}/metrics

    함체의 환경 모니터링 메트릭 이력을 조회합니다.

    **파라미터**:
    - **enclosure_id**: Enclosure ID (path parameter)
    - **limit**: 조회할 최대 개수 (기본: 100)
    - **start_time**: 시작 시간 필터 (선택)
    - **end_time**: 종료 시간 필터 (선택)

    **반환**:
    - 메트릭 목록
    """
    # Enclosure 존재 확인
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # Query metrics
    query = db.query(EnclosureMetric).filter(EnclosureMetric.enclosure_id == enclosure_id)

    if start_time:
        query = query.filter(EnclosureMetric.collected_at >= start_time)
    if end_time:
        query = query.filter(EnclosureMetric.collected_at <= end_time)

    query = query.order_by(EnclosureMetric.collected_at.desc())
    metrics = query.limit(limit).all()

    return {
        "success": True,
        "message": "Enclosure metrics retrieved successfully",
        "data": [_metric_to_response(m) for m in metrics]
    }


@router.get(
    "/{enclosure_id}/metrics/latest",
    summary="Enclosure 최신 메트릭 조회",
    description="함체의 가장 최근 환경 모니터링 메트릭을 조회합니다."
)
def get_enclosure_metrics_latest(
    enclosure_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    GET /api/devices/enclosures/{enclosure_id}/metrics/latest

    함체의 가장 최근 환경 모니터링 메트릭을 조회합니다.

    **파라미터**:
    - **enclosure_id**: Enclosure ID (path parameter)

    **반환**:
    - 가장 최근 메트릭 데이터
    """
    # Enclosure 존재 확인
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # Get latest metric
    metric = db.query(EnclosureMetric).filter(
        EnclosureMetric.enclosure_id == enclosure_id
    ).order_by(EnclosureMetric.collected_at.desc()).first()

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for enclosure {enclosure_id}"
        )

    return {
        "success": True,
        "message": "Latest enclosure metric retrieved successfully",
        "data": _metric_to_response(metric)
    }


@router.delete(
    "/{enclosure_id}/metrics",
    summary="Enclosure 메트릭 삭제",
    description="함체의 환경 모니터링 메트릭을 삭제합니다."
)
def delete_enclosure_metrics(
    enclosure_id: int,
    before_date: Optional[datetime] = Query(None, description="이 날짜 이전 메트릭만 삭제"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    DELETE /api/devices/enclosures/{enclosure_id}/metrics

    함체의 환경 모니터링 메트릭을 삭제합니다.

    **파라미터**:
    - **enclosure_id**: Enclosure ID (path parameter)
    - **before_date**: 이 날짜 이전 메트릭만 삭제 (선택)

    **반환**:
    - 삭제된 메트릭 수
    """
    # Enclosure 존재 확인
    enclosure = db.query(Enclosure).filter(Enclosure.id == enclosure_id).first()
    if not enclosure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enclosure with id {enclosure_id} not found"
        )

    # Build delete query
    query = db.query(EnclosureMetric).filter(EnclosureMetric.enclosure_id == enclosure_id)

    if before_date:
        query = query.filter(EnclosureMetric.collected_at < before_date)

    # Count and delete
    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return {
        "success": True,
        "message": f"Deleted {deleted_count} metrics",
        "data": {"deleted_count": deleted_count}
    }
