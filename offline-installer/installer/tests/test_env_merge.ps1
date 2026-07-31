# TEST-02 — Merge-EnvFile unit tests (FR-06). Pure logic, no docker required.
. (Join-Path $PSScriptRoot '..\lib\sync_files.ps1')

$fail = 0
function Assert($cond, $name) {
    if ($cond) { Write-Host "  PASS $name" -ForegroundColor Green }
    else { Write-Host "  FAIL $name" -ForegroundColor Red; $script:fail++ }
}

Write-Host "test_env_merge:"

# should_add_new_keys_when_missing
$existing = @('AUTH_MODE=token', 'POSTGRES_USER=gop_user')
$example  = @('AUTH_MODE=public', 'POSTGRES_USER=gop_user', 'NEW_FLAG=1', 'ANOTHER=abc')
$r = Merge-EnvFile -ExistingLines $existing -ExampleLines $example
Assert (($r.Added -contains 'NEW_FLAG') -and ($r.Added -contains 'ANOTHER')) 'should_add_new_keys_when_missing'
Assert ($r.Added.Count -eq 2) 'should_add_only_missing_keys'

# should_preserve_existing_values_when_present  (AUTH_MODE stays 'token', not example's 'public')
$authLine = $r.Lines | Where-Object { $_ -match '^AUTH_MODE=' } | Select-Object -First 1
Assert ($authLine -eq 'AUTH_MODE=token') 'should_preserve_existing_values_when_present'

# should_not_duplicate_existing_keys
$dupCount = @($r.Lines | Where-Object { $_ -match '^POSTGRES_USER=' }).Count
Assert ($dupCount -eq 1) 'should_not_duplicate_existing_keys'

if ($fail -eq 0) { Write-Host "test_env_merge: ALL PASS" -ForegroundColor Green; exit 0 }
else { Write-Host "test_env_merge: $fail FAILED" -ForegroundColor Red; exit 1 }
