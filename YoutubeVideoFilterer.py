import json
from openai import OpenAI
import os
from YoutubeVideoFetcher import YoutubeVideoFetcher

class YoutubeVideoFilterer:
    def __init__(self):
        self.api_key = os.environ.get("OPEN_API_KEY")

    def is_disruptive_technology(self, title, description):
        openai_client = OpenAI(
            api_key=os.environ.get("OPEN_API_KEY"),
        )

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Title: {title}\nDescription: {description}\n\nQuestion: Is this video related to disruptive technologies such as artificial intelligence, blockchain, IoT, autonomous vehicles, quantum computing, or other similar technologies? Answer with yes or no."}
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

    def filter_videos(self, videos):
        filtered_videos = []

        for video in videos:
            title = video["title"]
            description = video["description"]

            if self.is_disruptive_technology(title, description):
                filtered_videos.append(video)

        return filtered_videos

if __name__ == "__main__":
    fetcher = YoutubeVideoFetcher()
    videos = fetcher.fetch_videos_by_channel("UC7kCeZ53sli_9XwuQeFxLqw")
    schwabb_videos = fetcher.fetch_videos_by_channel("UCqoSrYgusd8ZddtMoWhjHYA")
    breakpoint()
    captions = fetcher.fetch_transcript('GZd212F2Kmg')
    converted_transcript = fetcher.convert_transcript(captions)
    filterer = YoutubeVideoFilterer()
    breakpoint()
    filterer.filter_videos(videos)