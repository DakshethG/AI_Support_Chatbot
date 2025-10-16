"""
Router logic for AI support bot - handles FAQ matching and business rules
"""

import os
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

import structlog
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz

from models.db_models import FAQItem, Message, Session as DBSession
from openrouter_client import ChatMessage, OpenRouterClient, OpenRouterResponse

logger = structlog.get_logger().bind(component="router")

# Business rule constants from environment
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))
MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", 6))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 2000))
FAQ_FUZZY_THRESHOLD = 85  # Minimum fuzzy match score for FAQ (increased for more precision)


class ChatRouter:
    def __init__(self, db_session: Session, openrouter_client: OpenRouterClient):
        self.db = db_session
        self.client = openrouter_client
        self.logger = structlog.get_logger().bind(component="chat_router")

    def _sanitize_message(self, message: str) -> str:
        """Sanitize user message for safety and length"""
        # Strip and truncate
        message = message.strip()
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH] + "..."
            self.logger.warning("Message truncated", original_length=len(message))
        
        # Basic prompt injection protection
        suspicious_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s*:",
            r"assistant\s*:",
            r"<\s*system\s*>",
            r"<\s*assistant\s*>",
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, message.lower()):
                self.logger.warning("Potential prompt injection detected", pattern=pattern)
                # Don't block completely, but log for monitoring
        
        return message

    def _search_faq(self, query: str) -> Optional[FAQItem]:
        """Search FAQ items for exact or fuzzy matches"""
        query_lower = query.lower().strip()
        
        if not query_lower or len(query_lower) < 3:
            return None

        # Get all active FAQ items
        faq_items = (
            self.db.query(FAQItem)
            .filter(FAQItem.active == True)
            .order_by(FAQItem.priority.desc(), FAQItem.usage_count.desc())
            .all()
        )

        best_match = None
        best_score = 0

        for faq in faq_items:
            # Check exact keyword matches first (must be significant portion of query)
            for keyword in faq.keywords or []:
                keyword_lower = keyword.lower()
                # Exact match or keyword is significant part of query
                if (keyword_lower in query_lower and len(keyword_lower) >= 4) or (
                    len(keyword_lower) >= 3 and query_lower.startswith(keyword_lower)
                ):
                    # Additional check: make sure it's actually related
                    query_words = set(query_lower.split())
                    keyword_words = set(keyword_lower.split())
                    if query_words.intersection(keyword_words):
                        self.logger.info("FAQ exact keyword match", faq_id=faq.id, keyword=keyword)
                        return faq

            # Fuzzy match against question (more strict)
            question_score = fuzz.ratio(query_lower, faq.question.lower())
            if question_score > best_score and question_score >= FAQ_FUZZY_THRESHOLD:
                best_score = question_score
                best_match = faq

            # Also check fuzzy match against keywords (more strict)
            for keyword in faq.keywords or []:
                keyword_score = fuzz.ratio(query_lower, keyword.lower())
                if keyword_score > best_score and keyword_score >= FAQ_FUZZY_THRESHOLD + 5:  # Higher threshold for keywords
                    best_score = keyword_score
                    best_match = faq

        if best_match:
            self.logger.info("FAQ fuzzy match found", faq_id=best_match.id, score=best_score)
            
            # Update usage statistics
            best_match.usage_count += 1
            best_match.last_used = datetime.utcnow()
            self.db.commit()

        return best_match

    def _build_context_messages(self, session_id: str, current_message: str) -> List[ChatMessage]:
        """Build context from recent messages in the session"""
        # Get recent messages from the session
        recent_messages = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(MAX_CONTEXT_MESSAGES)
            .all()
        )

        # Reverse to get chronological order
        recent_messages = list(reversed(recent_messages))

        # Build message list
        messages = []
        
        # Add system instruction
        system_prompt = self._build_system_prompt()
        messages.append(ChatMessage(role="system", content=system_prompt))

        # Add conversation history
        for msg in recent_messages:
            messages.append(ChatMessage(role=msg.role, content=msg.content))

        # Add current user message
        messages.append(ChatMessage(role="user", content=current_message))

        return messages

    def _build_system_prompt(self) -> str:
        """Build the system prompt with instructions for structured output"""
        return """You are an expert customer support AI for an e-commerce platform similar to Amazon.

You specialize in:
- Order management (tracking, cancellation, modification)
- Shipping and delivery questions
- Account management (password, profile, addresses)
- Returns and refunds
- Payment and billing issues
- Product-related questions

CRITICAL INSTRUCTION: You MUST respond with ONLY a JSON object. Do not include any text before or after the JSON.

The JSON object must have exactly these fields:
{
  "answer": "<your helpful response as a string>",
  "confidence": <float between 0.0 and 1.0>,
  "escalate": <true or false>,
  "suggested_actions": ["action1", "action2"]
}

When to ESCALATE (set escalate: true):
- Questions about legal issues, lawsuits, or threats
- Complex billing disputes involving large amounts
- Account security breaches or fraud
- Requests to speak with a manager/supervisor
- Issues requiring manual intervention (account locks, etc.)
- Anything outside your expertise areas above

When NOT to escalate (handle yourself):
- Standard order questions (tracking, status, delivery times)
- How-to questions about using the website/account
- Standard return/refund procedures
- General product information
- Shipping options and policies
- Standard account management
- Common troubleshooting

Guidelines:
- Be helpful, professional, and empathetic
- Provide step-by-step instructions when helpful
- Use specific details about policies (30-day returns, free shipping over $35, etc.)
- Don't escalate unnecessarily - you're capable of handling most customer service questions
- Set confidence high (0.8-0.95) for topics in your expertise areas
- Set confidence low (0.3-0.6) only when genuinely uncertain

Remember: ONLY return the JSON object, nothing else."""

    def _apply_business_rules(self, response: OpenRouterResponse, user_message: str) -> OpenRouterResponse:
        """Apply business rules to the LLM response"""
        user_message_lower = user_message.lower()
        answer_lower = response.answer.lower()
        
        # Rule 1: Only escalate on very low confidence (AI is genuinely unsure)
        if response.confidence < 0.4:  # Lowered threshold - trust the AI more
            self.logger.info("Applying very low confidence threshold rule", 
                           confidence=response.confidence)
            response.escalate = True
            if "human_review" not in response.suggested_actions:
                response.suggested_actions.append("human_review")

        # Rule 2: User message keywords that require escalation (NOT answer keywords)
        user_escalation_keywords = [
            # Legal/threat keywords
            "legal", "lawyer", "sue", "court", "attorney", "lawsuit",
            # Manager requests
            "manager", "supervisor", "escalate", "human", "person", "representative",
            # Security/fraud issues
            "fraud", "hack", "steal", "unauthorized", "security breach", "identity theft",
            # Complex billing disputes
            "dispute", "chargeback", "bank", "credit card dispute",
        ]
        
        for keyword in user_escalation_keywords:
            if keyword in user_message_lower:
                self.logger.info("User requested escalation via keyword", keyword=keyword)
                response.escalate = True
                if "human_review" not in response.suggested_actions:
                    response.suggested_actions.append("human_review")
                # Add explanation
                response.answer = f"I understand you need to speak with {keyword}. {response.answer} I'm connecting you with a human representative who can better assist with this request."
                break

        # Rule 3: Very short answers might indicate the AI couldn't help
        if len(response.answer.strip()) < 15:
            self.logger.info("Applying short answer rule", answer_length=len(response.answer))
            response.confidence = min(response.confidence, 0.3)
            response.escalate = True

        # Rule 4: Don't escalate for standard customer service topics
        standard_topics = [
            "track", "order", "shipping", "delivery", "return", "refund", 
            "password", "account", "address", "payment method", "cancel order",
            "when will", "how long", "how to", "where is", "status"
        ]
        
        is_standard_topic = any(topic in user_message_lower for topic in standard_topics)
        if is_standard_topic and response.confidence > 0.6:
            # Override escalation for standard topics where AI is confident
            if response.escalate and not any(keyword in user_message_lower for keyword in user_escalation_keywords):
                self.logger.info("Overriding escalation for standard customer service topic")
                response.escalate = False
                # Remove human_review from actions if it was added by confidence rule
                response.suggested_actions = [action for action in response.suggested_actions if action != "human_review"]

        return response

    async def route_message(
        self, 
        session_id: str, 
        message: str, 
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[OpenRouterResponse, Optional[FAQItem]]:
        """Main routing logic - checks FAQ first, then calls LLM"""
        
        # Sanitize input
        clean_message = self._sanitize_message(message)
        
        self.logger.info("Routing message", 
                        session_id=session_id, 
                        user_id=user_id, 
                        message_length=len(clean_message))

        # Step 1: Check for FAQ match (fast path)
        faq_match = self._search_faq(clean_message)
        if faq_match:
            self.logger.info("FAQ match found, returning direct answer", faq_id=faq_match.id)
            
            # Return FAQ answer with high confidence
            faq_response = OpenRouterResponse(
                answer=faq_match.answer,
                confidence=0.95,  # High confidence for FAQ matches
                escalate=False,
                suggested_actions=["check_faq", "contact_support"],
                usage=None,
                raw_response=f"FAQ match: {faq_match.question}",
            )
            
            return faq_response, faq_match

        # Step 2: Build context and call LLM
        try:
            context_messages = self._build_context_messages(session_id, clean_message)
            
            self.logger.info("Calling OpenRouter", 
                           session_id=session_id, 
                           context_messages=len(context_messages))
            
            llm_response = await self.client.chat_completion(
                messages=context_messages,
                temperature=0.15,
                max_tokens=512,
            )
            
            # Apply business rules
            final_response = self._apply_business_rules(llm_response, clean_message)
            
            self.logger.info("LLM response processed", 
                           session_id=session_id,
                           confidence=final_response.confidence,
                           escalate=final_response.escalate,
                           tokens_used=final_response.usage.total_tokens if final_response.usage else 0)
            
            return final_response, None
            
        except Exception as e:
            self.logger.error("Error in LLM routing", session_id=session_id, error=str(e))
            
            # Fallback response
            fallback_response = OpenRouterResponse(
                answer="I'm sorry, I'm experiencing technical difficulties. Please try again in a moment or contact our support team for immediate assistance.",
                confidence=0.0,
                escalate=True,
                suggested_actions=["retry", "contact_support", "technical_support"],
                usage=None,
                raw_response=f"Error: {str(e)}",
            )
            
            return fallback_response, None

    def get_suggested_questions(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get suggested questions from FAQ for user prompts"""
        faq_items = (
            self.db.query(FAQItem)
            .filter(FAQItem.active == True)
            .order_by(FAQItem.priority.desc(), FAQItem.usage_count.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": faq.id,
                "question": faq.question,
                "category": faq.category,
            }
            for faq in faq_items
        ]