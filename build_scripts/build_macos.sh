#!/bin/bash
# Build macOS .app bundle and .dmg installer for Om
# Usage on macOS: bash build_scripts/build_macos.sh
set -e

cd "$(dirname "$0")/.."

echo "── Installing build dependencies ──"
pip install -e ".[all]" pyinstaller

echo "── Cleaning previous builds ──"
rm -rf build dist agent_om.egg-info

echo "── Building macOS .app bundle ──"
pyinstaller build_binary.spec --clean --noconfirm

if [ ! -d "dist/Om.app" ]; then
    echo "ERROR: build failed — Om.app not found"
    exit 1
fi

if [ -n "$APPLE_DEVELOPER_ID" ]; then
    echo "── Code signing with: $APPLE_DEVELOPER_ID ──"
    codesign --deep --force --options runtime \
        --sign "$APPLE_DEVELOPER_ID" \
        dist/Om.app
else
    echo "  ⚠ APPLE_DEVELOPER_ID not set — skipping code signing"
    echo "    (users will need to right-click → Open on first launch)"
fi

echo "── Creating .dmg installer ──"
DMG_SRC="build/dmg_src"
rm -rf "$DMG_SRC"
mkdir -p "$DMG_SRC"
cp -R dist/Om.app "$DMG_SRC/"
ln -s /Applications "$DMG_SRC/Applications"

ARCH=$(uname -m)
hdiutil create -volname "Om 1.0.0" \
    -srcfolder "$DMG_SRC" \
    -ov -format UDZO \
    "dist/Om-1.0.0-$ARCH.dmg"

echo "── Building CLI .tar.gz ──"
cp dist/Om.app/Contents/MacOS/om dist/om-cli
cd dist
tar -czf om-macos-$ARCH.tar.gz om-cli
rm om-cli
cd ..

echo
echo "── Build complete ──"
ls -lh dist/
echo
echo "Install: drag Om.app to /Applications"
echo "Or run CLI: ./dist/Om.app/Contents/MacOS/om"
