#!/bin/bash

# 🚀 AI Support Bot - Auto Start Script
# This script automatically starts your AI Support Bot with all services

echo "🤖 AI Support Bot - Auto Start"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
print_status "Checking project directory..."
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found!"
    print_error "Please run this script from the ai-support-bot directory"
    echo ""
    echo "To navigate to the correct directory:"
    echo "cd /Users/vidyuthnihas/ai-support-bot"
    exit 1
fi

print_success "Found docker-compose.yml - we're in the right place!"

# Check if Docker is running
print_status "Checking Docker Desktop..."
if ! docker info >/dev/null 2>&1; then
    print_warning "Docker Desktop is not running. Starting it..."
    open -a Docker
    print_status "Waiting for Docker Desktop to start..."
    
    # Wait for Docker to be ready (max 2 minutes)
    counter=0
    while ! docker info >/dev/null 2>&1 && [ $counter -lt 24 ]; do
        sleep 5
        counter=$((counter + 1))
        echo -n "."
    done
    echo ""
    
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker Desktop failed to start. Please start it manually."
        exit 1
    fi
fi

print_success "Docker Desktop is running!"

# Stop any existing containers
print_status "Stopping any existing containers..."
docker-compose down >/dev/null 2>&1

# Build and start all services
print_status "Building and starting all services..."
echo "This may take a few minutes on the first run..."
docker-compose up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 10

# Check service status
print_status "Checking service health..."
healthy_services=0
total_services=0

while IFS= read -r line; do
    if [[ $line == *"ai-support-bot"* ]]; then
        total_services=$((total_services + 1))
        if [[ $line == *"Up"* ]] && [[ $line == *"healthy"* || $line == *"Up"* ]]; then
            healthy_services=$((healthy_services + 1))
        fi
    fi
done < <(docker-compose ps)

echo ""
print_status "Service Status: $healthy_services/$total_services services ready"

if [ $healthy_services -eq $total_services ]; then
    print_success "All services are running successfully!"
else
    print_warning "Some services may still be starting. Check with: docker-compose ps"
fi

echo ""
echo "🎉 AI Support Bot is now running!"
echo "================================"
echo ""
echo "🌐 Access Points:"
echo "  • Chat Interface:    http://localhost"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Grafana Dashboard: http://localhost:3001"
echo "  • Prometheus:        http://localhost:9090"
echo ""
echo "👤 Grafana Login:"
echo "  • Email: dakshith31@gmail.com"
echo "  • Password: Vids@1234"
echo ""
echo "🔧 Management Commands:"
echo "  • View logs:    docker-compose logs"
echo "  • Stop bot:     docker-compose down"
echo "  • Restart:      docker-compose up -d"
echo ""

# Test if the main interface is accessible
print_status "Testing chat interface..."
if curl -s http://localhost >/dev/null 2>&1; then
    print_success "Chat interface is accessible!"
    
    # Automatically open in browser
    read -p "🌐 Open chat interface in browser? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost
        print_success "Opened http://localhost in your browser!"
    fi
else
    print_warning "Chat interface not yet ready. Please wait a moment and try: http://localhost"
fi

echo ""
echo "💡 Quick Test Commands:"
echo "  # Test chat API:"
echo "  curl -X POST http://localhost/api/v1/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"message\": \"Hello!\"}'"
echo ""
echo "  # Get FAQ suggestions:"
echo "  curl http://localhost/api/v1/faq/suggestions?limit=5"
echo ""
echo "🌍 Want to make it public? See NGROK_SETUP.md for external access!"
echo ""
print_success "Setup complete! Your AI Support Bot is ready to chat! 🤖✨"