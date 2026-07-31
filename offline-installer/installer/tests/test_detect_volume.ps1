# TEST-01 — volume/project parsing unit tests (FR-03, R-01). Pure logic, no docker required.
. (Join-Path $PSScriptRoot '..\lib\detect_volume.ps1')

$fail = 0
function Assert($cond, $name) {
    if ($cond) { Write-Host "  PASS $name" -ForegroundColor Green }
    else { Write-Host "  FAIL $name" -ForegroundColor Red; $script:fail++ }
}

Write-Host "test_detect_volume:"

# should_extract_project_when_standard_prefix
Assert ((Get-ProjectNameFromVolume -Volume 'api-test-server_api-test-pgdata') -eq 'api-test-server') `
    'should_extract_project_when_standard_prefix'

# should_extract_project_when_renamed_prefix (user's partial rename case)
Assert ((Get-ProjectNameFromVolume -Volume 'pids-api-server_api-test-pgdata') -eq 'pids-api-server') `
    'should_extract_project_when_renamed_prefix'

# should_return_null_when_suffix_mismatch (pin-by-full-name path)
Assert ($null -eq (Get-ProjectNameFromVolume -Volume 'something_else_volume')) `
    'should_return_null_when_suffix_mismatch'

# should_handle_underscore_in_project_name
Assert ((Get-ProjectNameFromVolume -Volume 'my_proj_v2_api-test-pgdata') -eq 'my_proj_v2') `
    'should_handle_underscore_in_project_name'

if ($fail -eq 0) { Write-Host "test_detect_volume: ALL PASS" -ForegroundColor Green; exit 0 }
else { Write-Host "test_detect_volume: $fail FAILED" -ForegroundColor Red; exit 1 }
