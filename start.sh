#!/bin/bash
# Layer.ai Playable Studio - Quick Start Script
# Automatically sets up environment and launches the app

echo "🎮 Starting Layer.ai Playable Studio..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✅ .env created (edit with your API keys if needed)"
    echo ""
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed (check for streamlit as indicator)
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -q -r requirements.txt
    echo "✅ Dependencies installed"
    echo ""
fi

# Install package in editable mode if not already installed
if ! python3 -c "import src" 2>/dev/null; then
    echo "📦 Installing package in editable mode..."
    pip install -q -e .
    echo "✅ Package installed"
    echo ""
fi

# Launch Streamlit
echo "🚀 Launching app..."
echo ""
echo "═══════════════════════════════════════════════════"
echo "   Open in browser: http://localhost:8501"
echo "═══════════════════════════════════════════════════"
echo ""

python3 -m streamlit run src/app.py --server.headless=true
