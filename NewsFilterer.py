import os
from openai import OpenAI

class NewsFilterer:
    def __init__(self):
        self.api_key = os.environ.get("OPEN_API_KEY")

    def filter_news(self, news):
            """
            Filters the news articles based on the presence of specified AI-related keywords.
            Returns a list of news articles that contain any of the specified keywords.
            """
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