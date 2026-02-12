#!/usr/bin/env python3
"""
Forum Crawler - Main Entrypoint

Monitors public forums for keyword mentions.
"""

import logging
import sys
import argparse
import os
import json
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models import Forum, Keyword
from models.base import get_session_maker, init_db
from crawler import ForumCrawler
from parsers import CasinoGuruParser, BitcoinTalkParser, RedditParser, AskGamblersParser, BigWinBoardParser, XenForoParser, OwnedCoreParser, MoneySavingExpertParser, LCBParser
from notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crawler.log')
    ]
)

logger = logging.getLogger(__name__)


def get_cookies_for_forum(forum_name: str) -> Optional[Dict[str, str]]:
    """
    Load cookies from environment for specific forums.
    
    Args:
        forum_name: Name of the forum
        
    Returns:
        Dict of cookies or None
    """
    # Check for forum-specific cookies in environment
    # Format: CASINOMEISTER_COOKIES='{"cookie_name": "cookie_value", ...}'
    env_key = f"{forum_name.upper().replace('.', '_').replace('-', '_')}_COOKIES"
    cookies_json = os.getenv(env_key)
    
    if cookies_json:
        try:
            cookies = json.loads(cookies_json)
            logger.info(f"Loaded {len(cookies)} cookies for {forum_name}")
            return cookies
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse cookies for {forum_name}: {e}")
    
    return None


def get_parser_for_forum(forum_name: str):
    """
    Get the appropriate parser for a forum.
    
    Args:
        forum_name: Name of the forum
        
    Returns:
        Parser instance
    """
    # Check if it's a Reddit forum
    # Supports both 'reddit' (single forum) and 'r/subreddit' (per-subreddit forums)
    if forum_name.lower() == 'reddit' or forum_name.startswith('r/'):
        return RedditParser()
    
    parsers = {
        'casino.guru': CasinoGuruParser,
        'casino_guru': CasinoGuruParser,
        'bitcointalk': BitcoinTalkParser,
        'bitcointalk.org': BitcoinTalkParser,
        'askgamblers': AskGamblersParser,
        'askgamblers.com': AskGamblersParser,
        'bigwinboard': BigWinBoardParser,
        'bigwinboard.com': BigWinBoardParser,
        'casinomeister': XenForoParser,
        'casinomeister.com': XenForoParser,
        'ownedcore': OwnedCoreParser,
        'ownedcore.com': OwnedCoreParser,
        'moneysavingexpert': MoneySavingExpertParser,
        'moneysavingexpert.com': MoneySavingExpertParser,
        'lcb.org': LCBParser,
        'lcb': LCBParser,
    }
    
    parser_class = parsers.get(forum_name.lower())
    if not parser_class:
        # Default to CasinoGuruParser as fallback
        logger.warning(f"No specific parser for '{forum_name}', using CasinoGuruParser")
        parser_class = CasinoGuruParser
    
    return parser_class()


