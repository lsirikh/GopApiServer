#Requires -Version 5.1
<#
.SYNOPSIS
    GOP API Server 신규 PC 최초 배포 자동화 (git clone 후 실행)
.DESCRIPTION
    1) 관리자 권한 자동 상승 (UAC)
    2) certs/server.crt 없으면 server_install.exe 실행 → mkcert 자동 다운로드 + 인증서 발급 + rootCA 등록
    3) docker compose build → up -d
    4) 컨테이너 healthy 대기 + HTTPS 헬스체크 확인
    5) 접속 URL 안내

    v6.0-cert_installer_fix 이후 최소 사용자 조치 방식:
      git clone <repo>
      pwsh -ExecutionPolicy Bypass -File bootstrap.ps1
      (또는 Windows 파일탐색기에서 bootstrap.ps1 우클릭 → PowerShell로 실행)
.NOTES
    Author : GOP Team
    Version: 1.0.0
    태그    : v6.0-bootstrap_automation (2026-07-06)
#>

[CmdletBinding()]
param(
    [switch]$SkipCerts,       # 인증서 발급 스킵 (이미 발급됨)
    [switch]$SkipDocker,      # docker compose up 스킵
    [switch]$Rebuild,         # docker compose build --no-cache
    [switch]$AllowHttpFallback,  # 인증서 없이 HTTP로 기동 (개발용, 프로덕션 금지)
    [switch]$ForceCerts,      # 기존 cert 무시하고 강제 재발급 (SAN 변경 적용)
    [switch]$NonInteractive   # 완전 무인 (실패 시 종료 대기 Read-Host 도 스킵 — CI/스크립트용)
)

$ErrorActionPreference = 'Stop'

# 콘솔 한글 UTF-8
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 | Out-Null
} catch { }

# ----- 헬퍼 ----------------------------------------------------------------
function Write-Banner {
    param([string]$Title, [string]$Color = 'Cyan')
    $bar = '=' * 72
    Write-Host ''
    Write-Host $bar -ForegroundColor $Color
    Write-Host " $Title" -ForegroundColor White
    Write-Host $bar -ForegroundColor $Color
    Write-Host ''
}

function Write-Step {
    param([string]$Msg, [string]$Color = 'Cyan')
    Write-Host ('==> ' + $Msg) -ForegroundColor $Color
}

function Test-IsAdmin {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $pri = New-Object System.Security.Principal.WindowsPrincipal($id)
    return $pri.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ----- 0) 관리자 권한 자동 상승 -------------------------------------------
