"""
Google News RSS フェッチャー

NewsAPIを補完するため、Google NewsのRSSフィードからニュースを取得
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.news_dto import NewsDTO, NewsFetchResult


class GoogleNewsClient:
    """Google News RSS クライアント"""
    
    BASE_URL = "https://news.google.com/rss"
    
    # 検索キーワード（効率化：5個に厳選）
    SEARCH_QUERIES = [
        "forex USD JPY yen",           # 為替全般
        "Federal Reserve BOJ policy",  # 中央銀行
        "stock market Nikkei S&P",     # 株式市場
        "inflation GDP economy",       # 経済指標
        "oil gold commodity price",    # コモディティ
    ]
    
    # 経済関連フィルタリング用キーワード（タイトルに含まれるべき）
    ECONOMY_KEYWORDS = [
        # 英語
        "market", "stock", "economy", "economic", "financial", "finance",
        "bank", "fed", "boj", "ecb", "rate", "rates", "inflation",
        "gdp", "growth", "trade", "trading", "invest", "investment",
        "bond", "yield", "currency", "forex", "dollar", "yen", "euro",
        "oil", "gold", "commodity", "index", "nasdaq", "dow", "nikkei",
        "earnings", "profit", "revenue", "quarter", "fiscal",
        # 日本語
        "経済", "金融", "株式", "為替", "日銀", "市場", "投資",
        "円安", "円高", "ドル", "金利", "インフレ", "景気",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_top_stories(self, topic: str = "BUSINESS") -> NewsFetchResult:
        """
        トピック別トップストーリーを取得
        
        Args:
            topic: BUSINESS, TECHNOLOGY, WORLD 等
        
        Returns:
            NewsFetchResult
        """
        url = f"{self.BASE_URL}/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB"
        # Business topic URL
        if topic == "BUSINESS":
            url = f"{self.BASE_URL}/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
        
        return self._fetch_rss(url, "Google News Top Stories")
    
    def search(self, query: str) -> NewsFetchResult:
        """
        キーワード検索
        
        Args:
            query: 検索ワード
        
        Returns:
            NewsFetchResult
        """
        encoded_query = quote(query)
        url = f"{self.BASE_URL}/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        return self._fetch_rss(url, f"Google News Search: {query}")
    
    def _fetch_rss(self, url: str, source_name: str) -> NewsFetchResult:
        """RSSフィードをパース"""
        try:
            response = self.session.get(url, timeout=8)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            
            if channel is None:
                return NewsFetchResult(
                    success=False,
                    error_message="Invalid RSS feed",
                    source_api=source_name,
                )
            
            news_list = []
            for item in channel.findall("item"):
                try:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    source = item.find("source")
                    description = item.find("description")
                    
                    # 日時パース
                    published_at = datetime.now()
                    if pub_date is not None and pub_date.text:
                        try:
                            published_at = datetime.strptime(
                                pub_date.text, 
                                "%a, %d %b %Y %H:%M:%S %Z"
                            )
                        except ValueError:
                            pass
                    
                    dto = NewsDTO(
                        title=title.text if title is not None else "",
                        description=description.text if description is not None else "",
                        source_name=source.text if source is not None else "Google News",
                        published_at=published_at,
                        region="foreign",
                        url=link.text if link is not None else None,
                    )
                    
                    if dto.title.strip():
                        news_list.append(dto)
                        
                except Exception:
                    continue
            
            return NewsFetchResult(
                success=True,
                news_list=news_list,
                source_api=source_name,
            )
            
        except requests.RequestException as e:
            return NewsFetchResult(
                success=False,
                error_message=str(e),
                source_api=source_name,
            )
    
    def _is_economy_related(self, title: str) -> bool:
        """タイトルが経済関連かどうかを判定"""
        title_lower = title.lower()
        for keyword in self.ECONOMY_KEYWORDS:
            if keyword.lower() in title_lower:
                return True
        return False
    
    def fetch_economy_news(self) -> NewsFetchResult:
        """
        経済関連ニュースをまとめて取得（並列処理・フィルタリング付き）
        """
        all_news = []
        seen_urls = set()
        filtered_count = 0
        
        # 並列でクエリを実行（最大3スレッド）
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.search, query): query for query in self.SEARCH_QUERIES}
            
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result(timeout=10)
                    if result.success:
                        for news in result.news_list:
                            if news.url and news.url not in seen_urls:
                                if self._is_economy_related(news.title):
                                    all_news.append(news)
                                    seen_urls.add(news.url)
                                else:
                                    filtered_count += 1
                except Exception:
                    continue
        
        print(f"   📰 Google News: {len(all_news)}件取得 ({filtered_count}件を経済関連外として除外)")
        
        return NewsFetchResult(
            success=True,
            news_list=all_news,
            source_api="Google News (Economy)",
        )
    
    # 後方互換性のため旧メソッド名も残す
    def fetch_forex_news(self) -> NewsFetchResult:
        """為替関連ニュースを取得（fetch_economy_newsへのエイリアス）"""
        return self.fetch_economy_news()


def fetch_google_news() -> NewsFetchResult:
    """Google Newsからビジネスニュースを取得（簡易関数）"""
    client = GoogleNewsClient()
    return client.fetch_top_stories("BUSINESS")


def fetch_google_economy_news() -> NewsFetchResult:
    """Google Newsから経済関連ニュースを取得（簡易関数）"""
    client = GoogleNewsClient()
    return client.fetch_economy_news()


# 後方互換性のため旧関数名も残す
def fetch_google_forex_news() -> NewsFetchResult:
    """Google Newsから為替関連ニュースを取得（fetch_google_economy_newsへのエイリアス）"""
    return fetch_google_economy_news()
