#!/usr/bin/env python3
"""
Telegram notification module for sending match alerts.
"""

import os
import logging
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications to Telegram."""
    
    def __init__(self):
        """Initialize with credentials from environment."""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        self.notify_only_on_matches = os.getenv('NOTIFY_ONLY_ON_MATCHES', 'false').lower() == 'true'
        
        if not self.enabled:
            logger.warning("Telegram notifications disabled - missing credentials")
    
    def send_message(self, text: str, parse_mode: str = 'HTML', disable_preview: bool = True) -> bool:
        """
        Send a message to Telegram.
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'
            disable_preview: Disable link previews
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Telegram not configured, skipping notification")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_preview
        }
        
        try:
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False
    
    def notify_matches(self, forum_name: str, matches: List[dict]) -> bool:
        """
        Send notification about new matches found.
        
        Args:
            forum_name: Name of the forum
            matches: List of match dicts with keys: keyword, url, snippet
            
        Returns:
            True if sent successfully
        """
        if not matches:
            return False
        
        # Build message
        message = f"⚠️⚠️⚠️⚠️ <b>New Matches Found</b>\n\n"
        message += f"<b>Forum:</b> {forum_name}\n"
        message += f"<b>Matches:</b> {len(matches)}\n\n"
        
        # Add each match
        for i, match in enumerate(matches, 1):
            keyword = match.get('keyword', 'unknown')
            url = match.get('url', '')
            snippet = match.get('snippet', '')[:100]  # Truncate
            
            message += f"{i}. <b>{keyword}</b>\n"
            message += f"   <a href=\"{url}\">View Thread</a>\n"
            message += f"   <i>{snippet}...</i>\n\n"
        
        return self.send_message(message)
    
    def notify_forum_results(self, forum_name: str, stats: dict, matches: List[dict] = None) -> bool:
        """
        Send consolidated forum crawl results notification.
        
        Args:
            forum_name: Name of the forum
            stats: Dict with keys: matches_found, pages_crawled, errors
            matches: Optional list of match dicts with keys: keyword, url, snippet
            
        Returns:
            True if sent successfully
        """
        pages = stats.get('pages_crawled', 0)
        matches_count = stats.get('matches_found', 0)
        errors = stats.get('errors', 0)
        
        # Skip notification if no matches and NOTIFY_ONLY_ON_MATCHES is enabled
        if matches_count == 0 and self.notify_only_on_matches:
            logger.info(f"Skipping notification for {forum_name} - no matches found (NOTIFY_ONLY_ON_MATCHES=true)")
            return False
        
        # Build header
        if matches_count > 0:
            message = f"⚠️⚠️⚠️⚠️ <b>Crawl Complete - {matches_count} Match{'es' if matches_count > 1 else ''} Found</b>\n\n"
        else:
            message = f"✅ <b>Crawl Complete - No Matches</b>\n\n"
        
        message += f"<b>Forum:</b> {forum_name}\n"
        message += f"<b>Pages Crawled:</b> {pages}\n"
        
        if errors > 0:
            message += f"⚠️ <b>Errors:</b> {errors}\n"
        
        # Add match details if any
        if matches and matches_count > 0:
            message += f"\n<b>─────────────────</b>\n"
            message += f"<b>📋 Match Details:</b>\n\n"
            
            for match in matches:
                keyword = match.get('keyword', 'unknown')
                url = match.get('url', '')
                snippet = match.get('snippet', '')[:150]  # Truncate to 150 chars
                
                message += f"<b>Keyword:</b> {keyword}\n"
                message += f"   <a href=\"{url}\">View Thread</a>\n"
                if snippet:
                    message += f"   <i>{snippet}...</i>\n"
                message += f"\n"
        
        return self.send_message(message)
    
    def notify_crawl_summary(self, forum_name: str, stats: dict) -> bool:
        """
        Send crawl summary notification (DEPRECATED - use notify_forum_results).
        
        Args:
            forum_name: Name of the forum
            stats: Dict with keys: matches_found, pages_crawled, errors
            
        Returns:
            True if sent successfully
        """
        return self.notify_forum_results(forum_name, stats)
    
    def test_connection(self) -> bool:
        """Test Telegram connection."""
        if not self.enabled:
            print("❌ Telegram not configured")
            print("\nSet these environment variables:")
            print("  TELEGRAM_BOT_TOKEN=<your_bot_token>")
            print("  TELEGRAM_CHAT_ID=<your_chat_id>")
            return False
        
        message = "✅ Test notification from Forum Crawler"
        success = self.send_message(message)
        
        if success:
            print("✅ Telegram notification sent successfully!")
        else:
            print("❌ Failed to send Telegram notification")
        
        return success
