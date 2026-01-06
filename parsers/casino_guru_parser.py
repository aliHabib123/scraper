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
        
        Casino.guru uses <a class="title"> for thread links.
        """
        thread_urls = []
        
        # Parse base URL to get domain
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Casino.guru specific: thread links have class="title"
        thread_links = soup.find_all('a', class_='title', href=True)
        
        # Filter and convert to absolute URLs
        seen = set()
        for link in thread_links:
            href = link['href']
            
            # Skip pagination links and other non-thread links
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Skip if it's just a page number (like /forum/casinos/2)
            # Thread URLs contain the thread name/slug
            if href.count('/') <= 3:  # e.g., /forum/casinos/2 has 3 slashes
                continue
            
            # Convert to absolute URL
            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)
            
            # Remove anchor/fragment (#post-123)
            if '#' in url:
                url = url.split('#')[0]
            
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
    
    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all posts from a casino.guru thread.
        
        Returns:
            List of post dicts with 'content', 'author', 'post_number'
        """
        posts = []
        
        # Extract title first
        title = ''
        title_selectors = ['h1', '.thread-title', '.topic-title', '.discussion-title', 'title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Try multiple strategies to find all posts
        post_elements = []
        
        # Strategy 1: Look for post containers with common classes
        post_selectors = [
            '.post',
            '.message',
            '.comment',
            '.forum-post',
            'article.post',
            'div[class*="post"]',
            'div[class*="message"]',
            'li[class*="post"]',
        ]
        
        for selector in post_selectors:
            post_elements = soup.select(selector)
            if post_elements:
                logger.debug(f"Found {len(post_elements)} posts using selector: {selector}")
                break
        
        # Strategy 2: If no posts found, look for common content containers
        if not post_elements:
            # Try finding posts by structure
            for container_selector in ['.posts', '.messages', '.comments', '#posts', 'main', 'article']:
                container = soup.select_one(container_selector)
                if container:
                    # Find all divs with text content
                    post_elements = container.find_all(['div', 'article', 'li'], recursive=True, limit=100)
                    # Filter to those that look like posts (have substantial text)
                    post_elements = [p for p in post_elements if len(p.get_text(strip=True)) > 50]
                    if post_elements:
                        logger.debug(f"Found {len(post_elements)} potential posts in {container_selector}")
                        break
        
        # Process found posts
        for idx, post_elem in enumerate(post_elements, start=1):
            try:
                # Extract post content
                # Try to find the main content within the post
                content_elem = (
                    post_elem.select_one('.post-content') or
                    post_elem.select_one('.message-content') or
                    post_elem.select_one('.post-body') or
                    post_elem.select_one('.content') or
                    post_elem
                )
                
                content_text = content_elem.get_text(separator=' ', strip=True)
                
                # Skip if too short (likely not a real post)
                if len(content_text) < 20:
                    continue
                
                # Try to extract author
                author = 'Unknown'
                author_selectors = ['.author', '.username', '.post-author', '[class*="author"]', '[class*="username"]']
                for auth_sel in author_selectors:
                    author_elem = post_elem.select_one(auth_sel)
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                        break
                
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
        
        # Fallback: if no posts found, use the old method
        if not posts:
            logger.debug("No posts found with standard selectors, using fallback")
            thread_data = self.extract_thread_content(soup)
            if thread_data:
                posts = [{
                    'content': f"{thread_data['title']} {thread_data['content']}",
                    'author': 'Unknown',
                    'post_number': 1
                }]
        
        logger.debug(f"Extracted {len(posts)} posts from thread")
        return posts
