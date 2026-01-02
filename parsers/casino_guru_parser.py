from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class CasinoGuruParser(BaseParser):
    """Parser for casino.guru forum."""
    
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for casino.guru.
        
        Casino.guru uses ?page=N format for pagination.
        """
        if page_num == 1:
            return base_url
        
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page_num}"
    
    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract thread URLs from casino.guru category page.
        
        Looks for thread links in the forum listing.
        """
        thread_urls = []
        
        # Parse base URL to get domain
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Casino.guru typically has thread links in various patterns
        # Common selectors: a tags with href containing '/thread/', '/topic/', or similar
        
        # Try multiple strategies to find thread links
        thread_links = []
        
        # Strategy 1: Find links with 'thread' or 'topic' in href
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(pattern in href.lower() for pattern in ['/thread/', '/topic/', '/discussion/', '/post/']):
                thread_links.append(link)
        
        # Strategy 2: If no links found, look for links in specific containers
        if not thread_links:
            # Look for common forum list containers
            for container in soup.select('.topic-list, .thread-list, .forum-list, .discussions'):
                thread_links.extend(container.find_all('a', href=True))
        
        # Strategy 3: If still no links, get all links from main content area
        if not thread_links:
            main_content = soup.find('main') or soup.find('div', class_=['content', 'main-content'])
            if main_content:
                thread_links = main_content.find_all('a', href=True)
        
        # Convert to absolute URLs and deduplicate
        seen = set()
        for link in thread_links:
            href = link['href']
            
            # Skip non-thread links
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            if any(skip in href.lower() for skip in ['login', 'register', 'profile', 'search', 'category']):
                continue
            
            # Convert to absolute URL
            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)
            
            # Deduplicate
            if url not in seen:
                seen.add(url)
                thread_urls.append(url)
        
        logger.debug(f"Extracted {len(thread_urls)} thread URLs from {base_url}")
        return thread_urls
    
    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """
        Extract thread title and first post content from casino.guru thread page.
        """
        result = {
            'title': '',
            'content': ''
        }
        
        # Extract title
        title_selectors = [
            'h1',
            '.thread-title',
            '.topic-title',
            '.discussion-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract first post content
        # Try multiple strategies to find the first post
        content_text = ''
        
        # Strategy 1: Look for first post with specific classes
        post_selectors = [
            '.post-content',
            '.message-content',
            '.topic-content',
            '.thread-content',
            '.discussion-content',
            '.post-body',
            '.message-body',
            'article.post',
            '.forum-post'
        ]
        
        for selector in post_selectors:
            posts = soup.select(selector)
            if posts:
                # Get first post
                content_text = posts[0].get_text(separator=' ', strip=True)
                break
        
        # Strategy 2: If no content found, look for main content area
        if not content_text:
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main-content'])
            if main_content:
                # Get all paragraphs
                paragraphs = main_content.find_all('p', limit=5)
                content_text = ' '.join(p.get_text(strip=True) for p in paragraphs)
        
        # Strategy 3: If still no content, get text from body (excluding header/footer/nav)
        if not content_text:
            # Remove script, style, nav, header, footer elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # Get remaining text
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator=' ', strip=True)[:1000]
        
        result['content'] = content_text
        
        # Return None if we couldn't extract meaningful content
        if not result['title'] and not result['content']:
            logger.warning("Could not extract thread content")
            return None
        
        logger.debug(f"Extracted thread: {result['title'][:50]}...")
        return result