if (-not (Test-IsAdmin)) {
    Write-Host ''
    Write-Host '관리자 권한이 필요합니다. UAC를 통해 재실행합니다...' -ForegroundColor Yellow
    Write-Host '(mkcert 로컬 CA 등록과 인증서 발급에 관리자 권한이 필요합니다)' -ForegroundColor DarkGray

    $scriptPath = $PSCommandPath
    if (-not $scriptPath) { $scriptPath = $MyInvocation.MyCommand.Path }

    # 원본 param 재조립 (UAC 재실행에도 스위치 전파)
    $argList = @('-ExecutionPolicy', 'Bypass', '-File', "`"$scriptPath`"")
    if ($SkipCerts)          { $argList += '-SkipCerts' }
    if ($SkipDocker)         { $argList += '-SkipDocker' }
    if ($Rebuild)            { $argList += '-Rebuild' }
    if ($AllowHttpFallback)  { $argList += '-AllowHttpFallback' }
    if ($ForceCerts)         { $argList += '-ForceCerts' }
    if ($NonInteractive)     { $argList += '-NonInteractive' }

    Start-Process powershell.exe -Verb RunAs -ArgumentList $argList
    exit
}

Write-Banner 'GOP API Server 배포 자동화 (bootstrap.ps1)'

# 프로젝트 루트 = bootstrap.ps1 위치
$repoRoot = $PSScriptRoot
if (-not $repoRoot) { $repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }
Set-Location $repoRoot
Write-Host "프로젝트 루트: $repoRoot" -ForegroundColor DarkGray

# ----- 1) 사전 도구 검증 ---------------------------------------------------
Write-Step '1/5 사전 도구 검증'

# docker
$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host '[FAIL] docker.exe 를 찾을 수 없습니다.' -ForegroundColor Red
    Write-Host '  Docker Desktop 을 먼저 설치하고 실행해 주세요: https://www.docker.com/products/docker-desktop' -ForegroundColor Yellow
    Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
    [void](Read-Host)
    exit 1
}
Write-Host "  docker : $($docker.Source)" -ForegroundColor Green

# docker compose 정상 응답
try {
    $dockerVer = docker version --format '{{.Server.Version}}' 2>$null
    if (-not $dockerVer) { throw 'docker daemon 응답 없음' }
    Write-Host "  daemon : $dockerVer" -ForegroundColor Green
} catch {
    Write-Host '[FAIL] Docker Desktop 이 실행 중이 아닙니다.' -ForegroundColor Red
    Write-Host '  트레이 아이콘에서 Docker Desktop 을 시작한 후 다시 실행해 주세요.' -ForegroundColor Yellow
    Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
    [void](Read-Host)
    exit 1
}

# .env 확인 (없으면 .env.example 복사)
$envPath = Join-Path $repoRoot '.env'
$envExamplePath = Join-Path $repoRoot '.env.example'
if (-not (Test-Path $envPath)) {
    if (Test-Path $envExamplePath) {
        Copy-Item -Path $envExamplePath -Destination $envPath -Force
        Write-Host "  .env : .env.example 로부터 자동 생성" -ForegroundColor Yellow
    } else {
        Write-Host "  .env : 파일 없음 (docker-compose 기본값 사용)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  .env : 존재" -ForegroundColor Green
}

# ----- 2) 인증서 발급 -----------------------------------------------------
Write-Step '2/5 HTTPS 인증서 확인/발급'

$certDir = Join-Path $repoRoot 'certs'
$crt = Join-Path $certDir 'server.crt'
$key = Join-Path $certDir 'server.key'
$serverInstallExe = Join-Path $certDir 'server_install.exe'

$certsPresent = (Test-Path $crt) -and (Test-Path $key)

# v6.3-cert_gitignore: .exe 는 git 미추적(빌드 산출물). fresh clone 에서 인증서 발급에
#   server_install.exe 가 필요한데 없으면 .ps1 소스에서 먼저 빌드(placeholder CA, step 2.5 에서 실제 CA 재임베드).
if (-not $SkipCerts -and -not $certsPresent -and -not (Test-Path $serverInstallExe)) {
    $preBuild = Join-Path $repoRoot 'certs/installer_ps2exe/build_install_exe.ps1'
    if (Test-Path $preBuild) {
        Write-Host "  server_install.exe 미존재 -> .ps1 소스에서 빌드..." -ForegroundColor Cyan
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $preBuild
    }
}

if ($SkipCerts) {
    Write-Host "  -SkipCerts 지정됨: 인증서 발급 단계 스킵" -ForegroundColor Yellow
} elseif ($AllowHttpFallback -and -not $certsPresent) {
    Write-Host "  -AllowHttpFallback 지정됨: 인증서 없이 HTTP로 기동 (프로덕션 금지)" -ForegroundColor Yellow
    $env:ALLOW_HTTP_FALLBACK = 'true'
} elseif ($certsPresent -and -not $ForceCerts) {
    Write-Host "  server.crt / server.key 이미 존재. 스킵" -ForegroundColor Green
    Write-Host "  강제 재발급이 필요하면: $serverInstallExe 직접 실행" -ForegroundColor DarkGray
} elseif (Test-Path $serverInstallExe) {
    Write-Host "  server_install.exe 실행 중 (mkcert 자동 다운로드 + rootCA 등록 + server.crt/key 발급)..." -ForegroundColor Cyan

    # v6.0-installer_ps2exe_path_fix (2026-07-07):
    #   -CertDir 을 명시 전달 → EXE 내부 경로 자동판정(PS2EXE에서 빈 문자열 위험)에 의존하지 않음.
    #   -NonInteractive → EXE 가 SAN 입력/종료 대기에서 멈추지 않고 무인 진행.
    #   -WorkingDirectory → 혹시 상대경로 폴백이 타더라도 certs 를 CWD 로.
    $installArgs = @('-CertDir', "`"$certDir`"", '-NonInteractive')
    $installProc = Start-Process -FilePath $serverInstallExe -ArgumentList $installArgs `
                                 -WorkingDirectory $certDir -Wait -PassThru
    if ($installProc.ExitCode -ne 0) {
        Write-Host "[FAIL] server_install.exe exit code = $($installProc.ExitCode)" -ForegroundColor Red
        Write-Host "  로그: %TEMP%\GOP-Server-Install.log" -ForegroundColor Yellow
        if (-not $NonInteractive) { Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray; [void](Read-Host) }
        exit 1
    }

    # 발급 결과 검증 + certs\certs 중첩 등 오생성 안전망 (v6.0-installer_ps2exe_path_fix)
    if (-not ((Test-Path $crt) -and (Test-Path $key))) {
        Write-Host "  기대 경로에 인증서 없음 → 하위 경로 재탐색 (certs\certs 중첩 등 대비)..." -ForegroundColor Yellow
        $foundCrt = Get-ChildItem -Path $repoRoot -Filter 'server.crt' -Recurse -ErrorAction SilentlyContinue |
                    Where-Object { $_.FullName -ne $crt } | Select-Object -First 1
        if ($foundCrt) {
            $foundDir = Split-Path -Parent $foundCrt.FullName
            $foundKey = Join-Path $foundDir 'server.key'
            Write-Host "  발견: $($foundCrt.FullName) → certs\ 로 이동" -ForegroundColor Cyan
            Copy-Item -Path $foundCrt.FullName -Destination $crt -Force
            if (Test-Path $foundKey) { Copy-Item -Path $foundKey -Destination $key -Force }
            # rootCA.pem 도 같은 폴더에 있으면 함께 회수
            $foundRootCa = Join-Path $foundDir 'rootCA.pem'
            if (Test-Path $foundRootCa) { Copy-Item -Path $foundRootCa -Destination (Join-Path $certDir 'rootCA.pem') -Force }
        }
    }

    if (-not ((Test-Path $crt) -and (Test-Path $key))) {
        Write-Host "[FAIL] 인증서 발급 후에도 server.crt / server.key 를 찾을 수 없습니다." -ForegroundColor Red
        Write-Host "  기대 경로 : $certDir" -ForegroundColor DarkGray
        Write-Host "  로그      : %TEMP%\GOP-Server-Install.log" -ForegroundColor DarkGray
        Write-Host "  수동 확인 : Get-ChildItem -Path `"$repoRoot`" -Filter server.crt -Recurse" -ForegroundColor DarkGray
        if (-not $NonInteractive) { Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray; [void](Read-Host) }
        exit 1
    }
    Write-Host "  인증서 발급 완료: server.crt + server.key" -ForegroundColor Green
} else {
    Write-Host "[FAIL] server_install.exe 를 찾을 수 없습니다: $serverInstallExe" -ForegroundColor Red
    Write-Host "  대안 1) mkcert 를 직접 설치해서 발급:" -ForegroundColor Yellow
    Write-Host "     mkcert -install"
    Write-Host "     mkcert -cert-file certs/server.crt -key-file certs/server.key localhost 127.0.0.1 ::1 host.docker.internal"
    Write-Host "  대안 2) 개발 편의로 HTTP 허용 (프로덕션 금지):" -ForegroundColor Yellow
    Write-Host "     bootstrap.ps1 -AllowHttpFallback"
    Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
    [void](Read-Host)
    exit 1
}

