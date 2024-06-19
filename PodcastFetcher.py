import requests
import os

import requests

class PodcastFetcher:
    def __init__(self):
        self.api_key = os.environ.get("LISTEN_NOTES_API_KEY")
        self.base_url = "https://listen-api.listennotes.com/api/v2"

    def get_podcast_episodes(self, podcast_id):
        headers = {
            "X-ListenAPI-Key": self.api_key
        }
        url = f"{self.base_url}/podcasts/{podcast_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data['episodes']
        else:
            print(f"Error: {response.status_code}. {response.text}")
            return None
    
    def get_episode_transcript(self, episode_id):
        headers = {
            'X-ListenAPI-Key': self.api_key
        }
        url = f"{self.base_url}/episodes/{episode_id}/transcripts"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            transcript_data = response.json()
            return transcript_data.get('results', [])
        else:
            response.raise_for_status()

    def get_episode_details(self, episode_id):
        headers = {
            'X-ListenAPI-Key': self.api_key
        }
        params = {
            'show_transcript': 1
        }
        url = f"{self.base_url}/episodes/{episode_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            episode_data = response.json()
            return episode_data
        else:
            print(f"Error: {response.status_code}. {response.text}")
            return None

# Example usage
if __name__ == "__main__":
    fetcher = PodcastFetcher()

    # Search for a podcast episode
    podcast_id = "0eWaLuirNTJ"
    breakpoint()
    episodes = fetcher.get_podcast_episodes(podcast_id)
    if episodes:
        first_episode_id = episodes[0]['id']
        
        # Fetch transcript for the first episode found
        transcript = fetcher.get_episode_transcript(first_episode_id)
        print(transcript)
    else:
        print("No episodes found.")