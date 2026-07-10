"""

Test: EventMappingCamera model

PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 7
PRD: PRD_CategoryEvent_Refactoring.md v1.1 - category_event → category_event_mapping



Phase 1: Model Tests (TDD - Red Phase)

"""

import pytest

from sqlalchemy import inspect

from datetime import datetime

from app.utils.enums import EnumMappingEventCategory





# ============================================================

# Phase 1.1: Model Basic Structure Tests

# ============================================================



class TestEventMappingCameraModelBasicStructure:

    """Basic Structure Tests"""



    def test_event_mapping_camera_model_exists(self, test_db):

        """Test: EventMappingCamera model class exists"""

        from app.models.integration import EventMappingCamera

        assert EventMappingCamera is not None



    def test_event_mapping_camera_table_name(self, test_db):

        """Test: EventMappingCamera has correct table name"""

        from app.models.integration import EventMappingCamera

        assert EventMappingCamera.__tablename__ == "event_mapping_cameras"



    def test_event_mapping_camera_has_id_field(self, test_db):

        """Test: EventMappingCamera has id primary key field"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}



        assert 'id' in columns

        # Check if it's a primary key via table inspection

        pk_constraint = inspector.get_pk_constraint('event_mapping_cameras')

        pk_columns = pk_constraint['constrained_columns']

        assert 'id' in pk_columns



    def test_event_mapping_camera_has_event_mapping_id_fk(self, test_db):

        """Test: EventMappingCamera has event_mapping_id FK"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}

        fks = inspector.get_foreign_keys('event_mapping_cameras')



        assert 'event_mapping_id' in columns

        # Check FK reference

        em_fk = next((fk for fk in fks if 'event_mapping_id' in fk['constrained_columns']), None)

        assert em_fk is not None

        assert em_fk['referred_table'] == 'event_mappings'



    def test_event_mapping_camera_has_camera_id_fk(self, test_db):

        """Test: EventMappingCamera has camera_id FK"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}

        fks = inspector.get_foreign_keys('event_mapping_cameras')



        assert 'camera_id' in columns

        # Check FK reference

        camera_fk = next((fk for fk in fks if 'camera_id' in fk['constrained_columns']), None)

        assert camera_fk is not None

        assert camera_fk['referred_table'] == 'cameras'



    def test_event_mapping_camera_has_target_preset_id_fk(self, test_db):

        """Test: EventMappingCamera has target_preset_id FK"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}

        fks = inspector.get_foreign_keys('event_mapping_cameras')



        assert 'target_preset_id' in columns

        # Check FK reference to camera_presets

        preset_fk = next((fk for fk in fks if 'target_preset_id' in fk['constrained_columns']), None)

        assert preset_fk is not None

        assert preset_fk['referred_table'] == 'camera_presets'



    def test_event_mapping_camera_has_home_preset_id_fk(self, test_db):

        """Test: EventMappingCamera has home_preset_id FK"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}

        fks = inspector.get_foreign_keys('event_mapping_cameras')



        assert 'home_preset_id' in columns

        # Check FK reference to camera_presets

        preset_fk = next((fk for fk in fks if 'home_preset_id' in fk['constrained_columns']), None)

        assert preset_fk is not None

        assert preset_fk['referred_table'] == 'camera_presets'



    def test_event_mapping_camera_has_delay_time_field(self, test_db):

        """Test: EventMappingCamera has delay_time field"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}



        assert 'delay_time' in columns



    def test_event_mapping_camera_has_is_enable_field(self, test_db):

        """Test: EventMappingCamera has is_enable field"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}



        assert 'is_enable' in columns



    def test_event_mapping_camera_has_priority_field(self, test_db):

        """Test: EventMappingCamera has priority field"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}



        assert 'priority' in columns



    def test_event_mapping_camera_has_timestamps(self, test_db):

        """Test: EventMappingCamera has created_at and updated_at fields"""

        inspector = inspect(test_db.bind)

        columns = {col['name']: col for col in inspector.get_columns('event_mapping_cameras')}



        assert 'created_at' in columns

        assert 'updated_at' in columns





# ============================================================

# Phase 1.2: Model FK Behavior Tests

# ============================================================



