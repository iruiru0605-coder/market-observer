"""
Market Observer - メインエントリポイント
投資市場観測・助言ツール（完全自動実行版）

【設計思想】
このツールは投資判断そのものを行わず、
利用者（人間）が判断するための
「情報の重要度・信頼度・現在の判断しやすさ」を構造的に可視化する。

- ❌ 売買指示
- ❌ 将来予測
- ❌ 断定表現
- ✅ 「判断しやすいのか／しにくいのか」を可視化
- ✅ 「どの情報を重視すべき日なのか」を伝える
"""
import sys
from datetime import datetime

from analyzer import (
    classify_news_batch, 
    score_news_batch, 
    calculate_aggregate_scores, 
    detect_political_events,
    observe_macro,
    detect_triggers,
    detect_priority_macro
)
from alert import AlertDetector
from report import generate_report
from fetcher import fetch_news
from models import NewsDTO
from data import get_history_manager


def main():
    """メイン処理（完全自動実行）"""
    print("=" * 60)
    print("📊 Market Observer - 投資市場観測ツール")
    print(f"   実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    print("【注意】このツールは投資判断を行いません。")
    print("        情報整理・変化検知・判断材料の提示を目的としています。")
    print()
    
    # ===== 1. ニュース取得 =====
    print("-" * 40)
    print("📰 ニュースを取得中...")
    print("-" * 40)
    
    result = fetch_news()
    
    if not result.success:
        print(f"\n⚠️ ニュース取得に失敗しました: {result.error_message}")
        print("   環境変数 NEWSAPI_KEY が設定されているか確認してください。")
        print()
        print("   設定例: set NEWSAPI_KEY=your_api_key_here")
        return 1
    
    if result.count == 0:
        print("\n⚠️ ニュースが取得できませんでした。終了します。")
        return 1
    
    print(f"   ✓ {result.count}件のニュースを取得しました（{result.source_api}）")
    
    # ===== 2. DTOを分析用形式に変換 =====
    news_list = [dto.to_dict() for dto in result.news_list]
    
    # ===== 3. 分析 =====
    print()
    print("=" * 60)
    print("📊 分析中...")
    print("=" * 60)
    
    # アラート検知器
    detector = AlertDetector()
    
    # 分類
    classified = classify_news_batch(news_list)
    print(f"   ✓ 分類完了: {len(classified)}件")
    
    # スコアリング
    scored = score_news_batch(classified)
    print(f"   ✓ スコアリング完了")
    
    # 集計
    aggregates = calculate_aggregate_scores(scored)
    print(f"   ✓ 集計完了: 総合スコア {aggregates['total_score']:+.1f}")
    
    # アラート検出
    alerts = detector.detect_alerts(aggregates)
    detector.add_daily_score(aggregates)
    print(f"   ✓ アラート検出完了: {len(alerts)}件")
    
    # 政治発言検知
    political_events = detect_political_events(news_list)
    print(f"   ✓ 政治発言検知完了: {len(political_events)}件")
    
    # マクロ環境観測
    macro_observation = observe_macro(news_list)
    print(f"   ✓ マクロ環境観測完了: {macro_observation.total_count}件")
    
    # 最優先マクロ検知（新規追加）
    priority_macro = detect_priority_macro(news_list)
    print(f"   ✓ 最優先マクロ検知完了: {priority_macro.total_count}件")
    
    # ===== 4. 統計情報の計算 =====
    news_count = aggregates.get("news_count", 0)
    zero_count = aggregates.get("zero_score_count", 0)
    zero_ratio = (zero_count / news_count * 100) if news_count > 0 else 0
    
    plus2_count = sum(1 for n in scored if n.get("impact_score", 0) >= 2)
    minus2_count = sum(1 for n in scored if n.get("impact_score", 0) <= -2)
    plus2_ratio = (plus2_count / news_count * 100) if news_count > 0 else 0
    minus2_ratio = (minus2_count / news_count * 100) if news_count > 0 else 0
    
    macro_ratio = (macro_observation.total_count / news_count * 100) if news_count > 0 else 0
    
    # ===== 5. 履歴管理 =====
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
    
    print(f"   ✓ 履歴更新完了")
    
    # ===== 6. トリガー検知 =====
    triggers = detect_triggers(
        zero_ratio=zero_ratio,
        plus2_ratio=plus2_ratio,
        minus2_ratio=minus2_ratio,
        macro_ratio=macro_ratio,
        consecutive_high_zero_days=consecutive_high_zero,
    )
    print(f"   ✓ トリガー検知完了: {len(triggers)}件")
    
    # ===== 7. レポート生成 =====
    print()
    report = generate_report(
        scored, 
        aggregates, 
        alerts, 
        political_events,
        macro_observation,
        history_comparison,
        triggers,
        priority_macro
    )
    print()
    print(report)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
