import requests
import os
from openai import OpenAI

class PodcastFetcher:
    def __init__(self):
        self.base_url = "https://itunes.apple.com"
        self.api_key = os.environ.get("OPEN_API_KEY")

    # Gets all podcast episodes for a given podcast.
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
    
    # Determines if a podcast episode is related to disruptive technologies
    def is_disruptive_technology(self, title, description):
        openai_client = OpenAI(
            api_key=self.api_key,
        )

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Title: {title}\nDescription: {description}\n\nQuestion: Is this podcast episode related to disruptive technologies such as artificial intelligence, blockchain, IoT, autonomous vehicles, quantum computing, or other similar technologies? Answer with yes or no."}
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=10,
            n=1,
            stop=None,
            temperature=0.5,
        )

        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"

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
    
    def filter_and_download_episodes(self, podcast_id):
        episodes = self.get_podcast_episodes(podcast_id)
        if episodes:
            for episode in episodes:
                title = episode.get('trackName', 'Unknown Title')
                description = episode.get('description', '')
                if self.is_disruptive_technology(title, description):
                    audio_file_path = self.download_episode(episode)
        else:
            print("No episodes found or access is restricted.")

# Example usage
if __name__ == "__main__":
    fetcher = PodcastFetcher()
    podcast_id = "1502871393"

    # Fetch episodes for the podcast
    episodes = fetcher.filter_and_download_episodes(podcast_id)
    breakpoint();