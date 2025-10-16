"""
Database models for AI support bot
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, JSON, 
    ForeignKey, Index, create_engine, MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()
metadata = MetaData()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default=dict)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="created_by_user", foreign_keys="[Escalation.created_by]")

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Nullable for guest sessions
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active")  # active, ended, escalated
    meta_data = Column(JSON, default=dict)
    
    # Session summary and context
    summary = Column(Text, nullable=True)
    total_messages = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost_estimate = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="session", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_sessions_user_id', 'user_id'),
        Index('idx_sessions_created_at', 'created_at'),
        Index('idx_sessions_last_active', 'last_active_at'),
        Index('idx_sessions_status', 'status'),
    )

    def __repr__(self):
        return f"<Session(id='{self.id}', user_id='{self.user_id}', status='{self.status}')>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Message metadata
    tokens_used = Column(Integer, default=0)
    confidence = Column(Float, nullable=True)  # Only for assistant messages
    escalate_flag = Column(Boolean, default=False)
    suggested_actions = Column(JSON, default=list)
    meta_data = Column(JSON, default=dict)

    # Relationships
    session = relationship("Session", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_messages_session_id', 'session_id'),
        Index('idx_messages_created_at', 'created_at'),
        Index('idx_messages_role', 'role'),
    )

    def __repr__(self):
        return f"<Message(id='{self.id}', session_id='{self.session_id}', role='{self.role}')>"


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    reason = Column(String(500), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)  # Can be system-generated
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    priority = Column(String(10), default="medium")  # low, medium, high, urgent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Escalation details
    resolution_notes = Column(Text, nullable=True)
    meta_data = Column(JSON, default=dict)

    # Relationships
    session = relationship("Session", back_populates="escalations")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="escalations")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to])

    # Indexes
    __table_args__ = (
        Index('idx_escalations_session_id', 'session_id'),
        Index('idx_escalations_status', 'status'),
        Index('idx_escalations_created_at', 'created_at'),
        Index('idx_escalations_assigned_to', 'assigned_to'),
        Index('idx_escalations_priority', 'priority'),
    )

    def __repr__(self):
        return f"<Escalation(id='{self.id}', session_id='{self.session_id}', status='{self.status}')>"


class FAQItem(Base):
    __tablename__ = "faq_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)  # List of tags
    keywords = Column(JSON, default=list)  # Keywords for matching
    priority = Column(Integer, default=0)  # Higher priority items shown first
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Additional metadata
    meta_data = Column(JSON, default=dict)

    # Indexes
    __table_args__ = (
        Index('idx_faq_active', 'active'),
        Index('idx_faq_category', 'category'),
        Index('idx_faq_priority', 'priority'),
        Index('idx_faq_usage_count', 'usage_count'),
    )

    def __repr__(self):
        return f"<FAQItem(id='{self.id}', category='{self.category}', active='{self.active}')>"


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)
    model = Column(String(100), nullable=False)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Request metadata
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    meta_data = Column(JSON, default=dict)

    # Relationships
    session = relationship("Session", back_populates="usage_logs")

    # Indexes
    __table_args__ = (
        Index('idx_usage_logs_session_id', 'session_id'),
        Index('idx_usage_logs_created_at', 'created_at'),
        Index('idx_usage_logs_model', 'model'),
        Index('idx_usage_logs_success', 'success'),
    )

    def __repr__(self):
        return f"<UsageLog(id='{self.id}', model='{self.model}', total_tokens={self.total_tokens})>"


# Database utility functions
class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get a database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    async def get_async_session(self):
        """Get an async database session (for FastAPI dependency injection)"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# Sample FAQ data for Amazon-style customer support
