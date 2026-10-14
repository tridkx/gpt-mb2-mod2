param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$project = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$module = 'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord\Modules\YueQingShuRace'
$target = Join-Path $module 'AssetPackages\yqs.tpac'
$reportPath = Join-Path $project 'reports\experiments\simplified_skirt_2026-10-14\test_installation.json'
if (Get-Process | Where-Object { $_.ProcessName -match 'Bannerlord|TaleWorlds' }) {
    throw 'Exit the game and launcher before changing loaded assets; no process will be terminated.'
}
function Hash([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
if ($Restore) {
    $record = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($record.target -cne $target) { throw 'Unexpected restore target' }
    if ((Hash $target) -ne $record.candidate_sha256) { throw 'Installed asset changed since test installation; preserve it before restoring' }
    if ((Hash $record.backup) -ne $record.previous_sha256) { throw 'Backup hash mismatch' }
    Copy-Item -LiteralPath $record.backup -Destination $target -Force
    if ((Hash $target) -ne $record.previous_sha256) { throw 'Restored asset hash mismatch' }
    $record.installed = $false
    $record | Add-Member -NotePropertyName restored_at -NotePropertyValue (Get-Date -Format o) -Force
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Output 'Restored the pre-test YueQingShuRace asset.'
    return
}
# Explicit experimental installation: retain failed appearance checks and
# released validation unchanged. This is not the release installer.
$candidate = Join-Path $project 'build\mapped_candidate.tpac'
$structure = Get-Content -LiteralPath (Join-Path $project 'reports\experiments\simplified_skirt_2026-10-14\iteration3\mapped_structure_validation.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$candidateHash = Hash $candidate
if ($structure.status -ne 'pass' -or $structure.candidate_sha256 -ne $candidateHash) { throw 'Candidate differs from the structurally inspected asset' }
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw 'Installed YueQingShuRace module missing' }
if ((Hash $target) -eq $candidateHash) { Write-Output 'This candidate is already installed.'; return }
$previousHash = Hash $target
$otherFiles = @{}
foreach ($file in Get-ChildItem -LiteralPath $module -Recurse -File) {
    if ($file.FullName -ine $target) { $otherFiles[$file.FullName] = Hash $file.FullName }
}
$backupDir = Join-Path $project ('build\test_install_backups\skirt_proxy_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backupDir | Out-Null
$backup = Join-Path $backupDir 'yqs.tpac'
Copy-Item -LiteralPath $target -Destination $backup
if ((Hash $backup) -ne $previousHash) { throw 'Backup hash mismatch' }
try {
    Copy-Item -LiteralPath $candidate -Destination $target -Force
    if ((Hash $target) -ne $candidateHash) { throw 'Installed candidate hash mismatch' }
    foreach ($path in $otherFiles.Keys) {
        if ((Hash $path) -ne $otherFiles[$path]) { throw "Unexpected change to another module file: $path" }
    }
} catch {
    Copy-Item -LiteralPath $backup -Destination $target -Force
    throw
}
$record = [ordered]@{
    installed_at = Get-Date -Format o
    module = 'YueQingShuRace'
    baseline_version = 'v0.3.3'
    candidate = 'simplified_primary_surface_964_vertices'
    candidate_sha256 = $candidateHash
    previous_sha256 = $previousHash
    target = $target
    backup = $backup
    installed = $true
    experimental = $true
    offline_appearance_accepted = $false
    game_tested = $false
    other_installed_files_preserved = $otherFiles.Count
    released_workspace_module_preserved = $true
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Copy-Item -LiteralPath $reportPath -Destination (Join-Path $backupDir 'installation.json')
Write-Output "Installed experimental skirt proxy; SHA256 $candidateHash; backup $backup"
