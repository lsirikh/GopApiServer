@echo off
REM GOP 인증서 인스톨러 빌드 wrapper (차장님 PC에서 더블클릭 또는 명령행 실행)
REM 입력: certs/installer_ps2exe/{server,client}_install.ps1 + ps2exe.ps1
REM 출력: certs/server_install.exe + certs/client_install.exe
REM
REM 사전 요구사항: 인터넷 접속 (ps2exe.ps1 자동 다운로드) 또는 같은 폴더에 ps2exe.ps1 동봉

setlocal
set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\.."

echo.
echo ========================================
echo  GOP 인증서 인스톨러 빌드 시작
echo ========================================
echo.

REM ps2exe.ps1 다운로드 (없으면)
if not exist "%SCRIPT_DIR%ps2exe.ps1" (
    echo [INFO] ps2exe.ps1 다운로드 중...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/MScholtes/PS2EXE/master/Module/ps2exe.ps1' -OutFile '%SCRIPT_DIR%ps2exe.ps1' -UseBasicParsing"
    if errorlevel 1 (
        echo [ERROR] ps2exe.ps1 다운로드 실패. 인터넷 연결 또는 같은 폴더에 ps2exe.ps1 동봉 필요.
        pause
        exit /b 1
    )
)

REM rootCA.pem Base64 임베드 (mkcert CAROOT)
echo [INFO] rootCA.pem 임베드 (Base64)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$caRoot = $env:LOCALAPPDATA + '\mkcert\rootCA.pem'; ^
     if (-not (Test-Path $caRoot)) { Write-Host '[ERROR] mkcert rootCA.pem 없음. server_install.exe 먼저 실행하여 mkcert -install 수행.'; exit 1 }; ^
     $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($caRoot)); ^
     $ps1 = '%SCRIPT_DIR%client_install.ps1'; ^
     $c = Get-Content $ps1 -Raw -Encoding UTF8; ^
     $c = $c -replace \"'__ROOT_CA_BASE64_PLACEHOLDER__'\", (\"'\" + $b64 + \"'\"); ^
     Set-Content -Path $ps1 -Value $c -Encoding UTF8; ^
     Write-Host ('[OK] rootCA Base64 임베드: ' + $b64.Length + ' chars')"

if errorlevel 1 goto :error

echo.
echo [INFO] server_install.exe 빌드...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "& { . '%SCRIPT_DIR%ps2exe.ps1'; Invoke-PS2EXE -InputFile '%SCRIPT_DIR%server_install.ps1' -OutputFile '%REPO_ROOT%\certs\server_install.exe' -Title 'GOP Server Cert Setup' -Company 'GOP' -Version '1.0.0.0' -RequireAdmin }"

if errorlevel 1 goto :error

echo.
echo [INFO] client_install.exe 빌드...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "& { . '%SCRIPT_DIR%ps2exe.ps1'; Invoke-PS2EXE -InputFile '%SCRIPT_DIR%client_install.ps1' -OutputFile '%REPO_ROOT%\certs\client_install.exe' -Title 'GOP Client Cert Setup' -Company 'GOP' -Version '1.0.0.0' -RequireAdmin }"

if errorlevel 1 goto :error

echo.
echo ========================================
echo  빌드 완료
echo ========================================
echo.
echo  certs\server_install.exe  -^> 서버 PC에서 실행 (mkcert + 인증서 발급)
echo  certs\client_install.exe  -^> 클라 PC에서 실행 (rootCA 등록)
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] 빌드 실패. 위 오류 메시지 확인.
pause
exit /b 1
