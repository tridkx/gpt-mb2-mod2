param([switch]$LocalGameChecks)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$checkRoot = Join-Path $projectRoot "build/checks-$stamp"
$bundle = Join-Path $projectRoot 'dist/RaceTroopBuilder-v0.2.0-win-x64'
function Invoke-Dotnet([string[]]$Arguments) {
    & dotnet @Arguments
    if ($LASTEXITCODE -ne 0) { throw "dotnet failed: $($Arguments -join ' ')" }
}
Invoke-Dotnet @('build', (Join-Path $projectRoot 'source/RaceTroopBuilder.slnx'), '-c', 'Release', '--nologo')
$testArguments = @('run','--project',(Join-Path $projectRoot 'source/Tests/RaceTroopBuilder.Tests.csproj'),'-c','Release','--no-build','--',$checkRoot)
if ($LocalGameChecks) { $testArguments += '--local-game' }
Invoke-Dotnet $testArguments
if ($LocalGameChecks) {
    $gameRoot = 'D:/SteamLibrary/steamapps/common/Mount & Blade II Bannerlord'
    $runtimeTest = Join-Path $projectRoot 'source/RuntimeTests/bin/Release/net472/RaceTroopBuilder.RuntimeTests.exe'
    & $runtimeTest $gameRoot (Join-Path $checkRoot 'armor-runtime')
    if ($LASTEXITCODE -ne 0) { throw 'Armor runtime offline checks failed' }
}
foreach ($app in @('Gui','Cli')) {
    $destination = Join-Path $bundle ('app/' + $app.ToLowerInvariant())
    Invoke-Dotnet @('publish',(Join-Path $projectRoot "source/$app/RaceTroopBuilder.$app.csproj"),'-c','Release','-r','win-x64','--self-contained','true','--nologo','-o',$destination)
}
New-Item -ItemType Directory -Path (Join-Path $bundle 'examples'),(Join-Path $bundle 'schemas'),(Join-Path $bundle 'docs') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'README.md') -Destination $bundle
Copy-Item -Path (Join-Path $projectRoot 'examples/*.json') -Destination (Join-Path $bundle 'examples')
Copy-Item -Path (Join-Path $projectRoot 'schemas/*.json') -Destination (Join-Path $bundle 'schemas')
Copy-Item -Path (Join-Path $projectRoot 'docs/*.md') -Destination (Join-Path $bundle 'docs')
Copy-Item -LiteralPath (Join-Path $projectRoot 'CHANGELOG.md') -Destination $bundle
foreach ($folder in @('source','tools')) {
    $sourceRoot = Join-Path $projectRoot $folder
    foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/](bin|obj)[\\/]' }) {
        $relative = $file.FullName.Substring($projectRoot.Length).TrimStart([char[]]'\/')
        $destination = Join-Path $bundle $relative
        New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination
    }
}
Copy-Item -LiteralPath (Join-Path $projectRoot 'tools/portable-launch.cmd') -Destination (Join-Path $bundle 'Launch-GUI.cmd')
Copy-Item -LiteralPath (Join-Path $projectRoot 'tools/portable-cli.cmd') -Destination (Join-Path $bundle 'rtb.cmd')
$cli = Join-Path $bundle 'app/cli/RaceTroopBuilder.Cli.exe'
& $cli help | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Published CLI failed' }
if ($LocalGameChecks) {
    $gui = Start-Process -FilePath (Join-Path $bundle 'app/gui/RaceTroopBuilder.exe') -ArgumentList @('--smoke-test',('"' + (Join-Path $checkRoot 'gui-preview.png') + '"')) -WindowStyle Hidden -PassThru -Wait
    if ($gui.ExitCode -ne 0) { throw "Published GUI failed; see $checkRoot" }
}
# Include the licenses that accompany the exact runtime packages used by this publish.
$nugetLines = @(& dotnet nuget locals global-packages --list)
if ($LASTEXITCODE -ne 0) { throw 'Cannot locate runtime package notices' }
$nugetLocation = $nugetLines[0]
$nugetRoot = $nugetLocation.Substring($nugetLocation.IndexOf(':') + 1).Trim()
$runtimeConfig = Get-Content -LiteralPath (Join-Path $bundle 'app/gui/RaceTroopBuilder.runtimeconfig.json') -Raw | ConvertFrom-Json
$noticeRoot = Join-Path $bundle 'third-party-notices'
New-Item -ItemType Directory -Path $noticeRoot -Force | Out-Null
foreach ($framework in $runtimeConfig.runtimeOptions.includedFrameworks) {
    $packageRoot = Join-Path $nugetRoot ($framework.name.ToLowerInvariant() + '.runtime.win-x64/' + $framework.version)
    foreach ($notice in Get-ChildItem -LiteralPath $packageRoot -File | Where-Object { $_.Name -match '^(LICENSE|THIRD-PARTY-NOTICES)' }) {
        Copy-Item -LiteralPath $notice.FullName -Destination (Join-Path $noticeRoot ($framework.name + '-' + $notice.Name))
    }
}
Copy-Item -LiteralPath (Join-Path $nugetRoot 'lib.harmony/2.4.2/LICENSE') -Destination (Join-Path $noticeRoot 'Harmony-LICENSE')
$provider = Join-Path $bundle 'runtime-provider/RaceTroopArmor'
New-Item -ItemType Directory -Path (Join-Path $provider 'bin/Win64_Shipping_Client'),(Join-Path $provider 'ModuleData') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'tools/ArmorProvider.SubModule.xml') -Destination (Join-Path $provider 'SubModule.xml')
foreach ($file in @('RaceTroopBuilder.ArmorRuntime.dll','0Harmony.dll')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot ('source/Runtime/bin/Release/net472/' + $file)) -Destination (Join-Path $provider 'bin/Win64_Shipping_Client')
}
Copy-Item -LiteralPath (Join-Path $noticeRoot 'Harmony-LICENSE') -Destination $provider
$reportRoot = Join-Path $projectRoot 'reports'
New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null
$testSummary = Get-Content -LiteralPath (Join-Path $checkRoot 'tests.json') -Raw | ConvertFrom-Json
$guiSummary = $null
$catalogSummary = $null
if ($LocalGameChecks) {
    $guiSummary = Get-Content -LiteralPath (Join-Path $checkRoot 'gui-smoke.json') -Raw | ConvertFrom-Json
    $scan = (& $cli scan | Out-String | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0) { throw 'Published catalog scan failed' }
    $catalogSummary = @{ game_version=$scan.gameVersion; troop_count=$scan.troopCount; item_count=$scan.itemCount; race_count=$scan.races.Count }
    Copy-Item -LiteralPath (Join-Path $checkRoot 'armor-runtime/runtime-tests.txt') -Destination (Join-Path $reportRoot 'armor_runtime_tests.txt')
    Copy-Item -LiteralPath (Join-Path $checkRoot 'gui-preview.png') -Destination (Join-Path $reportRoot 'gui_preview.png')
}
$binaryHashes = @{}
foreach ($relative in @('app/gui/RaceTroopBuilder.exe','app/gui/RaceTroopBuilder.dll','app/gui/RaceTroopBuilder.Core.dll','app/cli/RaceTroopBuilder.Cli.exe','app/cli/RaceTroopBuilder.Cli.dll','app/cli/RaceTroopBuilder.Core.dll')) {
    $binaryHashes[$relative] = (Get-FileHash -LiteralPath (Join-Path $bundle $relative) -Algorithm SHA256).Hash.ToLowerInvariant()
}
$validation = @{ status='pass'; date=(Get-Date -Format 'yyyy-MM-dd'); version='v0.2.0'; framework='.NET 10';
    armor_runtime_tests=$(if ($LocalGameChecks) { 9 } else { $null }); test_count=$testSummary.count; tests=$testSummary.tests; gui=$guiSummary; catalog=$catalogSummary; binary_hashes=$binaryHashes;
    game_started=$false; actual_game_module_installed=$false; runtime_testing='pending user acceptance'; check_directory=$checkRoot }
$validation | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $reportRoot 'release_validation.json') -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $checkRoot 'tests.json') -Destination (Join-Path $reportRoot 'automated_tests.json')
New-Item -ItemType Directory -Path (Join-Path $bundle 'reports') -Force | Out-Null
Get-ChildItem -LiteralPath $reportRoot -File | Where-Object { $_.Name -ne 'delivery_manifest.json' } | Copy-Item -Destination (Join-Path $bundle 'reports')
$zip = Join-Path $projectRoot "dist/RaceTroopBuilder-v0.2.0-win-x64-$stamp.zip"
Compress-Archive -LiteralPath $bundle -DestinationPath $zip -CompressionLevel Optimal
@{ version='v0.2.0'; archive=$zip; sha256=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $reportRoot 'delivery_manifest.json') -Encoding UTF8
Write-Output "Bundle: $bundle"
Write-Output "Archive: $zip"
Write-Output "Checks: $checkRoot"
