#!/usr/bin/env python3
"""
Clear all matches from the database.
Useful for testing or starting fresh.
"""

from models import Match
from models.base import get_session_maker


def clear_all_matches():
    """Delete all matches from the database."""
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        # Count existing matches
        count = session.query(Match).count()
        
        if count == 0:
            print("✓ No matches to delete")
            return
        
        # Confirm deletion
        print(f"⚠️  Found {count} matches in the database")
        response = input("Delete all matches? [y/N]: ")
        
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Delete all matches
        session.query(Match).delete()
        session.commit()
        
        print(f"✓ Deleted {count} matches")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {str(e)}")
        
    finally:
        session.close()


if __name__ == '__main__':
    clear_all_matches()
