"""
Market Observer - Webアプリケーション
ブラウザUIダッシュボード

Flask サーバーで以下を提供:
- / : メインダッシュボード
- /api/report : レポートデータJSON
- /api/refresh : ニュース再取得
"""
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import os

from analyzer import (
    classify_news_batch, 
    score_news_batch, 
    calculate_aggregate_scores, 
    detect_political_events,
    observe_macro,
    detect_triggers,
    detect_priority_macro
)
from analyzer.market_summary import generate_market_summary
from alert import AlertDetector
from fetcher import fetch_news
from fetcher.market_data import get_market_data
from fetcher.economic_calendar import get_economic_indicators
from data import get_history_manager

# LLM分類器（利用可能な場合）
try:
    from analyzer.llm_classifier import GeminiClassifier, classify_with_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# LLM分類を使用するかどうか（環境変数で制御）
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true" and LLM_AVAILABLE



app = Flask(__name__, template_folder='templates', static_folder='static')


def generate_dashboard_data():
    """ダッシュボード用データを生成"""
    
    # ニュース取得
    result = fetch_news()
    
    if not result.success or result.count == 0:
        return {
            "success": False,
            "error": result.error_message or "ニュースを取得できませんでした",
            "timestamp": datetime.now().isoformat(),
        }
    
    # DTOを分析用形式に変換
    news_list = [dto.to_dict() for dto in result.news_list]
    
    # 分析（ハイブリッド方式：LLM + キーワード）
    detector = AlertDetector()
    
    if USE_LLM and len(news_list) > 0:
        # ハイブリッド方式: 上位50件のみLLM、残りはキーワードベース
        LLM_LIMIT = 50
        
        if len(news_list) <= LLM_LIMIT:
            # 全件LLM処理
            scored = classify_with_llm(news_list)
        else:
            # 上位はLLM、残りはキーワード
            llm_batch = news_list[:LLM_LIMIT]
            keyword_batch = news_list[LLM_LIMIT:]
            
            llm_scored = classify_with_llm(llm_batch)
            keyword_classified = classify_news_batch(keyword_batch)
            keyword_scored = score_news_batch(keyword_classified)
            
            scored = llm_scored + keyword_scored
        
        classified = scored  # LLMは分類済み
    else:
        # 従来のキーワードベース分類
        classified = classify_news_batch(news_list)
        scored = score_news_batch(classified)
    
    aggregates = calculate_aggregate_scores(scored)
    alerts = detector.detect_alerts(aggregates)
    political_events = detect_political_events(scored)
    macro_observation = observe_macro(scored)
    priority_macro = detect_priority_macro(scored)
    
    # 統計情報
    news_count = aggregates.get("news_count", 0)
    zero_count = aggregates.get("zero_score_count", 0)
    zero_ratio = (zero_count / news_count * 100) if news_count > 0 else 0
    
    plus2_count = sum(1 for n in scored if n.get("impact_score", 0) >= 2)
    minus2_count = sum(1 for n in scored if n.get("impact_score", 0) <= -2)
    plus2_ratio = (plus2_count / news_count * 100) if news_count > 0 else 0
    minus2_ratio = (minus2_count / news_count * 100) if news_count > 0 else 0
    
    macro_ratio = (macro_observation.total_count / news_count * 100) if news_count > 0 else 0
    
    # 履歴管理
    history_manager = get_history_manager()
    current_data = {
        "total_score": aggregates.get("total_score", 0),
        "zero_ratio": zero_ratio,
        "plus2_ratio": plus2_ratio,
        "minus2_ratio": minus2_ratio,
    }
    history_comparison = history_manager.get_7day_comparison(current_data)
    
    consecutive_high_zero = history_manager.get_consecutive_high_zero_days()
    if zero_ratio > 80:
        consecutive_high_zero += 1
    
    history_manager.add_daily_record(
        total_score=aggregates.get("total_score", 0),
        zero_ratio=zero_ratio,
        plus2_ratio=plus2_ratio,
        minus2_ratio=minus2_ratio,
        news_count=news_count,
        macro_ratio=macro_ratio,
    )
    
    # トリガー検知
    triggers = detect_triggers(
        zero_ratio=zero_ratio,
        plus2_ratio=plus2_ratio,
        minus2_ratio=minus2_ratio,
        macro_ratio=macro_ratio,
        consecutive_high_zero_days=consecutive_high_zero,
    )
    
    # 一言まとめ生成
    one_liner = _generate_one_liner(
        aggregates.get("total_score", 0),
        zero_ratio,
        priority_macro
    )
    
    # 判断しやすさ
    has_priority = priority_macro and priority_macro.has_any
    
    # 政治発言グループ化
    grouped_political = _group_political_events(political_events)
    
    # 評価保留理由の集計（記事詳細を含める）
    zero_reasons = {}
    for n in scored:
        if n.get("impact_score", 0) == 0:
            reason = n.get("score_reason", "不明")
            if reason not in zero_reasons:
                zero_reasons[reason] = {"count": 0, "articles": []}
            zero_reasons[reason]["count"] += 1
            # 最大5件まで記事を保存
            if len(zero_reasons[reason]["articles"]) < 5:
                zero_reasons[reason]["articles"].append({
                    "title": n.get("title", n.get("text", "")[:60]),
                    "url": n.get("url"),
                    "source_name": n.get("source_name", ""),
                })
    
    # ニュースをスコア別に分類
    positive_news = [n for n in scored if n.get("impact_score", 0) > 0]
    negative_news = [n for n in scored if n.get("impact_score", 0) < 0]
    neutral_news = [n for n in scored if n.get("impact_score", 0) == 0]
    
    return {
        "success": True,
        "timestamp": datetime.now().strftime("%Y年%m月%d日 %H:%M"),
        "summary": {
            "total_score": round(aggregates.get("total_score", 0), 1),
            "domestic_score": round(aggregates.get("domestic_score", 0), 1),
            "foreign_score": round(aggregates.get("foreign_score", 0), 1),
            "news_count": news_count,
            "zero_count": zero_count,
            "zero_ratio": round(zero_ratio, 0),
            "plus2_count": plus2_count,
            "minus2_count": minus2_count,
        },
        "one_liner": one_liner,
        "has_priority": has_priority,
        "priority_macro": {
            "fed": _format_priority_news(priority_macro.fed_news if priority_macro else [], "fed"),
            "treasury": _format_priority_news(priority_macro.treasury_news if priority_macro else [], "treasury"),
            "usdjpy": _format_priority_news(priority_macro.usdjpy_news if priority_macro else [], "usdjpy"),
            "employment": _format_priority_news(priority_macro.employment_news if priority_macro else [], "employment"),
            "inflation": _format_priority_news(priority_macro.inflation_news if priority_macro else [], "inflation"),
            "ism": _format_priority_news(priority_macro.ism_news if priority_macro else [], "ism"),
        },
        "history": history_comparison if history_comparison.get("has_history") else None,
        "triggers": [{"id": t.id, "name": t.name, "message": t.message} for t in triggers],
        # zero_reasons削除（ニュース一覧の評価保留と重複するため）
        "alerts": alerts,
        "political_events": grouped_political,
        "macro": {
            "fx_count": macro_observation.fx_count if macro_observation else 0,
            "rates_count": macro_observation.rates_count if macro_observation else 0,
            "data_count": macro_observation.data_count if macro_observation else 0,
        },
        "news": {
            "positive": positive_news[:10],
            "negative": negative_news[:10],
            "neutral": neutral_news[:10],
        },
        # マーケットデータ（為替・国債利回り・指標等）
        "market_data": _get_market_data_with_summary(),
        # 経済指標
        "economic_indicators": get_economic_indicators(),
    }


