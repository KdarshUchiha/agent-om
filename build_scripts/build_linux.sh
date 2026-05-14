#!/bin/bash
# Build Linux executable + .deb package
# Usage: bash build_scripts/build_linux.sh
set -e

cd "$(dirname "$0")/.."

echo "── Installing build dependencies ──"
pip install -e ".[all]" pyinstaller

echo "── Cleaning previous builds ──"
rm -rf build dist creatoragent.egg-info

echo "── Building Linux binary ──"
pyinstaller build_binary.spec --clean --noconfirm

BIN="dist/creatoragent"
if [ ! -f "$BIN" ]; then
    echo "ERROR: build failed"
    exit 1
fi

echo "── Creating .tar.gz archive ──"
cd dist
tar -czf creatoragent-linux-x64.tar.gz creatoragent
cd ..

echo "── Building .deb package ──"
DEB_DIR="build/deb/creatoragent_1.0.0_amd64"
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN" "$DEB_DIR/usr/local/bin" "$DEB_DIR/usr/share/doc/creatoragent"

cp dist/creatoragent "$DEB_DIR/usr/local/bin/creatoragent"
chmod 755 "$DEB_DIR/usr/local/bin/creatoragent"
cp README.md "$DEB_DIR/usr/share/doc/creatoragent/"
cp LICENSE "$DEB_DIR/usr/share/doc/creatoragent/copyright"

cat > "$DEB_DIR/DEBIAN/control" <<EOF
Package: creatoragent
Version: 1.0.0
Section: devel
Priority: optional
Architecture: amd64
Maintainer: CreatorAgent <noreply@creatoragent.dev>
Description: God-tier AI solution architect & builder CLI
 Multi-provider LLM agent CLI that builds games, AI agents,
 full-stack apps, and any kind of software. Works with free
 Gemini and Groq APIs, or paid Claude.
EOF

if command -v dpkg-deb &>/dev/null; then
    dpkg-deb --build "$DEB_DIR" "dist/creatoragent_1.0.0_amd64.deb"
    echo "  ✓ dist/creatoragent_1.0.0_amd64.deb"
else
    echo "  ⚠ dpkg-deb not found — skipping .deb (install: sudo apt install dpkg-dev)"
fi

echo
echo "── Build complete ──"
ls -lh dist/
echo
echo "Run: ./dist/creatoragent"
echo "Install system-wide: sudo cp dist/creatoragent /usr/local/bin/"
echo "Or install .deb: sudo dpkg -i dist/creatoragent_1.0.0_amd64.deb"
