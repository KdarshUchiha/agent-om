#!/bin/bash
# Build macOS .app bundle and .dmg installer
# Usage on macOS: bash build_scripts/build_macos.sh
set -e

cd "$(dirname "$0")/.."

echo "── Installing build dependencies ──"
pip install -e ".[all]" pyinstaller

echo "── Cleaning previous builds ──"
rm -rf build dist creatoragent.egg-info

echo "── Building macOS .app bundle ──"
pyinstaller build_binary.spec --clean --noconfirm

if [ ! -d "dist/CreatorAgent.app" ]; then
    echo "ERROR: build failed — CreatorAgent.app not found"
    exit 1
fi

# Code signing (optional — needs Apple Developer ID)
if [ -n "$APPLE_DEVELOPER_ID" ]; then
    echo "── Code signing with: $APPLE_DEVELOPER_ID ──"
    codesign --deep --force --options runtime \
        --sign "$APPLE_DEVELOPER_ID" \
        dist/CreatorAgent.app
else
    echo "  ⚠ APPLE_DEVELOPER_ID not set — skipping code signing"
    echo "    (users will need to right-click → Open on first launch)"
fi

echo "── Creating .dmg installer ──"
DMG_SRC="build/dmg_src"
rm -rf "$DMG_SRC"
mkdir -p "$DMG_SRC"

cp -R dist/CreatorAgent.app "$DMG_SRC/"
ln -s /Applications "$DMG_SRC/Applications"

# Create the .dmg
if command -v create-dmg &>/dev/null; then
    create-dmg \
        --volname "CreatorAgent 1.0.0" \
        --window-size 500 320 \
        --icon-size 100 \
        --icon "CreatorAgent.app" 130 150 \
        --app-drop-link 370 150 \
        --no-internet-enable \
        "dist/CreatorAgent-1.0.0.dmg" \
        "$DMG_SRC" || true
else
    # Fallback: use built-in hdiutil
    hdiutil create -volname "CreatorAgent 1.0.0" \
        -srcfolder "$DMG_SRC" \
        -ov -format UDZO \
        "dist/CreatorAgent-1.0.0.dmg"
fi

echo "── Also building CLI .tar.gz ──"
cd dist
# Extract just the executable for CLI users who don't want the .app
cp CreatorAgent.app/Contents/MacOS/creatoragent ./creatoragent-cli
tar -czf creatoragent-macos-$(uname -m).tar.gz creatoragent-cli
rm creatoragent-cli
cd ..

echo
echo "── Build complete ──"
ls -lh dist/
echo
echo "Install: drag CreatorAgent.app to /Applications"
echo "Or run CLI: ./dist/CreatorAgent.app/Contents/MacOS/creatoragent"
