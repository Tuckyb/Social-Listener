from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
import logging

from scrapers.youtube_scraper import YouTubeScraper
from analysis.cognitive_analyzer import MarketingInsightAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    platform: str
    export_format: Optional[str] = None

@app.get("/")
async def read_root():
    return {"message": "Welcome to Social Media Marketing Insights Tool"}

@app.post("/scrape")
async def scrape_comments(request: ScrapeRequest):
    try:
        logger.info(f"Received request for URL: {request.url}, Platform: {request.platform}")
        
        # Initialize only the requested scraper
        if request.platform == 'youtube':
            scraper = YouTubeScraper()
        else:
            raise HTTPException(status_code=400, detail=f"Platform {request.platform} is not supported yet")
        
        # Validate URL
        if not await scraper.validate_url(request.url):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Get comments using the scraper
        logger.info("Starting comment scraping...")
        result = await scraper.scrape(request.url)
        
        # Check for error in result
        if isinstance(result, dict) and "error" in result:
            logger.error(f"Scraping error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
            
        if not result or not isinstance(result, dict) or "comments" not in result:
            logger.error(f"Invalid scraper result format: {result}")
            raise HTTPException(status_code=500, detail="Invalid response from scraper")
            
        if not result["comments"]:
            logger.warning("No comments found")
            return {
                "success": True,
                "comments": [],
                "think": [],
                "feel": [],
                "act": [],
                "pain_points": [],
                "future_topics": [],
                "language_patterns": [],
                "sentiment": {"positive": [], "negative": []},
                "metadata": {
                    "total_comments": 0,
                    "analyzed_at": datetime.now().isoformat()
                }
            }
        
        # Initialize the analyzer
        analyzer = MarketingInsightAnalyzer()
        
        # Analyze comments
        logger.info(f"Analyzing {len(result['comments'])} comments...")
        analysis = analyzer.analyze_comments(result["comments"])
        
        # Prepare response
        response = {
            "success": True,
            "comments": result["comments"],
            "think": analysis.get("think", []),
            "feel": analysis.get("feel", []),
            "act": analysis.get("act", []),
            "pain_points": analysis.get("pain_points", []),
            "future_topics": analysis.get("future_topics", []),
            "language_patterns": analysis.get("language_patterns", []),
            "sentiment": {
                "positive": analysis.get("sentiment", {}).get("positive", []),
                "negative": analysis.get("sentiment", {}).get("negative", [])
            },
            "metadata": {
                "total_comments": len(result["comments"]),
                "analyzed_at": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Successfully analyzed {len(result['comments'])} comments")
        return response
        
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
