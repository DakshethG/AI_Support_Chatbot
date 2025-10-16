"""
AI Support Bot - FastAPI Application
Main application with all REST endpoints
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models.db_models import Base, Database, init_faq_data, User, Session as DBSession, Message, Escalation, FAQItem, UsageLog
from openrouter_client import create_openrouter_client, OpenRouterClient
from router import ChatRouter

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
chat_requests_total = Counter('chat_requests_total', 'Total chat requests', ['status'])
chat_response_time = Histogram('chat_response_time_seconds', 'Chat response time')
faq_matches_total = Counter('faq_matches_total', 'Total FAQ matches')
escalations_total = Counter('escalations_total', 'Total escalations created')
confidence_scores = Histogram('confidence_scores', 'LLM confidence scores')
active_sessions = Gauge('active_sessions_total', 'Number of active chat sessions')

# Global variables
db: Database = None
redis_client: redis.Redis = None
openrouter_client: OpenRouterClient = None

# Pydantic models for API
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    escalate: bool
    suggested_actions: List[str] = []
    session_id: str

class SessionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    id: str
    user_id: Optional[str]
    created_at: datetime
    last_active_at: datetime
    status: str
    total_messages: int

class EscalationRequest(BaseModel):
    session_id: str
    reason: str
    requested_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class FAQResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: Optional[str]
    tags: List[str] = []

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    confidence: Optional[float] = None

class SessionTranscriptResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]
    escalations: List[Dict[str, Any]] = []

class HealthResponse(BaseModel):
    status: str
    model: str
    database: str
    cache: str
    timestamp: datetime

# Rate limiting using Redis
class RateLimiter:
    def __init__(self, redis_client: redis.Redis, requests: int = 10, window: int = 60):
        self.redis = redis_client
        self.requests = requests
        self.window = window

    async def is_allowed(self, identifier: str) -> bool:
        key = f"rate_limit:{identifier}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.window)
        return current <= self.requests

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, openrouter_client
    
    logger.info("Starting AI Support Bot application")
    
    # Initialize database
    database_url = os.getenv("DATABASE_URL", "sqlite:///ai_support.db")
    db = Database(database_url)
    
    # Create tables if they don't exist
    try:
        db.create_tables()
        logger.info("Database tables created/verified")
        
        # Initialize FAQ data
        with next(db.get_session()) as db_session:
            init_faq_data(db_session)
            
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise
    
    # Initialize Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning("Redis connection failed, continuing without cache", error=str(e))
        redis_client = None
    
    # Initialize OpenRouter client
    try:
        openrouter_client = create_openrouter_client()
        # Test the connection
        async with openrouter_client:
            health = await openrouter_client.health_check()
            logger.info("OpenRouter client initialized", health=health)
    except Exception as e:
        logger.error("OpenRouter client initialization failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Support Bot application")
    if redis_client:
        await redis_client.close()
    if openrouter_client:
        await openrouter_client.session.aclose()

# Create FastAPI app
app = FastAPI(
    title="AI Support Bot",
    description="AI-powered customer support bot using OpenRouter and nvidia/nemotron-nano-9b-v2:free",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_db_session():
    """Get database session"""
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_rate_limiter():
    """Get rate limiter instance"""
    if redis_client:
        return RateLimiter(redis_client, 
                          requests=int(os.getenv("RATE_LIMIT_REQUESTS", 10)),
                          window=int(os.getenv("RATE_LIMIT_WINDOW", 60)))
    return None

async def check_rate_limit(request: Request, rate_limiter = Depends(get_rate_limiter)):
    """Check rate limit for the request"""
    if not rate_limiter:
        return True
    
    # Use IP address as identifier (could also use user_id if authenticated)
    identifier = request.client.host
    allowed = await rate_limiter.is_allowed(identifier)
    
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return True

# Utility functions
def create_or_update_session(db_session: Session, session_id: str, user_id: Optional[str] = None) -> DBSession:
    """Create or update a chat session"""
    session = db_session.query(DBSession).filter(DBSession.id == session_id).first()
    
    if not session:
        session = DBSession(
            id=session_id,
            user_id=user_id,
            meta_data={}
        )
        db_session.add(session)
    else:
        session.last_active_at = datetime.utcnow()
        if user_id:
            session.user_id = user_id
    
    db_session.commit()
    return session

def save_message(
    db_session: Session, 
    session_id: str, 
    role: str, 
    content: str, 
    confidence: Optional[float] = None,
    escalate_flag: bool = False,
    suggested_actions: List[str] = None,
    tokens_used: int = 0
) -> Message:
    """Save a message to the database"""
    message = Message(
        session_id=session_id,
        role=role,
        content=content,
        confidence=confidence,
        escalate_flag=escalate_flag,
        suggested_actions=suggested_actions or [],
        tokens_used=tokens_used,
    )
    
    db_session.add(message)
    
    # Update session stats
    session = db_session.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        session.total_messages += 1
        session.total_tokens_used += tokens_used
        session.last_active_at = datetime.utcnow()
    
    db_session.commit()
    return message

def log_usage(
    db_session: Session,
    session_id: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    response_time_ms: int,
    success: bool,
    error_message: Optional[str] = None
) -> UsageLog:
    """Log API usage"""
    usage_log = UsageLog(
        session_id=session_id,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        total_tokens=tokens_in + tokens_out,
        response_time_ms=response_time_ms,
        success=success,
        error_message=error_message,
    )
    
    db_session.add(usage_log)
    db_session.commit()
    return usage_log

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Health check endpoint"""
    return {"message": "AI Support Bot is running", "version": "1.0.0"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        generate_latest(), 
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/health", response_model=HealthResponse)
async def health_check(db_session: Session = Depends(get_db_session)):
    """Comprehensive health check"""
    health_status = "healthy"
    
    # Check database
    db_status = "healthy"
    try:
        db_session.execute("SELECT 1")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        health_status = "degraded"
    
    # Check Redis
    cache_status = "healthy"
    if redis_client:
        try:
            await redis_client.ping()
        except Exception as e:
            cache_status = f"unhealthy: {str(e)}"
            health_status = "degraded"
    else:
        cache_status = "disabled"
    
    # Check OpenRouter
    model_status = "unknown"
    try:
        async with openrouter_client:
            health = await openrouter_client.health_check()
            model_status = health.get("status", "unknown")
            if model_status != "healthy":
                health_status = "degraded"
    except Exception as e:
        model_status = f"unhealthy: {str(e)}"
        health_status = "degraded"
    
    return HealthResponse(
        status=health_status,
        model=model_status,
        database=db_status,
        cache=cache_status,
        timestamp=datetime.utcnow()
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db_session),
    rate_limit_ok: bool = Depends(check_rate_limit)
):
    """Main chat endpoint"""
    start_time = datetime.utcnow()
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid4())
    
    logger.info("Chat request received", 
               session_id=session_id, 
               user_id=request.user_id, 
               message_length=len(request.message))
    
    try:
        # Create/update session
        session = create_or_update_session(db_session, session_id, request.user_id)
        
        # Save user message
        user_message = save_message(
            db_session, 
            session_id, 
            "user", 
            request.message
        )
        
        # Create router and process message
        async with openrouter_client:
            router = ChatRouter(db_session, openrouter_client)
            response, faq_match = await router.route_message(
                session_id=session_id,
                message=request.message,
                user_id=request.user_id,
                metadata=request.metadata
            )
        
        # Save assistant response
        assistant_message = save_message(
            db_session,
            session_id,
            "assistant",
            response.answer,
            confidence=response.confidence,
            escalate_flag=response.escalate,
            suggested_actions=response.suggested_actions,
            tokens_used=response.usage.total_tokens if response.usage else 0
        )
        
        # Log usage in background
        if response.usage:
            background_tasks.add_task(
                log_usage,
                db_session,
                session_id,
                os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-nano-9b-v2:free"),
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                int((datetime.utcnow() - start_time).total_seconds() * 1000),
                True
            )
        
        # Create escalation if needed
        if response.escalate:
            escalation = Escalation(
                session_id=session_id,
                reason=f"Low confidence ({response.confidence}) or escalation requested",
                meta_data={"faq_match": faq_match.id if faq_match else None}
            )
            db_session.add(escalation)
            db_session.commit()
            
            logger.info("Escalation created", 
                       session_id=session_id, 
                       escalation_id=escalation.id)
        
        logger.info("Chat request completed", 
                   session_id=session_id, 
                   confidence=response.confidence,
                   escalate=response.escalate,
                   faq_match=faq_match.id if faq_match else None)
        
        # Update metrics
        chat_requests_total.labels(status='success').inc()
        confidence_scores.observe(response.confidence)
        if faq_match:
            faq_matches_total.inc()
        if response.escalate:
            escalations_total.inc()
        
        return ChatResponse(
            answer=response.answer,
            confidence=response.confidence,
            escalate=response.escalate,
            suggested_actions=response.suggested_actions,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error("Chat request failed", 
                    session_id=session_id, 
                    error=str(e))
        
        # Log failed usage
        background_tasks.add_task(
            log_usage,
            db_session,
            session_id,
            os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-nano-9b-v2:free"),
            0, 0,
            int((datetime.utcnow() - start_time).total_seconds() * 1000),
            False,
            str(e)
        )
        
        # Update error metrics
        chat_requests_total.labels(status='error').inc()
        
        # Return error response
        return ChatResponse(
            answer="I'm sorry, I'm experiencing technical difficulties. Please try again later or contact support.",
            confidence=0.0,
            escalate=True,
            suggested_actions=["retry", "contact_support"],
            session_id=session_id
        )

@app.post("/api/v1/session", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    db_session: Session = Depends(get_db_session)
):
    """Create a new chat session"""
    session_id = str(uuid4())
    session = create_or_update_session(db_session, session_id, request.user_id)
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        created_at=session.created_at,
        last_active_at=session.last_active_at,
        status=session.status,
        total_messages=session.total_messages
    )

