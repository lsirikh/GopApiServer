"""
DetectionDetail frame_width/frame_height 필드 테스트 (detection-sync-message FR-04).

브로커 v1.5 계약: 탐지 detail 에 frame_width/frame_height(AI 추론 프레임 해상도, px)가
objects[].bbox 좌표 해석 기준으로 규정돼 있으나 API DetectionDetail 스키마·Swagger 예시에
누락됐던 GAP(broker-v15 교차검증) 해소.
"""
from app.schemas.event import DetectionDetail


def test_should_include_frame_width_height_when_provided():
    d = DetectionDetail(thumbnail="http://x/t.jpg", frame_width=1920, frame_height=1080)
    assert d.frame_width == 1920
    assert d.frame_height == 1080


def test_should_default_frame_dims_none_when_omitted():
    d = DetectionDetail(thumbnail="http://x/t.jpg")
    assert d.frame_width is None
    assert d.frame_height is None


def test_should_expose_frame_dims_in_model_fields():
    assert "frame_width" in DetectionDetail.model_fields
    assert "frame_height" in DetectionDetail.model_fields
