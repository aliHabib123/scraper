#!/usr/bin/env python3
"""Quick test of pagination and CIBC thread detection."""

from parsers import CasinoGuruParser
from crawler import BaseCrawler

parser = CasinoGuruParser()
crawler = BaseCrawler()

base_url = "https://casino.guru/forum/general-gambling-discussion"

print("Testing /N pagination format:\n")

for page_num in range(1, 4):
    url = parser.get_paginated_url(base_url, page_num)
    print(f"Page {page_num}: {url}")
    
    soup = crawler.fetch_page(url)
    if soup:
        threads = parser.extract_thread_urls(soup, url)
        print(f"  ✓ Found {len(threads)} threads")
        
        # Check for CIBC
        cibc_threads = [t for t in threads if "cibc" in t.lower()]
        if cibc_threads:
            print(f"  ✓✓✓ CIBC thread found!")
    else:
        print(f"  ✗ Failed to fetch")
    print()
