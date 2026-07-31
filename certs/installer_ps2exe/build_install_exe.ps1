<#
.SYNOPSIS
    server_install.exe + client_install.exe 빌드 자동화
.DESCRIPTION
    1) PS2EXE 모듈 보장 (없으면 설치)
    2) rootCA.pem 을 Base64 로 읽어 client_install.ps1 의 placeholder 치환
    3) Invoke-PS2EXE 로 두 PS1 -> EXE 변환
    4) 결과물을 certs/ 에 배치
.NOTES
    실행: pwsh -ExecutionPolicy Bypass -File build_install_exe.ps1
#>

[CmdletBinding()]
param(
    # 버그 5 픽스 (2026-07-06): param() 기본값 평가 시 $MyInvocation.MyCommand.Path가 null일 수 있음
    # (powershell.exe -File 방식 실행 시 등). 본문에서 $PSScriptRoot 기반으로 계산.
    [string]$ProjectRoot     = '',
    [string]$CertsDir        = '',
    [string]$ServerPs1       = '',
    [string]$ClientPs1       = '',
    [string]$RootCaPath      = '',
    [string]$Version         = '1.0.0.0',
    [string]$Company         = 'GOP',
    [switch]$SkipModuleCheck,
    [switch]$KeepTemp
)

$ErrorActionPreference = 'Stop'

# ----- 경로 기본값 (본문에서 계산 — 버그 4·5 픽스) --------------------------
# 이 스크립트 위치: <repo>\certs\installer_ps2exe\build_install_exe.ps1
#   $PSScriptRoot                          = <repo>\certs\installer_ps2exe
#   Split-Path -Parent $PSScriptRoot       = <repo>\certs
#   Split-Path -Parent (그 부모)            = <repo>
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
if (-not $CertsDir)    { $CertsDir    = Split-Path -Parent $PSScriptRoot }  # <repo>\certs
if (-not $ServerPs1)   { $ServerPs1   = Join-Path $PSScriptRoot 'server_install.ps1' }
if (-not $ClientPs1)   { $ClientPs1   = Join-Path $PSScriptRoot 'client_install.ps1' }
if (-not $RootCaPath) {
    # mkcert -CAROOT 가능하면 사용
    $mkcert = Get-Command mkcert.exe -ErrorAction SilentlyContinue
    if ($mkcert) {
        $caRoot = (& $mkcert -CAROOT 2>$null | Select-Object -First 1).ToString().Trim()
        $RootCaPath = Join-Path $caRoot 'rootCA.pem'
    }
}

function Write-Step {
    param([string]$Msg, [string]$Color = 'Cyan')
    Write-Host ''
    Write-Host ('==> ' + $Msg) -ForegroundColor $Color
}

function Fail {
    param([string]$Msg)
    Write-Host "[FAIL] $Msg" -ForegroundColor Red
    exit 1
}

# ----- 0) 사전 검증 ---------------------------------------------------------
Write-Step '0/4 사전 검증'
Write-Host "  ProjectRoot : $ProjectRoot"
Write-Host "  CertsDir    : $CertsDir"
Write-Host "  ServerPs1   : $ServerPs1"
Write-Host "  ClientPs1   : $ClientPs1"
Write-Host "  RootCaPath  : $RootCaPath"
Write-Host "  Version     : $Version"

if (-not (Test-Path $ServerPs1)) { Fail "server_install.ps1 없음: $ServerPs1" }
if (-not (Test-Path $ClientPs1)) { Fail "client_install.ps1 없음: $ClientPs1" }
if (-not (Test-Path $CertsDir))  { New-Item -ItemType Directory -Path $CertsDir -Force | Out-Null }

# ----- 1) PS2EXE 모듈 -------------------------------------------------------
if (-not $SkipModuleCheck) {
    Write-Step '1/4 PS2EXE 모듈 확인'
    $mod = Get-Module -ListAvailable -Name ps2exe | Select-Object -First 1
    if (-not $mod) {
        Write-Host '  ps2exe 모듈 설치 중 (CurrentUser scope)...' -ForegroundColor Yellow
        try {
            if (-not (Get-PackageProvider -Name NuGet -ErrorAction SilentlyContinue)) {
                Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser | Out-Null
            }
            Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction SilentlyContinue
            Install-Module -Name ps2exe -Scope CurrentUser -Force -AllowClobber
        } catch {
            Fail "ps2exe 설치 실패: $($_.Exception.Message)"
        }
    } else {
        Write-Host "  ps2exe 발견: v$($mod.Version)" -ForegroundColor Green
    }
    Import-Module ps2exe -Force
} else {
    Import-Module ps2exe -Force -ErrorAction SilentlyContinue
}

