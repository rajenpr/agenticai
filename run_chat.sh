#!/bin/bash
# Start the CLI Chat Interface

echo "Starting IT Operations AI Agent CLI..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Please create one from .env.example"
    echo "Run: cp .env.example .env"
    echo "Then add your PORTKEY_API_KEY to the .env file"
    echo ""
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if API key is set
if [ -z "$PORTKEY_API_KEY" ]; then
    echo "Error: PORTKEY_API_KEY not set in .env file"
    exit 1
fi

python src/cli/chat.py
