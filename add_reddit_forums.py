#!/usr/bin/env python3
"""
Add Reddit subreddits as forums to the database.

Usage:
    python add_reddit_forums.py
"""

from models import Forum
from models.base import get_session_maker
from parsers import RedditParser

def add_reddit_forum(session, subreddit_name: str, enabled: bool = True, max_pages: int = 5):
    """
    Add a Reddit subreddit as a forum.
    
    Args:
        session: Database session
        subreddit_name: Name of subreddit (e.g., 'casino', 'gambling')
        enabled: Whether the forum is enabled
        max_pages: Maximum pages to crawl
    """
    # Create Reddit URL
    base_url = f"https://www.reddit.com/r/{subreddit_name}"
    
    # Check if forum already exists
    existing = session.query(Forum).filter(Forum.name == f"r/{subreddit_name}").first()
    if existing:
        print(f"Forum 'r/{subreddit_name}' already exists (ID: {existing.id})")
        return existing
    
    # Create new forum
    forum = Forum(
        name=f"r/{subreddit_name}",
        base_url=base_url,
        type='category',
        start_urls=[base_url],
        pagination_type='reddit_after',  # Reddit uses 'after' token
        enabled=enabled,
        max_pages=max_pages
    )
    
    session.add(forum)
    session.commit()
    
    print(f"✓ Added forum: r/{subreddit_name}")
    print(f"  URL: {base_url}")
    print(f"  Enabled: {enabled}")
    print(f"  Max pages: {max_pages}")
    
    return forum


def main():
    """Add recommended Reddit subreddits."""
    print("="*60)
    print("ADDING REDDIT SUBREDDITS")
    print("="*60)
    print()
    
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    # Recommended subreddits for casino/gambling monitoring
    subreddits = [
        ('casino', True, 5),           # General casino discussions
        ('gambling', True, 5),         # Broader gambling topics
        ('onlinegambling', True, 5),   # Online casinos specifically
        ('poker', False, 3),           # Poker (disabled by default)
        ('sportsbook', False, 3),      # Sports betting (disabled by default)
    ]
    
    print("Adding subreddits:\n")
    
    for subreddit, enabled, max_pages in subreddits:
        add_reddit_forum(session, subreddit, enabled, max_pages)
        print()
    
    print("="*60)
    print("SUMMARY")
    print("="*60)
    
    # Count forums
    all_forums = session.query(Forum).all()
    reddit_forums = [f for f in all_forums if f.name.startswith('r/')]
    enabled_reddit = [f for f in reddit_forums if f.enabled]
    
    print(f"Total forums: {len(all_forums)}")
    print(f"Reddit forums: {len(reddit_forums)}")
    print(f"Enabled Reddit forums: {len(enabled_reddit)}")
    print()
    
    print("Enabled Reddit forums:")
    for forum in enabled_reddit:
        print(f"  - {forum.name} (max {forum.max_pages} pages)")
    
    session.close()


if __name__ == '__main__':
    main()
