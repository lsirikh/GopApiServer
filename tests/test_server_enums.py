"""
Tests for Server Monitoring Enums
TDD: Test First
"""
import pytest
from app.utils.enums import EnumServerType, EnumServerStatus


class TestEnumServerType:
    """Tests for EnumServerType enum (25종)"""

    def test_enum_server_type_exists(self):
        """EnumServerType이 존재하는지 확인"""
        assert EnumServerType is not None

    def test_enum_server_type_is_string_enum(self):
        """EnumServerType이 str Enum인지 확인"""
        assert issubclass(EnumServerType, str)

    # 영상/미디어 관련 (8종)
    def test_vms_server_type(self):
        """VMS 서버 타입"""
        assert EnumServerType.VMS.value == "VMS"

    def test_nvr_api_server_type(self):
        """NVR API 서버 타입"""
        assert EnumServerType.NVR_API.value == "NVR_API"

    def test_streaming_server_type(self):
        """스트리밍 서버 타입"""
        assert EnumServerType.STREAMING.value == "STREAMING"

    def test_transcoder_server_type(self):
        """트랜스코더 서버 타입"""
        assert EnumServerType.TRANSCODER.value == "TRANSCODER"

    def test_media_server_type(self):
        """미디어 서버 타입"""
        assert EnumServerType.MEDIA.value == "MEDIA"

    def test_recording_server_type(self):
        """녹화 서버 타입"""
        assert EnumServerType.RECORDING.value == "RECORDING"

    def test_playback_server_type(self):
        """재생 서버 타입"""
        assert EnumServerType.PLAYBACK.value == "PLAYBACK"

    def test_storage_server_type(self):
        """스토리지 서버 타입"""
        assert EnumServerType.STORAGE.value == "STORAGE"

    # AI/분석 관련 (4종)
    def test_ai_analysis_server_type(self):
        """지능형영상 분석 서버 타입"""
        assert EnumServerType.AI_ANALYSIS.value == "AI_ANALYSIS"

    def test_ai_training_server_type(self):
        """AI 학습 서버 타입"""
        assert EnumServerType.AI_TRAINING.value == "AI_TRAINING"

    def test_ai_inference_server_type(self):
        """AI 추론 서버 타입"""
        assert EnumServerType.AI_INFERENCE.value == "AI_INFERENCE"

    def test_analytics_server_type(self):
        """분석 서버 타입"""
        assert EnumServerType.ANALYTICS.value == "ANALYTICS"

    # API 서버 관련 (4종)
    def test_db_api_server_type(self):
        """DB API 서버 타입"""
        assert EnumServerType.DB_API.value == "DB_API"

    def test_speaker_api_server_type(self):
        """SPEAKER API 서버 타입"""
        assert EnumServerType.SPEAKER_API.value == "SPEAKER_API"

    def test_enclosure_api_server_type(self):
        """함체관리 API 서버 타입"""
        assert EnumServerType.ENCLOSURE_API.value == "ENCLOSURE_API"

    def test_pids_api_server_type(self):
        """PIDS API 서버 타입"""
        assert EnumServerType.PIDS_API.value == "PIDS_API"

    # 인프라/네트워크 관련 (6종)
    def test_web_server_type(self):
        """웹 서버 타입"""
        assert EnumServerType.WEB.value == "WEB"

    def test_auth_server_type(self):
        """인증 서버 타입"""
        assert EnumServerType.AUTH.value == "AUTH"

    def test_proxy_server_type(self):
        """프록시 서버 타입"""
        assert EnumServerType.PROXY.value == "PROXY"

    def test_broker_server_type(self):
        """브로커 서버 타입"""
        assert EnumServerType.BROKER.value == "BROKER"

    def test_gateway_server_type(self):
        """게이트웨이 서버 타입"""
        assert EnumServerType.GATEWAY.value == "GATEWAY"

    def test_push_server_type(self):
        """푸시 서버 타입"""
        assert EnumServerType.PUSH.value == "PUSH"

    # 운영/관리 관련 (3종)
    def test_log_server_type(self):
        """로그 서버 타입"""
        assert EnumServerType.LOG.value == "LOG"

    def test_backup_server_type(self):
        """백업 서버 타입"""
        assert EnumServerType.BACKUP.value == "BACKUP"

    def test_monitoring_server_type(self):
        """모니터링 서버 타입"""
        assert EnumServerType.MONITORING.value == "MONITORING"

    # 기타 (1종)
    def test_etc_server_type(self):
        """기타 서버 타입"""
        assert EnumServerType.ETC.value == "ETC"

    def test_total_server_types_count(self):
        """서버 타입 총 개수 확인 (26종 - PIDS_API 포함)"""
        assert len(EnumServerType) == 26


class TestEnumServerStatus:
    """Tests for EnumServerStatus enum (3종)"""

    def test_enum_server_status_exists(self):
        """EnumServerStatus가 존재하는지 확인"""
        assert EnumServerStatus is not None

    def test_enum_server_status_is_string_enum(self):
        """EnumServerStatus가 str Enum인지 확인"""
        assert issubclass(EnumServerStatus, str)

    def test_normal_status(self):
        """정상 상태"""
        assert EnumServerStatus.NORMAL.value == "NORMAL"

    def test_warning_status(self):
        """경고 상태"""
        assert EnumServerStatus.WARNING.value == "WARNING"

    def test_error_status(self):
        """오류 상태"""
        assert EnumServerStatus.ERROR.value == "ERROR"

    def test_total_status_count(self):
        """상태 타입 총 개수 확인 (3종)"""
        assert len(EnumServerStatus) == 3
