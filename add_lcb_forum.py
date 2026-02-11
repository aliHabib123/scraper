#!/usr/bin/env python3
"""
Add LCB.org (Latest Casino Bonuses) forum to database.
"""

from models.base import get_session_maker, init_db
from models import Forum

def add_lcb_forum():
    """Add LCB.org forum with all start URLs."""
    
    # Initialize database
    init_db()
    
    # Get session
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Check if forum already exists
        existing = session.query(Forum).filter(Forum.name == 'lcb.org').first()
        if existing:
            print(f"✓ LCB.org forum already exists (ID: {existing.id})")
            print(f"  Base URL: {existing.base_url}")
            print(f"  Start URLs: {len(existing.start_urls)} URLs")
            print(f"  Enabled: {existing.enabled}")
            return
        
        # Create forum entry
        forum = Forum(
            name='lcb.org',
            base_url='https://lcb.org',
            type='category',
            start_urls=[
                'https://lcb.org/onlinecasinobonusforum/casinos',
                'https://lcb.org/onlinecasinobonusforum/no-deposit-casinos',
                'https://lcb.org/onlinecasinobonusforum/casino-whoring',
                'https://lcb.org/onlinecasinobonusforum/direct-casino-support',
                'https://lcb.org/onlinecasinobonusforum/online-slot-discussion',
            ],
            pagination_type='page_number',
            max_pages=10,
            enabled=True
        )
        
        session.add(forum)
        session.commit()
        
        print("=" * 70)
        print("✅ LCB.org Forum Added Successfully")
        print("=" * 70)
        print(f"Name: {forum.name}")
        print(f"Base URL: {forum.base_url}")
        print(f"Type: {forum.type}")
        print(f"Start URLs:")
        for idx, url in enumerate(forum.start_urls, 1):
            print(f"  {idx}. {url}")
        print(f"Pagination: {forum.pagination_type}")
        print(f"Max Pages: {forum.max_pages}")
        print(f"Enabled: {forum.enabled}")
        print(f"Forum ID: {forum.id}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
        raise
        
    finally:
        session.close()

if __name__ == '__main__':
    add_lcb_forum()
