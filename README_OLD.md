# AI Support Bot

An intelligent customer support bot powered by OpenRouter and the **nvidia/nemotron-nano-9b-v2:free** model. This production-ready solution features automatic FAQ matching, confidence-based escalation, session management, and comprehensive monitoring.

## 🚀 Features

- **Smart Routing**: FAQ matching with fuzzy search + LLM fallback
- **Confidence-Based Escalation**: Automatic human handoff for low-confidence responses
- **Session Management**: Persistent conversation tracking with context
- **Real-time Chat UI**: Clean React interface with typing indicators
- **Background Processing**: Celery workers for summaries and analytics
- **Monitoring**: Prometheus metrics + Grafana dashboards
- **Rate Limiting**: Redis-based protection against abuse
- **Production Ready**: Docker, health checks, structured logging

## 🏗️ Architecture

```
Frontend (React) → FastAPI Backend → OpenRouter API (nvidia/nemotron-nano-9b-v2:free)
                        ↓
            PostgreSQL + Redis + Celery Workers
```

## 📋 Requirements

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenRouter API Key

## ⚡ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-support-bot
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your OpenRouter API key:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Start with Docker Compose

```bash
docker-compose up --build
```

### 4. Access the Application

- **Chat Interface**: http://localhost (port 80)
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## 🛠️ Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
python -c "from models.db_models import Database; Database('sqlite:///ai_support.db').create_tables()"

# Start development server
python app.py
```

### Frontend Development

```bash
cd frontend/react-chat
npm install
npm start
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

## 📚 API Documentation

### Core Endpoints

#### Chat Endpoint
```http
POST /api/v1/chat
Content-Type: application/json

{
    "message": "How do I reset my password?",
    "session_id": "optional-session-id",
    "user_id": "optional-user-id",
    "metadata": {"source": "web"}
}
```

**Response:**
```json
{
    "answer": "To reset your password, click 'Forgot Password'...",
    "confidence": 0.95,
    "escalate": false,
    "suggested_actions": ["check_faq", "contact_support"],
    "session_id": "generated-session-id"
}
```

#### Session Management
```http
# Create session
POST /api/v1/session
{
    "user_id": "user-123",
    "metadata": {"channel": "web"}
}

# Get session
GET /api/v1/session/{session_id}
```

#### Manual Escalation
```http
POST /api/v1/escalate
{
    "session_id": "session-id",
    "reason": "User needs human assistance",
    "requested_by": "user-id"
}
```

#### FAQ Search
```http
# Search FAQ
GET /api/v1/faq?query=password&category=account&limit=10

# Get suggestions
GET /api/v1/faq/suggestions?limit=5
```

### Admin Endpoints

#### Session Management
```http
# List sessions
GET /api/v1/admin/sessions?page=1&limit=50&status=active

# Get transcript
GET /api/v1/admin/session/{session_id}/transcript
```

#### Usage Analytics
```http
GET /api/v1/usage?days=7
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | - | **Required** OpenRouter API key |
| `OPENROUTER_MODEL` | `nvidia/nemotron-nano-9b-v2:free` | Model to use |
| `DATABASE_URL` | `sqlite:///ai_support.db` | Database connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CONFIDENCE_THRESHOLD` | `0.6` | Min confidence before escalation |
| `MAX_CONTEXT_MESSAGES` | `6` | Messages to include in context |
| `RATE_LIMIT_REQUESTS` | `10` | Requests per window |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |

### Business Rules

The system applies these rules automatically:

1. **Confidence Threshold**: Responses below 60% confidence → escalate
2. **Keyword Escalation**: Messages containing "cancel", "refund", "billing" → escalate
3. **Short Response**: Responses under 10 characters → escalate
4. **FAQ Priority**: Exact keyword matches bypass LLM

## 🎯 Router Logic Flow