def _get_market_data_with_summary() -> dict:
    """マーケットデータと概況テキストを取得"""
    market_data = get_market_data()
    market_summary = generate_market_summary(market_data)
    market_data["summary"] = market_summary
    return market_data


def _generate_one_liner(total: float, zero_ratio: float, priority_macro) -> str:
    """今日の一言まとめを生成"""
    has_priority = priority_macro and priority_macro.has_any if priority_macro else False
    
    if has_priority:
        if zero_ratio >= 50:
            return "重要な情報が出ていますが、全体的には判断材料が少ない日です。"
        else:
            return "判断材料が揃っている日です。重要情報を確認してください。"
    else:
        if zero_ratio >= 70:
            return "判断材料が少なく、方向性を決めにくい日です。"
        elif zero_ratio >= 50:
            return "はっきりしたニュースが少なめの日です。"
        elif total >= 3:
            return "良いニュースが目立つ日です。"
        elif total <= -3:
            return "心配なニュースが目立つ日です。"
        else:
            return "特に大きな動きがない日です。"


def _format_priority_news(news_list, category_name: str = ""):
    """priority_macro用のニュース整形（LLM評価情報付き）"""
    if not news_list:
        return {"count": 0, "has": False, "articles": [], "summary": ""}
    
    articles = []
    total_score = 0
    score_count = 0
    
    for n in news_list[:5]:  # 最大5件
        score = n.get("impact_score", 0)
        total_score += score
        score_count += 1
        
        articles.append({
            "title": n.get("title", n.get("text", "")[:60]),
            "url": n.get("url"),
            "source_name": n.get("source_name", ""),
            "score": score,
            "reason": n.get("score_reason", ""),
            "time_horizon": n.get("time_horizon", "medium"),
            "confidence": n.get("confidence", 0),
        })
    
    # カテゴリサマリーを生成
    avg_score = total_score / score_count if score_count > 0 else 0
    summary = _generate_category_summary(category_name, avg_score, len(news_list))
    
    return {
        "count": len(news_list),
        "has": len(news_list) > 0,
        "articles": articles,
        "avg_score": round(avg_score, 1),
        "summary": summary,
    }


