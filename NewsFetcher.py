import requests
import os
from openai import OpenAI
from datetime import datetime
from MITTechReviewScraper import MITTechReviewScraper
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
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
    def save_news(self, news):
        # Initialize Chroma client
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Create or get the collection
        collection_name = "news_articles"
        chroma_collection = chroma_client.get_or_create_collection(name=collection_name)

        # Create Chroma vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Initialize the embedding model
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Create documents from news articles
        documents = []
        for i, article in enumerate(news):
            doc_text = f"Title: {article['title']}\nDescription: {article['description']}\nContent: {article['content']}"
            doc_metadata = {
                "source": article['source'],
                "timestamp": article['timestamp'].isoformat(),
                "url": article['url']
            }
            documents.append(Document(text=doc_text, metadata=doc_metadata))

        # Initialize LlamaIndex
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model
        )

        # Persist the index
        index.storage_context.persist()

        return index

    
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
    results = collection.peek(limit=5)

    # Use the same embedding model as when you saved the data
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load the existing index
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = chroma_client.get_collection("news_articles")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    # Create a query engine
    query_engine = index.as_query_engine()

    # Perform a test query
    response = query_engine.query("What are some recent developments in AI?")
    print(response)
    print(f"Sample items: {results}")
    breakpoint()
