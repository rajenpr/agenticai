#!/bin/bash
# Start the IT Operations API Server

echo "Starting IT Operations API Server..."
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python src/api/server.py
