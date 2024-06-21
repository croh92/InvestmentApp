import requests
import os
from MITTechReviewScraper import MITTechReviewScraper

class NewsFetcher:
    def __init__(self):
        self.source = "techcrunch"
        self.language = "en"
        self.news_api_key = os.environ['NEWS_API_KEY']

    def fetch_news(self):
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
    
    def filter_news(self, news):
        """
        Filters the news articles based on the presence of specified AI-related keywords.
        Returns a list of news articles that contain any of the specified keywords.
        """
        openai_client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPEN_API_KEY"),
        )
        filtered_articles = []

        for article in news:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Is the following article related to disruptive technologies? Example disruptive technologies include but are not limited to artificial intelligence, blockchain, IoT, autonomous vehicles, and quantum computing. Answer with yes or no.\n\n{article}"}
            ]
    
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1500,
                n=1,
                stop=None,
                temperature=0.7,
            )
        
            if "yes" in response.choices[0].message.content.lower():
                filtered_articles.append(article)
            
        return filtered_articles
    
