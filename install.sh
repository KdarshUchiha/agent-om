#!/usr/bin/env bash
# CreatorAgent universal installer
# Usage: curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/creatoragent/main/install.sh | bash
set -e

REPO="YOUR_USERNAME/creatoragent"
VERSION="${CREATOR_VERSION:-latest}"

# Detect platform
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
    linux)   PLATFORM="linux-x64"; ASSET="creatoragent-linux-x64.tar.gz" ;;
    darwin)
        case "$ARCH" in
            arm64)  PLATFORM="macos-arm64"; ASSET="creatoragent-macos-arm64.tar.gz" ;;
            x86_64) PLATFORM="macos-x64";   ASSET="creatoragent-macos-x86_64.tar.gz" ;;
            *) echo "❌ Unsupported macOS arch: $ARCH"; exit 1 ;;
        esac ;;
    *) echo "❌ Unsupported OS: $OS"; echo "   For Windows, download from: https://github.com/$REPO/releases"; exit 1 ;;
esac

INSTALL_DIR="${CREATOR_INSTALL_DIR:-$HOME/.local/bin}"
mkdir -p "$INSTALL_DIR"

echo "📥 Downloading CreatorAgent for $PLATFORM..."
if [ "$VERSION" = "latest" ]; then
    URL="https://github.com/$REPO/releases/latest/download/$ASSET"
else
    URL="https://github.com/$REPO/releases/download/$VERSION/$ASSET"
fi

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

curl -fsSL -o "$TMP/$ASSET" "$URL"
tar -xzf "$TMP/$ASSET" -C "$TMP"

# Find the binary inside the extracted folder
BIN=$(find "$TMP" -maxdepth 2 -type f -name "creatoragent*" ! -name "*.tar.gz" | head -1)
if [ -z "$BIN" ]; then
    echo "❌ Couldn't find binary in archive"
    exit 1
fi

cp "$BIN" "$INSTALL_DIR/creatoragent"
chmod +x "$INSTALL_DIR/creatoragent"

echo "✅ Installed to $INSTALL_DIR/creatoragent"

# Check PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo
    echo "⚠️  $INSTALL_DIR is not in your PATH. Add this to your shell config:"
    echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
fi

echo
echo "🚀 Try it:"
echo "    creatoragent --demo"
echo
echo "🔑 Set up a free API key:"
echo "    export GEMINI_API_KEY=...  # from https://aistudio.google.com"
echo "    export GROQ_API_KEY=...    # from https://console.groq.com"
