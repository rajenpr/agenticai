#!/bin/bash
# Start the Web Application Server

echo "Starting IT Operations AI Agent - Web Interface..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Please create one from .env.example"
    echo "Run: cp .env.example .env"
    echo "Then configure PORTKEY_API_KEY, LDAP_SERVER, and other settings"
    echo ""
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if required variables are set
if [ -z "$PORTKEY_API_KEY" ]; then
    echo "Error: PORTKEY_API_KEY not set in .env file"
    exit 1
fi

if [ -z "$LDAP_SERVER" ]; then
    echo "Warning: LDAP_SERVER not set. Using default."
fi

echo "Web server will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

python src/web/app.py
