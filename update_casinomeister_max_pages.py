#!/usr/bin/env python3
"""
Update CasinoMeister forum to max_pages=1 to avoid Cloudflare 403 errors.
"""

from models import Forum
from models.base import get_session_maker


def update_casinomeister_max_pages():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Find CasinoMeister forum
        forum = session.query(Forum).filter(Forum.name == "casinomeister.com").first()
        
        if not forum:
            print("❌ Forum 'casinomeister.com' not found in database")
            return
        
        old_max_pages = forum.max_pages
        
        # Update max_pages to 1
        forum.max_pages = 1
        session.commit()
        
        print(f"✓ Updated casinomeister.com:")
        print(f"  max_pages: {old_max_pages} → 1")
        print(f"  This limits crawling to page 1 of each sub-forum")
        print(f"  Expected threads per run: ~17 × 12 forums = ~200 threads")
        
    finally:
        session.close()


if __name__ == '__main__':
    update_casinomeister_max_pages()
