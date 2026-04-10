#!/bin/bash
# Simple HTTP server for frontend to avoid CORS issues

echo "🌐 Starting TED Bot Frontend Server..."
echo "Frontend will be available at: http://localhost:3000"
echo "API is running at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")/frontend"
python3 -m http.server 3000
