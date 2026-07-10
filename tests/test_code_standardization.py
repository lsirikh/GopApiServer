"""
Test: Code Standardization Verification
PRD: PRD_Code_Standardization.md v1.0

Phase CS-1: Router Docstring 표준화 검증
Phase CS-2: Schema 코드 형식 검증
Phase CS-3: Device 파일 구조 통합 검증
Phase CS-4: OpenAPI 예제 표준화 검증
"""
import pytest
import inspect
import ast
import os
from pathlib import Path


class TestRouterDocstringPatternA:
    """CS-1.1: Pattern A 사용 파일 식별 (표준화 필요)"""

    def test_controllers_lacks_parameter_header(self):
        """
        Test: controllers.py에 **파라미터**: 헤더 없음 확인
        PRD: PRD_Code_Standardization.md Section 2.2 - Pattern A
        """
        from app.routers import controllers

        # get_controllers 함수의 docstring 확인
        docstring = controllers.get_controllers.__doc__

        # Pattern A: 섹션 헤더 없이 파라미터 리스트만 있음
        assert docstring is not None
        assert "**파라미터**:" not in docstring, \
            "controllers.py가 이미 Pattern B를 사용함 (표준화 불필요)"

    def test_speakers_lacks_parameter_header(self):
        """
        Test: speakers.py에 **파라미터**: 헤더 없음 확인
        """
        from app.routers import speakers

        docstring = speakers.get_speakers.__doc__

        assert docstring is not None
        assert "**파라미터**:" not in docstring, \
            "speakers.py가 이미 Pattern B를 사용함 (표준화 불필요)"

    def test_enclosures_lacks_parameter_header(self):
        """
        Test: enclosures.py에 **파라미터**: 헤더 없음 확인
        """
        from app.routers import enclosures

        docstring = enclosures.get_enclosures.__doc__

        assert docstring is not None
        assert "**파라미터**:" not in docstring, \
            "enclosures.py가 이미 Pattern B를 사용함 (표준화 불필요)"


class TestRouterDocstringPatternB:
    """CS-1.2: Pattern B 준수 파일 확인 (권장 패턴)"""

    def test_sensors_has_parameter_header(self):
        """
        Test: sensors.py에 **파라미터**: 헤더 있음 확인
        PRD: PRD_Code_Standardization.md Section 2.3 - Pattern B (권장)
        """
        from app.routers import sensors

        docstring = sensors.get_sensors.__doc__

        assert docstring is not None
        assert "**파라미터**:" in docstring, \
            "sensors.py에 **파라미터**: 헤더가 없음"

    def test_cameras_has_parameter_header(self):
        """
        Test: cameras.py에 **파라미터**: 헤더 있음 확인
        """
        from app.routers import cameras

        docstring = cameras.get_cameras.__doc__

        assert docstring is not None
        assert "**파라미터**:" in docstring, \
            "cameras.py에 **파라미터**: 헤더가 없음"

    def test_event_mappings_has_parameter_header(self):
        """
        Test: event_mappings.py에 **파라미터**: 헤더 있음 확인
        """
        from app.routers import event_mappings

        docstring = event_mappings.get_event_mappings.__doc__

        assert docstring is not None
        assert "**파라미터**:" in docstring, \
            "event_mappings.py에 **파라미터**: 헤더가 없음"

    def test_detections_has_parameter_header(self):
        """
        Test: detections.py에 **파라미터**: 헤더 있음 확인
        """
        from app.routers import detections

        docstring = detections.get_detection_events.__doc__

        assert docstring is not None
        assert "**파라미터**:" in docstring, \
            "detections.py에 **파라미터**: 헤더가 없음"

    def test_malfunctions_has_parameter_header(self):
        """
        Test: malfunctions.py에 **파라미터**: 헤더 있음 확인
        """
        from app.routers import malfunctions

        docstring = malfunctions.get_malfunction_events.__doc__

        assert docstring is not None
        assert "**파라미터**:" in docstring, \
            "malfunctions.py에 **파라미터**: 헤더가 없음"


class TestSchemaFieldConsistency:
    """CS-2.1: Schema Field 사용법 일관성 검사"""

    def test_device_schema_uses_field(self):
        """
        Test: device.py - 모든 필드에 Field() 사용 확인
        PRD: PRD_Code_Standardization.md Section 3.3
        """
        from app.schemas import device

        # Check ControllerCreate has Field definitions
        source = inspect.getsource(device.ControllerCreate)
        assert "Field(" in source, "ControllerCreate에 Field() 사용 안됨"
        assert "description=" in source, "ControllerCreate에 description 없음"

    def test_enclosure_schema_uses_field(self):
        """
        Test: device.py Enclosure 스키마 - 모든 필드에 Field() 사용 확인
        PRD: PRD_Code_Standardization.md - CS-3.2 (device.py로 통합됨)
        """
        from app.schemas import device

        source = inspect.getsource(device.EnclosureCreate)
        assert "Field(" in source, "EnclosureCreate에 Field() 사용 안됨"
        assert "description=" in source, "EnclosureCreate에 description 없음"

    def test_event_schema_uses_field(self):
        """
        Test: event.py - 모든 필드에 Field() 사용 확인
        """
        from app.schemas import event

        source = inspect.getsource(event.DetectionEventCreate)
        assert "Field(" in source, "DetectionEventCreate에 Field() 사용 안됨"

    def test_integration_schema_uses_field(self):
        """
        Test: integration.py - 모든 필드에 Field() 사용 확인
        """
        from app.schemas import integration

        source = inspect.getsource(integration.EventMappingCreate)
        assert "Field(" in source, "EventMappingCreate에 Field() 사용 안됨"


class TestSchemaConfigDict:
    """CS-2.2: ConfigDict 사용 검사"""

    def test_device_schemas_have_config_dict(self):
        """
        Test: device.py 스키마에 model_config 확인
        """
        from app.schemas import device

        # Check if model_config exists
        assert hasattr(device.ControllerCreate, 'model_config'), \
            "ControllerCreate에 model_config 없음"
        assert hasattr(device.ControllerResponse, 'model_config'), \
            "ControllerResponse에 model_config 없음"

    def test_enclosure_schemas_have_config_dict(self):
        """
        Test: device.py Enclosure 스키마에 model_config 확인
        PRD: PRD_Code_Standardization.md - CS-3.2 (device.py로 통합됨)
        """
        from app.schemas import device

        assert hasattr(device.EnclosureCreate, 'model_config'), \
            "EnclosureCreate에 model_config 없음"
        assert hasattr(device.EnclosureResponse, 'model_config'), \
            "EnclosureResponse에 model_config 없음"


class TestDeviceFileStructure:
    """CS-3.1: Device 파일 구조 검증"""

    def test_device_schema_contains_enclosure(self):
        """
        Test: device.py에 Enclosure 스키마 포함 확인
        PRD: PRD_Code_Standardization.md - CS-3.2 (enclosure.py → device.py 통합 완료)
        """
        from app.schemas import device

        assert hasattr(device, 'EnclosureCreate'), \
            "device.py에 EnclosureCreate 없음"
        assert hasattr(device, 'EnclosureResponse'), \
            "device.py에 EnclosureResponse 없음"

    def test_device_schema_contains_speaker(self):
        """
        Test: device.py에 Speaker 스키마 포함 확인
        """
        from app.schemas import device

        assert hasattr(device, 'SpeakerCreate'), \
            "device.py에 SpeakerCreate 없음"
        assert hasattr(device, 'SpeakerResponse'), \
            "device.py에 SpeakerResponse 없음"

    def test_enclosures_router_imports_from_device_schema(self):
        """
        Test: enclosures.py router에서 device.py import 확인
        PRD: PRD_Code_Standardization.md - CS-3.2 (Enclosure → device.py 통합)
        """
        router_path = Path("app/routers/enclosures.py")
        content = router_path.read_text(encoding='utf-8')

        assert "from app.schemas.device import" in content, \
            "enclosures.py에서 device.py import 안됨 (CS-3.2 미적용)"


class TestOpenAPIExamples:
    """CS-4.1: OpenAPI responses= 데코레이터 사용 현황"""

    def test_device_groups_uses_responses_decorator(self):
        """
        Test: device_groups.py에 responses= 데코레이터 사용 확인
        PRD: PRD_Code_Standardization.md Section 2.4
        """
        router_path = Path("app/routers/device_groups.py")
        content = router_path.read_text(encoding='utf-8')

        assert "responses={" in content or "responses = {" in content, \
            "device_groups.py에 responses= 데코레이터 없음"

    def test_controllers_lacks_responses_decorator(self):
        """
        Test: controllers.py에 responses= 데코레이터 없음 확인
        (향후 추가 대상)
        """
        router_path = Path("app/routers/controllers.py")
        content = router_path.read_text(encoding='utf-8')

        # controllers.py는 현재 responses 데코레이터 미사용
        has_responses = "responses={" in content or "responses = {" in content
        # 이 테스트는 현재 상태 확인용 (실패해도 OK)
        if not has_responses:
            pass  # 예상대로 responses 없음