SAMPLE_FAQ_DATA = [
    # Account Management FAQs
    {
        "question": "How do I reset my password?",
        "answer": "To reset your password: 1) Go to the sign-in page, 2) Click 'Forgot your password?', 3) Enter your email or phone number, 4) Check your email/SMS for the reset code, 5) Create a new password. The reset link is valid for 24 hours.",
        "category": "account",
        "tags": ["password", "reset", "login", "security", "account"],
        "keywords": ["password", "reset", "forgot", "login", "account", "sign in", "access"],
        "priority": 10,
    },
    {
        "question": "How do I update my account information?",
        "answer": "To update your account: 1) Sign in to Your Account, 2) Go to 'Login & security' or 'Your Account', 3) Select the section you want to update (name, email, phone, address), 4) Make your changes and click 'Save changes'. Some changes may require verification.",
        "category": "account",
        "tags": ["account", "profile", "update", "information"],
        "keywords": ["update", "account", "profile", "information", "change", "edit", "name", "email", "address"],
        "priority": 8,
    },
    {
        "question": "How do I change my delivery address?",
        "answer": "To change your delivery address: 1) Go to Your Account > Your Addresses, 2) Click 'Add address' for a new one or 'Edit' for existing addresses, 3) Update the address details, 4) Set as default if needed. For pending orders, you may need to contact support if the order hasn't shipped yet.",
        "category": "account",
        "tags": ["address", "delivery", "shipping", "change"],
        "keywords": ["address", "delivery", "shipping", "change", "update", "location", "move"],
        "priority": 9,
    },
    
    # Order Management FAQs
    {
        "question": "How do I track my order?",
        "answer": "To track your order: 1) Go to Your Orders in your account, 2) Find the order and click 'Track package', 3) You'll see real-time tracking information. You can also use the tracking number with the carrier directly. Tracking is available once your order ships.",
        "category": "orders",
        "tags": ["track", "order", "shipping", "delivery", "status"],
        "keywords": ["track", "tracking", "order", "package", "shipment", "delivery", "where", "status"],
        "priority": 10,
    },
    {
        "question": "How do I cancel my order?",
        "answer": "To cancel an order: 1) Go to Your Orders, 2) Find the order you want to cancel, 3) Click 'Cancel items'. If the option isn't available, your order may have already shipped. You can still return it after delivery using our return process.",
        "category": "orders",
        "tags": ["cancel", "order", "cancellation"],
        "keywords": ["cancel", "cancellation", "order", "stop", "remove", "delete"],
        "priority": 9,
    },
    {
        "question": "How do I modify my order?",
        "answer": "Order modifications are limited once placed. You can: 1) Change delivery speed if available, 2) Update delivery instructions, 3) Change delivery address (if not yet shipped). For other changes like items or quantity, you'll need to cancel and reorder, or make changes after delivery through returns.",
        "category": "orders",
        "tags": ["modify", "order", "change", "edit"],
        "keywords": ["modify", "change", "edit", "order", "update", "alter"],
        "priority": 7,
    },
    
    # Shipping & Delivery FAQs
    {
        "question": "What are the shipping options and delivery times?",
        "answer": "Our shipping options include: • Standard Shipping (5-8 business days) - FREE on orders over $35 • Expedited Shipping (2-3 business days) - $7.99 • Priority Shipping (1-2 business days) - $12.99 • Same-day delivery available in select areas. Delivery times may vary during peak seasons.",
        "category": "shipping",
        "tags": ["shipping", "delivery", "options", "time", "speed"],
        "keywords": ["shipping", "delivery", "fast", "quick", "same day", "expedited", "standard", "time", "speed"],
        "priority": 8,
    },
    {
        "question": "My package was delivered but I can't find it",
        "answer": "If your package shows delivered but you can't find it: 1) Check all possible delivery locations (front/back door, mailbox, neighbors), 2) Ask family members or roommates, 3) Check with building management if applicable, 4) Wait 24 hours as sometimes packages are marked delivered early, 5) Contact us if still not found - we'll investigate with the carrier.",
        "category": "shipping",
        "tags": ["delivered", "missing", "package", "lost"],
        "keywords": ["delivered", "missing", "lost", "package", "find", "stolen", "not received"],
        "priority": 9,
    },
    {
        "question": "What if my package is damaged or defective?",
        "answer": "If you received a damaged or defective item: 1) Go to Your Orders, 2) Select 'Return or replace items', 3) Choose the reason (damaged/defective), 4) Select whether you want a replacement or refund, 5) Follow the return instructions. Most damaged items can be returned for free, and we'll send a replacement right away.",
        "category": "shipping",
        "tags": ["damaged", "defective", "broken", "return", "replace"],
        "keywords": ["damaged", "defective", "broken", "faulty", "wrong item", "return", "replace"],
        "priority": 8,
    },
    
    # Returns & Refunds FAQs
    {
        "question": "How do I return an item?",
        "answer": "To return an item: 1) Go to Your Orders within 30 days of delivery, 2) Select 'Return or replace items', 3) Choose your return reason and method (refund/exchange), 4) Print the prepaid return label, 5) Package the item securely, 6) Drop off at any UPS location or schedule a pickup. Most returns are free.",
        "category": "returns",
        "tags": ["return", "refund", "exchange", "send back"],
        "keywords": ["return", "refund", "exchange", "send back", "don't want", "wrong size", "don't like"],
        "priority": 10,
    },
    {
        "question": "When will I get my refund?",
        "answer": "Refund timing depends on your payment method: • Credit/Debit cards: 3-5 business days after we process your return • PayPal: 1-2 business days • Gift cards: Immediately after processing • Bank transfers: 5-10 business days. We'll send you an email confirmation when your refund is processed.",
        "category": "returns",
        "tags": ["refund", "timing", "when", "money back"],
        "keywords": ["refund", "money back", "when", "timing", "how long", "receive"],
        "priority": 8,
    },
    
    # Payment & Billing FAQs
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept: • Credit cards (Visa, Mastercard, American Express, Discover) • Debit cards • PayPal • Apple Pay • Google Pay • Gift cards and store credit • Bank transfers for large orders. All transactions are secure and encrypted for your protection.",
        "category": "billing",
        "tags": ["payment", "methods", "credit card", "paypal"],
        "keywords": ["payment", "pay", "credit card", "debit", "paypal", "apple pay", "google pay", "billing"],
        "priority": 7,
    },
    {
        "question": "I was charged incorrectly or twice",
        "answer": "If you notice an incorrect charge: 1) Check Your Orders to verify the charge details, 2) Look for any promotional discounts that may have been applied, 3) Check if there are separate charges for different shipments, 4) If you still believe there's an error, contact our billing support with your order number - we'll investigate and resolve any billing issues promptly.",
        "category": "billing",
        "tags": ["charge", "incorrect", "billing", "double", "error"],
        "keywords": ["charged", "billing", "incorrect", "wrong", "double", "twice", "error", "overcharge"],
        "priority": 9,
    },
    
    # General Support FAQs
    {
        "question": "How can I contact customer service?",
        "answer": "You can reach our customer service team: • Live Chat: Available 24/7 on our website • Phone: 1-888-280-4331 (24/7) • Email: support@company.com (response within 24 hours) • Help Center: Browse our comprehensive help articles. For the fastest response, try our live chat or phone support.",
        "category": "support",
        "tags": ["contact", "support", "customer service", "help"],
        "keywords": ["contact", "support", "customer service", "help", "phone", "chat", "email", "talk"],
        "priority": 6,
    },
]


def init_faq_data(db_session):
    """Initialize the database with sample FAQ data"""
    # Check if FAQ data already exists
    existing_count = db_session.query(FAQItem).count()
    if existing_count > 0:
        print(f"FAQ data already exists ({existing_count} items). Skipping initialization.")
        return

    # Add sample FAQ items
    for faq_data in SAMPLE_FAQ_DATA:
        faq_item = FAQItem(**faq_data)
        db_session.add(faq_item)
    
    db_session.commit()
    print(f"Initialized {len(SAMPLE_FAQ_DATA)} FAQ items.")