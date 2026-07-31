<#
.SYNOPSIS
  GOP API Server offline one-click installer (air-gapped upgrade, DB/data preserving).

.DESCRIPTION
  State machine: Phase 0 preflight (no changes) -> Phase 1 backup+integrity gate ->
  [POINT OF NO RETURN] -> Phase 2 apply (down/load/sync/up) -> Phase 3 verify.
  Any failure before the point-of-no-return aborts with ZERO changes. Any failure after it
  triggers unattended 3-layer rollback (images/config/data) to the pre-upgrade state.

.PARAMETER BundleDir   Directory with images/*.tar + payload/ + bundle.json (default: script dir).
.PARAMETER RepoDir     Target compose project dir (default: auto-detected from the running stack).
.PARAMETER Silent      Unattended; no prompts.
.PARAMETER Rollback    Standalone rollback from the latest (or -ManifestPath) backup manifest.
.PARAMETER Rehearse    Isolated sandbox rehearsal (clones real volume; real project untouched).
.PARAMETER ManifestPath  Specific manifest.json for -Rollback.

.EXAMPLE  .\install.ps1 -Rehearse          # prove rollback at home before the trip
.EXAMPLE  .\install.ps1 -Silent            # unattended upgrade on site
.EXAMPLE  .\install.ps1 -Rollback          # manual rollback using latest backup
#>
[CmdletBinding()]
param(
    [string]$BundleDir = $PSScriptRoot,
    [string]$RepoDir,
    [switch]$Silent,
    [switch]$Rollback,
    [switch]$Rehearse,
    [string]$ManifestPath
)

$ErrorActionPreference = 'Stop'
$libDir = Join-Path $PSScriptRoot 'lib'
foreach ($f in @('common', 'volume_snapshot', 'detect_volume', 'preflight', 'backup', 'sync_files', 'apply_stack', 'verify', 'rollback', 'rehearse')) {
    . (Join-Path $libDir "$f.ps1")
}

# --- logging ---
$logRoot = if ($RepoDir) { $RepoDir } else { $BundleDir }
$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
Set-LogFile (Join-Path $logRoot "install_$stamp.log")

function Resolve-BundleImagesTar { param([string]$Dir) return (Get-ChildItem -Path (Join-Path $Dir 'images') -Filter '*.tar' -ErrorAction SilentlyContinue | Select-Object -First 1).FullName }
function Read-BundleVersion { param([string]$Dir) $b = Join-Path $Dir 'bundle.json'; if (Test-Path $b) { return (Get-Content $b -Raw | ConvertFrom-Json).to_version } return 'unknown' }
function Find-LatestManifest { param([string]$Repo) return (Get-ChildItem -Path (Join-Path $Repo 'offline-installer-backups') -Recurse -Filter 'manifest.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName }

try {
    # ===== MODE: standalone rollback =====
    if ($Rollback) {
        Write-Log "MODE: standalone rollback" STEP
        $mp = if ($ManifestPath) { $ManifestPath } elseif ($RepoDir) { Find-LatestManifest $RepoDir } else { $null }
        if (-not $mp) { throw "no manifest found; pass -ManifestPath and/or -RepoDir" }
        Write-Log "using manifest: $mp" INFO
        $ok = Invoke-RollbackFromManifest -ManifestPath $mp
        exit ([int](-not $ok))
    }

    $ctx = New-InstallContext -RepoDir $RepoDir -BundleDir $BundleDir -Silent:$Silent -Rehearse:$Rehearse
    $ctx.Stamp = $stamp

    # ===== MODE: rehearsal =====
    if ($Rehearse) {
        Write-Log "MODE: rehearsal (isolated sandbox)" STEP
        $ok = Invoke-Rehearse -Ctx $ctx
        exit ([int](-not $ok))
    }

    # ===== MODE: install =====
    $ctx.ImagesTar = Resolve-BundleImagesTar $BundleDir
    $ctx.ToVersion = Read-BundleVersion $BundleDir
    Write-Log "GOP offline installer — bundle: $BundleDir  target -> v$($ctx.ToVersion)" STEP

    # Phase 0 — preflight (abort = zero changes)
    if (-not (Invoke-Preflight -Ctx $ctx)) { Write-Log "ABORTED at preflight — system unchanged." ERROR; exit 2 }

    # Phase 1 — backup + integrity gate (abort = zero changes)
    if (-not (Invoke-Backup -Ctx $ctx)) { Write-Log "ABORTED at backup — system unchanged." ERROR; exit 3 }

    # Phase 2 + 3 — apply then verify; failure after PONR => unattended rollback
    try {
        Invoke-ApplyStack -Ctx $ctx | Out-Null
        if (Invoke-Verify -Ctx $ctx) {
            Write-Log "===== UPGRADE SUCCESSFUL: v$($ctx.FromVersion) -> v$($ctx.ToVersion) =====" OK
            Write-Log "backups retained at: $($ctx.BackupDir)" INFO
            exit 0
        }
        Write-Log "verification failed -> rolling back" ERROR
        $rb = Invoke-Rollback -Ctx $ctx -Reason 'post-deploy verification failed'
        exit ([int](-not $rb) + 10)
    }
    catch {
        Write-Log "apply/verify error: $($_.Exception.Message) -> rolling back" ERROR
        $rb = Invoke-Rollback -Ctx $ctx -Reason $_.Exception.Message
        exit ([int](-not $rb) + 20)
    }
}
catch {
    Write-Log "FATAL: $($_.Exception.Message)" ERROR
    exit 1
}
