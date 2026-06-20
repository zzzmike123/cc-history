param(
    [string]$InnoSetupCompiler = ""
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Pyproject = Get-Content -Raw ".\pyproject.toml"
if ($Pyproject -notmatch '(?m)^version\s*=\s*"([^"]+)"') {
    throw "Could not read project version from pyproject.toml"
}
$Version = $Matches[1]
$InstallerName = "CC-History-Setup-$Version.exe"

Write-Host "==> Building CC History executable"
python -m pip install --upgrade pip
python -m pip install -e . pyinstaller
python -m PyInstaller --clean --noconfirm packaging\cc-history.spec

if (-not (Test-Path ".\dist\CC History.exe")) {
    throw "PyInstaller did not produce dist\CC History.exe"
}

if (-not $InnoSetupCompiler) {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            $InnoSetupCompiler = $candidate
            break
        }
    }
}

if (-not $InnoSetupCompiler -or -not (Test-Path $InnoSetupCompiler)) {
    Write-Host ""
    Write-Host "PyInstaller build is ready: dist\CC History.exe"
    Write-Host "Install Inno Setup 6 to build the one-click installer:"
    Write-Host "  winget install JRSoftware.InnoSetup"
    Write-Host "Then rerun:"
    Write-Host "  .\scripts\build_windows.ps1"
    exit 0
}

Write-Host "==> Building Windows installer"
& $InnoSetupCompiler ".\installer\cc-history.iss"

Write-Host ""
Write-Host "Done:"
Write-Host "  dist\CC History.exe"
Write-Host "  installer\output\$InstallerName"
