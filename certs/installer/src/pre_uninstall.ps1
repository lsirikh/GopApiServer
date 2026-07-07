<#
.SYNOPSIS
    GOP rootCA 신뢰 제거 (LocalMachine\Root)
.PARAMETER CertPath
    제거 대상 식별용 rootCA.pem (Thumbprint 추출)
.NOTES
    제어판 '프로그램 추가/제거' → GOP rootCA Installer → 제거 선택 시 호출.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $CertPath
)

$ErrorActionPreference = 'Continue'
$LogPath = Join-Path $env:TEMP 'GOP-RootCA-Uninstall.log'
$StoreName = 'Root'
$StoreScope = 'LocalMachine'

function Write-Log {
    param([string] $Level, [string] $Msg)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] [$Level] $Msg"
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

try {
    '=' * 78 | Out-File -LiteralPath $LogPath -Append -Encoding UTF8
    Write-Log 'INFO' "GOP rootCA 제거 시작 (User=$env:USERNAME)"

    if (-not (Test-Path -LiteralPath $CertPath)) {
        Write-Log 'WARN' "CertPath 없음 — Thumbprint 식별 불가, 수동 제거 필요"
        exit 0
    }

    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
    $cert.Import($CertPath)
    $thumb = $cert.Thumbprint
    Write-Log 'INFO' "Thumbprint = $thumb"

    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($StoreName, $StoreScope)
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    $target = $store.Certificates | Where-Object { $_.Thumbprint -eq $thumb }

    if ($target) {
        foreach ($c in $target) { $store.Remove($c) }
        Write-Log 'INFO' "$($target.Count) 개 인증서 제거 완료"
    } else {
        Write-Log 'WARN' '해당 Thumbprint 인증서가 저장소에 없음 — 이미 제거되었거나 미설치'
    }
    $store.Close()

    Write-Log 'INFO' 'GOP rootCA 제거 종료 (Result=SUCCESS)'
    exit 0
}
catch {
    Write-Log 'ERR' $_.Exception.Message
    Write-Log 'INFO' 'GOP rootCA 제거 종료 (Result=FAILED)'
    exit 1
}
