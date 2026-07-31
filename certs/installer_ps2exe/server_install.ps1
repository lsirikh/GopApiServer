#Requires -RunAsAdministrator
<#
.SYNOPSIS
    GOP API Server Certificate Setup
.DESCRIPTION
    mkcert 기반 로컬 CA 등록 + server.crt/server.key 발급 + Docker 재시작 안내.
    서버 PC에서 1회 실행. 빌드 시 PS2EXE 로 EXE 변환.
.NOTES
    Author : GOP Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    # v6.0-cert_installer_fix / v6.0-installer_ps2exe_path_fix:
    # CertDir 은 본문에서 실행 방식(PS1 직접 실행 vs PS2EXE EXE)을 감지해 계산.
    # bootstrap.ps1 이 -CertDir 을 명시 전달하면 그 값을 최우선 사용(권장, 경로 불일치 원천 차단).
    [string]$CertDir        = '',
    [string]$MkcertVersion  = 'v1.4.4',
    [string[]]$ExtraSans    = @(),
    # v6.0-installer_ps2exe_path_fix (2026-07-07): 무인 자동 실행 모드.
    # 지정 시 대화형 프롬프트(추가 SAN 입력 / 종료 대기 Read-Host) 전부 스킵.
    # bootstrap.ps1 이 이 스위치를 넘겨 EXE 가 중간에 멈추지 않게 한다.
    [switch]$NonInteractive
)

# ----- 환경 설정 ------------------------------------------------------------
$ErrorActionPreference = 'Stop'
$script:LogPath = Join-Path $env:TEMP 'GOP-Server-Install.log'

# ----- 스크립트/EXE 실제 위치 획득 (v6.0-installer_ps2exe_path_fix) --------
# ★ 근본 원인 규명 (2026-07-07 실측):
#   PS2EXE 로 빌드된 EXE 실행 시 아래 변수가 전부 빈 문자열이 된다.
#     $PSScriptRoot                    = ''
#     $MyInvocation.MyCommand.Path      = ''
#     $PSCommandPath                    = ''
#     $MyInvocation.MyCommand.Definition = (스크립트 소스코드 — 경로 아님)
#   유일하게 신뢰 가능한 값:
#     [Diagnostics.Process]::GetCurrentProcess().MainModule.FileName = EXE 절대경로
#   → 이전엔 else 분기가 빈 문자열을 반환해 CertDir 이 ''(빈값)이 되고,
#     Join-Path '' 'server.crt' 가 실패/CWD 오생성 → bootstrap 이 인증서를 못 찾는 버그.
$script:ScriptRoot =
    if ($PSScriptRoot) {
        $PSScriptRoot                                      # PS1 직접 실행 (개발 PC)
    } elseif ($MyInvocation.MyCommand.Path) {
        Split-Path -Parent $MyInvocation.MyCommand.Path    # 일부 호스트
    } else {
        # PS2EXE 빌드된 EXE: MainModule.FileName 만 EXE 절대경로를 준다.
        try {
            Split-Path -Parent ([System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName)
        } catch {
            (Get-Location).Path                            # 최후 안전망 (CWD)
        }
    }

# ----- CertDir 기본값 (본문 계산) ------------------------------------------
# 우선순위: -CertDir 명시값 > 실행 방식 감지.
#   (A) PS1 직접 실행: $ScriptRoot = <repo>\certs\installer_ps2exe → CertDir = 상위(<repo>\certs)
#   (B) PS2EXE EXE:    $ScriptRoot = <repo>\certs (EXE 위치)       → CertDir = 자체
if (-not $CertDir) {
    if ($script:ScriptRoot -like '*installer_ps2exe*') {
        $CertDir = Split-Path -Parent $script:ScriptRoot   # (A) PS1 직접 실행
    } else {
        $CertDir = $script:ScriptRoot                       # (B) EXE = certs 폴더 안
    }
}
# 방어: 그래도 빈 값이면 CWD 로 폴백 (인증서가 '' 경로에 안 생기도록)
if ([string]::IsNullOrWhiteSpace($CertDir)) {
    $CertDir = (Get-Location).Path
}

# 콘솔 한글 깨짐 방지
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding           = [System.Text.Encoding]::UTF8
    chcp 65001 | Out-Null
} catch { }

# ----- 헬퍼 함수 ------------------------------------------------------------
function Write-Log {
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet('INFO','WARN','ERROR','OK','STEP')][string]$Level = 'INFO'
    )
    $ts   = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts][$Level] $Message"

    $color = switch ($Level) {
        'INFO'  { 'Gray'    }
        'WARN'  { 'Yellow'  }
        'ERROR' { 'Red'     }
        'OK'    { 'Green'   }
        'STEP'  { 'Cyan'    }
    }
    Write-Host $line -ForegroundColor $color
    try { Add-Content -Path $script:LogPath -Value $line -Encoding UTF8 } catch { }
}

