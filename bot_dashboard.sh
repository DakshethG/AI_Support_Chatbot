#!/bin/bash

# AI Support Bot - Dashboard Script
# Clean, working version with formatted session management

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🤖 AI Support Bot - Dashboard${NC}"
echo "=================================="

# URLs Section
echo -e "\n${BLUE}🌐 ACCESS LINKS${NC}"
echo "----------------------------------------"
echo -e "${GREEN}Frontend (Chat):${NC} http://localhost:3000"
echo -e "${GREEN}API Docs:${NC}        http://localhost:8000/docs"
echo -e "${GREEN}Health Check:${NC}    http://localhost:8000/health"
echo -e "${GREEN}Grafana:${NC}         http://localhost:3001"
echo -e "${GREEN}Prometheus:${NC}      http://localhost:9090"

# Session Management (Formatted)
echo -e "\n${BLUE}👥 SESSION MANAGEMENT${NC}"
echo "----------------------------------------"
echo -e "${YELLOW}Recent Sessions (Formatted):${NC}"

curl -s "http://localhost:8000/api/v1/admin/sessions?limit=10" | python3 << 'EOF'
import json, sys
from datetime import datetime

try:
    sessions = json.load(sys.stdin)
    
    # Header
    print("\n{:<30} {:<8} {:<12} {:<12}".format("Session ID", "Messages", "Created", "Last Active"))
    print("-" * 70)
    
    # Sessions
    for session in sessions:
        try:
            created = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00')).strftime('%m/%d %H:%M')
            last_active = datetime.fromisoformat(session['last_active_at'].replace('Z', '+00:00')).strftime('%m/%d %H:%M')
            
            session_id = session['id'][:29] if len(session['id']) > 29 else session['id']
            messages = str(session['total_messages'])
            
            print("{:<30} {:<8} {:<12} {:<12}".format(session_id, messages, created, last_active))
        except Exception as e:
            print(f"Error processing session: {e}")
            
except Exception as e:
    print("Could not retrieve sessions")
EOF

# Usage Stats
echo -e "\n${BLUE}📊 USAGE STATISTICS${NC}"
echo "----------------------------------------"
curl -s "http://localhost:8000/api/v1/usage?days=1" | python3 << 'EOF'
import json, sys

try:
    data = json.load(sys.stdin)
    print("Total Requests:", data["total_requests"])
    print("Success Rate:", f"{data['success_rate']:.1%}")
    print("Total Tokens:", f"{data['total_tokens']:,}")
    print("Avg Response Time:", f"{data['avg_response_time_ms']:.0f}ms")
except:
    print("Could not retrieve usage stats")
EOF

# Quick Tests
echo -e "\n${BLUE}🧪 QUICK TESTS${NC}"
echo "----------------------------------------"
echo -e "${YELLOW}1. FAQ Test:${NC}"
echo 'curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d '"'"'{"message": "What is your return policy?", "session_id": "dashboard-test"}'"'"''

echo -e "\n${YELLOW}2. Escalation Test:${NC}" 
echo 'curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d '"'"'{"message": "I want to sue Amazon", "session_id": "dashboard-escalation"}'"'"''

# Interactive Menu
echo -e "\n${BLUE}🎯 QUICK ACTIONS${NC}"
echo "----------------------------------------"
echo "1) Run FAQ Test"
echo "2) Run Escalation Test" 
echo "3) Show All Sessions"
echo "4) Open Frontend"
echo "5) View Service Status"
echo "6) Exit"

read -p "Choose (1-6): " choice

case $choice in
    1)
        echo -e "\n${GREEN}🧪 Testing FAQ...${NC}"
        curl -X POST "http://localhost:8000/api/v1/chat" \
             -H "Content-Type: application/json" \
             -d '{"message": "What is your return policy?", "session_id": "dashboard-faq"}' | python3 -m json.tool
        ;;
    2)
        echo -e "\n${GREEN}🚨 Testing Escalation...${NC}"
        curl -X POST "http://localhost:8000/api/v1/chat" \
             -H "Content-Type: application/json" \
             -d '{"message": "I want to sue Amazon", "session_id": "dashboard-escalation"}' | python3 -m json.tool
        ;;
    3)
        echo -e "\n${GREEN}👥 All Sessions:${NC}"
        curl -s "http://localhost:8000/api/v1/admin/sessions?limit=20" | python3 -m json.tool
        ;;
    4)
        echo -e "\n${GREEN}🌐 Opening Frontend...${NC}"
        open http://localhost:3000 2>/dev/null || echo "Open: http://localhost:3000"
        ;;
    5)
        echo -e "\n${GREEN}🔍 Service Status:${NC}"
        docker-compose ps
        ;;
    6)
        echo -e "\n${GREEN}👋 Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "\n${RED}❌ Invalid choice${NC}"
        ;;
esac

echo -e "\n${CYAN}==================================${NC}"
echo -e "${GREEN}✅ Dashboard Complete!${NC}"
echo -e "${CYAN}==================================${NC}"