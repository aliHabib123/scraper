from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

from bs4 import BeautifulSoup

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class BigWinBoardParser(BaseParser):
    """Parser for bigwinboard.com forum (bbPress-style)."""

    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """Generate paginated URL.

        BigWinBoard uses WordPress-style pagination:
        /forum/<slug>/paged/2/
        """
        if page_num == 1:
            return base_url

        base_url = base_url.rstrip('/')
        return f"{base_url}/paged/{page_num}/"

    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract topic URLs from a forum category page."""
        thread_urls: List[str] = []

        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"

        # The category pages list topics as regular links.
        # Heuristics:
        # - must contain "/forum/" and the category slug
        # - must not be user profile links (/participant/)
        # - must not be pagination links (/paged/)
        # - must not be the category page itself
        base_path = urlparse(base_url).path.rstrip('/')

        seen = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('#') or href.startswith('javascript:'):
                continue

            if href.startswith('/'):
                url = urljoin(base_domain, href)
            elif href.startswith('http'):
                url = href
            else:
                url = urljoin(base_url, href)

            if '#' in url:
                url = url.split('#')[0]

            path = urlparse(url).path

            if '/participant/' in path:
                continue
            if '/paged/' in path:
                continue
            if '/forum/' not in path:
                continue

            # Limit to the same category subtree
            if not path.startswith(base_path + '/'):
                continue

            # Skip category root itself
            if path.rstrip('/') == base_path:
                continue

            # Require a non-trivial slug after the category
            remaining = path[len(base_path):].strip('/')
            if not remaining:
                continue
            if '/' in remaining:
                # Topic URLs are usually directly under the category
                # e.g. /forum/casino-complaints/topic-slug/
                pass

            if url not in seen:
                seen.add(url)
                thread_urls.append(url)

        logger.debug(f"Extracted {len(thread_urls)} thread URLs from {base_url}")
        return thread_urls

    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract thread title and first post content."""
        title = ''
        title_elem = soup.select_one('h1') or soup.select_one('title')
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Try common bbPress / WP selectors
        content_elem = (
            soup.select_one('.bbp-topic-content')
            or soup.select_one('.bbp-reply-content')
            or soup.select_one('.entry-content')
            or soup.select_one('article')
            or soup.select_one('main')
        )

        content = ''
        if content_elem:
            content = content_elem.get_text(separator=' ', strip=True)

        if not title and not content:
            logger.warning("Could not extract thread content")
            return None

        return {'title': title, 'content': content}

    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all posts from a topic page."""
        posts: List[Dict[str, str]] = []

        title = ''
        title_elem = soup.select_one('h1') or soup.select_one('title')
        if title_elem:
            title = title_elem.get_text(strip=True)

        # bbPress commonly uses these wrappers
        post_containers = []
        for selector in [
            'li.bbp-topic',
            'li.bbp-reply',
            'div.bbp-topic',
            'div.bbp-reply',
            'article',
        ]:
            post_containers = soup.select(selector)
            if post_containers:
                break

        # If we found lots of generic articles, try to reduce noise
        if post_containers and selector == 'article':
            filtered = []
            for art in post_containers:
                if art.select_one('.bbp-reply-content, .bbp-topic-content, .entry-content'):
                    filtered.append(art)
            if filtered:
                post_containers = filtered

        for idx, container in enumerate(post_containers, start=1):
            try:
                content_elem = (
                    container.select_one('.bbp-topic-content')
                    or container.select_one('.bbp-reply-content')
                    or container.select_one('.entry-content')
                    or container
                )
                content_text = content_elem.get_text(separator=' ', strip=True)

                if len(content_text) < 20:
                    continue

                author = 'Unknown'
                author_elem = (
                    container.select_one('a[href*="/participant/"]')
                    or container.select_one('.bbp-author-name')
                    or container.select_one('.bbp-author a')
                )
                if author_elem:
                    author = author_elem.get_text(strip=True)

                if idx == 1 and title:
                    content_text = f"{title} {content_text}"

                posts.append({
                    'content': content_text,
                    'author': author,
                    'post_number': idx
                })
            except Exception as e:
                logger.warning(f"Error extracting post {idx}: {str(e)}")

        if not posts:
            thread_data = self.extract_thread_content(soup)
            if thread_data:
                posts = [{
                    'content': f"{thread_data['title']} {thread_data['content']}".strip(),
                    'author': 'Unknown',
                    'post_number': 1
                }]

        logger.debug(f"Extracted {len(posts)} posts from thread")
        return posts
