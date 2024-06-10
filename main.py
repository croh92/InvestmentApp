from NewsFetcher import NewsFetcher
from NewsFilterer import NewsFilterer

if __name__ == "__main__":
    news_fetcher = NewsFetcher()
    news_articles = news_fetcher.fetch()
    news_filterer = NewsFilterer()
    news_articles = news_filterer.filter_news(news_articles)
    breakpoint()
    
    print(news_articles)