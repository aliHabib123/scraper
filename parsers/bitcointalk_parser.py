from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import logging

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class BitcoinTalkParser(BaseParser):
    """Parser for bitcointalk.org forum."""
    
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for BitcoinTalk.
        
        BitcoinTalk uses board.0, board.20, board.40 format (20 threads per page).
        Example: index.php?board=56.0, index.php?board=56.20, etc.
        """
        if page_num == 1:
            return base_url
        
        # Calculate offset (20 threads per page)
        offset = (page_num - 1) * 20
        
        # Parse URL and update board parameter
        if '?board=' in base_url:
            # Extract board number
            board_part = base_url.split('?board=')[1].split('.')[0]
            base_part = base_url.split('?')[0]
            return f"{base_part}?board={board_part}.{offset}"
        
        return base_url
    
    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract thread URLs from BitcoinTalk board page.
        
        BitcoinTalk threads are in <td> with class="subject windowbg" or "subject windowbg2"
        """
        thread_urls = []
        
        # Parse base URL to get domain
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Find all thread links
        # Threads are in table rows with class containing "windowbg"
        # Look for <span> with id starting with "msg_" which contains thread titles
        thread_links = []
        
        # Strategy 1: Find all links in subject columns
        subject_cells = soup.find_all('td', class_=lambda x: x and 'subject' in x)
        for cell in subject_cells:
            links = cell.find_all('a', href=True)
            for link in links:
                href = link['href']
                # Thread links contain "topic=" parameter
                if 'topic=' in href:
                    thread_links.append(link)
        
        # Strategy 2: Direct search for topic links
        if not thread_links:
            thread_links = soup.find_all('a', href=lambda x: x and 'topic=' in x)
        
        # Process found links
        seen = set()
        for link in thread_links:
            href = link['href']
            
            # Skip if not a topic link
            if 'topic=' not in href:
                continue
            
            # Skip action links (reply, quote, etc.)
            if any(action in href for action in ['action=', '#msg', 'sort=']):
                continue
            
            # Convert to absolute URL
            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)
            
            # Clean URL - remove session IDs and fragments
            if ';' in url:
                url = url.split(';')[0]
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
        Extract thread title and first post content from BitcoinTalk.
        """
        result = {
            'title': '',
            'content': ''
        }
        
        # Extract title
        # Title is usually in <h2> or <h3> in the linktree/page title area
        title_selectors = [
            'h2',
            'h3',
            '.subject a',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Skip generic titles
                if title_text and not title_text.startswith('Bitcoin Forum'):
                    result['title'] = title_text
                    break
        
        # Extract first post content
        # Posts are in div with class "post" or "windowbg"
        post_selectors = [
            '.post',
            '.inner',
            'div[class*="windowbg"]',
            '.postarea'
        ]
        
        for selector in post_selectors:
            posts = soup.select(selector)
            if posts:
                # Get first post
                first_post = posts[0]
                
                # Try to find the message content within the post
                content_elem = (
                    first_post.select_one('.post') or
                    first_post.select_one('.inner') or
                    first_post
                )
                
                result['content'] = content_elem.get_text(separator=' ', strip=True)
                break
        
        # Fallback: get all paragraphs
        if not result['content']:
            paragraphs = soup.find_all('p', limit=5)
            result['content'] = ' '.join(p.get_text(strip=True) for p in paragraphs)
        
        if not result['title'] and not result['content']:
            logger.warning("Could not extract thread content")
            return None
        
        logger.debug(f"Extracted thread: {result['title'][:50]}...")
        return result
    
    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all posts from a BitcoinTalk thread.
        """
        posts = []
        
        # Extract title first
        title = ''
        title_elem = soup.select_one('h2, h3')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Find all post divs
        # BitcoinTalk posts are typically in divs with class containing "windowbg"
        post_elements = soup.find_all('div', class_=lambda x: x and 'windowbg' in x)
        
        # Alternative: look for table structure
        if not post_elements:
            # Posts might be in table rows
            post_elements = soup.find_all('tr', class_=lambda x: x and 'windowbg' in x)
        
        for idx, post_elem in enumerate(post_elements, start=1):
            try:
                # Find post content
                content_elem = (
                    post_elem.select_one('.post') or
                    post_elem.select_one('.inner') or
                    post_elem.select_one('.postarea') or
                    post_elem
                )
                
                content_text = content_elem.get_text(separator=' ', strip=True)
                
                # Skip if too short
                if len(content_text) < 20:
                    continue
                
                # Extract author
                author = 'Unknown'
                author_elem = (
                    post_elem.select_one('.poster h4 a') or
                    post_elem.select_one('.poster a') or
                    post_elem.select_one('a[title*="View profile"]')
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
                    'content': f"{thread_data['title']} {thread_data['content']}",
                    'author': 'Unknown',
                    'post_number': 1
                }]
        
        logger.debug(f"Extracted {len(posts)} posts from thread")
        return posts
