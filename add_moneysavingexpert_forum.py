#!/usr/bin/env python3

from models import Forum
from models.base import get_session_maker


def add_moneysavingexpert(session):
    existing = session.query(Forum).filter(Forum.name == "moneysavingexpert.com").first()
    if existing:
        print(f"Forum 'moneysavingexpert.com' already exists (ID: {existing.id})")
        return existing

    start_urls = [
        "https://forums.moneysavingexpert.com/discussions",
    ]

    forum = Forum(
        name="moneysavingexpert.com",
        base_url="https://forums.moneysavingexpert.com",
        type='category',
        start_urls=start_urls,
        pagination_type='page_number',
        enabled=True,
        max_pages=10,
    )

    session.add(forum)
    session.commit()

    print("✓ Added forum: moneysavingexpert.com")
    print("  Start URLs:")
    for url in start_urls:
        print(f"    - {url}")
    print("  Enabled: True")
    print("  Max pages: 10")

    return forum


def main():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        add_moneysavingexpert(session)
    finally:
        session.close()


if __name__ == '__main__':
    main()
