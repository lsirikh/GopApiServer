<#
.SYNOPSIS
    GOP rootCA Inno Setup 인스톨러 빌드 스크립트
.DESCRIPTION
    - Inno Setup 6 (ISCC.exe) 자동 탐색
    - payload\rootCA.pem 존재/유효성 검증 (PEM 헤더 체크)
    - install_gop_rootca.iss 컴파일
    - 산출 EXE 의 SHA256 출력 (USB 배포 시 무결성 검증용)
.NOTES
    빌드 PC 요구사항:
      - Windows 10/11 + PowerShell 5.1
      - Inno Setup 6 (https://jrsoftware.org/isdl.php)
#>
[CmdletBinding()]
param(
    [string] $IsccPath
)

$ErrorActionPreference = 'Stop'
$ScriptRoot = $PSScriptRoot
$RepoRoot   = Resolve-Path (Join-Path $ScriptRoot '..')
$IssFile    = Join-Path $RepoRoot 'src\install_gop_rootca.iss'
$PayloadPem = Join-Path $RepoRoot 'payload\rootCA.pem'
$BuildDir   = Join-Path $RepoRoot 'build'

Write-Host '======================================================================'
Write-Host '  GOP rootCA Installer Build'
Write-Host '======================================================================'

# 1) ISCC.exe 탐색
if (-not $IsccPath) {
    $candidates = @(
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe'
    )
    $IsccPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $IsccPath -or -not (Test-Path $IsccPath)) {
    throw 'ISCC.exe 을(를) 찾을 수 없습니다. Inno Setup 6 설치 또는 -IsccPath 인자 지정.'
}
Write-Host "[OK]  ISCC : $IsccPath"

# 2) payload 검증
if (-not (Test-Path $PayloadPem)) {
    throw "payload\rootCA.pem 이 없습니다. mkcert -CAROOT 에서 복사하세요: $PayloadPem"
}
$pemHead = Get-Content -LiteralPath $PayloadPem -TotalCount 1
if ($pemHead -notmatch '-----BEGIN CERTIFICATE-----') {
    throw "rootCA.pem 헤더가 잘못되었습니다 (첫 줄: $pemHead). PEM 포맷이어야 합니다."
}
$pemSize = (Get-Item $PayloadPem).Length
Write-Host "[OK]  PEM  : $PayloadPem  ($pemSize bytes)"

# 3) build 디렉터리 준비
if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

# 4) ISCC 컴파일
Write-Host "`n[RUN] ISCC.exe `"$IssFile`""
$proc = Start-Process -FilePath $IsccPath -ArgumentList @("`"$IssFile`"") -Wait -PassThru -NoNewWindow
if ($proc.ExitCode -ne 0) {
    throw "ISCC 컴파일 실패 (ExitCode=$($proc.ExitCode))"
}

# 5) 산출물 확인 + SHA256
$exe = Get-ChildItem $BuildDir -Filter 'GOP-RootCA-Installer-v*.exe' |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exe) {
    throw "산출 EXE 없음: $BuildDir"
}
$sha = (Get-FileHash $exe.FullName -Algorithm SHA256).Hash
$size = '{0:N0}' -f $exe.Length

Write-Host '======================================================================'
Write-Host '  Build SUCCESS'
Write-Host '======================================================================'
Write-Host "  파일   : $($exe.FullName)"
Write-Host "  크기   : $size bytes"
Write-Host "  SHA256 : $sha"
Write-Host '======================================================================'

# 6) SHA 메모 파일
$shaMemoPath = Join-Path $BuildDir 'SHA256.txt'
"$sha  $($exe.Name)" | Out-File -LiteralPath $shaMemoPath -Encoding ASCII
Write-Host "  SHA256 메모: $shaMemoPath"