def crawl_forum(session: Session, forum: Forum, keywords: List[Keyword], notifier: TelegramNotifier = None) -> Dict[str, int]:
    """
    Crawl a single forum for keywords.
    
    Args:
        session: Database session
        forum: Forum to crawl
        keywords: Keywords to search for
        notifier: Optional Telegram notifier
        
    Returns:
        Dict with crawl statistics
    """
    logger.info(f"Processing forum: {forum.name}")
    
    # Get appropriate parser
    parser = get_parser_for_forum(forum.name)
    
    # Get cookies if available
    cookies = get_cookies_for_forum(forum.name)
    
    # Set rate limit based on forum type
    # Reddit: 100 requests per 10 minutes = 1 request per 6 seconds minimum
    # CasinoMeister/OwnedCore/MoneySavingExpert/AskGamblers/BigWinBoard: Has bot protection or JS rendering, use 3 seconds
    # LCB.org: Aggressive anti-scraping, use 5 seconds to avoid connection resets
    is_reddit = forum.name.lower() == 'reddit' or forum.name.startswith('r/')
    is_casinomeister = 'casinomeister' in forum.name.lower()
    is_ownedcore = 'ownedcore' in forum.name.lower()
    is_moneysavingexpert = 'moneysavingexpert' in forum.name.lower()
    is_askgamblers = 'askgamblers' in forum.name.lower()
    is_bigwinboard = 'bigwinboard' in forum.name.lower()
    is_lcb = 'lcb' in forum.name.lower()
    
    if is_reddit:
        rate_limit = 12.0  # Reddit aggressive rate limiting - slow down to avoid 403s
    elif is_lcb:
        rate_limit = 5.0  # LCB.org has aggressive anti-scraping protection
    elif is_casinomeister or is_ownedcore or is_moneysavingexpert or is_askgamblers or is_bigwinboard:
        rate_limit = 5.0  # Playwright/bot protection bypass or JS rendering
    else:
        rate_limit = 5.0
    
    logger.info(f"Using rate limit: {rate_limit}s per request")
    
    # Choose Cloudflare/bot bypass method
    # All forums with aggressive Cloudflare or JS rendering: Use Playwright with advanced bypass
    use_flaresolverr = False  # FlareSolverr disabled - using Playwright with persistent state instead
    use_playwright = is_casinomeister or is_moneysavingexpert or is_askgamblers or is_bigwinboard or is_ownedcore
    
    if use_flaresolverr:
        logger.info("Enabling FlareSolverr for Cloudflare bypass")
    elif use_playwright:
        logger.info("Enabling Playwright for bot protection bypass")
    
    # Check if headless mode should be disabled (for testing/debugging)
    # Set PLAYWRIGHT_HEADLESS=false to see browser window (useful on macOS for testing)
    headless = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() != 'false'
    
    # Create crawler with appropriate rate limit and cookies
    crawler = ForumCrawler(session, parser, rate_limit=rate_limit, cookies=cookies, use_playwright=use_playwright, use_flaresolverr=use_flaresolverr, headless=headless)
    
    # Crawl and get results
    stats = crawler.crawl_forum(forum, keywords)
    
    # Get matches from database for this forum (for notifications)
    from models import Match
    matches = session.query(Match).filter(
        Match.forum_id == forum.id,
        Match.keyword_id.in_([k.id for k in keywords])
    ).all()
    
    # Send consolidated notification with matches and summary
    if notifier:
        match_data = None
        if stats['matches_found'] > 0:
            match_data = [{
                'keyword': m.keyword.keyword,
                'url': m.page_url,
                'snippet': m.snippet
            } for m in matches[-stats['matches_found']:]]
        
        notifier.notify_forum_results(forum.name, stats, match_data)
    
    return stats


