#!/bin/bash

# PortfoliAI Setup Script
# This script sets up the environment and installs all dependencies

set -e  # Exit on any error

echo "🚀 PortfoliAI Setup Script"
echo "========================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    echo "   Please install Python 3.11 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
echo "   This may take a few minutes..."
./venv/bin/python3 -m pip install --upgrade pip --quiet
./venv/bin/python3 -m pip install -r requirements.txt --quiet

# Verify installation
echo ""
echo "🔍 Verifying installation..."
./venv/bin/python3 -c "import fastapi; print('✅ FastAPI installed')"
./venv/bin/python3 -c "import uvicorn; print('✅ Uvicorn installed')"
./venv/bin/python3 -c "import sklearn; print('✅ scikit-learn installed')"
./venv/bin/python3 -c "import pandas; print('✅ Pandas installed')"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ .env file created (you can add API keys later)"
    else
        echo "⚠️  Warning: env.example not found, skipping .env creation"
    fi
else
    echo "✅ .env file already exists"
fi
echo ""

echo "🎉 Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. (Optional) Add your Groq API key to .env for enhanced AI features"
echo "   2. Start the server:"
echo ""
echo "      ./start.sh"
echo ""
echo "   Or manually:"
echo ""
echo "      ./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port 8000"
echo ""
echo "   3. Open http://localhost:8000 in your browser"
echo ""


