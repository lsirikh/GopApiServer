"""
Test: Router ENUM usage verification
PRD: PRD_Device_Inheritance_Structure_Refactoring.md Section 8.1

TDD Phase 6: Verify routers use EnumDeviceCategory instead of hardcoded strings
"""
import pytest
import ast
import os


class TestRouterEnumUsage:
    """Router에서 EnumDeviceCategory 사용 여부 테스트"""

    def _check_file_for_hardcoded_strings(self, filepath: str) -> list:
        """파일에서 하드코딩된 category_device 문자열 찾기"""
        hardcoded_patterns = []

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 하드코딩된 문자열 패턴 검사
            if 'category_device' in line:
                # "controller", "sensor", "camera" 문자열이 직접 사용되는지 확인
                if '"controller"' in line or "'controller'" in line:
                    if 'EnumDeviceCategory' not in line:
                        hardcoded_patterns.append((i, line.strip()))
                if '"sensor"' in line or "'sensor'" in line:
                    if 'EnumDeviceCategory' not in line:
                        hardcoded_patterns.append((i, line.strip()))
                if '"camera"' in line or "'camera'" in line:
                    if 'EnumDeviceCategory' not in line:
                        hardcoded_patterns.append((i, line.strip()))

        return hardcoded_patterns

    def test_controllers_router_uses_enum(self):
        """controllers.py 라우터가 EnumDeviceCategory를 사용하는지 확인"""
        filepath = os.path.join('app', 'routers', 'controllers.py')
        hardcoded = self._check_file_for_hardcoded_strings(filepath)

        assert len(hardcoded) == 0, \
            f"controllers.py has hardcoded category_device strings:\n" + \
            "\n".join([f"  Line {ln}: {code}" for ln, code in hardcoded])

    def test_sensors_router_uses_enum(self):
        """sensors.py 라우터가 EnumDeviceCategory를 사용하는지 확인"""
        filepath = os.path.join('app', 'routers', 'sensors.py')
        hardcoded = self._check_file_for_hardcoded_strings(filepath)

        assert len(hardcoded) == 0, \
            f"sensors.py has hardcoded category_device strings:\n" + \
            "\n".join([f"  Line {ln}: {code}" for ln, code in hardcoded])

    def test_cameras_router_uses_enum(self):
        """cameras.py 라우터가 EnumDeviceCategory를 사용하는지 확인"""
        filepath = os.path.join('app', 'routers', 'cameras.py')
        hardcoded = self._check_file_for_hardcoded_strings(filepath)

        assert len(hardcoded) == 0, \
            f"cameras.py has hardcoded category_device strings:\n" + \
            "\n".join([f"  Line {ln}: {code}" for ln, code in hardcoded])

    def test_device_groups_router_uses_enum(self):
        """device_groups.py 라우터가 EnumDeviceCategory를 사용하는지 확인"""
        filepath = os.path.join('app', 'routers', 'device_groups.py')
        hardcoded = self._check_file_for_hardcoded_strings(filepath)

        assert len(hardcoded) == 0, \
            f"device_groups.py has hardcoded category_device strings:\n" + \
            "\n".join([f"  Line {ln}: {code}" for ln, code in hardcoded])
