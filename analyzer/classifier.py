"""
ニュース分類モジュール
ニュースを市場全体/セクター/テーマに分類
"""
from typing import Dict, Any, List
from config import CATEGORIES


def classify_news(news_text: str, source: str = "domestic") -> Dict[str, Any]:
    """
    ニュースを分類する
    
    Args:
        news_text: ニュース本文
        source: "domestic"（国内）または "foreign"（海外）
    
    Returns:
        分類結果辞書
    """
    # キーワードベースの簡易分類
    text_lower = news_text.lower()
    
    # 市場全体キーワード
    market_keywords = [
        "日経平均", "TOPIX", "ダウ", "S&P", "ナスダック", "NASDAQ",
        "FRB", "日銀", "金融政策", "金利", "円安", "円高",
        "GDP", "インフレ", "CPI", "雇用統計", "景気",
        "利上げ", "利下げ", "量的緩和", "QE",
    ]
    
    # セクターキーワード
    sector_keywords = {
        "テクノロジー": ["AI", "半導体", "クラウド", "ソフトウェア", "IT", "エヌビディア", "NVIDIA"],
        "金融": ["銀行", "証券", "保険", "メガバンク", "金融機関"],
        "自動車": ["自動車", "EV", "電気自動車", "トヨタ", "ホンダ"],
        "不動産": ["不動産", "REIT", "住宅"],
        "エネルギー": ["原油", "石油", "ガス", "電力", "再エネ"],
        "ヘルスケア": ["製薬", "医療", "バイオ", "ヘルスケア"],
        "消費": ["小売", "消費", "EC", "通販"],
    }
    
    # テーマキーワード
    theme_keywords = {
        "地政学リスク": ["戦争", "紛争", "制裁", "地政学", "ウクライナ", "中東", "台湾"],
        "規制・政策": ["規制", "法案", "法律", "独禁法", "規制緩和"],
        "決算・業績": ["決算", "業績", "売上", "利益", "増収", "減益"],
        "M&A": ["買収", "合併", "M&A", "TOB", "統合"],
    }
    
    # 分類判定
    category = "market"  # デフォルト
    sub_category = None
    
    # セクター判定
    for sector, keywords in sector_keywords.items():
        if any(kw in news_text for kw in keywords):
            category = "sector"
            sub_category = sector
            break
    
    # テーマ判定
    for theme, keywords in theme_keywords.items():
        if any(kw in news_text for kw in keywords):
            category = "theme"
            sub_category = theme
            break
    
    # 市場全体判定（優先度高）
    if any(kw in news_text for kw in market_keywords):
        category = "market"
        sub_category = None
    
    return {
        "text": news_text,
        "source": source,
        "category": category,
        "category_name": CATEGORIES.get(category, category),
        "sub_category": sub_category,
    }


def classify_news_batch(news_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    複数ニュースを一括分類
    
    Args:
        news_list: [{"text": "...", "source": "domestic/foreign", "url": "...", ...}, ...]
    
    Returns:
        分類結果リスト（元データのフィールドを保持）
    """
    results = []
    for item in news_list:
        # 分類を実行
        classified = classify_news(item["text"], item.get("source", "domestic"))
        # 元データのフィールドを保持（url, title, description等）
        merged = {**item, **classified}
        results.append(merged)
    return results
