# 🤖 AI Support Chatbot

A complete, production-ready AI-powered customer support chatbot built with Python, FastAPI, React, and Docker. Features intelligent FAQ matching, automatic escalation, session management, and comprehensive monitoring.

![AI Support Bot](https://img.shields.io/badge/AI-Support%20Bot-blue?style=for-the-badge&logo=robot)
![Version](https://img.shields.io/badge/Version-2.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

## ✨ Features

- 🧠 **Intelligent FAQ System** - High-confidence answers from curated knowledge base
- 🚨 **Smart Escalation** - Automatically escalates complex/legal issues to human agents
- 💬 **Session Management** - Persistent chat sessions with full conversation history
- 📊 **Analytics & Monitoring** - Grafana dashboards, Prometheus metrics, usage statistics
- 🔌 **REST API** - Complete API with auto-generated documentation
- 🎨 **Modern Frontend** - React-based chat interface with dark/light mode
- 🐳 **Docker Ready** - Full containerized deployment
- 🔐 **Production Ready** - Health checks, logging, error handling, rate limiting

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenRouter API key (for LLM functionality)

### 1. Clone the Repository
```bash
git clone https://github.com/DakshethG/AI_Support_Chatbot.git
cd AI_Support_Chatbot
```

### 2. Set Up Environment
```bash
# Create .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
```

### 3. Start Everything (One Command)
```bash
chmod +x start_bot.sh
./start_bot.sh
```

### 4. Access Your Chatbot
- **Chat Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001
- **Health Check**: http://localhost:8000/health

## 📱 Usage

### Chat Interface
Visit http://localhost:3000 to interact with the chatbot. It can handle:

- **FAQ Questions**: Return policy, shipping, order tracking, account management
- **Complex Issues**: Automatically escalates to human agents when needed
- **Follow-up Questions**: Maintains conversation context

### API Usage
```bash
# Send a chat message
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?", "session_id": "test"}'

# Get session history
curl "http://localhost:8000/api/v1/admin/sessions?limit=10"

# View usage statistics
curl "http://localhost:8000/api/v1/usage?days=7"
```

## 🛠️ Development

### Project Structure
```
ai-support-bot/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic
│   ├── scripts/            # Utility scripts
│   └── Dockerfile
├── frontend/               # React frontend
│   └── react-chat/
│       ├── src/
│       └── Dockerfile
├── infra/                  # Monitoring configuration
├── docker-compose.yml      # Container orchestration
├── start_bot.sh           # Complete launcher
├── bot_dashboard.sh       # Interactive dashboard
└── access.html           # Visual dashboard
```

### Available Scripts
- `./start_bot.sh` - Complete launcher (production)
- `./bot_dashboard.sh` - Interactive management dashboard
- `open access.html` - Visual dashboard in browser

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENROUTER_API_KEY=your_api_key_here

# Optional
DATABASE_URL=postgresql://user:password@db:5432/support_bot
REDIS_URL=redis://redis:6379/0
OPENROUTER_MODEL=nvidia/nemotron-nano-9b-v2:free
DEBUG=true
```

## 📊 Monitoring

### Grafana Dashboard (http://localhost:3001)
- **Login**: dakshith31@gmail.com / Vids@1234
- Request metrics, response times, error rates
- Session analytics and user engagement

### Prometheus Metrics (http://localhost:9090)
- Raw metrics collection
- Custom application metrics
- System resource monitoring

## 🧪 Testing

### Test the Chat System
```bash
# FAQ Test
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?", "session_id": "test"}'

# Escalation Test  
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to sue Amazon", "session_id": "escalation-test"}'
```

## 📝 API Documentation

Complete interactive API documentation is available at:
- **Development**: http://localhost:8000/docs
- **Alternative**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-----------|
| `/api/v1/chat` | POST | Send chat message |
| `/api/v1/admin/sessions` | GET | List chat sessions |
| `/api/v1/admin/session/{id}/transcript` | GET | Get session transcript |
| `/api/v1/usage` | GET | Usage statistics |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

## 🛐 Troubleshooting

### Common Issues

**Services not starting:**
```bash
docker-compose down -v
docker-compose up -d
```

**Frontend not accessible:**
- Check if running on http://localhost:3000
- Verify docker-compose.yml port mapping

**Rate limiting errors:**
- Add credits to OpenRouter account
- FAQ system works without LLM

### Logs
```bash
# View all logs
docker-compose logs

# Backend logs only
docker-compose logs -f backend

# Database logs
docker-compose logs -f postgres
```

## 🚀 Deployment

### Production Environment
```bash
# Production environment variables
ENVIRONMENT=production
LOG_LEVEL=INFO
OPENROUTER_API_KEY=your_production_key

# Deploy with docker-compose
docker-compose -f docker-compose.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Daksheth G** - *Initial work* - [@DakshethG](https://github.com/DakshethG)

---

## 🎯 Quick Commands Reference

```bash
# Start everything
./start_bot.sh

# Interactive dashboard
./bot_dashboard.sh

# Visual dashboard
open access.html

# Stop services
docker-compose down

# View status
docker-compose ps
```

**🌟 Star this repository if you found it helpful!**
- Bot avatar with personality
- Copy-to-clipboard functionality

### 📱 **Responsive Design**
- Mobile-first approach
- Touch-friendly interactions
- Adaptive layouts
- Cross-platform compatibility

---

## 📊 **Monitoring & Analytics**

### 🔍 **Real-Time Metrics**
- **Chat Volume**: Messages per hour/day
- **Response Times**: Average API response times
- **Confidence Scores**: AI confidence distribution
- **Escalation Rates**: Human handoff frequency
- **FAQ Performance**: Most/least popular questions

### 📈 **Business Analytics**
- **User Sessions**: Duration and engagement
- **Resolution Rates**: Successful vs escalated
- **Cost Tracking**: Token usage and API costs
- **Performance Trends**: Week-over-week improvements

---

## 🔒 **Security & Production**

### 🛡️ **Security Features**
- **Input Sanitization** - Prevents injection attacks
- **Rate Limiting** - IP-based request throttling
- **CORS Protection** - Configurable allowed origins
- **Secret Management** - Environment-based configuration
- **Audit Logging** - Comprehensive request tracking

### 🚀 **Production Ready**
- **Health Checks** for all services
- **Graceful Shutdowns** with proper cleanup
- **Error Handling** with user-friendly messages
- **Monitoring** with alerts and dashboards
- **Scalable Architecture** with containerization

---

## 🌍 **External Integration**

### 🔌 **API Integration**
Perfect for integrating with:
- **Websites** - Embed as chat widget
- **Mobile Apps** - RESTful API endpoints
- **Webhooks** - External service notifications
- **CRM Systems** - Customer data integration
- **Help Desk** - Ticket system integration

### 📱 **Multi-Channel Support**
- **Web Chat** - Built-in React interface
- **API Endpoints** - For custom integrations
- **Mobile Apps** - Responsive design
- **Third-party** - Webhook support

---

## 🤝 **Contributing**

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Make** changes and add tests
4. **Test**: Run `./start-bot.sh` and verify everything works
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Submit** pull request

---

## 🚨 **Troubleshooting**

### 🔧 **Common Issues**

**Docker not starting?**
```bash
# Make sure Docker Desktop is running
open -a Docker
# Wait for whale icon in menu bar
```

**Services not ready?**
```bash
# Check service status
docker-compose ps
# Wait 30-60 seconds for startup
```

**Chat not loading?**
```bash
# Check logs for errors
docker-compose logs frontend backend
# Try rebuilding
docker-compose up --build -d
```

**Need help?** Check our detailed guides:
- 🎯 [QUICK_START.md](./QUICK_START.md) - Beginner setup
- 📋 [HOW_TO_RUN.md](./HOW_TO_RUN.md) - Detailed management

---

## 📄 **License**

MIT License - feel free to use this in your projects!

---

## 🙏 **Acknowledgments**

- **OpenRouter** - For providing free AI model access
- **FastAPI** - For the excellent async framework  
- **React** - For the modern frontend framework
- **Docker** - For containerization magic
- **You** - For trying out this project! 🎉

---

<div align="center">

</div>
