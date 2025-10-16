"""
Background tasks for AI Support Bot
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import structlog

from workers.celery_app import celery_app
from models.db_models import Session as DBSession, Message, UsageLog, Escalation
from openrouter_client import create_openrouter_client, ChatMessage

logger = structlog.get_logger()

# Database setup for workers
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ai_support.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseTask(Task):
    """Base task with database session management"""
    
    def __call__(self, *args, **kwargs):
        db = SessionLocal()
        try:
            return super().__call__(db, *args, **kwargs)
        finally:
            db.close()


@celery_app.task(base=DatabaseTask)
def generate_session_summary(db, session_id: str):
    """Generate a summary for a completed session"""
    logger.info("Generating session summary", session_id=session_id)
    
    try:
        # Get session and messages
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            logger.error("Session not found", session_id=session_id)
            return {"error": "Session not found"}
        
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()
        
        if len(messages) < 2:  # Need at least user + assistant message
            logger.info("Not enough messages for summary", session_id=session_id)
            return {"message": "Not enough messages for summary"}
        
        # Build conversation for summarization
        conversation_text = []
        for msg in messages:
            if msg.role in ['user', 'assistant']:
                conversation_text.append(f"{msg.role.title()}: {msg.content}")
        
        # Create summarization prompt
        summary_prompt = f"""Please provide a concise summary of this customer support conversation:

{chr(10).join(conversation_text)}

Summary should be 2-3 sentences covering:
1. The main issue or question
2. The resolution or outcome
3. Any escalations or follow-up needed

