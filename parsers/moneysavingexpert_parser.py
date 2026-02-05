from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, quote
import logging

from bs4 import BeautifulSoup

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class MoneySavingExpertParser(BaseParser):
    """Parser for MoneySavingExpert forum (Vanilla Forums platform)."""

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """Generate search URL for MoneySavingExpert.
        
        Vanilla Forums search format:
        - /search?Search=keyword&Page=1
        """
        base_url = "https://forums.moneysavingexpert.com/search"
        encoded_keyword = quote(keyword)
        
        if page == 1:
            return f"{base_url}?Search={encoded_keyword}"
        
        return f"{base_url}?Search={encoded_keyword}&Page={page}"

    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """Generate paginated URL for Vanilla Forums.
        
        Vanilla Forums uses ?page=N format:
        - Page 1: /discussions
        - Page 2: /discussions?page=2
        """
        if page_num == 1:
            return base_url
        
        base_url = base_url.rstrip('/')
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"

    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract thread URLs from Vanilla Forums search/discussion page."""
        thread_urls: List[str] = []
        
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        seen = set()
        
        # Vanilla Forums threads are typically in:
        # - <div class="ItemDiscussion"> or similar
        # - <a> tags with class "Title" or in title containers
        
        # Strategy 1: Find all links with /discussion/ in href (most reliable)
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            
            # Must contain /discussion/
            if '/discussion/' not in href:
                continue
            
            # Skip pagination, profiles, categories
            if any(x in href for x in ['/categories/', '/profile/', '/embed/', '?page=', '#']):
                continue
            
            # Convert to absolute URL
            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                continue
            
            # Clean URL (remove anchors)
            if '#' in url:
                url = url.split('#')[0]
            
            if url not in seen:
                seen.add(url)
                thread_urls.append(url)
        
        
        logger.debug(f"Extracted {len(thread_urls)} thread URLs from {base_url}")
        return thread_urls

    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract thread title and first post content from Vanilla Forums thread page."""
        title = ''
        
        # Vanilla Forums thread title is typically in:
        # <h1 class="H"> or <h1> in the discussion header
        title_elem = (
            soup.find('h1', class_='H') or
            soup.find('h1', class_='DiscussionTitle') or
            soup.find('h1')
        )
        
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # First post content
        # Vanilla Forums posts are in <div class="Message"> or <div class="userContent">
        first_post = soup.find('div', class_='ItemComment') or soup.find('li', class_='ItemComment')
        
        content = ''
        if first_post:
            # Content is typically in <div class="Message"> or <div class="userContent">
            content_div = (
                first_post.find('div', class_='Message') or
                first_post.find('div', class_='userContent') or
                first_post.find('div', class_='Content')
            )
            if content_div:
                content = content_div.get_text(separator=' ', strip=True)
        
        if not title and not content:
            logger.warning("Could not extract thread content")
            return None
        
        return {'title': title, 'content': content}

    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all posts from a Vanilla Forums thread page."""
        posts: List[Dict[str, str]] = []
        
        # Extract title
        title = ''
        title_elem = (
            soup.find('h1', class_='H') or
            soup.find('h1', class_='DiscussionTitle') or
            soup.find('h1')
        )
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Find all post items
        # Vanilla Forums uses: <div class="ItemComment"> or <li class="ItemComment">
        post_items = (
            soup.find_all('div', class_='ItemComment') or
            soup.find_all('li', class_='ItemComment') or
            soup.find_all('div', class_=lambda x: x and 'Comment' in str(x))
        )
        
        for idx, item in enumerate(post_items, start=1):
            try:
                # Extract post content
                content_div = (
                    item.find('div', class_='Message') or
                    item.find('div', class_='userContent') or
                    item.find('div', class_='Content')
                )
                if not content_div:
                    continue
                
                content_text = content_div.get_text(separator=' ', strip=True)
                
                if len(content_text) < 20:
                    continue
                
                # Extract author
                author = 'Unknown'
                author_elem = (
                    item.find('a', class_='Username') or
                    item.find('span', class_='Username') or
                    item.find('div', class_='Author')
                )
                if author_elem:
                    author = author_elem.get_text(strip=True)
                
                # First post includes title
                if idx == 1 and title:
                    content_text = f"{title} {content_text}"
                
                posts.append({
                    'content': content_text,
                    'author': author,
                    'post_number': idx
                })
                
            except Exception as e:
                logger.warning(f"Error extracting post {idx}: {str(e)}")
                continue
        
        # Fallback
        if not posts:
            logger.debug("No posts found with standard selectors, using fallback")
            thread_data = self.extract_thread_content(soup)
            if thread_data:
                posts = [{
                    'content': f"{thread_data['title']} {thread_data['content']}".strip(),
                    'author': 'Unknown',
                    'post_number': 1
                }]
        
        logger.debug(f"Extracted {len(posts)} posts from thread")
        return posts
