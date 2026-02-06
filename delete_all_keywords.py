#!/usr/bin/env python3
"""
Delete all keywords from the database.

WARNING: This will delete ALL keywords and their associated matches.
"""

from models.base import get_session_maker
from models import Keyword


def delete_all_keywords(session):
    """Delete all keywords from database."""
    
    # Count existing keywords
    keyword_count = session.query(Keyword).count()
    
    if keyword_count == 0:
        print("No keywords found in database.")
        return
    
    print("=" * 70)
    print("⚠️  WARNING: Delete All Keywords")
    print("=" * 70)
    print(f"\nThis will permanently delete {keyword_count} keywords.")
    print("All associated matches will also be deleted (CASCADE).")
    print("\nAre you sure you want to continue?")
    
    confirm = input("\nType 'DELETE ALL' to confirm: ")
    
    if confirm != 'DELETE ALL':
        print("\n❌ Cancelled - no keywords were deleted.")
        return
    
    # Delete all keywords
    print(f"\nDeleting {keyword_count} keywords...")
    session.query(Keyword).delete()
    session.commit()
    
    print("\n" + "=" * 70)
    print(f"✓ Successfully deleted {keyword_count} keywords")
    print("=" * 70)


def main():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        delete_all_keywords(session)
    finally:
        session.close()


if __name__ == '__main__':
    main()
