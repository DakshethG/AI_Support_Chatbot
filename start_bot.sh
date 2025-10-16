#!/bin/bash

# AI Support Bot - Complete Launcher
# This script starts all services and opens the dashboard

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 AI Support Bot - Complete Launcher${NC}"
echo "======================================"

# Step 1: Start Docker Services
echo -e "\n${BLUE}🐳 Starting Docker Services...${NC}"
echo "docker-compose up -d"
docker-compose up -d

# Step 2: Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Step 3: Check service status
echo -e "\n${BLUE}🔍 Checking Service Status:${NC}"
docker-compose ps

# Step 4: Health Check
echo -e "\n${BLUE}❤️ Health Check:${NC}"
health_status=$(curl -s "http://localhost:8000/health" 2>/dev/null || echo "Service not ready")
if [[ "$health_status" == *"status"* ]]; then
    echo -e "${GREEN}✅ Backend API is running${NC}"
else
    echo -e "${RED}❌ Backend API not ready yet${NC}"
fi

# Step 5: Test Frontend
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" 2>/dev/null || echo "000")
if [[ "$frontend_status" == "200" ]]; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${RED}❌ Frontend not ready yet${NC}"
fi

# Step 6: Show all URLs
echo -e "\n${CYAN}🌐 YOUR AI SUPPORT BOT IS READY!${NC}"
echo "=================================="
echo -e "${GREEN}Frontend (Chat):${NC} http://localhost:3000"
echo -e "${GREEN}API Docs:${NC}        http://localhost:8000/docs"
echo -e "${GREEN}Health Check:${NC}    http://localhost:8000/health"
echo -e "${GREEN}Grafana:${NC}         http://localhost:3001"
echo -e "${GREEN}Prometheus:${NC}      http://localhost:9090"

# Step 7: Quick Test
echo -e "\n${BLUE}🧪 Quick Test:${NC}"
test_result=$(curl -s -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is your return policy?", "session_id": "startup-test"}' 2>/dev/null || echo "error")

if [[ "$test_result" == *"return policy"* ]]; then
    echo -e "${GREEN}✅ Chat system working!${NC}"
else
    echo -e "${YELLOW}⚠️ Chat system might need a moment to initialize${NC}"
fi

# Step 8: Launch Dashboard
echo -e "\n${CYAN}🎯 Launching Dashboard...${NC}"
echo "======================================"

# Run the dashboard
./bot_dashboard.sh