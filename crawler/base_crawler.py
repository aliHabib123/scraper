import httpx
import time
import logging
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseCrawler:
    """Base crawler with rate limiting and error handling."""
    
    def __init__(self, rate_limit: float = 2.0, timeout: int = 30):
        """
        Initialize crawler.
        
        Args:
            rate_limit: Minimum seconds between requests (default: 2.0)
            timeout: Request timeout in seconds (default: 30)
        """
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        self._wait_for_rate_limit()
        
        try:
            logger.info(f"Fetching: {url}")
            response = self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
        
        return None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
