# Build Windows .exe and .msi installer
# Run on Windows: powershell -ExecutionPolicy Bypass -File build_scripts\build_windows.ps1
$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "── Installing build dependencies ──" -ForegroundColor Cyan
pip install -e ".[all]" pyinstaller

Write-Host "── Cleaning previous builds ──" -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist, creatoragent.egg-info -ErrorAction SilentlyContinue

Write-Host "── Building Windows .exe ──" -ForegroundColor Cyan
pyinstaller build_binary.spec --clean --noconfirm

if (-not (Test-Path "dist\creatoragent.exe")) {
    Write-Host "ERROR: build failed" -ForegroundColor Red
    exit 1
}

Write-Host "── Creating .zip archive ──" -ForegroundColor Cyan
Compress-Archive -Path "dist\creatoragent.exe" -DestinationPath "dist\creatoragent-windows-x64.zip" -Force

# Optional: build .msi installer with WiX (if installed)
$wixPath = Get-Command "candle.exe" -ErrorAction SilentlyContinue
if ($wixPath) {
    Write-Host "── Building .msi installer (WiX detected) ──" -ForegroundColor Cyan

    $wxs = @"
<?xml version='1.0' encoding='windows-1252'?>
<Wix xmlns='http://schemas.microsoft.com/wix/2006/wi'>
  <Product Name='CreatorAgent' Manufacturer='CreatorAgent'
           Id='*' UpgradeCode='12345678-1234-1234-1234-123456789012'
           Language='1033' Codepage='1252' Version='1.0.0'>
    <Package Id='*' Keywords='Installer' Description='CreatorAgent CLI'
             Manufacturer='CreatorAgent' InstallerVersion='200'
             Languages='1033' Compressed='yes' SummaryCodepage='1252' />
    <Media Id='1' Cabinet='creatoragent.cab' EmbedCab='yes' />
    <Directory Id='TARGETDIR' Name='SourceDir'>
      <Directory Id='ProgramFiles64Folder'>
        <Directory Id='APPLICATIONFOLDER' Name='CreatorAgent'>
          <Component Id='MainExe' Guid='12345678-1234-1234-1234-123456789013'>
            <File Id='creatoragent.exe' Name='creatoragent.exe' DiskId='1'
                  Source='dist\creatoragent.exe' KeyPath='yes' />
            <Environment Id='PathEnv' Name='PATH' Value='[APPLICATIONFOLDER]'
                         Permanent='no' Part='last' Action='set' System='yes' />
          </Component>
        </Directory>
      </Directory>
    </Directory>
    <Feature Id='Complete' Level='1'>
      <ComponentRef Id='MainExe' />
    </Feature>
  </Product>
</Wix>
"@
    $wxs | Out-File -Encoding ascii build\creatoragent.wxs
    candle.exe -out build\creatoragent.wixobj build\creatoragent.wxs
    light.exe -out dist\creatoragent-1.0.0-win64.msi build\creatoragent.wixobj
    Write-Host "  ✓ dist\creatoragent-1.0.0-win64.msi" -ForegroundColor Green
} else {
    Write-Host "  ⚠ WiX not found — skipping .msi (install: choco install wixtoolset)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "── Build complete ──" -ForegroundColor Green
Get-ChildItem dist
Write-Host ""
Write-Host "Run: .\dist\creatoragent.exe"
