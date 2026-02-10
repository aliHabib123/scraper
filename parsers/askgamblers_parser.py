"""
Parser for AskGamblers forums (Invision Community/IPS).
"""

import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class AskGamblersParser(BaseParser):
    """Parser for AskGamblers Invision Community forums."""
    
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for IPS forums.
        
        Args:
            base_url: Base forum URL
            page_num: Page number (1-indexed)
            
        Returns:
            Paginated URL
        """
        if page_num == 1:
            return base_url
        
        # IPS uses /page/N format
        base_url = base_url.rstrip('/')
        return f"{base_url}/page/{page_num}/"
    
    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract thread URLs from category page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of thread URLs
        """
        thread_urls = []
        seen = set()
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # Find all links with /topic/ in href
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Skip non-topic links
                if '/topic/' not in href:
                    continue
                
                # Skip comment links (they have ?do=findComment)
                if '?do=findComment' in href or '&do=findComment' in href:
                    continue
                
                # Convert relative URL to absolute
                if href.startswith('/'):
                    full_url = f"{base_domain}{href}"
                elif not href.startswith('http'):
                    full_url = base_url.rstrip('/') + '/' + href
                else:
                    full_url = href
                
                # Remove query parameters and fragments for deduplication
                clean_url = full_url.split('?')[0].split('#')[0]
                
                # Remove /page/N/ suffix to get base thread URL (avoid scraping random pages)
                # Example: /topic/123/page/23/ -> /topic/123/
                import re
                clean_url = re.sub(r'/page/\d+/?$', '', clean_url)
                
                if clean_url not in seen:
                    seen.add(clean_url)
                    thread_urls.append(clean_url)
            
            logger.debug(f"Extracted {len(thread_urls)} thread URLs")
            
        except Exception as e:
            logger.error(f"Error extracting thread URLs: {str(e)}")
        
        return thread_urls
    
    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """
        Extract thread title and first post content.
        
        Args:
            soup: BeautifulSoup object of thread page
            
        Returns:
            Dict with 'title' and 'content' keys
        """
        try:
            # Extract title from h1.ipsType_pageTitle or similar
            title_elem = soup.find('h1', class_='ipsType_pageTitle')
            if not title_elem:
                # Alternative: Look for page title in meta tags
                title_elem = soup.find('meta', property='og:title')
                title = title_elem.get('content', 'Unknown') if title_elem else 'Unknown'
            else:
                title = title_elem.get_text(strip=True)
            
            # Extract first post content
            first_post = soup.find('article', class_='cPost')
            if not first_post:
                return None
            
            content_div = first_post.find('div', attrs={'data-role': 'commentContent'})
            if not content_div:
                return None
            
            content = content_div.get_text(separator=' ', strip=True)
            
            return {
                'title': title,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Error extracting thread content: {str(e)}")
            return None
    
    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all posts from a thread page.
        
        Args:
            soup: BeautifulSoup object of thread page
            
        Returns:
            List of dicts with post info (content, author, post_number)
        """
        posts = []
        
        try:
            # IPS posts are in article.cPost elements
            post_articles = soup.find_all('article', class_='cPost')
            
            for idx, article in enumerate(post_articles, 1):
                # Extract post content from data-role="commentContent"
                content_div = article.find('div', attrs={'data-role': 'commentContent'})
                if not content_div:
                    continue
                
                content = content_div.get_text(separator=' ', strip=True)
                
                # Extract author from cAuthorPane_author
                author_elem = article.find('a', class_='ipsType_break')
                author = author_elem.get_text(strip=True) if author_elem else 'Unknown'
                
                posts.append({
                    'content': content,
                    'author': author,
                    'post_number': idx
                })
            
            logger.debug(f"Extracted {len(posts)} posts from thread")
            
        except Exception as e:
            logger.error(f"Error extracting posts: {str(e)}")
        
        return posts
