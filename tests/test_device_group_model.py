"""
DeviceGroup Model Tests (TDD - Red Phase)
PRD: PRD_Device_Structure_Refactoring.md - Section 3.1
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.database import Base, engine, SessionLocal


class TestDeviceGroupModel:
    """DeviceGroup 모델 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """테스트 설정"""
        self.db = db_session

    def test_device_group_create(self, db_session):
        """DeviceGroup 생성 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(
            name="GOP 1구역",
            description="1구역 전방 감시 장비 그룹"
        )
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)

        assert group.id is not None
        assert group.name == "GOP 1구역"
        assert group.description == "1구역 전방 감시 장비 그룹"

    def test_device_group_name_unique(self, db_session):
        """DeviceGroup name UNIQUE 제약조건 테스트"""
        from app.models.device_group import DeviceGroup

        group1 = DeviceGroup(name="GOP 1구역")
        db_session.add(group1)
        db_session.commit()

        group2 = DeviceGroup(name="GOP 1구역")  # 동일한 이름
        db_session.add(group2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_device_group_description_nullable(self, db_session):
        """DeviceGroup description NULL 허용 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="GOP 2구역")  # description 없음
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)

        assert group.description is None

    def test_device_group_timestamps_auto_created(self, db_session):
        """DeviceGroup created_at/updated_at 자동 생성 테스트"""
        from app.models.device_group import DeviceGroup

        before_create = datetime.now()

        group = DeviceGroup(name="GOP 3구역")
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)

        after_create = datetime.now()

        assert group.created_at is not None
        assert group.updated_at is not None
        # 타임스탬프가 적절한 범위 내에 있는지 확인
        assert group.created_at >= before_create.replace(microsecond=0)

    def test_device_group_device_count(self, db_session):
        """DeviceGroup device_count 속성 테스트"""
        from app.models.device_group import DeviceGroup

        group = DeviceGroup(name="GOP 4구역")
        db_session.add(group)
        db_session.commit()
        db_session.refresh(group)

        # 디바이스가 없을 때 카운트는 0
        # lazy="dynamic" 사용 시 .count() 또는 .all() 사용
        assert group.device_mappings.count() == 0


