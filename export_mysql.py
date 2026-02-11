#!/usr/bin/env python3
"""
Export all data from MySQL database to JSON files for migration to SQLite.

Usage:
    python export_mysql.py

Output:
    - mysql_export.json (all data in one file)
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from models.base import get_session_maker
from models import Forum, Keyword, Match

# Load environment variables
load_dotenv()

def serialize_datetime(obj):
    """Convert datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_data():
    """Export all database tables to JSON."""
    print("=" * 70)
    print("MySQL Database Export")
    print("=" * 70)
    print(f"\nConnecting to MySQL database...")
    
    # Get database session
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Export Forums
        print("\n[1/3] Exporting Forums...")
        forums = session.query(Forum).all()
        forums_data = []
        for forum in forums:
            forums_data.append({
                'id': forum.id,
                'name': forum.name,
                'base_url': forum.base_url,
                'type': forum.type,
                'start_urls': forum.start_urls,
                'pagination_type': forum.pagination_type,
                'max_pages': forum.max_pages,
                'enabled': forum.enabled,
                'created_at': forum.created_at.isoformat() if forum.created_at else None,
                'updated_at': forum.updated_at.isoformat() if forum.updated_at else None,
            })
        print(f"   ✓ Exported {len(forums_data)} forums")
        
        # Export Keywords
        print("\n[2/3] Exporting Keywords...")
        keywords = session.query(Keyword).all()
        keywords_data = []
        for keyword in keywords:
            keywords_data.append({
                'id': keyword.id,
                'keyword': keyword.keyword,
                'enabled': keyword.enabled,
                'created_at': keyword.created_at.isoformat() if keyword.created_at else None,
                'updated_at': keyword.updated_at.isoformat() if keyword.updated_at else None,
            })
        print(f"   ✓ Exported {len(keywords_data)} keywords")
        
        # Export Matches
        print("\n[3/3] Exporting Matches...")
        matches = session.query(Match).all()
        matches_data = []
        for match in matches:
            matches_data.append({
                'id': match.id,
                'forum_id': match.forum_id,
                'keyword_id': match.keyword_id,
                'page_url': match.page_url,
                'snippet': match.snippet,
                'created_at': match.created_at.isoformat() if match.created_at else None,
            })
        print(f"   ✓ Exported {len(matches_data)} matches")
        
        # Combine all data
        export_data = {
            'export_date': datetime.now().isoformat(),
            'database_type': 'mysql',
            'forums': forums_data,
            'keywords': keywords_data,
            'matches': matches_data,
            'counts': {
                'forums': len(forums_data),
                'keywords': len(keywords_data),
                'matches': len(matches_data),
            }
        }
        
        # Write to JSON file
        output_file = 'mysql_export.json'
        print(f"\n[4/4] Writing to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Calculate file size
        file_size = os.path.getsize(output_file)
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        print(f"   ✓ Export complete: {size_str}")
        
        # Summary
        print("\n" + "=" * 70)
        print("Export Summary")
        print("=" * 70)
        print(f"Forums:   {len(forums_data)}")
        print(f"Keywords: {len(keywords_data)}")
        print(f"Matches:  {len(matches_data)}")
        print(f"\nOutput file: {output_file}")
        print("=" * 70)
        
        print("\n✅ Export successful!")
        print("\nNext steps:")
        print("1. Copy 'mysql_export.json' to your Windows laptop")
        print("2. Run 'python import_sqlite.py' on Windows to import data")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during export: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

if __name__ == '__main__':
    success = export_data()
    exit(0 if success else 1)
