#!/usr/bin/env python3
"""
Forum Crawler - Main Entrypoint

Monitors public forums for keyword mentions.
"""

import logging
import sys
import argparse
from typing import Dict, List

from sqlalchemy.orm import Session

from models import Forum, Keyword
from models.base import get_session_maker, init_db
from crawler import ForumCrawler
from parsers import CasinoGuruParser, BitcoinTalkParser, RedditParser, AskGamblersParser, BigWinBoardParser
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
    
    # Set rate limit based on forum type
    # Reddit: 100 requests per 10 minutes = 1 request per 6 seconds minimum
    # Use 7 seconds to be safe
    is_reddit = forum.name.lower() == 'reddit' or forum.name.startswith('r/')
    rate_limit = 7.0 if is_reddit else 2.0
    
    logger.info(f"Using rate limit: {rate_limit}s per request")
    
    # Create crawler with appropriate rate limit
    crawler = ForumCrawler(session, parser, rate_limit=rate_limit)
    
    # Crawl and get results
    stats = crawler.crawl_forum(forum, keywords)
    
    # Get matches from database for this forum (for notifications)
    from models import Match
    matches = session.query(Match).filter(
        Match.forum_id == forum.id,
        Match.keyword_id.in_([k.id for k in keywords])
    ).all()
    
    # Send notifications if new matches found and notifier configured
    if notifier and stats['matches_found'] > 0:
        match_data = [{
            'keyword': m.keyword.keyword,
            'url': m.page_url,
            'snippet': m.snippet
        } for m in matches[-stats['matches_found']:]]
        notifier.notify_matches(forum.name, match_data)
    
    # Send summary notification
    if notifier:
        notifier.notify_crawl_summary(forum.name, stats)
    
    return stats


def crawl_all_forums(session: Session, rate_limit: float = 2.0, notifier: TelegramNotifier = None) -> Dict[str, Dict]:
    """
    Crawl all enabled forums for all enabled keywords.
    
    Args:
        session: Database session
        rate_limit: Seconds between requests
        notifier: Optional Telegram notifier
        
    Returns:
        Dict with stats for each forum
    """
    # Fetch enabled forums and keywords
    forums = session.query(Forum).filter(Forum.enabled == True).all()
    keywords = session.query(Keyword).filter(Keyword.enabled == True).all()
    
    if not forums:
        logger.warning("No enabled forums found in database")
        return {}
    
    if not keywords:
        logger.warning("No enabled keywords found in database")
        return {}
    
    logger.info(f"Starting crawl: {len(forums)} forums, {len(keywords)} keywords")
    
    results = {}
    
    for forum in forums:
        try:
            stats = crawl_forum(session, forum, keywords, notifier)
            results[forum.name] = stats
        except Exception as e:
            logger.error(f"Error crawling {forum.name}: {str(e)}")
            results[forum.name] = {'matches_found': 0, 'pages_crawled': 0, 'errors': 1}
    
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
        
        results = crawl_all_forums(session, rate_limit=args.rate_limit, notifier=notifier)
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
