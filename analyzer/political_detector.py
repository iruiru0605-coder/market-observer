"""
政治発言・市場感応イベント検知モジュール

【重要】
- このモジュールは「観測」を目的とし、スコア付与は行わない
- 市場の「引き金になり得る事象」として可視化
- 投資判断・売買示唆は禁止
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PoliticalEvent:
    """政治発言・市場感応イベント"""
    
    speaker: str
    summary: str
    source_name: str
    original_text: str
    detected_keywords: List[str]
    published_at: datetime = None
    
    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker,
            "summary": self.summary,
            "source_name": self.source_name,
            "original_text": self.original_text[:200],
            "detected_keywords": self.detected_keywords,
            "evaluation": "未評価（方向性保留）",
            "position": "市場変動の引き金になり得る事象",
        }


class PoliticalEventDetector:
    """政治発言検知器"""
    
    # 検知対象の発言者キーワード
    SPEAKER_KEYWORDS = {
        "trump": "トランプ大統領",
        "president trump": "トランプ大統領",
        "donald trump": "トランプ大統領",
        "biden": "バイデン前大統領",
        "powell": "パウエルFRB議長",
        "yellen": "イエレン財務長官",
    }
    
    # 市場感応度の高いキーワード
    MARKET_SENSITIVE_KEYWORDS = [
        "tariff", "tariffs", "関税",
        "trade", "trade war", "貿易",
        "china", "中国",
        "nato", "NATO",
        "fed", "federal reserve", "FRB",
        "interest rate", "金利",
        "sanction", "制裁",
        "greenland", "グリーンランド",
        "canada", "カナダ",
        "mexico", "メキシコ",
    ]
    
    # 信頼できるソース
    TRUSTED_SOURCES = [
        "reuters", "bloomberg", "cnbc", "politico",
        "wall street journal", "financial times",
        "marketwatch", "thestreet",
    ]
    
    def detect(self, news_list: List[Dict[str, Any]]) -> List[PoliticalEvent]:
        """
        ニュースリストから政治発言・市場感応イベントを検知
        
        Returns:
            検知されたイベントのリスト
        """
        events = []
        
        for news in news_list:
            text = news.get("text", "").lower()
            title = news.get("title", "").lower() if news.get("title") else text
            source = news.get("source_name", "").lower()
            
            # 発言者の特定
            speaker = None
            for keyword, name in self.SPEAKER_KEYWORDS.items():
                if keyword in text:
                    speaker = name
                    break
            
            if not speaker:
                continue
            
            # 市場感応キーワードの検出
            detected_keywords = []
            for kw in self.MARKET_SENSITIVE_KEYWORDS:
                if kw.lower() in text:
                    detected_keywords.append(kw)
            
            # 市場感応キーワードがない場合はスキップ
            if not detected_keywords:
                continue
            
            # 要旨の生成
            summary = self._generate_summary(detected_keywords)
            
            event = PoliticalEvent(
                speaker=speaker,
                summary=summary,
                source_name=news.get("source_name", "Unknown"),
                original_text=news.get("text", ""),
                detected_keywords=detected_keywords,
            )
            events.append(event)
        
        return events
    
    def _generate_summary(self, keywords: List[str]) -> str:
        """キーワードから要旨を生成"""
        if "tariff" in keywords or "tariffs" in keywords or "関税" in keywords:
            return "関税に関する発言"
        elif "trade" in keywords or "貿易" in keywords:
            return "貿易政策に関する発言"
        elif "china" in keywords or "中国" in keywords:
            return "対中国政策に関する発言"
        elif "fed" in keywords or "interest rate" in keywords or "金利" in keywords:
            return "金融政策に関する発言"
        elif "greenland" in keywords:
            return "グリーンランドに関する発言"
        else:
            return "市場感応度の高い発言"


def detect_political_events(news_list: List[Dict[str, Any]]) -> List[PoliticalEvent]:
    """政治発言を検知（簡易関数）"""
    detector = PoliticalEventDetector()
    return detector.detect(news_list)
