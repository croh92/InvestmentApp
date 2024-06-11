import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import json

class YoutubeVideoFetcher:
    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

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
        return transcript
    
    # Converts the transcript into a single string
    def convert_transcript(self, transcript):
        # Extract the 'text' values from each dictionary and join them into a single line
        single_line_text = ' '.join([entry['text'] for entry in transcript])

        return single_line_text


    
if __name__ == "__main__":
    fetcher = YoutubeVideoFetcher()
    videos = fetcher.fetch_videos_by_channel("UC7kCeZ53sli_9XwuQeFxLqw")
    breakpoint()
    captions = fetcher.fetch_transcript('GZd212F2Kmg')
    converted_transcript = fetcher.convert_transcript(captions)
    