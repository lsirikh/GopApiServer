#Requires -RunAsAdministrator
<#
.SYNOPSIS
    GOP API Client - rootCA 신뢰 저장소 등록
.DESCRIPTION
    server_install.exe 가 발급한 rootCA.pem 을 Windows 'Root' 저장소에 등록한다.
    배포 방식 1: 스크립트 내부에 Base64 임베드 (단일 EXE)
    배포 방식 2: 스크립트와 같은 폴더의 rootCA.pem 사용 (fallback)
.NOTES
    Author : GOP Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [string]$RootCaPath = $null,
    [switch]$Force
)

# ----- 환경 설정 ------------------------------------------------------------
$ErrorActionPreference = 'Stop'
$script:LogPath    = Join-Path $env:TEMP 'GOP-Client-Install.log'
$script:ScriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding           = [System.Text.Encoding]::UTF8
    chcp 65001 | Out-Null
} catch { }

# ---------------------------------------------------------------------------
# rootCA.pem Base64 임베드 영역
# build_install_exe.ps1 이 아래 placeholder 를 실제 Base64 로 치환한다.
# 치환 후에도 스크립트는 그대로 PS 로도 동작해야 한다.
# ---------------------------------------------------------------------------
$EmbeddedRootCaBase64 = 'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUVnVENDQXVtZ0F3SUJBZ0lRWUFwMTBpU3NDNGFLUUdwUVpjRnQvakFOQmdrcWhraUc5dzBCQVFzRkFEQloKTVI0d0hBWURWUVFLRXhWdGEyTmxjblFnWkdWMlpXeHZjRzFsYm5RZ1EwRXhGekFWQmdOVkJBc01EbWRvYkdWbApYR2RvUUdkb2JHVmxNUjR3SEFZRFZRUUREQlZ0YTJObGNuUWdaMmhzWldWY1oyaEFaMmhzWldVd0hoY05Nall3Ck5qSTFNREV6TWpJNVdoY05Nell3TmpJMU1ERXpNakk1V2pCWk1SNHdIQVlEVlFRS0V4VnRhMk5sY25RZ1pHVjIKWld4dmNHMWxiblFnUTBFeEZ6QVZCZ05WQkFzTURtZG9iR1ZsWEdkb1FHZG9iR1ZsTVI0d0hBWURWUVFEREJWdAphMk5sY25RZ1oyaHNaV1ZjWjJoQVoyaHNaV1V3Z2dHaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQmp3QXdnZ0dLCkFvSUJnUURjd1lFTFVWZVVPd0hEbmVVakFIbEIxYlRQR0VQWm40Z0Eya0NHK2UwV3czV1NJOWJiWGpaaTMrckEKSEVPejVXSmpJK0tHUEFzLzFselhTQzZCZnd6aXlhWk9pZ2JRUDFwTXJ4ZEphSVQrRzU1bGVSeEJia1ovOEMrZgplZUZtNkg4QkZmbElYcTFJRzRqbE5ZUUxEWFRvMGgwZ2dIbXpxVUtsNjZUTWVEVWY1eEpwYVZQbHgzTWFjMFgxCjRleDMrU3hyZ1BVYnJSb3k5Uy9CMWlxdUlhTVl1dWhrUzRuR0dVeWxNcCt0ZDd3aURxbDZub1huWmlYWVVDTkEKUkFxWXkzSkhYWWxHbCszS0ZNOTgwK3Q0Q0xjaVdVVCthSlVrc1FKUjNxZ3JHeUVFYUJXNTYzbDBGczNOUFUzcwpRdkxRaVo4SmlkN2VNN3BiRVFzV0VLb0tEa3BROUY4N2xxQmdDKzduZzhEa0w2Ky9abVA2T2NmcWJlekZRMjBGCjIyY3E2WDJ1QkFreEtsaUREZlN3YjRpbTU1NlJGQzZOY2cwMXBwQ21nVmlkRDZhVmtLQ0cySnFqSjhBVnM4OFcKam5BYTBac0laMDFsWTFXWVpYTVJmTnNzTHlJd3hHL0cySDF1RFU0T2IvT2M0dHVxMTB2RUQ5TXUybjdqNFh4Ngp5OWlsWmJzQ0F3RUFBYU5GTUVNd0RnWURWUjBQQVFIL0JBUURBZ0lFTUJJR0ExVWRFd0VCL3dRSU1BWUJBZjhDCkFRQXdIUVlEVlIwT0JCWUVGRTlCUVBBZnh0djBabUREU3VYRFNSdWpPcUk1TUEwR0NTcUdTSWIzRFFFQkN3VUEKQTRJQmdRQWtFRVpsQUdSQ0tLdGVlVWJnYTZSMUErV01ZVkNhSDhJQzZiVGw2VDJBalZuNGMxMVFQenNlbGk3VgpsVk9Vajl6VUVHbFZkZVZ0akNKTUVWYUU1VktTbDNxY2tSQ3B6Y2hCOUthM0lzcGc0Vm9ieVZ1UTQ2d3U0L2hUCjZCM05SUVBSZEE3MDVDT2FndkVUbWp3YzBQVnZnWWxqYytIL0tQNXhwVXJwMklCRFJVN1Y0MExtL3dYUVUrdEUKSktPNWNXQk55QnJzZVR6SHNTQ3BjSVEzRFB2Z0JFdk8rMG9NVExvMTFoWXE0OGhXWXJoWnFOQ3ZCRXBpZU5uWQpDdGhYd1FVNEZZL3JSVWhnbWxtdmE3SGFKTkVGd1VkNHA4ZVdJa2tTeU0wNzVyVGlnQ2Z0THhLelovR1hyOHdTCmRNbWdydEN3Y1ltNEpZRDA2MG5EZEFwWHJ4aGwwdmRqMEhLRzM4S21aNCthYTFoWFU0M01xTk9SOFBxRTFEb2QKU2o4WDhYcE9EU1pmQXMwVzM5VWFCdGVuWTNkZWRUSGozRmc0cmtpTTVXV1FOcC9GTEFjZ1F0ejBRU3RTU0UyZwppemRQMFRkSkljT3M3dzNsdjUxUWt5WDMrWnJtZTR1ZUFRZzZrOWNNSzhtRkZFUm0xdWFiSFRsdzlyaS80U1RuCjhGc045ajA9Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K'