function Write-Banner {
    param([string]$Title)
    $bar = '=' * 72
    Write-Host ''
    Write-Host $bar  -ForegroundColor Cyan
    Write-Host (' ' + $Title) -ForegroundColor White
    Write-Host $bar  -ForegroundColor Cyan
    Write-Host ''
}

function Test-IsAdmin {
    $id  = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $pri = New-Object System.Security.Principal.WindowsPrincipal($id)
    return $pri.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-Mkcert {
    # 1) 스크립트와 같은 폴더
    $local = Join-Path $script:ScriptRoot 'mkcert.exe'
    if (Test-Path $local) { return (Resolve-Path $local).Path }

    # 2) PATH 검색
    $cmd = Get-Command 'mkcert.exe' -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # 3) 자주 쓰는 위치
    foreach ($p in @(
        "$env:ProgramFiles\mkcert\mkcert.exe",
        "$env:ProgramData\chocolatey\bin\mkcert.exe",
        "$env:USERPROFILE\scoop\shims\mkcert.exe"
    )) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Install-Mkcert {
    param([string]$Version = 'v1.4.4')

    Write-Log "mkcert.exe 다운로드 시작 ($Version)" 'STEP'
    $arch = if ([Environment]::Is64BitOperatingSystem) { 'amd64' } else { '386' }
    $url  = "https://github.com/FiloSottile/mkcert/releases/download/$Version/mkcert-$Version-windows-$arch.exe"
    $dst  = Join-Path $script:ScriptRoot 'mkcert.exe'

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $dst -UseBasicParsing -TimeoutSec 120
    } catch {
        Write-Log "mkcert 다운로드 실패: $($_.Exception.Message)" 'ERROR'
        Write-Log "폐쇄망인 경우 mkcert.exe 를 스크립트와 같은 폴더에 동봉하세요." 'WARN'
        throw
    }

    if (-not (Test-Path $dst)) { throw "mkcert.exe 다운로드 결과 파일이 없습니다: $dst" }
    Write-Log "mkcert.exe 다운로드 완료 -> $dst" 'OK'
    return $dst
}

function Invoke-Mkcert {
    param(
        [Parameter(Mandatory)][string]$ExePath,
        [Parameter(Mandatory)][string[]]$Args
    )
    Write-Log "mkcert 실행: $($Args -join ' ')" 'INFO'
    $p = Start-Process -FilePath $ExePath -ArgumentList $Args -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput "$env:TEMP\mkcert_stdout.txt" `
            -RedirectStandardError  "$env:TEMP\mkcert_stderr.txt"
    $out = (Get-Content "$env:TEMP\mkcert_stdout.txt" -Raw -ErrorAction SilentlyContinue)
    $err = (Get-Content "$env:TEMP\mkcert_stderr.txt" -Raw -ErrorAction SilentlyContinue)
    if ($out) { Write-Log $out.Trim() 'INFO' }
    if ($err) { Write-Log $err.Trim() 'WARN' }
    if ($p.ExitCode -ne 0) {
        throw "mkcert 종료 코드 $($p.ExitCode)"
    }
}

function Read-AdditionalIPs {
    Write-Host ''
    Write-Host '추가로 SAN 에 포함할 IP/도메인을 콤마로 입력하세요.' -ForegroundColor Yellow
    Write-Host '예) 192.168.0.50, gop-server.local'                  -ForegroundColor DarkGray
    Write-Host '없으면 그냥 Enter:'                                  -ForegroundColor DarkGray
    $raw = Read-Host '추가 SAN'
    if ([string]::IsNullOrWhiteSpace($raw)) { return @() }
    return ($raw -split '[,;\s]+' | Where-Object { $_ -ne '' })
}

# ----- 메인 로직 ------------------------------------------------------------
try {
    Write-Banner 'GOP 서버 인증서 설정 (mkcert 기반)'
    Write-Log "로그 파일: $script:LogPath" 'INFO'
    Write-Log "스크립트 위치: $script:ScriptRoot" 'INFO'

    if (-not (Test-IsAdmin)) {
        throw '관리자 권한이 필요합니다. 우클릭 > 관리자 권한으로 실행 하세요.'
    }

    # certs 폴더 보장
    if (-not (Test-Path $CertDir)) {
        New-Item -ItemType Directory -Path $CertDir -Force | Out-Null
        Write-Log "certs 폴더 생성: $CertDir" 'OK'
    }

    # 1) mkcert 확보
    Write-Banner '[1/5] mkcert.exe 확인'
    $mkcert = Find-Mkcert
    if (-not $mkcert) {
        Write-Log 'mkcert.exe 를 찾을 수 없습니다. 자동 다운로드를 시도합니다.' 'WARN'
        $mkcert = Install-Mkcert -Version $MkcertVersion
    } else {
        Write-Log "mkcert 발견: $mkcert" 'OK'
    }

    # 2) 로컬 CA 설치
    Write-Banner '[2/5] 로컬 CA 신뢰 저장소 등록 (mkcert -install)'
    Invoke-Mkcert -ExePath $mkcert -Args @('-install')
    Write-Log '로컬 CA 등록 완료' 'OK'

    # 3) SAN 입력 (v6.0-installer_ps2exe_path_fix: NonInteractive 면 프롬프트 스킵)
    Write-Banner '[3/5] 추가 SAN 입력'
    $userSans =
        if ($ExtraSans -and $ExtraSans.Count -gt 0) { $ExtraSans }
        elseif ($NonInteractive) {
            Write-Log '무인 모드(NonInteractive): 추가 SAN 입력 스킵, 기본 SAN 만 사용' 'INFO'
            @()
        }
        else { Read-AdditionalIPs }
    $defaultSans = @('localhost','127.0.0.1','::1','host.docker.internal')
    # v6.3-cert_san_expand (2026-07-31): 배포 고정 SAN — TLS 인증서에는 IP 와일드카드가 없어 서브넷 호스트를 열거한다.
    #   공인 IP(포트포워딩 대상) + 내부 서브넷 192.168.1.0/24 · 192.168.202.0/24 전체(각 1~254).
    #   → 서브넷 내 어느 IP로 서버가 뜨거나 접속하든 인증서 재발급 없이 신뢰된다.
    $publicSans = @('123.141.236.253','123.141.236.248')
    $subnetSans = foreach ($i in 1..254) { "192.168.1.$i"; "192.168.202.$i" }
    $allSans = ($defaultSans + $publicSans + $subnetSans + $userSans) | Where-Object { $_ } | Select-Object -Unique
    Write-Log ("SAN $($allSans.Count)개 발급 (기본+공인2+내부서브넷 192.168.1.0/24·192.168.202.0/24)") 'INFO'

    # 4) 인증서 발급
    Write-Banner '[4/5] server.crt / server.key 발급'
    $crt = Join-Path $CertDir 'server.crt'
    $key = Join-Path $CertDir 'server.key'

    # mkcert 인자 구성: -cert-file <crt> -key-file <key> <san1> <san2> ...
    $args = @('-cert-file', $crt, '-key-file', $key) + $allSans
    Invoke-Mkcert -ExePath $mkcert -Args $args

    if (-not (Test-Path $crt) -or -not (Test-Path $key)) {
        throw '인증서 파일이 생성되지 않았습니다.'
    }
    Write-Log "발급 완료" 'OK'
    Write-Log "  CRT: $crt" 'OK'
    Write-Log "  KEY: $key" 'OK'

    # 5) rootCA 위치 안내
    Write-Banner '[5/5] rootCA.pem 위치 및 클라이언트 배포 안내'
    $caRootOut = & $mkcert -CAROOT 2>&1
    $caRoot    = ($caRootOut | Select-Object -First 1).ToString().Trim()
    $rootCa    = Join-Path $caRoot 'rootCA.pem'

    Write-Log "rootCA 디렉터리: $caRoot" 'INFO'
    Write-Log "rootCA.pem    : $rootCa"  'INFO'

    if (Test-Path $rootCa) {
        $copyDst = Join-Path $CertDir 'rootCA.pem'
        Copy-Item -Path $rootCa -Destination $copyDst -Force
        Write-Log "rootCA.pem 을 certs 폴더로 복사했습니다: $copyDst" 'OK'
        Write-Log "이 파일을 client_install.exe 와 함께 클라이언트 PC 로 전달하세요." 'INFO'
    } else {
        Write-Log "rootCA.pem 을 찾을 수 없습니다: $rootCa" 'WARN'
    }

    Write-Banner '완료'
    Write-Host '다음 단계:' -ForegroundColor Yellow
    Write-Host '  1) Docker 컨테이너 재시작' -ForegroundColor White
    Write-Host '       docker compose up -d --force-recreate api-server' -ForegroundColor DarkCyan
    Write-Host '  2) 클라이언트 PC 에서 client_install.exe 실행' -ForegroundColor White
    Write-Host "  3) 로그 확인: $script:LogPath" -ForegroundColor DarkGray
    Write-Host ''
    # v6.0-installer_ps2exe_path_fix: 무인 모드면 종료 대기 스킵 (bootstrap 자동 흐름 유지)
    if (-not $NonInteractive) {
        Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
        [void](Read-Host)
    }
    exit 0
}
catch {
    Write-Log "치명적 오류: $($_.Exception.Message)" 'ERROR'
    Write-Log "위치: $($_.InvocationInfo.PositionMessage)" 'ERROR'
    Write-Host ''
    Write-Host "설치 실패. 로그: $script:LogPath" -ForegroundColor Red
    if (-not $NonInteractive) {
        Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
        [void](Read-Host)
    }
    exit 1
}