```
User Message
    ↓
1. Sanitize & validate input
    ↓
2. Search FAQ (exact + fuzzy matching)
    ↓
3. If FAQ match → return FAQ answer (high confidence)
    ↓
4. If no match → build context from recent messages
    ↓
5. Call OpenRouter with structured prompt
    ↓
6. Parse JSON response (answer, confidence, escalate, actions)
    ↓
7. Apply business rules (confidence threshold, keywords)
    ↓
8. Save to database & return response
    ↓
9. If escalate=true → create escalation ticket
```

## 📊 Monitoring & Analytics

### Metrics Available

- **Request Metrics**: Total requests, success rate, response times
- **Model Metrics**: Token usage, confidence scores, escalation rates
- **Business Metrics**: Session duration, FAQ hit rates, resolution rates

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin) for:

- Real-time chat metrics
- Model performance tracking
- Cost and usage analysis
- Error rate monitoring

### Health Checks

```http
GET /health
```

Returns comprehensive status of:
- Database connectivity
- Redis cache status
- OpenRouter API health
- Overall system status

## 🔒 Security Features

- **Input Sanitization**: Message length limits, prompt injection protection
- **Rate Limiting**: IP-based request throttling
- **CORS Protection**: Configurable allowed origins
- **Secrets Management**: Environment-based API key storage
- **Audit Logging**: Structured logs for all interactions

## 🚀 Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Set up external services**:
   - PostgreSQL database
   - Redis cluster
   - Load balancer

3. **Deploy with Kubernetes** (manifests included):
```bash
kubectl apply -f infra/k8s/
```

4. **Or use Docker Compose** with production overrides:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling Considerations

- **Backend**: Scale FastAPI pods based on CPU/memory
- **Workers**: Scale Celery workers based on queue length
- **Database**: Use read replicas for analytics queries
- **Cache**: Use Redis cluster for high availability

## 🧪 Testing

### Run All Tests
```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing with real database
- **Mock Tests**: OpenRouter API interaction testing

### Test Coverage

The test suite covers:
- All API endpoints
- OpenRouter client functionality
- Router logic and business rules
- Database models and operations
- Error handling and edge cases

## 📈 Performance

### Benchmarks

- **Response Time**: < 2s average (including LLM call)
- **Throughput**: 100+ requests/second per backend pod
- **FAQ Matching**: < 50ms for fuzzy search
- **Database**: Optimized indexes for fast lookups

### Optimization Tips

1. **FAQ Caching**: Frequently accessed FAQs cached in Redis
2. **Connection Pooling**: Database connections pooled for efficiency
3. **Async Processing**: Non-blocking I/O throughout
4. **Background Tasks**: Heavy operations moved to Celery workers

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Ensure tests pass: `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Submit pull request

## 📋 Roadmap

- [ ] Vector database integration for semantic FAQ search
- [ ] Multi-language support with translation
- [ ] Voice chat interface
- [ ] Advanced analytics and reporting
- [ ] A/B testing framework for responses
- [ ] Integration with CRM systems
- [ ] Mobile app support

## ⚠️ Troubleshooting

### Common Issues

**"OpenRouter API key not found"**
```bash
# Ensure API key is set
echo $OPENROUTER_API_KEY
# Or check .env file
```

**"Database connection failed"**
```bash
# Check PostgreSQL is running
docker-compose ps postgres
# Check connection string
```

**"Redis connection failed"**
```bash
# Check Redis is running
docker-compose ps redis
# Test connection
redis-cli ping
```

**"Chat not working"**
```bash
# Check backend health
curl http://localhost:8000/health
# Check logs
docker-compose logs backend
```

### Debug Mode

Enable debug mode for detailed logging:
```bash
DEBUG=true python app.py
```

## 📞 Support

- **Documentation**: Check this README and API docs at `/docs`
- **Issues**: Create GitHub issue with reproduction steps
- **Discussions**: Use GitHub Discussions for questions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenRouter** for providing access to nvidia/nemotron-nano-9b-v2:free model
- **FastAPI** for the excellent async web framework
- **React** for the frontend framework
- **Contributors** who helped improve this project

---

**Built with ❤️ for better customer support experiences**