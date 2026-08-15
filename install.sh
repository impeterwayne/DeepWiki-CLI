#!/usr/bin/env bash
set -e

echo "======================================================="
echo "         DeepWiki CLI - 1-Command Installer            "
echo "======================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python 3 was not found in PATH."
        exit 1
    else
        PY_CMD=python
    fi
else
    PY_CMD=python3
fi

echo "[1/2] Installing DeepWiki CLI package and dependencies..."
$PY_CMD -m pip install -e .

echo ""
echo "[2/2] Installing Playwright Chromium browser..."
$PY_CMD -m playwright install chromium

echo ""
echo "======================================================="
echo " SUCCESS! DeepWiki CLI is installed."
echo "======================================================="
echo ""
echo "You can now run 'deepwiki' directly from anywhere:"
echo "  deepwiki https://github.com/microsoft/vscode"
echo "  deepwiki microsoft/vscode -c 10"
echo "  deepwiki --help"
echo ""
