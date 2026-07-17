[CmdletBinding()]
param(
  [string]$EngineRoot = '',
  [string]$OutPak = '',
  [string]$Project = '',
  [string]$Map = '/Game/map/M_EntryPoint',
  [string]$TargetPlatform = 'Android_ASTC',
  [switch]$SkipCompile,
  [switch]$SkipCook
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $EngineRoot) {
  if ($env:UE_4_27_ROOT) {
    $EngineRoot = $env:UE_4_27_ROOT
  } else {
    $EngineRoot = 'D:\Epic Games\UE_4.27'
  }
}
if (-not $Project) {
  $Project = Join-Path $repoRoot 'project\spark.uproject'
}
if (-not $OutPak) {
  $OutPak = Join-Path $repoRoot 'artifacts\cppro_skin.pak'
}

$projectPath = (Resolve-Path -LiteralPath $Project).Path
$projectRoot = Split-Path -Parent $projectPath
$editorCmd = Join-Path $EngineRoot 'Engine\Binaries\Win64\UE4Editor-Cmd.exe'
$buildBat = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$unrealPak = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealPak.exe'
foreach ($required in @($editorCmd, $buildBat, $unrealPak)) {
  if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
    throw "Required UE4.27 tool not found: $required"
  }
}

$artifactRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'artifacts'))
$stagePath = Join-Path $artifactRoot 'staging'
$responseFile = Join-Path $artifactRoot 'cppro_skin.unrealpak-response.txt'
$outPath = [System.IO.Path]::GetFullPath($OutPak)
New-Item -ItemType Directory -Force -Path $artifactRoot,(Split-Path -Parent $outPath) | Out-Null

if (-not $SkipCompile) {
  Write-Host 'Compiling sparkEditor for UE4.27...'
  & $buildBat sparkEditor Win64 Development $projectPath -WaitMutex -NoHotReload
  if ($LASTEXITCODE -ne 0) {
    throw "Unreal editor build failed with exit code $LASTEXITCODE"
  }
}

if (-not $SkipCook) {
  Write-Host "Cooking $Map for $TargetPlatform..."
  & $editorCmd $projectPath -run=Cook "-TargetPlatform=$TargetPlatform" `
    "-Map=$Map" -unversioned -compressed -stdout -CrashForUAT -unattended `
    -NoLogTimes
  if ($LASTEXITCODE -ne 0) {
    throw "UE4 cook failed with exit code $LASTEXITCODE"
  }
}

$cookedRoot = Join-Path $projectRoot "Saved\Cooked\$TargetPlatform"
$normalizedMap = $Map.Trim().TrimEnd('/')
if (-not $normalizedMap.StartsWith('/Game/', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Map must be a /Game package path: $Map"
}
$mapRelative = $normalizedMap.Substring('/Game/'.Length).Replace('/', '\') + '.umap'
$cookedMap = Join-Path $cookedRoot (Join-Path 'spark\Content' $mapRelative)
if (-not (Test-Path -LiteralPath $cookedMap -PathType Leaf)) {
  throw "Cooked entry map not found: $cookedMap"
}

$resolvedStage = [System.IO.Path]::GetFullPath($stagePath)
if (-not $resolvedStage.StartsWith($artifactRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to use staging path outside artifacts: $resolvedStage"
}
if (Test-Path -LiteralPath $resolvedStage) {
  Remove-Item -LiteralPath $resolvedStage -Recurse -Force
}

$stageSpark = Join-Path $resolvedStage 'spark'
$stagePlugin = Join-Path $stageSpark 'Plugins\SkinApi'
New-Item -ItemType Directory -Force -Path $stageSpark,$stagePlugin | Out-Null

$cookedEngine = Join-Path $cookedRoot 'Engine'
if (Test-Path -LiteralPath $cookedEngine) {
  Copy-Item -LiteralPath $cookedEngine -Destination $resolvedStage -Recurse
}
Copy-Item -LiteralPath (Join-Path $cookedRoot 'spark\Content') `
  -Destination $stageSpark -Recurse
Copy-Item -LiteralPath (Join-Path $cookedRoot 'spark\AssetRegistry.bin') `
  -Destination $stageSpark
Copy-Item -LiteralPath (Join-Path $projectRoot 'Config') `
  -Destination $stageSpark -Recurse
Copy-Item -LiteralPath $projectPath `
  -Destination (Join-Path $stageSpark 'spark.uproject')
Copy-Item -LiteralPath (Join-Path $projectRoot 'Plugins\SkinApi\SkinApi.uplugin') `
  -Destination $stagePlugin
if (Test-Path -LiteralPath (Join-Path $projectRoot 'Plugins\SkinApi\Config')) {
  Copy-Item -LiteralPath (Join-Path $projectRoot 'Plugins\SkinApi\Config') `
    -Destination $stagePlugin -Recurse
}

$files = Get-ChildItem -LiteralPath $resolvedStage -Recurse -File
if (-not $files) {
  throw 'Staging tree is empty'
}
$responseLines = foreach ($file in $files) {
  $relative = $file.FullName.Substring($resolvedStage.Length).TrimStart('\','/')
  $destination = '../../../' + $relative.Replace('\','/')
  '"{0}" "{1}"' -f $file.FullName,$destination
}
$responseLines | Set-Content -LiteralPath $responseFile -Encoding UTF8

Write-Host "Packing $($files.Count) staged files..."
& $unrealPak $outPath "-Create=$responseFile" -compress -UTF8Output
if ($LASTEXITCODE -ne 0) {
  throw "UnrealPak failed with exit code $LASTEXITCODE"
}

& (Join-Path $PSScriptRoot 'verify-pak.ps1') -Pak $outPath -EngineRoot $EngineRoot
if ($LASTEXITCODE -ne 0) {
  throw 'PAK verification failed'
}

$item = Get-Item -LiteralPath $outPath
$hash = Get-FileHash -LiteralPath $outPath -Algorithm SHA256
[pscustomobject]@{
  Pak = $item.FullName
  Bytes = $item.Length
  SHA256 = $hash.Hash
  Map = $normalizedMap
  DeviceWritten = $false
}
