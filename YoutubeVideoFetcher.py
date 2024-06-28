import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import json
import hashlib
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

class YoutubeVideoFetcher:
    def __init__(self):
        self.youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_client = OpenAI(
            api_key=self.openai_api_key,
        )
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        self.youtube_channels = [
            "UC7kCeZ53sli_9XwuQeFxLqw", # Ticker Symbol: You
            "UCqoSrYgusd8ZddtMoWhjHYA", # Charles Schwabb
            "UCrM7B7SL_g1edFOnmj-SDKg", # Bloomberg Technology
        ]

        # Initialize Chroma
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "youtube_videos"
        self.chroma_collection = self.chroma_client.get_or_create_collection(name=self.collection_name)

    # Fetches videos from a specified youtube channel
    def fetch_videos_by_channel(self, channel_id, max_results=20):
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video"
        ) 
        response = request.execute()

        videos = []
        for item in response['items']:
            video = {
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'publishedAt': item['snippet']['publishedAt'],
                'channelTitle': item['snippet']['channelTitle']
            }
            videos.append(video)
        return videos
    
    def fetch_videos_from_channels(self, channel_ids, query, max_results=10):
        all_videos = []
        for channel_id in channel_ids:
            print(f"Fetching videos from channel ID: {channel_id}")
            videos = self.search_videos_by_channel(channel_id, query, max_results)
            all_videos.extend(videos)
        return all_videos

    def fetch_transcript(self, video_id):
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Convert the transcript to a single line
        single_line_transcript = ' '.join([entry['text'] for entry in transcript])
        return single_line_transcript
    
    # Checks if the youtube video is disruptive technology related or not to determine whether to add into the vector DB
    def is_disruptive_technology(self, title, description):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Title: {title}\nDescription: {description}\n\nQuestion: Is this video related to disruptive technologies such as artificial intelligence, blockchain, IoT, autonomous vehicles, quantum computing, or other similar technologies? Answer with yes or no."}
        ]

        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=10,
            n=1,
            stop=None,
            temperature=0.5,
        )

        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"

    # Filters the videos based on whether they are related to disruptive technologies
    def filter_videos(self, videos):
        filtered_videos = []

        for video in videos:
            title = video["title"]
            description = video["description"]

            # Combine title and description to create a unique identifier
            content = f"{title}|{description}"
            video_id = hashlib.md5(content.encode()).hexdigest()

            # Check if the article already exists in the collection by querying the title
            existing_docs = self.chroma_collection.get(
                where={"id": video_id}
            )
            
            # If it already exists, don't query Open AI. Just skip to the next article.
            if existing_docs['documents']:
                print(f"Video already exists: {video['title']}")
                continue  # Skip this article since it already exists

            # Only use Open AI to check if the video is related to disruptive technologies if it doesnt already exist in vector DB. Saves $$.
            if self.is_disruptive_technology(title, description):
                filtered_videos.append(video)

        return filtered_videos
    
    # Saves videos into the vector DB for future processing
    def save_videos(self, videos):
        # Initialize Chroma client
        chroma_client = self.chroma_client
        
        # Get the collection
        chroma_collection = chroma_client.get_or_create_collection(name=self.collection_name)

        # Create Chroma vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Initialize the embedding model
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Create documents from videos
        new_documents = []
        skipped_count = 0
        
        for video in videos:
            title = video['title']
            description = video['description']
            youtube_id = video['id']

            # Combine title and description to create a unique identifier
            unique_content = f"{title}|{description}"
            video_id = hashlib.md5(unique_content.encode()).hexdigest()
            
            # Check if the video already exists in the collection
            existing_docs = chroma_collection.get(
                where={"id": video_id}
            )

            if not existing_docs['documents']:  # If the video doesn't exist
                # Fetch and convert transcript
                try:
                    transcript = self.fetch_transcript(youtube_id)
                except Exception as e:
                    print(f"Failed to fetch transcript for video {youtube_id}: {str(e)}")
                    transcript = "Transcript unavailable"

                doc_text = f"Title: {title}\nDescription: {description}\nChannel: {video['channelTitle']}\nPublished At: {video['publishedAt']}\nTranscript: {transcript}"
                doc_metadata = {
                    "id": video_id,
                    "title": title,
                    "channel": video['channelTitle'],
                    "published_at": video['publishedAt'],
                    "youtube_id": youtube_id
                }
                new_documents.append(Document(doc_id=video_id, text=doc_text, metadata=doc_metadata))
            else:
                skipped_count+=1
                print(f"Duplicate video exists with title: {title}")

        if new_documents:
            # Initialize LlamaIndex with only new documents
            index = VectorStoreIndex.from_documents(
                new_documents,
                storage_context=storage_context,
                embed_model=embed_model
            )

            # Persist the index
            index.storage_context.persist()

            print(f"Added {len(new_documents)} new videos to the index.")

        print(f"Skipped {skipped_count} videos that already exist in the index.")
        return None
    
    # Fetch videos from all channels and save them to the vector DB
    def fetch_and_save_all_channels(self):
        for channel_id in self.youtube_channels:
            print(f"Processing channel: {channel_id}")
            videos = self.fetch_videos_by_channel(channel_id)
            filtered_videos = self.filter_videos(videos)
            self.save_videos(filtered_videos)
    
if __name__ == "__main__":
    fetcher = YoutubeVideoFetcher()
    videos = fetcher.fetch_videos_by_channel("UCrM7B7SL_g1edFOnmj-SDKg")
    schwabb_videos = fetcher.fetch_videos_by_channel("UCqoSrYgusd8ZddtMoWhjHYA")
    transcript = fetcher.fetch_transcript('w7VcuCOH2to')
    filtered_videos = fetcher.filter_videos(videos)
    fetcher.fetch_and_save_all_channels()

    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="youtube_videos")

    # Get the count of items in the collection
    print(f"Number of items in collection: {collection.count()}")

    # Retrieve a few items
    results = collection.peek(limit=20)

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
    