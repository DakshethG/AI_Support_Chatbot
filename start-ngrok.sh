#!/bin/bash

# AI Support Bot - Ngrok Setup Script
# This script starts ngrok tunnels for both frontend and backend

echo "🚀 Starting AI Support Bot with Ngrok tunnels..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install it first:"
    echo "   brew install ngrok/ngrok/ngrok"
    exit 1
fi

# Check if Docker containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Docker containers are not running. Starting them..."
    docker-compose up -d
    echo "⏳ Waiting for services to start..."
    sleep 10
fi

# Function to start ngrok tunnel
start_tunnel() {
    local port=$1
    local name=$2
    local config_name=$3
    
    echo "🌐 Starting ngrok tunnel for $name on port $port..."
    
    # Start ngrok in background and capture output
    ngrok http $port --log=stdout --log-level=info --log-format=json > /tmp/ngrok_$config_name.log 2>&1 &
    local ngrok_pid=$!
    
    # Wait a moment for ngrok to start
    sleep 3
    
    # Get the public URL
    local public_url=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('config', {}).get('addr') == 'http://localhost:$port':
            print(tunnel['public_url'])
            break
except:
    pass
" 2>/dev/null)
    
    if [ -n "$public_url" ]; then
        echo "✅ $name is now accessible at: $public_url"
        echo "$public_url" > "/tmp/ngrok_$config_name.url"
    else
        echo "❌ Failed to get public URL for $name"
    fi
    
    return $ngrok_pid
}

# Kill any existing ngrok processes
pkill -f ngrok

# Start ngrok for frontend (port 80)
start_tunnel 80 "Frontend (Chat Interface)" "frontend"
frontend_pid=$?

# Wait a moment between tunnels
sleep 2

# Start ngrok for backend (port 8000) - this requires a paid plan for multiple tunnels
# For free accounts, we'll just use the frontend tunnel
echo ""
echo "📝 Note: Free ngrok accounts only support 1 tunnel at a time."
echo "   For backend API access, use: [FRONTEND_URL]/api/v1/..."
echo ""

# Show access information
echo "🎉 AI Support Bot is now publicly accessible!"
echo ""
echo "📱 Frontend URL: $(cat /tmp/ngrok_frontend.url 2>/dev/null || echo 'Check ngrok dashboard')"
echo "🔗 API Base URL: $(cat /tmp/ngrok_frontend.url 2>/dev/null || echo 'Check ngrok dashboard')/api/v1"
echo "📊 Ngrok Dashboard: http://localhost:4040"
echo ""
echo "💡 Sample API Usage:"
echo "   curl -X POST $(cat /tmp/ngrok_frontend.url 2>/dev/null || echo '[NGROK_URL]')/api/v1/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"Hello!\"}'"
echo ""
echo "🛑 To stop ngrok tunnels, run: pkill -f ngrok"
echo ""
echo "Press Ctrl+C to stop monitoring..."

# Monitor the tunnels
trap 'echo ""; echo "🛑 Stopping ngrok tunnels..."; pkill -f ngrok; exit 0' INT

# Keep script running and show status
while true do
    if ! pgrep -f ngrok > /dev/null; then
        echo "❌ Ngrok tunnels stopped. Exiting..."
        break
    fi
    sleep 30
done