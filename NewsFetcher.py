import requests
import os
from MITTechReviewScraper import MITTechReviewScraper

class NewsFetcher:
    def __init__(self):
        self.source = "techcrunch"
        self.language = "en"
        self.api_key = os.environ['NEWS_API_KEY']

    def fetch(self):
        """
        Makes an API call to NewsAPI to fetch news articles from the specified source and language.
        Returns the news data in a structured format.
        """
        url = f"https://newsapi.org/v2/top-headlines?sources={self.source}&language={self.language}&apiKey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            news_api_articles = response.json()
        else:
            return {"error": "Failed to fetch news", "status_code": response.status_code}

        mit_scraper = MITTechReviewScraper()
        mit_articles = mit_scraper.get_latest_news()
        combined_articles = mit_articles + news_api_articles['articles']
        return combined_articles
    
