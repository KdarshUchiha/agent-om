# Building Native Installers

CreatorAgent ships as native standalone binaries for Linux, Windows, and macOS — no Python install required for end users.

## ⚠️ Important: Cross-compilation is NOT supported

Each platform's binary **must be built on that platform**:

| Target Platform | Build Where? | Output |
|---|---|---|
| Linux `.tar.gz` / `.deb` | Linux | ✅ Already built |
| Windows `.exe` / `.msi` | **Windows machine** | needed |
| macOS `.dmg` / `.app` | **Mac (Intel + Apple Silicon)** | needed |

The simplest way to get all three: **GitHub Actions** (next section).

---

## 🚀 Recommended: Auto-build via GitHub Actions

Push the project to GitHub, then tag a release. GitHub builds all three for free:

```bash
cd ~/.workspace/creatoragent

# 1. Push to GitHub
git init
git add -A
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USER/creatoragent.git
git push -u origin main

# 2. Tag a release
git tag v1.0.0
git push origin v1.0.0
```

Within ~10 minutes you'll have a GitHub Release with:
- `creatoragent-linux-x64.tar.gz`
- `creatoragent_1.0.0_amd64.deb`
- `creatoragent.exe`
- `creatoragent-windows-x64.zip`
- `CreatorAgent-1.0.0-x86_64.dmg` (Intel Mac)
- `CreatorAgent-1.0.0-arm64.dmg` (Apple Silicon)

The workflow is already in `.github/workflows/release.yml`.

---

## 🐧 Build Linux locally

```bash
cd ~/.workspace/creatoragent
bash build_scripts/build_linux.sh
```

Output:
- `dist/creatoragent` — single 29MB executable
- `dist/creatoragent-linux-x64.tar.gz` — distributable archive
- `dist/creatoragent_1.0.0_amd64.deb` — Debian/Ubuntu package (if `dpkg-deb` installed)

**Install:**
```bash
# Quick — copy binary
sudo cp dist/creatoragent /usr/local/bin/

# Or use .deb (Debian/Ubuntu)
sudo dpkg -i dist/creatoragent_1.0.0_amd64.deb
```

---

## 🪟 Build Windows (.exe + .msi)

**On a Windows machine** with Python 3.10+ installed:

```powershell
cd creatoragent
powershell -ExecutionPolicy Bypass -File build_scripts\build_windows.ps1
```

Output:
- `dist\creatoragent.exe` — single executable
- `dist\creatoragent-windows-x64.zip` — distributable archive
- `dist\creatoragent-1.0.0-win64.msi` — installer (if WiX Toolset installed)

**Install:**
- Double-click the `.msi` and follow the wizard
- Or copy `creatoragent.exe` to a folder on `%PATH%`

**Optional: WiX for `.msi`**
```powershell
choco install wixtoolset    # via Chocolatey
# or download: wixtoolset.org
```

---

## 🍎 Build macOS (.app + .dmg)

**On a Mac** (Intel or Apple Silicon) with Python 3.10+ installed:

```bash
cd creatoragent
bash build_scripts/build_macos.sh
```

Output:
- `dist/CreatorAgent.app` — macOS app bundle
- `dist/CreatorAgent-1.0.0.dmg` — drag-to-Applications installer
- `dist/creatoragent-macos-arm64.tar.gz` (or `x86_64`) — CLI tarball

**Install:**
- Open the `.dmg`
- Drag `CreatorAgent.app` to Applications
- Run from Spotlight or `open /Applications/CreatorAgent.app`

**First-launch note:** Without Apple Developer signing, users will see "unidentified developer" warnings. Workarounds:
1. Right-click → Open → "Open Anyway" (one-time)
2. Or sign with your Apple Developer ID:
   ```bash
   export APPLE_DEVELOPER_ID="Developer ID Application: Your Name (TEAMID)"
   bash build_scripts/build_macos.sh
   ```

**Optional: prettier .dmg with `create-dmg`:**
```bash
brew install create-dmg
```

---

## 📦 Distribution Channels

Once you have the binaries, distribute via:

| Channel | Best For |
|---|---|
| **GitHub Releases** | Simplest — just upload the artifacts |
| **Homebrew tap** (macOS/Linux) | `brew install yourname/tap/creatoragent` |
| **WinGet** (Windows) | `winget install creatoragent` |
| **Snap Store** (Linux) | `snap install creatoragent` |
| **PyPI** | `pip install creatoragent` (already supported via `pyproject.toml`) |

For a Homebrew tap, create a formula. For WinGet, submit a manifest. For Snap, run `snapcraft init`. All standard processes.

---

## 🛠️ Customizing the Build

The build is driven by `build_binary.spec` (PyInstaller spec file). Key knobs:

| To change | Edit |
|---|---|
| App name | `name='creatoragent'` in EXE() |
| Icon | `icon='path/to/icon.ico'` (Windows) or `.icns` (Mac) |
| Bundle ID | `bundle_identifier='com.creatoragent.cli'` |
| Console window | `console=True` (set `False` for GUI-only) |
| Excluded modules | `excludes=[...]` to shrink size |

Add a custom icon:
1. Create `icon.ico` (Windows), `icon.icns` (Mac), or `icon.png` (Linux)
2. In `build_binary.spec`, set `icon='icon.ico'` in the EXE() block
3. Rebuild

---

## 🧪 Testing the Binary

After building on any platform:

```bash
# Linux
./dist/creatoragent --demo

# Windows
.\dist\creatoragent.exe --demo

# macOS
./dist/CreatorAgent.app/Contents/MacOS/creatoragent --demo
```

---

## 📊 Binary Size

A single binary includes Python interpreter + all dependencies:

| Platform | Size |
|---|---|
| Linux (with all providers) | ~29 MB |
| Windows | ~30 MB |
| macOS | ~32 MB |

To shrink further:
- Build with `--onefile` and UPX compression (already enabled)
- Use the `[gemini]` extra only — saves ~10MB by skipping anthropic/groq
- Build per-provider versions (one with just Gemini, one with just Groq)
