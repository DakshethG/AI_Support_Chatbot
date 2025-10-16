#!/usr/bin/env python3
"""
Import Hugging Face Customer Support FAQ Dataset
Updates the bot with comprehensive real-world customer support FAQs
"""

import json
import requests
import subprocess
import re
from collections import defaultdict
from typing import List, Dict, Set

def fetch_huggingface_dataset() -> List[Dict[str, str]]:
    """Fetch the complete Hugging Face customer support FAQ dataset"""
    
    print("🔄 Fetching Hugging Face customer support FAQ dataset...")
    
    base_url = "https://datasets-server.huggingface.co/rows"
    dataset_name = "MakTek/Customer_support_faqs_dataset"
    
    all_faqs = []
    offset = 0
    batch_size = 100
    
    while offset < 200:  # Dataset has 200 total rows
        url = f"{base_url}?dataset={dataset_name}&config=default&split=train&offset={offset}&length={batch_size}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            for row_data in data.get('rows', []):
                row = row_data.get('row', {})
                if 'question' in row and 'answer' in row:
                    all_faqs.append({
                        'question': row['question'],
                        'answer': row['answer']
                    })
            
            print(f"✅ Fetched batch {offset}-{offset + batch_size - 1}")
            offset += batch_size
            
        except Exception as e:
            print(f"❌ Error fetching batch {offset}: {str(e)}")
            break
    
    print(f"📊 Total FAQs fetched: {len(all_faqs)}")
    return all_faqs

