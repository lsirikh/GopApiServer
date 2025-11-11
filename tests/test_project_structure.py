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


def test_init_files_exist():
    """Test that __init__.py files exist in all required directories"""
    base_dir = Path(__file__).parent.parent

    init_files = [
        "app/__init__.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "app/routers/__init__.py",
        "app/services/__init__.py",
        "app/repositories/__init__.py",
        "app/utils/__init__.py",
        "app/middleware/__init__.py",
        "tests/__init__.py",
    ]

    for init_file_path in init_files:
        file_path = base_dir / init_file_path
        assert file_path.exists(), f"{init_file_path} should exist"
        assert file_path.is_file(), f"{init_file_path} should be a file"