@app.get("/api/v1/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db_session: Session = Depends(get_db_session)
):
    """Get session information"""
    session = db_session.query(DBSession).filter(DBSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        created_at=session.created_at,
        last_active_at=session.last_active_at,
        status=session.status,
        total_messages=session.total_messages
    )

@app.post("/api/v1/escalate")
async def create_escalation(
    request: EscalationRequest,
    db_session: Session = Depends(get_db_session)
):
    """Create a manual escalation"""
    # Verify session exists
    session = db_session.query(DBSession).filter(DBSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    escalation = Escalation(
        session_id=request.session_id,
        reason=request.reason,
        created_by=request.requested_by,
        meta_data=request.metadata or {}
    )
    
    db_session.add(escalation)
    session.status = "escalated"
    db_session.commit()
    
    logger.info("Manual escalation created", 
               session_id=request.session_id, 
               escalation_id=escalation.id)
    
    return {"escalation_id": escalation.id, "status": "created"}

@app.get("/api/v1/faq", response_model=List[FAQResponse])
async def search_faq(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10,
    db_session: Session = Depends(get_db_session)
):
    """Search FAQ items"""
    query_obj = db_session.query(FAQItem).filter(FAQItem.active == True)
    
    if category:
        query_obj = query_obj.filter(FAQItem.category == category)
    
    if query:
        # Simple text search - could be improved with full-text search
        query_obj = query_obj.filter(
            FAQItem.question.contains(query) | 
            FAQItem.answer.contains(query)
        )
    
    faq_items = query_obj.order_by(
        FAQItem.priority.desc(), 
        FAQItem.usage_count.desc()
    ).limit(limit).all()
    
    return [
        FAQResponse(
            id=faq.id,
            question=faq.question,
            answer=faq.answer,
            category=faq.category,
            tags=faq.tags or []
        )
        for faq in faq_items
    ]

@app.get("/api/v1/faq/suggestions", response_model=List[Dict[str, str]])
async def get_suggested_questions(
    limit: int = 5,
    db_session: Session = Depends(get_db_session)
):
    """Get suggested questions for the UI"""
    router = ChatRouter(db_session, None)  # Don't need OpenRouter client for this
    return router.get_suggested_questions(limit)

# Admin endpoints
@app.get("/api/v1/admin/sessions")
async def list_sessions(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    db_session: Session = Depends(get_db_session)
):
    """List sessions with pagination"""
    query_obj = db_session.query(DBSession)
    
    if status:
        query_obj = query_obj.filter(DBSession.status == status)
    
    offset = (page - 1) * limit
    sessions = query_obj.order_by(
        DBSession.last_active_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "status": s.status,
            "created_at": s.created_at,
            "last_active_at": s.last_active_at,
            "total_messages": s.total_messages,
            "total_tokens": s.total_tokens_used,
        }
        for s in sessions
    ]

