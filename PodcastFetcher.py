import requests
import os

class PodcastFetcher:
    def __init__(self):
        self.base_url = "https://itunes.apple.com"

    def get_podcast_episodes(self, podcast_id):
        url = f"{self.base_url}/lookup"
        params = {
            'id': podcast_id,
            'entity': 'podcastEpisode',
            'limit': 20  # Adjust limit as needed
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and data['resultCount'] > 0:
                # Return all results except the first one, which is the podcast info
                return data['results'][1:] if data['resultCount'] > 1 else []
            else:
                return []
        else:
            print(f"Error: {response.status_code}")
            return []

    def download_episode(self, episode):
        episode_url = episode.get('episodeUrl')
        if episode_url:
            # Construct the filename using the episode's title
            title = episode.get('trackName', 'Unknown Episode')
            filename = f"{title}.mp3".replace("/", "-")  # Replace slashes to avoid file path issues

            response = requests.get(episode_url, allow_redirects=True)
            final_url = response.url
            
            # Verify the content type of the final URL
            head_response = requests.head(final_url)
            content_type = head_response.headers.get('Content-Type', '')

            if head_response.status_code == 200 and 'audio/mpeg' in content_type:
                response = requests.get(final_url, stream=True)
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                print(f"Downloaded {filename}")
            else:
                print(f"Failed to download {filename}. Content type: {content_type}")
        else:
            print(f"Episode URL not found in episode metadata.")

# Example usage
if __name__ == "__main__":
    fetcher = PodcastFetcher()
    podcast_id = "1502871393"

    # Fetch episodes for the podcast
    episodes = fetcher.get_podcast_episodes(podcast_id)
    breakpoint()
    if episodes:
        for episode in episodes:
            fetcher.download_episode(episode)
    else:
        print("No episodes found or access is restricted.")