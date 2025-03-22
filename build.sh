#!/bin/bash

echo "Building PomPom Application..."

# Create version variable
VERSION="1.0.0"

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist PomPom.spec

# Build executable
echo "Building executable..."
python -m PyInstaller --name="PomPom" --icon=icon.ico --add-data="icon.ico:." --noconsole --onefile main.py

# Create distribution directory
echo "Creating distribution package..."
DIST_DIR="PomPom-v$VERSION"
rm -rf "$DIST_DIR"
mkdir "$DIST_DIR"

# Copy files to distribution directory
echo "Copying files..."
cp dist/PomPom "$DIST_DIR"
cp icon.ico "$DIST_DIR"
cp README.md "$DIST_DIR"

# Create ZIP file
echo "Creating ZIP archive..."
zip -r "${DIST_DIR}.zip" "$DIST_DIR"

echo "Build complete!"
echo "Executable: $DIST_DIR/PomPom"
echo "ZIP archive: ${DIST_DIR}.zip" 