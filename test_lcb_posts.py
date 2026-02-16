#!/usr/bin/env python3
"""
Test LCB post extraction to find correct selectors.
"""

import os
from bs4 import BeautifulSoup
from crawler.playwright_crawler import PlaywrightCrawler

# Use Playwright to fetch thread page
url = 'https://lcb.org/onlinecasinobonusforum/casinos/new-synot-games-slots'
crawler = PlaywrightCrawler(rate_limit=2.0, headless=False, persistent_state=True)

print(f"Fetching: {url}")
soup = crawler.fetch(url, json_mode=False)

if not soup:
    print("Failed to fetch page")
    exit(1)

print(f"\n{'='*70}")
print("Looking for post elements...")
print('='*70)

# Test various selectors
selectors = [
    '.post',
    '.message',
    '.comment',
    '.forum-post',
    'article.post',
    'div[class*="post"]',
    'div[class*="message"]',
    '.topic-post',
    '.reply',
    'article',
    '[id^="msg"]',
    '.windowbg',
    '.post_wrapper',
]

for selector in selectors:
    elements = soup.select(selector)
    if elements:
        print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
        # Show first element's classes and id
        first = elements[0]
        print(f"  First element tag: {first.name}")
        print(f"  Classes: {first.get('class', [])}")
        print(f"  ID: {first.get('id', 'none')}")
        print(f"  Text preview: {first.get_text(strip=True)[:100]}...")

# Try to find any elements that look like posts
print(f"\n{'='*70}")
print("Looking for elements with 'msg' in ID...")
print('='*70)

msg_elements = soup.find_all(id=lambda x: x and 'msg' in x.lower())
print(f"Found {len(msg_elements)} elements with 'msg' in ID")
for elem in msg_elements[:3]:
    print(f"  - Tag: {elem.name}, ID: {elem.get('id')}, Classes: {elem.get('class', [])}")

print(f"\n{'='*70}")
print("Looking for common forum structures...")
print('='*70)

# Check for SMF (Simple Machines Forum) structure
if soup.find(class_='windowbg'):
    print("✓ Looks like SMF forum (windowbg class found)")
    posts = soup.find_all(class_='windowbg')
    print(f"  Found {len(posts)} posts with .windowbg")

# Check for other structures
if soup.find(id=lambda x: x and x.startswith('msg')):
    print("✓ Found elements with id starting with 'msg'")
    msgs = soup.find_all(id=lambda x: x and x.startswith('msg'))
    print(f"  Found {len(msgs)} elements")

crawler.close()
print(f"\n{'='*70}")
print("Test complete")
print('='*70)