# ----- 2.5) client_install.exe 재빌드 (이 서버 CA 임베드) -------------------
# v6.3-cert_san_expand: 서버 CA 는 이 서버 PC 의 mkcert -install 로 생성/사용된다.
#   클라 배포용 client_install.exe 가 이 서버의 rootCA 를 임베드해야 클라 PC 가 이 서버
#   인증서를 신뢰한다. 방금 발급된 certs/rootCA.pem 을 임베드해 client_install.exe 를 재생성한다.
#   git clone + bootstrap.ps1 만으로 배포용 client_install.exe 가 완성된다.
if ($SkipCerts) {
    Write-Step '2.5/5 client_install.exe 재빌드 (스킵 - -SkipCerts)'
} else {
    Write-Step '2.5/5 client_install.exe 재빌드 (이 서버 rootCA 임베드)'
    $buildScript = Join-Path $repoRoot 'certs/installer_ps2exe/build_install_exe.ps1'
    $rootCaPem   = Join-Path $certDir 'rootCA.pem'
    if ((Test-Path $buildScript) -and (Test-Path $rootCaPem)) {
        try {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $buildScript -RootCaPath $rootCaPem
            if ($LASTEXITCODE -ne 0) { throw "build_install_exe.ps1 exit $LASTEXITCODE" }
            Write-Host "  client_install.exe 재빌드 완료 (이 서버 CA 임베드)" -ForegroundColor Green
            Write-Host "  클라이언트 PC 로 전달해 실행: (repo)/certs/client_install.exe" -ForegroundColor Cyan
        } catch {
            Write-Host "  [WARN] client_install.exe 재빌드 실패: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "  대안) certs/rootCA.pem 을 클라 PC 의 client_install.exe 와 같은 폴더에 두고 실행" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [WARN] build 스크립트/rootCA.pem 미발견 - 재빌드 스킵" -ForegroundColor Yellow
    }
}

