"""Password masking helper for Response schemas.

PRD: v4.9 Phase 5 (SEC-1) — .NET 통합 UI 팀 보안 요청 회신

- DB / 모델 / Create·Update 요청 schema는 평문 유지
- 본 모듈은 **Response 직렬화 시점**에만 평문을 마스크로 치환
- None 은 None 으로 유지 (미설정 vs 마스킹 구분)

차장님 결재 (2026-06-24): "계정 비번 다 보호, 삭제가 아니라 마스킹"
"""
from typing import Optional


PASSWORD_MASK: str = "********"  # 8자 고정 — 길이 추정 차단


def mask_password_serializer(value: Optional[str]) -> Optional[str]:
    """Pydantic v2 field_serializer 본체.

    Args:
        value: ORM/DB에서 읽어온 평문 비밀번호 또는 None

    Returns:
        None → None / 평문 → PASSWORD_MASK ('********')
    """
    if value is None:
        return None
    return PASSWORD_MASK
