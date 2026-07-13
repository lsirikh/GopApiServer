"""
Tests for Speaker Geolocation feature
PRD: PRD_Speaker_Geolocation.md v1.0
TDD: Red -> Green -> Refactor
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError


class TestSpeakerGeolocationModel:
    """Phase 1.1: Test Speaker model has geolocation column"""

    def test_speaker_model_has_geolocation_column(self, test_db):
        """Speaker model should have geolocation column"""
        from app.models.device import Speaker
        from sqlalchemy import inspect

        mapper = inspect(Speaker)
        column_names = [c.key for c in mapper.columns]

        assert "geolocation" in column_names

    def test_speaker_geolocation_accepts_dict(self, test_db):
        """Speaker geolocation should accept dict (JSONB)"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(
            number_device=2401,
            group_device=0,
            name_device="VCS_2401",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL,
            geolocation={
                "location": "GOP 3초소 방송실",
                "latitude": 38.1234,
                "longitude": 127.5678,
                "altitude": 245.5
            }
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        assert speaker.geolocation is not None
        assert speaker.geolocation["location"] == "GOP 3초소 방송실"
        assert speaker.geolocation["latitude"] == 38.1234

    def test_speaker_geolocation_nullable(self, test_db):
        """Speaker geolocation should be nullable"""
        from app.models.device import Speaker
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType

        speaker = Speaker(
            number_device=2402,
            group_device=0,
            name_device="VCS_2402",
            type_device=EnumDeviceType.IpSpeaker,
            status=EnumDeviceStatus.ACTIVATED,
            speaker_type=EnumSpeakerType.NORMAL
            # No geolocation
        )
        test_db.add(speaker)
        test_db.commit()
        test_db.refresh(speaker)

        assert speaker.geolocation is None


