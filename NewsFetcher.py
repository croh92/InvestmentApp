import requests
import os
from openai import OpenAI
from datetime import datetime
from MITTechReviewScraper import MITTechReviewScraper
from DocumentEncoder import DocumentEncoder
from llama_index import GPTIndex, Document
import chromadb

class NewsFetcher:
    def __init__(self):
        self.source = "techcrunch"
        self.language = "en"
        self.news_api_key = os.environ['NEWS_API_KEY']

    # Fetches news articles from News API and MIT Technology Review
    def fetch_news(self):
        url = f"https://newsapi.org/v2/top-headlines?sources={self.source}&language={self.language}&apiKey={self.news_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            news_api_articles = response.json()['articles']
        else:
            return {"error": "Failed to fetch news", "status_code": response.status_code}

        mit_scraper = MITTechReviewScraper()
        mit_articles = mit_scraper.get_latest_news()
        breakpoint()

        combined_articles = []
        for article in news_api_articles:
            article['source'] = article['source']['id'] if article['source']['id'] else article['source']['name']
            article['timestamp'] = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
            combined_articles.append(article)

        for article in mit_articles:
            article['source'] = 'MIT Technology Review'
            article['timestamp'] = datetime.strptime(article['publishedAt'], "%a, %d %b %Y %H:%M:%S %z")
            combined_articles.append(article)
        
        return combined_articles
    
    # Filters the news articles based on whether they are related to disruptive technologies
    def filter_news(self, news):
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
    
    # Saves the news into a vector DB to generate insights off of it later
    def save_news(news):
        client = chromadb.Client()
        document_encoder = DocumentEncoder()
        collection = client.create_collection(name="news_articles")

        # Prepare documents for indexing with timestamps
        documents = [
            {
                "id": str(i),
                "text": article['description'],
                "source": article['source'],
                "timestamp": article['timestamp']
            }
            for i, article in enumerate(news)
        ]

        # Encode and store documents in Chroma
        for doc in documents:
            embedding = document_encoder.encode(doc["text"])
            metadata = {"source": doc["source"], "timestamp": doc["timestamp"].isoformat()}
            collection.insert(embedding, doc_id=doc["id"], metadata=metadata)

        # Initialize LlamaIndex
        index = GPTIndex(vector_store=collection)

        # Add documents to LlamaIndex
        for doc in documents:
            document = Document(doc_id=doc["id"], text=doc["text"], metadata={"source": doc["source"], "timestamp": doc["timestamp"].isoformat()})
            index.add(document)

    
if __name__ == "__main__":
    fetcher = NewsFetcher()
    news = fetcher.fetch_news()
    filtered_news = fetcher.filter_news(news)
    breakpoint()
