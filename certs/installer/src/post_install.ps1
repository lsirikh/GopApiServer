<#
.SYNOPSIS
    GOP rootCA 를 LocalMachine\Root (신뢰할 수 있는 루트 인증 기관) 에 등록한다.
.PARAMETER CertPath
    rootCA.pem 의 절대 경로 (Inno Setup 이 {app}\rootCA.pem 전달)
.NOTES
    - 반드시 관리자 권한으로 실행 (Inno 의 PrivilegesRequired=admin 으로 보장)
    - 한국어 로그: %TEMP%\GOP-RootCA-Install.log
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $CertPath
)

$ErrorActionPreference = 'Stop'
$LogPath = Join-Path $env:TEMP 'GOP-RootCA-Install.log'
$StoreName = 'Root'                # 신뢰할 수 있는 루트 인증 기관
$StoreScope = 'LocalMachine'       # 컴퓨터 전체

function Write-Log {
    param([string] $Level, [string] $Msg)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$ts] [$Level] $Msg"
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

try {
    '=' * 78 | Out-File -LiteralPath $LogPath -Append -Encoding UTF8
    Write-Log 'INFO'  "GOP rootCA 설치 시작 (PID=$PID, User=$env:USERNAME)"
    Write-Log 'INFO'  "CertPath = $CertPath"

    # 1) 파일 존재 확인
    if (-not (Test-Path -LiteralPath $CertPath)) {
        throw "인증서 파일을 찾을 수 없습니다: $CertPath"
    }

    # 2) PEM 로드 (Thumbprint 추출)
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
    $cert.Import($CertPath)
    $thumb   = $cert.Thumbprint
    $subject = $cert.Subject
    $notAfter = $cert.NotAfter.ToString('yyyy-MM-dd')
    Write-Log 'INFO' "Subject    = $subject"
    Write-Log 'INFO' "Thumbprint = $thumb"
    Write-Log 'INFO' "NotAfter   = $notAfter"

    # 3) 중복 등록 검사
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store($StoreName, $StoreScope)
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
    $existing = $store.Certificates | Where-Object { $_.Thumbprint -eq $thumb }
    $store.Close()

    if ($existing) {
        Write-Log 'WARN' "동일 Thumbprint 인증서가 이미 LocalMachine\Root 에 존재합니다. SKIP."
        Write-Log 'INFO' "GOP rootCA 설치 종료 (Result=ALREADY_INSTALLED)"
        exit 0
    }

    # 4) certutil -addstore -f Root <pem>
    Write-Log 'INFO' 'certutil -addstore -f Root <pem> 실행'
    $proc = Start-Process -FilePath 'certutil.exe' `
        -ArgumentList @('-addstore', '-f', $StoreName, "`"$CertPath`"") `
        -Wait -NoNewWindow -PassThru `
        -RedirectStandardOutput "$env:TEMP\gop-certutil-out.txt" `
        -RedirectStandardError  "$env:TEMP\gop-certutil-err.txt"

    $stdout = Get-Content "$env:TEMP\gop-certutil-out.txt" -Raw -ErrorAction SilentlyContinue
    $stderr = Get-Content "$env:TEMP\gop-certutil-err.txt" -Raw -ErrorAction SilentlyContinue
    if ($stdout) { Write-Log 'OUT' $stdout.Trim() }
    if ($stderr) { Write-Log 'ERR' $stderr.Trim() }

    if ($proc.ExitCode -ne 0) {
        throw "certutil 실패: ExitCode=$($proc.ExitCode)"
    }

    # 5) 등록 후 재검증
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
    $verify = $store.Certificates | Where-Object { $_.Thumbprint -eq $thumb }
    $store.Close()

    if (-not $verify) {
        throw '등록 직후 재조회 실패 — LocalMachine\Root 에서 인증서를 찾을 수 없습니다.'
    }

    Write-Log 'INFO' '등록 성공 — 신뢰할 수 있는 루트 인증 기관에 정상 반영됨'
    Write-Log 'INFO' "GOP rootCA 설치 종료 (Result=SUCCESS)"
    exit 0
}
catch {
    Write-Log 'FATAL' $_.Exception.Message
    Write-Log 'INFO'  "GOP rootCA 설치 종료 (Result=FAILED)"
    exit 1
}
finally {
    Remove-Item "$env:TEMP\gop-certutil-out.txt" -ErrorAction SilentlyContinue
    Remove-Item "$env:TEMP\gop-certutil-err.txt" -ErrorAction SilentlyContinue
}
