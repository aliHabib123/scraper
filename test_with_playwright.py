#!/usr/bin/env python3
"""
Test AskGamblers and BigWinBoard with Playwright to handle JavaScript rendering.
"""

from crawler.playwright_crawler import PlaywrightCrawler
from parsers import AskGamblersParser, BigWinBoardParser

def test_askgamblers():
    print("=" * 70)
    print("Testing AskGamblers with Playwright")
    print("=" * 70)
    
    url = 'https://forum.askgamblers.com/forum/21-online-slot-discussions/'
    crawler = PlaywrightCrawler(rate_limit=1.0, headless=True)
    
    try:
        soup = crawler.fetch_page(url)
        if not soup:
            print("❌ Failed to fetch page")
            return
        
        parser = AskGamblersParser()
        threads = parser.extract_thread_urls(soup, url)
        
        print(f"\n✓ Fetched page with Playwright")
        print(f"Threads found: {len(threads)}")
        
        if threads:
            print("\nFirst 5 threads:")
            for t in threads[:5]:
                print(f"  - {t}")
        else:
            print("\n⚠️  No threads found")
    
    finally:
        crawler.close()
    
    print()

def test_bigwinboard():
    print("=" * 70)
    print("Testing BigWinBoard with Playwright")
    print("=" * 70)
    
    url = 'https://www.bigwinboard.com/forum/casino-complaints/'
    crawler = PlaywrightCrawler(rate_limit=1.0, headless=True)
    
    try:
        soup = crawler.fetch_page(url)
        if not soup:
            print("❌ Failed to fetch page")
            return
        
        parser = BigWinBoardParser()
        threads = parser.extract_thread_urls(soup, url)
        
        print(f"\n✓ Fetched page with Playwright")
        print(f"Threads found: {len(threads)}")
        
        if threads:
            print("\nFirst 5 threads:")
            for t in threads[:5]:
                print(f"  - {t}")
        else:
            print("\n⚠️  No threads found")
    
    finally:
        crawler.close()
    
    print()

if __name__ == '__main__':
    test_askgamblers()
    test_bigwinboard()
