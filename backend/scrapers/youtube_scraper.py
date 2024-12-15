from typing import Dict, Any, List
import re
from datetime import datetime
import requests
import asyncio
import logging
from .base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.api_key = "AIzaSyCXhMQ0dgC1HZ5U-pXAYkoDWr3KbjnIX0E"
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def get_video_id(self, url: str) -> str:
        logger.info(f"Extracting video ID from URL: {url}")
        patterns = [
            r'(?:v=|\/videos\/|embed\/|youtu.be\/|\/v\/|\/e\/|watch\?v%3D|watch\?feature=player_embedded&v=|%2Fvideos%2F|embed%\u200C\u200B2F|youtu.be%2F|%2Fv%2F)([^#\&\?\n]*)',
            r'(?:v=|\/)([^#\&\?\n]*)',
            r'(?:v=|\/videos\/|embed\/|youtu.be\/|\/v\/|\/e\/|watch\?v%3D|watch\?feature=player_embedded&v=|%2Fvideos%2F|embed%\u200C\u200B2F|youtu.be%2F|%2Fv%2F)([^#\&\?\n]*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"Found video ID: {video_id}")
                return video_id
        raise ValueError("Invalid YouTube URL")

    async def fetch_comments_page(self, video_id: str, page_token: str = None) -> Dict[str, Any]:
        logger.info(f"Fetching comments for video ID: {video_id}, page token: {page_token}")
        params = {
            'key': self.api_key,
            'textFormat': 'plainText',
            'part': 'snippet,replies',
            'videoId': video_id,
            'maxResults': 100,  # Maximum allowed by YouTube API
            'order': 'relevance'
        }
        
        if page_token:
            params['pageToken'] = page_token
            
        try:
            response = requests.get(f'{self.base_url}/commentThreads', params=params)
            
            if response.status_code == 403:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'YouTube API quota exceeded')
                logger.error(f"YouTube API error: {error_message}")
                return {"error": f"YouTube API error: {error_message}"}
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Invalid request')
                logger.error(f"YouTube API error: {error_message}")
                return {"error": f"YouTube API error: {error_message}"}
            elif response.status_code != 200:
                logger.error(f"YouTube API error: {response.status_code}")
                return {"error": f"YouTube API error: HTTP {response.status_code}"}
                
            data = response.json()
            logger.info(f"Successfully fetched {len(data.get('items', []))} comments")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Failed to fetch comments: {str(e)}"}

    async def get_comments(self, url: str, limit: int = 1000) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.error("YouTube API key not set")
            return [{"error": "Please set up a YouTube API key first"}]

        try:
            video_id = await self.get_video_id(url)
            logger.info(f"Starting comment collection for video {video_id}")

            comments = []
            page_token = None
            total_api_calls = 0
            max_api_calls = (limit + 99) // 100  # Calculate how many API calls we need

            while total_api_calls < max_api_calls:
                response = await self.fetch_comments_page(video_id, page_token)
                
                if "error" in response:
                    logger.error(f"Error in response: {response['error']}")
                    return [{"error": response["error"]}]
                
                if 'items' not in response:
                    logger.error("No 'items' found in response")
                    return [{"error": "Invalid response from YouTube API"}]
                
                # Extract comments from response
                for item in response['items']:
                    try:
                        comment = {
                            'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                            'author': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            'likes': item['snippet']['topLevelComment']['snippet']['likeCount'],
                            'timestamp': item['snippet']['topLevelComment']['snippet']['publishedAt'],
                            'replies': []
                        }
                        
                        # Get replies if they exist
                        if item.get('replies'):
                            for reply in item['replies']['comments']:
                                comment['replies'].append({
                                    'text': reply['snippet']['textDisplay'],
                                    'author': reply['snippet']['authorDisplayName'],
                                    'likes': reply['snippet']['likeCount'],
                                    'timestamp': reply['snippet']['publishedAt']
                                })
                        
                        comments.append(comment)
                        
                        if len(comments) >= limit:
                            break
                    except KeyError as e:
                        logger.error(f"Failed to parse comment: {str(e)}")
                        continue

                if len(comments) >= limit or 'nextPageToken' not in response:
                    break
                    
                page_token = response['nextPageToken']
                total_api_calls += 1
                
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(0.1)

            logger.info(f"Successfully collected {len(comments)} comments")
            return comments

        except Exception as e:
            logger.error(f"Error collecting comments: {str(e)}")
            return [{"error": f"Failed to collect comments: {str(e)}"}]

    async def get_video_details(self, video_id: str) -> Dict[str, Any]:
        params = {
            'key': self.api_key,
            'part': 'snippet,statistics',
            'id': video_id
        }
        
        try:
            response = requests.get(f'{self.base_url}/videos', params=params)
            if response.status_code != 200:
                return {"error": f"YouTube API error: {response.status_code}"}
                
            data = response.json()
            if not data['items']:
                return {"error": "Video not found"}
                
            video = data['items'][0]
            return {
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'publishedAt': video['snippet']['publishedAt'],
                'viewCount': video['statistics']['viewCount'],
                'likeCount': video['statistics'].get('likeCount', 0),
                'commentCount': video['statistics'].get('commentCount', 0)
            }
        except Exception as e:
            return {"error": f"Failed to fetch video details: {str(e)}"}

    async def validate_url(self, url: str) -> bool:
        """Validate if the provided URL is a valid YouTube video URL."""
        try:
            video_id = await self.get_video_id(url)
            return bool(video_id)
        except ValueError:
            return False

    async def scrape(self, url: str) -> Dict[str, Any]:
        if not self.api_key:
            logger.error("YouTube API key not set")
            return {"error": "YouTube API key not set"}

        try:
            video_id = await self.get_video_id(url)
            logger.info(f"Got video ID: {video_id}")

            # Get comments first
            comments = await self.get_comments(url)
            if not comments:
                logger.error("No comments returned")
                return {"error": "No comments found"}
                
            if isinstance(comments, list) and comments and isinstance(comments[0], dict) and "error" in comments[0]:
                logger.error(f"Error in comments: {comments[0]['error']}")
                return {"error": comments[0]["error"]}

            # Get video details
            video_details = await self.get_video_details(video_id)
            if "error" in video_details:
                logger.error(f"Error getting video details: {video_details['error']}")
                return {"error": video_details["error"]}
            
            logger.info(f"Successfully scraped {len(comments)} comments")
            return {
                "title": video_details.get('title', ''),
                "author": video_details.get('channel', ''),
                "publish_date": video_details.get('publishedAt', ''),
                "views": video_details.get('viewCount', 0),
                "description": video_details.get('description', ''),
                "comments": comments,
                "comment_count": len(comments),
                "platform": "youtube",
                "url": url,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return {"error": f"Failed to scrape video: {str(e)}"}
