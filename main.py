"""
Market Observer - メインエントリポイント
投資市場観測・助言ツール（完全自動実行版）

【重要】
このツールは投資判断を行いません。
- ❌ 売買指示
- ❌ 銘柄・数量の提案
- ❌ 断定的な将来予測
- ✅ 情報収集・構造化
- ✅ 定量評価・変化検知
- ✅ 判断材料の提示
"""
import sys
from datetime import datetime

from analyzer import classify_news_batch, score_news_batch, calculate_aggregate_scores, detect_political_events
from alert import AlertDetector
from report import generate_report
from fetcher import fetch_news
from models import NewsDTO


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
    
    # ===== 4. レポート生成 =====
    print()
    report = generate_report(scored, aggregates, alerts, political_events)
    print()
    print(report)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
