import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

// Icons as simple SVG components
const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22,2 15,22 11,13 2,9"></polygon>
  </svg>
);

const CopyIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const TrashIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3,6 5,6 21,6"></polyline>
    <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
  </svg>
);

const ThemeIcon = ({ isDark }: { isDark: boolean }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    {isDark ? (
      <>
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </>
    ) : (
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    )}
  </svg>
);

// Types
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  confidence?: number;
}

interface ChatResponse {
  answer: string;
  confidence: number;
  escalate: boolean;
  suggested_actions: string[];
  session_id: string;
}

interface SuggestedQuestion {
  id: string;
  question: string;
  category: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [suggestedQuestions, setSuggestedQuestions] = useState<SuggestedQuestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize session and load suggestions
  useEffect(() => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    loadSuggestedQuestions();
    
    // Add welcome message
    setMessages([{
      id: uuidv4(),
      role: 'assistant',
      content: 'Hello! I\'m here to help you with your questions. How can I assist you today?',
      timestamp: new Date()
    }]);
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSuggestedQuestions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/faq/suggestions?limit=5`);
      setSuggestedQuestions(response.data);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || currentMessage.trim();
    
    if (!textToSend || isLoading) return;

    setError('');
    setIsLoading(true);
    setShowSuggestions(false);

    // Add user message immediately
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');

    try {
      const response = await axios.post<ChatResponse>(`${API_BASE_URL}/api/v1/chat`, {
        session_id: sessionId,
        message: textToSend,
        user_id: null,
        metadata: { source: 'web_chat' }
      });

      // Add assistant response (only show confidence for high-confidence FAQ responses)
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date(),
        confidence: response.data.confidence >= 0.9 ? response.data.confidence : undefined // Only show for FAQ/high confidence
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Handle escalation
      if (response.data.escalate) {
        const escalationMessage: Message = {
          id: uuidv4(),
          role: 'system',
          content: '🚨 This conversation has been escalated to a human agent. They will be with you shortly.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, escalationMessage]);
      }

    } catch (error: any) {
      console.error('Chat error:', error);
      
      let errorMessage = 'I apologize, but I\'m having trouble responding right now. Please try again.';
      
      if (error.response?.status === 429) {
        errorMessage = 'I\'m receiving too many requests. Please wait a moment before trying again.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'I\'m experiencing technical difficulties. Please try again in a few moments.';
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (question: string) => {
    sendMessage(question);
  };

  const clearChat = () => {
    setMessages([{
      id: uuidv4(),
      role: 'assistant',
      content: 'Hello! I\'m here to help you with your questions. How can I assist you today?',
      timestamp: new Date()
    }]);
    setSessionId(uuidv4());
    setShowSuggestions(true);
    setError('');
  };

  const copyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.body.classList.toggle('dark-mode');
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return '#6b7280';
    if (confidence >= 0.8) return '#10b981';
    if (confidence >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const getMessageClass = (role: string) => {
    switch (role) {
      case 'user':
        return 'message user-message';
      case 'assistant':
        return 'message assistant-message';
      case 'system':
        return 'message system-message';
      default:
        return 'message';
    }
  };

  return (
    <div className={`app ${isDarkMode ? 'dark-mode' : ''}`}>
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-left">
            <div className="bot-avatar">
              🤖
            </div>
            <div className="header-info">
              <h1>AI Support Assistant</h1>
              <span className="status">Online • Ready to help</span>
            </div>
          </div>
          <div className="header-actions">
            <button className="icon-button" onClick={toggleDarkMode} title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              <ThemeIcon isDark={isDarkMode} />
            </button>
            <button className="icon-button" onClick={clearChat} title="Clear Chat">
              <TrashIcon />
            </button>
          </div>
        </div>

        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={getMessageClass(message.role)}>
              <div className="message-bubble">
                {message.role === 'assistant' && (
                  <div className="bot-avatar-small">🤖</div>
                )}
                <div className="message-content-wrapper">
                  <div className="message-content">
                    {message.content}
                  </div>
                  <div className="message-meta">
                    <span className="message-time">{formatTime(message.timestamp)}</span>
                    {message.confidence !== undefined && (
                      <span 
                        className="confidence-indicator"
                        style={{ color: getConfidenceColor(message.confidence) }}
                      >
                        {Math.round(message.confidence * 100)}% confident
                      </span>
                    )}
                    {message.role !== 'system' && (
                      <button 
                        className="copy-button" 
                        onClick={() => copyMessage(message.content)}
                        title="Copy message"
                      >
                        <CopyIcon />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message assistant-message loading">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="message error-message">
              <div className="message-content">
                ⚠️ {error}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {showSuggestions && suggestedQuestions.length > 0 && (
          <div className="suggestions-container">
            <h3>Suggested Questions:</h3>
            <div className="suggestions">
              {suggestedQuestions.map((suggestion) => (
                <button
                  key={suggestion.id}
                  className="suggestion-button"
                  onClick={() => handleSuggestionClick(suggestion.question)}
                  disabled={isLoading}
                >
                  {suggestion.question}
                </button>
              ))}
            </div>
          </div>
        )}

        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className="input-container">
            <input
              ref={inputRef}
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              disabled={isLoading}
              className="chat-input"
            />
            <button
              type="submit"
              disabled={isLoading || !currentMessage.trim()}
              className="send-button"
              title="Send message"
            >
              {isLoading ? (
                <div className="spinner"></div>
              ) : (
                <SendIcon />
              )}
            </button>
          </div>
        </form>
      </div>

      <div className="footer">
        <p>Powered by AI Support Bot v1.0</p>
      </div>
    </div>
  );
}

export default App;