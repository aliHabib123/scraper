from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
import os

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class LCBParser(BaseParser):
    """Parser for LCB.org forum (Latest Casino Bonuses)."""
    
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for LCB.org.
        
        LCB.org uses offset-based pagination: /40, /80, /120, etc.
        40 topics per page.
        """
        if page_num == 1:
            return base_url
        
        # Calculate offset (40 topics per page)
        offset = (page_num - 1) * 40
        
        # Remove trailing slash if present
        base_url = base_url.rstrip('/')
        return f"{base_url}/{offset}"
    
    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract thread URLs from LCB.org category page.
        
        LCB.org uses links like: /onlinecasinobonusforum/casinos/topic-slug-id
        
        Extraction mode controlled by LCB_EXTRACTION_MODE environment variable:
        - 'comprehensive' (default): Extract all thread links including sidebar/widgets
        - 'targeted': Extract only main thread list, faster but less coverage
        """
        thread_urls = []
        
        # Parse base URL to get domain
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get extraction mode from environment variable
        extraction_mode = os.getenv('LCB_EXTRACTION_MODE', 'comprehensive').lower()
        
        # Find all links based on extraction mode
        if extraction_mode == 'targeted':
            # Targeted mode: Only extract main thread title links
            # LCB.org structure: <ul id="all-topics"><li class="full-row"><div class="topic-author-name"><a>Thread Title</a>
            main_content = soup.select_one('#all-topics, .all-topics')
            if main_content:
                # Extract only the main thread title link from each row
                # Each row has multiple links (title, last post, users), we want only the title
                all_links = main_content.select('.topic-author-name > a:first-of-type')
                if all_links:
                    logger.debug(f"LCB targeted mode: found {len(all_links)} thread title links in #all-topics")
                else:
                    # Fallback: get all links in topic-info if selector fails
                    all_links = main_content.select('.topic-info a')
                    logger.debug(f"LCB targeted mode: using .topic-info links ({len(all_links)} found)")
            else:
                # Fallback: try to find main content column
                main_content = soup.select_one('.col-12.col-xl-9, .main-content')
                if main_content:
                    all_links = main_content.find_all('a', href=True)
                    logger.debug(f"LCB targeted mode: using main content column with {len(all_links)} links")
                else:
                    # Last resort: use all links
                    all_links = soup.find_all('a', href=True)
                    logger.debug(f"LCB targeted mode: container not found, using all {len(all_links)} links")
        else:
            # Comprehensive mode: Extract from entire page (includes sidebars, widgets, etc.)
            all_links = soup.find_all('a', href=True)
            logger.debug(f"LCB comprehensive mode: searching all {len(all_links)} page links")
        
        # Filter thread links
        seen = set()
        for link in all_links:
            href = link['href']
            
            # Skip non-thread links
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Thread URLs contain the category path + topic name
            # Example: /onlinecasinobonusforum/casinos/5-6-biggest-online-casino-and-player-scams-1
            if '/onlinecasinobonusforum/' in href and href.count('/') >= 3:
                # Skip pagination links (just numbers)
                # Pagination: /onlinecasinobonusforum/casinos/40
                # Thread: /onlinecasinobonusforum/casinos/topic-name-1
                path_parts = href.rstrip('/').split('/')
                last_part = path_parts[-1]
                
                # Skip if last part is just a number (pagination)
                if last_part.isdigit():
                    continue
                
                # Skip if it's the base category URL
                if href.rstrip('/') in base_url:
                    continue
                
                # Convert to absolute URL
                if href.startswith('/'):
                    full_url = f"{base_domain}{href}"
                elif not href.startswith('http'):
                    full_url = base_url.rstrip('/') + '/' + href
                else:
                    full_url = href
                
                # Remove query parameters and fragments for deduplication
                clean_url = full_url.split('?')[0].split('#')[0]
                
                if clean_url not in seen:
                    seen.add(clean_url)
                    thread_urls.append(clean_url)
        
        logger.debug(f"Extracted {len(thread_urls)} thread URLs from {base_url}")
        return thread_urls
    
    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """
        Extract thread title and first post content from LCB.org thread page.
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
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                result['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract first post content
        content_text = ''
        
        # Strategy 1: Look for post content
        post_selectors = [
            '.post-content',
            '.message-content',
            '.topic-content',
            '.post-body',
            '.message-body',
            'article.post',
            '.forum-post'
        ]
        
        for selector in post_selectors:
            posts = soup.select(selector)
            if posts:
                content_text = posts[0].get_text(separator=' ', strip=True)
                break
        
        # Strategy 2: If no content found, look for main content area
        if not content_text:
            main_content = soup.find('main') or soup.find('article')
            if main_content:
                paragraphs = main_content.find_all('p', limit=5)
                content_text = ' '.join(p.get_text(strip=True) for p in paragraphs)
        
        result['content'] = content_text
        
        if not result['title'] and not result['content']:
            logger.warning("Could not extract thread content")
            return None
        
        logger.debug(f"Extracted thread: {result['title'][:50]}...")
        return result
    
    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all posts from an LCB.org thread.
        
        Returns:
            List of post dicts with 'content', 'author', 'post_number'
        """
        posts = []
        
        # Extract title first
        title = ''
        title_selectors = ['h1', '.thread-title', '.topic-title', 'title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Find post elements
        post_elements = []
        
        post_selectors = [
            '.post',
            '.message',
            '.comment',
            '.forum-post',
            'article.post',
            'div[class*="post"]',
            'div[class*="message"]',
        ]
        
        for selector in post_selectors:
            post_elements = soup.select(selector)
            if post_elements:
                logger.debug(f"Found {len(post_elements)} posts using selector: {selector}")
                break
        
        # Process found posts
        for idx, post_elem in enumerate(post_elements, start=1):
            try:
                content_elem = (
                    post_elem.select_one('.post-content') or
                    post_elem.select_one('.message-content') or
                    post_elem.select_one('.post-body') or
                    post_elem.select_one('.content') or
                    post_elem
                )
                
                content_text = content_elem.get_text(separator=' ', strip=True)
                
                if len(content_text) < 20:
                    continue
                
                author = 'Unknown'
                author_selectors = ['.author', '.username', '.post-author', '[class*="author"]']
                for auth_sel in author_selectors:
                    author_elem = post_elem.select_one(auth_sel)
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                        break
                
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
            thread_data = self.extract_thread_content(soup)
            if thread_data:
                posts = [{
                    'content': f"{thread_data['title']} {thread_data['content']}",
                    'author': 'Unknown',
                    'post_number': 1
                }]
        
        logger.debug(f"Extracted {len(posts)} posts from thread")
        return posts
