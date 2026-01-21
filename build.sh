#!/bin/bash
# Build script for Yocto Tool
# This script installs dependencies and builds a standalone executable

set -e  # Exit on error

echo "=================================="
echo "Yocto Tool Build Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}Warning: Running as root. This is not recommended for building.${NC}"
fi

echo ""
echo "Step 1: Installing system dependencies..."
echo "=========================================="

# Install system packages
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-dev \
    binutils \
    git

echo -e "${GREEN}✓ System dependencies installed${NC}"

echo ""
echo "Step 2: Installing Python dependencies..."
echo "=========================================="

# Upgrade pip
python3 -m pip install --upgrade pip

# Install PyInstaller for creating standalone executable
python3 -m pip install pyinstaller

echo -e "${GREEN}✓ Python dependencies installed${NC}"

echo ""
echo "Step 3: Building standalone executable..."
echo "=========================================="

# Clean previous builds
rm -rf build dist __pycache__
rm -f yocto_tool.spec

# Build with PyInstaller
pyinstaller --onefile \
    --name="YoctoTool" \
    --add-data="manager_rpi.py:." \
    --windowed \
    --icon=NONE \
    yocto_tool.py

echo -e "${GREEN}✓ Build completed!${NC}"

echo ""
echo "=================================="
echo "Build Summary"
echo "=================================="
echo "Executable location: dist/YoctoTool"
echo "Size: $(du -h dist/YoctoTool | cut -f1)"
echo ""
echo "To run the standalone executable:"
echo "  sudo ./dist/YoctoTool"
echo ""
echo "To install system-wide (optional):"
echo "  sudo cp dist/YoctoTool /usr/local/bin/"
echo "  sudo YoctoTool"
echo "=================================="
