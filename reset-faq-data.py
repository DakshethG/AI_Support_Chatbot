#!/usr/bin/env python3
"""
Reset FAQ Data Script - Updates the bot with new Amazon-style customer support FAQs
"""

import os
import sys
sys.path.append('backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db_models import Base, FAQItem, SAMPLE_FAQ_DATA

def reset_faq_data():
    """Reset FAQ data with new Amazon-style customer support FAQs"""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql://ai_support:password@localhost:5432/ai_support_db")
    
    print(f"🔄 Connecting to database: {database_url}")
    
    # Create engine and session
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
            print("\n🔍 Sample of new FAQs:")
            sample_faqs = db_session.query(FAQItem).limit(5).all()
            for i, faq in enumerate(sample_faqs, 1):
                print(f"  {i}. [{faq.category.upper()}] {faq.question}")
            
            print("\n🎉 FAQ data reset completed successfully!")
            print("\n💡 New FAQ categories include:")
            categories = set(faq['category'] for faq in SAMPLE_FAQ_DATA)
            for category in sorted(categories):
                count = len([faq for faq in SAMPLE_FAQ_DATA if faq['category'] == category])
                print(f"  • {category.title()}: {count} FAQs")
            
        except Exception as e:
            print(f"❌ Error resetting FAQ data: {str(e)}")
            db_session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🤖 AI Support Bot - FAQ Data Reset")
    print("=" * 50)
    print("This will replace all existing FAQ data with new Amazon-style customer support FAQs")
    print("Categories: Account, Orders, Shipping, Returns, Billing, Support")
    print("")
    
    # Ask for confirmation
    response = input("Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        sys.exit(1)
    
    success = reset_faq_data()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Restart your bot: docker-compose restart backend")
        print("2. Test the new FAQs at: http://localhost")
        print("3. Try questions like:")
        print("   - 'How do I track my order?'")
        print("   - 'How do I return something?'") 
        print("   - 'Change my address'")
        print("   - 'Cancel my order'")
        print("")
        print("The AI will now be much more helpful for customer support! 🎯")
        sys.exit(0)
    else:
        print("❌ Failed to reset FAQ data. Check the error above.")
        sys.exit(1)