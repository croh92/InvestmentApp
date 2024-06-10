import os
import googleapiclient.discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from youtube_transcript_api import YouTubeTranscriptApi

class YoutubeVideoFetcher:
    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self.API_SERVICE_NAME = "youtube"
        self.API_VERSION = "v3"
        self.CLIENT_SECRETS_FILE = "client_secret.json"
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
        self.youtube = self.get_authenticated_service()

    def get_authenticated_service(self):
        flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRETS_FILE, self.SCOPES)
        credentials = flow.run_local_server(port=0)
        return googleapiclient.discovery.build(self.API_SERVICE_NAME, self.API_VERSION, credentials=credentials)

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

    def fetch_transcript(self, video_id):
        try:
            # Get list of captions for the video
            captions = self.youtube.captions().list(
                part="snippet",
                videoId=video_id
            ).execute()

            for item in captions['items']:
                caption_id = item['id']
                name = item['snippet']['name']
                language = item['snippet']['language']
                print(f"Caption ID: {caption_id}, Name: {name}, Language: {language}")

                # Download the caption
                if language == 'en':
                    caption = self.youtube.captions().download(
                        id=caption_id,
                        tfmt="srt"
                    ).execute()
                    return caption.decode('utf-8')

            return "No English captions available."
        except Exception as e:
            print(f"ERROR: {e}")
        
    def fetch_videos_from_channels(self, channel_ids, query, max_results=10):
        all_videos = []
        for channel_id in channel_ids:
            print(f"Fetching videos from channel ID: {channel_id}")
            videos = self.search_videos_by_channel(channel_id, query, max_results)
            all_videos.extend(videos)
        return all_videos
    
if __name__ == "__main__":
    fetcher = YoutubeVideoFetcher()
    videos = fetcher.fetch_videos_by_channel("UC7kCeZ53sli_9XwuQeFxLqw")
    breakpoint()
    captions = fetcher.fetch_transcript('3JZ_D3ELwOQ')
    