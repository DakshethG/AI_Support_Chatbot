"""
Test cases for OpenRouter client
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx
import json

from openrouter_client import (
    OpenRouterClient, 
    OpenRouterConfig, 
    ChatMessage, 
    OpenRouterResponse, 
    create_openrouter_client
)


class TestOpenRouterConfig:
    """Test OpenRouter configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = OpenRouterConfig(api_key="test-key")
        
        assert config.api_key == "test-key"
        assert config.model == "nvidia/nemotron-nano-9b-v2:free"
        assert config.base_url == "https://openrouter.ai/api/v1/chat/completions"
        assert config.timeout == 30.0
        assert config.max_retries == 3


class TestChatMessage:
    """Test ChatMessage model"""
    
    def test_chat_message_creation(self):
        """Test creating chat message"""
        msg = ChatMessage(role="user", content="Hello")
        
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestOpenRouterClient:
    """Test OpenRouter client functionality"""
    
    @pytest.fixture
    def client_config(self):
        """Create test configuration"""
        return OpenRouterConfig(api_key="test-api-key")
    
    @pytest.fixture
    def client(self, client_config):
        """Create test client"""
        return OpenRouterClient(client_config)
    
    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.config.api_key == "test-api-key"
        assert client.config.model == "nvidia/nemotron-nano-9b-v2:free"
    
    def test_build_headers(self, client):
        """Test building request headers"""
        headers = client._build_headers()
        
        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers
    
    def test_build_payload(self, client):
        """Test building request payload"""
        messages = [
            ChatMessage(role="system", content="You are helpful"),
            ChatMessage(role="user", content="Hello")
        ]
        
        payload = client._build_payload(messages, temperature=0.2, max_tokens=100)
        
        assert payload["model"] == "nvidia/nemotron-nano-9b-v2:free"
        assert payload["temperature"] == 0.2
        assert payload["max_tokens"] == 100
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["content"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_successful_request(self, client):
        """Test successful API request"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"answer": "Hello!", "confidence": 0.9, "escalate": false, "suggested_actions": ["continue"]}'
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            messages = [ChatMessage(role="user", content="Hello")]
            response = await client.chat_completion(messages)
            
            assert response.answer == "Hello!"
            assert response.confidence == 0.9
            assert response.escalate is False
            assert "continue" in response.suggested_actions
            assert response.usage.total_tokens == 15
    
    @pytest.mark.asyncio
    async def test_request_with_invalid_json_response(self, client):
        """Test handling invalid JSON response"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON"
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            messages = [ChatMessage(role="user", content="Hello")]
            response = await client.chat_completion(messages)
            
            # Should fallback to using raw content
            assert response.answer == "This is not valid JSON"
            assert response.confidence == 0.3  # Fallback confidence
            assert response.escalate is True  # Fallback escalation
    
    @pytest.mark.asyncio
    async def test_request_retry_on_server_error(self, client):
        """Test retry logic on server error"""
        with patch.object(client.session, "post") as mock_post:
            # First call returns 500, second call succeeds
            mock_post.side_effect = [
                AsyncMock(status_code=500, text="Server Error"),
                AsyncMock(
                    status_code=200,
                    json=AsyncMock(return_value={
                        "choices": [{"message": {"content": '{"answer": "Success", "confidence": 0.8, "escalate": false, "suggested_actions": []}'}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
                    })
                )
            ]
            
            messages = [ChatMessage(role="user", content="Hello")]
            response = await client.chat_completion(messages)
            
            assert response.answer == "Success"
            assert mock_post.call_count == 2  # Should have retried
    
    @pytest.mark.asyncio
    async def test_request_timeout(self, client):
        """Test handling request timeout"""
        with patch.object(client.session, "post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")
            
            messages = [ChatMessage(role="user", content="Hello")]
            response = await client.chat_completion(messages)
            
            # Should return error response
            assert "technical difficulties" in response.answer.lower()
            assert response.confidence == 0.0
            assert response.escalate is True
    
    @pytest.mark.asyncio
    async def test_parse_response_with_usage(self, client):
        """Test parsing response with usage information"""
        mock_data = {
            "choices": [{
                "message": {
                    "content": '{"answer": "Test answer", "confidence": 0.75, "escalate": false, "suggested_actions": ["test"]}'
                }
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 10,
                "total_tokens": 30
            }
        }
        
        response = client._parse_response(mock_data)
        
        assert response.answer == "Test answer"
        assert response.confidence == 0.75
        assert response.usage.prompt_tokens == 20
        assert response.usage.completion_tokens == 10
        assert response.usage.total_tokens == 30
    
    @pytest.mark.asyncio
    async def test_parse_response_without_usage(self, client):
        """Test parsing response without usage information"""
        mock_data = {
            "choices": [{
                "message": {
                    "content": '{"answer": "Test answer", "confidence": 0.75, "escalate": false, "suggested_actions": []}'
                }
            }]
        }
        
        response = client._parse_response(mock_data)
        
        assert response.answer == "Test answer"
        assert response.usage is None
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check"""
        mock_response = {
            "choices": [{
                "message": {
                    "content": '{"status": "OK"}'
                }
            }]
        }
        
        with patch.object(client.session, "post") as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            
            health = await client.health_check()
            
            assert health["status"] == "healthy"
            assert health["model"] == "nvidia/nemotron-nano-9b-v2:free"
            assert health["response_received"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check failure"""
        with patch.object(client.session, "post") as mock_post:
            mock_post.side_effect = Exception("Connection failed")
            
            health = await client.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["response_received"] is False
            assert "Connection failed" in health["error"]


class TestCreateOpenRouterClient:
    """Test client factory function"""
    
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
    def test_create_client_with_env_var(self):
        """Test creating client from environment variable"""
        client = create_openrouter_client()
        
        assert client.config.api_key == "test-key"
        assert client.config.model == "nvidia/nemotron-nano-9b-v2:free"
    
    @patch.dict("os.environ", {
        "OPENROUTER_API_KEY": "test-key",
        "OPENROUTER_MODEL": "custom-model"
    })
    def test_create_client_with_custom_model(self):
        """Test creating client with custom model"""
        client = create_openrouter_client()
        
        assert client.config.api_key == "test-key"
        assert client.config.model == "custom-model"
    
    @patch.dict("os.environ", {}, clear=True)
    def test_create_client_without_api_key(self):
        """Test creating client without API key raises error"""
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
            create_openrouter_client()


class TestOpenRouterResponse:
    """Test OpenRouter response model"""
    
    def test_response_creation(self):
        """Test creating response object"""
        response = OpenRouterResponse(
            answer="Test answer",
            confidence=0.8,
            escalate=False,
            suggested_actions=["test_action"]
        )
        
        assert response.answer == "Test answer"
        assert response.confidence == 0.8
        assert response.escalate is False
        assert "test_action" in response.suggested_actions
        assert response.usage is None
        assert response.raw_response is None