#!/usr/bin/env python3

from models import Forum
from models.base import get_session_maker


def add_bigwinboard_casino_complaints(session):
    existing = session.query(Forum).filter(Forum.name == "bigwinboard.com").first()
    if existing:
        print(f"Forum 'bigwinboard.com' already exists (ID: {existing.id})")
        return existing

    start_url = "https://www.bigwinboard.com/forum/casino-complaints/"

    forum = Forum(
        name="bigwinboard.com",
        base_url="https://www.bigwinboard.com",
        type='category',
        start_urls=[start_url],
        pagination_type='page_number',
        enabled=True,
        max_pages=10,
    )

    session.add(forum)
    session.commit()

    print("✓ Added forum: bigwinboard.com")
    print(f"  Start URL: {start_url}")
    print("  Enabled: True")
    print("  Max pages: 10")

    return forum


def main():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        add_bigwinboard_casino_complaints(session)
    finally:
        session.close()


if __name__ == '__main__':
    main()
