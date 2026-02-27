@echo off
chcp 65001 >nul
echo ============================================================
echo   GOP DB Reset - admin/admin123 계정만 유지하고 초기화
echo ============================================================
echo.

set DB_PATH=data\gop.db

if exist %DB_PATH% (
    echo [1/3] 기존 DB 삭제: %DB_PATH%
    del /f %DB_PATH%
    echo       OK
) else (
    echo [1/3] DB 파일 없음 - 새로 생성합니다
)

echo.
echo [2/3] DB 초기화 (테이블 생성 + admin 계정 + 기본 설정)
python -c "from app.utils.init_db import initialize_database; initialize_database()"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 초기화 실패. Python 환경을 확인하세요.
    pause
    exit /b 1
)

echo.
echo [3/3] 완료!
echo.
echo   - admin / admin123 계정 생성됨 (Legacy + AccountUser)
echo   - 서버 카테고리 9종 생성됨
echo   - 보고서 템플릿 5종 생성됨
echo   - 샘플 더미 데이터: 없음
echo.
echo   서버를 시작하세요: uvicorn app.main:app --reload
echo ============================================================
pause
