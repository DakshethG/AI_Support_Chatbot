# 🚀 AI Support Bot - Complete Quick Start Guide

**Get your AI Support Bot running in under 5 minutes!** This guide covers everything from opening the project to accessing your bot locally and publicly.

---

## 📋 Prerequisites (One-time Setup)

### Required Software:
- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop)
- **Terminal/Command Line** - Built into macOS
- **Web Browser** - Any modern browser (Chrome, Firefox, Safari, Edge)

### Optional (for external access):
- **Ngrok Account** - [Sign up free](https://ngrok.com) for public URLs

---

## 🎯 Step-by-Step Instructions

### Step 1: Open Terminal and Navigate to Project
```bash
# Option A: If you're already in the project folder (you see files like docker-compose.yml)
pwd
# Should show: /Users/vidyuthnihas/ai-support-bot

# Option B: If you need to navigate to the project folder
cd /Users/vidyuthnihas/ai-support-bot

# Option C: Open project in Finder and drag folder to Terminal
# Just drag the ai-support-bot folder from Finder into Terminal window
```

### Step 2: Verify You're in the Right Place
```bash
# Check if you see the project files
ls -la

# You should see files like:
# - docker-compose.yml
# - backend/
# - frontend/
# - HOW_TO_RUN.md
# - README.md
```

### Step 3: Start Docker Desktop
```bash
# Start Docker Desktop (if not already running)
open -a Docker

# Wait for Docker to fully start (look for Docker icon in menu bar)
# Usually takes 30-60 seconds on first startup
```

### Step 4: Build and Start All Services
```bash
# This single command does everything!
docker-compose up --build -d

# What this does:
# - Builds all Docker containers
# - Starts PostgreSQL database
# - Starts Redis cache
# - Starts backend API
# - Starts frontend React app
# - Starts Celery workers
# - Starts Prometheus monitoring
# - Starts Grafana dashboards
```

### Step 5: Wait for Services to Start
```bash
# Check if all services are running (wait 30-60 seconds)
docker-compose ps

# You should see all services as "Up" and "healthy"
# If any show "starting", wait a bit longer
```

### Step 6: Test Your Bot! 🎉
```bash
# Open the chat interface in your browser
open http://localhost

# The modern AI Support Bot interface should load!
```

---

## 🌟 What You Should See

### 🤖 Modern Chat Interface:
- **AI Support Assistant** header with bot avatar
- **Dark/Light mode toggle** (moon/sun icon)
- **Suggested questions** to get started
- **Modern chat bubbles** with smooth animations
- **Copy message** functionality (hover to see)

### 💬 Try These Sample Conversations:
- "How do I reset my password?" (FAQ response)
- "What are your business hours?" (FAQ response) 
- "Tell me about machine learning" (AI response)
- "I'm frustrated with your service!" (Will escalate)

---

## 🔧 Additional Access Points

### 📊 Monitoring & Analytics:
```bash
# API Documentation
open http://localhost:8000/docs

# Grafana Dashboards (Username: dakshith31@gmail.com, Password: Vids@1234)
open http://localhost:3001

# Prometheus Metrics
open http://localhost:9090
```

### 🛠️ API Testing:
```bash
# Test the chat API directly
curl -X POST http://localhost/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Get FAQ suggestions
curl http://localhost/api/v1/faq/suggestions?limit=5

# Health check
curl http://localhost/api/v1/health
```

---

## 🌍 Make It Public (Optional)

### Quick Ngrok Setup:
```bash
# 1. Sign up at ngrok.com (free)
# 2. Get your auth token from the dashboard
# 3. Configure ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE

# 4. Make your bot publicly accessible!
ngrok http 80

# You'll get a public URL like: https://abc123.ngrok-free.app
# Now anyone can access your AI Support Bot!
```

---

## 🚨 Troubleshooting

### "Command not found: docker-compose"
```bash
# Make sure Docker Desktop is installed and running
open -a Docker
# Wait for it to fully start, then try again
```

### "Port already in use"
```bash
# Stop any existing containers
docker-compose down

# Start fresh
docker-compose up --build -d
```

### "Cannot connect to the Docker daemon"
```bash
# Start Docker Desktop
open -a Docker

# Wait 1-2 minutes for Docker to fully start
# Look for Docker whale icon in your menu bar (top right)
```

### "Services not starting"
```bash
# Check detailed logs
docker-compose logs

# Restart specific service (example: backend)
docker-compose restart backend

# Nuclear option - rebuild everything
docker-compose down -v
docker-compose up --build -d
```

### "Chat interface not loading"
```bash
# Check if all services are running
docker-compose ps

# Check frontend logs
docker-compose logs frontend

# Try rebuilding frontend
docker-compose up --build -d frontend
```

---

## 🎛️ Management Commands

### Stop the Bot:
```bash
docker-compose down
```

### Restart the Bot:
```bash
docker-compose up -d
```

### View Logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
```

### Update and Rebuild:
```bash
docker-compose up --build -d
```

### Complete Reset (removes all data):
```bash
docker-compose down -v
docker-compose up --build -d
```

---

## 📱 Usage Tips

### 🎨 UI Features:
- **Dark Mode**: Click moon/sun icon in header
- **Copy Messages**: Hover over messages to see copy button
- **Clear Chat**: Click trash icon in header
- **Suggested Questions**: Click any suggestion to send

### 📊 Monitoring:
- **Watch Confidence Scores**: See how confident the AI is
- **Escalation Alerts**: System messages when human help is needed
- **Response Times**: Monitor in Grafana dashboards

### 🔌 API Integration:
- **Base URL**: `http://localhost/api/v1/`
- **Documentation**: `http://localhost:8000/docs`
- **Public URL**: Use ngrok for external access

---

## 🎯 Success Checklist

✅ Docker Desktop is running  
✅ All services show "Up" and "healthy"  
✅ Chat interface loads at http://localhost  
✅ Can send messages and get responses  
✅ Dark/light mode toggle works  
✅ API endpoints respond correctly  
✅ Monitoring dashboards accessible  

**Congratulations! Your AI Support Bot is now fully operational! 🤖✨**

---

## 📞 Need Help?

- **📖 Documentation**: Check `HOW_TO_RUN.md` for detailed info
- **🌐 External Access**: See `NGROK_SETUP.md` for public URLs  
- **📋 Changes**: Review `CHANGELOG.md` for latest features
- **🐳 Docker**: Ensure Docker Desktop is running and updated

**Happy chatting! 🚀**