# ----- 3) docker compose build --------------------------------------------
if ($SkipDocker) {
    Write-Step '3/5 docker compose build (스킵)'
} else {
    Write-Step '3/5 docker compose build'
    Push-Location $repoRoot
    try {
        if ($Rebuild) {
            docker compose build --no-cache
        } else {
            docker compose build
        }
        if ($LASTEXITCODE -ne 0) { throw "docker compose build 실패 (exit $LASTEXITCODE)" }
        Write-Host "  build 성공" -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# ----- 4) docker compose up + healthy 대기 --------------------------------
if ($SkipDocker) {
    Write-Step '4/5 docker compose up (스킵)'
} else {
    Write-Step '4/5 docker compose up -d + healthy 대기'
    Push-Location $repoRoot
    try {
        docker compose up -d
        if ($LASTEXITCODE -ne 0) { throw "docker compose up 실패 (exit $LASTEXITCODE)" }
    } finally {
        Pop-Location
    }

    # healthy 대기 (최대 120초)
    Write-Host "  pids-api-server 컨테이너 healthy 대기 (최대 120초)..." -ForegroundColor DarkGray
    $maxWait = 120
    $waited = 0
    $healthy = $false
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 3
        $waited += 3
        try {
            $state = docker inspect pids-api-server --format '{{.State.Health.Status}}' 2>$null
        } catch { $state = $null }
        if ($state -eq 'healthy') {
            $healthy = $true
            break
        }
        Write-Host ("  [${waited}s] state=" + $state) -ForegroundColor DarkGray
    }

    if (-not $healthy) {
        Write-Host "[WARN] 120초 내에 healthy 도달하지 못했습니다. 로그를 확인해 주세요:" -ForegroundColor Yellow
        Write-Host "  docker logs pids-api-server --tail 50" -ForegroundColor DarkCyan
    } else {
        Write-Host "  healthy 도달" -ForegroundColor Green
    }
}

# ----- 5) 접속 확인 안내 --------------------------------------------------
Write-Banner '5/5 배포 완료'

$scheme = if ($env:ALLOW_HTTP_FALLBACK -eq 'true') { 'http' } else { 'https' }
Write-Host "API Base    : ${scheme}://localhost:8000" -ForegroundColor Green
Write-Host "Swagger UI  : ${scheme}://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health      : ${scheme}://localhost:8000/api/tracking/health" -ForegroundColor Green
Write-Host "DB Admin    : http://localhost:8080  (adminer)" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "기본 계정   : admin / admin123" -ForegroundColor DarkGray
Write-Host "매니저 계정 : m_manager, vms_manager, popup_manager, CameraManager," -ForegroundColor DarkGray
Write-Host "              BroadcastingManager, QLiteLampManager, NVRManager, EnclosureManager" -ForegroundColor DarkGray
Write-Host "매니저 pw   : sensorway1 (프로덕션에서는 즉시 변경)" -ForegroundColor Yellow
Write-Host ""
Write-Host "HTTPS 신뢰: 클라이언트 PC 에는 certs\client_install.exe 를 배포하여 rootCA 를 신뢰 저장소에 등록하세요." -ForegroundColor DarkGray
Write-Host ""
if (-not $NonInteractive) {
    Write-Host "엔터를 눌러 종료..." -ForegroundColor DarkGray
    [void](Read-Host)
}
exit 0
