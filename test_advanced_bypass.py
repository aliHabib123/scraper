#!/usr/bin/env python3
"""
Test advanced Cloudflare bypass on blocked forums.
Tests: Reddit, OwnedCore, MoneySavingExpert
"""

from crawler.playwright_crawler import PlaywrightCrawler
from parsers import RedditParser, XenForoParser, MoneySavingExpertParser

def test_reddit():
    print("=" * 70)
    print("Testing Reddit with Advanced Bypass")
    print("=" * 70)
    
    url = 'https://www.reddit.com/r/casino/new.json?limit=5'
    crawler = PlaywrightCrawler(rate_limit=2.0, headless=True, persistent_state=True)
    
    try:
        # Warm up IP
        crawler.warm_up_session('https://www.reddit.com')
        
        # Try to fetch (will fail - Reddit API doesn't work with Playwright HTML mode)
        print("\nAttempting to fetch Reddit...")
        soup = crawler.fetch_page(url)
        
        if soup:
            print("✓ Page loaded (but Reddit needs JSON API, not HTML)")
        else:
            print("❌ Failed to load")
    
    finally:
        crawler.close()
    
    print()

def test_moneysavingexpert():
    print("=" * 70)
    print("Testing MoneySavingExpert with Advanced Bypass")
    print("=" * 70)
    
    url = 'https://forums.moneysavingexpert.com/discussions'
    crawler = PlaywrightCrawler(rate_limit=2.0, headless=True, persistent_state=True)
    
    try:
        # Warm up IP
        crawler.warm_up_session('https://forums.moneysavingexpert.com')
        
        # Try to fetch
        print("\nAttempting to fetch MoneySavingExpert...")
        soup = crawler.fetch_page(url)
        
        if soup:
            parser = MoneySavingExpertParser()
            threads = parser.extract_thread_urls(soup, url)
            print(f"✓ Page loaded successfully")
            print(f"Threads found: {len(threads)}")
            
            if threads:
                print("\nFirst 3 threads:")
                for t in threads[:3]:
                    print(f"  - {t}")
        else:
            print("❌ Failed to load")
    
    finally:
        crawler.close()
    
    print()

if __name__ == '__main__':
    print("\n🔥 Testing Advanced Cloudflare Bypass")
    print("This includes:")
    print("  - Persistent browser state (cookies)")
    print("  - Human-like behavior (mouse, scroll)")
    print("  - IP warm-up (homepage + links + idle 30-60s)")
    print("\nNote: First run will take 1-2 minutes due to warm-up.\n")
    
    # Test MoneySavingExpert (most likely to work)
    test_moneysavingexpert()
    
    # Reddit won't work (needs residential IP + JSON API)
    # test_reddit()
