#!/usr/bin/env python3
"""
Forum management CLI tool.
"""

import sys
import json
import argparse
from models.base import get_session_maker
from models import Forum


def list_forums(session):
    """List all forums."""
    forums = session.query(Forum).all()
    
    if not forums:
        print("No forums found.")
        return
    
    print()
    for forum in forums:
        status = "✓ Enabled" if forum.enabled else "✗ Disabled"
        print(f"ID: {forum.id}")
        print(f"Name: {forum.name}")
        print(f"Status: {status}")
        print(f"Type: {forum.type}")
        print(f"Max Pages: {forum.max_pages}")
        print(f"Start URLs ({len(forum.start_urls)}):")
        for url in forum.start_urls:
            print(f"  - {url}")
        print("-" * 60)
    print()


def add_forum(session, name, base_url, start_urls, forum_type='category', max_pages=10):
    """Add a new forum."""
    try:
        # Parse start_urls if it's a JSON string
        if isinstance(start_urls, str):
            start_urls = json.loads(start_urls)
        
        forum = Forum(
            name=name,
            base_url=base_url,
            type=forum_type,
            start_urls=start_urls,
            pagination_type='page_number',
            max_pages=max_pages,
            enabled=True
        )
        session.add(forum)
        session.commit()
        print(f"✓ Added forum: '{name}' (ID: {forum.id})")
    except Exception as e:
        session.rollback()
        print(f"✗ Error: {str(e)}")


def update_forum(session, forum_id, **kwargs):
    """Update forum settings."""
    forum = session.query(Forum).filter_by(id=forum_id).first()
    if not forum:
        print(f"✗ Forum ID {forum_id} not found")
        return
    
    for key, value in kwargs.items():
        if value is not None:
            if key == 'start_urls' and isinstance(value, str):
                value = json.loads(value)
            setattr(forum, key, value)
    
    session.commit()
    print(f"✓ Updated forum: '{forum.name}'")


def remove_forum(session, forum_id):
    """Remove a forum."""
    forum = session.query(Forum).filter_by(id=forum_id).first()
    if not forum:
        print(f"✗ Forum ID {forum_id} not found")
        return
    
    confirm = input(f"Remove forum '{forum.name}'? This will delete all associated matches. (yes/no): ")
    if confirm.lower() == 'yes':
        session.delete(forum)
        session.commit()
        print(f"✓ Removed forum: '{forum.name}'")
    else:
        print("Cancelled")


def toggle_forum(session, forum_id):
    """Enable/disable a forum."""
    forum = session.query(Forum).filter_by(id=forum_id).first()
    if not forum:
        print(f"✗ Forum ID {forum_id} not found")
        return
    
    forum.enabled = not forum.enabled
    session.commit()
    status = "enabled" if forum.enabled else "disabled"
    print(f"✓ Forum '{forum.name}' is now {status}")


def main():
    parser = argparse.ArgumentParser(description='Manage forums')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List
    subparsers.add_parser('list', help='List all forums')
    
    # Add
    add_parser = subparsers.add_parser('add', help='Add a new forum')
    add_parser.add_argument('name', help='Forum name')
    add_parser.add_argument('base_url', help='Base URL')
    add_parser.add_argument('start_urls', help='Start URLs (JSON array or comma-separated)')
    add_parser.add_argument('--type', default='category', help='Forum type (default: category)')
    add_parser.add_argument('--max-pages', type=int, default=10, help='Max pages to crawl (default: 10)')
    
    # Update
    update_parser = subparsers.add_parser('update', help='Update forum settings')
    update_parser.add_argument('id', type=int, help='Forum ID')
    update_parser.add_argument('--name', help='New name')
    update_parser.add_argument('--start-urls', help='New start URLs (JSON array)')
    update_parser.add_argument('--max-pages', type=int, help='New max pages')
    
    # Remove
    remove_parser = subparsers.add_parser('remove', help='Remove a forum')
    remove_parser.add_argument('id', type=int, help='Forum ID to remove')
    
    # Toggle
    toggle_parser = subparsers.add_parser('toggle', help='Enable/disable a forum')
    toggle_parser.add_argument('id', type=int, help='Forum ID to toggle')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        if args.command == 'list':
            list_forums(session)
        elif args.command == 'add':
            # Handle comma-separated or JSON
            if args.start_urls.startswith('['):
                start_urls = json.loads(args.start_urls)
            else:
                start_urls = [url.strip() for url in args.start_urls.split(',')]
            add_forum(session, args.name, args.base_url, start_urls, args.type, args.max_pages)
        elif args.command == 'update':
            update_forum(session, args.id, 
                        name=args.name,
                        start_urls=args.start_urls,
                        max_pages=args.max_pages)
        elif args.command == 'remove':
            remove_forum(session, args.id)
        elif args.command == 'toggle':
            toggle_forum(session, args.id)
    finally:
        session.close()


if __name__ == '__main__':
    main()
