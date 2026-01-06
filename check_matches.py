#!/usr/bin/env python3
"""Check matches in database."""

from models.base import get_session_maker
from models import Match, Keyword, Forum

session = get_session_maker()()

# Total matches
total = session.query(Match).count()
print(f'Total matches found: {total}\n')

# By keyword
print('Matches by keyword:')
keywords = session.query(Keyword).all()
for kw in keywords:
    count = session.query(Match).filter_by(keyword_id=kw.id).count()
    print(f'  {kw.keyword}: {count}')

print()

# Sample matches
if total > 0:
    print('Sample matches:')
    matches = session.query(Match).limit(5).all()
    for m in matches:
        print(f'\nKeyword: {m.keyword.keyword}')
        print(f'URL: {m.page_url}')
        print(f'Snippet: {m.snippet[:150]}...')

session.close()
