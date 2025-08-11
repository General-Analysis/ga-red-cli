#!/bin/bash

# REDit CLI Installation Script with uv
echo "Installing REDit CLI (ga-red) with uv..."

# Check if we're in the cli directory
if [ ! -f "setup.py" ]; then
    echo "Error: Please run this script from the ga-red-cli directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo "✅ uv installed successfully"
fi

# Create virtual environment using uv
echo "🔧 Creating virtual environment..."
uv venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies and package with uv
echo "📦 Installing dependencies..."
uv pip install -r requirements.txt
uv pip install -e .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "To use the CLI, first activate the virtual environment:"
    echo "  source .venv/bin/activate"
    echo ""
    echo "Then you can use the 'ga-red' command:"
    echo "  ga-red --help"
    echo "  ga-red jobs list"
    echo "  ga-red jobs run configs/tap_llm_user.yaml"
    echo ""
    echo "To deactivate the virtual environment when done:"
    echo "  deactivate"
    echo ""
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi