"""
Market Observer - メインエントリポイント
投資市場観測・助言ツール

【重要】
このツールは投資判断を行いません。
- ❌ 売買指示
- ❌ 銘柄・数量の提案
- ❌ 断定的な将来予測
- ✅ 情報収集・構造化
- ✅ 定量評価・変化検知
- ✅ 判断材料の提示
"""
from analyzer import classify_news_batch, score_news_batch, calculate_aggregate_scores
from alert import AlertDetector
from report import generate_report


def main():
    """メイン処理"""
    print("=" * 60)
    print("📊 Market Observer - 投資市場観測ツール")
    print("=" * 60)
    print()
    print("【注意】このツールは投資判断を行いません。")
    print("        情報整理・変化検知・判断材料の提示を目的としています。")
    print()
    
    # アラート検知器
    detector = AlertDetector()
    
    # ニュース入力
    news_list = []
    
    print("-" * 40)
    print("📰 海外ニュースを入力してください")
    print("   （空行で入力終了）")
    print("-" * 40)
    
    while True:
        text = input("海外> ").strip()
        if not text:
            break
        news_list.append({"text": text, "source": "foreign"})
    
    print()
    print("-" * 40)
    print("📰 国内ニュースを入力してください")
    print("   （空行で入力終了）")
    print("-" * 40)
    
    while True:
        text = input("国内> ").strip()
        if not text:
            break
        news_list.append({"text": text, "source": "domestic"})
    
    if not news_list:
        print("\n⚠️ ニュースが入力されませんでした。終了します。")
        return
    
    print()
    print("=" * 60)
    print("📊 分析中...")
    print("=" * 60)
    
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
    
    # レポート生成
    print()
    report = generate_report(scored, aggregates, alerts)
    print()
    print(report)


if __name__ == "__main__":
    main()
