#!/usr/bin/env python3
"""
Debug script to inspect casino.guru HTML structure and test parser.
"""

import httpx
from bs4 import BeautifulSoup
from parsers import CasinoGuruParser

def inspect_page(url):
    """Fetch and inspect a casino.guru page."""
    
    print(f"Fetching: {url}\n")
    
    # Fetch page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = httpx.get(url, headers=headers, follow_redirects=True, timeout=30)
    print(f"Status: {response.status_code}\n")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Save HTML for inspection
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("✓ Saved HTML to debug_page.html\n")
    
    # Find all links
    all_links = soup.find_all('a', href=True)
    print(f"Total links found: {len(all_links)}\n")
    
    # Filter links that might be threads
    potential_threads = []
    for link in all_links:
        href = link['href']
        text = link.get_text(strip=True)
        
        # Skip empty links, anchors, javascript
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Look for forum-like URLs
        if any(pattern in href.lower() for pattern in ['/forum/', '/topic/', '/thread/', '/discussion/', '/post/']):
            potential_threads.append({
                'href': href,
                'text': text[:100],
                'classes': link.get('class', [])
            })
    
    print(f"Potential thread links: {len(potential_threads)}\n")
    
    # Show first 10
    print("First 10 potential threads:")
    print("-" * 80)
    for i, thread in enumerate(potential_threads[:10], 1):
        print(f"{i}. {thread['text']}")
        print(f"   URL: {thread['href']}")
        print(f"   Classes: {thread['classes']}")
        print()
    
    # Test parser
    print("=" * 80)
    print("Testing CasinoGuruParser:")
    print("=" * 80)
    parser = CasinoGuruParser()
    thread_urls = parser.extract_thread_urls(soup, url)
    print(f"Parser extracted: {len(thread_urls)} thread URLs\n")
    
    if thread_urls:
        print("First 5 URLs:")
        for url in thread_urls[:5]:
            print(f"  - {url}")
    else:
        print("⚠ No URLs extracted by parser!")
        print("\nDebugging info:")
        print("Looking for common forum containers...")
        
        # Check for common containers
        for selector in ['.topic-list', '.thread-list', '.forum-list', '.discussions', 'main', '.content']:
            elem = soup.select_one(selector)
            if elem:
                print(f"  ✓ Found: {selector}")
            else:
                print(f"  ✗ Not found: {selector}")


if __name__ == '__main__':
    # Test with casino.guru forum page
    test_url = 'https://casino.guru/forum/casinos'
    inspect_page(test_url)