def _generate_category_summary(category_name: str, avg_score: float, count: int) -> str:
    """カテゴリ別のサマリーを生成"""
    if count == 0:
        return ""
    
    # カテゴリ名の日本語マッピング
    category_labels = {
        "fed": "FRB関連",
        "treasury": "米国債関連",
        "usdjpy": "ドル円関連",
        "employment": "雇用関連",
        "inflation": "物価関連",
        "ism": "ISM関連",
    }
    label = category_labels.get(category_name, category_name)
    
    # スコアに基づくサマリー
    if avg_score >= 3:
        return f"{label}: 強い買い材料が目立つ（平均スコア {avg_score:+.1f}）"
    elif avg_score >= 1:
        return f"{label}: やや買い寄りの内容（平均スコア {avg_score:+.1f}）"
    elif avg_score >= -1:
        return f"{label}: 中立的な内容が中心（平均スコア {avg_score:+.1f}）"
    elif avg_score >= -3:
        return f"{label}: やや売り寄りの内容（平均スコア {avg_score:+.1f}）"
    else:
        return f"{label}: 強い売り材料が目立つ（平均スコア {avg_score:+.1f}）"

def _group_political_events(events):
    """政治発言を発言者ごとにグループ化"""
    if not events:
        return []
    
    grouped = {}
    
    for event in events:
        event_dict = event.to_dict() if hasattr(event, 'to_dict') else event
        speaker = event_dict.get("speaker", "不明")
        
        if speaker not in grouped:
            grouped[speaker] = {
                "speaker": speaker,
                "themes": {},
                "items": [],  # summary + URL のペアリスト
                "sources": [],
            }
        
        context = event_dict.get("context", "その他")
        grouped[speaker]["themes"][context] = grouped[speaker]["themes"].get(context, 0) + 1
        
        # summary と url をペアで保存（詳細情報付き）
        grouped[speaker]["items"].append({
            "summary": event_dict.get("summary", ""),
            "title": event_dict.get("title", ""),
            "description": event_dict.get("original_text", ""), # 冒頭テキスト
            "url": event_dict.get("url"),
            "source_name": event_dict.get("source_name", ""),
            "score": event_dict.get("impact_score", 0),
            "reason": event_dict.get("score_reason", ""),
        })
        grouped[speaker]["sources"].append(event_dict.get("source_name", ""))
    
    # リスト形式に変換
    result = []
    for speaker, data in grouped.items():
        # 重複を削除しつつURLを保持
        seen_summaries = set()
        unique_items = []
        for item in data["items"]:
            if item["summary"] not in seen_summaries:
                seen_summaries.add(item["summary"])
                unique_items.append(item)
        
        result.append({
            "speaker": speaker,
            "themes": [{"name": k, "count": v} for k, v in data["themes"].items()],
            "articles": unique_items[:5],  # items -> articles
            "count": len(unique_items),    # count追加
            "sources": list(set(data["sources"]))[:3],
        })
    
    return result


@app.route('/')
def index():
    """メインダッシュボード"""
    return render_template('dashboard.html')


@app.route('/api/report')
def api_report():
    """レポートデータAPI"""
    data = generate_dashboard_data()
    return jsonify(data)


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """ニュース再取得API"""
    data = generate_dashboard_data()
    return jsonify(data)


if __name__ == '__main__':
    print("=" * 60)
    print("📊 Market Observer - Dashboard")
    print("   http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
