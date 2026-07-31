# run_all.ps1 — unit test runner (TEST-01..03). Pure-logic tests; no docker required.
# The heavy drills (rehearsal / offline / acceptance) run separately:
#   ..\install.ps1 -Rehearse    (TEST-04, needs docker)
$here = $PSScriptRoot
$tests = @('test_detect_volume.ps1', 'test_env_merge.ps1', 'test_backup_integrity.ps1')
$rc = 0
foreach ($t in $tests) {
    Write-Host "`n=== $t ===" -ForegroundColor Cyan
    & (Join-Path $here $t)
    if ($LASTEXITCODE -ne 0) { $rc = 1 }
}
Write-Host ""
if ($rc -eq 0) { Write-Host "ALL UNIT TESTS PASSED" -ForegroundColor Green } else { Write-Host "SOME TESTS FAILED" -ForegroundColor Red }
Write-Host "Rollback drill (TEST-04): powershell -File ..\install.ps1 -Rehearse -RepoDir <repo>" -ForegroundColor Gray
exit $rc
