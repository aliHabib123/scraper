#!/usr/bin/env python3

from models import Forum
from models.base import get_session_maker


def add_ownedcore_gambling(session):
    existing = session.query(Forum).filter(Forum.name == "ownedcore.com").first()
    if existing:
        print(f"Forum 'ownedcore.com' already exists (ID: {existing.id})")
        return existing

    # Main gambling forum URL (includes all threads + sub-forums)
    start_urls = [
        "https://www.ownedcore.com/forums/gambling/",
    ]

    forum = Forum(
        name="ownedcore.com",
        base_url="https://www.ownedcore.com",
        type='category',
        start_urls=start_urls,
        pagination_type='custom',  # Uses indexN.html pagination
        enabled=True,
        max_pages=3,  # Adjust as needed
    )

    session.add(forum)
    session.commit()

    print("✓ Added forum: ownedcore.com")
    print("  Sub-forums:")
    for url in start_urls:
        print(f"    - {url}")
    print("  Enabled: True")
    print("  Max pages: 3")
    print("\n⚠️  Note: OwnedCore has Cloudflare protection")
    print("  This forum will use Playwright (non-headless) like CasinoMeister")

    return forum


def main():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        add_ownedcore_gambling(session)
    finally:
        session.close()


if __name__ == '__main__':
    main()
