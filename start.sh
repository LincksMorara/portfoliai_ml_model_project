#!/bin/bash

# PortfoliAI Start Script
# Starts the FastAPI server

set -e  # Exit on any error

echo "🚀 Starting PortfoliAI Server..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Run ./setup.sh first to set up the environment"
    exit 1
fi

# Check if dependencies are installed
if ! ./venv/bin/python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ Error: Dependencies not installed"
    echo "   Run ./setup.sh first to install dependencies"
    exit 1
fi

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Warning: Port 8000 is already in use"
    echo ""
    read -p "   Kill existing process and restart? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Stopping existing server..."
        pkill -f "uvicorn server:app" || true
        sleep 2
    else
        echo "   Using alternative port 8001..."
        PORT=8001
    fi
fi

PORT=${PORT:-8000}

echo "✅ Starting server on http://localhost:$PORT"
echo ""
echo "📝 Press Ctrl+C to stop the server"
echo ""

# Start the server
./venv/bin/python3 -m uvicorn server:app --host 0.0.0.0 --port $PORT


