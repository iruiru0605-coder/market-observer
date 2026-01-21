"""
ニュースデータ転送オブジェクト（DTO）
内部で使用するニュースの標準形式を定義
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class NewsDTO:
    """ニュースの内部表現"""
    
    # 必須フィールド
    title: str
    description: str
    source_name: str
    published_at: datetime
    
    # ソース区分
    region: str = "foreign"  # "domestic" or "foreign"
    
    # オプションフィールド
    url: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    
    # 分析結果（後から付与）
    category: Optional[str] = None
    sub_category: Optional[str] = None
    impact_score: Optional[int] = None
    
    @property
    def text(self) -> str:
        """分析用テキストを取得"""
        parts = [self.title]
        if self.description:
            parts.append(self.description)
        return " ".join(parts)
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "text": self.text,
            "source": self.region,
            "title": self.title,
            "description": self.description,
            "source_name": self.source_name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "url": self.url,
            "category": self.category,
            "sub_category": self.sub_category,
            "impact_score": self.impact_score,
        }


@dataclass
class NewsFetchResult:
    """ニュース取得結果"""
    
    success: bool
    news_list: List[NewsDTO] = field(default_factory=list)
    error_message: Optional[str] = None
    source_api: str = "unknown"
    fetch_time: datetime = field(default_factory=datetime.now)
    
    @property
    def count(self) -> int:
        return len(self.news_list)
