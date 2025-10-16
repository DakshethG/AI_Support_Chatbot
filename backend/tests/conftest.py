"""
Pytest configuration and fixtures for AI Support Bot tests
"""

import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app import app, get_db_session
from models.db_models import Base, Database, init_faq_data
from openrouter_client import OpenRouterClient, OpenRouterConfig, OpenRouterResponse, OpenRouterUsage


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///./test_ai_support.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db() -> Generator:
    """Create a test database session"""
    # Create test engine and session
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    
    try:
        # Initialize test data
        init_faq_data(db)
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(test_db) -> TestClient:
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openrouter_response():
    """Create a mock OpenRouter response"""
    return OpenRouterResponse(
        answer="This is a test response from the AI.",
        confidence=0.85,
        escalate=False,
        suggested_actions=["contact_support"],
        usage=OpenRouterUsage(
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=25
        ),
        raw_response='{"answer": "This is a test response from the AI.", "confidence": 0.85, "escalate": false, "suggested_actions": ["contact_support"]}'
    )


@pytest.fixture
def mock_openrouter_client(mock_openrouter_response):
    """Create a mock OpenRouter client"""
    class MockOpenRouterClient:
        def __init__(self):
            self.response = mock_openrouter_response
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        
        async def chat_completion(self, messages, temperature=0.15, max_tokens=512):
            return self.response
        
        async def health_check(self):
            return {
                "status": "healthy",
                "model": "nvidia/nemotron-nano-9b-v2:free",
                "response_received": True,
                "confidence": 0.85
            }
    
    return MockOpenRouterClient()


@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {
        "message": "How do I reset my password?",
        "session_id": None,
        "user_id": None,
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_session_data():
    """Sample session data"""
    return {
        "id": "test-session-123",
        "user_id": "test-user-456",
        "metadata": {"test": True}
    }


@pytest.fixture
def sample_faq_data():
    """Sample FAQ data for testing"""
    return {
        "question": "Test question?",
        "answer": "Test answer.",
        "category": "test",
        "tags": ["test", "sample"],
        "keywords": ["test", "question", "sample"],
        "priority": 5,
        "active": True
    }


@pytest.fixture
def sample_user_data():
    """Sample user data"""
    return {
        "id": "test-user-123",
        "name": "Test User",
        "email": "test@example.com",
        "role": "user"
    }


@pytest.fixture
def sample_escalation_data():
    """Sample escalation data"""
    return {
        "session_id": "test-session-123",
        "reason": "User requested human assistance",
        "requested_by": "test-user-123",
        "metadata": {"priority": "high"}
    }