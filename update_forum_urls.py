#!/usr/bin/env python3
"""
Update forum start URLs with specific casino.guru categories.
"""

from models.base import get_session_maker
from models import Forum

def update_casino_guru_urls():
    """Update casino.guru forum with specific category URLs."""
    
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Get casino.guru forum
        forum = session.query(Forum).filter_by(name='casino.guru').first()
        
        if not forum:
            print("❌ casino.guru forum not found in database")
            return
        
        print(f"Current configuration:")
        print(f"  Start URLs: {forum.start_urls}")
        print(f"  Max Pages: {forum.max_pages}")
        
        # Update with specific casino.guru forum categories
        forum.start_urls = [
            'https://casino.guru/forum/casinos',              # Casino discussions
            'https://casino.guru/forum/bonuses-and-promotions', # Bonus discussions
            'https://casino.guru/forum/complaints-discussion',   # Complaint discussions
            'https://casino.guru/forum/general-gambling-discussion', # General gambling
        ]
        
        # Optionally increase max_pages since we have specific categories
        forum.max_pages = 10
        
        session.commit()
        
        print("\n✅ Forum updated successfully!")
        print(f"\nNew configuration:")
        print(f"  Start URLs:")
        for url in forum.start_urls:
            print(f"    - {url}")
        print(f"  Max Pages: {forum.max_pages}")
        print(f"\nThis will now crawl up to {len(forum.start_urls)} categories × {forum.max_pages} pages each")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    update_casino_guru_urls()
