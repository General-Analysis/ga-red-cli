#!/bin/bash

# REDit CLI Installation Script
echo "Installing REDit CLI (ga-red)..."

# Check if we're in the cli directory
if [ ! -f "setup.py" ]; then
    echo "Error: Please run this script from the cli directory"
    exit 1
fi

# Install in editable mode for development
pip install -e .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "You can now use the 'ga-red' command from anywhere:"
    echo "  ga-red --help"
    echo "  ga-red jobs list"
    echo "  ga-red run config.yaml --monitor"
    echo ""
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
