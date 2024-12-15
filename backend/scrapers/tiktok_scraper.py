from typing import Dict, Any, List
import re
from datetime import datetime
from .base_scraper import BaseScraper
import asyncio
import requests
from bs4 import BeautifulSoup
import json

class TikTokScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def validate_url(self, url: str) -> bool:
        patterns = [
            r'^https?://(?:www\.)?tiktok\.com/@[\w.]+/video/\d+',
            r'^https?://(?:www\.)?vm\.tiktok\.com/[\w]+',
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    async def get_video_data(self, url: str) -> Dict[str, Any]:
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the SIGI_STATE script
        for script in soup.find_all('script', {'id': 'SIGI_STATE'}):
            try:
                data = json.loads(script.string)
                return data
            except:
                continue
                
        return {}

    async def get_comments(self, video_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        comments = []
        try:
            # Extract comments from video data
            items_list = video_data.get('ItemModule', {})
            if items_list:
                video_item = next(iter(items_list.values()))
                comment_data = video_data.get('CommentModule', {}).get(video_item.get('id', ''), {})
                
                for comment in comment_data.get('comments', []):
                    formatted_comment = self.format_comment({
                        "id": comment.get('cid', ''),
                        "text": comment.get('text', ''),
                        "author": comment.get('user', {}).get('unique_id', ''),
                        "timestamp": datetime.fromtimestamp(comment.get('create_time', 0)).isoformat(),
                        "likes": comment.get('digg_count', 0),
                        "replies": []
                    })
                    comments.append(formatted_comment)
                    await asyncio.sleep(self.rate_limit_delay)
                    
        except Exception as e:
            print(f"Error fetching TikTok comments: {str(e)}")
            
        return comments

    async def scrape(self, url: str) -> Dict[str, Any]:
        if not self.validate_url(url):
            raise ValueError("Invalid TikTok URL")
        
        try:
            # Get video data
            video_data = await self.get_video_data(url)
            
            # Get video details
            items_list = video_data.get('ItemModule', {})
            if not items_list:
                raise ValueError("Could not find video data")
                
            video_item = next(iter(items_list.values()))
            
            # Get comments
            comments = await self.get_comments(video_data)
            
            return {
                "title": video_item.get('desc', ''),
                "author": video_item.get('author', {}).get('unique_id', ''),
                "publish_date": datetime.fromtimestamp(video_item.get('createTime', 0)).isoformat(),
                "likes": video_item.get('stats', {}).get('diggCount', 0),
                "shares": video_item.get('stats', {}).get('shareCount', 0),
                "plays": video_item.get('stats', {}).get('playCount', 0),
                "description": video_item.get('desc', ''),
                "comments": comments,
                "comment_count": len(comments),
                "platform": "tiktok",
                "url": url,
                "music": video_item.get('music', {}).get('title', ''),
                "duration": video_item.get('video', {}).get('duration', 0),
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error scraping TikTok video: {str(e)}")
