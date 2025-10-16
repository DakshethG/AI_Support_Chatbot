# 🤖 AI Support Bot - Complete Run Guide

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (latest version)
- **Git** (for version control)
- **Web Browser** (Chrome, Firefox, Safari, or Edge)

### System Requirements
- **macOS/Linux/Windows** with Docker support
- **4GB RAM** minimum (8GB recommended)
- **2GB free disk space**

---

## 🚀 Quick Start (1-Minute Setup)

### 1. Clone & Navigate
```bash
git clone <your-repo-url>
cd ai-support-bot
```

### 2. Start Everything
```bash
docker-compose up --build -d
```

### 3. Access Your AI Bot
- **Chat Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs  
- **Grafana Dashboard**: http://localhost:3001

**That's it! Your AI Support Bot is now running!**

---

## 🔧 Detailed Setup Instructions

### Step 1: Environment Configuration
The project includes pre-configured environment variables in `.env`:

```bash
# Already configured - no changes needed!
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=nvidia/nemotron-nano-9b-v2:free
DATABASE_URL=postgresql://ai_support:password@localhost:5432/ai_support_db
REDIS_URL=redis://localhost:6379/0
```

### Step 2: Start Services
```bash
# Start all services in background
docker-compose up --build -d

# Or start with logs visible
docker-compose up --build
```

### Step 3: Verify Services
```bash
# Check all services are running
docker-compose ps

# Expected output: 7 healthy services
# - backend (FastAPI)
# - frontend (React/Nginx)  
# - postgres (Database)
# - redis (Cache)
# - worker (Celery)
# - prometheus (Metrics)
# - grafana (Dashboards)
```

---

## 🌐 Access Points & Credentials

### Main Application
| Service | URL | Purpose |
|---------|-----|---------|
| **Chat Interface** | http://localhost | Main user interface |
| **API Backend** | http://localhost:8000 | REST API |
| **API Documentation** | http://localhost:8000/docs | Swagger/OpenAPI docs |

### Monitoring & Analytics  
| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana** | http://localhost:3001 | dakshith31@gmail.com / Vids@1234 | Analytics dashboards |
| **Prometheus** | http://localhost:9090 | None | Metrics collection |

### Development/Debug
| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **PostgreSQL** | localhost:5432 | ai_support / password | Database |
| **Redis** | localhost:6379 | None | Cache |
| **Metrics** | http://localhost:8000/metrics | None | Prometheus metrics |

---

## ✨ Key Features Working

### 🎯 Smart AI Responses
- **FAQ Recognition**: Instant responses for common questions (95% confidence)
- **LLM Integration**: OpenRouter + nvidia/nemotron-nano-9b-v2:free for complex queries
- **Context Awareness**: Maintains conversation history

### 🛡️ Intelligent Escalation  
- **Confidence-Based**: Low confidence responses → human handoff
- **Keyword Detection**: Billing, frustration, complaints → escalation
- **Business Rules**: Customizable escalation triggers

### 📊 Real-Time Monitoring
- **Live Metrics**: Request rates, confidence scores, escalation rates
- **Performance Tracking**: Response times, token usage, costs
- **Business Analytics**: FAQ hit rates, user satisfaction, trends

### 🎨 Modern UI/UX
- **Dark/Light Mode**: Toggle between themes with smooth transitions
- **Modern Design**: Sleek chat bubbles with animations and shadows
- **Copy Messages**: Click-to-copy functionality for all messages
- **Responsive**: Works perfectly on desktop, tablet, and mobile
- **Bot Avatar**: Animated bot assistant with personality
- **Smooth Animations**: Message slide-ins and loading states

---

## 🧪 Testing Your Bot

### Test FAQ Recognition
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'

# Expected: 95% confidence, no escalation
```

### Test LLM Integration  
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is artificial intelligence?"}'

# Expected: AI-generated response via OpenRouter
```

### Test Escalation Logic
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am very frustrated with your service!"}'

# Expected: escalate=true, low confidence
```

---

## 🎮 Using the Chat Interface

### Web Interface (http://localhost)
1. **Type your question** in the input box
2. **Click suggested questions** for quick testing
3. **See confidence scores** displayed with each response  
4. **Watch escalation alerts** when human handoff is needed

### Sample Questions to Try
- "How do I reset my password?" (FAQ)
- "What are your business hours?" (FAQ)
- "Explain how machine learning works" (LLM)
- "I want to cancel my subscription" (May escalate)
- "I am frustrated!" (Will escalate)

---

## 📈 Monitoring with Grafana

### Login to Grafana
1. Go to http://localhost:3001
2. **Email**: dakshith31@gmail.com
3. **Password**: Vids@1234

### View Your Metrics
1. **Add Data Source**: Configuration → Data Sources → Prometheus
   - URL: `http://prometheus:9090`
