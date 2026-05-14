# Build Windows .exe installer for Om
# Run on Windows: powershell -ExecutionPolicy Bypass -File build_scripts\build_windows.ps1
$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "── Installing build dependencies ──" -ForegroundColor Cyan
pip install -e ".[all]" pyinstaller

Write-Host "── Cleaning previous builds ──" -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist, agent_om.egg-info -ErrorAction SilentlyContinue

Write-Host "── Building Windows .exe ──" -ForegroundColor Cyan
pyinstaller build_binary.spec --clean --noconfirm

if (-not (Test-Path "dist\om.exe")) {
    Write-Host "ERROR: build failed" -ForegroundColor Red
    exit 1
}

Write-Host "── Creating .zip archive ──" -ForegroundColor Cyan
Compress-Archive -Path "dist\om.exe" -DestinationPath "dist\om-windows-x64.zip" -Force

Write-Host ""
Write-Host "── Build complete ──" -ForegroundColor Green
Get-ChildItem dist
Write-Host ""
Write-Host "Run: .\dist\om.exe"
