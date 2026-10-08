param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$Mod,
    [Parameter(Mandatory=$true)][ValidatePattern('^v\d+\.\d+\.\d+$')][string]$Version,
    [ValidatePattern('^v\d+\.\d+\.\d+$')][string]$PreviousVersion,
    [string]$GameRoot = 'D:\SteamLibrary\steamapps\common\Mount & Blade II Bannerlord',
    [string]$Python = 'C:\ProgramData\anaconda3\python.exe',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$projectRoot = [IO.Path]::GetFullPath((Join-Path $workspaceRoot "mods\$Mod"))
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'mod.json') -PathType Leaf)) {
    $projectRoot = [IO.Path]::GetFullPath((Join-Path $workspaceRoot "mods\TianxiangCollection\sets\$Mod"))
}
if (-not $projectRoot.StartsWith($workspaceRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Project outside workspace' }
$config = Get-Content -LiteralPath (Join-Path $projectRoot 'mod.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($config.id -cne $Mod) { throw 'Configuration ID differs from requested module' }
function Get-ProjectFile([string]$relative) {
    $target = [IO.Path]::GetFullPath((Join-Path $projectRoot $relative))
    if (-not $target.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside intended mod' }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Missing project file: $relative" }
    return $target
}
$sourceModulePath = [IO.Path]::GetFullPath((Join-Path $projectRoot "module\$Mod"))
[xml]$descriptor = Get-Content -LiteralPath (Get-ProjectFile "module\$Mod\SubModule.xml") -Encoding UTF8
if ($descriptor.Module.Id.value -cne $Mod -or $descriptor.Module.Version.value -ne $Version) { throw 'Module ID/version differs from requested release' }
$report = Get-Content -LiteralPath (Get-ProjectFile $config.validation_report) -Raw -Encoding UTF8 | ConvertFrom-Json
$packagePath = Get-ProjectFile $config.package
if (-not $packagePath.StartsWith($sourceModulePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Package outside intended module' }
$assetHash = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash
if ($report.version -ne $Version -or $report.final_package_sha256 -ne $assetHash) { throw 'Package/version does not match validation report' }
if ($report.status -and $report.status -ne 'pass') { throw 'Validation report did not pass' }
& $Python (Join-Path $PSScriptRoot 'package_delivery.py') --mod $Mod --version $Version --check-only
if ($LASTEXITCODE -ne 0) { throw 'Delivery inputs invalid' }
$modulesRoot = [IO.Path]::GetFullPath((Join-Path $GameRoot 'Modules'))
$installedModulePath = [IO.Path]::GetFullPath((Join-Path $modulesRoot $Mod))
if (-not $installedModulePath.StartsWith($modulesRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Install target outside Modules' }
if ($Mod -in @('Native','SandBoxCore','Sandbox','StoryMode','CustomBattle','BirthAndDeath','Multiplayer')) { throw 'Cannot install over a native module' }
if ($CheckOnly) { Write-Output "Validated $Mod $Version; target $installedModulePath; no files installed or packaged."; return }
if (-not (Test-Path -LiteralPath $modulesRoot -PathType Container)) { throw 'Game Modules directory missing' }
if (Get-Process | Where-Object { $_.ProcessName -match 'Bannerlord|TaleWorlds' }) { throw 'Exit the game and launcher before installing loaded assets' }
foreach ($kind in @('Mod','Source')) {
    $currentArchive = Join-Path $projectRoot "dist\${Mod}_${kind}.zip"
    if ((Test-Path -LiteralPath $currentArchive) -and -not $PreviousVersion) { throw 'PreviousVersion required to preserve existing delivery archives' }
    if (Test-Path -LiteralPath $currentArchive) {
        if ($PreviousVersion -eq $Version) { throw 'PreviousVersion must differ from Version' }
        $backupArchive = Join-Path $projectRoot "dist\${Mod}_${PreviousVersion}_${kind}.zip"
        if (-not (Test-Path -LiteralPath $backupArchive)) { Copy-Item -LiteralPath $currentArchive -Destination $backupArchive }
    }
}
# Prepare and verify delivery before touching installed resources.
& $Python (Join-Path $PSScriptRoot 'package_delivery.py') --mod $Mod --version $Version
if ($LASTEXITCODE -ne 0) { throw 'Delivery package verification failed' }
$installedFiles = 0
foreach ($moduleFile in (Get-ChildItem -LiteralPath $sourceModulePath -Recurse -File)) {
    if ($moduleFile.Name -eq '.gitkeep') { continue }
    if ($moduleFile.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Module contains a linked file' }
    $relativeFile = $moduleFile.FullName.Substring($sourceModulePath.Length + 1)
    $destinationFile = [IO.Path]::GetFullPath((Join-Path $installedModulePath $relativeFile))
    if (-not $destinationFile.StartsWith($installedModulePath + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Install file outside intended module' }
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destinationFile)) -Force | Out-Null
    Copy-Item -LiteralPath $moduleFile.FullName -Destination $destinationFile -Force
    if ((Get-FileHash -LiteralPath $moduleFile.FullName -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash) { throw "Installed file differs: $relativeFile" }
    $installedFiles++
}
Write-Output "Installed $Mod $Version; verified $installedFiles files and delivery archives. Save the release with a local Git commit and a module-specific tag."
