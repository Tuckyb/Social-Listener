from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseScraper(ABC):
    def __init__(self):
        self.rate_limit_delay = 1.0  # Default delay between requests in seconds
        self.last_request_time = datetime.min

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        Validate if the URL is in the correct format for this scraper
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pass

    @abstractmethod
    async def get_comments(self, url: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get comments from the given URL
        
        Args:
            url (str): URL to get comments from
            limit (int, optional): Maximum number of comments to retrieve. Defaults to 100.
            
        Returns:
            List[Dict[str, Any]]: List of comments with their metadata
        """
        pass
