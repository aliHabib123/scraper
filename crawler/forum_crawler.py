import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Forum, Keyword, Match
from .base_crawler import BaseCrawler
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class ForumCrawler:
    """Main crawler for monitoring forums for keyword mentions."""
    
    def __init__(self, db_session: Session, parser: BaseParser, rate_limit: float = 2.0, cookies: Optional[Dict[str, str]] = None, use_playwright: bool = False, use_flaresolverr: bool = False, headless: bool = True):
        """
        Initialize forum crawler.
        
        Args:
            db_session: SQLAlchemy database session
            parser: Forum-specific parser instance
            rate_limit: Minimum seconds between requests
            cookies: Optional cookies dict for authenticated requests
            use_playwright: Use Playwright browser instead of httpx (for Cloudflare bypass)
            use_flaresolverr: Use FlareSolverr service for Cloudflare bypass (priority over Playwright)
            headless: Run Playwright in headless mode (default: True)
        """
        self.db_session = db_session
        self.parser = parser
        
        # Choose crawler based on flags (FlareSolverr > Playwright > BaseCrawler)
        if use_flaresolverr:
            from .flaresolverr_crawler import FlareSolverrCrawler
            self.crawler = FlareSolverrCrawler(rate_limit=rate_limit)
            logger.info(f"Using FlareSolverr for Cloudflare bypass")
        elif use_playwright:
            from .playwright_crawler import PlaywrightCrawler
            self.crawler = PlaywrightCrawler(rate_limit=rate_limit, headless=headless)
            mode = "headless" if headless else "visible"
            logger.info(f"Using Playwright browser ({mode}) for Cloudflare bypass")
        else:
            self.crawler = BaseCrawler(rate_limit=rate_limit, cookies=cookies)
        
        self.use_playwright = use_playwright
        self.use_flaresolverr = use_flaresolverr
    
    def crawl_forum(self, forum: Forum, keywords: List[Keyword]) -> Dict[str, int]:
        """
        Crawl a forum for all keywords.
        
        Args:
            forum: Forum object to crawl
            keywords: List of Keyword objects to search for
            
        Returns:
            Dict with statistics (matches_found, pages_crawled, errors)
        """
        stats = {
            'matches_found': 0,
            'pages_crawled': 0,
            'threads_found': 0,
            'errors': 0
        }
        
        if not keywords:
            logger.warning(f"No keywords to search for in forum: {forum.name}")
            return stats
        
        logger.info(f"Starting crawl of forum: {forum.name}")
        logger.info(f"Searching for {len(keywords)} keywords")
        
        # Warm up session for XenForo forums (establish cookies first)
        if 'casinomeister' in forum.name.lower() or forum.base_url:
            # Detect XenForo by checking if base_url exists
            if forum.base_url and not forum.base_url.endswith('reddit.com'):
                self.crawler.warm_up_session(forum.base_url)
        
        try:
            # Get thread URLs from start_urls
            thread_urls = []
            for start_url in forum.start_urls:
                logger.info(f"Processing start URL: {start_url}")
                urls, pages = self._crawl_category_pages(start_url, forum.max_pages)
                thread_urls.extend(urls)
                stats['pages_crawled'] += pages
                stats['threads_found'] += len(urls)
            
            logger.info(f"Found {len(thread_urls)} thread URLs")
            
            # Process each thread
            for thread_url in thread_urls:
                matches = self._process_thread(forum, thread_url, keywords)
                stats['matches_found'] += len(matches)
                
        except Exception as e:
            logger.error(f"Error crawling forum {forum.name}: {str(e)}")
            stats['errors'] += 1
        
        logger.info(f"Finished crawling {forum.name}: {stats}")
        
        # Cleanup browser/session resources if used
        if self.use_playwright or self.use_flaresolverr:
            self.crawler.close()
        
        return stats
    
    def _crawl_category_pages(self, start_url: str, max_pages: int) -> tuple[List[str], int]:
        """
        Crawl category pages to extract thread URLs.
        
        Args:
            start_url: Starting category URL
            max_pages: Maximum pages to crawl
            
        Returns:
            Tuple of (thread URLs list, number of pages crawled)
        """
        thread_urls = []
        pages_crawled = 0
        
        # Detect if this is Reddit (JSON API)
        is_reddit = 'reddit.com' in start_url
        
        for page_num in range(1, max_pages + 1):
            try:
                # Get paginated URL
                page_url = self.parser.get_paginated_url(start_url, page_num)
                
                # Fetch page (JSON for Reddit, HTML for others)
                # For page 2+, use previous page as referer to look like navigation
                if is_reddit:
                    soup = self.crawler.fetch(page_url, json_mode=True)
                else:
                    referer = self.parser.get_paginated_url(start_url, page_num - 1) if page_num > 1 else None
                    soup = self.crawler.fetch_page(page_url, referer=referer)
                
                if not soup:
                    logger.warning(f"Failed to fetch category page: {page_url}")
                    break
                
                # Extract thread URLs
                urls = self.parser.extract_thread_urls(soup, start_url)
                if not urls:
                    logger.info(f"No more threads found at page {page_num}")
                    break
                
                thread_urls.extend(urls)
                pages_crawled += 1
                logger.info(f"Page {page_num}: Found {len(urls)} threads")
                
                # For Reddit: check if there's a next page (after_token exists)
                is_reddit = 'reddit.com' in start_url
                if is_reddit and hasattr(self.parser, 'after_token'):
                    if self.parser.after_token is None:
                        logger.info(f"No more pages available (after_token is None)")
                        break
                
            except Exception as e:
                logger.error(f"Error crawling category page {page_num}: {str(e)}")
                break
        
        return thread_urls, pages_crawled
    
    def _process_thread(self, forum: Forum, thread_url: str, keywords: List[Keyword]) -> List[Match]:
        """
        Process a thread and check for keyword matches in all posts.
        
        Args:
            forum: Forum object
            thread_url: Thread URL to process
            keywords: Keywords to search for
            
        Returns:
            List of Match objects created
        """
        matches = []
        
        try:
            # Detect if this is Reddit (JSON API)
            is_reddit = 'reddit.com' in thread_url
            
            # Fetch thread page (JSON for Reddit, HTML for others)
            soup = self.crawler.fetch(thread_url + '.json' if is_reddit else thread_url, json_mode=is_reddit)
            if not soup:
                return matches
            
            # Extract all posts from thread
            posts = self.parser.extract_all_posts(soup)
            if not posts:
                logger.warning(f"No posts extracted from {thread_url}")
                return matches
            
            logger.debug(f"Processing {len(posts)} posts from thread")
            
            # Track which keywords have been matched in this thread (deduplicate)
            matched_keywords = set()
            
            # Check each post for keywords
            for post in posts:
                post_content = post['content'].lower()
                post_number = post.get('post_number', 0)
                author = post.get('author', 'Unknown')
                
                # Check each keyword
                for keyword in keywords:
                    # Skip if this keyword already matched in this thread
                    if keyword.id in matched_keywords:
                        continue
                    
                    if keyword.keyword.lower() in post_content:
                        # Create snippet (extract context around keyword)
                        snippet = self._create_snippet(post_content, keyword.keyword.lower())
                        
                        # Add context: post number and author
                        snippet_with_context = f"[Post #{post_number} by {author}] {snippet}"
                        
                        # Save match to database (only first occurrence per thread)
                        match = self._save_match(forum, keyword, thread_url, snippet_with_context)
                        if match:
                            matches.append(match)
                            matched_keywords.add(keyword.id)  # Mark as matched
                            logger.info(f"Match found: '{keyword.keyword}' in {thread_url} (post #{post_number})")
        
        except Exception as e:
            logger.error(f"Error processing thread {thread_url}: {str(e)}")
        
        return matches
    
    def _create_snippet(self, text: str, keyword: str, context_length: int = 200) -> str:
        """
        Create a snippet around the keyword.
        
        Args:
            text: Full text
            keyword: Keyword to find
            context_length: Characters of context to include
            
        Returns:
            Snippet string
        """
        pos = text.find(keyword)
        if pos == -1:
            return text[:context_length]
        
        start = max(0, pos - context_length // 2)
        end = min(len(text), pos + len(keyword) + context_length // 2)
        
        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _save_match(self, forum: Forum, keyword: Keyword, url: str, snippet: str) -> Optional[Match]:
        """
        Save a match to the database.
        
        Args:
            forum: Forum object
            keyword: Keyword object
            url: Page URL
            snippet: Text snippet
            
        Returns:
            Match object if saved, None if duplicate
        """
        try:
            match = Match(
                forum_id=forum.id,
                keyword_id=keyword.id,
                page_url=url,
                snippet=snippet
            )
            self.db_session.add(match)
            self.db_session.commit()
            return match
        except IntegrityError:
            self.db_session.rollback()
            logger.debug(f"Duplicate match skipped: {url}")
            return None
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving match: {str(e)}")
            return None
    
    def close(self):
        """Close the crawler."""
        self.crawler.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
