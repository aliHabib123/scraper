#!/usr/bin/env python3
"""
Test parsers locally to diagnose forum crawling issues.
"""

from crawler.base_crawler import BaseCrawler
from parsers import AskGamblersParser, BigWinBoardParser, RedditParser
from bs4 import BeautifulSoup

def test_askgamblers():
    print("=" * 70)
    print("Testing AskGamblers Parser")
    print("=" * 70)
    
    url = 'https://forum.askgamblers.com/forum/21-online-slot-discussions/'
    crawler = BaseCrawler(rate_limit=0.5)
    
    soup = crawler.fetch_page(url)
    if not soup:
        print("❌ Failed to fetch page")
        return
    
    parser = AskGamblersParser()
    threads = parser.extract_thread_urls(soup, url)
    
    print(f"\n✓ Fetched page successfully")
    print(f"Threads found: {len(threads)}")
    
    if threads:
        print("\nFirst 3 threads:")
        for t in threads[:3]:
            print(f"  - {t}")
    else:
        print("\n⚠️  No threads found - parser may need updating")
    
    print()

def test_bigwinboard():
    print("=" * 70)
    print("Testing BigWinBoard Parser")
    print("=" * 70)
    
    url = 'https://www.bigwinboard.com/forum/casino-complaints/'
    crawler = BaseCrawler(rate_limit=0.5)
    
    soup = crawler.fetch_page(url)
    if not soup:
        print("❌ Failed to fetch page")
        return
    
    parser = BigWinBoardParser()
    threads = parser.extract_thread_urls(soup, url)
    
    print(f"\n✓ Fetched page successfully")
    print(f"Threads found: {len(threads)}")
    
    if threads:
        print("\nFirst 3 threads:")
        for t in threads[:3]:
            print(f"  - {t}")
    else:
        print("\n⚠️  No threads found - parser may need updating")
    
    print()

def test_reddit():
    print("=" * 70)
    print("Testing Reddit API")
    print("=" * 70)
    
    url = 'https://www.reddit.com/r/casino/new.json?limit=5'
    crawler = BaseCrawler(rate_limit=0.5)
    
    soup = crawler.fetch(url, json_mode=True)
    if not soup:
        print("❌ Failed to fetch Reddit API (may be blocked)")
        return
    
    parser = RedditParser()
    threads = parser.extract_thread_urls(soup, 'https://www.reddit.com/r/casino')
    
    print(f"\n✓ Fetched Reddit API successfully")
    print(f"Threads found: {len(threads)}")
    
    if threads:
        print("\nFirst 3 threads:")
        for t in threads[:3]:
            print(f"  - {t}")
    else:
        print("\n⚠️  No threads found")
    
    print()

if __name__ == '__main__':
    test_askgamblers()
    test_bigwinboard()
    test_reddit()