class TestDeviceGroupMappingModel:
    """DeviceGroupMapping (Junction Table) 모델 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """테스트 설정"""
        self.db = db_session

    def test_device_group_mapping_create(self, db_session):
        """DeviceGroupMapping 생성 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # 그룹 생성
        group = DeviceGroup(name="테스트 그룹")
        db_session.add(group)
        db_session.commit()

        # 컨트롤러 생성 (Device Base)
        controller = Controller(
            number_device=1001,
            group_device=1,  # 레거시 필드
            name_device="CTL-001",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.10",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        # 매핑 생성
        mapping = DeviceGroupMapping(
            device_id=controller.id,
            category_device="controller",
            group_id=group.id
        )
        db_session.add(mapping)
        db_session.commit()
        db_session.refresh(mapping)

        assert mapping.id is not None
        assert mapping.device_id == controller.id
        assert mapping.category_device == "controller"
        assert mapping.group_id == group.id

    def test_device_group_mapping_unique_constraint(self, db_session):
        """device_id + group_id UNIQUE 제약조건 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        group = DeviceGroup(name="유니크 테스트 그룹")
        db_session.add(group)

        controller = Controller(
            number_device=1002,
            group_device=1,
            name_device="CTL-002",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.11",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        # 첫 번째 매핑
        mapping1 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group.id)
        db_session.add(mapping1)
        db_session.commit()

        # 동일한 조합으로 두 번째 매핑 시도
        mapping2 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group.id)
        db_session.add(mapping2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_device_group_mapping_cascade_delete_group(self, db_session):
        """CASCADE 삭제 테스트 (그룹 삭제 시 매핑 삭제)"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        group = DeviceGroup(name="삭제 테스트 그룹")
        db_session.add(group)

        controller = Controller(
            number_device=1003,
            group_device=1,
            name_device="CTL-003",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.12",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        mapping = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group.id)
        db_session.add(mapping)
        db_session.commit()

        mapping_id = mapping.id
        group_id = group.id

        # 그룹 삭제
        db_session.delete(group)
        db_session.commit()

        # 매핑도 삭제되었는지 확인
        deleted_mapping = db_session.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.id == mapping_id
        ).first()
        assert deleted_mapping is None

    def test_device_group_mapping_orphan_on_device_delete(self, db_session):
        """디바이스 삭제 시 매핑 동작 테스트

        Note: DeviceGroupMapping.device_id는 ForeignKey가 아니라 Integer이므로
        (Controller, Sensor, Camera 등 여러 테이블을 참조할 수 있음)
        CASCADE 삭제가 자동으로 일어나지 않음.
        라우터에서 디바이스 삭제 시 명시적으로 매핑도 삭제해야 함.
        """
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        group = DeviceGroup(name="디바이스 삭제 테스트 그룹")
        db_session.add(group)

        controller = Controller(
            number_device=1004,
            group_device=1,
            name_device="CTL-004",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.13",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        mapping = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group.id)
        db_session.add(mapping)
        db_session.commit()

        mapping_id = mapping.id
        device_id = controller.id

        # 컨트롤러 삭제 (라우터에서 명시적으로 매핑도 삭제해야 함)
        # 먼저 매핑 삭제
        db_session.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == "controller"
        ).delete()

        # 그 다음 컨트롤러 삭제
        db_session.delete(controller)
        db_session.commit()

        # 매핑도 삭제되었는지 확인
        deleted_mapping = db_session.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.id == mapping_id
        ).first()
        assert deleted_mapping is None

    def test_device_multiple_groups(self, db_session):
        """하나의 디바이스가 여러 그룹에 소속 (N:N) 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        # 여러 그룹 생성
        group1 = DeviceGroup(name="GOP 1구역")
        group2 = DeviceGroup(name="야간 감시")
        group3 = DeviceGroup(name="VIP 구역")
        db_session.add_all([group1, group2, group3])

        controller = Controller(
            number_device=1005,
            group_device=1,
            name_device="CTL-005",
            type_device=EnumDeviceType.Controller,
            version="1.0.0",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.14",
            ip_port=8080
        )
        db_session.add(controller)
        db_session.commit()

        # 하나의 컨트롤러를 여러 그룹에 할당
        mapping1 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group1.id)
        mapping2 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group2.id)
        mapping3 = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group3.id)
        db_session.add_all([mapping1, mapping2, mapping3])
        db_session.commit()

        # 컨트롤러의 그룹 수 확인
        db_session.refresh(controller)
        # device_groups relationship을 통해 확인
        # lazy="dynamic" 사용 시 .count() 사용
        assert controller.group_mappings.count() == 3

    def test_group_multiple_devices(self, db_session):
        """하나의 그룹에 여러 디바이스 소속 테스트"""
        from app.models.device_group import DeviceGroup, DeviceGroupMapping
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus

        group = DeviceGroup(name="다중 디바이스 그룹")
        db_session.add(group)

        # 여러 컨트롤러 생성
        controllers = []
        for i in range(5):
            controller = Controller(
                number_device=2000 + i,
                group_device=1,
                name_device=f"CTL-2{i:03d}",
                type_device=EnumDeviceType.Controller,
                version="1.0.0",
                status=EnumDeviceStatus.ACTIVATED,
                ip_address=f"192.168.2.{10+i}",
                ip_port=8080
            )
            controllers.append(controller)

        db_session.add_all(controllers)
        db_session.commit()

        # 모든 컨트롤러를 하나의 그룹에 할당
        for controller in controllers:
            mapping = DeviceGroupMapping(device_id=controller.id, category_device="controller", group_id=group.id)
            db_session.add(mapping)
        db_session.commit()

        # 그룹의 디바이스 수 확인
        db_session.refresh(group)
        # lazy="dynamic" 사용 시 .count() 사용
        assert group.device_mappings.count() == 5
