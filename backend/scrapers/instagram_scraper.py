from typing import Dict, Any, List
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import asyncio
import json

class InstagramScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def validate_url(self, url: str) -> bool:
        patterns = [
            r'^https?://(?:www\.)?instagram\.com/p/[\w-]+/?',
            r'^https?://(?:www\.)?instagram\.com/reel/[\w-]+/?'
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    def extract_shortcode(self, url: str) -> str:
        match = re.search(r'/(p|reel)/([\w-]+)', url)
        if not match:
            raise ValueError("Invalid Instagram URL")
        return match.group(2)

    async def get_post_data(self, shortcode: str) -> Dict[str, Any]:
        url = f"https://www.instagram.com/p/{shortcode}/"
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the shared data script
        for script in soup.find_all('script'):
            if 'window._sharedData' in str(script):
                data_str = str(script).split('window._sharedData = ')[1].split(';</script>')[0]
                data = json.loads(data_str)
                
                # Extract post data
                post_data = data.get('entry_data', {}).get('PostPage', [{}])[0].get('graphql', {}).get('shortcode_media', {})
                return post_data
                
        return {}

    async def get_post_comments(self, shortcode: str) -> List[Dict[str, Any]]:
        comments = []
        try:
            post_data = await self.get_post_data(shortcode)
            
            # Extract comments from post data
            edges = post_data.get('edge_media_to_comment', {}).get('edges', [])
            for edge in edges:
                node = edge.get('node', {})
                formatted_comment = self.format_comment({
                    "id": node.get('id', ''),
                    "text": node.get('text', ''),
                    "author": node.get('owner', {}).get('username', ''),
                    "timestamp": datetime.fromtimestamp(node.get('created_at', 0)).isoformat(),
                    "likes": node.get('edge_liked_by', {}).get('count', 0),
                    "replies": []
                })
                comments.append(formatted_comment)
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            print(f"Error fetching Instagram comments: {str(e)}")
            
        return comments

    async def scrape(self, url: str) -> Dict[str, Any]:
        if not self.validate_url(url):
            raise ValueError("Invalid Instagram URL")

        shortcode = self.extract_shortcode(url)
        
        try:
            post_data = await self.get_post_data(shortcode)
            comments = await self.get_post_comments(shortcode)
            
            owner = post_data.get('owner', {})
            
            return {
                "title": post_data.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                "author": owner.get('username', ''),
                "publish_date": datetime.fromtimestamp(post_data.get('taken_at_timestamp', 0)).isoformat(),
                "likes": post_data.get('edge_media_preview_like', {}).get('count', 0),
                "description": post_data.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                "comments": comments,
                "comment_count": len(comments),
                "platform": "instagram",
                "url": url,
                "is_video": post_data.get('is_video', False),
                "location": post_data.get('location', {}).get('name', None),
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error scraping Instagram post: {str(e)}")
