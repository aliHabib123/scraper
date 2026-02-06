import time
import random
import logging
import os
from typing import Optional
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None

try:
    from playwright_stealth import stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    stealth_sync = None

try:
    import capsolver
    CAPSOLVER_AVAILABLE = True
except ImportError:
    CAPSOLVER_AVAILABLE = False
    capsolver = None

logger = logging.getLogger(__name__)


class PlaywrightCrawler:
    """Crawler using Playwright for sites with Cloudflare/bot protection."""
    
    def __init__(self, rate_limit: float = 2.0, timeout: int = 30, headless: bool = True, persistent_state: bool = True):
        """
        Initialize Playwright crawler.
        
        Args:
            rate_limit: Minimum seconds between requests
            timeout: Request timeout in seconds
            headless: Run browser in headless mode (default: True)
            persistent_state: Use persistent browser state for better Cloudflare bypass (default: True)
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
        self.persistent_state = persistent_state
        self.last_request_time = 0
        self.state_file = 'playwright_state.json'
        
        # Initialize CapSolver if available and API key is set
        self.capsolver_enabled = False
        if CAPSOLVER_AVAILABLE:
            api_key = os.getenv('CAPSOLVER_API_KEY')
            if api_key:
                capsolver.api_key = api_key
                self.capsolver_enabled = True
                logger.info("CapSolver enabled for automatic Cloudflare challenge solving")
            else:
                logger.warning("CapSolver installed but CAPSOLVER_API_KEY not set")
        else:
            logger.debug("CapSolver not available - install with: pip install capsolver")
        
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
        # Load persistent state if available (for better Cloudflare bypass)
        import os
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation'],
            'extra_http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        }
        
        # Load persistent state if it exists
        if self.persistent_state and os.path.exists(self.state_file):
            try:
                context_options['storage_state'] = self.state_file
                logger.info(f"Loaded persistent browser state from {self.state_file}")
            except Exception as e:
                logger.warning(f"Failed to load persistent state: {e}")
        
        self.context: BrowserContext = self.browser.new_context(**context_options)
        
        # Create page and inject anti-detection scripts
        self.page: Page = self.context.new_page()
        
        # Apply playwright-stealth if available (better Cloudflare bypass)
        if STEALTH_AVAILABLE:
            stealth_sync(self.page)
            logger.info("Playwright stealth mode enabled")
        
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
            
            # Wait for JavaScript-rendered content to load
            # Try to wait for common content indicators
            try:
                # Wait for discussion items or main content area (with timeout)
                self.page.wait_for_selector('a[href*="/discussion/"]', timeout=5000, state='visible')
            except:
                # If specific selector times out, just wait a bit
                logger.debug("Specific selector not found, using general wait")
            
            # Additional wait for dynamic content
            self.page.wait_for_timeout(2000)  # 2 seconds for JS to fully render
            
            # Human-like behavior: random scroll
            self._simulate_human_behavior()
            
            # Get page content
            html = self.page.content()
            
            # Save persistent state for next run (better Cloudflare bypass)
            if self.persistent_state:
                try:
                    self.context.storage_state(path=self.state_file)
                except Exception as e:
                    logger.debug(f"Could not save state: {e}")
            
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
    
    def _simulate_human_behavior(self):
        """Simulate human-like mouse movement and scrolling."""
        try:
            # Random mouse movement
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            self.page.mouse.move(x, y)
            
            # Random scroll
            scroll_amount = random.randint(300, 800)
            self.page.mouse.wheel(0, scroll_amount)
            
            # Random short wait
            wait_ms = random.randint(500, 1500)
            self.page.wait_for_timeout(wait_ms)
            
        except Exception as e:
            logger.debug(f"Human behavior simulation failed (non-critical): {e}")
    
    def _solve_cloudflare_challenge(self, url: str) -> bool:
        """
        Solve Cloudflare Turnstile challenge using CapSolver.
        
        Args:
            url: URL of the page with the challenge
            
        Returns:
            True if challenge was solved, False otherwise
        """
        if not self.capsolver_enabled:
            return False
        
        try:
            # Extract site key from page
            page_content = self.page.content()
            
            # Cloudflare Turnstile uses data-sitekey attribute
            import re
            sitekey_match = re.search(r'data-sitekey=["\']([^"\']+)["\']', page_content)
            if not sitekey_match:
                # Try finding cf-chl-widget or turnstile widget
                sitekey_match = re.search(r'sitekey["\']?\s*:\s*["\']([^"\']+)["\']', page_content)
            
            if not sitekey_match:
                logger.warning("Could not extract Cloudflare site key from page")
                return False
            
            sitekey = sitekey_match.group(1)
            logger.info(f"Found Cloudflare site key: {sitekey[:20]}...")
            
            # Solve with CapSolver
            logger.info("Sending challenge to CapSolver...")
            solution = capsolver.solve({
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": url,
                "websiteKey": sitekey,
            })
            
            if not solution or 'token' not in solution:
                logger.error("CapSolver did not return a valid token")
                return False
            
            token = solution['token']
            logger.info("Received solution token from CapSolver")
            
            # Inject token into Cloudflare response field
            self.page.evaluate(f"""
                () => {{
                    const responseField = document.querySelector('[name="cf-turnstile-response"]');
                    if (responseField) {{
                        responseField.value = '{token}';
                    }}
                    
                    // Trigger Cloudflare callback
                    if (window.turnstile && window.turnstile.reset) {{
                        window.turnstile.reset();
                    }}
                }}
            """)
            
            # Wait for page to reload or challenge to clear
            self.page.wait_for_timeout(3000)
            
            # Check if challenge is still present
            page_content_after = self.page.content().lower()
            if 'challenge' in page_content_after or 'checking your browser' in page_content_after:
                logger.warning("Challenge still present after token injection")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"CapSolver challenge solving failed: {str(e)}")
            return False
    
    def warm_up_session(self, base_url: str) -> bool:
        """
        Advanced warm-up: visit homepage, browse internal links, idle.
        Critical for bypassing aggressive Cloudflare on datacenter IPs.
        
        Args:
            base_url: Base URL of the site
            
        Returns:
            True if warm-up successful, False otherwise
        """
        logger.info(f"🔥 Advanced IP warm-up for aggressive Cloudflare: {base_url}")
        
        try:
            # Step 1: Visit homepage
            logger.info("  1/4 Visiting homepage...")
            self.page.goto(base_url, timeout=self.timeout, wait_until='domcontentloaded')
            self.page.wait_for_timeout(random.randint(2000, 4000))
            self._simulate_human_behavior()
            
            # Check for Cloudflare challenge
            page_content = self.page.content().lower()
            if 'cloudflare' in page_content and ('challenge' in page_content or 'checking your browser' in page_content or 'verify you are human' in page_content or 'turnstile' in page_content):
                logger.warning("⚠️  Cloudflare challenge detected!")
                
                # Try CapSolver first if available
                if self.capsolver_enabled:
                    logger.info("Attempting to solve Cloudflare challenge with CapSolver...")
                    if self._solve_cloudflare_challenge(base_url):
                        logger.info("✓ Cloudflare challenge solved with CapSolver")
                    else:
                        logger.error("❌ CapSolver failed to solve challenge")
                        return False
                else:
                    # Manual completion fallback
                    logger.warning("Please complete the challenge in the browser window...")
                    logger.warning("Waiting 30 seconds for manual completion...")
                    self.page.wait_for_timeout(30000)
                    
                    page_content_after = self.page.content().lower()
                    if 'cloudflare' in page_content_after and 'challenge' in page_content_after:
                        logger.error("❌ Cloudflare challenge not completed")
                        return False
                    else:
                        logger.info("✓ Cloudflare challenge completed")
            
            # Step 2: Click 2-3 internal links
            logger.info("  2/4 Browsing internal links...")
            soup = BeautifulSoup(self.page.content(), 'html.parser')
            internal_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/') or base_url in href:
                    if not href.startswith('#') and 'javascript:' not in href:
                        full_url = href if href.startswith('http') else base_url.rstrip('/') + href
                        internal_links.append(full_url)
                        if len(internal_links) >= 10:  # Collect up to 10 candidates
                            break
            
            # Visit 2-3 random internal links (if available)
            if len(internal_links) >= 2:
                num_links = random.randint(2, min(3, len(internal_links)))
                sample_links = random.sample(internal_links, num_links)
            elif len(internal_links) == 1:
                num_links = 1
                sample_links = internal_links
            else:
                logger.debug("No internal links found for warm-up browsing")
                num_links = 0
                sample_links = []
            
            for i, link in enumerate(sample_links, 1):
                logger.info(f"     Visiting internal link {i}/{num_links}...")
                try:
                    self.page.goto(link, timeout=self.timeout, wait_until='domcontentloaded')
                    self.page.wait_for_timeout(random.randint(1500, 3000))
                    self._simulate_human_behavior()
                except Exception as e:
                    logger.debug(f"Failed to visit internal link (non-critical): {e}")
            
            # Step 3: Go back to homepage
            logger.info("  3/4 Returning to homepage...")
            self.page.goto(base_url, timeout=self.timeout, wait_until='domcontentloaded')
            
            # Step 4: Idle for 30-60 seconds (appear as real user reading)
            idle_time = random.randint(30, 60)
            logger.info(f"  4/4 Idling for {idle_time} seconds (appearing as real user)...")
            
            for i in range(0, idle_time, 10):
                self.page.wait_for_timeout(10000)
                # Occasional mouse movement during idle
                if random.random() > 0.5:
                    self._simulate_human_behavior()
            
            logger.info("✓ IP warm-up complete - ready to scrape")
            
            # Save state after successful warm-up
            if self.persistent_state:
                try:
                    self.context.storage_state(path=self.state_file)
                    logger.info(f"  Saved session state to {self.state_file}")
                except Exception as e:
                    logger.debug(f"Could not save state: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Warm-up failed: {str(e)}")
            return False
    
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
