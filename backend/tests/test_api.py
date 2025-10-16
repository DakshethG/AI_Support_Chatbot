"""
Test cases for FastAPI endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "AI Support Bot is running"
        assert response.json()["version"] == "1.0.0"
    
    def test_health_endpoint(self, test_client: TestClient):
        """Test health check endpoint"""
        with patch("app.openrouter_client") as mock_client:
            # Mock the health check
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
            
            response = test_client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "model" in data
            assert "database" in data
            assert "cache" in data
            assert "timestamp" in data


class TestChatEndpoint:
    """Test chat endpoint functionality"""
    
    @patch("app.openrouter_client")
    def test_chat_basic_request(self, mock_client, test_client: TestClient, sample_chat_request, mock_openrouter_response):
        """Test basic chat request"""
        # Setup mocks
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Mock router
        with patch("app.ChatRouter") as mock_router_class:
            mock_router = mock_router_class.return_value
            mock_router.route_message = AsyncMock(return_value=(mock_openrouter_response, None))
            
            response = test_client.post("/api/v1/chat", json=sample_chat_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert "answer" in data
            assert "confidence" in data
            assert "escalate" in data
            assert "suggested_actions" in data
            assert "session_id" in data
            
            assert data["answer"] == mock_openrouter_response.answer
            assert data["confidence"] == mock_openrouter_response.confidence
            assert data["escalate"] == mock_openrouter_response.escalate
    
    def test_chat_invalid_message(self, test_client: TestClient):
        """Test chat with invalid message"""
        response = test_client.post("/api/v1/chat", json={
            "message": "",  # Empty message
            "session_id": None
        })
        assert response.status_code == 422  # Validation error
    
    def test_chat_message_too_long(self, test_client: TestClient):
        """Test chat with message that's too long"""
        long_message = "x" * 2001  # Longer than max length
        response = test_client.post("/api/v1/chat", json={
            "message": long_message,
            "session_id": None
        })
        assert response.status_code == 422  # Validation error
    
    @patch("app.openrouter_client")
    def test_chat_with_escalation(self, mock_client, test_client: TestClient, mock_openrouter_response):
        """Test chat request that triggers escalation"""
        # Create escalation response
        escalation_response = mock_openrouter_response
        escalation_response.escalate = True
        escalation_response.confidence = 0.3
        
        # Setup mocks
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("app.ChatRouter") as mock_router_class:
            mock_router = mock_router_class.return_value
            mock_router.route_message = AsyncMock(return_value=(escalation_response, None))
            
            response = test_client.post("/api/v1/chat", json={
                "message": "I want to cancel my subscription!",
                "session_id": None
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["escalate"] is True


class TestSessionEndpoints:
    """Test session management endpoints"""
    
    def test_create_session(self, test_client: TestClient):
        """Test session creation"""
        response = test_client.post("/api/v1/session", json={
            "user_id": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["user_id"] == "test-user"
        assert "created_at" in data
        assert "status" in data
        assert data["total_messages"] == 0
    
    def test_create_session_no_user(self, test_client: TestClient):
        """Test session creation without user"""
        response = test_client.post("/api/v1/session", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["user_id"] is None
    
    def test_get_session(self, test_client: TestClient, test_db):
        """Test getting session by ID"""
        from models.db_models import Session as DBSession
        
        # Create a test session
        session = DBSession(id="test-session", user_id="test-user")
        test_db.add(session)
        test_db.commit()
        
        response = test_client.get("/api/v1/session/test-session")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "test-session"
        assert data["user_id"] == "test-user"
    
    def test_get_nonexistent_session(self, test_client: TestClient):
        """Test getting non-existent session"""
        response = test_client.get("/api/v1/session/nonexistent")
        assert response.status_code == 404


class TestEscalationEndpoints:
    """Test escalation endpoints"""
    
    def test_create_escalation(self, test_client: TestClient, test_db):
        """Test creating manual escalation"""
        from models.db_models import Session as DBSession
        
        # Create a test session first
        session = DBSession(id="test-session", user_id="test-user")
        test_db.add(session)
        test_db.commit()
        
        response = test_client.post("/api/v1/escalate", json={
            "session_id": "test-session",
            "reason": "User needs human assistance",
            "requested_by": "test-user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "escalation_id" in data
        assert data["status"] == "created"
    
    def test_escalate_nonexistent_session(self, test_client: TestClient):
        """Test escalating non-existent session"""
        response = test_client.post("/api/v1/escalate", json={
            "session_id": "nonexistent",
            "reason": "Test escalation"
        })
        
        assert response.status_code == 404


class TestFAQEndpoints:
    """Test FAQ endpoints"""
    
    def test_search_faq_all(self, test_client: TestClient):
        """Test searching all FAQ items"""
        response = test_client.get("/api/v1/faq")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0  # Should have sample FAQ items
        
        # Check structure of first item
        if data:
            faq = data[0]
            assert "id" in faq
            assert "question" in faq
            assert "answer" in faq
            assert "category" in faq
            assert "tags" in faq
    
    def test_search_faq_with_query(self, test_client: TestClient):
        """Test searching FAQ with query"""
        response = test_client.get("/api/v1/faq?query=password")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_faq_with_category(self, test_client: TestClient):
        """Test searching FAQ by category"""
        response = test_client.get("/api/v1/faq?category=account")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_suggested_questions(self, test_client: TestClient):
        """Test getting suggested questions"""
        response = test_client.get("/api/v1/faq/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5  # Default limit
        
        # Check structure
        if data:
            suggestion = data[0]
            assert "id" in suggestion
            assert "question" in suggestion
            assert "category" in suggestion


class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_list_sessions(self, test_client: TestClient, test_db):
        """Test listing sessions"""
        from models.db_models import Session as DBSession
        
        # Create test sessions
        for i in range(3):
            session = DBSession(id=f"test-session-{i}")
            test_db.add(session)
        test_db.commit()
        
        response = test_client.get("/api/v1/admin/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 3
    
    def test_get_session_transcript(self, test_client: TestClient, test_db):
        """Test getting session transcript"""
        from models.db_models import Session as DBSession, Message
        
        # Create test session and messages
        session = DBSession(id="test-session")
        test_db.add(session)
        test_db.commit()
        
        # Add some messages
        msg1 = Message(session_id="test-session", role="user", content="Hello")
        msg2 = Message(session_id="test-session", role="assistant", content="Hi there!")
        test_db.add_all([msg1, msg2])
        test_db.commit()
        
        response = test_client.get("/api/v1/admin/session/test-session/transcript")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == "test-session"
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["content"] == "Hi there!"
    
    def test_get_usage_stats(self, test_client: TestClient, test_db):
        """Test getting usage statistics"""
        from models.db_models import UsageLog
        
        # Add some usage logs
        log = UsageLog(
            model="test-model",
            total_tokens=100,
            success=True
        )
        test_db.add(log)
        test_db.commit()
        
        response = test_client.get("/api/v1/usage")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_days" in data
        assert "total_requests" in data
        assert "success_rate" in data
        assert "total_tokens" in data


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_disabled_without_redis(self, test_client: TestClient):
        """Test that rate limiting is disabled without Redis"""
        # Make multiple requests - should all succeed since Redis is not configured
        for _ in range(20):
            response = test_client.get("/")
            assert response.status_code == 200