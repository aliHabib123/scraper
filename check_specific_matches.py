#!/usr/bin/env python3
"""Check specific matches by ID."""

import sys
from models.base import get_session_maker
from models import Match

if len(sys.argv) < 2:
    print("Usage: python check_specific_matches.py <id1> <id2> ...")
    sys.exit(1)

session = get_session_maker()()

ids = [int(id_str) for id_str in sys.argv[1:]]

print(f"Checking matches with IDs: {ids}\n")
print("=" * 80)

for match_id in ids:
    match = session.query(Match).filter_by(id=match_id).first()
    
    if not match:
        print(f"\n✗ Match ID {match_id} not found")
        continue
    
    print(f"\nMatch ID: {match_id}")
    print(f"Forum: {match.forum.name}")
    print(f"Keyword: {match.keyword.keyword}")
    print(f"URL: {match.page_url}")
    print(f"Created: {match.created_at}")
    print(f"Snippet: {match.snippet}")
    print("-" * 80)

session.close()

# Check for duplicates based on unique constraint
print("\n" + "=" * 80)
print("DUPLICATE CHECK:")
print("=" * 80)

session = get_session_maker()()
matches = session.query(Match).filter(Match.id.in_(ids)).all()

if len(matches) >= 2:
    # Check if they have same forum_id, keyword_id, page_url
    first = matches[0]
    
    duplicates_found = False
    for i, match in enumerate(matches[1:], 1):
        is_dup = (
            match.forum_id == first.forum_id and
            match.keyword_id == first.keyword_id and
            match.page_url == first.page_url
        )
        
        if is_dup:
            duplicates_found = True
            print(f"\n⚠️  DUPLICATE DETECTED!")
            print(f"Match {first.id} and Match {match.id} have:")
            print(f"  - Same forum: {match.forum.name}")
            print(f"  - Same keyword: {match.keyword.keyword}")
            print(f"  - Same URL: {match.page_url}")
            print(f"\nThis should be prevented by unique constraint!")
        else:
            print(f"\n✓ Match {first.id} and Match {match.id} are different:")
            if match.forum_id != first.forum_id:
                print(f"  - Different forums: {first.forum.name} vs {match.forum.name}")
            if match.keyword_id != first.keyword_id:
                print(f"  - Different keywords: {first.keyword.keyword} vs {match.keyword.keyword}")
            if match.page_url != first.page_url:
                print(f"  - Different URLs")
                print(f"    URL 1: {first.page_url}")
                print(f"    URL 2: {match.page_url}")
    
    if not duplicates_found:
        print("\n✓ No duplicates found based on unique constraint (forum_id, keyword_id, page_url)")

session.close()
