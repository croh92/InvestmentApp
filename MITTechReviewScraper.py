import requests
import feedparser

class MITTechReviewScraper():
    def __init__(self, rss_url="https://www.technologyreview.com/feed/"):
        self.rss_url = rss_url

    def get_latest_news(self):
        # Fetch the RSS feed content with requests, ignoring SSL verification
        response = requests.get(self.rss_url, verify=False)
        
        # Parse the RSS feed using feedparser
        feed = feedparser.parse(response.content)
        
        articles = []
        # Return in standard format
        for entry in feed.entries:
            article = {
                'source': {'id': 'mit-technology-review', 'name': 'MIT Technology Review'},
                'author': entry.get('author', ''),
                'title': entry.title,
                'description': entry.summary,
                'url': entry.link,
                'urlToImage': '',
                'publishedAt': entry.published,
                'content': entry.summary
            }
            articles.append(article)
        
        return articles