2. **Create Dashboard** with these queries:
   - `chat_requests_total` - Total requests
   - `faq_matches_total` - FAQ usage
   - `escalations_total` - Escalation count
   - `rate(confidence_scores_sum[5m])` - Confidence trends

---

## 🛠️ Management Commands

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service  
docker-compose logs backend
docker-compose logs frontend
```

### Restart Service
```bash
docker-compose restart backend
```

### Rebuild & Restart
```bash
docker-compose up --build -d
```

### Clean Reset (Remove all data)
```bash
docker-compose down -v
docker-compose up --build -d
```

---

## 🔍 Troubleshooting

### Common Issues

**"Cannot connect to Docker daemon"**
```bash
# Start Docker Desktop first
open -a Docker
# Wait for Docker to start, then retry
```

**"Port already in use"**
```bash
# Check what's using the port
sudo lsof -i :8000
# Stop the process or change ports in docker-compose.yml
```

**"Chat not working"**
```bash
# Check backend health
curl http://localhost:8000/health
# Check logs
docker-compose logs backend
```

**"Grafana login not working"**
```bash
# Reset Grafana (will lose dashboards)
docker-compose down
docker volume rm ai-support-bot_grafana_data
docker-compose up grafana -d
```

### Check System Status
```bash
# All services status
docker-compose ps

# System resources
docker stats

# Health checks
curl http://localhost:8000/health
curl http://localhost:3001/api/health
```

---

## 🚀 Production Deployment

### Environment Variables for Production
```bash
# Update .env for production
APP_ENV=production  
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/ai_support_db
REDIS_URL=redis://prod-redis:6379/0
CORS_ORIGINS=https://yourdomain.com
```

### Scaling Recommendations  
- **Backend**: 2-4 instances behind load balancer
- **Workers**: Scale based on queue length
- **Database**: Use managed PostgreSQL (AWS RDS, etc.)
- **Cache**: Use Redis cluster for high availability

---

## 📁 Project Structure

```
ai-support-bot/
├── backend/                 # FastAPI application
│   ├── app.py              # Main API server
│   ├── openrouter_client.py # LLM integration
│   ├── router.py           # Chat routing logic
│   ├── models/db_models.py # Database models
│   ├── workers/            # Background tasks
│   └── tests/              # Test suite
├── frontend/react-chat/    # React frontend
├── docker-compose.yml      # Service orchestration  
├── .env                    # Environment variables
├── HOW_TO_RUN.md          # This guide
└── README.md              # Project overview
```

---

## 🎯 API Endpoints Reference

### Core Chat API
- `POST /api/v1/chat` - Main chat endpoint
- `GET /api/v1/faq` - Search FAQ items
- `POST /api/v1/escalate` - Manual escalation

### Session Management  
- `POST /api/v1/session` - Create session
- `GET /api/v1/session/{id}` - Get session

### Admin & Analytics
- `GET /api/v1/admin/sessions` - List sessions
- `GET /api/v1/usage` - Usage statistics
- `GET /metrics` - Prometheus metrics

**Full API documentation: http://localhost:8000/docs**

---

## 🎉 Success!

Your AI Support Bot is now fully operational with:

✅ **OpenRouter LLM** (nvidia/nemotron-nano-9b-v2:free)  
✅ **Smart FAQ Recognition**  
✅ **Real-time Chat Interface**  
✅ **Confidence-based Escalation**  
✅ **Session Management**  
✅ **Comprehensive Monitoring**  
✅ **Production-ready Architecture**

**Start chatting at http://localhost and explore the full system!**

---

## 🌍 External Access with Ngrok

**Want to share your AI Support Bot with others or access it remotely?**

### Quick Ngrok Setup:
```bash
# 1. Sign up at ngrok.com (free)
# 2. Get your auth token from dashboard
# 3. Configure ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE

# 4. Make your bot public!
ngrok http 80
```

### What You Get:
- **Public URL**: `https://abc123.ngrok-free.app`
- **API Access**: `https://abc123.ngrok-free.app/api/v1/`
- **Mobile Access**: Works on any device worldwide
- **API Integration**: Use for webhooks, external apps

### Sample External API Usage:
```bash
export BOT_URL="https://abc123.ngrok-free.app"

# Test from anywhere in the world!
curl -X POST $BOT_URL/api/v1/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello from the internet!"}'
```

📄 **Detailed Setup**: See [NGROK_SETUP.md](./NGROK_SETUP.md) for complete instructions

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs`
3. Verify all services: `docker-compose ps`
4. Test API health: `curl http://localhost:8000/health`

**Happy chatting! 🤖✨**