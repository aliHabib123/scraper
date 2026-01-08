#!/usr/bin/env python3
"""
Alternative approach: Add all Reddit subreddits as ONE forum with multiple start_urls.

Usage:
    python add_reddit_single_forum.py
"""

from models import Forum
from models.base import get_session_maker

def add_reddit_forum_combined(session):
    """
    Add a single Reddit forum that crawls multiple subreddits.
    """
    # Check if forum already exists
    existing = session.query(Forum).filter(Forum.name == "reddit").first()
    if existing:
        print(f"Forum 'reddit' already exists (ID: {existing.id})")
        return existing
    
    # Subreddits to monitor
    subreddits = ['casino', 'gambling', 'onlinegambling']
    
    # Create start URLs
    start_urls = [f"https://www.reddit.com/r/{sub}" for sub in subreddits]
    
    # Create new forum
    forum = Forum(
        name="reddit",
        base_url="https://www.reddit.com",
        type='category',
        start_urls=start_urls,
        pagination_type='reddit_after',
        enabled=True,
        max_pages=5
    )
    
    session.add(forum)
    session.commit()
    
    print(f"✓ Added forum: reddit")
    print(f"  Subreddits: {', '.join(subreddits)}")
    print(f"  Start URLs:")
    for url in start_urls:
        print(f"    - {url}")
    print(f"  Enabled: True")
    print(f"  Max pages: 5")
    
    return forum


def main():
    """Add Reddit as a single forum."""
    print("="*60)
    print("ADDING REDDIT AS SINGLE FORUM")
    print("="*60)
    print()
    
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    add_reddit_forum_combined(session)
    
    print()
    print("="*60)
    print("Note: With this approach, you'll need to update")
    print("get_parser_for_forum() to detect 'reddit' forum name")
    print("="*60)
    
    session.close()


if __name__ == '__main__':
    main()
