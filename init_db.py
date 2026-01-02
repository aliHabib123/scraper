#!/usr/bin/env python3
"""
Database initialization script.

Creates tables and optionally loads sample data.
"""

import sys
import argparse
from models.base import init_db, get_session_maker
from models import Forum, Keyword

def create_sample_data(session):
    """Create sample forum and keywords for testing."""
    
    # Create sample forum for casino.guru
    forum = Forum(
        name='casino.guru',
        base_url='https://casino.guru',
        type='category',
        start_urls=[
            'https://casino.guru/forum'
        ],
        pagination_type='page_number',
        max_pages=5,
        enabled=True
    )
    session.add(forum)
    
    # Create sample keywords
    keywords = [
        Keyword(keyword='bonus', enabled=True),
        Keyword(keyword='scam', enabled=True),
        Keyword(keyword='withdrawal', enabled=True),
    ]
    
    for keyword in keywords:
        session.add(keyword)
    
    session.commit()
    print("Sample data created successfully!")
    print(f"- Forum: {forum.name}")
    print(f"- Keywords: {', '.join(k.keyword for k in keywords)}")


def main():
    parser = argparse.ArgumentParser(description='Initialize database')
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='Load sample forums and keywords'
    )
    
    args = parser.parse_args()
    
    try:
        print("Initializing database tables...")
        init_db()
        print("✓ Tables created successfully")
        
        if args.sample_data:
            print("\nLoading sample data...")
            SessionMaker = get_session_maker()
            session = SessionMaker()
            create_sample_data(session)
            session.close()
        
        print("\nDatabase initialization complete!")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
