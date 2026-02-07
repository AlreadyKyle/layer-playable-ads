#!/bin/bash
# Layer.ai Playable Studio - Next.js + FastAPI Start Script
# Runs both the FastAPI backend and Next.js frontend concurrently

set -e
trap "kill 0" EXIT

echo "Starting Layer.ai Playable Studio (Next.js)..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo ".env created (edit with your API keys if needed)"
    echo ""
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install Python deps if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
    echo "Dependencies installed"
    echo ""
fi

# Install frontend deps if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    echo "Frontend dependencies installed"
    echo ""
fi

echo "Starting FastAPI on http://localhost:8000"
echo "Starting Next.js on http://localhost:3000"
echo ""
echo "============================================"
echo "  Open in browser: http://localhost:3000"
echo "============================================"
echo ""

# Start both servers
uvicorn api.main:app --reload --port 8000 &
cd frontend && npm run dev &

wait
