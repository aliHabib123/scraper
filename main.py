#!/usr/bin/env python3
"""
Forum Crawler - Main Entrypoint

Monitors public forums for keyword mentions.
"""

import logging
import sys
import argparse
from typing import Dict

from sqlalchemy.orm import Session

from models import Forum, Keyword
from models.base import get_session_maker, init_db
from crawler import ForumCrawler
from parsers import CasinoGuruParser, BitcoinTalkParser

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
    parsers = {
        'casino.guru': CasinoGuruParser,
        'casino_guru': CasinoGuruParser,
        'bitcointalk': BitcoinTalkParser,
        'bitcointalk.org': BitcoinTalkParser,
    }
    
    parser_class = parsers.get(forum_name.lower())
    if not parser_class:
        # Default to CasinoGuruParser as fallback
        logger.warning(f"No specific parser for '{forum_name}', using CasinoGuruParser")
        parser_class = CasinoGuruParser
    
    return parser_class()


def crawl_all_forums(session: Session, rate_limit: float = 2.0) -> Dict[str, Dict]:
    """
    Crawl all enabled forums for all enabled keywords.
    
    Args:
        session: Database session
        rate_limit: Seconds between requests
        
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
        logger.info(f"Processing forum: {forum.name}")
        
        try:
            # Get appropriate parser
            parser = get_parser_for_forum(forum.name)
            
            # Create crawler and process forum
            with ForumCrawler(session, parser, rate_limit=rate_limit) as crawler:
                stats = crawler.crawl_forum(forum, keywords)
                results[forum.name] = stats
                
        except Exception as e:
            logger.error(f"Failed to crawl forum '{forum.name}': {str(e)}")
            results[forum.name] = {
                'matches_found': 0,
                'pages_crawled': 0,
                'errors': 1
            }
    
    return results


def print_summary(results: Dict[str, Dict]):
    """Print summary of crawl results."""
    print("\n" + "="*60)
    print("CRAWL SUMMARY")
    print("="*60)
    
    total_matches = 0
    total_pages = 0
    total_errors = 0
    
    for forum_name, stats in results.items():
        print(f"\n{forum_name}:")
        print(f"  Matches found: {stats['matches_found']}")
        print(f"  Pages crawled: {stats['pages_crawled']}")
        print(f"  Errors: {stats['errors']}")
        
        total_matches += stats['matches_found']
        total_pages += stats['pages_crawled']
        total_errors += stats['errors']
    
    print("\n" + "-"*60)
    print("TOTALS:")
    print(f"  Total matches: {total_matches}")
    print(f"  Total pages: {total_pages}")
    print(f"  Total errors: {total_errors}")
    print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Forum crawler for keyword monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database tables'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=2.0,
        help='Minimum seconds between requests (default: 2.0)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            sys.exit(1)
        return
    
    # Run crawler
    try:
        SessionMaker = get_session_maker()
        session = SessionMaker()
        
        results = crawl_all_forums(session, rate_limit=args.rate_limit)
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
