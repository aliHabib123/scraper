#!/usr/bin/env python3
"""
Import data from MySQL export JSON file into SQLite database.

Usage:
    python import_sqlite.py

Requirements:
    - mysql_export.json file (created by export_mysql.py)
    - .env configured with SQLite DATABASE_URL
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from models.base import get_session_maker, init_db
from models import Forum, Keyword, Match

# Load environment variables
load_dotenv()

def parse_datetime(dt_str):
    """Parse ISO format datetime string to datetime object."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except:
        return None

def import_data():
    """Import all data from JSON to SQLite database."""
    print("=" * 70)
    print("SQLite Database Import")
    print("=" * 70)
    
    # Check if export file exists
    export_file = 'mysql_export.json'
    if not os.path.exists(export_file):
        print(f"\n❌ Error: {export_file} not found!")
        print("\nPlease ensure you have:")
        print("1. Run 'python export_mysql.py' on your Mac")
        print("2. Copied 'mysql_export.json' to this directory")
        return False
    
    # Check database configuration
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("\n❌ Error: DATABASE_URL not set in .env file!")
        print("\nPlease set DATABASE_URL in .env:")
        print("DATABASE_URL=sqlite:///scraper.db")
        return False
    
    if not db_url.startswith('sqlite'):
        print(f"\n⚠️  Warning: DATABASE_URL is not SQLite: {db_url}")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Import cancelled.")
            return False
    
    # Load export data
    print(f"\nLoading {export_file}...")
    with open(export_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   Export Date: {data['export_date']}")
    print(f"   Source: {data['database_type']}")
    print(f"   Forums: {data['counts']['forums']}")
    print(f"   Keywords: {data['counts']['keywords']}")
    print(f"   Matches: {data['counts']['matches']}")
    
    # Initialize SQLite database
    print(f"\nInitializing SQLite database...")
    init_db()
    print(f"   ✓ Database initialized")
    
    # Get session
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Import Forums
        print("\n[1/3] Importing Forums...")
        for forum_data in data['forums']:
            forum = Forum(
                id=forum_data['id'],
                name=forum_data['name'],
                base_url=forum_data['base_url'],
                type=forum_data['type'],
                start_urls=forum_data['start_urls'],
                pagination_type=forum_data['pagination_type'],
                max_pages=forum_data['max_pages'],
                enabled=forum_data['enabled'],
                created_at=parse_datetime(forum_data.get('created_at')),
                updated_at=parse_datetime(forum_data.get('updated_at')),
            )
            session.add(forum)
        session.commit()
        print(f"   ✓ Imported {len(data['forums'])} forums")
        
        # Import Keywords
        print("\n[2/3] Importing Keywords...")
        for keyword_data in data['keywords']:
            keyword = Keyword(
                id=keyword_data['id'],
                keyword=keyword_data['keyword'],
                enabled=keyword_data['enabled'],
                created_at=parse_datetime(keyword_data.get('created_at')),
                updated_at=parse_datetime(keyword_data.get('updated_at')),
            )
            session.add(keyword)
        session.commit()
        print(f"   ✓ Imported {len(data['keywords'])} keywords")
        
        # Import Matches
        print("\n[3/3] Importing Matches...")
        batch_size = 1000
        matches_data = data['matches']
        total_matches = len(matches_data)
        
        for i in range(0, total_matches, batch_size):
            batch = matches_data[i:i + batch_size]
            for match_data in batch:
                match = Match(
                    id=match_data['id'],
                    forum_id=match_data['forum_id'],
                    keyword_id=match_data['keyword_id'],
                    page_url=match_data['page_url'],
                    snippet=match_data['snippet'],
                    created_at=parse_datetime(match_data.get('created_at')),
                )
                session.add(match)
            session.commit()
            print(f"   Progress: {min(i + batch_size, total_matches)}/{total_matches} matches")
        
        print(f"   ✓ Imported {total_matches} matches")
        
        # Verify import
        print("\n[4/4] Verifying import...")
        forum_count = session.query(Forum).count()
        keyword_count = session.query(Keyword).count()
        match_count = session.query(Match).count()
        
        print(f"   Forums in database: {forum_count}")
        print(f"   Keywords in database: {keyword_count}")
        print(f"   Matches in database: {match_count}")
        
        # Check if counts match
        if (forum_count == len(data['forums']) and 
            keyword_count == len(data['keywords']) and 
            match_count == len(data['matches'])):
            print(f"   ✓ Verification successful - all data imported correctly")
        else:
            print(f"   ⚠️  Warning: Count mismatch detected!")
            return False
        
        # Summary
        print("\n" + "=" * 70)
        print("Import Summary")
        print("=" * 70)
        print(f"Forums:   {forum_count}")
        print(f"Keywords: {keyword_count}")
        print(f"Matches:  {match_count}")
        print(f"\nDatabase: {db_url}")
        print("=" * 70)
        
        print("\n✅ Import successful!")
        print("\nYour SQLite database is ready to use.")
        print("You can now run: python main.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
        
    finally:
        session.close()

if __name__ == '__main__':
    success = import_data()
    exit(0 if success else 1)
