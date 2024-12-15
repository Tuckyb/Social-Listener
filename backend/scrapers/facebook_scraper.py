from typing import Dict, Any, List
import re
from datetime import datetime
from .base_scraper import BaseScraper
import asyncio
import requests
from bs4 import BeautifulSoup
import json

class FacebookScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def validate_url(self, url: str) -> bool:
        patterns = [
            r'^https?://(?:www\.)?facebook\.com/[\w.]+/posts/\d+',
            r'^https?://(?:www\.)?facebook\.com/[\w.]+/photos/[\w.]+',
            r'^https?://(?:www\.)?facebook\.com/permalink\.php\?story_fbid=\d+&id=\d+'
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    async def get_post_data(self, url: str) -> Dict[str, Any]:
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        post_data = {}
        
        try:
            # Try to find the post content
            post_content = soup.find('div', {'data-testid': 'post_message'})
            if post_content:
                post_data['text'] = post_content.get_text(strip=True)
            
            # Try to find author
            author = soup.find('h2', {'class': 'actor'})
            if author:
                post_data['author'] = author.get_text(strip=True)
            
            # Try to find timestamp
            timestamp = soup.find('abbr', {'class': 'timestamp'})
            if timestamp:
                post_data['timestamp'] = timestamp.get('title')
            
            # Try to find reactions
            reactions = soup.find('span', {'class': '_3dlh'})
            if reactions:
                post_data['reactions'] = reactions.get_text(strip=True)
                
        except Exception as e:
            print(f"Error extracting Facebook post data: {str(e)}")
        
        return post_data

    async def get_comments(self, url: str) -> List[Dict[str, Any]]:
        comments = []
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find comments
            comment_elements = soup.find_all('div', {'class': 'UFIComment'})
            
            for comment in comment_elements:
                try:
                    comment_text = comment.find('span', {'class': 'UFICommentBody'})
                    comment_author = comment.find('a', {'class': 'UFICommentActorName'})
                    comment_time = comment.find('abbr')
                    comment_likes = comment.find('span', {'class': 'UFILikeSentence'})
                    
                    formatted_comment = self.format_comment({
                        "id": comment.get('id', ''),
                        "text": comment_text.get_text(strip=True) if comment_text else '',
                        "author": comment_author.get_text(strip=True) if comment_author else '',
                        "timestamp": comment_time.get('title') if comment_time else '',
                        "likes": comment_likes.get_text(strip=True) if comment_likes else '0',
                        "replies": []
                    })
                    comments.append(formatted_comment)
                    await asyncio.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    print(f"Error processing Facebook comment: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching Facebook comments: {str(e)}")
            
        return comments

    async def scrape(self, url: str) -> Dict[str, Any]:
        if not self.validate_url(url):
            raise ValueError("Invalid Facebook URL")
        
        try:
            # Get post data
            post_data = await self.get_post_data(url)
            
            # Get comments
            comments = await self.get_comments(url)
            
            return {
                "title": post_data.get('text', '')[:100] + '...' if len(post_data.get('text', '')) > 100 else post_data.get('text', ''),
                "author": post_data.get('author', ''),
                "publish_date": post_data.get('timestamp', ''),
                "likes": post_data.get('reactions', '0'),
                "description": post_data.get('text', ''),
                "comments": comments,
                "comment_count": len(comments),
                "platform": "facebook",
                "url": url,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error scraping Facebook post: {str(e)}")