@app.get("/api/v1/admin/session/{session_id}/transcript", response_model=SessionTranscriptResponse)
async def get_session_transcript(
    session_id: str,
    db_session: Session = Depends(get_db_session)
):
    """Get full session transcript"""
    session = db_session.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db_session.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()
    
    escalations = db_session.query(Escalation).filter(
        Escalation.session_id == session_id
    ).all()
    
    return SessionTranscriptResponse(
        session_id=session_id,
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                confidence=msg.confidence
            )
            for msg in messages
        ],
        escalations=[
            {
                "id": esc.id,
                "reason": esc.reason,
                "status": esc.status,
                "created_at": esc.created_at.isoformat(),
            }
            for esc in escalations
        ]
    )

@app.get("/api/v1/usage")
async def get_usage_stats(
    days: int = 7,
    db_session: Session = Depends(get_db_session)
):
    """Get usage statistics"""
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    usage_logs = db_session.query(UsageLog).filter(
        UsageLog.created_at >= start_date
    ).all()
    
    total_requests = len(usage_logs)
    successful_requests = len([u for u in usage_logs if u.success])
    total_tokens = sum(u.total_tokens for u in usage_logs)
    avg_response_time = sum(u.response_time_ms or 0 for u in usage_logs) / total_requests if total_requests > 0 else 0
    
    return {
        "period_days": days,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
        "total_tokens": total_tokens,
        "avg_response_time_ms": avg_response_time,
        "total_cost_estimate": sum(u.cost_estimate for u in usage_logs),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=bool(os.getenv("DEBUG", False)),
    )