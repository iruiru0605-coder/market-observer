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
    context: str  # 文脈（金融政策/関税/中央銀行独立性等）
    source_name: str
    original_text: str
    detected_keywords: List[str]
    url: str = None  # 記事URL
    published_at: datetime = None
    
    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker,
            "summary": self.summary,
            "context": self.context,
            "source_name": self.source_name,
            "original_text": self.original_text[:200],
            "detected_keywords": self.detected_keywords,
            "url": self.url,
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
    
    # 市場感応度の高いキーワードと文脈カテゴリ
    MARKET_SENSITIVE_KEYWORDS = {
        # 関税・貿易
        "tariff": "関税政策",
        "tariffs": "関税政策",
        "関税": "関税政策",
        "trade": "貿易政策",
        "trade war": "貿易政策",
        "貿易": "貿易政策",
        # 対外政策
        "china": "対中国政策",
        "中国": "対中国政策",
        "nato": "外交・安全保障",
        "greenland": "外交・安全保障",
        "canada": "対北米政策",
        "mexico": "対北米政策",
        # 金融政策
        "fed": "金融政策",
        "federal reserve": "金融政策",
        "frb": "金融政策",
        "interest rate": "金融政策",
        "rate cut": "金融政策",
        "rate hike": "金融政策",
        "金利": "金融政策",
        # 制裁
        "sanction": "経済制裁",
        "制裁": "経済制裁",
    }
    
    # 要旨テンプレート
    SUMMARY_TEMPLATES = {
        "関税政策": {
            "tariff": "関税変更に関する発言",
            "default": "関税政策に関する発言",
        },
        "貿易政策": {
            "trade war": "貿易摩擦に関する発言",
            "default": "貿易政策に関する発言",
        },
        "対中国政策": {
            "default": "対中国政策に関する発言",
        },
        "金融政策": {
            "rate cut": "FRBに対する利下げ圧力を示唆",
            "rate hike": "金利上昇への言及",
            "fed": "中央銀行政策への言及",
            "default": "金融政策に関する発言",
        },
        "外交・安全保障": {
            "greenland": "グリーンランドに関する発言",
            "nato": "NATO同盟に関する発言",
            "default": "外交・安全保障に関する発言",
        },
        "対北米政策": {
            "default": "北米諸国への政策発言",
        },
        "経済制裁": {
            "default": "経済制裁に関する発言",
        },
    }
    
    def detect(self, news_list: List[Dict[str, Any]]) -> List[PoliticalEvent]:
        """
        ニュースリストから政治発言・市場感応イベントを検知
        """
        events = []
        
        for news in news_list:
            text = news.get("text", "").lower()
            source = news.get("source_name", "Unknown")
            
            # 発言者の特定
            speaker = None
            for keyword, name in self.SPEAKER_KEYWORDS.items():
                if keyword in text:
                    speaker = name
                    break
            
            if not speaker:
                continue
            
            # 市場感応キーワードと文脈の検出
            detected_keywords = []
            context = None
            
            for kw, ctx in self.MARKET_SENSITIVE_KEYWORDS.items():
                if kw.lower() in text:
                    detected_keywords.append(kw)
                    if context is None:
                        context = ctx
            
            if not detected_keywords:
                continue
            
            # 要旨の生成（具体化）
            summary = self._generate_summary(context, detected_keywords, text)
            
            event = PoliticalEvent(
                speaker=speaker,
                summary=summary,
                context=context or "その他",
                source_name=source,
                original_text=news.get("text", ""),
                detected_keywords=detected_keywords,
                url=news.get("url"),
            )
            events.append(event)
        
        return events
    
    def _generate_summary(self, context: str, keywords: List[str], text: str) -> str:
        """キーワードから具体的な要旨を生成"""
        templates = self.SUMMARY_TEMPLATES.get(context, {})
        
        # 具体的なキーワードに基づいて要旨を選択
        for kw in keywords:
            if kw in templates:
                return templates[kw]
        
        return templates.get("default", "市場感応度の高い発言")


def detect_political_events(news_list: List[Dict[str, Any]]) -> List[PoliticalEvent]:
    """政治発言を検知（簡易関数）"""
    detector = PoliticalEventDetector()
    return detector.detect(news_list)