Return ONLY the summary text, nothing else."""

        # Call OpenRouter for summarization
        try:
            import asyncio
            
            async def get_summary():
                client = create_openrouter_client()
                async with client:
                    messages_for_llm = [ChatMessage(role="user", content=summary_prompt)]
                    response = await client.chat_completion(messages_for_llm, temperature=0.1, max_tokens=200)
                    return response.answer.strip()
            
            summary = asyncio.run(get_summary())
        except Exception as e:
            logger.error("Failed to generate LLM summary", session_id=session_id, error=str(e))
            # Fallback to simple summary
            summary = f"Session with {len(messages)} messages. "
            if any(msg.escalate_flag for msg in messages if hasattr(msg, 'escalate_flag')):
                summary += "Escalated to human agent. "
            summary += f"Last activity: {session.last_active_at.strftime('%Y-%m-%d %H:%M')}"
        
        # Update session with summary
        session.summary = summary
        db.commit()
        
        logger.info("Session summary generated", session_id=session_id, summary_length=len(summary))
        return {"success": True, "summary": summary}
        
    except Exception as e:
        logger.error("Failed to generate session summary", session_id=session_id, error=str(e))
        return {"error": str(e)}


@celery_app.task(base=DatabaseTask)
def cleanup_old_sessions(db, days_old: int = 30):
    """Clean up old sessions and associated data"""
    logger.info("Starting session cleanup", days_old=days_old)
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old sessions
        old_sessions = db.query(DBSession).filter(
            DBSession.last_active_at < cutoff_date,
            DBSession.status != 'escalated'  # Don't delete escalated sessions
        ).all()
        
        deleted_count = 0
        for session in old_sessions:
            # Delete associated messages and usage logs (cascading delete)
            db.delete(session)
            deleted_count += 1
        
        db.commit()
        
        logger.info("Session cleanup completed", deleted_sessions=deleted_count)
        return {"success": True, "deleted_sessions": deleted_count}
        
    except Exception as e:
        logger.error("Session cleanup failed", error=str(e))
        return {"error": str(e)}


@celery_app.task(base=DatabaseTask)
def generate_daily_analytics(db, date: str = None):
    """Generate daily analytics report"""
    if date:
        target_date = datetime.fromisoformat(date).date()
    else:
        target_date = datetime.utcnow().date() - timedelta(days=1)  # Previous day
    
    logger.info("Generating daily analytics", date=target_date)
    
    try:
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        # Session metrics
        total_sessions = db.query(DBSession).filter(
            DBSession.created_at >= start_time,
            DBSession.created_at <= end_time
        ).count()
        
        # Message metrics
        messages = db.query(Message).filter(
            Message.created_at >= start_time,
            Message.created_at <= end_time
        ).all()
        
        total_messages = len(messages)
        user_messages = len([m for m in messages if m.role == 'user'])
        assistant_messages = len([m for m in messages if m.role == 'assistant'])
        
        # Escalation metrics
        escalations = db.query(Escalation).filter(
            Escalation.created_at >= start_time,
            Escalation.created_at <= end_time
        ).count()
        
        # Usage metrics
        usage_logs = db.query(UsageLog).filter(
            UsageLog.created_at >= start_time,
            UsageLog.created_at <= end_time
        ).all()
        
        total_tokens = sum(log.total_tokens for log in usage_logs)
        total_requests = len(usage_logs)
        successful_requests = len([log for log in usage_logs if log.success])
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Confidence metrics
        assistant_messages_with_confidence = [
            m for m in messages 
            if m.role == 'assistant' and m.confidence is not None
        ]
        
        if assistant_messages_with_confidence:
            avg_confidence = sum(m.confidence for m in assistant_messages_with_confidence) / len(assistant_messages_with_confidence)
            low_confidence_count = len([m for m in assistant_messages_with_confidence if m.confidence < 0.6])
        else:
            avg_confidence = 0
            low_confidence_count = 0
        
        analytics = {
            "date": target_date.isoformat(),
            "sessions": {
                "total": total_sessions,
                "escalations": escalations,
                "escalation_rate": escalations / total_sessions if total_sessions > 0 else 0
            },
            "messages": {
                "total": total_messages,
                "user": user_messages,
                "assistant": assistant_messages
            },
            "performance": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "total_tokens": total_tokens,
                "avg_tokens_per_request": total_tokens / total_requests if total_requests > 0 else 0
            },
            "quality": {
                "avg_confidence": avg_confidence,
                "low_confidence_responses": low_confidence_count,
                "low_confidence_rate": low_confidence_count / len(assistant_messages_with_confidence) if assistant_messages_with_confidence else 0
            }
        }
        
        logger.info("Daily analytics generated", date=target_date, analytics=analytics)
        return {"success": True, "analytics": analytics}
        
    except Exception as e:
        logger.error("Failed to generate daily analytics", date=target_date, error=str(e))
        return {"error": str(e)}


@celery_app.task(base=DatabaseTask)
def process_escalation_notifications(db, escalation_id: str):
    """Process notifications for new escalations"""
    logger.info("Processing escalation notification", escalation_id=escalation_id)
    
    try:
        escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not escalation:
            logger.error("Escalation not found", escalation_id=escalation_id)
            return {"error": "Escalation not found"}
        
        session = db.query(DBSession).filter(DBSession.id == escalation.session_id).first()
        
        # Here you would implement actual notification logic:
        # - Send email to support team
        # - Post to Slack channel
        # - Create ticket in ticketing system
        # - Send SMS for urgent escalations
        
        # For now, just log the escalation
        notification_data = {
            "escalation_id": escalation.id,
            "session_id": escalation.session_id,
            "reason": escalation.reason,
            "priority": escalation.priority,
            "user_id": session.user_id if session else None,
            "created_at": escalation.created_at.isoformat()
        }
        
        logger.info("Escalation notification processed", **notification_data)
        
        # In a real implementation, you might:
        # - Send to email service (SendGrid, SES, etc.)
        # - Post to Slack webhook
        # - Create Jira/ServiceNow ticket
        # - Trigger PagerDuty alert for urgent issues
        
        return {"success": True, "notification_sent": True}
        
    except Exception as e:
        logger.error("Failed to process escalation notification", escalation_id=escalation_id, error=str(e))
        return {"error": str(e)}


@celery_app.task(base=DatabaseTask)
def update_faq_usage_stats(db):
    """Update FAQ usage statistics"""
    logger.info("Updating FAQ usage statistics")
    
    try:
        from models.db_models import FAQItem
        
        # This is a simple implementation
        # In production, you might want more sophisticated analytics
        
        # Get FAQ items that haven't been used recently
        week_ago = datetime.utcnow() - timedelta(days=7)
        unused_faqs = db.query(FAQItem).filter(
            FAQItem.last_used < week_ago
        ).all()
        
        # Could implement:
        # - Decay unused FAQ priorities
        # - Suggest FAQ improvements based on low match rates
        # - Identify gaps in FAQ coverage
        
        logger.info("FAQ usage stats updated", unused_faqs=len(unused_faqs))
        return {"success": True, "unused_faqs": len(unused_faqs)}
        
    except Exception as e:
        logger.error("Failed to update FAQ usage stats", error=str(e))
        return {"error": str(e)}


# Periodic tasks (requires celery beat scheduler)
@celery_app.task
def schedule_daily_cleanup():
    """Schedule daily cleanup tasks"""
    cleanup_old_sessions.delay(days_old=30)
    generate_daily_analytics.delay()
    update_faq_usage_stats.delay()
    return {"success": True}


# Helper function to trigger session summary after conversation ends
def trigger_session_summary(session_id: str, delay: int = 300):
    """Trigger session summary generation with delay"""
    generate_session_summary.apply_async(args=[session_id], countdown=delay)