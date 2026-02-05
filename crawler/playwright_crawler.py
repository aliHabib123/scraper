import time
import random
import logging
from typing import Optional
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None

logger = logging.getLogger(__name__)


class PlaywrightCrawler:
    """Crawler using Playwright for sites with Cloudflare/bot protection."""
    
    def __init__(self, rate_limit: float = 2.0, timeout: int = 30, headless: bool = True):
        """
        Initialize Playwright crawler.
        
        Args:
            rate_limit: Minimum seconds between requests
            timeout: Request timeout in seconds
            headless: Run browser in headless mode (default: True)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )
        
        self.rate_limit = rate_limit
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.headless = headless
        self.last_request_time = 0
        
        # Initialize Playwright with stealth settings
        self.playwright = sync_playwright().start()
        
        # Launch with args to avoid detection
        self.browser: Browser = self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        # Create context with realistic browser fingerprint
        self.context: BrowserContext = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # Create page and inject anti-detection scripts
        self.page: Page = self.context.new_page()
        
        # Remove webdriver property
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Add realistic chrome object
            window.chrome = {
                runtime: {}
            };
            
            // Override plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        logger.info("Playwright browser initialized")
    
    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests with random jitter."""
        elapsed = time.time() - self.last_request_time
        
        # Add random jitter (0-0.5 seconds) to make timing more human-like
        jitter = random.uniform(0, 0.5)
        wait_time = self.rate_limit + jitter
        
        if elapsed < wait_time:
            time.sleep(wait_time - elapsed)
        
        self.last_request_time = time.time()
    
    def fetch_page(self, url: str, referer: Optional[str] = None) -> Optional[BeautifulSoup]:
        """
        Fetch a page using Playwright and return BeautifulSoup object.
        
        Args:
            url: URL to fetch
            referer: Optional Referer header (not used in Playwright, kept for compatibility)
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        self._wait_for_rate_limit()
        
        try:
            logger.info(f"Fetching with Playwright: {url}")
            
            # Navigate to the page
            response = self.page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
            
            if response is None:
                logger.error(f"Failed to load page: {url}")
                return None
            
            # Check status code
            if response.status >= 400:
                logger.error(f"HTTP error fetching {url}: {response.status}")
                return None
            
            # Wait a bit for any JavaScript to execute
            self.page.wait_for_timeout(1000)  # 1 second
            
            # Get page content
            html = self.page.content()
            
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error fetching {url} with Playwright: {str(e)}")
            return None
    
    def fetch(self, url: str, json_mode: bool = False):
        """
        Compatibility method for BaseCrawler interface.
        
        Args:
            url: URL to fetch
            json_mode: Not supported in Playwright (returns HTML as BeautifulSoup)
            
        Returns:
            BeautifulSoup object or None
        """
        if json_mode:
            logger.warning("JSON mode not supported in PlaywrightCrawler, fetching as HTML")
        return self.fetch_page(url)
    
    def warm_up_session(self, base_url: str) -> bool:
        """
        Warm up session by visiting homepage (optional for Playwright).
        
        Args:
            base_url: Base URL of the site
            
        Returns:
            Always True (Playwright handles this automatically)
        """
        logger.info(f"Playwright warm-up (bypasses Cloudflare automatically): {base_url}")
        # Playwright doesn't need explicit warm-up, but we can visit the homepage anyway
        try:
            self.page.goto(base_url, timeout=self.timeout, wait_until='domcontentloaded')
            self.page.wait_for_timeout(2000)  # Wait 2 seconds for Cloudflare challenge
            logger.info("Playwright session ready")
            return True
        except Exception as e:
            logger.warning(f"Warm-up navigation failed (continuing anyway): {str(e)}")
            return True  # Continue anyway, individual requests will handle errors
    
    def close(self):
        """Close browser and cleanup resources."""
        try:
            if hasattr(self, 'page'):
                self.page.close()
            if hasattr(self, 'context'):
                self.context.close()
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
            logger.info("Playwright browser closed")
        except Exception as e:
            logger.warning(f"Error closing Playwright: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
