#!/usr/bin/env python3
"""
Add gambling-related company keywords to the database.

Keywords extracted from keywords.csv with smart derivatives:
- Full company names and URLs
- Multi-word combinations
- Individual distinctive words
"""

from models.base import get_session_maker
from models import Keyword


# All keywords to add (extracted from CSV with derivatives)
KEYWORDS = [
    # Infinity Europ SARL - amorzee.com
    "Infinity Europ SARL",
    "Infinity Europ",
    "Europ SARL",
    "Europ",
    "amorzee.com",
    "amorzee",
    
    # Ennestrad Service Oü - articlealchemy.net, shorevida.com
    "Ennestrad Service",
    "Ennestrad",
    "articlealchemy.net",
    "articlealchemy",
    "shorevida.com",
    "shorevida",
    
    # XALTRONIS LIMITED - Cloud2phone.com
    "XALTRONIS LIMITED",
    "XALTRONIS",
    "Cloud2phone.com",
    "cloud2phone",
    
    # Jagmoth Digital Oü - contentmagiconline.com
    "Jagmoth Digital",
    "Jagmoth",
    "contentmagiconline.com",
    "contentmagiconline",
    
    # CiBC Company KFT - digikeyboard.com, digitalkeyboard.*
    "CiBC Company",
    "CiBC",
    "digikeyboard.com",
    "digikeyboard",
    "digitalkeyboard.co.uk",
    "digitalkeyboard.net",
    "digitalkeyboard",
    
    # Karlov International Oü - e-content4u.net
    "Karlov International",
    "Karlov",
    "e-content4u.net",
    "e-content4u",
    
    # Nalvirox Tech Limited - gearovo.com
    "Nalvirox Tech",
    "Nalvirox",
    "gearovo.com",
    "gearovo",
    
    # DI2 Sky Limited - globalsportplus.*
    "DI2 Sky",
    "DI2",
    "globalsportplus.co.uk",
    "globalsportplus.com",
    "globalsportplus.net",
    "globalsportplus.org",
    "globalsportplus",
    
    # BIVOLIX GLOBAL LIMITED - golfinex.com
    "BIVOLIX GLOBAL",
    "BIVOLIX",
    "golfinex.com",
    "golfinex",
    
    # UAB Krivon Global - brightspacia.com
    "Krivon Global",
    "Krivon",
    "brightspacia.com",
    "brightspacia",
    
    # EchoSpark Oü - dartstation.shop
    "EchoSpark",
    "dartstation.shop",
    "dartstation",
    
    # Inventia LTD - easyfitplanner.com
    "Inventia",
    "easyfitplanner.com",
    "easyfitplanner",
    
    # Panther Retail Global EOOD - knockoutco.net
    "Panther Retail",
    "Panther",
    "knockoutco.net",
    "knockoutco",
    
    # Boros Agency Oü - poolnation.store, scriptgpt.online
    "Boros Agency",
    "Boros",
    "poolnation.store",
    "poolnation",
    "scriptgpt.online",
    "scriptgpt",
    
    # UAB Anivela - primekickz.shop
    "Anivela",
    "primekickz.shop",
    "primekickz",
    
    # Vista Content Experts s.r.o. - provollyworld.com
    "Vista Content",
    "Vista",
    "provollyworld.com",
    "provollyworld",
    
    # Codemania LTD - upskillbridge.net
    "Codemania",
    "upskillbridge.net",
    "upskillbridge",
    
    # Yaffimayah Vision Oü - onlinecontenthub.net
    "Yaffimayah Vision",
    "Yaffimayah",
    "onlinecontenthub.net",
    "onlinecontenthub",
    
    # Typhon SRL - puresounds.cloud
    "Typhon",
    "puresounds.cloud",
    "puresounds",
    
    # Astronix Group Limited - skillcrafters.net
    "Astronix Group",
    "Astronix",
    "skillcrafters.net",
    "skillcrafters",
    
    # Slavin Technology Ltd - snookerhallsupplies.com
    "Slavin Technology",
    "Slavin",
    "snookerhallsupplies.com",
    "snookerhallsupplies",
    
    # Mastar General Limited - wallvibe.net
    "Mastar General",
    "Mastar",
    "wallvibe.net",
    "wallvibe",
    
    # Artavena Virtual Oü - writemycontent.net
    "Artavena Virtual",
    "Artavena",
    "writemycontent.net",
    "writemycontent",
]


def add_keywords(session):
    """Add all keywords to database, skipping duplicates."""
    added = 0
    skipped = 0
    
    print("=" * 70)
    print("Adding Keywords to Database")
    print("=" * 70)
    print(f"\nTotal keywords to process: {len(KEYWORDS)}\n")
    
    for keyword in KEYWORDS:
        # Check if already exists
        existing = session.query(Keyword).filter_by(keyword=keyword).first()
        if existing:
            skipped += 1
            print(f"  - Skipped (exists): {keyword}")
            continue
        
        # Add new keyword
        kw = Keyword(keyword=keyword, enabled=True)
        session.add(kw)
        added += 1
        print(f"  + Added: {keyword}")
    
    session.commit()
    
    print("\n" + "=" * 70)
    print(f"✓ Import complete!")
    print(f"  Added: {added} new keywords")
    print(f"  Skipped: {skipped} duplicates")
    print("=" * 70)


def main():
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    try:
        add_keywords(session)
    finally:
        session.close()


if __name__ == '__main__':
    main()