class TestEventMappingCameraFKBehavior:

    """EventMappingCamera FK Behavior Tests"""



    def test_event_mapping_camera_cascade_delete_on_event_mapping(self, test_db):

        """Test: EventMappingCamera CASCADE delete when EventMapping deleted"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()

        test_db.refresh(event_mapping)



        # Create EventMappingCamera

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id,

            delay_time=10,

            is_enable=True

        )

        test_db.add(emc)

        test_db.commit()

        emc_id = emc.id



        # Delete EventMapping

        test_db.delete(event_mapping)

        test_db.commit()



        # EventMappingCamera should be deleted (CASCADE)

        deleted_emc = test_db.query(EventMappingCamera).filter(

            EventMappingCamera.id == emc_id

        ).first()

        assert deleted_emc is None



    def test_event_mapping_camera_set_null_on_camera_delete(self, test_db, test_camera):

        """Test: EventMappingCamera.camera_id SET NULL when Camera deleted"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping

        from app.models.device import Camera



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()



        # Create EventMappingCamera with camera_id

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id,

            camera_id=test_camera.id,

            delay_time=10,

            is_enable=True

        )

        test_db.add(emc)

        test_db.commit()

        emc_id = emc.id



        # Delete Camera

        test_db.delete(test_camera)

        test_db.commit()

        test_db.expire_all()



        # EventMappingCamera should still exist with camera_id=NULL

        updated_emc = test_db.query(EventMappingCamera).filter(

            EventMappingCamera.id == emc_id

        ).first()

        assert updated_emc is not None

        assert updated_emc.camera_id is None



    def test_event_mapping_camera_set_null_on_target_preset_delete(self, test_db, test_preset):

        """Test: EventMappingCamera.target_preset_id SET NULL when CameraPreset deleted"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping

        from app.models.camera_preset import CameraPreset



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()



        # Create EventMappingCamera with target_preset_id

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id,

            target_preset_id=test_preset.id,

            delay_time=10,

            is_enable=True

        )

        test_db.add(emc)

        test_db.commit()

        emc_id = emc.id



        # Delete CameraPreset

        test_db.delete(test_preset)

        test_db.commit()

        test_db.expire_all()



        # EventMappingCamera should still exist with target_preset_id=NULL

        updated_emc = test_db.query(EventMappingCamera).filter(

            EventMappingCamera.id == emc_id

        ).first()

        assert updated_emc is not None

        assert updated_emc.target_preset_id is None



    def test_event_mapping_camera_set_null_on_home_preset_delete(self, test_db, test_camera):

        """Test: EventMappingCamera.home_preset_id SET NULL when CameraPreset deleted"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping

        from app.models.camera_preset import CameraPreset



        # Create a separate preset for home (not using test_preset fixture to avoid cascade issues)

        home_preset = CameraPreset(

            camera_id=test_camera.id,

            camera_name=test_camera.name_device,

            preset_index=0,

            preset_name="Home",

            touring_time=0

        )

        test_db.add(home_preset)

        test_db.commit()

        test_db.refresh(home_preset)



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()



        # Create EventMappingCamera with home_preset_id

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id,

            home_preset_id=home_preset.id,

            delay_time=10,

            is_enable=True

        )

        test_db.add(emc)

        test_db.commit()

        emc_id = emc.id



        # Delete CameraPreset (home)

        test_db.delete(home_preset)

        test_db.commit()

        test_db.expire_all()



        # EventMappingCamera should still exist with home_preset_id=NULL

        updated_emc = test_db.query(EventMappingCamera).filter(

            EventMappingCamera.id == emc_id

        ).first()

        assert updated_emc is not None

        assert updated_emc.home_preset_id is None





# ============================================================

# Phase 1.3: Model Default Values Tests

# ============================================================



class TestEventMappingCameraDefaultValues:

    """Basic Structure Tests"""



    def test_event_mapping_camera_delay_time_default_zero(self, test_db):

        """Test: EventMappingCamera.delay_time defaults to 0"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()



        # Create EventMappingCamera without delay_time

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id

        )

        test_db.add(emc)

        test_db.commit()

        test_db.refresh(emc)



        assert emc.delay_time == 0



    def test_event_mapping_camera_is_enable_default_true(self, test_db):

        """Test: EventMappingCamera.is_enable defaults to True"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()



        # Create EventMappingCamera without is_enable

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id

        )

        test_db.add(emc)

        test_db.commit()

        test_db.refresh(emc)



        assert emc.is_enable is True



    def test_event_mapping_camera_priority_default_null(self, test_db):

        """Test: EventMappingCamera.priority defaults to None (NULL)"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()



        # Create EventMappingCamera without priority

        emc = EventMappingCamera(

            event_mapping_id=event_mapping.id

        )

        test_db.add(emc)

        test_db.commit()

        test_db.refresh(emc)



        assert emc.priority is None





# ============================================================

# Phase 1.4: EventMapping Relationship Test

# ============================================================



class TestEventMappingCamerasRelationship:

    """EventMapping.cameras relationship Tests"""



    def test_event_mapping_has_cameras_relationship(self, test_db):

        """Test: EventMapping has 'cameras' relationship"""

        from app.models.integration import EventMappingCamera

        from app.models.integration import EventMapping



        # Create EventMapping

        event_mapping = EventMapping(

            name_event="Test Mapping",

            category_event_mapping=EnumMappingEventCategory.FENCE_SENSOR_ONLY,

            status=True

        )

        test_db.add(event_mapping)

        test_db.commit()

        test_db.refresh(event_mapping)



        # Create multiple EventMappingCameras

        emc1 = EventMappingCamera(

            event_mapping_id=event_mapping.id,

            delay_time=10,

            is_enable=True

        )

        emc2 = EventMappingCamera(

            event_mapping_id=event_mapping.id,

            delay_time=20,

            is_enable=True

        )

        test_db.add_all([emc1, emc2])

        test_db.commit()



        # Check relationship

        test_db.refresh(event_mapping)

        assert hasattr(event_mapping, 'cameras')

        cameras_list = list(event_mapping.cameras)

        assert len(cameras_list) == 2

