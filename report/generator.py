"""
レポート生成モジュール
日次市場観測レポートを生成

【重要】
- このレポートは「観測・状況整理」を目的とする
- 投資助言・売買示唆につながる表現は禁止
- +0 = 失敗ではなく「方向性を断定できない」状態
- 初心者でも理解できる平易な日本語を使用
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import Counter
from config import get_log_filename


def generate_report(
    scored_news_list: List[Dict[str, Any]],
    aggregate_scores: Dict[str, Any],
    alerts: List[Dict[str, str]],
    political_events: Optional[List] = None,
    macro_observation = None,
    history_comparison: Optional[Dict[str, Any]] = None,
    triggers: Optional[List] = None,
    save_to_file: bool = True
) -> str:
    """
    日次市場観測レポートを生成
    """
    now = datetime.now()
    news_count = aggregate_scores.get("news_count", 0)
    zero_count = aggregate_scores.get("zero_score_count", 0)
    zero_ratio = (zero_count / news_count * 100) if news_count > 0 else 0
    total = aggregate_scores.get("total_score", 0)
    
    # スコア分布を計算
    plus2_count = sum(1 for n in scored_news_list if n.get("impact_score", 0) >= 2)
    minus2_count = sum(1 for n in scored_news_list if n.get("impact_score", 0) <= -2)
    plus2_ratio = (plus2_count / news_count * 100) if news_count > 0 else 0
    minus2_ratio = (minus2_count / news_count * 100) if news_count > 0 else 0
    
    # ===== ヘッダー =====
    report_lines = [
        "=" * 60,
        "📊 日次市場観測レポート",
        f"   生成日時: {now.strftime('%Y年%m月%d日 %H:%M')}",
        "=" * 60,
        "",
    ]
    
    # ===== 1. サマリー =====
    report_lines.extend([
        "┌─────────────────────────────────────────────────────┐",
        "│ 【サマリー】                                          │",
        "├─────────────────────────────────────────────────────┤",
        f"│  総合スコア: {total:+.1f}                                      │",
        f"│  国内: {aggregate_scores.get('domestic_score', 0):+.1f}  /  海外: {aggregate_scores.get('foreign_score', 0):+.1f}                         │",
        f"│  分析ニュース数: {news_count}件                               │",
        f"│  評価保留（±0）: {zero_count} / {news_count} 件（約{zero_ratio:.0f}%）              │",
        "└─────────────────────────────────────────────────────┘",
        "",
    ])
    
    # 状況解釈（平易な日本語）
    if zero_ratio >= 50:
        situation = "判断材料が少ない日"
        explanation = "今日は、はっきりとした良いニュース・悪いニュースが少なく、様子見の状態です。"
    elif total >= 5:
        situation = "良いニュースが多い日"
        explanation = "今日は、市場にとってプラスに見えるニュースが多く見られます。"
    elif total >= 2:
        situation = "やや良いニュースがある日"
        explanation = "今日は、少しプラスに見えるニュースがあります。"
    elif total <= -5:
        situation = "心配なニュースが多い日"
        explanation = "今日は、市場にとってマイナスに見えるニュースが多く見られます。"
    elif total <= -2:
        situation = "やや心配なニュースがある日"
        explanation = "今日は、少しマイナスに見えるニュースがあります。"
    else:
        situation = "特に大きな変化がない日"
        explanation = "今日は、良いニュースと悪いニュースが混在しており、特に偏りはありません。"
    
    report_lines.extend([
        f"📍 今日の状況: {situation}",
        f"   {explanation}",
        "",
    ])
    
    # ===== 2. 過去7日間との比較 =====
    if history_comparison and history_comparison.get("has_history"):
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【過去7日間との比較】                                  │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        days = history_comparison.get("days_count", 0)
        avg_total = history_comparison.get("avg_total_score", 0)
        avg_zero = history_comparison.get("avg_zero_ratio", 0)
        
        report_lines.append(f"   ※ 過去{days}日分のデータと比較しています")
        report_lines.append("")
        
        # 総合スコア比較
        report_lines.append(f"   ・過去{days}日平均の総合スコア: {avg_total:+.2f}")
        report_lines.append(f"   ・本日の総合スコア: {total:+.1f}")
        
        score_diff = total - avg_total
        if abs(score_diff) < 0.5:
            report_lines.append("   → 最近1週間と比べて、大きな変化はありません。")
        elif score_diff > 0:
            report_lines.append("   → 最近1週間と比べると、やや良いニュースが増えています。")
        else:
            report_lines.append("   → 最近1週間と比べると、やや慎重な評価が増えています。")
        
        report_lines.append("")
        
        # 評価保留比較
        report_lines.append("   ・評価保留（判断がつかないニュース）の割合")
        report_lines.append(f"     過去{days}日平均: {avg_zero:.0f}%")
        report_lines.append(f"     本日: {zero_ratio:.0f}%")
        
        zero_diff = zero_ratio - avg_zero
        if abs(zero_diff) < 10:
            report_lines.append("   → いつもと同じくらいです。")
        elif zero_diff > 0:
            report_lines.append("   → 今日は、判断材料として使いにくいニュースが多い日です。")
        else:
            report_lines.append("   → 今日は、判断しやすいニュースが多い日です。")
        
        report_lines.append("")
    
    # ===== 3. 観測メモ（トリガー） =====
    report_lines.extend([
        "┌─────────────────────────────────────────────────────┐",
        "│ 【観測メモ（自動検知）】                                │",
        "└─────────────────────────────────────────────────────┘",
    ])
    
    if triggers:
        for trigger in triggers:
            msg = trigger.message if hasattr(trigger, 'message') else trigger.get('message', '')
            report_lines.append(f"   💡 {msg}")
    else:
        report_lines.append("   現在、特筆すべき観測メモはありません。")
    
    report_lines.append("")
    
    # ===== 4. 評価保留ニュースの内訳 =====
    zero_news = [n for n in scored_news_list if n.get("impact_score", 0) == 0]
    if zero_news:
        reason_counts = Counter(n.get("score_reason", "不明") for n in zero_news)
        
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【評価保留ニュースの内訳】                             │",
            "│ ※なぜ判断できないニュースが多いかが分かります          │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        for reason, count in reason_counts.most_common():
            report_lines.append(f"   ・{reason}: {count}件")
        report_lines.append("")
    
    # ===== 5. 変化点・アラート =====
    report_lines.append("【変化点・アラート】")
    if alerts:
        for alert in alerts:
            severity = "⚠️" if alert.get("severity") == "warning" else "ℹ️"
            report_lines.append(f"   {severity} {alert.get('message', '')}")
    else:
        report_lines.append("   特に大きな変化は見られませんでした。")
    report_lines.append("")
    
    # ===== 6. 国内外乖離 =====
    gap = aggregate_scores.get("domestic_foreign_gap", 0)
    report_lines.extend([
        "【国内と海外の比較】",
        f"   スコアの差: {gap:+.1f}",
    ])
    
    if abs(gap) < 2:
        gap_analysis = "国内と海外で、ニュースの受け止め方に大きな差はありません。"
    elif gap >= 2:
        gap_analysis = "国内の方が、海外より楽観的なニュースが多いようです。"
    else:
        gap_analysis = "国内の方が、海外より慎重なニュースが多いようです。"
    
    report_lines.extend([
        f"   {gap_analysis}",
        "",
    ])
    
    # ===== 7. シナリオ =====
    report_lines.append("【今後の可能性（参考）】")
    scenarios = _generate_scenarios(total, gap, alerts, zero_count, news_count)
    for i, scenario in enumerate(scenarios, 1):
        report_lines.append(f"   可能性{i}: {scenario}")
    report_lines.append("")
    
    # ===== 8. マクロ環境観測 =====
    if macro_observation and macro_observation.total_count > 0:
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【経済の大きな流れ（金利・為替・指標）】                │",
            "│ ※株価に直接影響しませんが、背景として重要です        │",
            "└─────────────────────────────────────────────────────┘",
        ])
        
        if macro_observation.fx_count > 0:
            report_lines.append(f"   📈 為替（ドル・円など）に関するニュース: {macro_observation.fx_count}件")
        
        if macro_observation.rates_count > 0:
            report_lines.append(f"   📉 金利・国債に関するニュース: {macro_observation.rates_count}件")
        
        if macro_observation.data_count > 0:
            report_lines.append(f"   📊 経済指標に関するニュース: {macro_observation.data_count}件")
        
        report_lines.append("")
    
    # ===== 9. 政治発言 =====
    if political_events:
        report_lines.extend([
            "┌─────────────────────────────────────────────────────┐",
            "│ 【重要人物の発言（参考情報）】                         │",
            "│ ※スコアには影響していません                          │",
            "└─────────────────────────────────────────────────────┘",
        ])
        for event in political_events:
            event_dict = event.to_dict() if hasattr(event, 'to_dict') else event
            report_lines.extend([
                f"   - 発言者: {event_dict.get('speaker', '不明')}",
                f"     内容: {event_dict.get('summary', '不明')}",
                f"     分野: {event_dict.get('context', '不明')}",
                f"     情報源: {event_dict.get('source_name', '不明')}",
                "",
            ])
    report_lines.append("")
    
    # ===== 10. 注意点 =====
    report_lines.extend([
        "【このレポートについて】",
        "   ・このレポートは情報をまとめたものであり、投資のアドバイスではありません。",
        "   ・「判断できない」ニュースが多いことは、失敗ではなく正常な状態です。",
        "   ・最終的な判断は、ご自身の責任でお願いいたします。",
        "",
        "=" * 60,
    ])
    
    report = "\n".join(report_lines)
    
    # ===== 11. 詳細ニュース一覧 =====
    detail_lines = [
        "",
        "┌─────────────────────────────────────────────────────┐",
        "│ 【詳細ニュース一覧】                                    │",
        "└─────────────────────────────────────────────────────┘",
    ]
    
    for news in scored_news_list:
        score = news.get('impact_score', 0)
        reason = news.get('score_reason', '理由なし')
        category = news.get('category_name', '-')
        sub = f" ({news['sub_category']})" if news.get("sub_category") else ""
        source = news.get('source', '-')
        text = news.get('text', '')[:100]
        
        # スコア変動マーク（±2以上）
        mark = " ★" if abs(score) >= 2 else ""
        
        detail_lines.extend([
            "",
            f"[{source}] スコア: {score:+d}{mark}",
            f"  分類: {category}{sub}",
            f"  判定理由: {reason}",
            f"  内容: {text}...",
        ])
    
    details = "\n".join(detail_lines)
    
    # ファイル保存
    if save_to_file:
        log_path = get_log_filename()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(report)
            f.write(details)
        print(f"\n📁 レポート保存: {log_path}")
    
    return report + details


def _generate_scenarios(total_score: float, gap: float, alerts: List, zero_count: int, news_count: int) -> List[str]:
    """シナリオを生成（初心者向けの平易な表現）"""
    scenarios = []
    
    if news_count > 0 and zero_count / news_count > 0.5:
        scenarios.append("はっきりしたニュースが出るまで、動きが少ない状態が続くかもしれません。")
        scenarios.append("新しいニュースが出れば、方向性が見えてくるかもしれません。")
    elif total_score >= 3:
        scenarios.append("良いニュースが続けば、しばらく良い流れが続くかもしれません。")
        scenarios.append("一度調整が入る可能性もあります。")
    elif total_score <= -3:
        scenarios.append("悪いニュースが一段落すれば、回復の動きが出るかもしれません。")
        scenarios.append("さらに悪いニュースが続く可能性もあります。")
    else:
        scenarios.append("新しいニュースを待つ状態が続くかもしれません。")
        scenarios.append("何か大きなニュースが出れば、方向性が決まるかもしれません。")
    
    return scenarios[:2]
