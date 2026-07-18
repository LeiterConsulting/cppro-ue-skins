[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Pak,
  [string]$EngineRoot = '',
  [string[]]$ExpectedAssets = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $EngineRoot) {
  if ($env:UE_4_27_ROOT) {
    $EngineRoot = $env:UE_4_27_ROOT
  } else {
    $EngineRoot = 'D:\Epic Games\UE_4.27'
  }
}
$unrealPak = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealPak.exe'
if (-not (Test-Path -LiteralPath $unrealPak -PathType Leaf)) {
  throw "UnrealPak.exe not found: $unrealPak"
}
$pakPath = (Resolve-Path -LiteralPath $Pak).Path

& $unrealPak $pakPath -Test
if ($LASTEXITCODE -ne 0) {
  throw "UnrealPak integrity test failed with exit code $LASTEXITCODE"
}

$listing = (& $unrealPak $pakPath -List 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) {
  throw "UnrealPak listing failed with exit code $LASTEXITCODE"
}

$maps = [regex]::Matches($listing, 'spark/Content/[^"]+\.umap')
if ($maps.Count -ne 1 -or $maps[0].Value -ne 'spark/Content/map/M_EntryPoint.umap') {
  throw "Expected exactly spark/Content/map/M_EntryPoint.umap; found: $($maps.Value -join ', ')"
}
foreach ($asset in $ExpectedAssets) {
  if (-not $listing.Contains($asset)) {
    throw "Expected asset not present: $asset"
  }
}
if (-not $listing.Contains('LogPakFile: Display: Mount point ../../../')) {
  Write-Warning 'UnrealPak output did not expose the mount-point line; inspect the list manually.'
}

$item = Get-Item -LiteralPath $pakPath
$hash = Get-FileHash -LiteralPath $pakPath -Algorithm SHA256
[pscustomobject]@{
  Pak = $item.FullName
  Bytes = $item.Length
  SHA256 = $hash.Hash
  Maps = $maps.Count
  CanonicalMap = $maps[0].Value
  ExpectedAssets = $ExpectedAssets.Count
  Integrity = 'PASS'
}
