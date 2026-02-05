import time
import random
import logging
import httpx
from typing import Optional, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FlareSolverrCrawler:
    """Crawler using FlareSolverr service for Cloudflare bypass."""
    
    def __init__(self, rate_limit: float = 2.0, flaresolverr_url: str = "http://localhost:8191/v1"):
        """
        Initialize FlareSolverr crawler.
        
        Args:
            rate_limit: Minimum seconds between requests
            flaresolverr_url: FlareSolverr API endpoint
        """
        self.rate_limit = rate_limit
        self.flaresolverr_url = flaresolverr_url
        self.last_request_time = 0
        self.session_id = None
        
        logger.info(f"FlareSolverr crawler initialized (API: {flaresolverr_url})")
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limiting with random jitter."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            wait_time = self.rate_limit - elapsed
            
            if wait_time > 0:
                # Add small random jitter (0-0.5s)
                jitter = random.uniform(0, 0.5)
                total_wait = wait_time + jitter
                time.sleep(total_wait)
        
        self.last_request_time = time.time()
    
    def _create_session(self) -> Optional[str]:
        """Create a FlareSolverr session for maintaining cookies/state."""
        try:
            response = httpx.post(
                self.flaresolverr_url,
                json={"cmd": "sessions.create"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "ok":
                session_id = data.get("session")
                logger.info(f"FlareSolverr session created: {session_id}")
                return session_id
            else:
                logger.error(f"Failed to create FlareSolverr session: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating FlareSolverr session: {str(e)}")
            return None
    
    def fetch_page(self, url: str, referer: Optional[str] = None) -> Optional[BeautifulSoup]:
        """
        Fetch a page using FlareSolverr and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            referer: Optional Referer header
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        self._wait_for_rate_limit()
        
        # Create session if not exists
        if not self.session_id:
            self.session_id = self._create_session()
        
        try:
            logger.info(f"Fetching with FlareSolverr: {url}")
            
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000,  # 60 seconds
            }
            
            # Add session if available
            if self.session_id:
                payload["session"] = self.session_id
            
            # Make request to FlareSolverr
            response = httpx.post(
                self.flaresolverr_url,
                json=payload,
                timeout=70  # Slightly longer than maxTimeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                logger.error(f"FlareSolverr error: {data.get('message', 'Unknown error')}")
                return None
            
            # Extract HTML from response
            solution = data.get("solution", {})
            html = solution.get("response")
            status = solution.get("status")
            
            if not html:
                logger.error(f"No HTML content in FlareSolverr response")
                return None
            
            if status and status >= 400:
                logger.error(f"HTTP error from FlareSolverr: {status}")
                return None
            
            logger.info(f"✓ Successfully fetched via FlareSolverr: {url}")
            return BeautifulSoup(html, 'html.parser')
            
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {url} with FlareSolverr")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url} with FlareSolverr: {str(e)}")
            return None
    
    def fetch(self, url: str, json_mode: bool = False):
        """
        Compatibility method for BaseCrawler interface.
        
        Args:
            url: URL to fetch
            json_mode: Not supported in FlareSolverr (returns HTML as BeautifulSoup)
            
        Returns:
            BeautifulSoup object or None
        """
        if json_mode:
            logger.warning("JSON mode not supported in FlareSolverrCrawler, fetching as HTML")
        return self.fetch_page(url)
    
    def warm_up_session(self, base_url: str) -> bool:
        """
        Warm up session by visiting homepage.
        
        Args:
            base_url: Base URL of the site
            
        Returns:
            True if successful
        """
        logger.info(f"FlareSolverr warm-up: {base_url}")
        result = self.fetch_page(base_url)
        if result:
            logger.info("FlareSolverr session warmed up successfully")
            return True
        else:
            logger.warning("FlareSolverr warm-up failed (continuing anyway)")
            return True  # Continue anyway
    
    def close(self):
        """Close session and cleanup resources."""
        if self.session_id:
            try:
                httpx.post(
                    self.flaresolverr_url,
                    json={
                        "cmd": "sessions.destroy",
                        "session": self.session_id
                    },
                    timeout=10
                )
                logger.info(f"FlareSolverr session closed: {self.session_id}")
            except Exception as e:
                logger.warning(f"Error closing FlareSolverr session: {str(e)}")
        
        self.session_id = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
