# TEST-03 — backup integrity gate (FR-04). Negative cases are pure (no docker);
# the positive case (valid snapshot volume) is exercised live by Invoke-Backup / Invoke-Rehearse.
. (Join-Path $PSScriptRoot '..\lib\backup.ps1')

$fail = 0
function Assert($cond, $name) {
    if ($cond) { Write-Host "  PASS $name" -ForegroundColor Green }
    else { Write-Host "  FAIL $name" -ForegroundColor Red; $script:fail++ }
}
$tmp = Join-Path $env:TEMP ("ofl_bi_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$ctx = @{ SnapshotVolume = 'definitely_missing_volume_xyz'; PostgresImage = 'postgres:16-alpine' }

Write-Host "test_backup_integrity:"

# should_block_when_dump_missing
$r = Test-BackupIntegrity -Ctx $ctx -DumpPath (Join-Path $tmp 'nope.sql')
Assert ((-not $r.Ok) -and ($r.Reason -eq 'dump missing')) 'should_block_when_dump_missing'

# should_block_when_dump_too_small
$small = Join-Path $tmp 'small.sql'; 'tiny' | Set-Content $small
$r = Test-BackupIntegrity -Ctx $ctx -DumpPath $small
Assert ((-not $r.Ok) -and ($r.Reason -like 'dump too small*')) 'should_block_when_dump_too_small'

# should_block_when_header_missing
$noHead = Join-Path $tmp 'nohead.sql'; ('x' * 2000) | Set-Content $noHead
$r = Test-BackupIntegrity -Ctx $ctx -DumpPath $noHead
Assert ((-not $r.Ok) -and ($r.Reason -eq 'dump header missing')) 'should_block_when_header_missing'

Remove-Item -Recurse -Force $tmp
if ($fail -eq 0) { Write-Host "test_backup_integrity: ALL PASS" -ForegroundColor Green; exit 0 }
else { Write-Host "test_backup_integrity: $fail FAILED" -ForegroundColor Red; exit 1 }
