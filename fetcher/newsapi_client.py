"""
NewsAPI クライアント
海外経済ニュースを自動取得
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Optional

from models import NewsDTO, NewsFetchResult


class NewsAPIClient:
    """NewsAPI.org クライアント"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    # 経済・金融関連キーワード
    KEYWORDS = [
        "stock market", "economy", "Federal Reserve", "inflation",
        "interest rate", "GDP", "earnings", "S&P 500", "Dow Jones",
        "NASDAQ", "bond", "treasury", "recession", "employment",
        # 為替関連
        "dollar yen", "yen", "forex", "currency intervention", "rate check",
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        if not self.api_key:
            raise ValueError("NewsAPI key not found. Set NEWSAPI_KEY environment variable.")
    
    def fetch_top_headlines(self, country: str = "us", category: str = "business") -> NewsFetchResult:
        """
        トップヘッドラインを取得
        
        Args:
            country: 国コード (us, jp, etc.)
            category: カテゴリ (business, technology, etc.)
        """
        try:
            url = f"{self.BASE_URL}/top-headlines"
            params = {
                "country": country,
                "category": category,
                "apiKey": self.api_key,
                "pageSize": 20,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                return NewsFetchResult(
                    success=False,
                    error_message=data.get("message", "Unknown error"),
                    source_api="NewsAPI",
                )
            
            news_list = self._parse_articles(data.get("articles", []), region="foreign" if country != "jp" else "domestic")
            
            return NewsFetchResult(
                success=True,
                news_list=news_list,
                source_api="NewsAPI",
            )
            
        except requests.RequestException as e:
            return NewsFetchResult(
                success=False,
                error_message=str(e),
                source_api="NewsAPI",
            )
    
    def fetch_everything(self, query: Optional[str] = None, days_back: int = 1) -> NewsFetchResult:
        """
        全記事検索
        
        Args:
            query: 検索クエリ（Noneの場合は経済キーワード）
            days_back: 何日前までの記事を取得するか
        """
        try:
            url = f"{self.BASE_URL}/everything"
            
            # クエリ構築
            if query is None:
                query = " OR ".join(self.KEYWORDS[:5])  # 最初の5キーワード
            
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            params = {
                "q": query,
                "from": from_date,
                "language": "en",
                "sortBy": "relevancy",
                "apiKey": self.api_key,
                "pageSize": 30,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                return NewsFetchResult(
                    success=False,
                    error_message=data.get("message", "Unknown error"),
                    source_api="NewsAPI",
                )
            
            news_list = self._parse_articles(data.get("articles", []), region="foreign")
            
            return NewsFetchResult(
                success=True,
                news_list=news_list,
                source_api="NewsAPI",
            )
            
        except requests.RequestException as e:
            return NewsFetchResult(
                success=False,
                error_message=str(e),
                source_api="NewsAPI",
            )
    
    def _parse_articles(self, articles: List[dict], region: str = "foreign") -> List[NewsDTO]:
        """APIレスポンスをNewsDTOに変換"""
        news_list = []
        
        for article in articles:
            try:
                # 日時パース
                published_str = article.get("publishedAt", "")
                if published_str:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                else:
                    published_at = datetime.now()
                
                dto = NewsDTO(
                    title=article.get("title", "") or "",
                    description=article.get("description", "") or "",
                    source_name=article.get("source", {}).get("name", "Unknown"),
                    published_at=published_at,
                    region=region,
                    url=article.get("url"),
                    author=article.get("author"),
                    content=article.get("content"),
                )
                
                # 空のタイトルはスキップ
                if dto.title.strip():
                    news_list.append(dto)
                    
            except Exception:
                continue
        
        return news_list


def fetch_news(api_key: Optional[str] = None) -> NewsFetchResult:
    """
    ニュースを取得（簡易関数）
    NewsAPI + Google News を併用
    
    Returns:
        NewsFetchResult
    """
    all_news = []
    existing_urls = set()
    
    # 1. NewsAPI ビジネストップヘッドライン
    try:
        client = NewsAPIClient(api_key)
        headlines = client.fetch_top_headlines(country="us", category="business")
        for news in headlines.news_list:
            if news.url and news.url not in existing_urls:
                all_news.append(news)
                existing_urls.add(news.url)
    except Exception:
        pass  # NewsAPIが失敗してもGoogle Newsで続行
    
    # 2. Google News 為替関連検索（追加ソース）
    try:
        from .googlenews_client import GoogleNewsClient
        google_client = GoogleNewsClient()
        forex_result = google_client.fetch_forex_news()
        
        if forex_result.success:
            for news in forex_result.news_list:
                if news.url and news.url not in existing_urls:
                    all_news.append(news)
                    existing_urls.add(news.url)
    except Exception:
        pass  # Google Newsが失敗してもNewsAPIの結果は返す
    
    # 3. Google News ビジネストップ（追加ソース）
    try:
        from .googlenews_client import GoogleNewsClient
        google_client = GoogleNewsClient()
        google_top = google_client.fetch_top_stories("BUSINESS")
        
        if google_top.success:
            for news in google_top.news_list:
                if news.url and news.url not in existing_urls:
                    all_news.append(news)
                    existing_urls.add(news.url)
    except Exception:
        pass
    
    if not all_news:
        return NewsFetchResult(
            success=False,
            error_message="No news could be fetched from any source",
            source_api="NewsAPI + Google News",
        )
    
    return NewsFetchResult(
        success=True,
        news_list=all_news,
        source_api="NewsAPI + Google News",
    )
