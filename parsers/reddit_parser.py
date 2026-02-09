from typing import List, Dict, Optional
import json
import logging

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class RedditParser(BaseParser):
    """Parser for Reddit subreddits using JSON API."""
    
    def __init__(self):
        """Initialize Reddit parser."""
        # Reddit API requires custom User-Agent format: <platform>:<app>:<version> (by /u/<username>)
        # Generic browser User-Agents are blocked with 403
        self.user_agent = "python:forum-scraper:v1.0 (by /u/ForumMonitor)"
        self.after_token = None  # Track pagination token
    
    def get_reddit_headers(self):
        """Get Reddit-compliant headers."""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
        }
    
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for Reddit.
        
        Reddit uses JSON API with 'after' parameter for pagination.
        
        Args:
            base_url: Base subreddit URL (e.g., https://www.reddit.com/r/casino)
            page_num: Page number (1 for first page, >1 uses after_token)
            
        Returns:
            JSON API URL with appropriate after token
        """
        # Convert regular Reddit URL to JSON API endpoint
        if not base_url.endswith('.json'):
            base_url = base_url.rstrip('/')
            base_url = f"{base_url}/new.json"
        
        # ALWAYS reset token on page 1 (new subreddit)
        if page_num == 1:
            self.after_token = None
            return f"{base_url}?limit=30"
        
        # Subsequent pages use 'after' token (if available)
        if self.after_token:
            return f"{base_url}?limit=30&after={self.after_token}"
        else:
            # No more pages available
            return f"{base_url}?limit=30"
    
    def extract_thread_urls(self, soup, base_url: str) -> List[str]:
        """
        Extract post URLs from Reddit JSON response.
        
        Note: 'soup' parameter is actually the JSON response dict for Reddit,
        not a BeautifulSoup object. We keep the name for API compatibility.
        
        Args:
            soup: JSON response dict from Reddit API
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute post URLs
        """
        if not isinstance(soup, dict):
            logger.error("Expected dict (JSON response) but got different type")
            return []
        
        post_urls = []
        
        try:
            # Reddit JSON structure: data -> children -> [post1, post2, ...]
            data = soup.get('data', {})
            children = data.get('children', [])
            
            # Store the 'after' token for pagination
            self.after_token = data.get('after')  # Will be None if no more pages
            
            for child in children:
                post_data = child.get('data', {})
                permalink = post_data.get('permalink')
                
                if permalink:
                    # Convert to full URL
                    full_url = f"https://www.reddit.com{permalink}"
                    post_urls.append(full_url)
            
            logger.debug(f"Extracted {len(post_urls)} post URLs from Reddit (after={self.after_token})")
            
        except Exception as e:
            logger.error(f"Error extracting Reddit post URLs: {str(e)}")
        
        return post_urls
    
    def extract_thread_content(self, soup) -> Optional[Dict[str, str]]:
        """
        Extract post title and content from Reddit JSON response.
        
        Args:
            soup: JSON response dict from Reddit post API
            
        Returns:
            Dict with 'title' and 'content' keys, or None if extraction fails
        """
        if not isinstance(soup, dict):
            logger.error("Expected dict (JSON response) but got different type")
            return None
        
        try:
            # Reddit post JSON structure: [post_listing, comments_listing]
            # We want the first element (post data)
            if isinstance(soup, list) and len(soup) > 0:
                post_data = soup[0].get('data', {}).get('children', [])[0].get('data', {})
            else:
                # Single post structure
                post_data = soup.get('data', {}).get('children', [])[0].get('data', {})
            
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            
            return {
                'title': title,
                'content': selftext
            }
            
        except Exception as e:
            logger.error(f"Error extracting Reddit post content: {str(e)}")
            return None
    
    def extract_all_posts(self, soup) -> List[Dict[str, str]]:
        """
        Extract post and optionally top-level comments from Reddit.
        
        For Reddit, we extract:
        1. The main post (title + selftext)
        2. Optionally top comments (future enhancement)
        
        Args:
            soup: JSON response dict from Reddit post API
            
        Returns:
            List of dicts with 'content' and metadata
        """
        posts = []
        
        try:
            # Handle both list (post+comments) and dict (post only) responses
            if isinstance(soup, list) and len(soup) > 0:
                # Post is in first element
                post_listing = soup[0]
                post_data = post_listing.get('data', {}).get('children', [])[0].get('data', {})
            else:
                # Single post structure
                post_data = soup.get('data', {}).get('children', [])[0].get('data', {})
            
            # Extract post data
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            author = post_data.get('author', 'Unknown')
            
            # Combine title and content
            content = f"{title}\n\n{selftext}".strip()
            
            if content:
                posts.append({
                    'content': content,
                    'author': author,
                    'post_number': 1
                })
            
            # TODO: Future enhancement - extract top comments
            # if isinstance(soup, list) and len(soup) > 1:
            #     comments_listing = soup[1]
            #     # Extract and process comments
            
        except Exception as e:
            logger.error(f"Error extracting Reddit posts: {str(e)}")
        
        return posts
    
    def get_next_page_token(self, soup) -> Optional[str]:
        """
        Extract the 'after' token for pagination.
        
        Reddit uses 'after' tokens instead of page numbers.
        
        Args:
            soup: JSON response dict from Reddit API
            
        Returns:
            'after' token string or None if no more pages
        """
        try:
            data = soup.get('data', {})
            after = data.get('after')
            return after
        except Exception as e:
            logger.error(f"Error extracting pagination token: {str(e)}")
            return None
