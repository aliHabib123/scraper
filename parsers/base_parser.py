from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class BaseParser(ABC):
    """Abstract base class for forum-specific parsers."""
    
    @abstractmethod
    def get_paginated_url(self, base_url: str, page_num: int) -> str:
        """
        Generate paginated URL for a given page number.
        
        Args:
            base_url: Base URL of the category/search page
            page_num: Page number (1-indexed)
            
        Returns:
            Full paginated URL
        """
        pass
    
    @abstractmethod
    def extract_thread_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract thread URLs from a category/search page.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute thread URLs
        """
        pass
    
    @abstractmethod
    def extract_thread_content(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """
        Extract thread title and first post content.
        
        Args:
            soup: BeautifulSoup object of the thread page
            
        Returns:
            Dict with 'title' and 'content' keys, or None if extraction fails
        """
        pass
    
    def extract_all_posts(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all posts from a thread (title + all post contents).
        Default implementation extracts just the first post.
        Override in subclass for better coverage.
        
        Args:
            soup: BeautifulSoup object of the thread page
            
        Returns:
            List of dicts with 'content' and optional 'author', 'post_number' keys
        """
        # Default: just return first post
        thread_data = self.extract_thread_content(soup)
        if thread_data:
            return [{
                'content': f"{thread_data['title']} {thread_data['content']}",
                'post_number': 1
            }]
        return []
