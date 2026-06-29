"""
TokenBlacklist model — JWT jti 블랙리스트

PRD: v4.9 Phase 2-A4 (D1 결재: 잠정 DB 저장소)
- IBlacklistStore 추상화는 v5.0에서 Redis/NATS KV 전환 시 도입
"""
from datetime import datetime
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, DateTime
from app.database import Base


class TokenBlacklist(Base):
    """
    JWT jti 블랙리스트 (logout/lock/password-change/forced 시 등록)

    조회 패턴: get_current_account_user 의존성에서 jti 단건 조회 (jti UNIQUE 인덱스)
    정리: APScheduler 1시간마다 expires_at < now() 인 row 삭제 (Phase 5)
    """
    __tablename__ = "token_blacklist"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True, index=True)
    token_type = Column(String(20), nullable=False, default="access")  # 'access' or 'refresh'
    reason = Column(String(50), nullable=False)  # LOGOUT / LOCK / PASSWORD_CHANGE / FORCED / REVOKED
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<TokenBlacklist jti={self.jti[:8]}... reason={self.reason}>"
