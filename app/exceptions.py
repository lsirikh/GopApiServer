"""
공용 HTTP 예외 — 안정 머신 코드를 error.code 로 노출하기 위한 HTTPException 확장.

PRD Force_Logout FR-SVF-10 (계약 C4):
전역 핸들러(app/main.py)는 status→code 매핑(401→UNAUTHORIZED)만 했기에 revoked/expired/invalid
가 모두 동일 코드로 뭉개져 클라가 폐기 상태를 신뢰성 있게 구분할 수 없었다. detection 지점에서
안정 sub-code 를 부여하면 핸들러가 그 코드를 error.code 로 렌더하고, 클라는 메시지 문자열이 아니라
이 코드로 분기한다. 401(재인증 필요) vs 403(권한 부족, 세션 유지) 구분도 명확해진다.
"""
from typing import Optional
from fastapi import HTTPException, status


class RevokedTokenError(HTTPException):
    """폐기된 세션 → 401 + error.code='SESSION_REVOKED' (+ details.reason).

    클라는 SESSION_REVOKED 수신 시 토큰 폐기·UI 잠금·재로그인. reason 으로 메시지 맞춤화 가능
    (FORCED / LOGOUT / PASSWORD_CHANGE 등). WWW-Authenticate 는 RFC 6750 invalid_token 으로.
    """
    def __init__(self, reason: Optional[str] = None, detail: str = "Session has been revoked"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
        self.code = "SESSION_REVOKED"
        self.details = {"reason": reason} if reason else None
