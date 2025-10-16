# AI Support Bot - Complete Startup Commands

## 🚀 QUICK START (Copy & Paste These Commands)

### Option 1: Complete Launch (Recommended)
```bash
cd /Users/vidyuthnihas/ai-support-bot && ./start_bot.sh
```

### Option 2: Manual Step-by-Step
```bash
# Navigate to project directory
cd /Users/vidyuthnihas/ai-support-bot

# Start all Docker services
docker-compose up -d

# Wait for services to start
sleep 5

# Run the dashboard
./bot_dashboard.sh
```

### Option 3: Visual HTML Dashboard
```bash
cd /Users/vidyuthnihas/ai-support-bot && open access.html
```

## 🔧 Individual Commands

### Start Services
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose up -d
```

### Check Status
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose ps
```

### View Logs
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose logs -f backend
```

### Test Chat System
```bash
cd /Users/vidyuthnihas/ai-support-bot
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?", "session_id": "test"}'
```

### View Sessions (Formatted)
```bash
cd /Users/vidyuthnihas/ai-support-bot
curl "http://localhost:8000/api/v1/admin/sessions?limit=10" | python3 -m json.tool
```

### Stop All Services
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose down
```

## 🌐 Access URLs (After Starting)

- **Frontend Chat**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Dashboard**: http://localhost:3001
- **Prometheus Metrics**: http://localhost:9090

## 📁 Available Scripts in /Users/vidyuthnihas/ai-support-bot/

```bash
# Complete launcher (starts everything + dashboard)
./start_bot.sh

# Dashboard only (assumes services are running)
./bot_dashboard.sh

# Visual HTML dashboard
open access.html
```

## ⚡ ONE-LINER COMMANDS

### Start Everything and Open Frontend
```bash
cd /Users/vidyuthnihas/ai-support-bot && ./start_bot.sh && open http://localhost:3000
```

### Quick Test
```bash
cd /Users/vidyuthnihas/ai-support-bot && curl -X POST "http://localhost:8000/api/v1/chat" -H "Content-Type: application/json" -d '{"message": "What is your return policy?", "session_id": "quick-test"}' | python3 -m json.tool
```

### Full Status Check
```bash
cd /Users/vidyuthnihas/ai-support-bot && docker-compose ps && curl -s "http://localhost:8000/health" | python3 -m json.tool
```

## 🛠️ Troubleshooting Commands

### Restart Everything
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose down
docker-compose up -d
sleep 5
./bot_dashboard.sh
```

### Reset Database
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose down -v
docker-compose up -d
```

### View All Logs
```bash
cd /Users/vidyuthnihas/ai-support-bot
docker-compose logs
```

---

## 🎯 RECOMMENDED: Use This Command to Start Everything
```bash
cd /Users/vidyuthnihas/ai-support-bot && ./start_bot.sh
```

This single command will:
1. Navigate to the correct directory
2. Start all Docker services
3. Check service health
4. Test the system
5. Show you all the URLs
6. Launch the interactive dashboard