def categorize_faqs(faqs: List[Dict[str, str]]) -> List[Dict]:
    """Categorize FAQs and generate keywords"""
    
    print("🏷️  Categorizing FAQs and generating keywords...")
    
    # Category keywords mapping
    category_patterns = {
        'account': [
            'account', 'password', 'reset', 'login', 'sign', 'profile', 'privacy',
            'personal', 'information', 'update', 'unsubscribe', 'newsletter'
        ],
        'orders': [
            'order', 'track', 'cancel', 'change', 'modify', 'placed', 'history'
        ],
        'shipping': [
            'shipping', 'delivery', 'international', 'expedited', 'package', 
            'lost', 'damaged', 'address', 'transit'
        ],
        'returns': [
            'return', 'refund', 'exchange', 'policy', 'satisfaction', 'guarantee',
            'final sale', 'clearance', 'receipt', 'packaging'
        ],
        'payment': [
            'payment', 'credit', 'debit', 'paypal', 'price', 'promo', 'discount',
            'gift card', 'store credit', 'adjustment', 'billing'
        ],
        'products': [
            'product', 'item', 'stock', 'available', 'discontinued', 'pre-order',
            'backorder', 'size', 'color', 'warranty', 'demonstration', 'review'
        ],
        'services': [
            'gift wrapping', 'installation', 'bulk', 'wholesale', 'custom',
            'live chat', 'phone', 'business hours'
        ],
        'general': [
            'contact', 'support', 'customer', 'help', 'job', 'career', 'company'
        ]
    }
    
    categorized_faqs = []
    used_questions = set()  # Track duplicates
    
    for faq in faqs:
        question = faq['question'].strip()
        answer = faq['answer'].strip()
        
        # Skip duplicates
        if question in used_questions:
            continue
        used_questions.add(question)
        
        # Skip generic placeholders
        if '[phone number]' in answer or '[email address]' in answer or '[working hours]' in answer:
            # Replace placeholders with realistic values
            answer = answer.replace('[phone number]', '1-888-280-4331')
            answer = answer.replace('[email address]', 'support@company.com')
            answer = answer.replace('[working hours]', 'Monday-Friday 9AM-6PM EST')
        
        # Determine category
        question_lower = question.lower()
        answer_lower = answer.lower()
        combined_text = f"{question_lower} {answer_lower}"
        
        category_scores = {}
        for category, keywords in category_patterns.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                category_scores[category] = score
        
        # Assign to highest scoring category, default to 'general'
        category = max(category_scores, key=category_scores.get) if category_scores else 'general'
        
        # Generate keywords from question
        keywords = []
        
        # Extract meaningful words (skip common words)
        skip_words = {'how', 'can', 'do', 'does', 'what', 'when', 'where', 'why', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        question_words = re.findall(r'\b\w{3,}\b', question_lower)
        keywords.extend([word for word in question_words if word not in skip_words])
        
        # Add category-specific keywords
        if category in category_patterns:
            for keyword in category_patterns[category]:
                if keyword in combined_text:
                    keywords.append(keyword)
        
        # Remove duplicates and limit keywords
        keywords = list(set(keywords))[:8]
        
        # Assign priority based on common questions
        high_priority_patterns = [
            'track', 'return', 'cancel', 'password', 'shipping', 'refund', 
            'contact', 'payment', 'order'
        ]
        priority = 10 if any(pattern in question_lower for pattern in high_priority_patterns) else 5
        
        categorized_faqs.append({
            'question': question,
            'answer': answer,
            'category': category,
            'keywords': keywords,
            'tags': [category] + keywords[:3],  # Use category + top keywords as tags
            'priority': priority
        })
    
    # Print category distribution
    category_counts = defaultdict(int)
    for faq in categorized_faqs:
        category_counts[faq['category']] += 1
    
    print("\n📊 FAQ Category Distribution:")
    for category, count in sorted(category_counts.items()):
        print(f"  • {category.title()}: {count} FAQs")
    
    return categorized_faqs

def update_database_with_faqs(faqs: List[Dict]) -> bool:
    """Update the database with new FAQ data via Docker"""
    
    print("\n🔄 Updating database with new FAQ data...")
    
    # Create Python script to run in Docker
    faqs_json = json.dumps(faqs, indent=2)
    
    update_script = f'''
import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db_models import Base, FAQItem

def update_faq_data():
    database_url = "postgresql://ai_support:password@postgres:5432/ai_support_db"
    print("🔄 Connecting to database...")
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    faqs_data = {faqs_json}
    
    with SessionLocal() as db_session:
        try:
            # Delete existing FAQ items
            deleted_count = db_session.query(FAQItem).delete()
            print(f"❌ Deleted {{deleted_count}} existing FAQ items")
            
            # Add new FAQ items
            added_count = 0
            for faq_data in faqs_data:
                faq_item = FAQItem(**faq_data)
                db_session.add(faq_item)
                added_count += 1
            
            db_session.commit()
            print(f"✅ Added {{added_count}} new Hugging Face FAQ items")
            
            # Show sample FAQs by category
            print("\\n🔍 Sample FAQs by category:")
            categories = db_session.query(FAQItem.category).distinct().all()
            for (category,) in categories:
                sample = db_session.query(FAQItem).filter(
                    FAQItem.category == category
                ).first()
                if sample:
                    print(f"  • [{{category.upper()}}] {{sample.question}}")
            
            total_faqs = db_session.query(FAQItem).count()
            print(f"\\n📊 Total FAQ items in database: {{total_faqs}}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating FAQ data: {{str(e)}}")
            db_session.rollback()
            return False

if __name__ == "__main__":
    success = update_faq_data()
    sys.exit(0 if success else 1)
'''
    
    try:
        # Run the script inside Docker
        cmd = [
            'docker', 'exec', '-i', 'ai-support-bot-backend-1',
            'python', '-c', update_script
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Error updating database:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error executing database update: {str(e)}")
        return False

def main():
    """Main function"""
    print("🤖 AI Support Bot - Hugging Face FAQ Import")
    print("=" * 55)
    print("This will import comprehensive customer support FAQs from Hugging Face")
    print("Dataset: MakTek/Customer_support_faqs_dataset")
    print("")
    
    # Fetch dataset
    try:
        faqs = fetch_huggingface_dataset()
        if not faqs:
            print("❌ No FAQs fetched from Hugging Face")
            return False
        
        # Process and categorize
        processed_faqs = categorize_faqs(faqs)
        
        print(f"\n📋 Summary:")
        print(f"  • Total FAQs: {len(processed_faqs)}")
        print(f"  • Categories: {len(set(faq['category'] for faq in processed_faqs))}")
        print(f"  • High Priority: {len([faq for faq in processed_faqs if faq['priority'] == 10])}")
        
        # Ask for confirmation
        print(f"\n🔄 Ready to update database with {len(processed_faqs)} FAQs")
        response = input("Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return False
        
        # Update database
        success = update_database_with_faqs(processed_faqs)
        
        if success:
            print("\n🎉 Success! Your AI Support Bot now has comprehensive FAQ coverage!")
            print("\n🚀 Next steps:")
            print("1. Your bot is already running with the new FAQs")
            print("2. Test at: http://localhost")
            print("3. Try questions like:")
            print("   - 'How can I track my order?'")
            print("   - 'What is your return policy?'")
            print("   - 'Can I cancel my order?'")
            print("   - 'What payment methods do you accept?'")
            print("   - 'Do you offer international shipping?'")
            print("")
            print("Your bot now has professional-grade customer support knowledge! 🎯")
            return True
        else:
            print("❌ Failed to update database")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)