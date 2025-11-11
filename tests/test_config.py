"""
Test: 환경 설정 검증
"""
from pathlib import Path


def test_env_example_file_exists():
    """Test that .env.example file exists"""
    base_dir = Path(__file__).parent.parent
    env_example_file = base_dir / ".env.example"

    assert env_example_file.exists(), ".env.example should exist"
    assert env_example_file.is_file(), ".env.example should be a file"


def test_env_example_contains_required_variables():
    """Test that .env.example contains all required environment variables"""
    base_dir = Path(__file__).parent.parent
    env_example_file = base_dir / ".env.example"

    with open(env_example_file, "r") as f:
        content = f.read()

    required_vars = [
        "AUTH_MODE",
        "JWT_SECRET_KEY",
        "JWT_ALGORITHM",
        "JWT_EXPIRATION_HOURS",
        "DATABASE_URL",
        "HOST",
        "PORT",
        "DEBUG",
        "LOG_LEVEL",
        "CORS_ORIGINS",
    ]

    for var in required_vars:
        assert var in content, f"{var} should be in .env.example"
