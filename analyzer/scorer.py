"""
投資インパクトスコア算出モジュール
"""
from typing import Dict, Any, List
from config import SCORE_MIN, SCORE_MAX


def calculate_impact_score(classified_news: Dict[str, Any]) -> int:
    """
    ニュースから投資インパクトスコアを算出
    
    評価軸:
    1. 株価への方向性（ポジティブ/ネガティブ）
    2. 影響の強度（短期/中期/構造）
    3. 影響範囲（個別/業界/市場）
    
    Returns:
        -10〜+10の整数スコア
    """
    text = classified_news.get("text", "")
    category = classified_news.get("category", "market")
    
    score = 0
    
    # ===== 1. 方向性評価 =====
    
    # ポジティブキーワード
    positive_keywords = {
        # 強ポジティブ (+3)
        "過去最高": 3, "急騰": 3, "大幅上昇": 3, "予想上回る": 3,
        "利下げ": 2, "金融緩和": 2, "景気回復": 2,
        # 中ポジティブ (+2)
        "上昇": 2, "増益": 2, "好調": 2, "改善": 2, "成長": 2,
        "買い越し": 2, "需要増": 2,
        # 弱ポジティブ (+1)
        "堅調": 1, "安定": 1, "維持": 1, "底堅い": 1,
    }
    
    # ネガティブキーワード
    negative_keywords = {
        # 強ネガティブ (-3)
        "暴落": -3, "急落": -3, "危機": -3, "破綻": -3, "デフォルト": -3,
        "利上げ": -2, "金融引き締め": -2, "リセッション": -2,
        # 中ネガティブ (-2)
        "下落": -2, "減益": -2, "悪化": -2, "低下": -2, "減少": -2,
        "売り越し": -2, "需要減": -2, "インフレ懸念": -2,
        # 弱ネガティブ (-1)
        "軟調": -1, "弱含み": -1, "警戒": -1, "懸念": -1,
    }
    
    # キーワードマッチング
    for kw, val in positive_keywords.items():
        if kw in text:
            score += val
    
    for kw, val in negative_keywords.items():
        if kw in text:
            score += val
    
    # ===== 2. 影響範囲による補正 =====
    
    # 市場全体は影響大
    if category == "market":
        score = int(score * 1.2)
    # セクターは中程度
    elif category == "sector":
        score = int(score * 1.0)
    # テーマは個別性が高い
    elif category == "theme":
        score = int(score * 0.8)
    
    # ===== 3. ソースによる補正 =====
    
    source = classified_news.get("source", "domestic")
    if source == "foreign":
        # 海外ニュースは先行指標として重視
        score = int(score * 1.1)
    
    # ===== スコア範囲制限 =====
    score = max(SCORE_MIN, min(SCORE_MAX, score))
    
    return score


def score_news_batch(classified_news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    複数ニュースを一括スコアリング
    """
    results = []
    for news in classified_news_list:
        news_with_score = news.copy()
        news_with_score["impact_score"] = calculate_impact_score(news)
        results.append(news_with_score)
    return results


def calculate_aggregate_scores(scored_news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ニュースリストから集計スコアを算出
    """
    if not scored_news_list:
        return {
            "total_score": 0,
            "domestic_score": 0,
            "foreign_score": 0,
            "domestic_foreign_gap": 0,
            "news_count": 0,
        }
    
    domestic_scores = [n["impact_score"] for n in scored_news_list if n.get("source") == "domestic"]
    foreign_scores = [n["impact_score"] for n in scored_news_list if n.get("source") == "foreign"]
    
    domestic_avg = sum(domestic_scores) / len(domestic_scores) if domestic_scores else 0
    foreign_avg = sum(foreign_scores) / len(foreign_scores) if foreign_scores else 0
    
    all_scores = [n["impact_score"] for n in scored_news_list]
    total_avg = sum(all_scores) / len(all_scores) if all_scores else 0
    
    return {
        "total_score": round(total_avg, 1),
        "domestic_score": round(domestic_avg, 1),
        "foreign_score": round(foreign_avg, 1),
        "domestic_foreign_gap": round(domestic_avg - foreign_avg, 1),
        "news_count": len(scored_news_list),
    }
