#!/usr/bin/env python3
"""
Reset FAQ Data via Docker - Updates the bot with new Amazon-style customer support FAQs
"""

import os
import sys
import subprocess

def run_faq_reset():
    """Run the FAQ reset script inside the backend Docker container"""
    
    print("🤖 AI Support Bot - FAQ Data Reset (Docker)")
    print("=" * 55)
    print("This will replace all existing FAQ data with new Amazon-style customer support FAQs")
    print("Categories: Account, Orders, Shipping, Returns, Billing, Support")
    print("")
    
    # Ask for confirmation
    response = input("Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return False
    
    print("\n🔄 Resetting FAQ data via Docker container...")
    
    # Create the Python script to run inside Docker
    reset_script = '''
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db_models import Base, FAQItem, SAMPLE_FAQ_DATA

def reset_faq_data():
    database_url = os.getenv("DATABASE_URL", "postgresql://ai_support:password@postgres:5432/ai_support_db")
    print(f"🔄 Connecting to database: {database_url}")
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db_session:
        try:
            # Delete all existing FAQ items
            deleted_count = db_session.query(FAQItem).delete()
            print(f"❌ Deleted {deleted_count} existing FAQ items")
            
            # Add new FAQ items
            added_count = 0
            for faq_data in SAMPLE_FAQ_DATA:
                faq_item = FAQItem(**faq_data)
                db_session.add(faq_item)
                added_count += 1
            
            # Commit the changes
            db_session.commit()
            print(f"✅ Added {added_count} new Amazon-style FAQ items")
            
            # Verify the new data
            total_faqs = db_session.query(FAQItem).count()
            print(f"📊 Total FAQ items in database: {total_faqs}")
            
            # Show sample of new FAQs
            print("\\n🔍 Sample of new FAQs:")
            sample_faqs = db_session.query(FAQItem).limit(5).all()
            for i, faq in enumerate(sample_faqs, 1):
                print(f"  {i}. [{faq.category.upper()}] {faq.question}")
            
            print("\\n🎉 FAQ data reset completed successfully!")
            print("\\n💡 New FAQ categories include:")
            categories = set(faq['category'] for faq in SAMPLE_FAQ_DATA)
            for category in sorted(categories):
                count = len([faq for faq in SAMPLE_FAQ_DATA if faq['category'] == category])
                print(f"  • {category.title()}: {count} FAQs")
            
            return True
            
        except Exception as e:
            print(f"❌ Error resetting FAQ data: {str(e)}")
            db_session.rollback()
            return False

if __name__ == "__main__":
    success = reset_faq_data()
    sys.exit(0 if success else 1)
'''
    
    try:
        # Run the script inside the backend Docker container
        cmd = [
            'docker', 'exec', '-i', 'ai-support-bot-backend-1',
            'python', '-c', reset_script
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n🚀 Next steps:")
            print("1. Your bot is already running with the new FAQs!")
            print("2. Test the new FAQs at: http://localhost")
            print("3. Try questions like:")
            print("   - 'How do I track my order?'")
            print("   - 'How do I return something?'") 
            print("   - 'Change my address'")
            print("   - 'Cancel my order'")
            print("")
            print("The AI will now be much more helpful for customer support! 🎯")
            return True
        else:
            print(f"❌ Error running FAQ reset:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Command timed out. The database might be slow to respond.")
        return False
    except Exception as e:
        print(f"❌ Error executing command: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_faq_reset()
    sys.exit(0 if success else 1)