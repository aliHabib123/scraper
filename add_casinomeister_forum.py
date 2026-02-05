#!/usr/bin/env python3

from models import Forum
from models.base import get_session_maker


def add_casinomeister_complaints(session):
    existing = session.query(Forum).filter(Forum.name == "casinomeister.com").first()
    if existing:
        print(f"Forum 'casinomeister.com' already exists (ID: {existing.id})")
        return existing

    start_urls = [
        "https://www.casinomeister.com/forums/community/casinomeister-complaints-notes.508/",
        "https://www.casinomeister.com/forums/community/casino-complaints-non-bonus-issues/",
        "https://www.casinomeister.com/forums/community/casino-complaints-bonus-issues/",
        "https://www.casinomeister.com/forums/community/source-of-wealth-issues.438/",
        "https://www.casinomeister.com/forums/community/self-exclusion-responsible-gambling-complaints.347/",
        "https://www.casinomeister.com/forums/community/payment-processing-issues/",
        "https://www.casinomeister.com/forums/community/1668-jaz-licensee-issues.411/",
        "https://www.casinomeister.com/forums/community/virtual-group-issues.428/",
        "https://www.casinomeister.com/forums/community/sportsbook-complaints/",
        "https://www.casinomeister.com/forums/community/poker-complaints/",
        "https://www.casinomeister.com/forums/community/casino-spam-complaints/",
        "https://www.casinomeister.com/forums/community/other-complaints/",
    ]

    forum = Forum(
        name="casinomeister.com",
        base_url="https://www.casinomeister.com",
        type='category',
        start_urls=start_urls,
        pagination_type='page_number',
        enabled=True,
        max_pages=1,
    )

    session.add(forum)
    session.commit()

    print("✓ Added forum: casinomeister.com")
    print("  Sub-forums:")
    for url in start_urls:
        print(f"    - {url}")
    print("  Enabled: True")
    print("  Max pages: 1")

    return forum


def main():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        add_casinomeister_complaints(session)
    finally:
        session.close()


if __name__ == '__main__':
    main()
