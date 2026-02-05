import httpx
import time
import logging
from typing import Optional, Union, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseCrawler:
    """Base crawler with rate limiting and error handling."""
    
    def __init__(self, rate_limit: float = 2.0, timeout: int = 30, cookies: Optional[Dict[str, str]] = None):
        """
        Initialize crawler.
        
        Args:
            rate_limit: Minimum seconds between requests (default: 2.0)
            timeout: Request timeout in seconds (default: 30)
            cookies: Optional dict of cookies to send with requests
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            cookies=cookies or {},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
        )
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def warm_up_session(self, base_url: str) -> bool:
        """
        Warm up session by visiting the homepage to establish cookies.
        Critical for sites like XenForo that require cookies from first visit.
        
        Args:
            base_url: Base URL of the site (e.g., https://www.casinomeister.com)
            
        Returns:
            True if warm-up successful, False otherwise
        """
        self._wait_for_rate_limit()
        
        try:
            logger.info(f"Warming up session: {base_url}")
            response = self.client.get(base_url)
            response.raise_for_status()
            logger.info(f"Session warm-up successful (cookies established)")
            return True
        except Exception as e:
            logger.warning(f"Session warm-up failed: {str(e)}")
            return False
    
    def fetch_page(self, url: str, referer: Optional[str] = None) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            referer: Optional Referer header to make request look like internal navigation
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        self._wait_for_rate_limit()
        
        try:
            logger.info(f"Fetching: {url}")
            
            # Add Referer header if provided (helps with bot detection)
            headers = {}
            if referer:
                headers['Referer'] = referer
            
            response = self.client.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
        
        return None
    
    def fetch_json(self, url: str, max_retries: int = 3) -> Optional[Dict[Any, Any]]:
        """
        Fetch a JSON API response (e.g., Reddit) with retry logic.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retries for rate limit errors
            
        Returns:
            Dict (parsed JSON) or None if request fails
        """
        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            
            try:
                logger.info(f"Fetching: {url}")
                response = self.client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    # Check x-ratelimit-reset header for wait time
                    reset_after = e.response.headers.get('x-ratelimit-reset', '60')
                    wait_time = int(reset_after) + 5  # Add 5 second buffer
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limited (429) on final attempt. URL: {url}")
                else:
                    logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
                break
            except httpx.RequestError as e:
                logger.error(f"Request error fetching {url}: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {str(e)}")
                break
        
        return None
    
    def fetch(self, url: str, json_mode: bool = False) -> Optional[Union[BeautifulSoup, Dict[Any, Any]]]:
        """
        Fetch a page - returns either BeautifulSoup (HTML) or Dict (JSON).
        
        Args:
            url: URL to fetch
            json_mode: If True, parse as JSON instead of HTML
            
        Returns:
            BeautifulSoup object, Dict, or None if request fails
        """
        if json_mode:
            return self.fetch_json(url)
        return self.fetch_page(url)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
