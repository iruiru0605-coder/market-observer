"""
投資インパクトスコア算出モジュール

【重要】
- スコアロジック自体は変更しない
- 判定理由は観測・状況整理のために付与
- +0 = 失敗ではなく「方向性を断定できない」状態
"""
from typing import Dict, Any, List, Tuple
from config import SCORE_MIN, SCORE_MAX


def calculate_impact_score(classified_news: Dict[str, Any]) -> Tuple[int, str]:
    """
    ニュースから投資インパクトスコアを算出
    
    評価軸:
    1. 株価への方向性（ポジティブ/ネガティブ）
    2. 影響の強度（短期/中期/構造）
    3. 影響範囲（個別/業界/市場）
    
    Returns:
        (score, reason): スコア(-10〜+10)と判定理由
    """
    text = classified_news.get("text", "")
    category = classified_news.get("category", "market")
    
    score = 0
    matched_positive = []
    matched_negative = []
    
    # ===== 1. 方向性評価 =====
    
    # ポジティブキーワード
    positive_keywords = {
        # 強ポジティブ (+3)
        "過去最高": 3, "急騰": 3, "大幅上昇": 3, "予想上回る": 3,
        "beat expectations": 3, "record high": 3, "surge": 3,
        "利下げ": 2, "金融緩和": 2, "景気回復": 2,
        "rate cut": 2, "easing": 2, "recovery": 2,
        # 中ポジティブ (+2)
        "上昇": 2, "増益": 2, "好調": 2, "改善": 2, "成長": 2,
        "買い越し": 2, "需要増": 2,
        "rise": 2, "growth": 2, "gains": 2, "rally": 2,
        # 弱ポジティブ (+1)
        "堅調": 1, "安定": 1, "維持": 1, "底堅い": 1,
        "stable": 1, "steady": 1,
    }
    
    # ネガティブキーワード
    negative_keywords = {
        # 強ネガティブ (-3)
        "暴落": -3, "急落": -3, "危機": -3, "破綻": -3, "デフォルト": -3,
        "crash": -3, "plunge": -3, "crisis": -3, "default": -3,
        "利上げ": -2, "金融引き締め": -2, "リセッション": -2,
        "rate hike": -2, "tightening": -2, "recession": -2,
        # 中ネガティブ (-2)
        "下落": -2, "減益": -2, "悪化": -2, "低下": -2, "減少": -2,
        "売り越し": -2, "需要減": -2, "インフレ懸念": -2,
        "decline": -2, "drop": -2, "fall": -2, "loss": -2, "tariff": -2,
        # 弱ネガティブ (-1)
        "軟調": -1, "弱含み": -1, "警戒": -1, "懸念": -1,
        "uncertainty": -1, "concern": -1, "cautious": -1,
    }
    
    # キーワードマッチング
    text_lower = text.lower()
    
    for kw, val in positive_keywords.items():
        if kw.lower() in text_lower:
            score += val
            matched_positive.append(kw)
    
    for kw, val in negative_keywords.items():
        if kw.lower() in text_lower:
            score += val
            matched_negative.append(kw)
    
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
    
    # ===== 判定理由の生成 =====
    reason = _generate_reason(score, matched_positive, matched_negative, category)
    
    return score, reason


def _generate_reason(score: int, positive: List[str], negative: List[str], category: str) -> str:
    """
    判定理由を生成
    
    観測・状況整理のための説明であり、投資助言ではない
    """
    import random
    
    # ±0 で評価材料がない場合のバリエーション
    neutral_reasons = [
        "市場影響が限定的と判断",
        "定性的情報に留まり、価格材料不足",
        "市場全体への波及が不明確",
        "個別・話題性中心で指数影響は限定的",
        "事実報道で方向性を断定できず",
    ]
    
    if score == 0:
        if not positive and not negative:
            return random.choice(neutral_reasons)
        elif positive and negative:
            return f"好悪材料が混在（+: {', '.join(positive[:2])} / -: {', '.join(negative[:2])}）"
        else:
            return "定性的情報に留まり、価格材料不足"
    
    elif score > 0:
        if score >= 5:
            return f"強い好材料あり（{', '.join(positive[:3])}）"
        elif score >= 2:
            return f"やや好材料（{', '.join(positive[:2])}）"
        else:
            return f"弱い好材料の示唆（{', '.join(positive[:2])}）"
    
    else:  # score < 0
        if score <= -5:
            return f"強い懸念材料あり（{', '.join(negative[:3])}）"
        elif score <= -2:
            return f"やや懸念材料（{', '.join(negative[:2])}）"
        else:
            return f"弱い懸念材料の示唆（{', '.join(negative[:2])}）"


def score_news_batch(classified_news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    複数ニュースを一括スコアリング
    """
    results = []
    for news in classified_news_list:
        news_with_score = news.copy()
        score, reason = calculate_impact_score(news)
        news_with_score["impact_score"] = score
        news_with_score["score_reason"] = reason
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
            "zero_score_count": 0,
        }
    
    domestic_scores = [n["impact_score"] for n in scored_news_list if n.get("source") == "domestic"]
    foreign_scores = [n["impact_score"] for n in scored_news_list if n.get("source") == "foreign"]
    
    domestic_avg = sum(domestic_scores) / len(domestic_scores) if domestic_scores else 0
    foreign_avg = sum(foreign_scores) / len(foreign_scores) if foreign_scores else 0
    
    all_scores = [n["impact_score"] for n in scored_news_list]
    total_avg = sum(all_scores) / len(all_scores) if all_scores else 0
    
    zero_count = sum(1 for s in all_scores if s == 0)
    
    return {
        "total_score": round(total_avg, 1),
        "domestic_score": round(domestic_avg, 1),
        "foreign_score": round(foreign_avg, 1),
        "domestic_foreign_gap": round(domestic_avg - foreign_avg, 1),
        "news_count": len(scored_news_list),
        "zero_score_count": zero_count,
    }
