#!/bin/bash

# TED Bot Development Startup Script

echo "🚀 Starting TED Bot Development Environment"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "✅ Poetry installed"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
cd backend
poetry install

# Check .env file
if [ ! -f "../.env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp ../.env.example ../.env
    echo "⚠️  Please update .env with your actual API keys and Supabase URL"
    exit 1
fi

# Start the FastAPI server
echo ""
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "💬 Chat Endpoint: http://localhost:8000/api/v1/chat"
echo "🔍 Search Endpoint: http://localhost:8000/api/v1/tenders/search"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd ..
poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
