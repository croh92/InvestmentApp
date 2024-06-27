import requests
import os
from openai import OpenAI
from datetime import datetime, timezone
from MITTechReviewScraper import MITTechReviewScraper
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
import hashlib

class NewsFetcher:
    def __init__(self):
        self.news_api_sources = [
        "techcrunch",
        "wired",
        "the-verge",
        "ars-technica",
        "recode",
        "engadget"
        "hacker-news",
        "techradar",
        "the-next-web",
        "bloomberg"
        ]
        self.language = "en"
        self.news_api_key = os.environ['NEWS_API_KEY']
        
        # Initialize Chroma
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "news_articles"
        self.chroma_collection = self.chroma_client.get_or_create_collection(name=self.collection_name)

    # Fetches news articles from News API and MIT Technology Review
    def fetch_news(self):
        news_api_url = f"https://newsapi.org/v2/everything"
        news_api_params = {
            "sources": ",".join(self.news_api_sources),
            "language": self.language,
            "q": "technology",
            "apiKey": self.news_api_key
        }
        response = requests.get(news_api_url, params=news_api_params)
        if response.status_code == 200:
            news_api_articles = response.json()['articles']
        else:
            return {"error": "Failed to fetch news", "status_code": response.status_code}

        mit_scraper = MITTechReviewScraper()
        mit_articles = mit_scraper.get_latest_news()

        combined_articles = []
        
        for article in news_api_articles:
            article['source'] = article['source']['id'] if article['source']['id'] else article['source']['name']
            try:
                article['timestamp'] = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                # If that fails, try parsing with the format that includes timezone offset
                article['timestamp'] = datetime.strptime(article['publishedAt'], "%Y-%m-%dT%H:%M:%S%z")
        
            # Ensure the timestamp is timezone-aware
            if article['timestamp'].tzinfo is None:
                article['timestamp'] = article['timestamp'].replace(tzinfo=timezone.utc)
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
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        filtered_articles = []

        for article in news:
            # Combine title and description to create a unique identifier
            content = f"{article['title']}|{article['description']}"
            article_id = hashlib.md5(content.encode()).hexdigest()

            # Check if the article already exists in the collection by querying the title
            existing_docs = self.chroma_collection.get(
                where={"id": article_id}
            )
            
            # If it already exists, don't query Open AI. Just skip to the next article.
            if existing_docs['documents']:
                print(f"Article already exists: {article['title']}")
                continue  # Skip this article since it already exists
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Is the following article related to disruptive technologies? Example disruptive technologies include but are not limited to artificial intelligence, blockchain, IoT, autonomous vehicles, and quantum computing. Answer with yes or no.\n\n{article}"}
            ]
    
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
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
    def save_news(self, news):
        # Initialize Chroma client
        chroma_client = self.chroma_client
        
        chroma_collection = chroma_client.get_or_create_collection(name=self.collection_name)

        # Create Chroma vector store
        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)

        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Initialize the embedding model
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Create documents from news articles
        new_documents = []
        
        for article in news:
            title = article['title']
            description = article['description']

            # Combine title and description to create a unique identifier
            unique_content = f"{title}|{description}"
            article_id = hashlib.md5(unique_content.encode()).hexdigest()
            
            # Check if the article already exists in the collection by querying the title
            existing_docs = chroma_collection.get(
                where={"id": article_id}
            )

            if not existing_docs['documents']:  # If the article doesn't exist
                doc_text = f"Title: {article['title']}\nDescription: {article['description']}\nContent: {article['content']}"
                doc_metadata = {
                    "id": article_id,
                    "title": article['title'],
                    "source": article['source'],
                    "timestamp": article['timestamp'].isoformat(),
                    "url": article['url']
                }
                new_documents.append(Document(doc_id=article_id, text=doc_text, metadata=doc_metadata))
            else:
                print(f"Duplicate article exists with title: {title}")

        if new_documents:
            # Initialize LlamaIndex with only new documents
            index = VectorStoreIndex.from_documents(
                new_documents,
                storage_context=storage_context,
                embed_model=embed_model
            )

            # Persist the index
            index.storage_context.persist()
            print(f"Added {len(new_documents)} new articles to the index.")

        return
        
if __name__ == "__main__":
    fetcher = NewsFetcher()
    news = fetcher.fetch_news()
    filtered_news = fetcher.filter_news(news)
    fetcher.save_news(filtered_news)

    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="news_articles")

    # Get the count of items in the collection
    print(f"Number of items in collection: {collection.count()}")

    # Retrieve a few items
    results = collection.peek(limit=36)

    # Use the same embedding model as when you saved the data
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load the existing index
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    # Create a query engine
    query_engine = index.as_query_engine(similarity_top_k=5)

    # Perform a test query
    response = query_engine.query("What are some recent developments in AI?")
    print(response)
    print(f"Sample items: {results}")
