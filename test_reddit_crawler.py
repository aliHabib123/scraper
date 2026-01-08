#!/usr/bin/env python3
"""Test Reddit crawler functionality."""

from crawler import BaseCrawler
from parsers import RedditParser

# Test subreddit
subreddit = "casino"
base_url = f"https://www.reddit.com/r/{subreddit}"

print("="*60)
print(f"TESTING REDDIT CRAWLER: r/{subreddit}")
print("="*60)
print()

crawler = BaseCrawler()
parser = RedditParser()

# Step 1: Test fetching subreddit listing
print("Step 1: Fetching subreddit listing...")
list_url = parser.get_paginated_url(base_url, 1)
print(f"URL: {list_url}")

json_data = crawler.fetch_json(list_url)
if not json_data:
    print("✗ Failed to fetch subreddit listing")
    exit(1)

print("✓ Fetched JSON data successfully")
print()

# Step 2: Extract post URLs
print("Step 2: Extracting post URLs...")
post_urls = parser.extract_thread_urls(json_data, base_url)
print(f"✓ Found {len(post_urls)} posts")

if post_urls:
    print("\nFirst 5 posts:")
    for i, url in enumerate(post_urls[:5], 1):
        title = url.split('/')[-2].replace('_', ' ')[:50]
        print(f"  {i}. {title}...")
print()

# Step 3: Test fetching and parsing a single post
if post_urls:
    print("Step 3: Testing post content extraction...")
    test_post_url = post_urls[0]
    print(f"Fetching: {test_post_url}")
    
    # Fetch post JSON
    post_json = crawler.fetch_json(test_post_url + '.json')
    if post_json:
        print("✓ Fetched post JSON")
        
        # Extract posts (title + content)
        posts = parser.extract_all_posts(post_json)
        print(f"✓ Extracted {len(posts)} post(s)")
        
        if posts:
            post = posts[0]
            print(f"\nPost content preview:")
            print(f"  Author: {post.get('author', 'Unknown')}")
            print(f"  Content length: {len(post['content'])} chars")
            print(f"  Preview: {post['content'][:200]}...")
    else:
        print("✗ Failed to fetch post")
print()

# Step 4: Test keyword matching
print("Step 4: Testing keyword matching...")
test_keyword = "casino"

if post_urls and json_data:
    matches = 0
    for url in post_urls[:10]:  # Test first 10 posts
        post_json = crawler.fetch_json(url + '.json')
        if post_json:
            posts = parser.extract_all_posts(post_json)
            for post in posts:
                if test_keyword.lower() in post['content'].lower():
                    matches += 1
                    break
    
    print(f"✓ Found '{test_keyword}' in {matches}/10 posts")

print()
print("="*60)
print("REDDIT CRAWLER TEST COMPLETE")
print("="*60)
