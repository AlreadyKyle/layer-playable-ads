#!/bin/bash
# Layer.ai Playable Studio - Quick Start Script
# Use this script to quickly launch the Streamlit app in Codespaces or local environment

echo "🎮 Starting Layer.ai Playable Studio..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "✅ .env created! Please edit it with your API keys:"
    echo "   - LAYER_API_KEY"
    echo "   - LAYER_WORKSPACE_ID"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
    echo "You can edit .env in the file explorer or run: nano .env"
    echo ""
fi

# Launch Streamlit
echo "🚀 Launching Streamlit on port 8501..."
echo "   The app will be available at the forwarded URL"
echo ""

# Use venv Python if available, otherwise use system streamlit
if [ -f "./venv/bin/python" ]; then
    echo "   Using virtual environment Python..."
    ./venv/bin/python -m streamlit run src/app.py
else
    echo "   Using system Streamlit..."
    streamlit run src/app.py
fi
