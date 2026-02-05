from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

from bs4 import BeautifulSoup

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class XenForoParser(BaseParser):
    """Parser for XenForo forums (e.g., CasinoMeister)."""

    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """Generate paginated URL for XenForo.
        
        XenForo uses /page-N format:
        - Page 1: /forums/community/subforum/
        - Page 2: /forums/community/subforum/page-2
        """
        if page_num == 1:
            return base_url
        
        base_url = base_url.rstrip('/')
        return f"{base_url}/page-{page_num}"

    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract thread URLs from XenForo sub-forum page."""
        thread_urls: List[str] = []
        
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        seen = set()
        
        # XenForo threads are typically in:
        # - <div class="structItem structItem--thread">
        # - <h3 class="structItem-title"> with <a> tag
        # - Or <a data-tp-primary="on"> for thread links
        
        # Strategy 1: Look for structItem--thread containers
        thread_items = soup.find_all('div', class_=lambda x: x and 'structItem--thread' in x)
        
        for item in thread_items:
            # Find the main thread link
            title_container = item.find('div', class_='structItem-title')
            if not title_container:
                continue
            
            link = title_container.find('a', href=True)
            if not link:
                continue
            
            href = link['href']
            
            # Convert to absolute URL
            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)
            
            # Remove anchors
            if '#' in url:
                url = url.split('#')[0]
            
            # XenForo thread URLs contain /threads/
            if '/threads/' not in url:
                continue
            
            if url not in seen:
                seen.add(url)
                thread_urls.append(url)
        
        # Strategy 2: Fallback - find all links with /threads/ in href
        if not thread_urls:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                
                if '/threads/' not in href:
                    continue
                
                # Skip pagination, members, etc.
                if any(x in href for x in ['/page-', '/members/', '/forums/', '#']):
                    continue
                
                # Convert to absolute URL
                if href.startswith('/'):
                    url = urljoin(base_domain, href)
                elif href.startswith('http'):
                    url = href
                else:
                    continue
                
                if url not in seen:
                    seen.add(url)
                    thread_urls.append(url)
        
        logger.debug(f"Extracted {len(thread_urls)} thread URLs from {base_url}")
        return thread_urls

    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract thread title and first post content from XenForo thread page."""
        title = ''
        
        # XenForo thread title is typically in:
        # <h1 class="p-title-value">
        title_elem = (
            soup.find('h1', class_='p-title-value') or
            soup.find('h1', class_=lambda x: x and 'p-title' in x) or
            soup.find('h1')
        )
        
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # First post content
        # XenForo posts are in <article class="message message--post">
        first_post = soup.find('article', class_=lambda x: x and 'message--post' in x)
        
        content = ''
        if first_post:
            # Content is in <div class="bbWrapper">
            content_div = first_post.find('div', class_='bbWrapper')
            if content_div:
                content = content_div.get_text(separator=' ', strip=True)
        
        if not title and not content:
            logger.warning("Could not extract thread content")
            return None
        
        return {'title': title, 'content': content}

    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all posts from a XenForo thread page."""
        posts: List[Dict[str, str]] = []
        
        # Extract title
        title = ''
        title_elem = (
            soup.find('h1', class_='p-title-value') or
            soup.find('h1', class_=lambda x: x and 'p-title' in x) or
            soup.find('h1')
        )
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Find all post articles
        # XenForo uses: <article class="message message--post">
        post_articles = soup.find_all('article', class_=lambda x: x and 'message--post' in x)
        
        for idx, article in enumerate(post_articles, start=1):
            try:
                # Extract post content from bbWrapper
                content_div = article.find('div', class_='bbWrapper')
                if not content_div:
                    continue
                
                content_text = content_div.get_text(separator=' ', strip=True)
                
                if len(content_text) < 20:
                    continue
                
                # Extract author
                author = 'Unknown'
                author_elem = (
                    article.find('a', class_='username') or
                    article.find('h4', class_='message-name') or
                    article.find('a', attrs={'data-user-id': True})
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
