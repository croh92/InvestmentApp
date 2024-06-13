import requests
import os

import requests

class PodcastFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://listen-api.listennotes.com/api/v2"

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

    def search_podcasts(self, query, type='episode'):
        headers = {
            'X-ListenAPI-Key': self.api_key
        }
        params = {
            'q': query,
            'type': type
        }
        url = f"{self.base_url}/search"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            search_results = response.json()
            return search_results.get('results', [])
        else:
            response.raise_for_status()

# Example usage
if __name__ == "__main__":
    api_key = "YOUR_LISTEN_NOTES_API_KEY"
    fetcher = PodcastFetcher(api_key)

    # Search for a podcast episode
    search_query = "technology"
    episodes = fetcher.search_podcasts(search_query)
    if episodes:
        first_episode_id = episodes[0]['id']
        
        # Fetch transcript for the first episode found
        transcript = fetcher.get_episode_transcript(first_episode_id)
        print(transcript)
    else:
        print("No episodes found.")