# ----- 헬퍼 함수 ------------------------------------------------------------
function Write-Log {
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet('INFO','WARN','ERROR','OK','STEP')][string]$Level = 'INFO'
    )
    $ts   = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts][$Level] $Message"
    $color = switch ($Level) {
        'INFO'  { 'Gray'   }
        'WARN'  { 'Yellow' }
        'ERROR' { 'Red'    }
        'OK'    { 'Green'  }
        'STEP'  { 'Cyan'   }
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

function Get-RootCaBytes {
    param([string]$ExplicitPath)

    # 1) 명시적 경로
    if ($ExplicitPath -and (Test-Path $ExplicitPath)) {
        Write-Log "rootCA 파일 사용 (명시 경로): $ExplicitPath" 'INFO'
        return [System.IO.File]::ReadAllBytes($ExplicitPath)
    }

    # 2) 임베드 Base64
    if ($EmbeddedRootCaBase64 -and
        $EmbeddedRootCaBase64 -ne '__ROOT_CA_BASE64_PLACEHOLDER__' -and
        $EmbeddedRootCaBase64.Length -gt 100) {
        Write-Log "rootCA 사용: 스크립트 내부 임베드 (Base64, $($EmbeddedRootCaBase64.Length) chars)" 'INFO'
        try {
            $clean = $EmbeddedRootCaBase64 -replace '\s',''
            return [Convert]::FromBase64String($clean)
        } catch {
            Write-Log "임베드 Base64 디코딩 실패: $($_.Exception.Message)" 'WARN'
        }
    }

    # 3) 같은 폴더의 rootCA.pem
    $sideCar = Join-Path $script:ScriptRoot 'rootCA.pem'
    if (Test-Path $sideCar) {
        Write-Log "rootCA 파일 사용 (동봉): $sideCar" 'INFO'
        return [System.IO.File]::ReadAllBytes($sideCar)
    }

    throw 'rootCA.pem 을 찾을 수 없습니다. 다음 중 하나가 필요합니다: (1) -RootCaPath 인자, (2) 임베드된 Base64, (3) 스크립트와 같은 폴더의 rootCA.pem'
}

function ConvertTo-X509Certificate {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    # PEM 또는 DER 모두 처리
    try {
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2(,$Bytes)
        return $cert
    } catch {
        # PEM 텍스트일 수 있음 -> Base64 본문 추출 후 DER 로 변환
        $text  = [System.Text.Encoding]::ASCII.GetString($Bytes)
        $b64   = ($text -replace '-----BEGIN [^-]+-----','' -replace '-----END [^-]+-----','' -replace '\s','')
        $der   = [Convert]::FromBase64String($b64)
        return New-Object System.Security.Cryptography.X509Certificates.X509Certificate2(,$der)
    }
}

function Test-CertInStore {
    param(
        [Parameter(Mandatory)][System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert
    )
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root','LocalMachine')
    try {
        $store.Open('ReadOnly')
        $existing = $store.Certificates | Where-Object { $_.Thumbprint -eq $Cert.Thumbprint }
        return [bool]$existing
    } finally {
        $store.Close()
    }
}

function Install-RootCert {
    param(
        [Parameter(Mandatory)][System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert
    )
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root','LocalMachine')
    try {
        $store.Open('ReadWrite')
        $store.Add($Cert)
        Write-Log '인증서를 LocalMachine\Root 저장소에 추가했습니다.' 'OK'
    } finally {
        $store.Close()
    }
}

function Confirm-Installed {
    param(
        [Parameter(Mandatory)][System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert
    )
    Write-Log '설치 검증 중...' 'STEP'
    $found = Test-CertInStore -Cert $Cert
    if ($found) {
        Write-Log ("검증 OK - Thumbprint: " + $Cert.Thumbprint) 'OK'
        Write-Log ("Subject  : " + $Cert.Subject)                'INFO'
        Write-Log ("Issuer   : " + $Cert.Issuer)                 'INFO'
        Write-Log ("Valid To : " + $Cert.NotAfter)               'INFO'
        return $true
    }
    return $false
}

# ----- 메인 로직 ------------------------------------------------------------
try {
    Write-Banner 'GOP 클라이언트 인증서 설치 (rootCA -> Windows 신뢰 저장소)'
    Write-Log "로그 파일: $script:LogPath" 'INFO'

    if (-not (Test-IsAdmin)) {
        throw '관리자 권한이 필요합니다. 우클릭 > 관리자 권한으로 실행 하세요.'
    }

    Write-Banner '[1/4] rootCA.pem 로드'
    $bytes = Get-RootCaBytes -ExplicitPath $RootCaPath
    Write-Log ("rootCA 바이트 수: " + $bytes.Length) 'INFO'

    Write-Banner '[2/4] X509 인증서 객체 생성'
    $cert = ConvertTo-X509Certificate -Bytes $bytes
    Write-Log ("Subject    : " + $cert.Subject)    'INFO'
    Write-Log ("Thumbprint : " + $cert.Thumbprint) 'INFO'

    Write-Banner '[3/4] 신뢰 저장소 등록 (멱등)'
    if ((Test-CertInStore -Cert $cert) -and -not $Force) {
        Write-Log '이미 신뢰 저장소에 등록되어 있습니다. (skip)' 'OK'
    } else {
        Install-RootCert -Cert $cert
    }

    Write-Banner '[4/4] 검증'
    $ok = Confirm-Installed -Cert $cert
    if (-not $ok) { throw '신뢰 저장소에서 인증서를 다시 찾지 못했습니다.' }

    # certutil 보조 검증 (있으면)
    try {
        $certutil = Get-Command certutil.exe -ErrorAction SilentlyContinue
        if ($certutil) {
            $matches = & certutil.exe -store Root 2>&1 | Select-String -Pattern $cert.Thumbprint -SimpleMatch
            if ($matches) {
                Write-Log 'certutil 보조 검증 OK' 'OK'
            } else {
                Write-Log 'certutil 출력에서 Thumbprint 를 찾지 못했습니다 (참고용)' 'WARN'
            }
        }
    } catch {
        Write-Log "certutil 보조 검증 스킵: $($_.Exception.Message)" 'WARN'
    }

    Write-Banner '완료'
    Write-Host '브라우저/앱을 재시작하면 HTTPS 경고 없이 GOP API 서버에 접속할 수 있습니다.' -ForegroundColor Yellow
    Write-Host ''
    Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
    [void](Read-Host)
    exit 0
}
catch {
    Write-Log "치명적 오류: $($_.Exception.Message)" 'ERROR'
    Write-Log "위치: $($_.InvocationInfo.PositionMessage)" 'ERROR'
    Write-Host ''
    Write-Host "설치 실패. 로그: $script:LogPath" -ForegroundColor Red
    Write-Host '엔터를 눌러 종료...' -ForegroundColor DarkGray
    [void](Read-Host)
    exit 1
}
