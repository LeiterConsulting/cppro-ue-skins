[CmdletBinding()]
param(
  [string]$Python = '',
  [string]$OutDir = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = (Resolve-Path (Join-Path $root '..\..')).Path
if (-not $Python) {
  $Python = Join-Path $repo '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
  throw "Python environment not found: $Python"
}
if (-not $OutDir) {
  $OutDir = Join-Path $repo 'artifacts\skin-loader\windows-x86_64'
}

& $Python (Join-Path $root 'make_icon.py')
if ($LASTEXITCODE -ne 0) {
  throw "Icon generation failed with exit code $LASTEXITCODE"
}

$icon = Join-Path $root 'assets\cppro-loader.ico'
$catalog = Join-Path $repo 'catalog\skins.json'
$assets = Join-Path $root 'assets'
$work = Join-Path $root 'build'
$spec = Join-Path $root 'spec'
New-Item -ItemType Directory -Force -Path $OutDir, $work, $spec | Out-Null

$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = $root
try {
  & $Python (Join-Path $repo 'tools\build-skin-catalog.py') --check
  if ($LASTEXITCODE -ne 0) {
    throw "Generated catalog check failed with exit code $LASTEXITCODE"
  }
  & $Python -m unittest discover -s (Join-Path $root 'tests') -v
  if ($LASTEXITCODE -ne 0) {
    throw "Loader unit tests failed with exit code $LASTEXITCODE"
  }
  & $Python (Join-Path $root 'verify_catalog.py')
  if ($LASTEXITCODE -ne 0) {
    throw "Catalog verification failed with exit code $LASTEXITCODE"
  }
} finally {
  $env:PYTHONPATH = $previousPythonPath
}

$common = @(
  '--noconfirm',
  '--clean',
  '--onefile',
  '--windowed',
  '--icon', $icon,
  '--paths', $root,
  '--hidden-import', 'pywinusb.hid',
  '--add-data', "$catalog;catalog",
  '--add-data', "$assets;assets",
  '--distpath', $OutDir,
  '--workpath', $work,
  '--specpath', $spec
)

& $Python -m PyInstaller @common `
  '--name' 'CPPRO-Skin-Loader' `
  (Join-Path $root 'entry.py')
if ($LASTEXITCODE -ne 0) {
  throw "Loader build failed with exit code $LASTEXITCODE"
}

$executable = Join-Path $OutDir 'CPPRO-Skin-Loader.exe'
$hash = (Get-FileHash -LiteralPath $executable -Algorithm SHA256).Hash
$checksum = Join-Path $OutDir 'SHA256SUMS.txt'
$checksumLines = @("$hash  CPPRO-Skin-Loader.exe")
$catalogDocument = Get-Content -LiteralPath $catalog -Raw | ConvertFrom-Json
foreach ($skin in $catalogDocument.skins) {
  $checksumLines += "$($skin.sha256)  $($skin.filename)"
}
Set-Content -LiteralPath $checksum -Value $checksumLines -Encoding ascii

Get-Item -LiteralPath $executable, $checksum |
  Select-Object Name, Length, LastWriteTime
