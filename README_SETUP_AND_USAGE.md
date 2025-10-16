# AI Support Bot - Setup & Usage Guide

## Quick Start

### 1. Start the Application
```bash
# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 2. Access the Application
- **Frontend (User Interface)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Stop the Application
```bash
docker-compose down
```

## Environment Setup

### Prerequisites
- Docker and Docker Compose installed
- OpenRouter API key (for LLM functionality)

### Environment Configuration
Create `.env` file:
```bash
OPENROUTER_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@db:5432/support_bot
REDIS_URL=redis://redis:6379/0
```

## API Endpoints

### Chat API
```bash
# Send a message
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?", "session_id": "test-session"}'
```

### Session Management
```bash
# Get all sessions (admin)
curl "http://localhost:8000/api/v1/admin/sessions?limit=10"

# Get specific session transcript
curl "http://localhost:8000/api/v1/admin/session/{session_id}/transcript"

# Get session analytics
curl "http://localhost:8000/api/v1/admin/session/{session_id}/analytics"
```

### Usage Statistics
```bash
# Get usage for last 7 days
curl "http://localhost:8000/api/v1/usage?days=7"

# Get usage for specific date range
curl "http://localhost:8000/api/v1/usage?start_date=2024-01-01&end_date=2024-01-31"
```

### Health & Monitoring
```bash
# Health check
curl "http://localhost:8000/health"

# System metrics
curl "http://localhost:8000/metrics"
```

## Database Operations

### Reset FAQ Data
```bash
# Enter backend container
docker-compose exec backend bash

# Run FAQ reset script
python scripts/reset_faq_data.py
```

### Database Migrations
```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U user -d support_bot

# Common queries
SELECT * FROM faqs LIMIT 5;
SELECT * FROM chat_sessions ORDER BY created_at DESC LIMIT 10;
SELECT * FROM messages WHERE session_id = 'your_session_id';
```

## Testing the Chatbot

### FAQ Questions (Always Work)
```bash
# Return policy
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?", "session_id": "test-1"}'

# Shipping information
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the shipping options?", "session_id": "test-2"}'

# Order tracking
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I track my order?", "session_id": "test-3"}'
```

### Escalation Testing
```bash
# Should escalate (legal issues)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to sue Amazon", "session_id": "test-escalate"}'

# Should escalate (human request)
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to speak to a human", "session_id": "test-human"}'
```

## Logs and Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Backend Container Access
```bash
# Enter backend container
docker-compose exec backend bash

# Check Python environment
python --version
pip list

# Test database connection
python -c "from app.database import engine; print('DB Connected!' if engine else 'DB Failed!')"
```

## Common Issues & Solutions

### OpenRouter Rate Limit
```
Error: Rate limit exceeded: free-models-per-day
Solution: Add credits to OpenRouter account or wait for daily reset
Workaround: FAQ system still works without LLM
```

### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose exec backend alembic upgrade head
docker-compose up -d
```

### Frontend Not Loading
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# Kill processes if needed
kill -9 <PID>
```

## Development Commands

### Code Quality
```bash
# Enter backend container
docker-compose exec backend bash

# Run linting
ruff check .
ruff format .

# Run tests
pytest

# Type checking
mypy .
```

### Database Schema Updates
```bash
# After modifying models
docker-compose exec backend alembic revision --autogenerate -m "add new table"
docker-compose exec backend alembic upgrade head
```

## Production Deployment

### Environment Variables
```bash
# Production .env
OPENROUTER_API_KEY=prod_key_here
DATABASE_URL=postgresql://user:secure_password@prod-db:5432/support_bot
REDIS_URL=redis://prod-redis:6379/0
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Health Monitoring
```bash
# Set up monitoring for these endpoints
curl "http://your-domain.com/health"
curl "http://your-domain.com/metrics"
```

## API Response Examples

### Successful FAQ Response
```json
{
  "answer": "Our return policy allows you to return products within 30 days of purchase for a full refund, provided they are in their original condition and packaging.",
  "confidence": 0.95,
  "escalate": false,
  "suggested_actions": ["check_faq", "contact_support"],
  "session_id": "test-session"
}
```

### Escalation Response
```json
{
  "answer": "I'm connecting you with a human representative who can better assist with this request.",
  "confidence": 0.0,
  "escalate": true,
  "suggested_actions": ["human_review", "technical_support"],
  "session_id": "test-session"
}
```

### Usage Statistics Response
```json
{
  "period_days": 7,
  "total_requests": 150,
  "successful_requests": 145,
  "success_rate": 0.97,
  "total_tokens": 50000,
  "avg_response_time_ms": 1200.0,
  "total_cost_estimate": 2.50
}
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all services |
| `docker-compose logs -f backend` | View backend logs |
| `docker-compose exec backend bash` | Enter backend container |
| `curl http://localhost:8000/health` | Check API health |
| `curl http://localhost:3000` | Check frontend |
| `docker-compose down` | Stop all services |
| `docker-compose down -v` | Stop and remove volumes |

**Frontend**: http://localhost:3000  
**Backend API**: http://localhost:8000  
**Docs**: http://localhost:8000/docs