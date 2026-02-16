#!/usr/bin/env python3
"""
Add LCB.org test forum configuration (single category, 2 pages only).
For testing purposes.
"""

from models.base import get_session_maker, init_db
from models import Forum

def add_lcb_test():
    """Add LCB.org forum with single start URL and max 2 pages for testing."""
    
    # Initialize database
    init_db()
    
    # Get session
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Check if forum already exists
        existing = session.query(Forum).filter(Forum.name == 'lcb.org').first()
        if existing:
            # Update existing forum
            print(f"✓ LCB.org forum already exists (ID: {existing.id})")
            print(f"  Updating to test configuration...")
            
            existing.start_urls = ['https://lcb.org/onlinecasinobonusforum/casinos']
            existing.max_pages = 2
            existing.enabled = True
            
            session.commit()
            
            print("=" * 70)
            print("✅ LCB.org Forum Updated to Test Configuration")
            print("=" * 70)
            print(f"Name: {existing.name}")
            print(f"Base URL: {existing.base_url}")
            print(f"Type: {existing.type}")
            print(f"Start URLs:")
            for idx, url in enumerate(existing.start_urls, 1):
                print(f"  {idx}. {url}")
            print(f"Pagination: {existing.pagination_type}")
            print(f"Max Pages: {existing.max_pages}")
            print(f"Enabled: {existing.enabled}")
            print(f"Forum ID: {existing.id}")
            print("=" * 70)
            return
        
        # Create new forum entry
        forum = Forum(
            name='lcb.org',
            base_url='https://lcb.org',
            type='category',
            start_urls=[
                'https://lcb.org/onlinecasinobonusforum/casinos',
            ],
            pagination_type='page_number',
            max_pages=2,
            enabled=True
        )
        
        session.add(forum)
        session.commit()
        
        print("=" * 70)
        print("✅ LCB.org Test Forum Added Successfully")
        print("=" * 70)
        print(f"Name: {forum.name}")
        print(f"Base URL: {forum.base_url}")
        print(f"Type: {forum.type}")
        print(f"Start URLs:")
        for idx, url in enumerate(forum.start_urls, 1):
            print(f"  {idx}. {url}")
        print(f"Pagination: {forum.pagination_type}")
        print(f"Max Pages: {forum.max_pages} (TEST MODE)")
        print(f"Enabled: {forum.enabled}")
        print(f"Forum ID: {forum.id}")
        print("=" * 70)
        print("\n⚠️  TEST CONFIGURATION - Only 2 pages of /casinos will be crawled")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
        raise
        
    finally:
        session.close()

if __name__ == '__main__':
    add_lcb_test()