# ----- 2) rootCA.pem -> Base64 치환 -----------------------------------------
Write-Step '2/4 rootCA.pem Base64 임베드'

$tempDir = Join-Path $env:TEMP ("gop_build_" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

$clientPs1Patched = Join-Path $tempDir 'client_install.ps1'
$serverPs1Copy    = Join-Path $tempDir 'server_install.ps1'

# server 는 그대로 복사
Copy-Item -Path $ServerPs1 -Destination $serverPs1Copy -Force

# client 는 placeholder 치환
$clientRaw = Get-Content -Path $ClientPs1 -Raw -Encoding UTF8

if (-not $RootCaPath -or -not (Test-Path $RootCaPath)) {
    Write-Host "  [WARN] rootCA.pem 미발견 -> placeholder 유지 (런타임 fallback 으로 동작)" -ForegroundColor Yellow
    Set-Content -Path $clientPs1Patched -Value $clientRaw -Encoding UTF8
} else {
    $rootBytes = [System.IO.File]::ReadAllBytes($RootCaPath)
    $b64       = [Convert]::ToBase64String($rootBytes)
    Write-Host "  rootCA 바이트   : $($rootBytes.Length)"
    Write-Host "  Base64 길이     : $($b64.Length)"
    if ($clientRaw -notmatch '__ROOT_CA_BASE64_PLACEHOLDER__') {
        Fail "client_install.ps1 에 __ROOT_CA_BASE64_PLACEHOLDER__ 가 없습니다."
    }
    $patched = $clientRaw.Replace('__ROOT_CA_BASE64_PLACEHOLDER__', $b64)
    Set-Content -Path $clientPs1Patched -Value $patched -Encoding UTF8
    Write-Host "  치환 완료 -> $clientPs1Patched" -ForegroundColor Green
}

# ----- 3) PS2EXE 변환 -------------------------------------------------------
Write-Step '3/4 PS2EXE 변환'

$serverExe = Join-Path $CertsDir 'server_install.exe'
$clientExe = Join-Path $CertsDir 'client_install.exe'

$commonArgs = @{
    NoConsole       = $false
    RequireAdmin    = $true
    Version         = $Version
    Company         = $Company
    Product         = 'GOP Certificate Installer'
    Copyright       = "Copyright (c) $(Get-Date -Format yyyy) $Company"
    Verbose         = $false
}
# 클라 설치기는 관리자 불필요 (CurrentUser 저장소, 설치 확인창만 표시)
$clientArgs = $commonArgs.Clone()
$clientArgs.RequireAdmin = $false

try {
    Write-Host "  -> $serverExe" -ForegroundColor Cyan
    Invoke-PS2EXE `
        -InputFile  $serverPs1Copy `
        -OutputFile $serverExe `
        -Title      'GOP 서버 인증서 설정' `
        -Description 'GOP API 서버용 mkcert 인증서 발급기' `
        @commonArgs
    if (-not (Test-Path $serverExe)) { Fail 'server_install.exe 생성 실패' }
    Write-Host "  OK ($([math]::Round((Get-Item $serverExe).Length/1KB,1)) KB)" -ForegroundColor Green
} catch {
    Fail "server_install.exe 빌드 실패: $($_.Exception.Message)"
}

try {
    Write-Host "  -> $clientExe" -ForegroundColor Cyan
    Invoke-PS2EXE `
        -InputFile  $clientPs1Patched `
        -OutputFile $clientExe `
        -Title      'GOP 클라이언트 인증서 설치' `
        -Description 'GOP rootCA 신뢰 저장소 등록기' `
        @clientArgs
    if (-not (Test-Path $clientExe)) { Fail 'client_install.exe 생성 실패' }
    Write-Host "  OK ($([math]::Round((Get-Item $clientExe).Length/1KB,1)) KB)" -ForegroundColor Green
} catch {
    Fail "client_install.exe 빌드 실패: $($_.Exception.Message)"
}

# ----- 4) 정리 --------------------------------------------------------------
Write-Step '4/4 완료'
Write-Host "  certs\server_install.exe" -ForegroundColor Green
Write-Host "  certs\client_install.exe" -ForegroundColor Green

if (-not $KeepTemp) {
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "  Temp 유지: $tempDir" -ForegroundColor DarkGray
}

Write-Host ''
Write-Host 'OK. 빌드 완료.' -ForegroundColor Green
exit 0
