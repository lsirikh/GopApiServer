<#
.SYNOPSIS
  git pull 후 무인 재배포 + DB 마이그레이션 자동 적용 (Windows / Docker Desktop).

.DESCRIPTION
  api-server 코드는 Dockerfile `COPY . .` 로 이미지에 구워진다(바인드마운트 아님).
  따라서 host 에서 `git pull` 만 하면 실행 중 컨테이너는 옛 코드라 새 마이그레이션이 반영되지
  않는다. 본 스크립트가 올바른 순서를 캡슐화한다:

    1) git pull --ff-only           (원격 최신 코드/마이그레이션 SQL 수신)
    2) docker compose build         (새 코드/SQL 을 이미지에 재굽기 — 필수)
    3) docker compose up -d --force-recreate
                                     (기동 lifespan 이 대기 마이그레이션을 멱등·fail-fast 로 자동 적용)
    4) healthy 대기 + 마이그레이션 적용 결과(schema_migrations) 출력

  전부 멱등 — 반복 실행 안전. 새 커밋이 없으면 아무것도 하지 않고 종료(-Force 로 강제).

.PARAMETER Service
  대상 compose 서비스명 (기본 api-server).
.PARAMETER Force
  새 커밋이 없어도 강제 rebuild + recreate.
.PARAMETER NoBuild
  rebuild 생략하고 recreate 만 (코드 변경 없이 재기동만 필요할 때).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File deploy\update.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File deploy\update.ps1 -Force
#>
[CmdletBinding()]
param(
    [string]$Service = "api-server",
    [switch]$Force,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
$Container = "pids-api-server"

# repo 루트로 이동 (스크립트 위치의 상위)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "==> repo: $root"

# 1) git pull ---------------------------------------------------------------
$before = (git rev-parse HEAD).Trim()
Write-Host "==> git pull --ff-only (현재 $($before.Substring(0,7)))"
git pull --ff-only
if ($LASTEXITCODE -ne 0) {
    throw "git pull 실패 — 로컬 미커밋 변경/충돌 가능. 'git status' 확인 후 재시도."
}
$after = (git rev-parse HEAD).Trim()

if (($before -eq $after) -and (-not $Force)) {
    Write-Host "==> 이미 최신 ($($after.Substring(0,7))). 변경 없음 — 종료. (강제 재배포: -Force)"
    exit 0
}

# 변경된 마이그레이션/스키마 파일 안내
if ($before -ne $after) {
    $changed = (git diff --name-only $before $after -- app/migrations app/utils/init_db.py) | Where-Object { $_ }
    if ($changed) {
        Write-Host "==> 마이그레이션/스키마 관련 변경 감지:"
        $changed | ForEach-Object { Write-Host "     $_" }
    } else {
        Write-Host "==> 코드 변경 감지 (마이그레이션 파일 변경은 없음)"
    }
}

# 2) build ------------------------------------------------------------------
if (-not $NoBuild) {
    Write-Host "==> docker compose build $Service"
    docker compose build $Service
    if ($LASTEXITCODE -ne 0) { throw "docker compose build 실패 (exit $LASTEXITCODE)" }
} else {
    Write-Host "==> build 생략 (-NoBuild)"
}

# 3) recreate (startup lifespan 이 idempotent 마이그레이션 자동 적용) -------
Write-Host "==> docker compose up -d --force-recreate $Service"
docker compose up -d --force-recreate $Service
if ($LASTEXITCODE -ne 0) { throw "docker compose up 실패 (exit $LASTEXITCODE)" }

# 4) healthy 대기 -----------------------------------------------------------
Write-Host "==> healthy 대기 (최대 120s)"
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 3
    $st = (docker inspect $Container --format '{{.State.Health.Status}}' 2>$null)
    if ($st -eq "healthy") { $ok = $true; break }
    if ($st -eq "unhealthy") { break }
}
if (-not $ok) {
    Write-Host "!! 컨테이너 healthy 실패 — 최근 로그 40줄:"
    docker logs $Container --tail 40
    Write-Host ""
    Write-Host "!! 마이그레이션 실패(fail-fast) 가능. 롤백:"
    Write-Host "     git reset --hard $before"
    Write-Host "     docker compose build $Service; docker compose up -d --force-recreate $Service"
    throw "배포 실패 — healthy 미도달"
}

# 마이그레이션 적용 결과 출력 (재기동 후 컨테이너 = 새 코드)
Write-Host "==> 마이그레이션 적용 상태:"
docker compose exec -T $Service python -m app.cli.migrate --status

Write-Host ""
Write-Host "==> 완료: $($before.Substring(0,7)) -> $($after.Substring(0,7)) (healthy)"
