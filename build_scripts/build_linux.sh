#!/bin/bash
# Build Linux executable + .deb package for Om
# Usage: bash build_scripts/build_linux.sh
set -e

cd "$(dirname "$0")/.."

echo "── Installing build dependencies ──"
pip install -e ".[all]" pyinstaller

echo "── Cleaning previous builds ──"
rm -rf build dist agent_om.egg-info agent_om.egg-info *.egg-info

echo "── Building Linux binary ──"
pyinstaller build_binary.spec --clean --noconfirm

BIN="dist/om"
if [ ! -f "$BIN" ]; then
    echo "ERROR: build failed"
    exit 1
fi

echo "── Creating .tar.gz archive ──"
cd dist
tar -czf om-linux-x64.tar.gz om
cd ..

echo "── Building .deb package ──"
DEB_DIR="build/deb/agent-om_1.0.0_amd64"
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN" "$DEB_DIR/usr/local/bin" "$DEB_DIR/usr/share/doc/om"

cp dist/om "$DEB_DIR/usr/local/bin/om"
chmod 755 "$DEB_DIR/usr/local/bin/om"
cp README.md "$DEB_DIR/usr/share/doc/om/"
cp LICENSE "$DEB_DIR/usr/share/doc/om/copyright"

cat > "$DEB_DIR/DEBIAN/control" <<CTRL
Package: agent-om
Version: 1.0.0
Section: devel
Priority: optional
Architecture: amd64
Maintainer: KdarshUchiha <noreply@github.com>
Description: Om — God-tier AI solution architect & builder CLI
 Multi-provider LLM agent CLI that builds games, AI agents,
 full-stack apps, and any kind of software. Works with free
 Gemini and Groq APIs, or paid Claude.
CTRL

if command -v dpkg-deb &>/dev/null; then
    dpkg-deb --build "$DEB_DIR" "dist/agent-om_1.0.0_amd64.deb"
    echo "  ✓ dist/agent-om_1.0.0_amd64.deb"
else
    echo "  ⚠ dpkg-deb not found — skipping .deb (install: sudo apt install dpkg-dev)"
fi

echo
echo "── Build complete ──"
ls -lh dist/
echo
echo "Run: ./dist/om"
echo "Install system-wide: sudo cp dist/om /usr/local/bin/"
echo "Or install .deb: sudo dpkg -i dist/agent-om_1.0.0_amd64.deb"
