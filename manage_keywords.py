#!/usr/bin/env python3
"""
Keyword management CLI tool.
"""

import sys
import argparse
from models.base import get_session_maker
from models import Keyword


def list_keywords(session):
    """List all keywords."""
    keywords = session.query(Keyword).all()
    
    if not keywords:
        print("No keywords found.")
        return
    
    print(f"\n{'ID':<5} {'Keyword':<30} {'Enabled':<10}")
    print("-" * 50)
    for kw in keywords:
        status = "✓ Yes" if kw.enabled else "✗ No"
        print(f"{kw.id:<5} {kw.keyword:<30} {status:<10}")
    print()


def add_keyword(session, keyword, enabled=True):
    """Add a new keyword."""
    try:
        kw = Keyword(keyword=keyword, enabled=enabled)
        session.add(kw)
        session.commit()
        print(f"✓ Added keyword: '{keyword}'")
    except Exception as e:
        session.rollback()
        print(f"✗ Error: {str(e)}")


def remove_keyword(session, keyword_id):
    """Remove a keyword by ID."""
    kw = session.query(Keyword).filter_by(id=keyword_id).first()
    if not kw:
        print(f"✗ Keyword ID {keyword_id} not found")
        return
    
    confirm = input(f"Remove keyword '{kw.keyword}'? This will delete all associated matches. (yes/no): ")
    if confirm.lower() == 'yes':
        session.delete(kw)
        session.commit()
        print(f"✓ Removed keyword: '{kw.keyword}'")
    else:
        print("Cancelled")


def toggle_keyword(session, keyword_id):
    """Enable/disable a keyword."""
    kw = session.query(Keyword).filter_by(id=keyword_id).first()
    if not kw:
        print(f"✗ Keyword ID {keyword_id} not found")
        return
    
    kw.enabled = not kw.enabled
    session.commit()
    status = "enabled" if kw.enabled else "disabled"
    print(f"✓ Keyword '{kw.keyword}' is now {status}")


def main():
    parser = argparse.ArgumentParser(description='Manage keywords')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List
    subparsers.add_parser('list', help='List all keywords')
    
    # Add
    add_parser = subparsers.add_parser('add', help='Add a new keyword')
    add_parser.add_argument('keyword', help='Keyword to add')
    add_parser.add_argument('--disabled', action='store_true', help='Add as disabled')
    
    # Remove
    remove_parser = subparsers.add_parser('remove', help='Remove a keyword')
    remove_parser.add_argument('id', type=int, help='Keyword ID to remove')
    
    # Toggle
    toggle_parser = subparsers.add_parser('toggle', help='Enable/disable a keyword')
    toggle_parser.add_argument('id', type=int, help='Keyword ID to toggle')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        if args.command == 'list':
            list_keywords(session)
        elif args.command == 'add':
            add_keyword(session, args.keyword, enabled=not args.disabled)
        elif args.command == 'remove':
            remove_keyword(session, args.id)
        elif args.command == 'toggle':
            toggle_keyword(session, args.id)
    finally:
        session.close()


if __name__ == '__main__':
    main()
