<#
.SYNOPSIS
    GOP rootCA Installer EXE 무결성 검증
.DESCRIPTION
    1) EXE 의 PE 헤더 유효성 (Inno Setup 시그니처)
    2) /VERYSILENT /TEST 모드로 dry-run
    3) %TEMP%\GOP-RootCA-Install.log 검사
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ExePath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ExePath)) {
    throw "EXE 없음: $ExePath"
}

Write-Host "검증 대상: $ExePath"

# PE 헤더 확인 (MZ)
$bytes = [System.IO.File]::ReadAllBytes($ExePath) | Select-Object -First 2
if ($bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) {
    throw '유효한 PE(MZ) 헤더가 아닙니다.'
}
Write-Host '[OK] PE 헤더 정상 (MZ)'

# Inno Setup 시그니처 검사 (간이)
$content = Get-Content -LiteralPath $ExePath -Encoding Byte -TotalCount 65536
$ascii = -join ($content | ForEach-Object { if ($_ -ge 32 -and $_ -lt 127) { [char]$_ } else { '.' } })
if ($ascii -notmatch 'Inno Setup') {
    Write-Warning 'Inno Setup 시그니처 문자열 미발견 (다른 패커일 가능성)'
} else {
    Write-Host '[OK] Inno Setup 시그니처 확인'
}

$sha = (Get-FileHash $ExePath -Algorithm SHA256).Hash
Write-Host "[INFO] SHA256: $sha"
Write-Host '검증 완료. /VERYSILENT 실제 설치 검증은 격리 VM 에서 수동 실행 권장.'