def crawl_all_forums(session: Session, notifier: TelegramNotifier = None) -> Dict[str, Dict]:
    """
    Crawl all enabled forums for all enabled keywords with automatic retry on rate limits.
    
    When a forum hits rate limits (e.g., Reddit 403), it moves to the next forum
    and retries the blocked forum after all others are processed.
    
    Args:
        session: Database session
        notifier: Optional Telegram notifier
        
    Returns:
        Dict mapping forum names to crawl statistics
    """
    # Get all enabled forums
    forums = session.query(Forum).filter(Forum.enabled == True).all()
    
    # Get all enabled keywords
    keywords = session.query(Keyword).filter(Keyword.enabled == True).all()
    
    if not forums:
        logger.warning("No enabled forums found in database")
        return {}
    
    if not keywords:
        logger.warning("No enabled keywords found in database")
        return {}
    
    logger.info(f"Starting crawl: {len(forums)} forums, {len(keywords)} keywords")
    
    results = {}
    failed_forums = []  # Forums that hit rate limits
    max_retries = 2  # Maximum retry attempts per forum
    retry_wait_minutes = 30  # Wait time before retrying rate-limited forums
    
    # First pass: crawl all forums
    for forum in forums:
        try:
            logger.info(f"Processing forum: {forum.name}")
            stats = crawl_forum(session, forum, keywords, notifier)
            results[forum.name] = stats
            
            # Check if forum hit rate limits (high error rate)
            error_rate = stats.get('errors', 0) / max(stats.get('threads_found', 1), 1)
            if error_rate > 0.5 and stats.get('errors', 0) > 10:
                logger.warning(f"{forum.name} hit rate limits (error rate: {error_rate:.0%})")
                failed_forums.append({'forum': forum, 'retry_count': 0})
        except Exception as e:
            logger.error(f"Error crawling {forum.name}: {str(e)}")
            results[forum.name] = {'matches_found': 0, 'pages_crawled': 0, 'errors': 1}
    
    # Retry pass: attempt rate-limited forums after waiting
    if failed_forums:
        logger.info(f"\n{'='*60}")
        logger.info(f"Detected {len(failed_forums)} forum(s) with rate limiting")
        logger.info(f"Waiting {retry_wait_minutes} minutes before retry...")
        logger.info(f"{'='*60}\n")
        
        import time
        time.sleep(retry_wait_minutes * 60)  # Wait before retrying
        
        for item in failed_forums[:]:  # Copy list to allow modification
            forum = item['forum']
            retry_count = item['retry_count']
            
            if retry_count >= max_retries:
                logger.warning(f"Skipping {forum.name} - max retries reached")
                continue
            
            try:
                logger.info(f"Retrying forum: {forum.name} (attempt {retry_count + 1}/{max_retries})")
                stats = crawl_forum(session, forum, keywords, notifier)
                
                # Merge stats with previous results
                prev_stats = results.get(forum.name, {})
                results[forum.name] = {
                    'matches_found': prev_stats.get('matches_found', 0) + stats.get('matches_found', 0),
                    'pages_crawled': prev_stats.get('pages_crawled', 0) + stats.get('pages_crawled', 0),
                    'threads_found': prev_stats.get('threads_found', 0) + stats.get('threads_found', 0),
                    'errors': prev_stats.get('errors', 0) + stats.get('errors', 0),
                }
                
                logger.info(f"✓ Successfully retried {forum.name}")
                failed_forums.remove(item)
            except Exception as e:
                logger.error(f"Retry failed for {forum.name}: {str(e)}")
                item['retry_count'] += 1
    
    return results


def print_summary(results: Dict[str, Dict]):
    """Print summary of crawl results."""
    print("\n" + "="*60)
    print("CRAWL SUMMARY")
    print("="*60)
    
    total_matches = 0
    total_pages = 0
    total_threads = 0
    total_errors = 0
    
    for forum_name, stats in results.items():
        matches = stats.get('matches_found', 0)
        pages = stats.get('pages_crawled', 0)
        threads = stats.get('threads_found', 0)
        errors = stats.get('errors', 0)
        
        total_matches += matches
        total_pages += pages
        total_threads += threads
        total_errors += errors
        
        print(f"\n{forum_name}:")
        print(f"  Matches found: {matches}")
        print(f"  Pages crawled: {pages}")
        print(f"  Threads processed: {threads}")
        print(f"  Errors: {errors}")
    
    print("\n" + "-"*60)
    print("TOTALS:")
    print(f"  Total matches: {total_matches}")
    print(f"  Total pages: {total_pages}")
    print(f"  Total threads: {total_threads}")
    print(f"  Total errors: {total_errors}")
    print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Forum keyword crawler')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--rate-limit', type=float, help='Rate limit in seconds')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize Telegram notifier
    notifier = None if args.no_telegram else TelegramNotifier()
    
    # Get database session
    SessionMaker = get_session_maker()
    session = SessionMaker()
    
    # Run crawler
    try:
        SessionMaker = get_session_maker()
        session = SessionMaker()
        
        results = crawl_all_forums(session, notifier=notifier)
        print_summary(results)
        
        session.close()
        
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
