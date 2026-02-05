from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

from bs4 import BeautifulSoup

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class OwnedCoreParser(BaseParser):
    """Parser for ownedcore.com forum (vBulletin 4.2.3)."""

    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for OwnedCore.
        
        OwnedCore uses unique pagination:
        Page 1: /forums/gambling/
        Page 2: /forums/gambling/index2.html
        Page 3: /forums/gambling/index3.html
        """
        if page_num == 1:
            return base_url
        
        base_url = base_url.rstrip('/')
        return f"{base_url}/index{page_num}.html"

    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract thread URLs from a vBulletin forum page."""
        thread_urls: List[str] = []
        
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # vBulletin thread links are typically in the threadbit class
        # Look for links with showthread.php or /threads/ pattern
        seen = set()
        
        # Method 1: Find threadbit containers
        threadbits = soup.find_all('li', class_=lambda x: x and 'threadbit' in x)
        for threadbit in threadbits:
            link = threadbit.find('a', class_='title')
            if not link or not link.get('href'):
                continue
            
            href = link['href']
            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)
            
            # Remove anchor
            if '#' in url:
                url = url.split('#')[0]
            
            if url not in seen:
                seen.add(url)
                thread_urls.append(url)
        
        # Method 2: Fallback - find all links with showthread.php
        if not thread_urls:
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'showthread.php' not in href and '/threads/' not in href:
                    continue
                
                if href.startswith('/'):
                    url = urljoin(base_domain, href)
                elif href.startswith('http'):
                    url = href
                else:
                    url = urljoin(base_url, href)
                
                if '#' in url:
                    url = url.split('#')[0]
                
                if url not in seen:
                    seen.add(url)
                    thread_urls.append(url)
        
        logger.debug(f"Extracted {len(thread_urls)} thread URLs from {base_url}")
        return thread_urls

    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract thread title and first post content from vBulletin thread."""
        title = ''
        title_elem = soup.find('h1') or soup.find('span', class_='threadtitle') or soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract first post content
        content = ''
        content_elem = (
            soup.find('div', class_='content') or
            soup.find('div', class_='postbody') or
            soup.find('blockquote', class_='postcontent') or
            soup.find('div', class_='postcontent') or
            soup.find('div', class_='post_message')
        )
        
        if content_elem:
            content = content_elem.get_text(separator=' ', strip=True)
        
        if not title and not content:
            logger.warning("Could not extract thread content")
            return None
        
        return {'title': title, 'content': content}

    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all posts from a vBulletin thread."""
        posts: List[Dict[str, str]] = []
        
        # vBulletin posts are typically in postcontainer or postbit divs
        post_containers = (
            soup.find_all('li', class_=lambda x: x and 'postbit' in x) or
            soup.find_all('div', class_=lambda x: x and 'postbit' in x) or
            soup.find_all('div', id=lambda x: x and x.startswith('post_'))
        )
        
        for idx, container in enumerate(post_containers, start=1):
            try:
                # Extract post content
                content_elem = (
                    container.find('div', class_='content') or
                    container.find('div', class_='postbody') or
                    container.find('blockquote', class_='postcontent') or
                    container.find('div', class_='postcontent') or
                    container.find('div', class_='post_message')
                )
                
                if not content_elem:
                    continue
                
                content_text = content_elem.get_text(separator=' ', strip=True)
                
                if len(content_text) < 20:
                    continue
                
                # Extract author
                author = 'Unknown'
                author_elem = (
                    container.find('a', class_='username') or
                    container.find('span', class_='username') or
                    container.find('div', class_='username')
                )
                if author_elem:
                    author = author_elem.get_text(strip=True)
                
                posts.append({
                    'content': content_text,
                    'author': author,
                    'post_number': idx
                })
                
            except Exception as e:
                logger.warning(f"Error extracting post {idx}: {str(e)}")
        
        # Fallback: If no posts found, try to get thread title and first post
        if not posts:
            title = ''
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Try to find any content
            content_elem = (
                soup.find('div', class_='postbody') or
                soup.find('div', class_='post_message') or
                soup.find('blockquote')
            )
            
            if content_elem:
                content = content_elem.get_text(separator=' ', strip=True)
                posts.append({
                    'content': f"{title} {content}".strip(),
                    'author': 'Unknown',
                    'post_number': 1
                })
        
        logger.debug(f"Extracted {len(posts)} posts from thread")
        return posts
