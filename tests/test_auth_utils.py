"""
Test: 인증 유틸리티 함수 검증
"""


def test_hash_password_creates_bcrypt_hash():
    """Test that hash_password creates a bcrypt hash"""
    from app.utils.auth import hash_password

    password = "secure123"
    hashed = hash_password(password)

    # Bcrypt hashes start with $2b$
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60  # Bcrypt hashes are 60 characters


def test_verify_password_validates_correctly():
    """Test that verify_password correctly validates passwords"""
    from app.utils.auth import hash_password, verify_password

    password = "secure123"
    hashed = hash_password(password)

    # Correct password should verify
    assert verify_password(password, hashed) is True

    # Incorrect password should not verify
    assert verify_password("wrongpassword", hashed) is False


def test_same_password_produces_different_hashes():
    """Test that hashing same password twice produces different hashes (salt)"""
    from app.utils.auth import hash_password

    password = "secure123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Hashes should be different due to salt
    assert hash1 != hash2