class TestSpeakerGeolocationSchema:
    """Phase 2.1: Test Speaker schemas have geolocation field"""

    def test_speaker_create_has_geolocation_field(self):
        """SpeakerCreate schema should have geolocation field"""
        from app.schemas.device import SpeakerCreate, Geolocation

        data = SpeakerCreate(
            number_device=2401,
            name_device="VCS_2401",
            geolocation=Geolocation(
                location="GOP 3초소 방송실",
                latitude=38.1234,
                longitude=127.5678
            )
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "GOP 3초소 방송실"

    def test_speaker_create_geolocation_optional(self):
        """SpeakerCreate geolocation should be optional"""
        from app.schemas.device import SpeakerCreate

        data = SpeakerCreate(
            number_device=2401,
            name_device="VCS_2401"
            # No geolocation
        )
        assert data.geolocation is None

    def test_speaker_update_has_geolocation_field(self):
        """SpeakerUpdate schema should have geolocation field"""
        from app.schemas.device import SpeakerUpdate, Geolocation

        data = SpeakerUpdate(
            geolocation=Geolocation(
                location="Updated Location",
                latitude=38.5678
            )
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Updated Location"

    def test_speaker_response_has_geolocation_field(self):
        """SpeakerResponse schema should have geolocation field"""
        from app.schemas.device import SpeakerResponse, Geolocation
        from datetime import datetime

        data = SpeakerResponse(
            id=1,
            number_device=2401,
            group_device=0,
            name_device="VCS_2401",
            type_device="IpSpeaker",
            status="ACTIVATED",
            is_enable=True,
            speaker_type="NORMAL",
            geolocation=Geolocation(location="Test Location"),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Test Location"

    def test_speaker_nested_response_has_geolocation_field(self):
        """SpeakerNestedResponse schema should have geolocation field"""
        from app.schemas.device import SpeakerNestedResponse, Geolocation

        data = SpeakerNestedResponse(
            id=1,
            category_device="speaker",
            number_device=2401,
            name_device="VCS_2401",
            type_device="IpSpeaker",
            status="ACTIVATED",
            is_enable=True,
            speaker_type="NORMAL",
            geolocation=Geolocation(location="Nested Location")
        )
        assert data.geolocation is not None
        assert data.geolocation.location == "Nested Location"


class TestSpeakerGeolocationAPI:
    """Phase 3.1: Test Speaker API with geolocation"""

    def test_create_speaker_with_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/speakers should accept geolocation"""
        payload = {
            "number_device": 2410,
            "group_device": 0,
            "name_device": "Speaker with Location",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "speaker_type": "NORMAL",
            "geolocation": {
                "location": "GOP 3초소 방송실",
                "latitude": 38.1234,
                "longitude": 127.5678,
                "altitude": 245.5
            }
        }
        response = client.post("/api/devices/speakers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is not None
        assert data["data"]["geolocation"]["location"] == "GOP 3초소 방송실"
        assert data["data"]["geolocation"]["latitude"] == 38.1234

    def test_create_speaker_without_geolocation(self, client: TestClient, test_db):
        """POST /api/devices/speakers without geolocation should work"""
        payload = {
            "number_device": 2411,
            "group_device": 0,
            "name_device": "Speaker No Location",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "speaker_type": "NORMAL"
        }
        response = client.post("/api/devices/speakers", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["geolocation"] is None

    def test_get_speaker_includes_geolocation(self, client: TestClient, test_db):
        """GET /api/devices/speakers/{id} should include geolocation"""
        # Create a speaker with geolocation via API
        payload = {
            "number_device": 2412,
            "group_device": 0,
            "name_device": "Speaker for GET test",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "speaker_type": "NORMAL",
            "geolocation": {
                "location": "Test Location",
                "latitude": 38.5,
                "longitude": 127.5
            }
        }
        create_response = client.post("/api/devices/speakers", json=payload)
        assert create_response.status_code == 201
        speaker_id = create_response.json()["data"]["id"]

        response = client.get(f"/api/devices/speakers/{speaker_id}")
        assert response.status_code == 200
        data = response.json()
        assert "geolocation" in data["data"]
        assert data["data"]["geolocation"]["location"] == "Test Location"

    def test_update_speaker_geolocation(self, client: TestClient, test_db):
        """PATCH /api/devices/speakers/{id} should update geolocation"""
        # Create a speaker first via API
        create_payload = {
            "number_device": 2413,
            "group_device": 0,
            "name_device": "Speaker for PATCH test",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "speaker_type": "NORMAL"
        }
        create_response = client.post("/api/devices/speakers", json=create_payload)
        assert create_response.status_code == 201
        speaker_id = create_response.json()["data"]["id"]

        # Now update with geolocation
        payload = {
            "geolocation": {
                "location": "Updated Location",
                "latitude": 39.0,
                "longitude": 128.0
            }
        }
        response = client.patch(f"/api/devices/speakers/{speaker_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["geolocation"]["location"] == "Updated Location"
        assert data["data"]["geolocation"]["latitude"] == 39.0

    def test_replace_speaker_with_geolocation(self, client: TestClient, test_db):
        """PUT /api/devices/speakers/{id} should accept geolocation"""
        # Create a speaker first via API
        create_payload = {
            "number_device": 2414,
            "group_device": 0,
            "name_device": "Speaker for PUT test",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "speaker_type": "NORMAL"
        }
        create_response = client.post("/api/devices/speakers", json=create_payload)
        assert create_response.status_code == 201
        speaker_id = create_response.json()["data"]["id"]

        # Now replace with geolocation
        payload = {
            "number_device": 2414,
            "group_device": 0,
            "name_device": "Speaker Replaced",
            "type_device": "IpSpeaker",
            "status": "ACTIVATED",
            "speaker_type": "NORMAL",
            "geolocation": {
                "location": "Replaced Location",
                "latitude": 38.0,
                "longitude": 127.0
            }
        }
        response = client.put(f"/api/devices/speakers/{speaker_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["geolocation"]["location"] == "Replaced Location"


class TestGeolocationValidation:
    """Test geolocation field validation"""

    def test_latitude_range_validation(self):
        """Latitude should be between -90 and 90"""
        from app.schemas.device import Geolocation

        # Valid latitude
        geo = Geolocation(latitude=38.1234)
        assert geo.latitude == 38.1234

        # Invalid latitude (too high)
        with pytest.raises(ValidationError):
            Geolocation(latitude=91.0)

        # Invalid latitude (too low)
        with pytest.raises(ValidationError):
            Geolocation(latitude=-91.0)

    def test_longitude_range_validation(self):
        """Longitude should be between -180 and 180"""
        from app.schemas.device import Geolocation

        # Valid longitude
        geo = Geolocation(longitude=127.5678)
        assert geo.longitude == 127.5678

        # Invalid longitude (too high)
        with pytest.raises(ValidationError):
            Geolocation(longitude=181.0)

        # Invalid longitude (too low)
        with pytest.raises(ValidationError):
            Geolocation(longitude=-181.0)

    def test_location_max_length_validation(self):
        """Location should have max length of 500 characters"""
        from app.schemas.device import Geolocation

        # Valid location (within limit)
        geo = Geolocation(location="A" * 500)
        assert len(geo.location) == 500

        # Invalid location (too long)
        with pytest.raises(ValidationError):
            Geolocation(location="A" * 501)
