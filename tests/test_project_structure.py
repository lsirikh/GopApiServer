"""
Test: 프로젝트 디렉토리 구조 검증
"""
import os
from pathlib import Path


def test_project_directories_exist():
    """Test that all required project directories exist"""
    base_dir = Path(__file__).parent.parent

    required_dirs = [
        "app",
        "tests",
        "data",
        "logs",
    ]

    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        assert dir_path.exists(), f"Directory {dir_name} should exist"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"


def test_requirements_file_exists():
    """Test that requirements.txt exists"""
    base_dir = Path(__file__).parent.parent
    requirements_file = base_dir / "requirements.txt"

    assert requirements_file.exists(), "requirements.txt should exist"
    assert requirements_file.is_file(), "requirements.txt should be a file"
